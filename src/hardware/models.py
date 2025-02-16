# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

from dataclasses        import dataclass
from typing             import Optional
from ..utils.constants  import ButtonFunction  # Changed from .utils to ..utils
from ..utils.exceptions import ConfigError   # Changed from .utils to ..utils

@dataclass
class ButtonConfig:
    """Configuration settings for a button"""
    pin: int
    function: str
    pull_up: bool = True
    bounce_time: float = 0.05
    hold_time: Optional[float] = None
    hold_repeat: bool = False

    def __post_init__(self):
        """
        Validate configuration after initialization
        
        Raises:
            ConfigError: If button function is invalid
        """
        try:
            ButtonFunction(self.function)
        except ValueError:
            valid_functions = [f.value for f in ButtonFunction]
            raise ConfigError(
                f"Invalid button function: {self.function}. "
                f"Must be one of: {', '.join(valid_functions)}"
            )

        # Validate pin number is positive
        if not isinstance(self.pin, int) or self.pin < 0:
            raise ConfigError(f"Pin must be a positive integer, got {self.pin}")
        
        if self.bounce_time <= 0:
            raise ConfigError(f"Bounce time must be positive, got {self.bounce_time}")
        
        if self.hold_time is not None and self.hold_time < 0:
            raise ConfigError(f"Hold time cannot be negative, got {self.hold_time}")

