# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

import time
import pigpio
import logging
from ..utils.exceptions import BacklightError
from ..utils.config     import Config

logger = logging.getLogger('DisplayController')

class DisplayBacklight:
    """Controls display backlight brightness using hardware PWM via pigpio"""

    def __init__(self):
        """Initialize backlight with configuration from config file"""
        config = Config().display.get('backlight', {})
        self.pin: int = config['pin']
        self.gamma: float = config['gamma']
        self.retry_attempts: int = config['retry_attempts']
        self.pwmf: int = config['pwm_frequency']

        self.current_step = 0
        self.pi = None

        # Get brightness levels from config
        self.brightness_levels = config['brightness_levels']

        self._initialize_pwm()

    def _initialize_pwm(self) -> None:
        """Initialize pigpio PWM with retry logic"""
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Attempting to initialize PWM on pin {self.pin} (attempt {attempt + 1}/{self.retry_attempts})")
                self.pi = pigpio.pi()
                if not self.pi.connected:
                    raise BacklightError("Failed to connect to pigpio daemon")

                # Set up pin as output
                self.pi.set_mode(self.pin, pigpio.OUTPUT)

                # Start at full brightness
                self.set_brightness(self.brightness_levels[0])
                logger.info("PWM initialization successful")
                break
            except Exception as e:
                logger.error(f"PWM initialization attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.retry_attempts - 1:
                    raise BacklightError(f"Failed to initialize PWM after {self.retry_attempts} attempts: {str(e)}")
                time.sleep(0.5)

    def _pwm_brightness_value(self, value: float) -> int:
        """
        normalize brightness value (0-1) to hardware PWM value (0-255)
        Applies gamma correction
        """
        if value == 0:
            return 0
        gamma_corrected = pow(value, self.gamma)
        return min(255, max(0, int(gamma_corrected * 255)))

    def set_brightness(self, raw_value: float) -> None:
        """Set brightness with gamma correction and value conversion"""
        if not self.pi or not self.pi.connected:
            logger.error("Attempted to set brightness but PWM not initialized")
            raise BacklightError("PWM not initialized")

        try:
            hw_value = self._pwm_brightness_value(raw_value)
            self.pi.set_PWM_dutycycle(self.pin, hw_value)
            logger.debug(f"Set brightness raw:{raw_value:.3f} hw_value:{hw_value}")
        except Exception as e:
            logger.error(f"Failed to set brightness: {str(e)}")
            raise BacklightError(f"Invalid brightness value: {str(e)}")

    def step_brightness(self) -> None:
        """Step brightness down by one level, cycling back to 100% after 0%"""
        if not self.pi or not self.pi.connected:
            logger.error("Attempted to step brightness but PWM not initialized")
            raise BacklightError("PWM not initialized")

        try:
            # Move to next brightness level
            self.current_step = (self.current_step + 1) % len(self.brightness_levels)
            # Set the new brightness from our levels list
            raw_value = self.brightness_levels[self.current_step]
            self.set_brightness(raw_value)
            logger.debug(f"Set brightness to {self.get_brightness_percentage()}%")
        except Exception as e:
            logger.error(f"Failed to set brightness: {str(e)}")
            raise BacklightError(f"Failed to step brightness: {str(e)}")

    def get_brightness_percentage(self) -> int:
        """Get current brightness as percentage"""
        if not self.pi or not self.pi.connected:
            logger.error("Attempted to get brightness but PWM not initialized")
            raise BacklightError("PWM not initialized")

        return int(self.brightness_levels[self.current_step] * 100)

    def cleanup(self) -> None:
        """Clean up pigpio resources"""
        if self.pi and self.pi.connected:
            try:
                logger.info("Cleaning up PWM device")
                self.pi.set_PWM_dutycycle(self.pin, 0)
                self.pi.stop()
            except Exception as e:
                logger.error(f"Error during PWM cleanup: {str(e)}")
                raise BacklightError(f"Failed to cleanup PWM device: {str(e)}")

