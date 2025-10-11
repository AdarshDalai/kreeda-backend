# Kreeda Backend - Development TODO Checklist

> **Development Roadmap with Testing & CI/CD Verification**
>
> This document provides a step-by-step development checklist organized by sprints. Each task includes testing requirements and CI/CD verification steps to ensure quality at every stage.

## Table of Contents

1. [Pre-Development Setup](#pre-development-setup)
2. [Sprint 1: Foundation & Core Authentication](#sprint-1-foundation--core-authentication)
3. [Sprint 2: User Profile & Email Verification](#sprint-2-user-profile--email-verification)
4. [Sprint 3: Advanced Authentication Features](#sprint-3-advanced-authentication-features)
5. [Sprint 4: Testing & Quality Assurance](#sprint-4-testing--quality-assurance)
6. [Sprint 5: Cricket Module - Data Models](#sprint-5-cricket-module---data-models)
7. [Sprint 6: Cricket Module - Match Management](#sprint-6-cricket-module---match-management)
8. [Sprint 7: Cricket Module - Scorekeeping](#sprint-7-cricket-module---scorekeeping)
9. [Sprint 8: Deployment & Monitoring](#sprint-8-deployment--monitoring)
10. [Definition of Done](#definition-of-done)

---

## Pre-Development Setup

### ✅ Environment Setup
- [x] Install Python 3.11+
- [x] Install Docker & Docker Compose
- [x] Install PostgreSQL (via Docker)
- [x] Install Redis (via Docker)
- [x] Clone repository
- [x] Create virtual environment
- [x] Install dependencies

### ✅ Project Initialization
- [x] Set up FastAPI project structure
- [x] Configure SQLAlchemy with async support
- [x] Set up Alembic for migrations
- [x] Configure environment variables (.env)
- [x] Set up basic logging

### ✅ Testing Infrastructure
- [x] Install pytest and pytest-asyncio
- [x] Configure pytest.ini
- [x] Set up test database
- [x] Create conftest.py with fixtures
- [x] Configure coverage reporting

### ✅ CI/CD Pipeline
- [x] Set up GitHub Actions workflow
- [x] Configure automated testing
- [x] Add linting (flake8, black)
- [x] Add coverage reporting
- [x] Configure Docker build

**Verification**:
```bash
# Run tests
pytest --version
pytest tests/ -v

# Check Docker
docker-compose up -d
docker-compose ps

# Verify CI/CD
git push origin main
# Check GitHub Actions tab
```

---

## Sprint 1: Foundation & Core Authentication

**Goal**: Implement basic authentication system with user registration and login.

### Task 1.1: Database Models - User Authentication ✅

#### Implementation
- [x] Create `UserAuth` model in `src/models/user_auth.py`
  - [x] Fields: user_id, email, password_hash, phone_number
  - [x] Fields: is_email_verified, is_phone_verified, is_active
  - [x] Fields: last_login, created_at
  - [x] Use SQLAlchemy 2.0 Mapped types
  
#### Testing
- [x] Write model tests in `tests/test_models.py`
  - [x] Test model creation
  - [x] Test field validation
  - [x] Test unique constraints

#### Verification
```bash
# Run tests
pytest tests/test_models.py::test_user_auth_model -v

# Create migration
alembic revision --autogenerate -m "Add UserAuth model"
alembic upgrade head

# Verify database
docker-compose exec db psql -U kreeda_user -d kreeda_db -c "\d user_auth"
```

**Status**: ✅ Completed

---

### Task 1.2: Database Models - User Profile ✅

#### Implementation
- [x] Create `UserProfile` model in `src/models/user_profile.py`
  - [x] Fields: id, user_id (FK), name, avatar_url
  - [x] Fields: location, date_of_birth, bio
  - [x] Fields: preferences (JSON), roles (JSON)
  - [x] Fields: created_at, updated_at

#### Testing
- [x] Write model tests
  - [x] Test profile creation
  - [x] Test foreign key relationship
  - [x] Test JSON field handling

#### Verification
```bash
pytest tests/test_models.py::test_user_profile_model -v
alembic revision --autogenerate -m "Add UserProfile model"
alembic upgrade head
```

**Status**: ✅ Completed

---

### Task 1.3: Password Security ✅

#### Implementation
- [x] Create password utility in `src/core/security.py`
  - [x] Implement bcrypt hashing
  - [x] Implement password verification
  - [x] Create password validator in `src/utils/validators.py`
  - [x] Rules: min 8 chars, uppercase, lowercase, digit, special char

#### Testing
- [x] Write security tests in `tests/test_security.py`
  - [x] Test password hashing
  - [x] Test password verification
  - [x] Test password validation rules
  - [x] Test weak password rejection

#### Verification
```bash
pytest tests/test_security.py -v --cov=src/core/security --cov=src/utils/validators

# Manual test
python -c "from src.core.security import hash_password, verify_password; \
           h = hash_password('Test@123'); \
           print('Valid:', verify_password('Test@123', h))"
```

**Status**: ✅ Completed

---

### Task 1.4: JWT Token System ✅

#### Implementation
- [x] Implement JWT token generation in `src/core/security.py`
  - [x] Create access token (1 hour expiry)
  - [x] Create refresh token (30 day expiry)
  - [x] Add token validation
  - [x] Add token decoding with error handling

#### Testing
- [x] Write JWT tests in `tests/test_security.py`
  - [x] Test token creation
  - [x] Test token validation
  - [x] Test expired token handling
  - [x] Test invalid token handling

#### Verification
```bash
pytest tests/test_security.py::test_create_access_token -v
pytest tests/test_security.py::test_verify_token -v

# Manual test
python -c "from src.core.security import create_access_token, verify_token; \
           token = create_access_token('test-user-id', 'test@example.com'); \
           print('Token:', token); \
           payload = verify_token(token); \
           print('Payload:', payload)"
```

**Status**: ✅ Completed

---

### Task 1.5: User Registration Endpoint ✅

#### Implementation
- [x] Create schemas in `src/schemas/auth.py`
  - [x] `UserRegisterRequest` - email, password, phone, name
  - [x] `UserResponse` - user data response
  - [x] `AuthResponse` - user + session
  
- [x] Create service in `src/services/auth.py`
  - [x] `AuthService.register()` method
  - [x] Check email uniqueness
  - [x] Validate password strength
  - [x] Hash password
  - [x] Create user and profile
  - [x] Generate tokens
  
- [x] Create router in `src/routers/auth.py`
  - [x] `POST /auth/register` endpoint

#### Testing
- [x] Write registration tests in `tests/test_auth.py`
  - [x] Test successful registration
  - [x] Test duplicate email rejection
  - [x] Test weak password rejection
  - [x] Test missing fields validation
  - [x] Test token generation

#### Verification
```bash
# Unit tests
pytest tests/test_auth.py::test_register_user_success -v
pytest tests/test_auth.py::test_register_duplicate_email -v
pytest tests/test_auth.py::test_register_weak_password -v

# Integration test
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "phone_number": "+1234567890",
    "name": "Test User"
  }'

# Verify in database
docker-compose exec db psql -U kreeda_user -d kreeda_db \
  -c "SELECT email, is_email_verified FROM user_auth;"
```

**Status**: ✅ Completed

---

### Task 1.6: User Login Endpoint ✅

#### Implementation
- [x] Create schemas
  - [x] `UserLoginRequest` - email, password
  
- [x] Create service
  - [x] `AuthService.login()` method
  - [x] Validate credentials
  - [x] Check account status (is_active)
  - [x] Update last_login timestamp
  - [x] Generate new tokens
  
- [x] Create router
  - [x] `POST /auth/signin/password` endpoint

#### Testing
- [x] Write login tests in `tests/test_auth.py`
  - [x] Test successful login
  - [x] Test invalid email
  - [x] Test invalid password
  - [x] Test inactive account
  - [x] Test token generation

#### Verification
```bash
# Unit tests
pytest tests/test_auth.py::test_login_success -v
pytest tests/test_auth.py::test_login_invalid_credentials -v

# Integration test
curl -X POST http://localhost:8000/auth/signin/password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Should return access_token and refresh_token
```

**Status**: ✅ Completed

---

### Task 1.7: Get Current User Endpoint ✅

#### Implementation
- [x] Create authentication dependency in `src/core/security.py`
  - [x] `get_current_user()` dependency
  - [x] Extract token from Authorization header
  - [x] Validate token
  - [x] Fetch user from database
  
- [x] Create service
  - [x] `AuthService.get_user()` method
  
- [x] Create router
  - [x] `GET /auth/user` endpoint

#### Testing
- [x] Write tests in `tests/test_auth.py`
  - [x] Test get user with valid token
  - [x] Test get user with invalid token
  - [x] Test get user with expired token
  - [x] Test get user with missing token

#### Verification
```bash
# Unit tests
pytest tests/test_auth.py::test_get_current_user -v

# Integration test
# First, register and login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/signin/password \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['session']['access_token'])")

# Then get current user
curl -X GET http://localhost:8000/auth/user \
  -H "Authorization: Bearer $TOKEN"
```

**Status**: ✅ Completed

---

### Sprint 1 Checkpoint

**Definition of Done**:
- [x] All Task 1.1-1.7 tests passing
- [x] Code coverage > 80% for auth module
- [x] Linting passes (flake8, black)
- [x] CI/CD pipeline green
- [x] Manual API testing successful
- [x] Documentation updated

**Verification**:
```bash
# Run all sprint 1 tests
pytest tests/test_auth.py -v --cov=src/services/auth --cov=src/routers/auth

# Run full test suite
pytest --cov=src --cov-report=term-missing

# Lint code
black src/ --check
flake8 src/

# Push to trigger CI/CD
git push origin feature/sprint-1
# Verify GitHub Actions passes
```

---

## Sprint 2: User Profile & Email Verification

**Goal**: Implement user profile management and email verification workflow.

### Task 2.1: User Profile CRUD Operations ✅

#### Implementation
- [x] Create schemas in `src/schemas/user_profile.py`
  - [x] `UserProfileResponse` - profile data
  - [x] `UserProfileUpdateRequest` - update fields
  
- [x] Create service in `src/services/user_profile.py`
  - [x] `UserProfileService.get_profile()` method
  - [x] `UserProfileService.update_profile()` method
  
- [x] Create router in `src/routers/user_profile.py`
  - [x] `GET /user/profile/` endpoint
  - [x] `PUT /user/profile/` endpoint

#### Testing
- [x] Write profile tests in `tests/test_user_profile.py`
  - [x] Test get profile
  - [x] Test update profile
  - [x] Test update with invalid data
  - [x] Test unauthorized access

#### Verification
```bash
pytest tests/test_user_profile.py -v

# Integration test
# Get profile
curl -X GET http://localhost:8000/user/profile/ \
  -H "Authorization: Bearer $TOKEN"

# Update profile
curl -X PUT http://localhost:8000/user/profile/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "location": "San Francisco",
    "bio": "Software developer"
  }'
```

**Status**: ✅ Completed

---

### Task 2.2: Email Service Setup ✅

#### Implementation
- [x] Create email utility in `src/utils/email.py`
  - [x] `send_verification_email()` function
  - [x] `send_password_reset_email()` function
  - [x] `send_welcome_email()` function
  - [x] Token generation for verification
  
- [x] Configure SMTP settings in `src/config/settings.py`

#### Testing
- [x] Write email tests in `tests/test_email.py`
  - [x] Test email formatting
  - [x] Test token generation
  - [x] Test token validation
  - [x] Mock SMTP for testing

#### Verification
```bash
pytest tests/test_email.py -v

# Manual test (with SMTP configured)
python -c "from src.utils.email import send_verification_email; \
           import asyncio; \
           asyncio.run(send_verification_email('test@example.com', 'test-token'))"
```

**Status**: ✅ Completed

---

### Task 2.3: Email Verification Workflow ✅

#### Implementation
- [x] Update registration to send verification email
  - [x] Generate verification token
  - [x] Store token in Redis with expiry (24 hours)
  - [x] Send verification email
  
- [x] Create verification endpoints
  - [x] `GET /auth/verify-email?token=...` - Verify email
  - [x] `POST /auth/resend-verification` - Resend verification
  
- [x] Update service methods
  - [x] `AuthService.verify_email()` method
  - [x] `AuthService.resend_verification_email()` method

#### Testing
- [x] Write verification tests in `tests/test_auth.py`
  - [x] Test email verification success
  - [x] Test invalid token
  - [x] Test expired token
  - [x] Test resend verification
  - [x] Test rate limiting (max 3 per hour)

#### Verification
```bash
pytest tests/test_auth.py::test_email_verification -v

# Integration test
# 1. Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"verify@example.com","password":"Test@123456"}'

# 2. Get verification token from email/logs

# 3. Verify email
curl -X GET "http://localhost:8000/auth/verify-email?token=<TOKEN>"

# 4. Check database
docker-compose exec db psql -U kreeda_user -d kreeda_db \
  -c "SELECT email, is_email_verified FROM user_auth WHERE email='verify@example.com';"
```

**Status**: ✅ Completed

---

### Sprint 2 Checkpoint

**Definition of Done**:
- [x] All Task 2.1-2.3 tests passing
- [x] Email verification workflow working
- [x] Profile CRUD operations functional
- [x] Code coverage maintained > 80%
- [x] CI/CD pipeline green

---

## Sprint 3: Advanced Authentication Features

**Goal**: Implement token refresh, password recovery, and user updates.

### Task 3.1: Refresh Token System ✅

#### Implementation
- [x] Create Redis client in `src/utils/redis_client.py`
  - [x] `store_refresh_token()` method
  - [x] `validate_refresh_token()` method
  - [x] `invalidate_session()` method
  
- [x] Update login to store refresh token in Redis
  
- [x] Create token refresh endpoint
  - [x] `POST /auth/token` endpoint
  - [x] Validate refresh token
  - [x] Generate new access token
  - [x] Rotate refresh token (optional)

#### Testing
- [x] Write token refresh tests in `tests/test_auth.py`
  - [x] Test successful token refresh
  - [x] Test invalid refresh token
  - [x] Test expired refresh token
  - [x] Test token rotation

#### Verification
```bash
pytest tests/test_auth.py::test_refresh_token -v

# Integration test
# Get refresh token from login
REFRESH_TOKEN=$(curl -s -X POST http://localhost:8000/auth/signin/password \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@123456"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['session']['refresh_token'])")

# Refresh access token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
```

**Status**: ✅ Completed

---

### Task 3.2: Password Recovery ✅

#### Implementation
- [x] Create password recovery endpoints
  - [x] `POST /auth/recover` - Request password reset
  - [x] `POST /auth/reset-password` - Reset password with token
  
- [x] Create service methods
  - [x] `AuthService.request_password_reset()` method
    - [x] Generate reset token
    - [x] Store in Redis with 1-hour expiry
    - [x] Send reset email
  - [x] `AuthService.reset_password()` method
    - [x] Validate token
    - [x] Validate new password
    - [x] Update password hash
    - [x] Invalidate reset token

#### Testing
- [x] Write password recovery tests in `tests/test_auth.py`
  - [x] Test request password reset
  - [x] Test reset password success
  - [x] Test invalid token
  - [x] Test expired token
  - [x] Test weak new password

#### Verification
```bash
pytest tests/test_auth.py::test_password_recovery -v

# Integration test
# Request reset
curl -X POST http://localhost:8000/auth/recover \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Get token from email/logs

# Reset password
curl -X POST http://localhost:8000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "<RESET_TOKEN>",
    "new_password": "NewSecure123!"
  }'

# Test login with new password
curl -X POST http://localhost:8000/auth/signin/password \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"NewSecure123!"}'
```

**Status**: ✅ Completed

---

### Task 3.3: Update User Information ✅

#### Implementation
- [x] Create update user endpoint
  - [x] `PUT /auth/user` endpoint
  
- [x] Create service method
  - [x] `AuthService.update_user()` method
  - [x] Support email update (resets verification)
  - [x] Support password update (validates strength)
  - [x] Support phone update (resets verification)
  - [x] Check email uniqueness

#### Testing
- [x] Write update user tests in `tests/test_auth.py`
  - [x] Test update email
  - [x] Test update password
  - [x] Test update phone
  - [x] Test email uniqueness check
  - [x] Test verification reset

#### Verification
```bash
pytest tests/test_auth.py::test_update_user -v

# Integration test
curl -X PUT http://localhost:8000/auth/user \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com",
    "password": "UpdatedPass123!"
  }'
```

**Status**: ✅ Completed

---

### Task 3.4: Sign Out Endpoint ✅

#### Implementation
- [x] Create sign out endpoint
  - [x] `POST /auth/signout` endpoint
  
- [x] Create service method
  - [x] `AuthService.sign_out()` method
  - [x] Invalidate refresh token in Redis
  - [x] Log sign out event

#### Testing
- [x] Write sign out tests in `tests/test_auth.py`
  - [x] Test successful sign out
  - [x] Test token invalidation
  - [x] Test using old token after sign out

#### Verification
```bash
pytest tests/test_auth.py::test_sign_out -v

# Integration test
curl -X POST http://localhost:8000/auth/signout \
  -H "Authorization: Bearer $TOKEN"

# Try to use old token (should fail)
curl -X GET http://localhost:8000/auth/user \
  -H "Authorization: Bearer $TOKEN"
```

**Status**: ✅ Completed

---

### Sprint 3 Checkpoint

**Definition of Done**:
- [x] All Task 3.1-3.4 tests passing
- [x] Token refresh working
- [x] Password recovery working
- [x] User update working
- [x] Sign out invalidates sessions
- [x] Code coverage > 80%

---

## Sprint 4: Testing & Quality Assurance

**Goal**: Achieve comprehensive test coverage and set up quality gates.

### Task 4.1: Integration Tests ✅

#### Implementation
- [x] Create integration tests in `tests/test_integration.py`
  - [x] Test complete user journey (register → login → profile)
  - [x] Test password recovery flow
  - [x] Test email verification flow
  - [x] Test token refresh flow
  - [x] Test multi-step authentication scenarios

#### Verification
```bash
pytest tests/test_integration.py -v
pytest -m integration --cov=src
```

**Status**: ✅ Completed

---

### Task 4.2: Edge Case Testing ✅

#### Implementation
- [x] Add edge case tests
  - [x] Concurrent registration with same email
  - [x] Multiple token refresh attempts
  - [x] Expired token edge cases
  - [x] Invalid JSON payloads
  - [x] SQL injection attempts (via ORM)
  - [x] XSS attempts (via validation)

#### Verification
```bash
pytest tests/ -v -k "edge"
```

**Status**: ✅ Completed

---

### Task 4.3: Performance Testing

#### Implementation
- [ ] Create performance tests in `tests/test_performance.py`
  - [ ] Test concurrent registrations
  - [ ] Test concurrent logins
  - [ ] Test database query performance
  - [ ] Test Redis performance
  - [ ] Load test with locust (optional)

#### Verification
```bash
pytest tests/test_performance.py -v

# Optional: Load testing
# pip install locust
# locust -f tests/locustfile.py
```

**Status**: ⏳ Pending

---

### Task 4.4: Code Quality Gates ✅

#### Implementation
- [x] Configure pre-commit hooks
  - [x] Black formatting
  - [x] Flake8 linting
  - [x] MyPy type checking (optional)
  
- [x] Configure coverage thresholds
  - [x] Minimum 80% overall
  - [x] Minimum 90% for critical paths

- [x] Set up Codecov integration

#### Verification
```bash
# Run quality checks
black src/ tests/ --check
flake8 src/ tests/

# Coverage check
pytest --cov=src --cov-report=term --cov-fail-under=80

# Type checking (optional)
mypy src/
```

**Status**: ✅ Completed

---

### Sprint 4 Checkpoint

**Definition of Done**:
- [x] Integration tests passing
- [x] Edge case tests passing
- [ ] Performance tests created
- [x] Code coverage > 80%
- [x] Quality gates in place
- [x] CI/CD enforcing quality standards

---

## Sprint 5: Cricket Module - Data Models

**Goal**: Design and implement cricket-specific data models.

### Task 5.1: Cricket Match Models

#### Implementation
- [ ] Create models in `src/models/cricket/`
  - [ ] `Match` model
    - [ ] match_id, title, match_type (Test/ODI/T20)
    - [ ] venue, start_time, end_time
    - [ ] status (scheduled/in_progress/completed/cancelled)
    - [ ] created_by, created_at, updated_at
  
  - [ ] `Team` model
    - [ ] team_id, name, logo_url
    - [ ] captain_id, coach, home_ground
    - [ ] created_at, updated_at
  
  - [ ] `MatchTeam` model (junction table)
    - [ ] match_id, team_id
    - [ ] team_type (home/away)
    - [ ] score, wickets, overs

#### Testing
- [ ] Write model tests in `tests/test_cricket_models.py`
  - [ ] Test match creation
  - [ ] Test team creation
  - [ ] Test match-team relationship

#### Verification
```bash
pytest tests/test_cricket_models.py -v
alembic revision --autogenerate -m "Add cricket models"
alembic upgrade head
```

**Status**: ⏳ Pending

---

### Task 5.2: Player & Squad Models

#### Implementation
- [ ] Create models
  - [ ] `Player` model
    - [ ] player_id, user_id (optional, for registered users)
    - [ ] name, jersey_number, role (batsman/bowler/all-rounder)
    - [ ] batting_hand, bowling_style
    - [ ] created_at, updated_at
  
  - [ ] `Squad` model
    - [ ] squad_id, match_id, team_id
    - [ ] player_id, is_playing_11, is_captain, is_wicket_keeper
    - [ ] batting_order

#### Testing
- [ ] Write player tests
  - [ ] Test player creation
  - [ ] Test squad selection
  - [ ] Test playing 11 validation (max 11)

#### Verification
```bash
pytest tests/test_cricket_models.py::test_player -v
pytest tests/test_cricket_models.py::test_squad -v
```

**Status**: ⏳ Pending

---

### Task 5.3: Innings & Over Models

#### Implementation
- [ ] Create models
  - [ ] `Innings` model
    - [ ] innings_id, match_id, team_id
    - [ ] innings_number (1st/2nd)
    - [ ] total_runs, total_wickets, total_overs
    - [ ] is_declared, is_completed
  
  - [ ] `Over` model
    - [ ] over_id, innings_id
    - [ ] over_number, bowler_id
    - [ ] runs_in_over, wickets_in_over
    - [ ] is_maiden

#### Testing
- [ ] Write innings tests
  - [ ] Test innings creation
  - [ ] Test over tracking
  - [ ] Test run calculation

#### Verification
```bash
pytest tests/test_cricket_models.py::test_innings -v
```

**Status**: ⏳ Pending

---

### Task 5.4: Ball & Delivery Models

#### Implementation
- [ ] Create models
  - [ ] `Ball` model
    - [ ] ball_id, over_id, innings_id
    - [ ] ball_number, batsman_id, bowler_id
    - [ ] runs_scored, is_wicket, wicket_type
    - [ ] extras_type, extras_runs
    - [ ] timestamp
  
  - [ ] `Wicket` model
    - [ ] wicket_id, ball_id
    - [ ] batsman_out_id, fielder_id
    - [ ] wicket_type (bowled/caught/lbw/run out/etc.)
    - [ ] runs_at_wicket, overs_at_wicket

#### Testing
- [ ] Write ball tests
  - [ ] Test ball recording
  - [ ] Test wicket recording
  - [ ] Test extras handling
  - [ ] Test run calculation

#### Verification
```bash
pytest tests/test_cricket_models.py::test_ball -v
pytest tests/test_cricket_models.py::test_wicket -v
```

**Status**: ⏳ Pending

---

### Sprint 5 Checkpoint

**Definition of Done**:
- [ ] All cricket models created
- [ ] Database migrations applied
- [ ] Model tests passing
- [ ] Relationships validated
- [ ] Code coverage > 80%

---

## Sprint 6: Cricket Module - Match Management

**Goal**: Implement match creation, team management, and squad selection.

### Task 6.1: Match Creation Endpoints

#### Implementation
- [ ] Create schemas in `src/schemas/cricket/match.py`
  - [ ] `MatchCreateRequest`
  - [ ] `MatchResponse`
  - [ ] `MatchUpdateRequest`
  
- [ ] Create service in `src/services/cricket/match_service.py`
  - [ ] `MatchService.create_match()`
  - [ ] `MatchService.update_match()`
  - [ ] `MatchService.get_match()`
  - [ ] `MatchService.list_matches()`
  
- [ ] Create router in `src/routers/cricket/match.py`
  - [ ] `POST /cricket/matches` - Create match
  - [ ] `GET /cricket/matches/{match_id}` - Get match
  - [ ] `GET /cricket/matches` - List matches
  - [ ] `PUT /cricket/matches/{match_id}` - Update match
  - [ ] `DELETE /cricket/matches/{match_id}` - Delete match

#### Testing
- [ ] Write match management tests
  - [ ] Test create match
  - [ ] Test update match
  - [ ] Test get match
  - [ ] Test list matches with filters
  - [ ] Test authorization (only creator can update)

#### Verification
```bash
pytest tests/test_cricket_match.py -v

# Integration test
curl -X POST http://localhost:8000/cricket/matches \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "India vs Australia",
    "match_type": "T20",
    "venue": "Melbourne Cricket Ground",
    "start_time": "2024-11-01T14:00:00Z"
  }'
```

**Status**: ⏳ Pending

---

### Task 6.2: Team Management Endpoints

#### Implementation
- [ ] Create team schemas and service
- [ ] Create endpoints
  - [ ] `POST /cricket/teams` - Create team
  - [ ] `GET /cricket/teams/{team_id}` - Get team
  - [ ] `PUT /cricket/teams/{team_id}` - Update team
  - [ ] `POST /cricket/matches/{match_id}/teams` - Add team to match

#### Testing
- [ ] Write team tests
  - [ ] Test team creation
  - [ ] Test team updates
  - [ ] Test adding team to match

#### Verification
```bash
pytest tests/test_cricket_team.py -v
```

**Status**: ⏳ Pending

---

### Task 6.3: Squad Selection Endpoints

#### Implementation
- [ ] Create player and squad schemas
- [ ] Create endpoints
  - [ ] `POST /cricket/teams/{team_id}/players` - Add player
  - [ ] `POST /cricket/matches/{match_id}/squads` - Select squad
  - [ ] `GET /cricket/matches/{match_id}/squads` - Get squad
  - [ ] `PUT /cricket/matches/{match_id}/squads/{player_id}` - Update player status

#### Testing
- [ ] Write squad tests
  - [ ] Test squad selection
  - [ ] Test playing 11 validation
  - [ ] Test captain selection

#### Verification
```bash
pytest tests/test_cricket_squad.py -v
```

**Status**: ⏳ Pending

---

### Sprint 6 Checkpoint

**Definition of Done**:
- [ ] Match CRUD operations working
- [ ] Team management working
- [ ] Squad selection working
- [ ] All tests passing
- [ ] Code coverage > 80%

---

## Sprint 7: Cricket Module - Scorekeeping

**Goal**: Implement live scorekeeping functionality.

### Task 7.1: Start Match & Toss

#### Implementation
- [ ] Create endpoints
  - [ ] `POST /cricket/matches/{match_id}/start` - Start match
  - [ ] `POST /cricket/matches/{match_id}/toss` - Record toss
    - [ ] Toss winner, elected to bat/bowl
    - [ ] Create first innings

#### Testing
- [ ] Write match start tests
  - [ ] Test toss recording
  - [ ] Test innings creation
  - [ ] Test validation (squad must be finalized)

#### Verification
```bash
pytest tests/test_cricket_scorekeeping.py::test_start_match -v
```

**Status**: ⏳ Pending

---

### Task 7.2: Record Ball-by-Ball

#### Implementation
- [ ] Create ball recording endpoint
  - [ ] `POST /cricket/matches/{match_id}/innings/{innings_id}/balls` - Record ball
  
- [ ] Create service method
  - [ ] Validate batsman, bowler, fielders
  - [ ] Calculate runs, extras
  - [ ] Update over, innings, match totals
  - [ ] Handle wickets
  - [ ] Handle end of over, innings, match

#### Testing
- [ ] Write ball recording tests
  - [ ] Test normal ball
  - [ ] Test wide, no-ball, bye, leg-bye
  - [ ] Test wicket ball
  - [ ] Test end of over
  - [ ] Test end of innings

#### Verification
```bash
pytest tests/test_cricket_scorekeeping.py::test_record_ball -v
```

**Status**: ⏳ Pending

---

### Task 7.3: Live Score Updates (WebSocket)

#### Implementation
- [ ] Implement WebSocket endpoint
  - [ ] `WS /cricket/matches/{match_id}/live` - Live updates
  
- [ ] Broadcast score updates
  - [ ] On ball recorded
  - [ ] On wicket
  - [ ] On end of over
  - [ ] On end of innings

#### Testing
- [ ] Write WebSocket tests
  - [ ] Test connection
  - [ ] Test message broadcasting
  - [ ] Test concurrent connections

#### Verification
```bash
pytest tests/test_cricket_websocket.py -v

# Manual test with websocat or browser
websocat ws://localhost:8000/cricket/matches/123/live
```

**Status**: ⏳ Pending

---

### Task 7.4: Match Statistics & Summary

#### Implementation
- [ ] Create statistics endpoints
  - [ ] `GET /cricket/matches/{match_id}/scorecard` - Full scorecard
  - [ ] `GET /cricket/matches/{match_id}/statistics` - Match stats
  - [ ] `GET /cricket/players/{player_id}/statistics` - Player stats

#### Testing
- [ ] Write statistics tests
  - [ ] Test scorecard generation
  - [ ] Test batting statistics
  - [ ] Test bowling statistics
  - [ ] Test team statistics

#### Verification
```bash
pytest tests/test_cricket_statistics.py -v
```

**Status**: ⏳ Pending

---

### Sprint 7 Checkpoint

**Definition of Done**:
- [ ] Scorekeeping functional
- [ ] Live updates working
- [ ] Statistics accurate
- [ ] All tests passing
- [ ] WebSocket tested

---

## Sprint 8: Deployment & Monitoring

**Goal**: Deploy to production and set up monitoring.

### Task 8.1: Production Configuration

#### Implementation
- [ ] Create production environment
  - [ ] Set up production database
  - [ ] Set up production Redis
  - [ ] Configure environment variables
  - [ ] Set up SSL/TLS certificates
  
- [ ] Update Docker configuration
  - [ ] Multi-stage Dockerfile for smaller images
  - [ ] Docker Compose for production
  - [ ] Health checks

#### Verification
```bash
# Build production image
docker build -t kreeda-backend:prod .

# Test production configuration
docker-compose -f docker-compose.prod.yml up -d

# Verify health
curl https://api.kreeda.com/health
```

**Status**: ⏳ Pending

---

### Task 8.2: Logging & Monitoring

#### Implementation
- [ ] Enhanced logging
  - [ ] Structured JSON logging
  - [ ] Log aggregation (e.g., ELK stack)
  - [ ] Error tracking (e.g., Sentry)
  
- [ ] Metrics & Monitoring
  - [ ] Prometheus metrics
  - [ ] Grafana dashboards
  - [ ] Uptime monitoring

#### Verification
```bash
# Check logs
docker-compose logs -f

# Check metrics
curl http://localhost:8000/metrics

# Verify Grafana dashboard
open http://localhost:3000
```

**Status**: ⏳ Pending

---

### Task 8.3: Database Backups

#### Implementation
- [ ] Set up automated backups
  - [ ] Daily PostgreSQL backups
  - [ ] Backup retention policy (30 days)
  - [ ] Backup to cloud storage (S3/GCS)
  
- [ ] Test restore process
  - [ ] Document restore procedure
  - [ ] Test restore from backup

#### Verification
```bash
# Manual backup
docker-compose exec db pg_dump -U kreeda_user kreeda_db > backup.sql

# Restore test
docker-compose exec -T db psql -U kreeda_user kreeda_db < backup.sql
```

**Status**: ⏳ Pending

---

### Task 8.4: Documentation Finalization

#### Implementation
- [ ] Complete API documentation
  - [ ] Update OpenAPI specs
  - [ ] Add request/response examples
  - [ ] Document error codes
  
- [ ] Deployment documentation
  - [ ] Installation guide
  - [ ] Configuration guide
  - [ ] Troubleshooting guide
  
- [ ] User documentation
  - [ ] API usage guide
  - [ ] Code examples
  - [ ] Best practices

#### Verification
```bash
# Generate API docs
# Accessible at /api/docs

# Review documentation completeness
```

**Status**: ⏳ Pending

---

### Sprint 8 Checkpoint

**Definition of Done**:
- [ ] Deployed to production
- [ ] Monitoring in place
- [ ] Backups automated
- [ ] Documentation complete
- [ ] Production ready

---

## Definition of Done

Every task must meet these criteria before being marked complete:

### Code Quality
- [ ] Code follows style guide (PEP 8)
- [ ] Black formatting applied
- [ ] Flake8 linting passes
- [ ] No commented-out code
- [ ] No TODO comments in production code

### Testing
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Edge cases tested
- [ ] Code coverage > 80% for changed code
- [ ] All tests passing in CI/CD

### Documentation
- [ ] Code has docstrings
- [ ] API endpoints documented in OpenAPI
- [ ] CONTEXT.md updated if needed
- [ ] README updated if needed
- [ ] Changelog updated

### Security
- [ ] No secrets in code
- [ ] Input validation implemented
- [ ] SQL injection protected (via ORM)
- [ ] XSS protection (via validation)
- [ ] Authentication/authorization implemented

### Performance
- [ ] No N+1 query issues
- [ ] Appropriate indexes added
- [ ] Caching considered
- [ ] No blocking operations in async code

### CI/CD
- [ ] All CI/CD checks passing
- [ ] Code reviewed (if team)
- [ ] Branch merged to main
- [ ] Deployed to staging/production

### Verification
- [ ] Manual testing completed
- [ ] Postman/curl tests successful
- [ ] Error cases tested
- [ ] Database state verified

---

## Testing Commands

### Run Tests by Sprint

```bash
# Sprint 1: Authentication
pytest tests/test_auth.py -v

# Sprint 2: Profile & Email
pytest tests/test_user_profile.py tests/test_email.py -v

# Sprint 3: Advanced Auth
pytest tests/test_auth.py::test_refresh_token -v
pytest tests/test_auth.py::test_password_recovery -v

# Sprint 4: Integration
pytest tests/test_integration.py -v

# Sprint 5-7: Cricket Module
pytest tests/test_cricket_*.py -v
```

### Run Tests by Type

```bash
# Unit tests only
pytest -m unit -v

# Integration tests only
pytest -m integration -v

# Slow tests
pytest -m slow -v

# All tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing
```

### CI/CD Simulation

```bash
# Simulate CI/CD locally
black src/ tests/ --check
flake8 src/ tests/
pytest --cov=src --cov-report=term --cov-fail-under=80
docker build -t kreeda-backend:test .
```

---

## Progress Tracking

### Completed Sprints
- [x] Sprint 1: Foundation & Core Authentication (100%)
- [x] Sprint 2: User Profile & Email Verification (100%)
- [x] Sprint 3: Advanced Authentication Features (100%)
- [x] Sprint 4: Testing & Quality Assurance (90%)

### In Progress Sprints
- [ ] Sprint 5: Cricket Module - Data Models (0%)
- [ ] Sprint 6: Cricket Module - Match Management (0%)
- [ ] Sprint 7: Cricket Module - Scorekeeping (0%)
- [ ] Sprint 8: Deployment & Monitoring (0%)

### Overall Progress: 67.5%

---

## Next Actions

### Immediate (This Week)
1. Complete Sprint 4 performance testing
2. Start Sprint 5: Design cricket data models
3. Create database schema for cricket module

### Short-term (This Month)
1. Complete Sprint 5: Cricket models
2. Complete Sprint 6: Match management
3. Begin Sprint 7: Scorekeeping

### Long-term (Next Quarter)
1. Complete Sprint 7: Live scoring
2. Complete Sprint 8: Production deployment
3. Add advanced features (analytics, predictions)

---

## Conclusion

This TODO document provides a comprehensive roadmap for developing the Kreeda backend. Each task includes:
- Clear implementation steps
- Testing requirements
- Verification commands
- Definition of Done criteria

Follow this checklist to ensure:
- ✅ Test-driven development
- ✅ CI/CD verification at every step
- ✅ High code quality
- ✅ Production-ready code

Update this document as you progress and mark tasks complete when they meet the Definition of Done.
