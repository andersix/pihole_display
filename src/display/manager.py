# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

import subprocess
import time
import logging
from typing import Optional
from ..utils.exceptions import DisplayError
from ..utils.config import Config
from .tmux import TMuxController
from .backlight import DisplayBacklight

logger = logging.getLogger('DisplayController')

class DisplayManager:
    """Manages display output and PADD integration"""

    def __init__(self):
        """Initialize display manager with TMux controller"""
        self.tmux = TMuxController()
        self.backlight = None  # Will be set by ButtonManager
        self._previous_brightness = 1.0  # Store previous brightness level
        config = Config().display.get('tmux', {})
        self.session_name = config.get('session_name', 'display')
        self.padd_window = config.get('padd_window', 'padd')
        self.control_window = config.get('control_window', 'control')

    def set_backlight(self, backlight: DisplayBacklight) -> None:
        """Set the backlight controller"""
        self.backlight = backlight

    def check_padd(self) -> bool:
        """
        Verify PADD session exists and is running

        Returns:
            bool: True if session exists, False otherwise
        """
        try:
            logger.debug("Checking for PADD tmux session")
            result = subprocess.run(
                ['tmux', 'has-session', '-t', self.session_name],
                capture_output=True
            )

            if result.returncode != 0:
                logger.error("PADD tmux session not found")
                return False

            logger.debug("PADD tmux session found")
            return True

        except Exception as e:
            logger.error(f"Error checking PADD session: {e}")
            return False

    def show_update_selection(self) -> bool:
        """
        Show update selection screen

        Returns:
            bool: True if display switched successfully
        """
        try:
            logger.debug("Switching to control window for update selection")
            self.tmux.switch_window(self.control_window)

            # Set display to full brightness
            if self.backlight:
                self._previous_brightness = self.backlight.brightness_levels[self.backlight.current_step]
                self.backlight.set_brightness(1.0)

            self._clear_screen()

            print("\n" * 2)
            print("    +--------------------------------+")
            print("    |     Pi-hole Update Request     |")
            print("    +--------------------------------+")
            print("\n    Button 3: Update Gravity")
            print("    - Updates blocklists")
            print("    - Takes 2-3 minutes")
            print("\n    Button 4: Update Pi-hole")
            print("    - Updates core software")
            print("    - Takes 5+ minutes")
            print("\n    Waiting 30s for selection...")
            print("    Any other button cancels")

            return True

        except Exception as e:
            logger.error(f"Error showing update selection: {e}")
            return False

    def show_system_control(self) -> bool:
        """
        Show system control options

        Returns:
            bool: True if display switched successfully
        """
        try:
            logger.debug("Switching to control window for system control")
            self.tmux.switch_window(self.control_window)

            # Set display to full brightness
            if self.backlight:
                self._previous_brightness = self.backlight.brightness_levels[self.backlight.current_step]
                self.backlight.set_brightness(1.0)

            self._clear_screen()

            print("\n" * 2)
            print("    +--------------------------------+")
            print("    |     System Control Request     |")
            print("    +--------------------------------+")
            print("\n    WARNING: Power state change!")
            print("\n    Button 3: Restart System")
            print("    - System will reboot")
            print("\n    Button 4: Shutdown System")
            print("    - System will power off")
            print("\n    Waiting 30s for selection...")
            print("    Any other button cancels")

            return True

        except Exception as e:
            logger.error(f"Error showing system control: {e}")
            return False

    def switch_to_padd(self) -> None:
        """Switch back to PADD window"""
        try:
            logger.debug("Switching back to PADD window")
            self.tmux.switch_window(self.padd_window)
            # Restore previous brightness
            if self.backlight:
                self.backlight.set_brightness(self._previous_brightness)
                # Also update current_step to match
                for i, level in enumerate(self.backlight.brightness_levels):
                    if level == self._previous_brightness:
                        self.backlight.current_step = i
                        break
            logger.debug("Successfully switched to PADD window")
        except Exception as e:
            logger.error(f"Error switching to PADD window: {e}")
            raise DisplayError(f"Failed to switch to PADD window: {e}")

    def _clear_screen(self) -> None:
        """Clear screen and reset cursor position"""
        try:
            # Clear screen
            subprocess.run(['clear'], check=True)
            # Move cursor to top
            print("\033[H", end="")
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to clear screen: {e}")
            raise DisplayError(f"Failed to clear screen: {e}")

