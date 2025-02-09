# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:fileformat=unix:

import subprocess
import logging
from threading import Timer
import time
from typing import Optional, Tuple
from ..utils.exceptions import ServiceError
from ..utils.constants import (
    CONFIRMATION_TIMEOUT,
    FEEDBACK_DELAY,
    SYSTEM_CONTROL_HOLD
)
from ..display.manager import DisplayManager

logger = logging.getLogger('DisplayController')

class SystemOps:
    """Manages system-level operations like reboot, shutdown and apt update/upgrade"""

    def __init__(self, display_manager: DisplayManager):
        """Initialize SystemOps controller"""
        try:
            self.display = display_manager
            self._waiting_for_confirmation = False
            self._confirmation_timer: Optional[Timer] = None
            logger.info("Initializing SystemOps controller")
        except Exception as e:
            logger.error(f"Failed to initialize SystemOps controller: {str(e)}")
            raise ServiceError(f"Failed to initialize SystemOps controller: {str(e)}")

    def _run_process_command(self, command: list[str], operation: str, finish: bool = True) -> Tuple[int, str]:
        """
        Execute a process command with proper output handling

        Args:
            command: Command list to execute
            operation: Operation name for logging
            finish: Whether to switch back to PADD when done

        Returns:
            tuple containing (return_code, output_text)
        """
        logger.info(f"Starting {operation}")
        output = ""
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            while process.poll() is None:
                line = process.stdout.readline()
                if line:
                    output += line
                    print(line.rstrip())

            returncode = process.wait()

            if returncode == 0:
                logger.info(f"{operation} completed successfully")
                if finish:
                    print(f"\n{operation} completed successfully")
            else:
                logger.error(f"{operation} failed")
                if finish:
                    print(f"\n{operation} failed")

            return returncode, output

        except subprocess.SubprocessError as e:
            error_msg = f"Failed to {operation}: {str(e)}"
            logger.error(error_msg)
            print(f"\nError: {error_msg}")  # Always show error
            raise ServiceError(error_msg)
        finally:
            if finish:
                time.sleep(FEEDBACK_DELAY)
                self.display.switch_to_padd()

    def show_menu(self, hold_time: float) -> None:
        """button 1 hold for system control menu"""
        logger.info(f"Button 1 held for {hold_time:.1f} seconds")

        if hold_time >= SYSTEM_CONTROL_HOLD:
            logger.info("Showing system control menu")
            self._waiting_for_confirmation = True
            self._start_confirmation_timer()
            self.display.show_system_menu()

    def request_system_update(self) -> None:
        """button 2 press - confirm update"""
        if self._waiting_for_confirmation:
            logger.info("System update confirmed")
            self._clear_confirmation_state()
            self.update_system()

    def request_reboot(self) -> None:
        """button 3 press - confirm restart"""
        if self._waiting_for_confirmation:
            logger.info("System restart confirmed")
            self._clear_confirmation_state()
            self.reboot_system()

    def request_shutdown(self) -> None:
        """button 4 press - confirm shutdown"""
        if self._waiting_for_confirmation:
            logger.info("System shutdown confirmed")
            self._clear_confirmation_state()
            self.shutdown_system()

    def update_system(self) -> None:
        """Execute system update"""
        try:
            print("\nUpdating package lists...")
            returncode, output = self._run_process_command(
                ['sudo', 'apt-get', 'update'],
                'package list update',
                finish=False
            )

            if returncode != 0:
                logger.error("Package list update failed")
                print("\nPackage list update failed")
                time.sleep(FEEDBACK_DELAY)
                self.display.switch_to_padd()
                return

            # Check if all packages are up to date
            if "All packages are up to date." in output:
                logger.info("System is already up to date")
                print("\nSystem is already up to date")
                time.sleep(FEEDBACK_DELAY)
                self.display.switch_to_padd()
                return

            print("\nUpgrading packages...")
            self._run_process_command(
                ['sudo', 'apt-get', '-y', 'full-upgrade'],
                'system upgrade',
                finish=True
            )
        except Exception as e:
            logger.error(f"Failed to update system: {str(e)}")
            print(f"\nError: Failed to update system: {str(e)}")
            time.sleep(FEEDBACK_DELAY)
            self.display.switch_to_padd()

    def reboot_system(self) -> None:
        """Handle system reboot"""
        logger.info("Initiating system reboot")
        try:
            print("\nRebooting system...")
            time.sleep(FEEDBACK_DELAY)
            subprocess.run(['sudo', 'reboot'], check=True)
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to reboot system: {str(e)}")
            raise ServiceError(f"Failed to reboot system: {str(e)}")

    def shutdown_system(self) -> None:
        """Handle system shutdown"""
        logger.info("Initiating system shutdown")
        try:
            print("\nShutting down system...")
            time.sleep(FEEDBACK_DELAY)
            subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to shutdown system: {str(e)}")
            raise ServiceError(f"Failed to shutdown system: {str(e)}")

    def _start_confirmation_timer(self) -> None:
        """Start confirmation timeout timer"""
        if self._confirmation_timer:
            self._confirmation_timer.cancel()
        self._confirmation_timer = Timer(CONFIRMATION_TIMEOUT, self._handle_timeout)
        self._confirmation_timer.start()

    def _handle_timeout(self) -> None:
        """Handle confirmation timeout"""
        if self._waiting_for_confirmation:
            logger.info("System control timeout - cancelling")
            self.cancel_confirmation()

    def _clear_confirmation_state(self) -> None:
        """Clear confirmation state and cancel timer"""
        if self._confirmation_timer:
            self._confirmation_timer.cancel()
            self._confirmation_timer = None
        self._waiting_for_confirmation = False

    def cancel_confirmation(self) -> None:
        """Cancel pending system control confirmation"""
        if self._waiting_for_confirmation:
            logger.info("System control cancelled")
            print("\n    System control cancelled")
            self._clear_confirmation_state()
            time.sleep(FEEDBACK_DELAY)
            self.display.switch_to_padd()

    def cleanup(self) -> None:
        """Clean up SystemOps resources"""
        try:
            self._clear_confirmation_state()
            logger.info("Cleaned up SystemOps controller")
        except Exception as e:
            logger.error(f"Error during SystemOps cleanup: {str(e)}")

