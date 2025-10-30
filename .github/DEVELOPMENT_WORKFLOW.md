# Kreeda Backend - AI-Assisted Development Workflow

## Philosophy: Design → Build → Test → Iterate

This guide outlines a professional development approach for building Kreeda with AI assistance (GitHub Copilot, ChatGPT, etc.) while maintaining production-grade quality standards used at companies like Google, Meta, Uber.

---

## Table of Contents
1. [Development Phases](#development-phases)
2. [Pre-Development Setup](#pre-development-setup)
3. [Phase-by-Phase Implementation](#phase-by-phase-implementation)
4. [Quality Gates](#quality-gates)
5. [AI Prompt Templates](#ai-prompt-templates)
6. [Error Handling Strategy](#error-handling-strategy)
7. [Testing Strategy](#testing-strategy)
8. [Code Review Checklist](#code-review-checklist)

---

## Development Phases

### Phase 0: Foundation ✅ (COMPLETED)
- [x] Database schema design
- [x] API design specification
- [x] Base models (User, Auth, Sport Profiles)
- [x] Docker setup
- [x] Alembic migrations

### Phase 1: Cricket Profiles & Teams (Current)
**Goal**: Enable users to create sport profiles and form teams

**Components**:
1. Sport profile schemas (Pydantic)
2. Cricket player profile schemas
3. Sport profile service layer
4. Team management service
5. API routers
6. Unit + Integration tests

### Phase 2: Match Management
**Goal**: Create and configure cricket matches

**Components**:
1. Match creation flow
2. Official assignment
3. Playing XI submission
4. Toss mechanism
5. Match state management

### Phase 3: Live Scoring Engine
**Goal**: Ball-by-ball scoring with validation

**Components**:
1. Innings management
2. Ball recording
3. Wicket handling
4. Score aggregation
5. Dual-scorer validation

### Phase 4: Scoring Integrity
**Goal**: Multi-validator consensus system

**Components**:
1. Event sourcing implementation
2. Dispute management
3. Consensus resolution
4. Audit logging

### Phase 5: Real-time Features
**Goal**: WebSocket live updates

**Components**:
1. WebSocket connection management
2. Event broadcasting
3. Spectator feed
4. Push notifications

### Phase 6: Analytics & Statistics
**Goal**: Player/team performance analytics

**Components**:
1. Match summaries
2. Player statistics
3. Leaderboards
4. Historical trends

---

## Pre-Development Setup

### 1. Environment Checklist
```bash
# Verify Docker is running
docker ps

# Verify services are up
docker-compose ps

# Check database connection
docker exec -it kreeda-backend-db-1 psql -U kreeda_user -d kreeda_db -c "SELECT version();"

# Check Redis connection
docker exec -it kreeda-backend-redis-1 redis-cli ping

# Verify migrations are current
alembic current
```

### 2. Branch Strategy
```bash
# Always work in feature branches
git checkout -b feature/cricket-profiles

# Never commit directly to master
# Use descriptive branch names:
# - feature/[component-name]
# - fix/[bug-description]
# - refactor/[what-being-refactored]
```

### 3. Development Dependencies
Add to `requirements.txt` for testing:
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.1  # For testing FastAPI endpoints
faker==20.0.0  # For generating test data
```

---

## Phase-by-Phase Implementation

## PHASE 1: Cricket Profiles & Teams

### Step 1.1: Pydantic Schemas (Models → Schemas)

**AI Prompt Template**:
```
Context: I'm building Kreeda, a cricket scorekeeping app with FastAPI. 
I have the following SQLAlchemy models defined in src/models/sport_profile.py 
and src/models/cricket/player_profile.py.

Task: Create comprehensive Pydantic schemas in src/schemas/cricket/profile.py for:
1. SportProfileCreate (request)
2. SportProfileResponse (response)
3. CricketPlayerProfileCreate (request)
4. CricketPlayerProfileUpdate (request)
5. CricketPlayerProfileResponse (response with nested user data)
6. CricketPlayerProfileDetailResponse (includes career stats)

Requirements:
- Follow existing auth.py schema patterns
- Use UUID4 for IDs
- Include field validators for enums
- Add example values in Field() descriptions
- Career stats should be read-only computed fields
- Include proper typing with Optional where needed

Constraints:
- Must match API_DESIGN.md section 1.3-1.4
- Follow SOLID principles
- Add docstrings to all classes
```

**Expected Output**: `src/schemas/cricket/profile.py` with 6+ schema classes

**Validation Steps**:
```bash
# 1. Check Python syntax
python -m py_compile src/schemas/cricket/profile.py

# 2. Import test
python -c "from src.schemas.cricket.profile import CricketPlayerProfileResponse; print('✅ Import successful')"

# 3. Schema validation test
python -c "
from src.schemas.cricket.profile import CricketPlayerProfileCreate
from src.models.enums import PlayingRole, BattingStyle

profile = CricketPlayerProfileCreate(
    sport_profile_id='123e4567-e89b-12d3-a456-426614174000',
    playing_role=PlayingRole.BATSMAN,
    batting_style=BattingStyle.RIGHT_HAND
)
print('✅ Schema validation successful')
"
```

### Step 1.2: Service Layer (Business Logic)

**AI Prompt Template**:
```
Context: Kreeda cricket scorekeeping app. I have Pydantic schemas defined 
in src/schemas/cricket/profile.py and SQLAlchemy models in src/models/.

Task: Create a robust service layer in src/services/cricket/profile.py with the following class:

class CricketProfileService:
    @staticmethod
    async def create_sport_profile(user_id: UUID, request: SportProfileCreate, db: AsyncSession) -> SportProfileResponse
    
    @staticmethod
    async def get_sport_profile(profile_id: UUID, db: AsyncSession) -> SportProfileResponse
    
    @staticmethod
    async def create_cricket_profile(request: CricketPlayerProfileCreate, db: AsyncSession) -> CricketPlayerProfileResponse
    
    @staticmethod
    async def get_cricket_profile(profile_id: UUID, db: AsyncSession, include_stats: bool = True) -> CricketPlayerProfileDetailResponse
    
    @staticmethod
    async def update_cricket_profile(profile_id: UUID, request: CricketPlayerProfileUpdate, db: AsyncSession) -> CricketPlayerProfileResponse

Requirements:
- Proper error handling with custom exceptions (ProfileNotFoundError, DuplicateProfileError)
- Validation: user can only have ONE profile per sport
- Use async SQLAlchemy queries (select, update)
- Include database transaction management (commit/rollback)
- Add comprehensive logging with contextual info
- Return proper HTTP-ready responses
- Follow dependency injection pattern

Error Handling Pattern:
- Raise ValueError for validation errors (400)
- Raise PermissionError for unauthorized access (403)
- Raise LookupError for not found (404)
- Log all errors with request context

Code Quality:
- Type hints on all functions
- Docstrings with Args, Returns, Raises
- Single Responsibility Principle
- Keep functions under 50 lines
```

**Expected Output**: `src/services/cricket/profile.py` with CricketProfileService class

**Validation Steps**:
```bash
# 1. Syntax check
python -m py_compile src/services/cricket/profile.py

# 2. Run linter
flake8 src/services/cricket/profile.py --max-line-length=120

# 3. Type checking (if using mypy)
mypy src/services/cricket/profile.py

# 4. Write immediate unit test
cat > tests/unit/test_services/test_cricket_profile.py << 'EOF'
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.cricket.profile import CricketProfileService

@pytest.mark.asyncio
async def test_create_sport_profile_success():
    # Mock database session
    db = AsyncMock()
    # Test logic here
    pass
EOF

# 5. Run the test
pytest tests/unit/test_services/test_cricket_profile.py -v
```

### Step 1.3: API Router (HTTP Layer)

**AI Prompt Template**:
```
Context: Kreeda cricket scorekeeping app. Service layer complete in 
src/services/cricket/profile.py.

Task: Create API router in src/routers/cricket/profile.py following API_DESIGN.md 
sections 1.1-1.4.

Endpoints to implement:
1. POST /api/v1/profiles/sports - Create sport profile
2. GET /api/v1/profiles/sports - List my sport profiles
3. POST /api/v1/profiles/cricket - Create cricket player profile
4. GET /api/v1/profiles/cricket/{profile_id} - Get cricket profile details
5. PATCH /api/v1/profiles/cricket/{profile_id} - Update cricket profile

Requirements:
- Use FastAPI dependency injection (Depends)
- Authentication via JWT (get user_id from token)
- Proper HTTP status codes (201, 200, 404, 400, 403)
- Response models match API_DESIGN.md
- Error handling middleware
- Request validation
- Add OpenAPI tags and descriptions
- Include response examples

Response Format (wrap everything):
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "ISO8601",
    "request_id": "generated_uuid"
  }
}

Error Handling:
- 400: Validation errors → {"success": false, "error": {"code": "VALIDATION_ERROR", ...}}
- 401: Unauthorized → {"success": false, "error": {"code": "UNAUTHORIZED", ...}}
- 403: Forbidden → {"success": false, "error": {"code": "FORBIDDEN", ...}}
- 404: Not found → {"success": false, "error": {"code": "NOT_FOUND", ...}}
- 500: Server error → {"success": false, "error": {"code": "INTERNAL_ERROR", ...}}

Code Quality:
- Thin router layer (delegate to service)
- Proper async/await
- Use HTTPException
- Add logging for all requests
```

**Expected Output**: `src/routers/cricket/profile.py`

**Validation Steps**:
```bash
# 1. Register router in main.py
# Add: from src.routers.cricket.profile import router as cricket_profile_router
# Add: app.include_router(cricket_profile_router)

# 2. Restart FastAPI
docker-compose restart app

# 3. Check OpenAPI docs
open http://localhost:8000/docs

# 4. Test endpoint with curl
curl -X POST http://localhost:8000/api/v1/profiles/sports \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"sport_type": "CRICKET", "visibility": "PUBLIC"}'

# 5. Check logs
docker logs kreeda-backend-app-1 --tail=50
```

### Step 1.4: Integration Tests

**AI Prompt Template**:
```
Context: Kreeda app. I've implemented cricket profile endpoints in 
src/routers/cricket/profile.py and services in src/services/cricket/profile.py.

Task: Create comprehensive integration tests in tests/integration/test_cricket_profile_flow.py

Test Scenarios:
1. test_create_sport_profile_and_cricket_profile_success
   - Register user → Create sport profile → Create cricket profile
   - Verify database records created
   - Verify response format matches API_DESIGN.md

2. test_cannot_create_duplicate_sport_profile
   - Create sport profile for CRICKET
   - Attempt to create another CRICKET profile
   - Should return 400 error

3. test_get_cricket_profile_includes_career_stats
   - Create profile
   - Verify stats initialized to 0
   - Verify response includes all stat fields

4. test_update_cricket_profile_playing_role
   - Create profile as BATSMAN
   - Update to ALL_ROUNDER
   - Verify change persisted

5. test_unauthorized_access_returns_401
   - Attempt to create profile without token
   - Should return 401

Requirements:
- Use pytest fixtures from conftest.py
- Clean database state between tests (rollback)
- Use FastAPI TestClient for HTTP requests
- Assert status codes, response structure, database state
- Test both success and failure paths
- Mock external dependencies (email, Redis if needed)

Code Quality:
- Clear test names (test_what_when_expected)
- Arrange-Act-Assert pattern
- One assertion per logical concept
- Use parametrize for similar tests
```

**Expected Output**: `tests/integration/test_cricket_profile_flow.py`

**Run Tests**:
```bash
# 1. Create test database
docker exec -it kreeda-backend-db-1 psql -U kreeda_user -c "DROP DATABASE IF EXISTS test_kreeda;"
docker exec -it kreeda-backend-db-1 psql -U kreeda_user -c "CREATE DATABASE test_kreeda;"

# 2. Run migrations on test DB
DATABASE_URL=postgresql+asyncpg://kreeda_user:kreeda_pass@localhost/test_kreeda alembic upgrade head

# 3. Run tests with coverage
pytest tests/integration/test_cricket_profile_flow.py -v --cov=src/services/cricket --cov=src/routers/cricket --cov-report=html

# 4. Review coverage report
open htmlcov/index.html

# 5. Ensure >80% coverage before proceeding
```

### Step 1.5: Error Handling & Logging

**AI Prompt Template**:
```
Context: Cricket profile implementation complete. Need production-grade error handling.

Task: Create comprehensive error handling in src/core/exceptions.py and logging in src/core/logging.py

1. Custom Exception Classes:
class KreedaException(Exception):
    """Base exception"""
    
class ValidationError(KreedaException):
    """400 errors"""
    
class UnauthorizedError(KreedaException):
    """401 errors"""
    
class ForbiddenError(KreedaException):
    """403 errors"""
    
class NotFoundError(KreedaException):
    """404 errors"""
    
class ConflictError(KreedaException):
    """409 errors"""

2. Global Exception Handler:
Create middleware in src/middleware/error_handler.py that:
- Catches all exceptions
- Logs with full context (user_id, request_id, endpoint, payload)
- Returns standardized error response
- Sanitizes error messages for production
- Includes stack trace in logs (not in response)

3. Structured Logging:
Setup in src/core/logging.py:
- JSON formatted logs
- Include request_id, user_id, timestamp
- Different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Separate files for error logs
- Integration with Docker log driver

Requirements:
- Use Python's logging module
- Add request_id to all log entries
- Log all database queries in DEBUG mode
- Never log sensitive data (passwords, tokens)
- Add performance metrics (request duration)

Example Log Entry:
{
  "timestamp": "2025-10-30T15:32:45Z",
  "level": "ERROR",
  "request_id": "req_abc123",
  "user_id": "uuid-456",
  "endpoint": "/api/v1/profiles/cricket",
  "method": "POST",
  "error_type": "ValidationError",
  "error_message": "Invalid playing_role",
  "stack_trace": "...",
  "duration_ms": 45
}
```

**Expected Output**: 
- `src/core/exceptions.py`
- `src/core/logging.py`
- `src/middleware/error_handler.py`

**Validation**:
```bash
# 1. Register middleware in main.py
# Add: from src.middleware.error_handler import error_handler_middleware
# Add: app.add_middleware(error_handler_middleware)

# 2. Test error handling
curl -X POST http://localhost:8000/api/v1/profiles/cricket \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# 3. Check logs
docker logs kreeda-backend-app-1 --tail=20 | grep ERROR

# 4. Verify error response format
# Should match API_DESIGN.md error structure
```

---

## Quality Gates

### Before Committing Code

**Checklist**:
- [ ] All tests pass (`pytest -v`)
- [ ] Code coverage >80% for new code
- [ ] No linting errors (`flake8 src/`)
- [ ] Type hints present (`mypy src/`)
- [ ] Docstrings on all public functions
- [ ] No hardcoded values (use config/env vars)
- [ ] Error handling in place
- [ ] Logging added for key operations
- [ ] API matches API_DESIGN.md specification
- [ ] Database queries are async
- [ ] No N+1 query problems
- [ ] Sensitive data not logged
- [ ] Docker container builds successfully
- [ ] Manual testing done via Swagger/Postman

### Before Merging to Master

**Additional Checks**:
- [ ] Integration tests pass
- [ ] No breaking changes to existing APIs
- [ ] Database migration tested (up and down)
- [ ] Performance benchmarks met (<500ms P95)
- [ ] Memory leaks checked (if long-running tasks)
- [ ] Security review (SQL injection, XSS, CSRF)
- [ ] Code reviewed by at least one other person
- [ ] Documentation updated (if API changes)

---

## AI Prompt Templates

### Template 1: Implementing a New Feature

```
Context: [Brief project description + current state]

Task: [Specific component to build]

Requirements:
- [Functional requirement 1]
- [Functional requirement 2]
- [Non-functional requirement 1]

Constraints:
- Must follow [pattern/principle]
- Must match [design doc] specification
- Must use [technology/library]

Code Quality Standards:
- SOLID principles
- DRY (Don't Repeat Yourself)
- Type hints on all functions
- Comprehensive error handling
- Logging for debugging
- Unit testable design

Output Format:
- File path: [where to create]
- Include docstrings and comments
- Follow existing code style
```

### Template 2: Debugging an Issue

```
Context: [What you're trying to do]

Issue: [What's going wrong]

Error Message:
```
[Full error traceback]
```

Relevant Code:
[Paste relevant code sections]

Environment:
- Python version: 3.11
- FastAPI version: 0.104.1
- Running in: Docker

Expected Behavior: [What should happen]

Actual Behavior: [What's happening]

Question: [Specific question about the fix]

Requirements:
- Root cause analysis
- Proposed fix with explanation
- Prevention strategy for future
```

### Template 3: Code Review

```
Context: I've implemented [feature]. Please review for:

1. SOLID Principles Adherence
2. Security Vulnerabilities
3. Performance Issues
4. Error Handling Gaps
5. Testing Coverage
6. Code Smells

Code:
[Paste code or file content]

Specific Concerns:
- [Any specific area you're unsure about]

Output Format:
- Issues found (High/Medium/Low severity)
- Specific recommendations
- Refactoring suggestions if needed
```

---

## Error Handling Strategy

### 1. Exception Hierarchy

```python
# src/core/exceptions.py

class KreedaException(Exception):
    """Base exception for all Kreeda errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(KreedaException):
    """400 Bad Request - Invalid input data"""
    http_status = 400

class UnauthorizedError(KreedaException):
    """401 Unauthorized - Missing or invalid authentication"""
    http_status = 401

class ForbiddenError(KreedaException):
    """403 Forbidden - Insufficient permissions"""
    http_status = 403

class NotFoundError(KreedaException):
    """404 Not Found - Resource doesn't exist"""
    http_status = 404

class ConflictError(KreedaException):
    """409 Conflict - Resource already exists or state conflict"""
    http_status = 409

class InternalServerError(KreedaException):
    """500 Internal Server Error - Unexpected server error"""
    http_status = 500
```

### 2. Usage in Services

```python
# src/services/cricket/profile.py

from src.core.exceptions import NotFoundError, ConflictError, ValidationError

class CricketProfileService:
    @staticmethod
    async def create_sport_profile(user_id: UUID, request: SportProfileCreate, db: AsyncSession):
        # Check for duplicates
        existing = await db.execute(
            select(SportProfile).where(
                SportProfile.user_id == user_id,
                SportProfile.sport_type == request.sport_type
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError(
                message=f"User already has a {request.sport_type} profile",
                error_code="DUPLICATE_SPORT_PROFILE",
                details={"sport_type": request.sport_type}
            )
        
        # Validation
        if request.sport_type not in SportType:
            raise ValidationError(
                message="Invalid sport type",
                error_code="INVALID_SPORT_TYPE",
                details={"allowed_types": [s.value for s in SportType]}
            )
        
        # Create profile
        try:
            profile = SportProfile(**request.dict(), user_id=user_id)
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
            return SportProfileResponse.from_orm(profile)
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create sport profile: {e}", exc_info=True)
            raise InternalServerError(
                message="Failed to create profile",
                error_code="PROFILE_CREATION_FAILED"
            )
```

### 3. Global Error Handler

```python
# src/middleware/error_handler.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from src.core.exceptions import KreedaException
from src.core.logging import logger
import uuid
import time

async def error_handler_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()
    
    try:
        response = await call_next(request)
        return response
    except KreedaException as e:
        duration = (time.time() - start_time) * 1000
        logger.error(
            f"Kreeda error: {e.error_code}",
            extra={
                "request_id": request_id,
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details,
                "endpoint": str(request.url),
                "method": request.method,
                "duration_ms": duration
            }
        )
        return JSONResponse(
            status_code=e.http_status,
            content={
                "success": False,
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                },
                "meta": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "request_id": request_id
                }
            }
        )
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.critical(
            f"Unhandled exception: {str(e)}",
            exc_info=True,
            extra={
                "request_id": request_id,
                "endpoint": str(request.url),
                "method": request.method,
                "duration_ms": duration
            }
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred"
                },
                "meta": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "request_id": request_id
                }
            }
        )
```

---

## Testing Strategy

### Test Pyramid

```
       /\
      /E2E\         <- 10% (End-to-End via HTTP)
     /------\
    /Integration\   <- 30% (Service + DB)
   /------------\
  /    Unit      \  <- 60% (Pure logic, mocked DB)
 /----------------\
```

### Unit Tests (60% of tests)

**Focus**: Business logic in services, validators, utilities

```python
# tests/unit/test_services/test_cricket_profile.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from src.services.cricket.profile import CricketProfileService
from src.core.exceptions import ConflictError, NotFoundError

@pytest.mark.asyncio
async def test_create_sport_profile_duplicate_raises_conflict():
    # Arrange
    user_id = uuid4()
    request = MagicMock(sport_type=SportType.CRICKET)
    db = AsyncMock()
    
    # Mock existing profile found
    existing_result = MagicMock()
    existing_result.scalar_one_or_none.return_value = MagicMock()
    db.execute.return_value = existing_result
    
    # Act & Assert
    with pytest.raises(ConflictError) as exc_info:
        await CricketProfileService.create_sport_profile(user_id, request, db)
    
    assert exc_info.value.error_code == "DUPLICATE_SPORT_PROFILE"
    assert "already has" in exc_info.value.message

@pytest.mark.asyncio
async def test_get_cricket_profile_not_found_raises_error():
    # Arrange
    profile_id = uuid4()
    db = AsyncMock()
    
    # Mock no profile found
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result
    
    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await CricketProfileService.get_cricket_profile(profile_id, db)
    
    assert exc_info.value.error_code == "PROFILE_NOT_FOUND"
```

### Integration Tests (30% of tests)

**Focus**: Service + Database interaction, full request flow

```python
# tests/integration/test_cricket_profile_flow.py

import pytest
from httpx import AsyncClient
from src.main import app
from src.database.connection import get_db
from src.models.user_auth import UserAuth
from src.models.sport_profile import SportProfile

@pytest.mark.asyncio
async def test_complete_profile_creation_flow(db_session, test_user):
    """Test: User creates sport profile, then cricket profile"""
    
    # Create sport profile
    sport_profile = SportProfile(
        user_id=test_user.user_id,
        sport_type=SportType.CRICKET,
        visibility=ProfileVisibility.PUBLIC
    )
    db_session.add(sport_profile)
    await db_session.commit()
    await db_session.refresh(sport_profile)
    
    # Create cricket profile
    cricket_profile = CricketPlayerProfile(
        sport_profile_id=sport_profile.id,
        playing_role=PlayingRole.BATSMAN,
        batting_style=BattingStyle.RIGHT_HAND
    )
    db_session.add(cricket_profile)
    await db_session.commit()
    await db_session.refresh(cricket_profile)
    
    # Verify
    assert cricket_profile.id is not None
    assert cricket_profile.matches_played == 0
    assert cricket_profile.total_runs == 0
    
    # Verify database state
    from sqlalchemy import select
    result = await db_session.execute(
        select(CricketPlayerProfile).where(
            CricketPlayerProfile.sport_profile_id == sport_profile.id
        )
    )
    fetched = result.scalar_one()
    assert fetched.playing_role == PlayingRole.BATSMAN
```

### E2E Tests (10% of tests)

**Focus**: Full HTTP request/response cycle

```python
# tests/e2e/test_cricket_profile_api.py

import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_create_cricket_profile_via_api(auth_headers):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create sport profile
        response = await client.post(
            "/api/v1/profiles/sports",
            json={"sport_type": "CRICKET", "visibility": "PUBLIC"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        sport_profile_id = data["data"]["id"]
        
        # Create cricket profile
        response = await client.post(
            "/api/v1/profiles/cricket",
            json={
                "sport_profile_id": sport_profile_id,
                "playing_role": "BATSMAN",
                "batting_style": "RIGHT_HAND"
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["playing_role"] == "BATSMAN"
        assert "career_stats" in data["data"]
```

---

## Code Review Checklist

### Self-Review Before Commit

**SOLID Principles**:
- [ ] **S**ingle Responsibility: Each class/function has one clear purpose
- [ ] **O**pen/Closed: Can extend behavior without modifying existing code
- [ ] **L**iskov Substitution: Subclasses can replace base classes
- [ ] **I**nterface Segregation: No forced implementation of unused methods
- [ ] **D**ependency Inversion: Depend on abstractions, not concretions

**Code Quality**:
- [ ] No code duplication (DRY principle)
- [ ] No magic numbers (use constants/config)
- [ ] Functions <50 lines, classes <300 lines
- [ ] Meaningful variable/function names
- [ ] No commented-out code
- [ ] No print() statements (use logger)
- [ ] No TODO comments without tickets

**Error Handling**:
- [ ] All errors are caught and logged
- [ ] Custom exceptions used appropriately
- [ ] Validation errors return 400 with details
- [ ] Database errors trigger rollback
- [ ] No bare except: clauses

**Security**:
- [ ] No SQL injection vulnerabilities (use ORM)
- [ ] No sensitive data in logs
- [ ] Authentication checked on protected routes
- [ ] Input validation on all endpoints
- [ ] CORS configured correctly
- [ ] No hardcoded secrets

**Performance**:
- [ ] No N+1 queries (use joinedload)
- [ ] Database queries have indexes
- [ ] Async/await used correctly
- [ ] No blocking I/O operations
- [ ] Pagination on list endpoints

**Testing**:
- [ ] Unit tests for business logic
- [ ] Integration tests for DB operations
- [ ] E2E tests for critical flows
- [ ] Edge cases covered
- [ ] Error paths tested

**Documentation**:
- [ ] Docstrings on public functions
- [ ] API changes reflected in API_DESIGN.md
- [ ] Schema changes have migrations
- [ ] README updated if setup changed

---

## Daily Development Workflow

### Morning Routine
```bash
# 1. Pull latest changes
git pull origin master

# 2. Start Docker services
docker-compose up -d

# 3. Check service health
docker-compose ps
docker logs kreeda-backend-app-1 --tail=10

# 4. Run migrations
alembic upgrade head

# 5. Run tests to ensure baseline
pytest -v

# 6. Create feature branch
git checkout -b feature/[today's-work]
```

### During Development
```bash
# 1. Make changes

# 2. Run tests frequently
pytest tests/unit/test_services/test_[your_module].py -v

# 3. Check in browser/Postman
open http://localhost:8000/docs

# 4. Check logs
docker logs kreeda-backend-app-1 -f

# 5. Commit often
git add .
git commit -m "feat: add cricket profile creation"
```

### Before Push
```bash
# 1. Run full test suite
pytest -v --cov=src --cov-report=html

# 2. Check coverage
open htmlcov/index.html

# 3. Run linter
flake8 src/ --max-line-length=120

# 4. Type check
mypy src/

# 5. Check for secrets
git diff | grep -i "password\|secret\|key"

# 6. Push
git push origin feature/[your-branch]
```

---

## Success Metrics

### Code Quality Metrics
- **Test Coverage**: >80% for all new code
- **Code Duplication**: <3% (use `radon`)
- **Cyclomatic Complexity**: <10 per function
- **Documentation**: 100% of public APIs

### Performance Metrics
- **Response Time**: P50 <100ms, P95 <500ms, P99 <1000ms
- **Database Queries**: <5 queries per endpoint
- **Memory Usage**: <512MB per container
- **Error Rate**: <0.1% in production

### Development Velocity
- **Build Time**: <2 minutes
- **Test Execution**: <5 minutes for full suite
- **Deployment**: <10 minutes from push to production

---

## Key Takeaways

1. **Design First**: Always consult API_DESIGN.md and schema.md before coding
2. **Test as You Build**: Write tests immediately after implementation
3. **Error Handling is Not Optional**: Every service method must handle errors
4. **Log Everything**: But never log sensitive data
5. **Docker is Your Environment**: If it works locally but not in Docker, it's broken
6. **SOLID Principles**: They exist for a reason - follow them
7. **Code Review Yourself**: Use the checklist before asking others
8. **AI is a Tool**: Verify everything it generates, don't blindly trust
9. **Incremental Progress**: Small, tested commits > large, untested dumps
10. **Documentation is Code**: Update docs with every API change

---

**Remember**: Code is read 10x more than it's written. Write code for the next developer (which might be future you).
