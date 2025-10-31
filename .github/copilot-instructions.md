# Kreeda Backend - AI Coding Agent Instructions

## Project Vision
Kreeda is a **sports scorekeeping platform** for casual and serious players to track scores, performance, and match statistics in real-time. Starting with cricket (MVP), with planned expansion to other sports.

### Core Value Proposition
- **Live ball-by-ball scoring** with real-time spectator experience (like TV broadcasts)
- **Integrity-based scoring system** - adaptive validation (umpire/referee → dual scorers → single scorer) based on match scale
- **Rich analytics** - player profiles, statistics, match highlights accessible via mobile app
- **Complete match history** - ball-by-ball replay and analysis

### Technical Foundation
Built with FastAPI, PostgreSQL, Redis on Docker. Emphasizes **event sourcing for scoring integrity** and multi-sport extensibility. Designed for easy Docker deployment from GitHub repo.

## Architecture Layers (Top-Down)
1. **Identity Layer** (`user_auth`, `user_profile`) - Supabase-compatible authentication
2. **Sport Profiles** (`sport_profiles`, `cricket_player_profiles`) - Multi-sport player identities
3. **Teams & Memberships** (`teams`, `team_memberships`) - Team organization and rosters
4. **Match Management** (`matches`, `match_officials`, `match_playing_xi`) - Match setup and configuration
5. **Live Scoring** (`innings`, `overs`, `balls`, `wickets`) - Event-sourced ball-by-ball recording
6. **Scoring Integrity** (`scoring_events`, `scoring_disputes`, `scoring_consensus`) - Multi-validator validation system
7. **Performance Aggregates** (`batting_innings`, `bowling_figures`, `partnerships`) - Real-time statistics
8. **Archives & Summaries** (`match_summaries`, `match_archives`) - Historical data and highlights

**Critical Design Pattern**: 
- Data flows through `user_auth` → `sport_profiles` → `cricket_player_profiles` → teams/matches
- **Never query `user_auth` directly for cricket data** - always traverse through sport profiles
- Every ball creates immutable records - current state is **derived** from event log, not updated in place

## Development Approach

### Current Phase: Design & Architecture
- **Status**: Design phase - models and schemas defined, implementation in progress
- **Philosophy**: Design first, implement in small testable chunks
- **Testing Strategy**: Test each component as it's developed before moving to next
- **Reference Documents**: `docs/API_DESIGN.md` (API contracts) and `docs/schema.md` (database design) are authoritative

### When Implementing Features
1. **Always check design docs first** - `docs/API_DESIGN.md` for endpoints, `docs/schema.md` for data models
2. **Follow layered approach** - Models → Schemas → Services → Routers → Tests
3. **Validate against design** - Ensure implementation matches documented API contracts
4. **Test incrementally** - Write tests for each service/router as you build it
5. **Report design anomalies** - If you find inconsistencies between schema.md and API_DESIGN.md, flag them

### Local Setup
```bash
# Start services (PostgreSQL, Redis)
docker-compose up -d

# Run migrations
alembic upgrade head

# Start development server
uvicorn src.main:app --reload --port 8000
```

### Database Migrations
- **Always use Alembic** for schema changes (never manual SQL)
- Run `alembic revision --autogenerate -m "description"` after model changes
- Review migration files before applying - auto-generated code may need JSONB defaults or enum handling
- Migration file naming: `{revision}_{description}.py` (e.g., `40cfc5d68d9c_initial_schema_user_auth_profiles_and_.py`)

### Configuration
- Settings in `src/config/settings.py` use pydantic-settings
- `.env` file for local overrides (never commit)
- Connection strings use asyncpg for async SQLAlchemy: `postgresql+asyncpg://user:pass@host/db`
- Docker services: PostgreSQL on 5432, Redis on 6379, FastAPI on 8000

### Docker Deployment
- **All services run in Docker** - app, PostgreSQL, Redis defined in `docker-compose.yml`
- **Deployment ready** - Dockerfile optimized for direct GitHub → Docker deployment
- **Database initialization** - `init-db.sql` auto-runs on first PostgreSQL container start (installs uuid-ossp, pg_trgm, pg_stat_statements extensions)
- **Hot reload** - Development mode has volume mounts for live code changes

### Environment Variables
Create a `.env` file in the project root (never commit to git):
```env
# App Configuration
APP_ENV=development
LOG_LEVEL=INFO

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://kreeda_user:kreeda_pass@localhost:5432/kreeda_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kreeda_db
DB_USER=kreeda_user
DB_PASS=kreeda_pass

# Redis
REDIS_URL=redis://localhost:6379

# JWT Security
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# Email (for OTP/verification - optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@kreeda.app
```

**Note**: Docker Compose sets these automatically, but you can override in `.env` for custom local setup.

## Cricket-Specific Conventions

### Event Sourcing Pattern
Every ball bowled creates immutable records in `balls` table. Current match state is **derived** from event log, not updated directly. When implementing scoring:
1. Create `Ball` record with full context (bowler, batsman, runs, extras)
2. If wicket: Create linked `Wicket` record with dismissal details
3. Update aggregates (`batting_innings`, `bowling_figures`) via calculated queries
4. Never delete or modify past balls - use `disputed` status flags instead

### JSONB Configuration Fields
- `matches.match_rules` - Flexible match format (players_per_team, overs, powerplay, etc.)
- `matches.venue` - Location with lat/lng
- Validate JSONB schemas in Pydantic schemas before DB insertion
- Example: `{"players_per_team": 11, "overs_per_side": 20, "balls_per_over": 6}`

### Enums Everywhere
All cricket-specific values use SQLAlchemy Enums (defined in `src/models/enums.py`):
- Match types: `MatchType.T20`, `MatchType.ODI`, `MatchType.CUSTOM`
- Player roles: `PlayingRole.BATSMAN`, `PlayingRole.ALL_ROUNDER`
- Dismissals: `DismissalType.BOWLED`, `DismissalType.CAUGHT`
- **Always import from `src.models.enums`**, never hardcode strings

### Multi-Validator Scoring Integrity System
Kreeda uses an adaptive validation system based on match scale:

#### Validation Tiers
1. **TRIPLE** (Professional matches)
   - Umpire + 2 independent scorers
   - Requires 2/3 consensus for validation
   - Disputes escalated to umpire override
   
2. **DUAL** (Serious amateur/league)
   - Team A scorer + Team B scorer
   - Both must agree for auto-validation
   - Mismatches create dispute requiring umpire/captain resolution
   
3. **SINGLE** (Casual matches)
   - One trusted scorer
   - Auto-validated, but can be disputed by players
   
4. **HONOR** (Practice/friendly)
   - Self-scoring by batsmen
   - No validation, purely trust-based

#### Consensus Algorithm
When implementing scoring validation (`src/services/cricket/scoring_integrity.py`):

```python
# Each scoring event creates a ScoringEvent record
# Event hash = SHA256(innings_id + ball_number + event_data + prev_hash)
# This creates an immutable blockchain-like chain

# For DUAL validation:
1. Scorer A submits event → stored with status PENDING
2. Scorer B submits event → system compares
3. If data matches → auto-validate, create Ball record
4. If mismatch → create ScoringDispute, notify officials

# Dispute resolution priority:
1. Umpire override (if assigned)
2. Video review (if available)
3. Majority vote (3 scorers)
4. Captain consensus
5. Abandon ball (last resort)
```

**Key tables**: `scoring_events`, `scoring_disputes`, `scoring_consensus`

### WebSocket Implementation for Live Scoring
Live match updates use WebSocket connections for real-time experience:

#### Connection Pattern
```python
# Client connects to: ws://localhost:8000/ws/matches/{match_id}/live
# Authorization via query param: ?token=<jwt_token>

# On connection, send current match state
# Then stream events as they happen:
{
  "type": "BALL_BOWLED",
  "data": {
    "ball": {...},
    "innings_state": {
      "score": "145/4",
      "overs": 15.3,
      "run_rate": 9.35
    },
    "striker": {...},
    "bowler": {...}
  },
  "timestamp": "2025-10-30T15:32:45Z"
}
```

#### Event Types to Broadcast
- `BALL_BOWLED` - Every legal delivery
- `WICKET_FALLEN` - Dismissal
- `OVER_COMPLETE` - End of over
- `INNINGS_COMPLETE` - Innings finished
- `MATCH_COMPLETE` - Final result
- `SCORING_DISPUTE_RAISED` - Validation conflict
- `DISPUTE_RESOLVED` - Consensus reached
- `PLAYER_CHANGED` - Batsman/bowler rotation
- `MILESTONE_ACHIEVED` - Fifty, century, hat-trick, etc.

**Implementation location**: `src/routers/cricket/websocket.py` (to be created)

## Code Patterns

### Router → Service → Model Layer
```python
# routers/cricket/match.py - Only request/response handling
@router.post("/matches")
async def create_match(request: MatchCreateRequest, db: AsyncSession = Depends(get_db)):
    return await MatchService.create_match(request, db)

# services/cricket/match.py - Business logic
class MatchService:
    @staticmethod
    async def create_match(request: MatchCreateRequest, db: AsyncSession):
        # Validation, DB operations, response building

# models/cricket/match.py - SQLAlchemy ORM models only
```

### Async Session Handling
- **Always** use `AsyncSession` with `async with` or FastAPI dependency injection
- Get DB session: `db: AsyncSession = Depends(get_db)` in routers
- Use `await db.execute()`, `await db.commit()`, never synchronous calls
- Sessions auto-close via `get_db()` dependency

### Authentication Pattern
- JWT tokens created with `create_access_token()` in `src/core/security.py`
- Tokens contain `{"sub": str(user_id)}` payload
- Verify with `decode_access_token(token)` - returns payload or None
- Extract from headers: `authorization.split(" ")[1]` after checking `startswith("Bearer ")`
- Supabase-compatible response format (see `AuthResponse`, `SessionResponse` schemas)

### UUID Usage
- All primary keys use UUID v4: `Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`
- Import: `from sqlalchemy.dialects.postgresql import UUID` and `import uuid`
- In schemas, use `pydantic.UUID4` for type hints

## Testing Approach
- **No test suite exists yet** - when implementing tests:
  - Use pytest with pytest-asyncio for async support
  - Create fixtures for DB session, test data factories
  - Test services independently from routers
  - Use in-memory Redis or mock for integration tests

### Testing Strategy & Patterns

#### Test Structure
```
tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Fast, isolated tests
│   ├── test_services/
│   │   ├── test_auth_service.py
│   │   ├── test_match_service.py
│   │   └── test_scoring_service.py
│   └── test_models/
│       └── test_cricket_models.py
├── integration/                   # Database + service tests
│   ├── test_match_creation_flow.py
│   ├── test_scoring_validation.py
│   └── test_match_lifecycle.py
└── e2e/                          # Full API endpoint tests
    ├── test_auth_endpoints.py
    ├── test_match_endpoints.py
    └── test_live_scoring_endpoints.py
```

#### Key Fixtures (conftest.py)
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from src.database.connection import get_db
from src.models.base import Base

@pytest.fixture
async def db_session():
    """Create test database session"""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_kreeda")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def test_user_factory(db_session):
    """Factory for creating test users"""
    async def create_user(email="test@test.com", **kwargs):
        from src.models.user_auth import UserAuth
        user = UserAuth(email=email, **kwargs)
        db_session.add(user)
        await db_session.commit()
        return user
    return create_user

@pytest.fixture
def test_match_factory(db_session):
    """Factory for creating test matches"""
    # Similar pattern for matches
```

#### Test Examples

**Unit Test - Service Logic**
```python
# tests/unit/test_services/test_scoring_service.py
import pytest
from src.services.cricket.scoring import ScoringService

@pytest.mark.asyncio
async def test_validate_ball_event_dual_scoring(db_session):
    # Test dual scorer consensus
    scorer_a_event = {...}
    scorer_b_event = {...}
    
    result = await ScoringService.validate_dual_events(
        scorer_a_event, scorer_b_event, db_session
    )
    
    assert result.is_validated == True
    assert result.consensus_reached == True
```

**Integration Test - Full Flow**
```python
# tests/integration/test_match_lifecycle.py
@pytest.mark.asyncio
async def test_complete_match_flow(db_session, test_user_factory, test_team_factory):
    # 1. Create teams
    # 2. Create match
    # 3. Conduct toss
    # 4. Score innings
    # 5. Verify match summary
```

**E2E Test - API Endpoint**
```python
# tests/e2e/test_match_endpoints.py
from fastapi.testclient import TestClient

def test_create_match_endpoint(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/matches",
        json={...},
        headers=auth_headers
    )
    assert response.status_code == 201
    assert "match_code" in response.json()["data"]
```

#### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_services/test_auth_service.py

# Specific test
pytest tests/unit/test_services/test_auth_service.py::test_register_user

# Async tests only
pytest -k "asyncio"

# Watch mode (requires pytest-watch)
ptw
```

#### Test Database Setup
```bash
# Create test database
docker exec -it kreeda-backend-db-1 psql -U kreeda_user -c "CREATE DATABASE test_kreeda;"

# Run migrations on test DB
DATABASE_URL=postgresql+asyncpg://kreeda_user:kreeda_pass@localhost/test_kreeda alembic upgrade head
```

## Critical Files Reference
- **API contracts**: `docs/API_DESIGN.md` (1400+ lines) - authoritative endpoint specs
- **Schema design**: `docs/schema.md` - explains event sourcing, multi-validator consensus
- **Main router registration**: `src/main.py` - only place to register new routers
- **Base model**: `src/models/base.py` - all models inherit from `Base`
- **Migration template**: `alembic/versions/40cfc5d68d9c_initial_schema_user_auth_profiles_and_.py` - reference for complex migrations

## Multi-Sport Extensibility
When adding new sports (football, hockey):
1. Add enum to `SportType` in `src/models/enums.py`
2. Create `{sport}_player_profiles` table extending `sport_profiles` (see `cricket_player_profiles`)
3. Create sport-specific models in `src/models/{sport}/` directory
4. Keep core match/team tables sport-agnostic via `sport_type` enum column

## Common Pitfalls
- **Don't** query `user_auth` directly for player stats - use `cricket_player_profiles`
- **Don't** use synchronous SQLAlchemy calls - this is fully async with asyncpg
- **Don't** modify `match_rules` JSONB without Pydantic validation
- **Don't** create duplicate enum values - check `src/models/enums.py` first
- **Don't** forget to update relationships when adding foreign keys
- **Don't** deviate from design docs without discussion - API_DESIGN.md and schema.md are the source of truth
- **Redis is configured** (`src/utils/redis_client.py`) but not actively used yet - OTP/session storage pending

## Implementation Status & Next Steps

### Completed
- ✅ **Phase 1**: Cricket Profiles (merged to master, v1.0.0-phase1-cricket-profiles)
  - Sport profiles and cricket player profiles
  - 17 unit tests, 100% passing
- ✅ **Phase 2**: Teams & Match Management (merged to master, v2.0.0-phase2-teams-matches)
  - Team CRUD with JSONB support (colors, home ground)
  - Match creation, toss management, state machine
  - 44 tests total (24 unit + 3 integration), 61% coverage
  - 11 REST API endpoints
- ✅ Base authentication system (Supabase-compatible)
- ✅ User profile management
- ✅ Database schema design (all models defined)
- ✅ Alembic migration setup
- ✅ Docker containerization
- ✅ Redis configuration

### Current Phase: Phase 3 - Live Scoring & Event Sourcing
- 🚧 Ball-by-ball event sourcing implementation
- 🚧 Multi-scorer validation/consensus system
- 🚧 Performance aggregation (real-time statistics)
- 🚧 WebSocket support for live match updates
- 🚧 Match archives and replay capability

### Next Development Priorities (Phase 3)
1. **Ball-by-Ball Event Sourcing**
   - Implement innings, overs, balls, wickets models
   - Event sourcing pattern: immutable ball records
   - Derive current state from event log
   
2. **Multi-Scorer Validation System**
   - Implement scoring_events, scoring_disputes, scoring_consensus
   - Build consensus algorithm (TRIPLE/DUAL/SINGLE/HONOR tiers)
   - Blockchain-like event hashing for integrity
   
3. **Performance Aggregation**
   - Real-time batting_innings, bowling_figures updates
   - Partnership tracking
   - Statistical calculations (run rate, economy, strike rate)
   
4. **WebSocket Implementation**
   - Real-time match updates for spectators
   - Event broadcasting (BALL_BOWLED, WICKET_FALLEN, etc.)
   - Connection management for live matches
   
5. **Match Archives**
   - Post-match summary generation
   - Ball-by-ball replay capability
   - Highlight extraction and storage
