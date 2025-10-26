#!/bin/bash
# Database initialization script for Kreeda backend
# This script starts Docker services and runs Alembic migrations

set -e  # Exit on error

echo "🏏 Kreeda Backend - Database Initialization"
echo "==========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Start Docker services
echo "🚀 Starting Docker services (PostgreSQL + Redis)..."
docker-compose up -d db redis

echo ""
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Check if PostgreSQL is accepting connections
until docker-compose exec -T db pg_isready -U kreeda_user > /dev/null 2>&1; do
    echo "   Still waiting for PostgreSQL..."
    sleep 2
done

echo "✅ PostgreSQL is ready"
echo ""

# Generate Alembic migration
echo "📝 Generating Alembic migration..."
docker-compose run --rm app alembic revision --autogenerate -m "Create cricket module schema with all tables"

echo ""
echo "🔄 Running migrations..."
docker-compose run --rm app alembic upgrade head

echo ""
echo "✅ Database initialization complete!"
echo ""
echo "Next steps:"
echo "  - Start the app: docker-compose up app"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
