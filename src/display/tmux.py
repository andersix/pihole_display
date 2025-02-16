# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

import subprocess
import logging
from pathlib            import Path
from ..utils.exceptions import DisplayError
from ..utils.constants  import PATHS
from ..utils.config     import Config

logger = logging.getLogger('DisplayController')

class TMuxController:
    """Manages tmux sessions and windows"""
    
    def __init__(self):
        """Initialize TMux controller with configuration"""
        self.config = Config().display['tmux']
        self.padd_path = PATHS['padd_script']
        self.session_name = self.config['session_name']
        self._verify_tmux_available()

    def _verify_tmux_available(self) -> None:
        """Verify tmux is installed and available"""
        try:
            subprocess.run(['tmux', '-V'], capture_output=True, check=True)
            logger.debug("Tmux is available")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            error_msg = "Tmux is not available on the system"
            logger.critical(error_msg)
            raise DisplayError(error_msg)
    
    def _run_tmux_command(self, command: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """
        Run a tmux command with proper error handling
        
        Args:
            command: List of command components
            check: Whether to raise on non-zero exit
            
        Returns:
            CompletedProcess instance
        """
        try:
            full_command = ['tmux'] + command
            logger.debug(f"Running tmux command: {' '.join(full_command)}")
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=check
            )
            return result
        except subprocess.SubprocessError as e:
            error_msg = f"Tmux command failed: {str(e)}"
            logger.error(error_msg)
            if check:
                raise DisplayError(error_msg)
            return e.returncode

    def has_session(self) -> bool:
        """Check if session exists"""
        try:
            result = self._run_tmux_command(
                ['has-session', '-t', self.session_name],
                check=False
            )
            exists = result.returncode == 0
            logger.debug(f"Session {self.session_name} exists: {exists}")
            return exists
        except Exception:
            logger.error(f"Error checking session {self.session_name}")
            return False

    def switch_window(self, window_name: str) -> None:
        """
        Switch to specified window
        
        Args:
            window_name: Name of window to switch to
        """
        try:
            # Verify window exists
            result = self._run_tmux_command(
                ['list-windows', '-t', self.session_name],
                check=False
            )
            
            if result.returncode != 0 or not any(
                window_name in line for line in result.stdout.splitlines()
            ):
                raise DisplayError(f"Window {window_name} not found")
            
            # Perform switch
            self._run_tmux_command([
                'select-window',
                '-t', f'{self.session_name}:{window_name}'
            ])
            
            # Verify switch
            current = self._run_tmux_command([
                'display-message',
                '-p', '#W'  # Current window name
            ])
            
            if current.stdout.strip() != window_name:
                raise DisplayError("Window switch verification failed")
                
            logger.debug(f"Successfully switched to window: {window_name}")
            
        except Exception as e:
            error_msg = f"Failed to switch to window {window_name}: {str(e)}"
            logger.error(error_msg)
            raise DisplayError(error_msg)

