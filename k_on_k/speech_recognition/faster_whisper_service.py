"""
Faster-Whisper-based speech recognition for Kitten on Keys.
Uses the faster-whisper package (whisper.cpp port) for low-latency streaming transcription.
"""

import logging
from typing import Dict, Any, List, Optional, Callable

import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class FasterWhisperService:
    """
    Service for speech recognition using the faster-whisper library.
    Provides lower-latency, streaming transcription.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the faster-whisper service.

        Args:
            config: Application configuration dict
        """
        fw_config = config.get("speech_recognition", {}).get("faster_whisper", {})
        self.model_name = fw_config.get("model_name", "openai/whisper-large-v3-turbo")
        self.device = fw_config.get("device", "cpu")
        self.compute_type = fw_config.get("compute_type", "default")
        self.chunk_length_s = fw_config.get("chunk_length_s", 1.0)
        self.beam_size = fw_config.get("beam_size", None)

        self.language = config.get("general", {}).get("language", "en-US")[:2]
        
        # Load the faster-whisper model
        logger.info(f"Loading faster-whisper model: {self.model_name} on {self.device} (compute_type={self.compute_type})")
        self.model = WhisperModel(
            self.model_name,
            device=self.device,
            compute_type=self.compute_type,
        )
        self.is_loaded = True
        self.last_transcript = ""

        # Callback for on_transcription
        self.on_transcription: Optional[Callable[[str], None]] = None
        self.on_command: Optional[Callable[[str], None]] = None

    def process_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """
        Process a chunk of audio data and return any new transcription text.

        Args:
            audio_data: NumPy array of audio samples (mono)

        Returns:
            New transcription text, or None if no new text
        """
        try:
            # Run streaming transcription on the chunk
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=self.beam_size or 5,
                language=self.language,
                step=self.chunk_length_s,
            )
            combined = "".join([seg.text for seg in segments]).strip()
            if combined and combined != self.last_transcript:
                # Extract new part
                new_text = combined[len(self.last_transcript):].strip()
                self.last_transcript = combined
                return new_text
            return None
        except Exception as e:
            logger.error(f"Error in faster-whisper transcription: {e}")
            return None

    def reset(self):
        """Reset transcription state to start fresh."""
        self.last_transcript = ""

    def detect_commands(self, text: str, trigger_phrases: List[str]) -> Optional[str]:
        """
        Detect trigger phrases in the text, identical to WhisperService.
        """
        if not text:
            return None
        lower = text.lower()
        for phrase in trigger_phrases:
            if phrase.lower() in lower:
                return phrase
        return None

    def is_available(self) -> bool:
        """
        Check if the model is loaded and ready.
        """
        return getattr(self, "is_loaded", False) 