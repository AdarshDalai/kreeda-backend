# Kreeda Backend - Package Structure

This document provides an overview of the Python package structure for the Kreeda backend application.

## Project Structure

```
kreeda-backend/
├── app/                          # Main application package
│   ├── __init__.py              # App metadata and version info
│   ├── main.py                  # FastAPI application entry point
│   │
│   ├── api/                     # REST API layer
│   │   ├── __init__.py         # API package documentation
│   │   └── v1/                 # API version 1
│   │       ├── __init__.py     # V1 API router exports
│   │       ├── api.py          # Main API router configuration
│   │       └── endpoints/      # Individual endpoint modules
│   │           ├── __init__.py # Endpoint module exports
│   │           ├── auth.py     # Authentication endpoints
│   │           ├── oauth2.py   # OAuth2 authorization server
│   │           ├── users.py    # User management endpoints
│   │           ├── teams.py    # Team management endpoints
│   │           ├── tournaments.py # Tournament endpoints
│   │           ├── matches.py  # Match management endpoints
│   │           └── scores.py   # Scoring endpoints
│   │
│   ├── core/                   # Core infrastructure
│   │   ├── __init__.py        # Core component exports
│   │   ├── config.py          # Application configuration
│   │   ├── database.py        # Database connection management
│   │   ├── oauth2.py          # OAuth2 authorization server
│   │   └── exceptions.py      # Global exception handlers
│   │
│   ├── models/                # Database models (SQLAlchemy)
│   │   ├── __init__.py       # Model exports and documentation
│   │   ├── user.py           # User account model
│   │   ├── team.py           # Team model
│   │   ├── tournament.py     # Tournament model
│   │   ├── match.py          # Match model
│   │   └── score.py          # Score model
│   │
│   ├── repositories/          # Data access layer
│   │   ├── __init__.py       # Repository exports
│   │   └── user.py           # User repository
│   │
│   ├── schemas/               # Pydantic models for validation
│   │   ├── __init__.py       # Common schema base classes
│   │   └── auth.py           # Authentication schemas
│   │
│   └── services/              # Business logic layer
│       ├── __init__.py       # Service exports
│       └── auth.py           # Authentication service
│
├── docs/                      # Documentation and examples
│   ├── __init__.py           # Documentation package
│   └── oauth2_documentation.py # OAuth2 implementation guide
│
├── alembic/                   # Database migrations
├── scripts/                   # Utility scripts
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
├── docker-compose.yml         # Multi-container setup
└── README.md                  # Project overview
```

## Package Descriptions

### `/app` - Main Application Package
The root package containing all application code with version info and metadata.

### `/app/api` - REST API Layer
Contains all HTTP endpoints organized by version. Currently implements v1 with:
- Authentication and OAuth2 endpoints
- User, team, tournament, match, and score management
- RESTful design with proper HTTP status codes
- OpenAPI/Swagger documentation

### `/app/core` - Core Infrastructure
Fundamental application components:
- Configuration management with environment variables
- Database connection and session handling
- OAuth2 2.0 authorization server implementation
- Global exception handling and error responses

### `/app/models` - Database Models
SQLAlchemy ORM models defining the database schema:
- User accounts and authentication data
- Team management and membership
- Tournament organization
- Match scheduling and tracking
- Scoring and statistics

### `/app/repositories` - Data Access Layer
Repository pattern implementation for database operations:
- Abstraction layer between business logic and database
- Async/await support for high performance
- Transaction management and error handling

### `/app/schemas` - Data Validation
Pydantic models for request/response validation:
- Input validation and type checking
- API documentation generation
- OAuth2 compliant token formats

### `/app/services` - Business Logic
Core business logic and service layer:
- Authentication and authorization services
- OAuth2 provider integrations (Google, Apple)
- Cross-cutting concerns and complex operations

### `/docs` - Documentation
Comprehensive documentation and configuration examples:
- OAuth2 implementation guides
- API integration examples
- Security best practices

## Import Examples

```python
# Import main app components
from app import __version__
from app.core import settings, get_db
from app.api.v1 import api_router

# Import models
from app.models import User, Team, Tournament, Match, Score

# Import services
from app.services import auth_service, oauth_service

# Import repositories  
from app.repositories import user_repository

# Import schemas
from app.schemas import BaseSchema, ResponseSchema
```

## Benefits of This Structure

1. **Clean Separation of Concerns**: Each package has a specific responsibility
2. **Easy Navigation**: Logical organization makes code easy to find
3. **Scalable Architecture**: New features can be added without restructuring
4. **Import Management**: Proper `__init__.py` files control what's exposed
5. **Documentation**: Each package is self-documenting with docstrings
6. **Testing**: Structure supports easy unit and integration testing
7. **Maintainability**: Clear boundaries make code easier to maintain

This structure follows Python packaging best practices and supports the growth of the Kreeda platform as a professional sports management system.
