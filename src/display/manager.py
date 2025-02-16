# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

import subprocess
import time
import logging
from typing             import Optional
from pathlib            import Path
from ..utils.exceptions import DisplayError
from ..utils.config     import Config
from .tmux              import TMuxController
from .backlight         import DisplayBacklight

logger = logging.getLogger('DisplayController')

class DisplayManager:
    """Manages display output and PADD integration"""

    def __init__(self):
        """
        Initialize display manager with TMux controller.
        One tmux window for PADD, one for the PiHole menus
        """
        self.tmux = TMuxController()
        self.backlight = None
        self._previous_brightness = 1.0
        config = Config().display['tmux']
        self.session_name = config['session_name']
        self.padd_window = config['padd_window']
        self.control_window = config['control_window']

    def set_backlight(self, backlight: DisplayBacklight) -> None:
        """Set the backlight controller"""
        self.backlight = backlight

    def check_padd(self) -> bool:
        """
        Verify PADD session exists and is running
        Returns: True if session exists, False otherwise
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

    def show_pihole_menu(self) -> bool:
        """
        Show pihole menu selection screen
        Returns: True if display switched successfully
        """
        try:
            logger.debug("Switching to control window for pihole menu")
            self.tmux.switch_window(self.control_window)

            # Set display to full brightness
            if self.backlight:
                self._previous_brightness = self.backlight.brightness_levels[self.backlight.current_step]
                self.backlight.set_brightness(1.0)

            self._clear_screen()

            print("    +---------------------------------+")
            print("    |       Pi-Hole Update Menu       |")
            print("    +---------------------------------+")
            print("\n")
            print("    Button 2: Update Gravity")
            print("    - press to update blocklists")
            print("\n")
            print("    Button 3: Update Pi-hole")
            print("    - press to update core software")
            print("\n")
            print("    Button 4: Update PADD")
            print("    - press to update dashboard code")
            print("\n")
            print("    Waiting 30s for selection")
            print("    Any other button cancels")

            return True

        except Exception as e:
            logger.error(f"Error showing update selection: {e}")
            return False

    def show_system_menu(self) -> bool:
        """
        Show system control menu
        Returns: True if display switched successfully
        """
        try:
            logger.debug("Switching to control window for system control")
            self.tmux.switch_window(self.control_window)

            # Set display to full brightness
            if self.backlight:
                self._previous_brightness = self.backlight.brightness_levels[self.backlight.current_step]
                self.backlight.set_brightness(1.0)

            self._clear_screen()

            print("    +--------------------------------+")
            print("    |      System Control Menu       |")
            print("    +--------------------------------+")
            print("\n")
            print("    Button 2: Update System")
            print("    - press to update RPi OS and system packages")
            print("\n")
            print("    Button 3: Restart System")
            print("    - press to reboot")
            print("\n")
            print("    Button 4: Shutdown System")
            print("    - press to shutdown, then power off")
            print("\n")
            print("    Waiting 30s for selection...")
            print("    Any other button cancels")

            return True

        except Exception as e:
            logger.error(f"Error showing system control: {e}")
            return False

    def switch_to_padd(self) -> None:
        """Switch to PADD window"""
        try:
            logger.debug("Switching to PADD window")
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
        """Clear the LCD screen and reset cursor position"""
        try:
            # Clear screen
            subprocess.run(['clear'], check=True)
            # Move cursor to top
            print("\033[H", end="")
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to clear screen: {e}")
            raise DisplayError(f"Failed to clear screen: {e}")

