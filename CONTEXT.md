# Kreeda Backend - Context for Development

> **Master Reference Document for GitHub Copilot & Development Team**
> 
> This document provides comprehensive context about the Kreeda backend project to enable AI-assisted development and onboard new team members.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Design Patterns](#architecture--design-patterns)
3. [Technology Stack](#technology-stack)
4. [Database Schema](#database-schema)
5. [API Specifications](#api-specifications)
6. [Authentication & Security](#authentication--security)
7. [Testing Strategy](#testing-strategy)
8. [Code Standards & Conventions](#code-standards--conventions)
9. [Business Rules & Constraints](#business-rules--constraints)
10. [Common Patterns & Examples](#common-patterns--examples)

---

## Project Overview

### What is Kreeda?

Kreeda is a **digital scorekeeping application** backend built with FastAPI. The system provides:
- Supabase-compatible authentication system
- User profile management
- Real-time session handling with Redis
- Comprehensive test coverage (80%+ target)
- Production-ready logging and monitoring

### Project Goals

1. **Test-Driven Development**: Every feature must have corresponding unit and integration tests
2. **CI/CD Integration**: Automated testing and deployment pipeline
3. **Production-Ready**: Enterprise-level security, logging, and error handling
4. **Developer-Friendly**: Clear documentation, consistent patterns, and helpful error messages
5. **Scalable Architecture**: Designed to handle growth in users and features

### Current Status

- ✅ User authentication (register, login, token refresh)
- ✅ User profile management (CRUD operations)
- ✅ Email verification workflow
- ✅ Password recovery system
- ✅ Comprehensive test suite (pytest)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ Docker containerization
- ✅ Database migrations (Alembic)

---

## Architecture & Design Patterns

### Layered Architecture

```
┌─────────────────────────────────────┐
│         Routers (API Layer)         │  ← HTTP endpoints, request validation
├─────────────────────────────────────┤
│       Services (Business Logic)     │  ← Core business logic, orchestration
├─────────────────────────────────────┤
│     Models (Data Access Layer)      │  ← SQLAlchemy ORM models
├─────────────────────────────────────┤
│      Database (PostgreSQL)          │  ← Data persistence
└─────────────────────────────────────┘

       Supporting Layers:
       ├── Schemas (Pydantic) - Data validation
       ├── Utils - Shared utilities
       └── Core - Security, config
```

### Design Patterns Used

#### 1. **Dependency Injection**
```python
# Database session injection
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)  # ← Injected
):
    return await AuthService.get_user(user_id, db)
```

#### 2. **Service Layer Pattern**
- All business logic is in service classes (`AuthService`, `UserProfileService`)
- Routers are thin, focusing only on HTTP concerns
- Services are stateless and use static methods

#### 3. **Repository Pattern** (Implicit via SQLAlchemy)
```python
# Data access abstracted through SQLAlchemy
result = await db.execute(select(UserAuth).where(UserAuth.email == email))
user = result.scalar_one_or_none()
```

#### 4. **DTO Pattern** (via Pydantic Schemas)
```python
# Request/Response DTOs
class UserRegisterRequest(BaseModel):
    email: str
    password: str
    phone_number: Optional[str] = None
```

---

## Technology Stack

### Core Framework
- **FastAPI** (0.104.1) - Modern, high-performance web framework
- **Uvicorn** (0.24.0) - ASGI server
- **Python** (3.11+) - Programming language

### Database & ORM
- **PostgreSQL** (15) - Primary database
- **SQLAlchemy** (2.0.23) - ORM with async support
- **Alembic** (1.13.1) - Database migrations
- **asyncpg** (0.29.0) - PostgreSQL async driver

### Caching & Sessions
- **Redis** (7) - Session storage, caching, OTP storage
- **redis-py** (5.0.1) - Redis client

### Authentication & Security
- **PyJWT** (2.8.0) - JWT token generation/validation
- **passlib** (1.7.4) + **bcrypt** (4.0.1) - Password hashing
- **pydantic[email]** (2.5.0) - Email validation

### Testing
- **pytest** (7.4.3) - Test framework
- **pytest-asyncio** (0.21.1) - Async test support
- **pytest-cov** (4.1.0) - Coverage reporting
- **httpx** (0.25.1) - HTTP client for testing

### Development Tools
- **Docker** + **Docker Compose** - Containerization
- **GitHub Actions** - CI/CD pipeline
- **flake8** + **black** - Code linting and formatting

---

## Database Schema

### Tables Overview

#### `user_auth` - Authentication Data
```sql
CREATE TABLE user_auth (
    user_id UUID PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    password_hash VARCHAR NOT NULL,
    phone_number VARCHAR,
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_phone_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

**Purpose**: Stores authentication credentials and verification status

**Key Fields**:
- `user_id`: Unique identifier (UUID)
- `email`: Unique email address (used for login)
- `password_hash`: Bcrypt hashed password
- `is_email_verified`: Email verification status
- `is_active`: Soft delete / account status

#### `user_profiles` - User Profile Data
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES user_auth(user_id),
    name VARCHAR,
    avatar_url VARCHAR,
    location VARCHAR,
    date_of_birth DATE,
    bio TEXT,
    preferences JSON,
    roles JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Purpose**: Stores user profile information and preferences

**Key Fields**:
- `user_id`: Foreign key to user_auth
- `preferences`: JSON field for user settings
- `roles`: JSON array of user roles

### SQLAlchemy Models

#### UserAuth Model
```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime
from uuid import UUID

class UserAuth(Base):
    __tablename__ = "user_auth"
    
    user_id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

**Note**: Using SQLAlchemy 2.0 `Mapped` types for better type safety

---

## API Specifications

### Authentication Endpoints

#### POST `/auth/register`
Register a new user account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "phone_number": "+1234567890",
  "name": "John Doe"
}
```

**Response** (201 Created):
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "created_at": "2024-10-11T12:00:00Z",
    ...
  },
  "session": {
    "access_token": "eyJ0eXAi...",
    "refresh_token": "eyJ0eXAi...",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

**Validation Rules**:
- Password: Min 8 chars, must contain uppercase, lowercase, digit, special char
- Email: Valid email format
- Phone: Optional, must be valid format if provided

#### POST `/auth/signin/password`
Login with email and password.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):
```json
{
  "user": { /* user object */ },
  "session": { /* session object */ }
}
```

**Error Cases**:
- 401: Invalid credentials
- 400: Missing required fields
- 403: Account not active

#### GET `/auth/user`
Get current authenticated user.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "phone": "+1234567890",
  "app_metadata": { /* ... */ },
  "user_metadata": { /* ... */ }
}
```

#### POST `/auth/token`
Refresh access token using refresh token.

**Request Body**:
```json
{
  "refresh_token": "eyJ0eXAi..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

#### PUT `/auth/user`
Update user information (email, password, phone).

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "email": "newemail@example.com",
  "password": "NewSecurePass123!",
  "phone": "+9876543210"
}
```

**Response** (200 OK): Updated user object

**Notes**:
- Changing email resets `is_email_verified` to false
- Changing phone resets `is_phone_verified` to false
- All fields are optional

#### POST `/auth/recover`
Initiate password recovery.

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Response** (200 OK):
```json
{
  "message": "Password recovery email sent"
}
```

**Notes**:
- Always returns success to prevent email enumeration
- Sends email with password reset token (if email exists)
- Token expires in 1 hour

#### POST `/auth/signout`
Sign out user (invalidate session).

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "message": "Signed out successfully"
}
```

### User Profile Endpoints

#### GET `/user/profile/`
Get current user's profile.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "John Doe",
  "avatar_url": "https://...",
  "location": "San Francisco",
  "date_of_birth": "1990-01-01",
  "bio": "Software developer",
  "preferences": {},
  "roles": ["user"],
  "created_at": "2024-10-11T12:00:00Z",
  "updated_at": "2024-10-11T12:00:00Z"
}
```

#### PUT `/user/profile/`
Update current user's profile.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "name": "Jane Doe",
  "location": "New York",
  "bio": "Updated bio",
  "preferences": {"theme": "dark"}
}
```

**Response** (200 OK): Updated profile object

---

## Authentication & Security

### Password Security

#### Hashing Algorithm
- **Algorithm**: Bcrypt
- **Rounds**: 12 (default in passlib)
- **Library**: `passlib.hash.bcrypt`

```python
from passlib.hash import bcrypt

# Hash password
password_hash = bcrypt.hash("user_password")

# Verify password
is_valid = bcrypt.verify("user_password", password_hash)
```

#### Password Validation Rules
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
- Not in common password list

**Implementation**: `src/utils/validators.py`

### JWT Token System

#### Token Types
1. **Access Token**: Short-lived (1 hour), used for API authentication
2. **Refresh Token**: Long-lived (30 days), used to obtain new access tokens

#### Token Structure
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "type": "access" | "refresh",
  "exp": 1234567890,
  "iat": 1234567890
}
```

#### Token Generation
```python
import jwt
from datetime import datetime, timedelta

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": str(user_id),
        "email": email,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
```

#### Token Storage
- **Access Token**: Client-side (memory, not localStorage)
- **Refresh Token**: 
  - Redis: Key `refresh_token:{user_id}`, TTL 30 days
  - Client-side: Secure, HttpOnly cookie (recommended for web)

### Redis Session Management

#### Session Storage Pattern
```python
# Store refresh token
await redis_client.set(
    f"refresh_token:{user_id}",
    refresh_token,
    ex=30 * 24 * 60 * 60  # 30 days
)

# Validate refresh token
stored_token = await redis_client.get(f"refresh_token:{user_id}")
if stored_token == refresh_token:
    # Valid
```

#### OTP Storage Pattern
```python
# Store OTP
await redis_client.set(
    f"otp:{email}",
    otp_code,
    ex=600  # 10 minutes
)

# Verify and delete OTP
stored_otp = await redis_client.get(f"otp:{email}")
if stored_otp == otp_code:
    await redis_client.delete(f"otp:{email}")
    # Valid
```

---

## Testing Strategy

### Test Pyramid

```
         /\
        /E2E\         ← Integration Tests (10%)
       /------\
      /        \
     /  Integ.  \     ← Integration Tests (30%)
    /------------\
   /              \
  /   Unit Tests   \  ← Unit Tests (60%)
 /------------------\
```

### Test Structure

```
tests/
├── conftest.py           # Fixtures, test database setup
├── test_auth.py          # Authentication endpoint tests
├── test_user_profile.py  # Profile management tests
└── test_integration.py   # End-to-end journey tests
```

### Test Fixtures (conftest.py)

```python
@pytest_asyncio.fixture
async def test_db():
    """Provide test database session"""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def test_user(test_db):
    """Create a test user"""
    user_auth = UserAuth(
        user_id=uuid4(),
        email="test@example.com",
        password_hash=hash_password("Test@123456"),
        is_email_verified=True,
        is_active=True
    )
    test_db.add(user_auth)
    await test_db.commit()
    return user_auth
```

### Testing Patterns

#### 1. Unit Tests (Services & Utilities)
```python
@pytest.mark.unit
async def test_register_user_success(test_db):
    """Test successful user registration"""
    request = UserRegisterRequest(
        email="newuser@example.com",
        password="SecurePass123!",
        phone_number="+1234567890"
    )
    
    result = await AuthService.register(request, test_db)
    
    assert result.user.email == "newuser@example.com"
    assert result.session.access_token is not None
    assert result.session.refresh_token is not None
```

#### 2. Integration Tests (API Endpoints)
```python
@pytest.mark.integration
async def test_register_and_login_flow(client):
    """Test complete registration and login flow"""
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

#### 3. Error Case Testing
```python
async def test_register_duplicate_email(test_db, test_user):
    """Test registration with existing email"""
    request = UserRegisterRequest(
        email=test_user.email,  # Duplicate
        password="Test@123456"
    )
    
    with pytest.raises(ValueError, match="already registered"):
        await AuthService.register(request, test_db)
```

### Coverage Requirements
- **Overall**: 80% minimum
- **Critical Paths**: 100% (auth, payments)
- **Utils**: 90%
- **Routers**: 85%

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific markers
pytest -m unit
pytest -m integration

# Specific file
pytest tests/test_auth.py -v

# Specific test
pytest tests/test_auth.py::test_register_user_success -v
```

---

## Code Standards & Conventions

### File Organization

```
src/
├── config/          # Application configuration
├── core/            # Core utilities (security, etc.)
├── database/        # Database connection, session management
├── models/          # SQLAlchemy ORM models
├── routers/         # FastAPI route handlers
├── schemas/         # Pydantic models (DTOs)
├── services/        # Business logic layer
└── utils/           # Shared utilities
```

### Naming Conventions

#### Files & Modules
- **Snake Case**: `user_profile.py`, `auth_service.py`
- **Descriptive**: File name should reflect content

#### Classes
- **PascalCase**: `UserAuth`, `AuthService`, `UserRegisterRequest`
- **Suffixes**: 
  - Models: `User`, `UserAuth`
  - Services: `AuthService`, `UserProfileService`
  - Schemas: `UserRequest`, `UserResponse`

#### Functions & Methods
- **Snake Case**: `get_user()`, `create_access_token()`
- **Verbs**: Start with action verb (get, create, update, delete, validate)

#### Variables
- **Snake Case**: `user_id`, `access_token`, `is_verified`
- **Descriptive**: Avoid abbreviations unless common (id, url, etc.)

### Type Hints

**Always use type hints for function signatures:**

```python
from typing import Optional, List
from uuid import UUID

async def get_user(
    user_id: UUID,
    db: AsyncSession
) -> Optional[UserAuth]:
    """Get user by ID"""
    result = await db.execute(
        select(UserAuth).where(UserAuth.user_id == user_id)
    )
    return result.scalar_one_or_none()
```

### Docstrings

**Use docstrings for all public functions:**

```python
async def register(
    request: UserRegisterRequest,
    db: AsyncSession
) -> AuthResponse:
    """
    Register a new user account.
    
    Args:
        request: User registration data (email, password, etc.)
        db: Database session
        
    Returns:
        AuthResponse containing user data and session tokens
        
    Raises:
        ValueError: If email already exists or password is weak
    """
    # Implementation...
```

### Error Handling

**Use specific exceptions with descriptive messages:**

```python
# Good
if not user_auth:
    raise ValueError(f"User with email {email} not found")

# Bad
if not user_auth:
    raise Exception("Error")
```

**Handle async exceptions properly:**

```python
try:
    await db.commit()
except Exception as e:
    await db.rollback()
    logger.error(f"Database error: {e}")
    raise
```

### Async/Await Usage

**Always use async for database operations:**

```python
# Good
async def get_user(user_id: str, db: AsyncSession):
    result = await db.execute(select(UserAuth).where(...))
    return result.scalar_one_or_none()

# Bad (blocking)
def get_user(user_id: str, db: Session):
    return db.query(UserAuth).filter(...).first()
```

### Logging

**Use structured logging:**

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Good
logger.info(f"User registered: {user_id}", extra={
    "user_id": user_id,
    "email": email
})

# Bad
print(f"User registered: {user_id}")
```

---

## Business Rules & Constraints

### User Registration
1. Email must be unique across the system
2. Password must meet strength requirements (see Password Security)
3. Email verification is required for full access (future)
4. Phone number is optional but must be valid if provided
5. User profile is automatically created upon registration

### Authentication
1. Access tokens expire after 1 hour
2. Refresh tokens expire after 30 days
3. Users cannot have multiple active sessions (single device)
4. Inactive accounts (is_active=false) cannot login

### Password Management
1. Passwords must be hashed with bcrypt (12 rounds)
2. Password reset tokens expire after 1 hour
3. Old passwords cannot be reused (future: password history)
4. Password must be changed if weak on next login (future)

### Email Verification
1. Verification email sent immediately upon registration
2. Verification token expires after 24 hours
3. User can request resend (max 3 times per hour)
4. Changing email resets verification status

### Rate Limiting (Future)
1. Login attempts: 5 per 15 minutes per IP
2. Registration: 3 per hour per IP
3. Password reset: 3 per hour per email
4. OTP requests: 3 per hour per phone/email

### Data Privacy
1. User can request data export (GDPR compliance - future)
2. User can request account deletion (soft delete)
3. Deleted accounts retained for 30 days before hard delete
4. Personal data encrypted at rest (future)

---

## Common Patterns & Examples

### Creating a New Endpoint

#### Step 1: Define Pydantic Schema (schemas/)
```python
# src/schemas/example.py
from pydantic import BaseModel

class ExampleRequest(BaseModel):
    field1: str
    field2: Optional[int] = None

class ExampleResponse(BaseModel):
    id: UUID
    field1: str
    created_at: datetime
```

#### Step 2: Create Service Method (services/)
```python
# src/services/example.py
from sqlalchemy.ext.asyncio import AsyncSession

class ExampleService:
    @staticmethod
    async def create_example(
        request: ExampleRequest,
        db: AsyncSession
    ) -> ExampleResponse:
        """Create new example"""
        # Business logic here
        example = Example(...)
        db.add(example)
        await db.commit()
        await db.refresh(example)
        return ExampleResponse.model_validate(example)
```

#### Step 3: Add Router Endpoint (routers/)
```python
# src/routers/example.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/example", tags=["example"])

@router.post("/", response_model=ExampleResponse)
async def create_example(
    request: ExampleRequest,
    current_user: UserAuth = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new example"""
    return await ExampleService.create_example(request, db)
```

#### Step 4: Register Router (main.py)
```python
# src/main.py
from src.routers.example import router as example_router

app.include_router(example_router)
```

#### Step 5: Write Tests
```python
# tests/test_example.py
@pytest.mark.unit
async def test_create_example(test_db):
    request = ExampleRequest(field1="test")
    result = await ExampleService.create_example(request, test_db)
    assert result.field1 == "test"
```

### Database Query Patterns

#### Select with Filter
```python
from sqlalchemy import select

result = await db.execute(
    select(UserAuth).where(UserAuth.email == email)
)
user = result.scalar_one_or_none()
```

#### Select with Multiple Filters
```python
result = await db.execute(
    select(UserAuth)
    .where(UserAuth.email == email)
    .where(UserAuth.is_active == True)
)
user = result.scalar_one_or_none()
```

#### Select with Join
```python
result = await db.execute(
    select(UserAuth, UserProfile)
    .join(UserProfile, UserAuth.user_id == UserProfile.user_id)
    .where(UserAuth.email == email)
)
user, profile = result.first()
```

#### Update
```python
user = await db.get(UserAuth, user_id)
user.email = new_email
user.updated_at = datetime.utcnow()
await db.commit()
await db.refresh(user)
```

#### Delete (Soft)
```python
user = await db.get(UserAuth, user_id)
user.is_active = False
await db.commit()
```

### Redis Cache Pattern

```python
from src.utils.redis_client import redis_client

# Cache user data
async def get_user_cached(user_id: str) -> Optional[dict]:
    # Try cache first
    cached = await redis_client.get(f"user:{user_id}")
    if cached:
        return cached
    
    # Fetch from database
    user = await db.get(UserAuth, user_id)
    if user:
        user_dict = {
            "id": str(user.user_id),
            "email": user.email,
            # ... other fields
        }
        # Cache for 1 hour
        await redis_client.set(
            f"user:{user_id}",
            user_dict,
            ex=3600
        )
        return user_dict
    
    return None
```

### Background Task Pattern (Future)

```python
from fastapi import BackgroundTasks

async def send_email_background(email: str, subject: str, body: str):
    """Send email in background"""
    # Email sending logic
    pass

@router.post("/send-welcome")
async def send_welcome_email(
    user_id: str,
    background_tasks: BackgroundTasks
):
    """Send welcome email"""
    user = await get_user(user_id)
    background_tasks.add_task(
        send_email_background,
        user.email,
        "Welcome to Kreeda",
        "Welcome message..."
    )
    return {"message": "Email queued"}
```

### Dependency Injection Pattern

```python
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserAuth:
    """Get current authenticated user"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.get(UserAuth, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

## Development Workflow

### Adding a New Feature

1. **Create Branch**: `git checkout -b feature/feature-name`
2. **Write Tests First** (TDD):
   ```python
   # tests/test_new_feature.py
   async def test_new_feature():
       # Test implementation
       pass
   ```
3. **Implement Feature**:
   - Add schema if needed
   - Add service method
   - Add router endpoint
4. **Run Tests**: `pytest tests/test_new_feature.py -v`
5. **Check Coverage**: `pytest --cov=src`
6. **Lint Code**: `black src/ && flake8 src/`
7. **Commit**: `git commit -m "feat: add new feature"`
8. **Push**: `git push origin feature/feature-name`
9. **Create PR**: CI/CD will run tests automatically

### Database Migration Workflow

1. **Modify Model**:
   ```python
   # src/models/user_auth.py
   class UserAuth(Base):
       # Add new field
       new_field: Mapped[str] = mapped_column(String)
   ```

2. **Generate Migration**:
   ```bash
   alembic revision --autogenerate -m "Add new_field to user_auth"
   ```

3. **Review Migration**:
   ```python
   # alembic/versions/xxxxx_add_new_field.py
   def upgrade():
       op.add_column('user_auth', sa.Column('new_field', sa.String()))
   
   def downgrade():
       op.drop_column('user_auth', 'new_field')
   ```

4. **Apply Migration**:
   ```bash
   alembic upgrade head
   ```

5. **Test Migration**:
   ```bash
   # Rollback
   alembic downgrade -1
   # Re-apply
   alembic upgrade head
   ```

---

## Troubleshooting Guide

### Common Issues

#### 1. Database Connection Error
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution**:
- Check if PostgreSQL is running: `docker-compose ps`
- Verify DATABASE_URL in `.env`
- Check database logs: `docker-compose logs db`

#### 2. Redis Connection Error
```
redis.exceptions.ConnectionError: Connection refused
```
**Solution**:
- Check if Redis is running: `docker-compose ps`
- Verify REDIS_URL in `.env`
- Test connection: `docker-compose exec redis redis-cli ping`

#### 3. JWT Token Invalid
```
fastapi.exceptions.HTTPException: 401 Unauthorized
```
**Solution**:
- Check JWT_SECRET matches across environments
- Verify token hasn't expired
- Check token format: `Bearer <token>`

#### 4. Migration Conflicts
```
alembic.util.exc.CommandError: Target database is not up to date
```
**Solution**:
```bash
# Check current version
alembic current

# View pending migrations
alembic heads

# Stamp to specific version if needed
alembic stamp head
```

---

## Performance Optimization

### Database Query Optimization

1. **Use Select Loading** (avoid N+1 queries):
```python
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(UserAuth)
    .options(selectinload(UserAuth.profile))
    .where(UserAuth.email == email)
)
```

2. **Use Indexes**:
```python
# In model
class UserAuth(Base):
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
```

3. **Connection Pooling** (already configured):
```python
engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

### Redis Caching Strategy

1. **Cache Frequently Accessed Data**:
   - User profiles
   - Session data
   - Configuration

2. **Set Appropriate TTLs**:
   - User data: 1 hour
   - Session: Token expiry
   - OTP: 10 minutes

3. **Use Redis Pipelines for Batch Operations**:
```python
pipe = redis_client.pipeline()
pipe.set("key1", "value1")
pipe.set("key2", "value2")
await pipe.execute()
```

---

## Security Best Practices

### 1. Input Validation
- Always use Pydantic schemas for request validation
- Sanitize user input (no SQL injection via ORM)
- Validate file uploads (size, type)

### 2. Authentication
- Use HTTPS in production (TLS/SSL)
- Implement token rotation
- Set appropriate token expiry times
- Use secure cookie flags (HttpOnly, Secure, SameSite)

### 3. Authorization
- Check user permissions in service layer
- Use dependency injection for auth checks
- Implement role-based access control (RBAC)

### 4. Data Protection
- Never log passwords or tokens
- Use environment variables for secrets
- Encrypt sensitive data at rest (future)
- Implement audit logging

### 5. Rate Limiting
- Implement per-IP rate limiting (future)
- Implement per-user rate limiting (future)
- Use Redis for rate limit counters

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Application
APP_ENV=development
DEBUG=True

# Email (Future)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

---

## Conclusion

This document provides the essential context for developing the Kreeda backend. It should be:
- **Referenced** when implementing new features
- **Updated** when architecture changes
- **Used** as a prompt for GitHub Copilot
- **Shared** with new team members for onboarding

For specific implementation tasks, refer to:
- **TODO.md** - Development checklist
- **QUICK_REFERENCE.md** - Common commands and snippets
- **DOCUMENTATION_SUMMARY.md** - Documentation overview
