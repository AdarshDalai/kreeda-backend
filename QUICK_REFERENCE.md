# 🏏 Kreeda Backend - Quick Reference

## 🚀 Start/Stop Commands

```bash
# Start all services
docker-compose up -d

# Start only database services
docker-compose up -d db redis

# Stop all services
docker-compose down

# Stop and remove all data (⚠️  DESTRUCTIVE)
docker-compose down -v

# View logs (live)
docker-compose logs -f app
docker-compose logs -f db

# Restart a service
docker-compose restart app
```

## 📊 Database Commands

```bash
# Connect to database
docker-compose exec db psql -U kreeda_user -d kreeda_db

# List all tables
docker-compose exec -T db psql -U kreeda_user -d kreeda_db -c "\dt"

# Describe a specific table
docker-compose exec -T db psql -U kreeda_user -d kreeda_db -c "\d scoring_events"

# List all enum types
docker-compose exec -T db psql -U kreeda_user -d kreeda_db -c "\dT+"

# List all extensions
docker-compose exec -T db psql -U kreeda_user -d kreeda_db -c "\dx"

# Count total tables
docker-compose exec -T db psql -U kreeda_user -d kreeda_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
```

## 🔄 Migration Commands

```bash
# Check current migration
docker-compose run --rm app alembic current

# View migration history
docker-compose run --rm app alembic history

# Generate new migration
docker-compose run --rm app alembic revision --autogenerate -m "Description here"

# Apply migrations
docker-compose run --rm app alembic upgrade head

# Rollback one migration
docker-compose run --rm app alembic downgrade -1

# Rollback to specific revision
docker-compose run --rm app alembic downgrade <revision_id>
```

## 🌐 API Endpoints

- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📁 Project Structure

```
kreeda-backend/
├── src/
│   ├── models/           # SQLAlchemy models
│   │   ├── enums.py      # All enum types
│   │   ├── base.py       # Base model class
│   │   ├── user_auth.py  # Authentication
│   │   ├── user_profile.py # User profiles
│   │   ├── sport_profile.py # Sport profiles
│   │   └── cricket/      # Cricket module (18 models)
│   ├── schemas/          # Pydantic schemas (next phase)
│   ├── routers/          # API routes
│   ├── services/         # Business logic
│   ├── config/           # Settings
│   └── main.py           # FastAPI app
├── alembic/              # Database migrations
├── docs/                 # Documentation
│   └── schema.md         # Complete DB schema
├── scripts/              # Helper scripts
│   └── init-db.sh        # DB initialization
├── docker-compose.yml    # Docker configuration
└── DATABASE_SETUP.md     # Setup instructions
```

## 🏗️ Cricket Database Tables (21 tables)

### Identity (4 tables)
- `user_auth` - Authentication
- `user_profiles` - User data
- `sport_profiles` - Multi-sport profiles
- `cricket_player_profiles` - Cricket stats

### Teams (2 tables)
- `teams` - Team entities
- `team_memberships` - Roster

### Matches (3 tables)
- `matches` - Match config
- `match_officials` - Scorers/umpires
- `match_playing_xi` - Playing 11

### Live Scoring (4 tables)
- `innings` - Innings tracking
- `overs` - Over progression
- `balls` - Ball-by-ball
- `wickets` - Wicket details

### Performance (3 tables)
- `batting_innings` - Batting stats
- `bowling_figures` - Bowling stats
- `partnerships` - Partnership tracking

### Integrity (3 tables) 👑
- `scoring_events` - Event sourcing
- `scoring_disputes` - Conflicts
- `scoring_consensus` - Validation

### Archives (2 tables)
- `match_summaries` - Aggregates
- `match_archives` - Archive index

## 🔒 Environment Variables

```bash
# Essential variables (in .env)
DATABASE_URL=postgresql+asyncpg://kreeda_user:kreeda_pass@db:5432/kreeda_db
REDIS_URL=redis://redis:6379
JWT_SECRET=<64+ character random string>
APP_ENV=development
```

## 🧪 Testing

```bash
# Run a simple query
docker-compose exec -T db psql -U kreeda_user -d kreeda_db -c "SELECT * FROM user_auth LIMIT 5;"

# Test API endpoint
curl http://localhost:8000/docs

# Check app health
docker-compose exec app python -c "import sys; print(sys.version)"
```

## 🛠️ Troubleshooting

### Docker not running
```bash
# Open Docker Desktop app
open -a Docker
sleep 15
docker info
```

### Database connection errors
```bash
# Check if PostgreSQL is ready
docker-compose exec db pg_isready -U kreeda_user

# Restart database
docker-compose restart db
```

### App won't start
```bash
# Check logs
docker-compose logs app

# Rebuild container
docker-compose build app
docker-compose up -d app
```

### Migration errors
```bash
# Reset database (⚠️  DELETES ALL DATA)
docker-compose down -v
docker-compose up -d db redis
sleep 10
docker-compose run --rm app alembic upgrade head
```

## 📞 Quick Stats

- **Total Tables**: 22 (21 models + alembic_version)
- **Custom ENUMs**: 26 types
- **Foreign Keys**: 40+ relationships
- **PostgreSQL Extensions**: 3 (uuid-ossp, pg_trgm, pg_stat_statements)
- **Ports**: 8000 (app), 5432 (postgres), 6379 (redis)

---

**For detailed documentation**: See `IMPLEMENTATION_COMPLETE.md` and `DATABASE_SETUP.md`
