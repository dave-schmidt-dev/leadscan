#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "🚀 Setting up LeadScan..."

# Check for Python 3

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env with your GOOGLE_PLACES_API_KEY before running."
    exit 1
fi

# Check if venv is valid/exists
if [ -d "venv" ]; then
    # Check if the venv path matches the current directory
    VENV_PATH=$(grep "VIRTUAL_ENV=" venv/bin/activate | head -1 | cut -d'=' -f2 | tr -d '"')
    CURRENT_PATH=$(pwd)
    if [[ "$VENV_PATH" != "$CURRENT_PATH"* ]]; then
        echo "🔄 Old virtual environment detected (path mismatch). Recreating..."
        rm -rf venv
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating fresh virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
# echo "🔌 Activating virtual environment..."
# source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
./venv/bin/python3 -m pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies from requirements.txt..."
./venv/bin/pip install -r requirements.txt

# Run the application
echo "✅ Setup complete! Starting LeadScan..."
echo "🌐 Open http://127.0.0.1:5000 in your browser"
./venv/bin/python3 run.py
