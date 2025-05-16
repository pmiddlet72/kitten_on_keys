"""Speech recognition package for Kitten on Keys."""

from k_on_k.speech_recognition.service import SpeechRecognitionService
from k_on_k.speech_recognition.faster_whisper_service import FasterWhisperService

__all__ = ["SpeechRecognitionService", "FasterWhisperService"]
