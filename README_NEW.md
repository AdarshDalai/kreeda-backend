# Kreeda Backend

FastAPI backend with comprehensive authentication and user profile management.

## Features

- **Supabase-compatible authentication**
  - Email/password registration and login
  - Anonymous user support  
  - OTP-based authentication (email/SMS)
  - JWT token-based auth with refresh tokens
  - Email verification workflow
  - Password reset functionality

- **User profile management**
  - Create, read, update, delete user profiles
  - Support for avatars, bio, location, preferences

- **Security**
  - Password strength validation
  - Bcrypt password hashing
  - JWT token authentication
  - Redis-based session management
  - Refresh token rotation

- **Infrastructure**
  - Docker containerization
  - Automated database migrations (Alembic)
  - Comprehensive logging
  - Redis caching
  - Connection pooling
  - CORS support

- **Testing & CI/CD**
  - Unit tests with pytest
  - Integration tests
  - GitHub Actions CI/CD pipeline
  - Code coverage reporting

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

1. Clone the repository:
\`\`\`bash
git clone https://github.com/AdarshDalai/kreeda-backend.git
cd kreeda-backend
\`\`\`

2. Create virtual environment:
\`\`\`bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
\`\`\`

3. Install dependencies:
\`\`\`bash
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing
\`\`\`

4. Configure environment:
\`\`\`bash
cp .env.example .env
# Edit .env with your configuration
\`\`\`

5. Run database migrations:
\`\`\`bash
alembic upgrade head
\`\`\`

6. Start the server:
\`\`\`bash
uvicorn src.main:app --reload
\`\`\`

The API will be available at \`http://localhost:8000\`

### Using Docker

\`\`\`bash
docker-compose up -d
\`\`\`

## API Documentation

Interactive docs available at:
- Swagger UI: \`http://localhost:8000/api/docs\`
- ReDoc: \`http://localhost:8000/api/redoc\`

## Testing

\`\`\`bash
pytest  # Run all tests
pytest -m unit  # Unit tests only
pytest -m integration  # Integration tests only
pytest --cov=src --cov-report=html  # With coverage
\`\`\`

## License

MIT
