# Kreeda Backend

FastAPI backend with comprehensive authentication and user profile management.

## Features
- Supabase-compatible authentication
- User profile management
- Docker containerization
- Automated database migrations
- Comprehensive test suite
- Test-driven development with 80%+ coverage
- CI/CD pipeline with GitHub Actions
- Production-ready logging and monitoring

## 📚 Documentation

Comprehensive documentation is available to help you develop and maintain this project:

### Core Documentation

- **[CONTEXT.md](CONTEXT.md)** - Master reference for GitHub Copilot and developers
  - Complete architecture and design patterns
  - Database schema and API specifications
  - Testing strategy and code standards
  - Use this when implementing features or asking Copilot for help

- **[TODO.md](TODO.md)** - Development roadmap with testing verification
  - Step-by-step task checklist organized by sprints
  - Testing requirements for each feature
  - CI/CD verification steps
  - Definition of Done criteria
  - Use this to track progress and ensure quality

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Fast lookup guide
  - Common commands (Docker, database, testing)
  - Code snippets and patterns
  - API testing examples
  - Troubleshooting tips
  - Use this for daily development tasks

- **[DOCUMENTATION_SUMMARY.md](DOCUMENTATION_SUMMARY.md)** - Documentation overview
  - Explains the purpose of each document
  - Reading order recommendations
  - How to use documentation effectively
  - Start here if you're new to the project

### Quick Start Guide

**For New Developers**:
1. Read [DOCUMENTATION_SUMMARY.md](DOCUMENTATION_SUMMARY.md) (5 min)
2. Read [CONTEXT.md](CONTEXT.md) - Project Overview section (15 min)
3. Review [TODO.md](TODO.md) - Current sprint status (10 min)
4. Bookmark [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for daily use
5. Follow the installation instructions below

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/AdarshDalai/kreeda-backend.git
cd kreeda-backend
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start the services**
```bash
docker-compose up -d
```

4. **Run database migrations**
```bash
docker-compose exec app alembic upgrade head
```

5. **Access the application**
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

### Running Tests

```bash
# Run all tests
docker-compose exec app pytest

# Run with coverage
docker-compose exec app pytest --cov=src --cov-report=html

# Run specific test file
docker-compose exec app pytest tests/test_auth.py -v
```

## 🔑 API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/signin/password` - Login with email/password
- `GET /auth/user` - Get current user
- `POST /auth/token` - Refresh access token
- `PUT /auth/user` - Update user information
- `POST /auth/recover` - Request password reset
- `POST /auth/signout` - Sign out user

### User Profile
- `GET /user/profile/` - Get current user's profile
- `PUT /user/profile/` - Update current user's profile

For detailed API documentation with examples, see [QUICK_REFERENCE.md](QUICK_REFERENCE.md) or visit http://localhost:8000/api/docs

## 🧪 Testing Strategy

This project follows a comprehensive testing approach:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test complete user journeys
- **Coverage Target**: Minimum 80% overall, 100% for critical paths
- **CI/CD Integration**: Automated testing on every push

See [CONTEXT.md](CONTEXT.md) for detailed testing patterns and [TODO.md](TODO.md) for testing checklists.

## 🏗️ Architecture

The project follows a clean layered architecture:

```
┌─────────────────────────────────────┐
│         Routers (API Layer)         │
├─────────────────────────────────────┤
│       Services (Business Logic)     │
├─────────────────────────────────────┤
│     Models (Data Access Layer)      │
├─────────────────────────────────────┤
│      Database (PostgreSQL)          │
└─────────────────────────────────────┘
```

For detailed architecture documentation, see [CONTEXT.md](CONTEXT.md).

## 📂 Project Structure

```
kreeda-backend/
├── src/
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── database/         # Database connection
│   ├── utils/            # Utilities (email, logger, redis)
│   └── core/             # Security, config
├── tests/                # Test suite
├── alembic/              # Database migrations
├── docs/                 # Additional documentation
└── docker-compose.yml    # Docker configuration
```

## 🛠️ Development Workflow

1. **Plan**: Check [TODO.md](TODO.md) for your current task
2. **Reference**: Review patterns in [CONTEXT.md](CONTEXT.md)
3. **Develop**: Write tests first, then implement features
4. **Test**: Run tests and verify coverage
5. **Verify**: Follow the Definition of Done in [TODO.md](TODO.md)
6. **Document**: Update documentation if needed

See [DOCUMENTATION_SUMMARY.md](DOCUMENTATION_SUMMARY.md) for detailed workflow.

## 🤖 GitHub Copilot Usage

This project includes comprehensive context for GitHub Copilot:

- Use [CONTEXT.md](CONTEXT.md) as reference when prompting Copilot
- Example: "Following the patterns in CONTEXT.md, create an endpoint for..."
- See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for Copilot prompt examples

## 🔒 Security

- Passwords hashed with bcrypt (12 rounds)
- JWT tokens with 1-hour access token expiry
- Refresh tokens stored in Redis with 30-day expiry
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM
- Email verification workflow
- Password strength validation

See [CONTEXT.md](CONTEXT.md) for detailed security documentation.

## 📊 Current Status

✅ **Completed Features**:
- User authentication (register, login, token refresh)
- User profile management
- Email verification workflow
- Password recovery system
- Comprehensive test suite (80%+ coverage)
- CI/CD pipeline
- Docker containerization
- Database migrations

⏳ **In Progress**:
- Cricket module data models
- Match management
- Live scorekeeping

📋 **Planned Features**:
- WebSocket for live updates
- Advanced analytics
- Admin dashboard

See [TODO.md](TODO.md) for detailed progress tracking.

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/feature-name`
2. Write tests first (TDD approach)
3. Implement the feature following patterns in [CONTEXT.md](CONTEXT.md)
4. Ensure all tests pass: `pytest --cov=src`
5. Follow Definition of Done in [TODO.md](TODO.md)
6. Submit a pull request

## 📄 License

[Add your license information here]

## 👥 Team

[Add team information here]

## 🆘 Support

- Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common issues
- Review [CONTEXT.md](CONTEXT.md) for detailed documentation
- Create an issue on GitHub for bugs or questions

---

**Last Updated**: 2024-10-11

For more information, see:
- [CONTEXT.md](CONTEXT.md) - Comprehensive project context
- [TODO.md](TODO.md) - Development roadmap
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick commands and snippets
- [DOCUMENTATION_SUMMARY.md](DOCUMENTATION_SUMMARY.md) - Documentation guide
