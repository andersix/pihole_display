# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

import logging
from typing              import List, Callable, Optional
from ..utils.exceptions  import ButtonError
from ..utils.config      import Config
from ..hardware          import ButtonConfig, ButtonHandler
from ..display.backlight import DisplayBacklight
from ..services.pihole   import PiHole
from ..services.system   import SystemOps
from ..display.manager   import DisplayManager

logger = logging.getLogger('DisplayController')

class ButtonManager:
    """Manages multiple button instances and their associated controllers"""

    def __init__(self, display_manager: DisplayManager):
        """
        Initialize button manager and controllers

        Args:
            display_manager: DisplayManager instance for display control
        """
        self.buttons: List[ButtonHandler] = []
        try:
            logger.info("Initializing ButtonManager and controllers")
            self.display = display_manager
            self.backlight = DisplayBacklight() # Pass backlight to display manager
            self.display.set_backlight(self.backlight)
            self.pihole = PiHole(display_manager=self.display)
            self.system = SystemOps(display_manager=self.display)
        except Exception as e:
            error_msg = f"Failed to initialize controllers: {str(e)}"
            logger.critical(error_msg)
            raise ButtonError(error_msg)

    def add_button(self,
                  config: ButtonConfig,
                  callback: Optional[Callable[[], None]] = None,
                  hold_callback: Optional[Callable[[float], None]] = None) -> None:
        """
        Add a new button to manage

        Args:
            config: ButtonConfig object for the new button
            callback: Optional function to call when button is pressed
            hold_callback: Optional function to call when button is held
        """
        try:
            button = ButtonHandler(
                config=config,
                callback=callback,
                hold_callback=hold_callback
            )
            self.buttons.append(button)
            logger.info(f"Added button {config.function} on pin {config.pin}")
        except Exception as e:
            error_msg = f"Failed to add button on pin {config.pin}: {str(e)}"
            logger.error(error_msg)
            raise ButtonError(error_msg)

    def cancel_confirmation(self) -> None:
        """Cancel any pending confirmation in either pihole or system mode"""
        if self.pihole._waiting_for_confirmation:
            self.pihole.cancel_update()
        elif self.system._waiting_for_confirmation:
            self.system.cancel_confirmation()

    def cleanup(self) -> None:
        """Clean up all managed resources"""
        logger.info("Starting cleanup of ButtonManager")
        try:
            for button in self.buttons:
                button.cleanup()
            self.backlight.cleanup()
            self.pihole.cleanup()
            self.system.cleanup()
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

