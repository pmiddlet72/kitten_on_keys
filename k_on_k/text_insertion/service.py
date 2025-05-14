"""
Text insertion service for Kitten on Keys.
Handles sending text to the currently active application.
"""

import logging
import re
import time
from typing import Dict, Any, Optional

from pynput.keyboard import Controller as KeyboardController, Key

logger = logging.getLogger(__name__)


class TextInsertionService:
    """
    Service for inserting text into the active application.
    Uses keyboard simulation to type text into the currently focused window.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the text insertion service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.text_config = config["text_insertion"]
        
        # Text processing options
        self.capitalize_sentences = self.text_config["capitalize_sentences"]
        self.add_punctuation = self.text_config["add_punctuation"]
        self.auto_spacing = self.text_config["auto_spacing"]
        
        # State
        self.is_running = False
        self.last_text_ends_with_space = True
        self.current_sentence_has_capital = False
        
        # Keyboard controller for typing
        self.keyboard = KeyboardController()
    
    def start(self):
        """Start the text insertion service."""
        if self.is_running:
            return
            
        logger.info("Starting text insertion service")
        self.is_running = True
    
    def stop(self):
        """Stop the text insertion service."""
        if not self.is_running:
            return
            
        logger.info("Stopping text insertion service")
        self.is_running = False
    
    def insert_text(self, text: str):
        """
        Insert text into the active application by simulating keyboard input.
        
        Args:
            text: Text to insert
        """
        if not self.is_running or not text:
            return
        
        logger.debug(f"Inserting text: {text}")
        
        # Process text before insertion
        processed_text = self._process_text(text)
        
        if processed_text:
            try:
                # Type text using the keyboard controller
                self.keyboard.type(processed_text)
                
                # Update state for next insertion
                self.last_text_ends_with_space = processed_text.endswith(" ")
                self.current_sentence_has_capital = not any(processed_text.endswith(x) for x in [".", "!", "?"])
                
            except Exception as e:
                logger.error(f"Error inserting text: {str(e)}")
    
    def _process_text(self, text: str) -> str:
        """
        Process text before insertion.
        Applies capitalization, punctuation, and spacing rules.
        
        Args:
            text: Raw text to process
            
        Returns:
            Processed text ready for insertion
        """
        if not text:
            return ""
        
        # Add space before text if needed
        if self.auto_spacing and not self.last_text_ends_with_space and not text.startswith((" ", ",", ".", "!", "?", ":", ";", ")", "]", "}")):
            text = " " + text
        
        # Capitalize first letter of sentences
        if self.capitalize_sentences and not self.current_sentence_has_capital:
            # If this is the start of a new sentence
            if self.last_text_ends_with_space or not self.auto_spacing:
                text = text[0].upper() + text[1:] if text else ""
                self.current_sentence_has_capital = True
        
        # Fix common spacing issues
        if self.auto_spacing:
            # Add space after punctuation if missing
            text = re.sub(r'([.!?:;,])([^\s\d])', r'\1 \2', text)
            
            # Remove space before punctuation
            text = re.sub(r'\s+([.!?:;,])', r'\1', text)
            
            # Ensure only one space between words
            text = re.sub(r'\s{2,}', ' ', text)
        
        return text
    
    def type_command(self, command: str):
        """
        Execute special typing commands.
        
        Args:
            command: Command to execute
        """
        if not self.is_running:
            return
            
        logger.debug(f"Executing typing command: {command}")
        
        # Handle various commands
        if command == "backspace":
            self.keyboard.press(Key.backspace)
            self.keyboard.release(Key.backspace)
        elif command == "delete":
            self.keyboard.press(Key.delete)
            self.keyboard.release(Key.delete)
        elif command == "new_line":
            self.keyboard.press(Key.enter)
            self.keyboard.release(Key.enter)
        # Add more commands as needed 