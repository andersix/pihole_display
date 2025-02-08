# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:fileformat=unix:

import subprocess
import logging
from threading import Timer
import time
from typing import Optional
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

    def _run_system_command(self, command: list[str], operation: str) -> None:
        """
        Execute a system command with proper output handling

        Args:
            command: Command list to execute
            operation: Operation name for logging
        """
        logger.info(f"Starting {operation}")
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )

            while process.poll() is None:
                line = process.stdout.readline()
                if line:
                    print(line.rstrip())

            returncode = process.wait()

            if returncode == 0:
                logger.info(f"{operation} completed successfully")
                print(f"\n{operation} completed successfully")
            else:
                logger.error(f"{operation} failed")
                print(f"\n{operation} failed")

        except subprocess.SubprocessError as e:
            logger.error(f"Failed to {operation}: {str(e)}")
            print(f"\nError: Failed to {operation}: {str(e)}")
            raise ServiceError(f"Failed to {operation}: {str(e)}")
        finally:
            time.sleep(FEEDBACK_DELAY)
            if operation != "shutdown system":  # Don't switch back if shutting down
                self.display.switch_to_padd()

    def update_system(self) -> None:
        """Execute system update"""
        self._run_system_command(
            ['sudo', 'apt', 'update', '&&', 'sudo', 'apt', '-y', 'full-upgrade'],
            'system update'
        )

    def reboot_system(self) -> None:
        """Handle system reboot"""
        self._run_system_command(['sudo', 'reboot'], 'reboot system')

    def shutdown_system(self) -> None:
        """Handle system shutdown"""
        self._run_system_command(['sudo', 'shutdown', '-h', 'now'], 'shutdown system')

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

    def handle_button1_held(self, hold_time: float) -> None:
        """Handle button 1 hold for system control"""
        logger.info(f"Button 1 held for {hold_time:.1f} seconds")

        if hold_time >= SYSTEM_CONTROL_HOLD:
            logger.info("Showing system control options")
            self._waiting_for_confirmation = True
            self._start_confirmation_timer()
            self.display.show_system_control()

    def handle_button2_press(self) -> None:
        """Handle button 2 press - confirm update"""
        if self._waiting_for_confirmation:
            logger.info("System update confirmed")
            self._clear_confirmation_state()
            self.update_system()

    def handle_button3_press(self) -> None:
        """Handle button 3 press - confirm restart"""
        if self._waiting_for_confirmation:
            logger.info("System restart confirmed")
            self._clear_confirmation_state()
            self.reboot_system()

    def handle_button4_press(self) -> None:
        """Handle button 4 press - confirm shutdown"""
        if self._waiting_for_confirmation:
            logger.info("System shutdown confirmed")
            self._clear_confirmation_state()
            self.shutdown_system()

    def cleanup(self) -> None:
        """Clean up SystemOps resources"""
        try:
            self._clear_confirmation_state()
            logger.info("Cleaned up SystemOps controller")
        except Exception as e:
            logger.error(f"Error during SystemOps cleanup: {str(e)}")

