# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

import yaml
import logging
from logging.handlers import RotatingFileHandler
from pathlib          import Path
from typing           import Any, Dict
from .exceptions      import ConfigError

class Config:
    """Configuration handler for PiHole Display"""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        """Ensure singleton instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize configuration if not already loaded"""
        if not self._config:
            self._load_config()
            self._setup_logging()

    def _load_config(self) -> None:
        """Load configuration from yaml file"""
        try:
            # Get project root directory (parent of src)
            root_dir = Path(__file__).parent.parent.parent
            config_file = root_dir / 'config' / 'config.yaml'

            with open(config_file, 'r') as f:
                self._config = yaml.safe_load(f)
        except Exception as e:
            raise ConfigError(f"Failed to load config: {str(e)}")

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        try:
            log_config = self._config['logging']
            root_dir = Path(__file__).parent.parent.parent
            log_dir = root_dir / 'log'
            log_dir.mkdir(exist_ok=True)

            logging.basicConfig(
                level=getattr(logging, log_config['level']),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    RotatingFileHandler(
                        log_dir / log_config['file'],
                        maxBytes=log_config['max_bytes'],
                        backupCount=log_config['backup_count']
                    )
                ]
            )
        except Exception as e:
            raise ConfigError(f"Failed to setup logging: {str(e)}")

    @property
    def display(self) -> Dict[str, Any]:
        """Get display configuration"""
        return self._config['display']

    @property
    def buttons(self) -> Dict[str, Any]:
        """Get buttons configuration"""
        return self._config['buttons']

    @property
    def paths(self) -> Dict[str, Any]:
        """Get paths configuration"""
        return self._config['paths']

    @property
    def timing(self) -> Dict[str, Any]:
        """Get timing configuration"""
        return self._config['timing']

    @property
    def logging(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self._config['logging']

    @property
    def button_functions(self) -> Dict[str, str]:
        """Get button functions enumeration"""
        return self._config['button_functions']

