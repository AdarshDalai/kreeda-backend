#!/bin/bash
# Development server startup script

set -e

echo "🚀 Starting Kreeda Backend Development Server"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements/development.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your actual configuration"
fi

# Start the development server
echo "Starting FastAPI development server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug