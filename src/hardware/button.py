# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

import time
import logging
from typing             import Callable, Optional
from gpiozero           import Button as GPIOButton
from gpiozero.exc       import GPIOZeroError
from ..utils.exceptions import ButtonError
from .models            import ButtonConfig

logger = logging.getLogger('DisplayController')

class ButtonHandler:
    """
    A class to handle button input using gpiozero Button

    This class provides a wrapper around GPIOZero's Button class,
    adding support for hold duration tracking and custom callbacks.
    """

    def __init__(self,
                 config: ButtonConfig,
                 callback: Optional[Callable[[], None]] = None,
                 hold_callback: Optional[Callable[[float], None]] = None):
        """
        Initialize the button handler.

        Args:
            config: ButtonConfig object containing pin and setup information
            callback: Optional function to call when button is pressed
            hold_callback: Optional function to call when button is released after hold
        """
        try:
            self._hold_start: Optional[float] = None
            self._press_handled = False
            self.function = config.function

            self.button = GPIOButton(
                pin=config.pin,
                pull_up=config.pull_up,
                bounce_time=config.bounce_time,
                hold_time=config.hold_time,
                hold_repeat=config.hold_repeat
            )

            self._setup_callbacks(callback, hold_callback)

            logger.info(f"Initialized {self.function} button on pin {config.pin}")

        except GPIOZeroError as e:
            error_msg = f"Failed to initialize button on pin {config.pin}: {str(e)}"
            logger.error(error_msg)
            raise ButtonError(error_msg)

    def _setup_callbacks(self,
                        press_callback: Optional[Callable[[], None]],
                        hold_callback: Optional[Callable[[float], None]]) -> None:
        """
        Set up button callbacks

        Args:
            press_callback: Function to call on button press
            hold_callback: Function to call on button release after hold
        """
        self._press_callback = press_callback
        self._hold_callback = hold_callback

        if hold_callback:
            def on_press():
                """Handle button press"""
                self._hold_start = time.time()
                self._press_handled = False
                logger.debug(f"{self.function} button pressed at {self._hold_start}")

                # If this is a button that can handle both press and hold,
                # we'll wait to see if it's a hold before executing press
                if not self._hold_callback:
                    self._handle_press()

            self.button.when_pressed = on_press
            self.button.when_released = self._on_release
        elif press_callback:
            self.button.when_pressed = press_callback

    def _handle_press(self) -> None:
        """Handle button press event"""
        if self._press_callback and not self._press_handled:
            self._press_callback()
            self._press_handled = True
            logger.debug(f"{self.function} button press handled")

    def _on_release(self) -> None:
        """Handle button release and calculate hold duration"""
        if self._hold_start is not None:
            hold_duration = time.time() - self._hold_start
            logger.debug(f"{self.function} button released after {hold_duration:.2f}s")

            # Check if this is a short press or a hold
            if self._hold_callback and hold_duration >= self.button.hold_time:
                # This was a hold, execute hold callback
                logger.debug(f"{self.function} executing hold callback")
                self._hold_callback(hold_duration)
            else:
                # This was a short press, execute press callback
                logger.debug(f"{self.function} executing press callback")
                self._handle_press()

        self._hold_start = None
        self._press_handled = False

    def cleanup(self) -> None:
        """
        Clean up button resources

        This method ensures proper cleanup of GPIO resources
        """
        try:
            if hasattr(self, 'button') and self.button is not None:
                pin_number = self.button.pin.number
                self.button.close()
                logger.debug(f"Cleaned up button on pin {pin_number}")
            else:
                logger.debug("No button to clean up")
        except Exception as e:
            error_msg = f"Error during button cleanup: {str(e)}"
            logger.error(error_msg)
            raise ButtonError(error_msg)

