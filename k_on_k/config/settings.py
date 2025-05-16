"""
Configuration settings for Kitten on Keys
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any

import yaml

logger = logging.getLogger(__name__)

# Default configuration paths
CONFIG_DIR = Path.home() / ".kitten_on_keys"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def get_default_config() -> Dict[str, Any]:
    """
    Return the default configuration settings.
    
    Returns:
        Dict containing default configuration values
    """
    return {
        "general": {
            "wake_word": "k.o.k.",
            "language": "en-US",
            "debug": False,
        },
        "hotkeys": {
            "toggle_dictation": "ctrl+alt+d",
        },
        "audio": {
            "sample_rate": 16000,
            "chunk_size": 1024,
            "channels": 1,
            "device_index": None,  # None means default device
        },
        "speech_recognition": {
            # Choose the STT engine: whisper or faster-whisper
            "engine": "faster-whisper",
            "model": "turbo",  # Options for whisper: tiny, base, small, medium, large, turbo
            # Settings for faster-whisper engine
            "faster_whisper": {
                "model_name": "openai/whisper-large-v3-turbo",
                "device": "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu",
                "compute_type": "int8_float16",  # Options: int8, int16, int8_float16, default
                "chunk_length_s": 1.0,
                "beam_size": 5
            },
            # Mapping of voice commands to punctuation or formatting
            "punctuation_commands": {
                "period": ".",
                "comma": ",",
                "question mark": "?",
                "exclamation point": "!",
                "new line": "\n",
                "dash": "-",
                "semicolon": ";",
                "colon": ":",
                "open parenthesis": "(",
                "close parenthesis": ")",
                "open bracket": "[",
                "close bracket": "]",
                "open curly brace": "{",
                "close curly brace": "}",
                "open quote": "\"",
                "close quote": "\""
            },
            "trigger_phrases": [
                "k.o.k. start",
                "k.o.k. stop",
                "k.o.k. pause",
                "k.o.k. resume",
            ],
        },
        "text_insertion": {
            "capitalize_sentences": True,
            "add_punctuation": True,
            "auto_spacing": True,
        },
        "daemon": {
            "autostart": False,
            "notifications": True,
        },
    }


def load_config() -> Dict[str, Any]:
    """
    Load configuration from file or create default if it doesn't exist.
    
    Returns:
        Dict containing configuration values
    """
    # Create config directory if it doesn't exist
    CONFIG_DIR.mkdir(exist_ok=True)
    
    # If config file doesn't exist, create it with defaults
    if not CONFIG_FILE.exists():
        default_config = get_default_config()
        save_config(default_config)
        return default_config
    
    # Load existing config
    try:
        with open(CONFIG_FILE, "r") as f:
            config = yaml.safe_load(f)
        
        # Update with any missing default values
        default_config = get_default_config()
        config = _merge_configs(config, default_config)
        
        return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        logger.info("Using default configuration")
        return get_default_config()


def save_config(config: Dict[str, Any]) -> bool:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dict to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        return False


def _merge_configs(user_config: Dict[str, Any], default_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge user config with default config, ensuring all required keys exist.
    
    Args:
        user_config: User configuration dict
        default_config: Default configuration dict
        
    Returns:
        Merged configuration dict
    """
    result = user_config.copy()
    
    for key, value in default_config.items():
        if key not in result:
            result[key] = value
        elif isinstance(value, dict) and isinstance(result[key], dict):
            result[key] = _merge_configs(result[key], value)
    
    return result
