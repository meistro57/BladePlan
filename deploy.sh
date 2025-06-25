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
pip install --upgrade -r requirements.txt

# Parse command line arguments for mode
MODE="production"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dev)
            MODE="development"
            shift
            ;;
        --prod)
            MODE="production"
            shift
            ;;
        *)
            echo "Usage: $0 [--dev|--prod]"
            exit 1
            ;;
    esac
done

# Ensure required ForgeCore environment variables are set
REQUIRED_VARS=(FORGECORE_DB_HOST FORGECORE_DB_USER FORGECORE_DB_PASSWORD FORGECORE_DB_NAME)
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set" >&2
        exit 1
    fi
done

# Set Flask environment
export FLASK_ENV="$MODE"

# Start the Flask application
python app/cut_optimizer_app.py

