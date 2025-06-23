#!/usr/bin/env bash
set -e

# Navigate to the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Pull the latest code
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    git pull --ff-only
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install required Python packages
pip install -r requirements.txt

# Start the Flask application
python app/cut_optimizer_app.py

