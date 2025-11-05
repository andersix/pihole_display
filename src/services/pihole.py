# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

import subprocess
import time
import logging

from threading import Timer
from typing    import Optional
from pathlib   import Path

from ..utils.exceptions import ServiceError
from ..utils.constants  import (
    CONFIRMATION_TIMEOUT,
    FEEDBACK_DELAY,
    PATHS,
    UPDATE_SELECT_HOLD
)

from ..display.manager  import DisplayManager

logger = logging.getLogger('DisplayController')

class PiHole:
    """Manages PiHole requests and operations"""

    def __init__(self, display_manager: DisplayManager):
        try:
            self.display = display_manager
            self._waiting_for_confirmation = False
            self._confirmation_timer: Optional[Timer] = None
            logger.info("Initializing PiHole controller")
        except Exception as e:
            logger.error(f"Failed to initialize PiHole controller: {str(e)}")
            raise ServiceError(f"Failed to initialize PiHole controller: {str(e)}")

    def _start_confirmation_timer(self) -> None:
        """Start confirmation timeout timer"""
        if self._confirmation_timer:
            self._confirmation_timer.cancel()
        self._confirmation_timer = Timer(CONFIRMATION_TIMEOUT, self._handle_timeout)
        self._confirmation_timer.start()
        logger.debug("Started confirmation timer")

    def _handle_timeout(self) -> None:
        """Handle confirmation timeout"""
        if self._waiting_for_confirmation:
            logger.info("Update selection timeout - cancelling")
            self.cancel_update()

    def _clear_confirmation_state(self) -> None:
        """Clear all confirmation state"""
        if self._confirmation_timer:
            self._confirmation_timer.cancel()
            self._confirmation_timer = None
        self._waiting_for_confirmation = False
        logger.debug("Cleared confirmation state")

    def is_waiting_for_confirmation(self) -> bool:
        """Check if waiting for user confirmation"""
        return self._waiting_for_confirmation

    def cancel_update(self) -> None:
        """Cancel any pending update confirmation"""
        if self._waiting_for_confirmation:
            logger.info("Update cancelled")
            print("\n    Update cancelled")
            self._clear_confirmation_state()
            time.sleep(FEEDBACK_DELAY)
            self.display.switch_to_padd()

    def show_menu(self, hold_time: float) -> None:
        """Handle button 2 hold event for showing Pi-Hole menu"""
        logger.info(f"Button 2 held for {hold_time:.1f} seconds")

        if hold_time >= UPDATE_SELECT_HOLD:
            logger.info("Showing Pi-Hole menu")
            self._waiting_for_confirmation = True
            self._start_confirmation_timer()
            if not self.display.show_pihole_menu():
                logger.error("Failed to show pihole menu screen")
                self.cancel_update()

    def request_gravity_update(self) -> None:
        """Handle button 2 press for gravity update confirmation"""
        if self._waiting_for_confirmation:
            print("    Gravity update selected\n")
            logger.info("Gravity update selected")
            self._clear_confirmation_state()
            self.update_gravity()

    def request_pihole_update(self) -> None:
        """Handle button 3 press for pihole update confirmation"""
        if self._waiting_for_confirmation:
            print("    Pi-hole update selected\n")
            logger.info("Pi-hole update selected")
            self._clear_confirmation_state()
            self.update_pihole()

    def request_padd_update(self) -> None:
        """Handle button 4 press for PADD update confirmation"""
        if self._waiting_for_confirmation:
            print("    PADD update selected\n")
            logger.info("PADD update selected")
            self._clear_confirmation_state()
            self.update_padd()


    def _run_process_command(self, command: list[str], operation: str, cwd: Optional[str] = None, finish: bool = True) -> int:
        """
        Execute a process command with proper output handling

        Args:
            command: Command list to execute
            operation: Operation name for logging
            cwd: Optional working directory for command
            finish: Whether to switch back to PADD when done

        Returns:
            Process return code
        """
        logger.info(f"Starting {operation}")
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=cwd
            )

            while process.poll() is None:
                line = process.stdout.readline()
                if line:
                    print(line.rstrip())

            returncode = process.wait()

            if returncode == 0:
                logger.info(f"{operation} completed successfully")
                if finish:
                    print(f"\n    {operation} completed successfully")
            else:
                logger.error(f"{operation} failed")
                if finish:
                    print(f"\n    {operation} failed")

            return returncode

        except subprocess.SubprocessError as e:
            logger.error(f"Failed to {operation}: {str(e)}")
            if finish:
                print(f"\n    Error: Failed to {operation}: {str(e)}")
            raise ServiceError(f"Failed to {operation}: {str(e)}")
        finally:
            if finish:
                time.sleep(FEEDBACK_DELAY)
                self.display.switch_to_padd()

    def update_gravity(self) -> None:
        """Execute gravity update (update Pi-hole's blocklists)"""
        logger.info("Starting gravity update")

        try:
            print("\n    Updating gravity (blocklists)...")

            # Run pihole gravity update
            process = subprocess.Popen(
                ['sudo', 'pihole', '-g'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Stream output to display in real-time
            while process.poll() is None:
                line = process.stdout.readline()
                if line:
                    print(f"    {line.rstrip()}")

            # Get any remaining output
            remaining_stdout, stderr = process.communicate()
            if remaining_stdout:
                for line in remaining_stdout.splitlines():
                    print(f"    {line}")

            returncode = process.returncode

            # Provide feedback based on result
            if returncode == 0:
                logger.info("Gravity update completed successfully")
                print("\n    Gravity update completed successfully")
            else:
                logger.error(f"Gravity update failed with return code {returncode}")
                print("\n    Gravity update failed")
                # Display stderr if present
                if stderr:
                    for line in stderr.splitlines():
                        logger.error(f"Gravity update error: {line}")
                        print(f"    {line}")

        except Exception as e:
            logger.error(f"Failed to update gravity: {str(e)}")
            print(f"\n    Error: Failed to update gravity: {str(e)}")
        finally:
            time.sleep(FEEDBACK_DELAY)
            self.display.switch_to_padd()

    def update_pihole(self) -> None:
        """Execute Pi-hole core software update"""
        logger.info("Starting Pi-hole update")

        try:
            print("\n    Updating Pi-hole core software...")

            # Run pihole update
            process = subprocess.Popen(
                ['sudo', 'pihole', '-up'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Stream output to display in real-time
            while process.poll() is None:
                line = process.stdout.readline()
                if line:
                    print(f"    {line.rstrip()}")

            # Get any remaining output
            remaining_stdout, stderr = process.communicate()
            if remaining_stdout:
                for line in remaining_stdout.splitlines():
                    print(f"    {line}")

            returncode = process.returncode

            # Provide feedback based on result
            if returncode == 0:
                logger.info("Pi-hole update completed successfully")
                print("\n    Pi-hole update completed successfully")
            else:
                logger.error(f"Pi-hole update failed with return code {returncode}")
                print("\n    Pi-hole update failed")
                # Display stderr if present
                if stderr:
                    for line in stderr.splitlines():
                        logger.error(f"Pi-hole update error: {line}")
                        print(f"    {line}")

        except Exception as e:
            logger.error(f"Failed to update Pi-hole: {str(e)}")
            print(f"\n    Error: Failed to update Pi-hole: {str(e)}")
        finally:
            time.sleep(FEEDBACK_DELAY)
            # Wait for FTL service to restart and PADD to recover
            self._wait_for_ftl_recovery()
            self.display.switch_to_padd()

    def update_padd(self) -> None:
        """
        Update PADD from git repository

        Note: PADD is a git submodule. This performs a git pull within the
        submodule directory to get the latest code. This is appropriate for
        end-user installations.
        """
        logger.info("Starting PADD update")
        padd_dir = Path(PATHS['padd_dir'])

        try:
            print("\n    Updating PADD...")

            # Run git pull and capture output
            process = subprocess.Popen(
                ['git', 'pull'],
                cwd=str(padd_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Stream output to display
            output_lines = []
            while process.poll() is None:
                line = process.stdout.readline()
                if line:
                    output_lines.append(line.rstrip())
                    print(f"    {line.rstrip()}")

            # Get any remaining output
            remaining_stdout, stderr = process.communicate()
            if remaining_stdout:
                for line in remaining_stdout.splitlines():
                    output_lines.append(line)
                    print(f"    {line}")

            returncode = process.returncode
            output_text = '\n'.join(output_lines)

            # Determine result and provide feedback
            if returncode == 0:
                if "Already up to date" in output_text or "Already up-to-date" in output_text:
                    logger.info("PADD is already up to date")
                    print("\n    PADD is already up to date")
                else:
                    logger.info("PADD updated successfully")
                    print("\n    PADD updated successfully")
            else:
                logger.error(f"PADD update failed with return code {returncode}")
                print("\n    PADD update failed")
                if stderr:
                    for line in stderr.splitlines():
                        logger.error(f"PADD update error: {line}")
                        print(f"    {line}")

        except subprocess.TimeoutExpired:
            logger.error("PADD update timed out")
            print("\n    Error: Update timed out")
        except Exception as e:
            logger.error(f"Failed to update PADD: {str(e)}")
            print(f"\n    Error: Failed to update PADD: {str(e)}")
        finally:
            time.sleep(FEEDBACK_DELAY)
            self.display.switch_to_padd()

    def _wait_for_ftl_recovery(self, max_wait: int = 30, check_interval: float = 2.0) -> None:
        """
        Wait for FTL service to come back online after Pi-hole update.

        Pi-hole updates restart the FTL service, which can leave PADD in a bad state
        showing "No connection to FTL!" errors. This method waits for FTL to be
        responsive again before returning control to PADD.

        Args:
            max_wait: Maximum seconds to wait for FTL recovery
            check_interval: Seconds between FTL availability checks
        """
        logger.info("Waiting for FTL service to recover after Pi-hole update")
        print("\n    Waiting for FTL service to restart...")

        start_time = time.time()
        ftl_recovered = False

        while (time.time() - start_time) < max_wait:
            try:
                # Check if FTL is responding using dig query (same method PADD uses)
                result = subprocess.run(
                    ['dig', '+short', '+time=1', '+tries=1', 'chaos', 'txt', 'local.api.ftl', '@localhost'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )

                # If dig returns 0 and has output, FTL is responding
                if result.returncode == 0 and result.stdout.strip():
                    logger.info("FTL service recovered successfully")
                    print("    FTL service is back online")
                    ftl_recovered = True
                    break

            except (subprocess.SubprocessError, subprocess.TimeoutExpired):
                pass  # FTL not ready yet, continue waiting

            time.sleep(check_interval)

        if not ftl_recovered:
            logger.warning(f"FTL service did not recover within {max_wait} seconds")
            print(f"    Warning: FTL may still be restarting")

        # Give PADD one more refresh cycle to update its display
        time.sleep(1)

    def cleanup(self) -> None:
        """Clean up PiHole resources"""
        try:
            self._clear_confirmation_state()
            logger.info("Cleaned up PiHole controller")
        except Exception as e:
            logger.error(f"Error during PiHole cleanup: {str(e)}")

