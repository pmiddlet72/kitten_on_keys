#!/usr/bin/env python3
"""
Kitten on Keys (KoK) - Main Entry Point
A speech-to-text dictation application for Linux Mint/Cinnamon
"""

import logging
import signal
import sys
import threading
from pathlib import Path

from k_on_k.audio_capture.service import AudioCaptureService
from k_on_k.config.settings import load_config
from k_on_k.daemon.service import DaemonService
from k_on_k.hotkey_service.service import HotkeyService
from k_on_k.speech_recognition.service import SpeechRecognitionService
from k_on_k.text_insertion.service import TextInsertionService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path.home() / ".kitten_on_keys" / "kok.log"),
    ],
)
logger = logging.getLogger("kitten_on_keys")


class KittenOnKeys:
    """Main application class that coordinates all services."""

    def __init__(self):
        """Initialize application components."""
        self.running = False
        self.config = load_config()
        # If debug mode, set both root and our logger to DEBUG so handlers will emit debug records
        if self.config.get("general", {}).get("debug", False):
            logging.root.setLevel(logging.DEBUG)
            logger.setLevel(logging.DEBUG)
        
        # Initialize all services
        self.audio_service = AudioCaptureService(self.config)
        self.stt_service = SpeechRecognitionService(self.config)
        self.text_service = TextInsertionService(self.config)
        self.hotkey_service = HotkeyService(self.config)
        self.daemon_service = DaemonService(self.config)
        
        # Set up event handlers
        self.hotkey_service.on_dictation_hotkey = self.toggle_dictation
        # Wrap transcription callback to log and then insert text
        def _handle_transcription(text):
            logger.info(f"Transcribed text: {text}")
            self.text_service.insert_text(text)
        self.stt_service.on_transcription = _handle_transcription
        self.audio_service.on_audio_data = self.stt_service.process_audio
        
        # Handle signals
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def start(self):
        """Start all services and enter the main loop."""
        try:
            logger.info("Starting Kitten on Keys")
            self.running = True
            
            # Start services in correct order
            self.daemon_service.start()
            self.text_service.start()
            self.stt_service.start()
            self.audio_service.start()
            
            # Start hotkey service last as it may block
            self.hotkey_service.start()
            
            # Enter main loop
            logger.info("Kitten on Keys started successfully")
            while self.running:
                signal.pause()
                
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            self.stop()

    def stop(self, signum=None, frame=None):
        """Stop all services gracefully."""
        if not self.running:
            return
            
        logger.info("Stopping Kitten on Keys")
        self.running = False
        
        # Stop services in reverse order
        self.hotkey_service.stop()
        self.audio_service.stop()
        self.stt_service.stop()
        self.text_service.stop()
        self.daemon_service.stop()
        
        logger.info("Kitten on Keys stopped")

    def toggle_dictation(self):
        """Toggle dictation mode on/off."""
        if self.audio_service.is_recording:
            logger.info("Stopping dictation")
            # Stop capturing audio and transcription
            self.audio_service.stop_recording()
            self.stt_service.stop_listening()
        else:
            logger.info("Starting dictation")
            # Begin capturing audio and processing transcription
            self.stt_service.start_listening()
            self.audio_service.start_recording()


def main():
    """Application entry point."""
    # Create config directory if it doesn't exist
    config_dir = Path.home() / ".kitten_on_keys"
    config_dir.mkdir(exist_ok=True)
    
    # Start the application
    app = KittenOnKeys()
    app.start()


if __name__ == "__main__":
    main()
