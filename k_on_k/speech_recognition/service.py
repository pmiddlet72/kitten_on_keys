"""
Speech recognition service for Kitten on Keys.
This service coordinates speech-to-text functionality and manages the underlying models.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Callable, Union

import numpy as np

from k_on_k.speech_recognition.whisper_service import WhisperService

logger = logging.getLogger(__name__)


class SpeechRecognitionService:
    """
    Main service for speech recognition functionality.
    Coordinates the underlying speech-to-text models and handles transcription.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the speech recognition service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.stt_config = config["speech_recognition"]
        self.model_type = self.stt_config["model"]
        self.trigger_phrases = self.stt_config["trigger_phrases"]
        
        # State
        self.is_running = False
        self.is_listening = False
        self.processing_thread = None
        self.audio_buffer = []
        self.lock = threading.Lock()
        
        # Model instances
        self.whisper_service = None
        self.active_model = None
        
        # Callback for transcribed text
        self.on_transcription: Optional[Callable[[str], None]] = None
        self.on_command: Optional[Callable[[str], None]] = None
    
    def start(self):
        """Start the speech recognition service."""
        if self.is_running:
            return
            
        logger.info("Starting speech recognition service")
        self.is_running = True
        
        # Initialize model based on configuration
        self._initialize_model()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_audio, daemon=True)
        self.processing_thread.start()
    
    def stop(self):
        """Stop the speech recognition service."""
        if not self.is_running:
            return
            
        logger.info("Stopping speech recognition service")
        self.is_running = False
        self.is_listening = False
        
        # Wait for processing thread to end
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
    
    def _initialize_model(self):
        """Initialize the speech-to-text model based on configuration."""
        if self.model_type == "whisper":
            logger.info("Initializing Whisper model")
            self.whisper_service = WhisperService(self.config)
            self.active_model = self.whisper_service
        else:
            logger.warning(f"Unsupported model type: {self.model_type}, falling back to Whisper")
            self.whisper_service = WhisperService(self.config)
            self.active_model = self.whisper_service
    
    def process_audio(self, audio_data: np.ndarray):
        """
        Process incoming audio data.
        
        Args:
            audio_data: Audio data as numpy array
        """
        if not self.is_running:
            return
            
        with self.lock:
            self.audio_buffer.append(audio_data)
    
    def _process_audio(self):
        """
        Background thread to process audio data.
        This runs continuously in the background when the service is running.
        """
        while self.is_running:
            try:
                # Check if we have audio data to process
                if not self.is_listening or not self.active_model:
                    time.sleep(0.1)
                    continue
                
                # Process audio data in chunks
                with self.lock:
                    if not self.audio_buffer:
                        time.sleep(0.1)
                        continue
                        
                    # Get a copy of the buffer and clear it
                    buffer_copy = self.audio_buffer.copy()
                    self.audio_buffer = []
                
                # Process audio data with active model
                if buffer_copy:
                    audio_data = np.concatenate(buffer_copy)
                    transcript = self.active_model.process_audio(audio_data)
                    
                    if transcript:
                        # Check for trigger commands
                        command = self.active_model.detect_commands(transcript, self.trigger_phrases)
                        
                        if command and self.on_command:
                            self.on_command(command)
                        elif self.on_transcription:
                            self.on_transcription(transcript)
                
            except Exception as e:
                logger.error(f"Error processing audio data: {str(e)}")
                time.sleep(0.1)
    
    def start_listening(self):
        """Start listening for speech."""
        if not self.is_running or not self.active_model:
            return
            
        logger.info("Starting speech recognition listening")
        self.is_listening = True
        
        # Reset model state
        if hasattr(self.active_model, "reset"):
            self.active_model.reset()
    
    def stop_listening(self):
        """Stop listening for speech."""
        if not self.is_listening:
            return
            
        logger.info("Stopping speech recognition listening")
        self.is_listening = False
        
        # Clear buffer
        with self.lock:
            self.audio_buffer = [] 