#!/bin/bash

# Kreeda Backend - Quick Setup Script

set -e

echo "🚀 Kreeda Backend Setup"
echo "======================="

# Check Python version
echo "📦 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $python_version detected"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-test.txt
echo "✅ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Create logs directory
mkdir -p logs
echo "✅ Logs directory created"

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start PostgreSQL and Redis services"
echo "3. Run: source .venv/bin/activate"
echo "4. Run: alembic upgrade head"
echo "5. Run: uvicorn src.main:app --reload"
echo ""
echo "Or use Docker:"
echo "  docker-compose up -d"
echo ""
echo "API Documentation:"
echo "  http://localhost:8000/api/docs"
echo ""
