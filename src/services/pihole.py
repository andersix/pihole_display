# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

import subprocess
import time
import logging
from threading import Timer
from typing import Optional
from ..utils.exceptions import ServiceError
from ..utils.constants import CONFIRMATION_TIMEOUT, FEEDBACK_DELAY
from ..display.manager import DisplayManager

logger = logging.getLogger('DisplayController')

class PiHole:
    """Manages PiHole operations"""
    
    def __init__(self, display_manager: DisplayManager):
        """
        Initialize PiHole controller
        
        Args:
            display_manager: DisplayManager instance for output control
        """
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

    def handle_button2_held(self, hold_time: float) -> None:
        """Handle button 2 hold event for showing update selection"""
        logger.info(f"Button 2 held for {hold_time:.1f} seconds")
        
        if hold_time >= 1.0:
            logger.info("Showing update selection")
            self._waiting_for_confirmation = True
            self._start_confirmation_timer()
            if not self.display.show_update_selection():
                logger.error("Failed to show update selection screen")
                self.cancel_update()

    def handle_button3_press(self) -> None:
        """Handle button 3 press for gravity update confirmation"""
        if self._waiting_for_confirmation:
            logger.info("Gravity update selected")
            self._clear_confirmation_state()
            self.update_gravity()

    def handle_button4_press(self) -> None:
        """Handle button 4 press for pihole update confirmation"""
        if self._waiting_for_confirmation:
            logger.info("Pi-hole update selected")
            self._clear_confirmation_state()
            self.update_pihole()

    def _run_pihole_command(self, command: list[str], operation: str) -> None:
        """
        Execute a Pi-hole command with proper output handling
        
        Args:
            command: Command list to execute
            operation: Name of operation for logging
        """
        logger.info(f"Starting Pi-hole {operation}")
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
            self.display.switch_to_padd()

    def update_gravity(self) -> None:
        """Execute gravity update"""
        self._run_pihole_command(['sudo', 'pihole', '-g'], 'gravity update')

    def update_pihole(self) -> None:
        """Execute Pi-hole update"""
        self._run_pihole_command(['sudo', 'pihole', '-up'], 'Pi-hole update')

    def cleanup(self) -> None:
        """Clean up PiHole resources"""
        try:
            self._clear_confirmation_state()
            logger.info("Cleaned up PiHole controller")
        except Exception as e:
            logger.error(f"Error during PiHole cleanup: {str(e)}")

