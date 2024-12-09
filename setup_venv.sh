#!/bin/bash

VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"

# Create the virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment."
    exit 1
  fi
else
  echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
# /bin for Mac, /Scripts for Windows
source "$VENV_DIR/bin/activate" || { echo "Error: Failed to activate virtual environment."; exit 1; }

# Install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
  echo "Installing dependencies from $REQUIREMENTS_FILE..."
  pip install --no-cache-dir -r "$REQUIREMENTS_FILE"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    deactivate
    exit 1
  fi
else
  echo "Error: $REQUIREMENTS_FILE not found."
  deactivate
  exit 1
fi

echo "Setup complete. Virtual environment is ready."