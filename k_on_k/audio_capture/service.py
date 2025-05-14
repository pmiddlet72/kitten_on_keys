"""
Audio capture service for Kitten on Keys.
Handles microphone input and provides audio data to the speech recognition service.
"""

import logging
import queue
import threading
import time
from typing import Callable, Dict, Any, Optional

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


class AudioCaptureService:
    """
    Service for capturing audio from the microphone.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the audio capture service.
        
        Args:
            config: Application configuration dict
        """
        self.config = config
        self.audio_config = config["audio"]
        
        # Audio settings
        self.sample_rate = self.audio_config["sample_rate"]
        self.chunk_size = self.audio_config["chunk_size"]
        self.channels = self.audio_config["channels"]
        self.device_index = self.audio_config["device_index"]
        
        # State
        self.stream = None
        self.is_running = False
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.processing_thread = None
        
        # Callback for processing audio data
        self.on_audio_data: Optional[Callable[[np.ndarray], None]] = None
    
    def start(self):
        """Start the audio capture service."""
        if self.is_running:
            return
            
        logger.info("Starting audio capture service")
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.processing_thread.start()
    
    def stop(self):
        """Stop the audio capture service."""
        if not self.is_running:
            return
            
        logger.info("Stopping audio capture service")
        self.stop_recording()
        self.is_running = False
        
        # Wait for processing thread to end
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
    
    def start_recording(self):
        """Start recording audio from microphone."""
        if self.is_recording or not self.is_running:
            return
            
        logger.info("Starting audio recording")
        self.is_recording = True
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                channels=self.channels,
                dtype="float32",
                device=self.device_index,
                callback=self._audio_callback,
            )
            self.stream.start()
        except Exception as e:
            logger.error(f"Error starting audio stream: {str(e)}")
            self.is_recording = False
    
    def stop_recording(self):
        """Stop recording audio."""
        if not self.is_recording:
            return
            
        logger.info("Stopping audio recording")
        self.is_recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
    
    def _audio_callback(self, indata, frames, time_info, status):
        """
        Callback function for audio data from sounddevice.
        
        Args:
            indata: Input audio data
            frames: Number of frames
            time_info: Time information
            status: Status of the callback
        """
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Add audio data to queue
        if self.is_recording:
            audio_data = np.copy(indata[:, 0])  # Use first channel if stereo
            self.audio_queue.put(audio_data)
    
    def _process_queue(self):
        """Process audio data from the queue."""
        while self.is_running:
            try:
                # Get audio data from queue with timeout
                try:
                    audio_data = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Process audio data if callback is set
                if self.on_audio_data and self.is_recording:
                    self.on_audio_data(audio_data)
                
                # Mark task as done
                self.audio_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing audio data: {str(e)}")
                time.sleep(0.1)
    
    def list_audio_devices(self):
        """
        List available audio input devices.
        
        Returns:
            List of available audio input devices
        """
        devices = sd.query_devices()
        input_devices = [d for d in devices if d["max_input_channels"] > 0]
        return input_devices 