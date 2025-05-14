"""
Whisper-based speech recognition for Kitten on Keys.
Uses OpenAI's Whisper model for efficient and accurate speech recognition.
"""

import logging
import os
import time
from typing import Dict, Any, List, Optional, Callable

import numpy as np
import torch
import whisper

logger = logging.getLogger(__name__)


class WhisperService:
    """
    Service for speech recognition using OpenAI's Whisper model.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Whisper service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.whisper_config = config["speech_recognition"]["whisper"]
        self.model_size = self.whisper_config["model_size"]
        self.device = self.whisper_config["device"]
        
        # State
        self.model = None
        self.is_loaded = False
        self.language = config["general"]["language"]
        self.audio_buffer = []
        self.last_transcript = ""
        
        # Load model at initialization
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            logger.info(f"Loading Whisper model (size: {self.model_size}, device: {self.device})")
            start_time = time.time()
            
            self.model = whisper.load_model(
                self.model_size, 
                device=self.device
            )
            
            load_time = time.time() - start_time
            logger.info(f"Whisper model loaded in {load_time:.2f} seconds")
            self.is_loaded = True
            
        except Exception as e:
            logger.error(f"Error loading Whisper model: {str(e)}")
            self.is_loaded = False
    
    def process_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """
        Process audio data and return transcription.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Transcription text if successful, None otherwise
        """
        if not self.is_loaded:
            logger.warning("Whisper model not loaded, cannot process audio")
            return None
        
        try:
            # Add audio to buffer
            self.audio_buffer.append(audio_data)
            
            # Convert buffer to audio data for Whisper
            audio = np.concatenate(self.audio_buffer)
            
            # Transcribe audio
            result = self.model.transcribe(
                audio,
                language=self.language[:2],  # Use first 2 chars (e.g., "en" from "en-US")
                fp16=(self.device == "cuda"),
            )
            
            transcript = result["text"].strip()
            
            # Only return new part of transcript
            if transcript and transcript != self.last_transcript:
                new_part = transcript[len(self.last_transcript):].strip()
                self.last_transcript = transcript
                return new_part
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing audio with Whisper: {str(e)}")
            return None
    
    def reset(self):
        """Reset the transcription state."""
        self.audio_buffer = []
        self.last_transcript = ""
    
    def detect_commands(self, text: str, trigger_phrases: List[str]) -> Optional[str]:
        """
        Detect if the text contains trigger commands.
        
        Args:
            text: Transcribed text
            trigger_phrases: List of trigger phrases to detect
            
        Returns:
            Detected command or None
        """
        if not text:
            return None
            
        lower_text = text.lower()
        
        for phrase in trigger_phrases:
            if phrase.lower() in lower_text:
                return phrase
                
        return None
    
    def is_available(self) -> bool:
        """
        Check if the Whisper service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        return self.is_loaded
