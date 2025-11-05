# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

import subprocess
import time
import logging
from typing             import Optional
from pathlib            import Path
from ..utils.exceptions import DisplayError
from ..utils.config     import Config
from ..utils.constants  import CONFIRMATION_TIMEOUT
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
            print(f"    Waiting {CONFIRMATION_TIMEOUT}s for selection")
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
            print(f"    Waiting {CONFIRMATION_TIMEOUT}s for selection...")
            print("    Any other button cancels")

            return True

        except Exception as e:
            logger.error(f"Error showing system control: {e}")
            return False

    def switch_to_padd(self) -> None:
        """Switch to PADD window and force refresh"""
        try:
            logger.debug("Switching to PADD window")

            # Force PADD to redraw by sending WINCH signal (window resize)
            # This triggers PADD's TerminalResize handler to clear screen and refresh
            self._refresh_padd_display()

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

    def _refresh_padd_display(self) -> None:
        """
        Force PADD to refresh by sending WINCH (window resize) signal.

        This triggers PADD's TerminalResize handler which:
        - Checks terminal size with SizeChecker
        - Clears screen and scrollback buffer
        - Kills the sleep timer to force immediate redraw

        This is especially useful after Pi-hole updates that restart FTL,
        ensuring PADD recovers from "No connection to FTL!" errors.
        """
        try:
            # Get PID of padd.sh process in the padd window
            result = subprocess.run(
                ['tmux', 'list-panes', '-t', f'{self.session_name}:{self.padd_window}',
                 '-F', '#{pane_pid}'],
                capture_output=True,
                text=True,
                check=True
            )

            pane_pid = result.stdout.strip()
            if not pane_pid:
                logger.warning("Could not find PADD pane PID for refresh")
                return

            # Get the actual padd.sh process PID (child of the shell in tmux pane)
            ps_result = subprocess.run(
                ['pgrep', '-P', pane_pid, '-f', 'padd.sh'],
                capture_output=True,
                text=True
            )

            padd_pid = ps_result.stdout.strip()
            if padd_pid:
                # Send WINCH (Window Change) signal to force PADD to redraw
                subprocess.run(['kill', '-WINCH', padd_pid], check=False)
                logger.debug(f"Sent WINCH signal to PADD process {padd_pid}")
            else:
                logger.debug("PADD process not found, skipping WINCH signal")

        except Exception as e:
            # Non-critical - PADD will still work, just might not refresh immediately
            logger.debug(f"Could not send WINCH signal to PADD: {e}")

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

