# Kreeda Backend - Quick Reference Guide

> **Fast Lookup Guide for Common Tasks, Commands & Code Snippets**
>
> This document provides quick access to frequently used commands, code patterns, and solutions without reading lengthy documentation.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Common Commands](#common-commands)
3. [Code Snippets](#code-snippets)
4. [GitHub Copilot Prompts](#github-copilot-prompts)
5. [API Testing Examples](#api-testing-examples)
6. [Troubleshooting](#troubleshooting)
7. [File Locations](#file-locations)

---

## Quick Start

### Start Development Environment
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test
pytest tests/test_auth.py::test_register_user_success -v
```

### Access API
```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/api/docs
```

---

## Common Commands

### Docker Commands

#### Start/Stop
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart service
docker-compose restart app

# Rebuild and start
docker-compose up --build -d
```

#### Logs & Debugging
```bash
# Follow logs
docker-compose logs -f

# App logs only
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app

# Show errors
docker-compose logs app | grep ERROR
```

#### Shell Access
```bash
# App container shell
docker-compose exec app bash

# Database shell
docker-compose exec db psql -U kreeda_user -d kreeda_db

# Redis shell
docker-compose exec redis redis-cli
```

### Database Commands

#### Migrations
```bash
# Apply migrations
docker-compose exec app alembic upgrade head

# Create new migration
docker-compose exec app alembic revision --autogenerate -m "description"

# Rollback migration
docker-compose exec app alembic downgrade -1

# Check current version
docker-compose exec app alembic current

# View history
docker-compose exec app alembic history
```

#### Database Queries
```bash
# Count users
docker-compose exec db psql -U kreeda_user -d kreeda_db \
  -c "SELECT COUNT(*) FROM user_auth;"

# List users
docker-compose exec db psql -U kreeda_user -d kreeda_db \
  -c "SELECT email, is_email_verified, created_at FROM user_auth;"

# Show tables
docker-compose exec db psql -U kreeda_user -d kreeda_db -c "\dt"

# Describe table
docker-compose exec db psql -U kreeda_user -d kreeda_db -c "\d user_auth"
```

#### Backup & Restore
```bash
# Backup
docker-compose exec db pg_dump -U kreeda_user kreeda_db > backup.sql

# Restore
docker-compose exec -T db psql -U kreeda_user kreeda_db < backup.sql
```

### Redis Commands

```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# List all keys
docker-compose exec redis redis-cli KEYS '*'

# Get specific key
docker-compose exec redis redis-cli GET "refresh_token:user-id"

# Delete key
docker-compose exec redis redis-cli DEL "key-name"

# Flush all data (⚠️ DANGER)
docker-compose exec redis redis-cli FLUSHALL

# Monitor commands
docker-compose exec redis redis-cli MONITOR
```

### Testing Commands

#### Run Tests
```bash
# All tests
pytest

# Verbose output
pytest -v

# Specific file
pytest tests/test_auth.py -v

# Specific test
pytest tests/test_auth.py::test_register_user_success -v

# By marker
pytest -m unit -v
pytest -m integration -v

# Failed tests only
pytest --lf

# Stop on first failure
pytest -x
```

#### Coverage
```bash
# Run with coverage
pytest --cov=src

# HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=src --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=80
```

### Code Quality

```bash
# Format code
black src/ tests/

# Check formatting (don't modify)
black src/ tests/ --check

# Lint code
flake8 src/ tests/

# Type checking (if mypy installed)
mypy src/
```

---

## Code Snippets

### Creating a New Endpoint

#### 1. Schema (DTOs)
```python
# src/schemas/example.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class ExampleCreateRequest(BaseModel):
    name: str
    description: str | None = None

class ExampleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True  # For SQLAlchemy models
```

#### 2. Service (Business Logic)
```python
# src/services/example_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.example import Example
from src.schemas.example import ExampleCreateRequest, ExampleResponse

class ExampleService:
    @staticmethod
    async def create(request: ExampleCreateRequest, db: AsyncSession) -> ExampleResponse:
        """Create new example"""
        example = Example(
            name=request.name,
            description=request.description
        )
        db.add(example)
        await db.commit()
        await db.refresh(example)
        return ExampleResponse.model_validate(example)
    
    @staticmethod
    async def get_by_id(example_id: UUID, db: AsyncSession) -> ExampleResponse | None:
        """Get example by ID"""
        result = await db.execute(
            select(Example).where(Example.id == example_id)
        )
        example = result.scalar_one_or_none()
        return ExampleResponse.model_validate(example) if example else None
```

#### 3. Router (API Endpoints)
```python
# src/routers/example.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import get_db
from src.core.security import get_current_user
from src.schemas.example import ExampleCreateRequest, ExampleResponse
from src.services.example_service import ExampleService

router = APIRouter(prefix="/examples", tags=["Examples"])

@router.post("/", response_model=ExampleResponse, status_code=201)
async def create_example(
    request: ExampleCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new example"""
    return await ExampleService.create(request, db)

@router.get("/{example_id}", response_model=ExampleResponse)
async def get_example(
    example_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get example by ID"""
    example = await ExampleService.get_by_id(example_id, db)
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    return example
```

#### 4. Register Router
```python
# src/main.py
from src.routers.example import router as example_router

app.include_router(example_router)
```

### Database Patterns

#### Select Single Record
```python
from sqlalchemy import select

result = await db.execute(
    select(User).where(User.email == email)
)
user = result.scalar_one_or_none()
```

#### Select Multiple Records
```python
result = await db.execute(
    select(User).where(User.is_active == True)
)
users = result.scalars().all()
```

#### Select with Join
```python
result = await db.execute(
    select(User, Profile)
    .join(Profile, User.id == Profile.user_id)
    .where(User.email == email)
)
user, profile = result.first()
```

#### Insert
```python
user = User(email=email, password_hash=password_hash)
db.add(user)
await db.commit()
await db.refresh(user)  # Get auto-generated fields
```

#### Update
```python
user = await db.get(User, user_id)
user.email = new_email
user.updated_at = datetime.utcnow()
await db.commit()
await db.refresh(user)
```

#### Delete (Soft Delete)
```python
user = await db.get(User, user_id)
user.is_active = False
await db.commit()
```

#### Delete (Hard Delete)
```python
user = await db.get(User, user_id)
await db.delete(user)
await db.commit()
```

### Redis Patterns

```python
from src.utils.redis_client import redis_client

# Set value with expiry
await redis_client.set("key", "value", ex=3600)  # 1 hour

# Get value
value = await redis_client.get("key")

# Delete key
await redis_client.delete("key")

# Check if key exists
exists = await redis_client.exists("key")

# Set with JSON
import json
await redis_client.set("user:123", json.dumps({"name": "John"}))

# Get and parse JSON
data = await redis_client.get("user:123")
user_data = json.loads(data) if data else None
```

### Testing Patterns

#### Unit Test
```python
import pytest
from src.services.auth import AuthService

@pytest.mark.unit
async def test_register_user(test_db):
    """Test user registration"""
    request = UserRegisterRequest(
        email="test@example.com",
        password="SecurePass123!"
    )
    
    result = await AuthService.register(request, test_db)
    
    assert result.user.email == "test@example.com"
    assert result.session.access_token is not None
```

#### Integration Test
```python
@pytest.mark.integration
async def test_register_and_login(client):
    """Test registration and login flow"""
    # Register
    register_response = await client.post("/auth/register", json={
        "email": "user@example.com",
        "password": "Test@123456"
    })
    assert register_response.status_code == 201
    
    # Login
    login_response = await client.post("/auth/signin/password", json={
        "email": "user@example.com",
        "password": "Test@123456"
    })
    assert login_response.status_code == 200
```

#### Test with Fixtures
```python
async def test_with_user(test_db, test_user):
    """Test using existing user fixture"""
    user = await AuthService.get_user(test_user.user_id, test_db)
    assert user.email == test_user.email
```

---

## GitHub Copilot Prompts

### General Development

```
# Create a new FastAPI endpoint
Create a FastAPI POST endpoint at /api/items that accepts an ItemCreateRequest 
and returns an ItemResponse. Include proper authentication and database session 
dependency injection.

# Write a database query
Write an SQLAlchemy async query to fetch all active users who registered in the 
last 7 days, ordered by creation date descending.

# Create a test
Write a pytest test for the user registration endpoint that verifies successful 
registration, token generation, and database record creation.

# Add error handling
Add proper error handling to this function including database rollback on error, 
logging, and raising appropriate HTTPException with status codes.
```

### Specific to Kreeda

```
# Authentication
Create a password reset endpoint following the existing auth patterns in this 
codebase. Include token generation, Redis storage, email sending, and proper 
validation.

# Cricket scoring
Create a FastAPI endpoint to record a cricket ball delivery. Include batsman, 
bowler, runs scored, wicket information, and update innings totals.

# WebSocket
Implement a WebSocket endpoint for live cricket score updates. Broadcast 
updates when a ball is recorded.

# Testing
Write comprehensive tests for the match creation service including success case, 
validation errors, and authorization checks.
```

---

## API Testing Examples

### Authentication Flow

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "phone_number": "+1234567890",
    "name": "Test User"
  }'

# Save tokens from response
ACCESS_TOKEN="<access_token_from_response>"
REFRESH_TOKEN="<refresh_token_from_response>"

# 2. Login
curl -X POST http://localhost:8000/auth/signin/password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# 3. Get current user
curl -X GET http://localhost:8000/auth/user \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 4. Update user
curl -X PUT http://localhost:8000/auth/user \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com",
    "password": "NewSecurePass123!"
  }'

# 5. Refresh token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"

# 6. Sign out
curl -X POST http://localhost:8000/auth/signout \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Profile Management

```bash
# Get profile
curl -X GET http://localhost:8000/user/profile/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Update profile
curl -X PUT http://localhost:8000/user/profile/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "location": "San Francisco",
    "bio": "Software Developer",
    "preferences": {"theme": "dark"}
  }'
```

### Using httpie (Alternative)

```bash
# Install: pip install httpie

# Register
http POST localhost:8000/auth/register \
  email=test@example.com \
  password=SecurePass123! \
  name="Test User"

# Login
http POST localhost:8000/auth/signin/password \
  email=test@example.com \
  password=SecurePass123!

# Get user (with token)
http GET localhost:8000/auth/user \
  "Authorization: Bearer $ACCESS_TOKEN"
```

---

## Troubleshooting

### Database Issues

#### Connection Error
```bash
# Check if PostgreSQL is running
docker-compose ps db

# Check logs
docker-compose logs db

# Restart database
docker-compose restart db

# Test connection
docker-compose exec app python -c "from src.database.connection import engine; print('OK')"
```

#### Migration Issues
```bash
# Check current version
docker-compose exec app alembic current

# View pending migrations
docker-compose exec app alembic heads

# Reset migrations (⚠️ DANGER - data loss)
docker-compose exec db psql -U kreeda_user -d kreeda_db \
  -c "DELETE FROM alembic_version;"
docker-compose exec app alembic upgrade head
```

### Redis Issues

```bash
# Check if Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check memory usage
docker-compose exec redis redis-cli INFO memory

# Clear all keys (⚠️ DANGER)
docker-compose exec redis redis-cli FLUSHALL
```

### Application Issues

#### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

#### Module Import Errors
```bash
# Rebuild container
docker-compose up --build -d

# Check Python path
docker-compose exec app python -c "import sys; print(sys.path)"

# Reinstall dependencies
docker-compose exec app pip install -r requirements.txt
```

#### Test Failures
```bash
# Run specific failing test
pytest tests/test_auth.py::test_register_user_success -v

# Show print statements
pytest -s

# Show full traceback
pytest --tb=long

# Drop to debugger on failure
pytest --pdb
```

### Clean Slate

```bash
# Stop everything and remove volumes
docker-compose down -v

# Remove all containers and images
docker system prune -a --volumes

# Rebuild from scratch
docker-compose up --build -d

# Run migrations
docker-compose exec app alembic upgrade head

# Run tests
docker-compose exec app pytest
```

---

## File Locations

### Configuration
```
.env                          # Environment variables
src/config/settings.py        # Application settings
pytest.ini                    # Pytest configuration
alembic.ini                   # Alembic configuration
```

### Source Code
```
src/
├── main.py                   # FastAPI app entry point
├── routers/                  # API endpoints
│   ├── auth.py               # Authentication routes
│   └── user_profile.py       # Profile routes
├── services/                 # Business logic
│   ├── auth.py               # Auth service
│   └── user_profile.py       # Profile service
├── models/                   # Database models
│   ├── user_auth.py          # UserAuth model
│   └── user_profile.py       # UserProfile model
├── schemas/                  # Pydantic schemas
│   ├── auth.py               # Auth DTOs
│   └── user_profile.py       # Profile DTOs
└── utils/                    # Utilities
    ├── email.py              # Email service
    ├── logger.py             # Logging
    ├── redis_client.py       # Redis client
    └── validators.py         # Validators
```

### Tests
```
tests/
├── conftest.py               # Test fixtures
├── test_auth.py              # Auth tests
├── test_user_profile.py      # Profile tests
└── test_integration.py       # Integration tests
```

### Documentation
```
README.md                     # Project overview
CONTEXT.md                    # Detailed context for development
TODO.md                       # Development checklist
QUICK_REFERENCE.md            # This file
QUICK_COMMANDS.md             # Docker and CLI commands
```

---

## Environment Variables

### Required
```bash
DATABASE_URL=postgresql+asyncpg://kreeda_user:kreeda_pass@localhost:5432/kreeda_db
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key-here
```

### Optional
```bash
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600
APP_ENV=development
DEBUG=True
LOG_LEVEL=INFO
```

---

## Useful Links

### Local Development
- **API Docs (Swagger)**: http://localhost:8000/api/docs
- **API Docs (ReDoc)**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

### Monitoring (if configured)
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

---

## Keyboard Shortcuts (Pytest)

```
pytest --help    # Show all options
-v               # Verbose
-s               # Show print statements
-x               # Stop on first failure
--lf             # Run last failed tests
--ff             # Run failed first, then others
--pdb            # Drop to debugger on failure
-k "pattern"     # Run tests matching pattern
-m marker        # Run tests with specific marker
--cov=src        # Coverage report
--durations=10   # Show 10 slowest tests
```

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/feature-name

# Make changes and commit
git add .
git commit -m "feat: add feature description"

# Push to remote
git push origin feature/feature-name

# Create pull request on GitHub
# CI/CD will run automatically

# After PR approval
git checkout main
git pull origin main
git branch -d feature/feature-name
```

---

## Performance Tips

1. **Use connection pooling** (already configured)
2. **Cache frequently accessed data** in Redis
3. **Use database indexes** on frequently queried fields
4. **Avoid N+1 queries** - use `selectinload()` for relationships
5. **Use async/await** for all I/O operations
6. **Monitor slow queries** with `echo=True` during development

---

## Security Checklist

- [x] Passwords hashed with bcrypt
- [x] JWT tokens with expiry
- [x] Input validation with Pydantic
- [x] SQL injection protection (ORM)
- [x] Environment variables for secrets
- [ ] HTTPS in production
- [ ] Rate limiting
- [ ] CORS configuration
- [ ] Security headers

---

## Next Steps

1. Read **CONTEXT.md** for detailed project context
2. Read **TODO.md** for development roadmap
3. Start with Sprint 1 tasks
4. Follow TDD approach (tests first)
5. Run CI/CD checks before pushing
6. Update documentation as you progress

---

## Support

### Getting Help
1. Check this quick reference
2. Check **CONTEXT.md** for detailed info
3. Check **TODO.md** for task specifics
4. Check existing tests for patterns
5. Use GitHub Copilot with context

### Common Questions
- **Q: How do I add a new endpoint?**
  - A: See "Creating a New Endpoint" section above

- **Q: How do I run specific tests?**
  - A: `pytest tests/test_file.py::test_name -v`

- **Q: How do I reset the database?**
  - A: `docker-compose down -v && docker-compose up -d`

- **Q: How do I check test coverage?**
  - A: `pytest --cov=src --cov-report=html`

- **Q: Where are the logs?**
  - A: `docker-compose logs -f app`

---

**Last Updated**: 2024-10-11

**Version**: 1.0.0
