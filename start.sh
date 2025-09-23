#!/bin/bash

# Make sure pip packages are in PATH
export PATH="$HOME/.local/bin:$PATH"

# Run database migrations
python -m alembic upgrade head

# Start the application
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}