#!/bin/bash
# Setup script for Kitten on Keys

set -e  # Exit on error

echo "Setting up Kitten on Keys..."

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "Conda is not installed. Please install Conda first."
    echo "Visit https://docs.conda.io/projects/miniconda/en/latest/miniconda-install.html"
    exit 1
fi

# Create conda environment
echo "Creating conda environment with Python 3.13..."
conda env create -f environment.yml

# Activate environment
echo "Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate kitten_on_keys

# Install dependencies with Poetry
echo "Installing project dependencies with Poetry..."
poetry install

echo ""
echo "Setup complete! To run Kitten on Keys:"
echo "1. Activate the conda environment: conda activate kitten_on_keys"
echo "2. Run the application: poetry run kitten-on-keys"
echo ""
echo "You can also create a desktop entry for easy access by running:"
echo "python -c \"from k_on_k.daemon.service import DaemonService; DaemonService({}).setup_autostart(True)\"" 