#!/bin/bash

# Kreeda Backend Entrypoint Script
# NoSQL version - DynamoDB ready

set -e

echo "🏏 Starting Kreeda Backend..."

# Check if DynamoDB Local is available
if [ -n "$DYNAMODB_ENDPOINT_URL" ]; then
    echo "⏳ Waiting for DynamoDB Local..."
    while ! curl -s "$DYNAMODB_ENDPOINT_URL/" >/dev/null 2>&1; do
        echo "  DynamoDB Local is unavailable - sleeping"
        sleep 2
    done
    echo "✅ DynamoDB Local is ready!"
fi

echo "🚀 Starting API server..."
# Start the FastAPI application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
