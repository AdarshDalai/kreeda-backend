# Kreeda Development Workflow 🚀

## Quick Start Guide

Based on our comprehensive planning documentation, here's your actionable development workflow to bring Kreeda to life.

## Current Status ✅

- ✅ **Branch**: `mvp-cricket-scorecard` (focused development)
- ✅ **Documentation**: Complete technical specifications
- ✅ **Environment**: Basic `.env.example` configuration
- ✅ **Planning**: 28-week development roadmap

## Immediate Action Plan (Next 7 Days)

### Day 1-2: Development Environment Setup

#### 1. Project Structure Creation
```bash
# Create the core backend structure
mkdir -p {app,app/api,app/core,app/models,app/schemas,app/services,app/utils}
mkdir -p {app/api/v1,app/api/v1/endpoints}
mkdir -p {app/db,app/tests,scripts,requirements}
mkdir -p {docker,nginx}

# Create initial files
touch app/__init__.py app/main.py app/config.py
touch requirements/{base.txt,development.txt,production.txt,test.txt}
touch docker/{Dockerfile,docker-compose.yml,docker-compose.dev.yml}
touch {README.md,CHANGELOG.md,pyproject.toml}
```

#### 2. Python Environment & Dependencies
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install core dependencies
pip install fastapi[all] uvicorn[standard] sqlalchemy[asyncio] 
pip install alembic asyncpg redis python-multipart python-jose[cryptography]
pip install supabase pytest pytest-asyncio httpx

# Generate requirements
pip freeze > requirements/base.txt
```

#### 3. Docker Setup
Create production-ready containerization from day one.

#### 4. Database Setup
- PostgreSQL with Docker
- Redis for caching and real-time features
- Alembic migrations setup

### Day 3-4: Core API Foundation

#### 1. FastAPI Application Structure
- Main application setup with proper configuration
- Health check endpoints
- CORS and middleware configuration
- Basic authentication integration with Supabase

#### 2. Database Models (Cricket Focus)
Priority models for MVP:
- **User** (players, scorers, spectators)
- **Team** (cricket teams)
- **Match** (cricket matches)
- **CricketScorecard** (ball-by-ball data)
- **Scorer** (dual scorer system)

#### 3. API Endpoints (Phase 1)
Focus on core cricket scorecard functionality:
- User management
- Team creation/management
- Match setup and control
- Basic scoring endpoints

### Day 5-7: Cricket Scoring Engine

#### 1. Cricket Business Logic
- Ball-by-ball scoring system
- Over calculations and innings tracking
- Basic cricket rules validation
- Score aggregation and statistics

#### 2. WebSocket Integration
- Real-time score updates
- Connection management
- Event broadcasting to spectators

#### 3. Testing Setup
- Unit tests for scoring logic
- Integration tests for API endpoints
- Test database setup

## Development Workflow Structure

### Branch Strategy
```
master (stable)
├── develop (integration)
├── feature/cricket-scoring-engine
├── feature/user-authentication
├── feature/websocket-realtime
└── mvp-cricket-scorecard (current - MVP focus)
```

### Daily Development Flow

#### Morning Routine (30 minutes)
1. **Review**: Check overnight CI/CD runs
2. **Plan**: Review current sprint tasks and priorities
3. **Sync**: Update from develop branch if needed
4. **Test**: Run local test suite

#### Development Cycle (2-3 hour blocks)
1. **Feature Branch**: Create focused feature branches
   ```bash
   git checkout -b feature/cricket-ball-tracking
   ```

2. **TDD Approach**: Write tests first, then implement
   ```bash
   # Write test
   pytest app/tests/test_cricket_scoring.py::test_ball_tracking -v
   
   # Implement feature
   # Run tests until green
   pytest app/tests/test_cricket_scoring.py -v
   ```

3. **Commit Strategy**: Small, atomic commits
   ```bash
   git add .
   git commit -m "feat: implement ball-by-ball tracking for cricket scorecard
   
   - Add CricketBall model with delivery details
   - Implement ball validation logic
   - Add tests for scoring edge cases
   
   Refs: #KRDA-001"
   ```

4. **Code Review**: Self-review before pushing
   - Check for security issues
   - Verify test coverage
   - Validate against architecture docs

#### Evening Wrap-up (15 minutes)
1. **Push Changes**: Push completed features
2. **Update Status**: Update sprint board/documentation
3. **Plan Tomorrow**: Prepare next day's priorities

### Quality Gates

#### Before Each Commit
```bash
# Run quality checks
pytest                          # All tests pass
black app/                      # Code formatting
flake8 app/                     # Linting
mypy app/                       # Type checking
```

#### Before Each PR
```bash
# Comprehensive testing
pytest --cov=app --cov-report=html     # Test coverage >80%
docker-compose up --build              # Docker build success
```

#### Before Each Sprint
- Architecture review against documentation
- Performance benchmarking
- Security assessment
- User story acceptance criteria validation

## Sprint 1 Implementation Priority (Week 1-2)

### Must-Have (P0) - Core Infrastructure
1. **FastAPI Application**
   - Basic app structure and configuration
   - Health check endpoints
   - Environment-based configuration

2. **Database Setup**
   - PostgreSQL with Docker
   - Alembic migration system
   - Basic User model

3. **Authentication**
   - Supabase JWT integration
   - User registration/login endpoints
   - Protected route middleware

4. **Docker Environment**
   - Development docker-compose
   - Production-ready Dockerfile
   - Database initialization scripts

### Should-Have (P1) - Cricket Foundation
1. **Cricket Models**
   - Team, Match, CricketScorecard models
   - Basic relationships and constraints

2. **Core API Endpoints**
   - User CRUD operations
   - Team management
   - Match creation and basic operations

3. **Basic Testing**
   - Unit tests for models
   - API endpoint tests
   - CI/CD pipeline setup

### Could-Have (P2) - Enhancement
1. **Redis Integration**
   - Caching layer setup
   - Session management

2. **API Documentation**
   - Swagger/OpenAPI documentation
   - API versioning structure

## File Structure Template

```
kreeda-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # API dependencies (auth, db)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py          # API router aggregation
│   │       └── endpoints/
│   │           ├── auth.py     # Authentication endpoints
│   │           ├── users.py    # User management
│   │           ├── teams.py    # Team management
│   │           ├── matches.py  # Match management
│   │           └── cricket.py  # Cricket-specific endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # JWT and security utilities
│   │   ├── config.py           # Pydantic settings
│   │   └── events.py           # WebSocket event handlers
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy base setup
│   │   ├── session.py          # Database session management
│   │   └── init_db.py          # Database initialization
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User SQLAlchemy model
│   │   ├── team.py             # Team model
│   │   ├── match.py            # Match model
│   │   └── cricket.py          # Cricket-specific models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # User Pydantic schemas
│   │   ├── team.py             # Team schemas
│   │   ├── match.py            # Match schemas
│   │   └── cricket.py          # Cricket schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py     # User business logic
│   │   ├── team_service.py     # Team business logic
│   │   ├── match_service.py    # Match business logic
│   │   └── cricket_service.py  # Cricket scoring logic
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py       # Custom validation logic
│   │   ├── helpers.py          # Utility functions
│   │   └── exceptions.py       # Custom exceptions
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py         # Pytest configuration
│       ├── test_auth.py        # Authentication tests
│       ├── test_cricket.py     # Cricket logic tests
│       └── integration/        # Integration tests
├── alembic/                    # Database migrations
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
├── scripts/
│   ├── init-db.sh             # Database initialization
│   └── run-dev.sh             # Development server script
├── requirements/
│   ├── base.txt               # Core dependencies
│   ├── development.txt        # Development dependencies
│   ├── production.txt         # Production dependencies
│   └── test.txt               # Testing dependencies
├── .env                       # Environment variables (local)
├── .env.example               # Environment template
├── pyproject.toml             # Python project configuration
├── README.md                  # Project documentation
└── CHANGELOG.md               # Version history
```

## Key Implementation Decisions

### Technology Choices Confirmed
- **Backend**: FastAPI (async, high performance, great documentation)
- **Database**: PostgreSQL (reliability, cricket statistics complexity)
- **Cache**: Redis (real-time features, session management)
- **Auth**: Supabase (rapid development, scalable)
- **WebSockets**: FastAPI native (real-time scoring)
- **Containerization**: Docker (consistent environments)

### Architecture Patterns
- **Repository Pattern**: Clean data access layer
- **Service Layer**: Business logic separation
- **Dependency Injection**: FastAPI's built-in DI
- **Event-Driven**: WebSocket events for real-time updates
- **Clean Architecture**: Domain-driven design principles

## Success Checkpoints

### Week 1 Success Criteria
- ✅ FastAPI application running with health check
- ✅ PostgreSQL database connected with basic User model
- ✅ Supabase authentication working
- ✅ Docker development environment operational
- ✅ Basic API endpoints tested and documented

### Week 2 Success Criteria
- ✅ Cricket models (Team, Match, Scorecard) implemented
- ✅ Core API endpoints for user and team management
- ✅ Basic cricket match creation and scoring
- ✅ WebSocket connection established for real-time updates
- ✅ Test coverage >70% for implemented features

## Next Document Creation

After Week 1-2 implementation, we'll need:
1. **API Documentation** - Detailed endpoint documentation
2. **Database Migration Guide** - Schema evolution strategy
3. **Mobile App Kickoff** - Flutter app setup and architecture
4. **Performance Benchmarks** - Baseline performance metrics

## Getting Started Command

```bash
# Let's begin! 🚀
git checkout mvp-cricket-scorecard
echo "Starting Kreeda MVP development..."
echo "Next: Run the project structure creation commands above"
```

This workflow is designed to be practical, focused, and aligned with our comprehensive planning documentation. It balances rapid MVP development with long-term scalability and maintainability.