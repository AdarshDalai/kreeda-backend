# Database Setup Instructions

## Prerequisites
- Docker Desktop must be running
- All model files are already created

## Step-by-Step Setup

### 1. Start Docker Desktop
Open Docker Desktop application on your Mac and wait for it to start.

### 2. Start Database Services
```bash
# Start PostgreSQL and Redis
docker-compose up -d db redis

# Wait for PostgreSQL to be ready (about 10 seconds)
sleep 10

# Verify PostgreSQL is running
docker-compose exec db pg_isready -U kreeda_user
```

### 3. Generate and Run Migrations
```bash
# Generate migration from models
docker-compose run --rm app alembic revision --autogenerate -m "Create cricket module schema with all tables"

# Apply migration to database
docker-compose run --rm app alembic upgrade head
```

### 4. Verify Setup
```bash
# Check database tables
docker-compose exec db psql -U kreeda_user -d kreeda_db -c "\dt"

# Check PostgreSQL extensions
docker-compose exec db psql -U kreeda_user -d kreeda_db -c "\dx"
```

### 5. Start Full Application
```bash
# Start all services including the app
docker-compose up

# Or run in background
docker-compose up -d
```

## Quick Start (All-in-One)
```bash
# Make script executable
chmod +x scripts/init-db.sh

# Run initialization script
./scripts/init-db.sh
```

## Troubleshooting

### Docker not running
```
ERROR: Cannot connect to the Docker daemon
```
**Solution**: Start Docker Desktop application

### Port already in use
```
Error: port 5432 already allocated
```
**Solution**: Stop existing PostgreSQL or change port in docker-compose.yml

### Migration errors
```bash
# Reset and recreate database
docker-compose down -v
docker-compose up -d db redis
sleep 10
docker-compose run --rm app alembic upgrade head
```

## Database Schema Overview

### Created Tables (30+):
1. **Identity Layer**: `user_auth`, `user_profiles`, `sport_profiles`
2. **Cricket Profiles**: `cricket_player_profiles`
3. **Teams**: `teams`, `team_memberships`
4. **Matches**: `matches`, `match_officials`, `match_playing_xi`
5. **Live Scoring**: `innings`, `overs`, `balls`, `wickets`
6. **Performance**: `batting_innings`, `bowling_figures`, `partnerships`
7. **Integrity System**: `scoring_events`, `scoring_disputes`, `scoring_consensus`
8. **Archives**: `match_summaries`, `match_archives`

### PostgreSQL Extensions:
- `uuid-ossp`: UUID generation
- `pg_trgm`: Fuzzy text search
- `pg_stat_statements`: Query performance monitoring

## Useful Commands

```bash
# View logs
docker-compose logs -f app
docker-compose logs -f db

# Connect to database
docker-compose exec db psql -U kreeda_user -d kreeda_db

# Stop services
docker-compose down

# Stop and remove volumes (CAUTION: deletes all data)
docker-compose down -v

# Rebuild app container
docker-compose build app

# Run alembic commands
docker-compose run --rm app alembic current
docker-compose run --rm app alembic history
docker-compose run --rm app alembic downgrade -1
```
