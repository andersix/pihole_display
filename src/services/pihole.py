# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

import subprocess
import time
import logging
from threading import Timer
from typing import Optional
from pathlib import Path
from ..utils.exceptions import ServiceError
from ..utils.constants import (
    CONFIRMATION_TIMEOUT,
    FEEDBACK_DELAY,
    PATHS,
    UPDATE_SELECT_HOLD
)
from ..display.manager import DisplayManager

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
        """Execute gravity update"""
        self._run_process_command(
            command=['sudo', 'pihole', '-g'],
            operation='gravity update'
        )

    def update_pihole(self) -> None:
        """Execute Pi-hole update"""
        self._run_process_command(
            command=['sudo', 'pihole', '-up'],
            operation='Pi-hole update'
        )

    def update_padd(self) -> None:
        """Check and update PADD if needed"""
        logger.info("Starting PADD update check")
        padd_dir = Path(PATHS['padd_dir'])

        try:
            print("\n    Checking PADD for updates...")

            # Fetch updates without finishing
            fetch_result = self._run_process_command(
                command=['git', 'fetch'],
                operation='git fetch',
                cwd=str(padd_dir),
                finish=False
            )

            if fetch_result != 0:
                logger.error("Failed to fetch PADD updates")
                print("\n    Failed to fetch PADD updates")
                return

            # Check status without finishing
            status_result = self._run_process_command(
                command=['git', 'status', '-uno'],
                operation='check PADD status',
                cwd=str(padd_dir),
                finish=False
            )

            if "Your branch is behind" in str(status_result):
                print("\n    Updates available. Updating PADD...")

                # Pull changes and finish
                self._run_process_command(
                    command=['git', 'pull'],
                    operation='update PADD',
                    cwd=str(padd_dir),
                    finish=True
                )
            else:
                logger.info("PADD is already up to date")
                print("\n    PADD is already up to date")
                time.sleep(FEEDBACK_DELAY)
                self.display.switch_to_padd()

        except Exception as e:
            logger.error(f"Failed to update PADD: {str(e)}")
            print(f"\n    Error: Failed to update PADD: {str(e)}")
            time.sleep(FEEDBACK_DELAY)
            self.display.switch_to_padd()


    def cleanup(self) -> None:
        """Clean up PiHole resources"""
        try:
            self._clear_confirmation_state()
            logger.info("Cleaned up PiHole controller")
        except Exception as e:
            logger.error(f"Error during PiHole cleanup: {str(e)}")

