# Kitten on Keys (KoK)

A speech-to-text dictation application for Linux Mint/Cinnamon that enables voice dictation in any application.

## Features

- Global hotkey to start/stop dictation
- Voice command triggers ("K.o.K., start", "K.o.K., stop")
- Real-time dictation in any application with text input
- Runs as a daemon in the background
- Optimized for Linux Mint with Cinnamon desktop environment

## Requirements

- Python 3.13
- Linux Mint with Cinnamon desktop
- Microphone for audio input
- Conda for environment management

## Installation

### Using Conda (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/kitten_on_keys.git
cd kitten_on_keys

# Create and activate conda environment
conda env create -f environment.yml
conda activate kitten_on_keys

# Install project dependencies using Poetry
poetry install
```

### Alternative Method (venv)

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install using Poetry
poetry install
```

## Development Installation

To make the `kitten-on-keys` command available anywhere within your `kok` environment without affecting your global packages, install your project in "editable" mode:

```bash
# Activate the conda environment
conda activate kok

# Install the project into the current environment in editable mode
pip install -e .
```

Now you can run:

```bash
kitten-on-keys
```

from any directory, provided the `kok` environment is active and its `bin` is first on your `PATH`.  If needed, you can ensure that by placing this in your `~/.bashrc` after activating:

```bash
# Ensure conda env's bin comes first
export PATH="$CONDA_PREFIX/bin:$PATH"
```

## Usage

Start the daemon service:

```bash
# Make sure the conda environment is activated
conda activate kitten_on_keys

# Run the application
poetry run kitten-on-keys
```

Default hotkeys:
- Start/Stop dictation: Ctrl+Alt+D

You can customize hotkeys and other settings in the configuration file.

## Architecture

This project uses a vertical slice architecture to minimize dependencies between components:

- `audio_capture`: Manages microphone input and audio processing
- `speech_recognition`: Handles the STT models and transcription
- `text_insertion`: Manages sending text to active applications
- `hotkey_service`: Handles global hotkey registration and events
- `daemon`: Background service management
- `config`: Application configuration

## License

MIT

