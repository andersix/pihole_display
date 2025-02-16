# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

from enum    import Enum
from .config import Config

# Load configuration
config = Config()

class ButtonFunction(Enum):
    """Enumeration of button functions from config"""
    BRIGHTNESS_SYSTEM = config.button_functions['brightness_system']
    UPDATE_SELECT = config.button_functions['update_select']
    CONFIRM_1 = config.button_functions['confirm_1']
    CONFIRM_2 = config.button_functions['confirm_2']

# Timing constants
CONFIRMATION_TIMEOUT = config.timing['confirmation_timeout']
FEEDBACK_DELAY = config.timing['feedback_delay']

# Button hold thresholds
SYSTEM_CONTROL_HOLD = float(config.buttons['1']['hold_time'])
UPDATE_SELECT_HOLD = float(config.buttons['2']['hold_time'])

# Paths
PATHS = config.paths
