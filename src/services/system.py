# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:fileformat=unix:
import subprocess
import logging
from threading import Timer
import time
from typing import Optional
from ..utils.exceptions import ServiceError
from ..utils.constants import CONFIRMATION_TIMEOUT, FEEDBACK_DELAY
from ..display.manager import DisplayManager

logger = logging.getLogger('DisplayController')

class SystemOs:
    """Manages system-level operations like reboot and shutdown"""
    
    def __init__(self, display_manager: DisplayManager):
        """Initialize SystemOs controller"""
        try:
            self.display = display_manager
            self._waiting_for_confirmation = False
            self._confirmation_timer: Optional[Timer] = None
            logger.info("Initializing SystemOs controller")
        except Exception as e:
            logger.error(f"Failed to initialize SystemOs controller: {str(e)}")
            raise ServiceError(f"Failed to initialize SystemOs controller: {str(e)}")

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
        
        if hold_time >= 5.0:  # Only activate after 5 seconds
            logger.info("Showing system control options")
            self._waiting_for_confirmation = True
            self._start_confirmation_timer()
            self.display.show_system_control()

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

    def reboot_system(self) -> None:
        """Handle system reboot"""
        logger.info("Initiating system reboot")
        try:
            print("\n    Rebooting system...")
            time.sleep(FEEDBACK_DELAY)
            subprocess.run(['sudo', 'reboot'], check=True)
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to reboot system: {str(e)}")
            raise ServiceError(f"Failed to reboot system: {str(e)}")

    def shutdown_system(self) -> None:
        """Handle system shutdown"""
        logger.info("Initiating system shutdown")
        try:
            print("\n    Shutting down system...")
            time.sleep(FEEDBACK_DELAY)
            subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to shutdown system: {str(e)}")
            raise ServiceError(f"Failed to shutdown system: {str(e)}")

    def cleanup(self) -> None:
        """Clean up SystemOs resources"""
        try:
            self._clear_confirmation_state()
            logger.info("Cleaned up SystemOs controller")
        except Exception as e:
            logger.error(f"Error during SystemOs cleanup: {str(e)}")

