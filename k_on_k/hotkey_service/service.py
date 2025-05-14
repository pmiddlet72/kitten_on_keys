"""
Hotkey service for Kitten on Keys.
Handles global hotkey registration and events.
"""

import logging
import threading
from typing import Dict, Any, Callable, Optional

from pynput import keyboard

logger = logging.getLogger(__name__)


class HotkeyService:
    """
    Service for handling global hotkeys.
    Registers and manages hotkeys for controlling the application.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the hotkey service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.hotkey_config = config["hotkeys"]
        
        # Hotkey mappings
        self.toggle_dictation_key = self.hotkey_config["toggle_dictation"]
        
        # State
        self.is_running = False
        self.listener = None
        
        # Callbacks
        self.on_dictation_hotkey: Optional[Callable[[], None]] = None
        
        # Parse hotkey combinations
        self.hotkey_combinations = self._parse_hotkeys()
    
    def start(self):
        """Start the hotkey service and register global hotkeys."""
        if self.is_running:
            return
            
        logger.info("Starting hotkey service")
        self.is_running = True
        
        # Start keyboard listener in a separate thread
        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.listener.start()
    
    def stop(self):
        """Stop the hotkey service and unregister global hotkeys."""
        if not self.is_running:
            return
            
        logger.info("Stopping hotkey service")
        self.is_running = False
        
        # Stop listener
        if self.listener:
            self.listener.stop()
            self.listener = None
    
    def _parse_hotkeys(self) -> Dict[str, set]:
        """
        Parse hotkey combinations from configuration.
        
        Returns:
            Dictionary of hotkey name to set of keys
        """
        hotkeys = {}
        
        # Parse toggle dictation hotkey
        toggle_keys = self._parse_hotkey_combination(self.toggle_dictation_key)
        if toggle_keys:
            hotkeys["toggle_dictation"] = toggle_keys
        
        return hotkeys
    
    def _parse_hotkey_combination(self, hotkey_str: str) -> set:
        """
        Parse a hotkey string (e.g., "ctrl+alt+d") into a set of keys.
        
        Args:
            hotkey_str: String representation of hotkey combination
            
        Returns:
            Set of key objects
        """
        keys = set()
        
        if not hotkey_str:
            return keys
            
        parts = hotkey_str.lower().split("+")
        for part in parts:
            part = part.strip()
            
            if part == "ctrl":
                keys.add(keyboard.Key.ctrl)
            elif part == "alt":
                keys.add(keyboard.Key.alt)
            elif part == "shift":
                keys.add(keyboard.Key.shift)
            elif part == "cmd" or part == "win":
                keys.add(keyboard.Key.cmd)
            elif len(part) == 1:
                keys.add(keyboard.KeyCode.from_char(part))
            else:
                try:
                    key_attr = getattr(keyboard.Key, part, None)
                    if key_attr:
                        keys.add(key_attr)
                except AttributeError:
                    logger.warning(f"Unknown key: {part}")
        
        return keys
    
    # Track currently pressed keys
    current_keys = set()
    
    def _on_key_press(self, key):
        """
        Handle key press events.
        
        Args:
            key: The key that was pressed
        """
        if not self.is_running:
            return
        
        try:
            # Add key to currently pressed keys
            self.current_keys.add(key)
            
            # Check for hotkey combinations
            self._check_hotkeys()
                
        except Exception as e:
            logger.error(f"Error in key press handler: {str(e)}")
    
    def _on_key_release(self, key):
        """
        Handle key release events.
        
        Args:
            key: The key that was released
        """
        if not self.is_running:
            return
            
        try:
            # Remove key from currently pressed keys
            self.current_keys.discard(key)
            
        except Exception as e:
            logger.error(f"Error in key release handler: {str(e)}")
    
    def _check_hotkeys(self):
        """Check if any registered hotkey combinations are pressed."""
        if not self.is_running:
            return
        
        # Check toggle dictation hotkey
        if "toggle_dictation" in self.hotkey_combinations:
            toggle_keys = self.hotkey_combinations["toggle_dictation"]
            if toggle_keys.issubset(self.current_keys) and self.on_dictation_hotkey:
                logger.debug("Toggle dictation hotkey pressed")
                # Clear current keys to prevent multiple triggers
                self.current_keys.clear()
                # Call callback
                self.on_dictation_hotkey()
    
    def set_hotkey(self, name: str, hotkey_str: str) -> bool:
        """
        Set a new hotkey combination.
        
        Args:
            name: Name of the hotkey (e.g., "toggle_dictation")
            hotkey_str: String representation of hotkey combination
            
        Returns:
            True if successful, False otherwise
        """
        if not name or not hotkey_str:
            return False
            
        try:
            keys = self._parse_hotkey_combination(hotkey_str)
            if keys:
                self.hotkey_combinations[name] = keys
                
                # Update config
                self.hotkey_config[name] = hotkey_str
                
                logger.info(f"Set hotkey {name} to {hotkey_str}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error setting hotkey {name}: {str(e)}")
            return False 