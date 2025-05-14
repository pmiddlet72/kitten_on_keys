"""
Daemon service for Kitten on Keys.
Handles running the application as a background service.
"""

import logging
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DaemonService:
    """
    Service for managing the application as a background daemon.
    Handles startup, shutdown, and notifications.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the daemon service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.daemon_config = config["daemon"]
        
        # Daemon settings
        self.autostart = self.daemon_config["autostart"]
        self.notifications = self.daemon_config["notifications"]
        
        # State
        self.is_running = False
        self.pid_file = Path.home() / ".kitten_on_keys" / "kok.pid"
    
    def start(self):
        """Start the daemon service."""
        if self.is_running:
            return
            
        logger.info("Starting daemon service")
        self.is_running = True
        
        # Create PID file
        self._create_pid_file()
        
        # Show notification if enabled
        if self.notifications:
            self._show_notification("Kitten on Keys", "Dictation service started")
    
    def stop(self):
        """Stop the daemon service."""
        if not self.is_running:
            return
            
        logger.info("Stopping daemon service")
        self.is_running = False
        
        # Remove PID file
        self._remove_pid_file()
        
        # Show notification if enabled
        if self.notifications:
            self._show_notification("Kitten on Keys", "Dictation service stopped")
    
    def _create_pid_file(self):
        """Create a PID file to track the running daemon."""
        try:
            with open(self.pid_file, "w") as f:
                f.write(str(os.getpid()))
        except Exception as e:
            logger.error(f"Error creating PID file: {str(e)}")
    
    def _remove_pid_file(self):
        """Remove the PID file when daemon stops."""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception as e:
            logger.error(f"Error removing PID file: {str(e)}")
    
    def _show_notification(self, title: str, message: str):
        """
        Show a desktop notification.
        
        Args:
            title: Notification title
            message: Notification message
        """
        try:
            # Try to use notify-send (Linux)
            subprocess.run(
                ["notify-send", title, message],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            logger.error(f"Error showing notification: {str(e)}")
    
    def setup_autostart(self, enable: bool) -> bool:
        """
        Configure application to start automatically on login.
        
        Args:
            enable: Whether to enable or disable autostart
            
        Returns:
            True if successful, False otherwise
        """
        try:
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_file = autostart_dir / "kitten_on_keys.desktop"
            
            if enable:
                # Create autostart directory if it doesn't exist
                autostart_dir.mkdir(exist_ok=True, parents=True)
                
                # Get script path
                script_path = sys.argv[0]
                
                # Create desktop entry file
                desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Kitten on Keys
Comment=Speech-to-text dictation service
Exec=python3 {script_path}
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
"""
                
                with open(autostart_file, "w") as f:
                    f.write(desktop_entry)
                    
                # Update config
                self.autostart = True
                self.daemon_config["autostart"] = True
                
                logger.info("Autostart enabled")
                return True
                
            else:
                # Remove autostart file if it exists
                if autostart_file.exists():
                    autostart_file.unlink()
                
                # Update config
                self.autostart = False
                self.daemon_config["autostart"] = False
                
                logger.info("Autostart disabled")
                return True
                
        except Exception as e:
            logger.error(f"Error setting up autostart: {str(e)}")
            return False
    
    @staticmethod
    def is_daemon_running() -> Optional[int]:
        """
        Check if the daemon is already running.
        
        Returns:
            PID of running daemon if found, None otherwise
        """
        pid_file = Path.home() / ".kitten_on_keys" / "kok.pid"
        
        if not pid_file.exists():
            return None
            
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
                
            # Check if process with this PID exists
            try:
                os.kill(pid, 0)  # Signal 0 doesn't kill the process but checks if it exists
                return pid
            except OSError:
                # Process doesn't exist
                return None
                
        except Exception:
            return None 