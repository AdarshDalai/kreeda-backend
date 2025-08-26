#!/bin/bash

# Kreeda Backend Entrypoint Script
# Wait for database and start the application

set -e

echo "🏏 Starting Kreeda Backend..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
  echo "  Database is unavailable - sleeping"
  sleep 2
done

echo "✅ Database is ready!"

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head

echo "🚀 Starting API server..."
# Start the FastAPI application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
