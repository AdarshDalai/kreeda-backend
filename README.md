# Kreeda Backend API

Digital Cricket Scorekeeping Platform - Backend API built with FastAPI.

## Overview

Kreeda Backend API is a comprehensive cricket match management system that allows users to create teams, schedule matches, record ball-by-ball scoring, and generate real-time scorecards. It serves as the backend for a digital cricket scorekeeping platform, providing both REST API endpoints and WebSocket connections for live updates.

## Key Features

- User Authentication (Supabase Integration)
- Team Management and Player Rosters
- Cricket Match Creation and Scheduling
- Ball-by-Ball Scoring with Detailed Statistics
- Real-time Scorecard Updates via WebSockets
- Match History and Player Statistics
- Data Integrity Validation

## Tech Stack

- **FastAPI** - Modern, high-performance Python web framework
- **PostgreSQL** - Primary relational database
- **SQLAlchemy 2.0** - Asynchronous ORM for database operations
- **Supabase** - Authentication service integration
- **Redis** - Caching and pub/sub for real-time updates
- **Cloudflare R2** - Object storage for file uploads
- **WebSockets** - Real-time bidirectional communication

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)

## Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd kreeda-backend
   ```

2. **Environment Setup**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Using Docker (Recommended)**

   ```bash
   # Start all services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f app
   
   # Stop services
   docker-compose down
   ```

4. **Manual Setup**

   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run database migrations
   alembic upgrade head
   
   # Start the application
   uvicorn app.main:app --reload
   ```

## API Documentation

Once running, visit:

- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

## API Endpoints

### Authentication

```text
POST /api/v1/auth/register    # User registration
POST /api/v1/auth/login       # User login
GET  /api/v1/auth/me          # Current user info
POST /api/v1/auth/refresh     # Refresh token
```

### Teams

```text
GET    /api/v1/teams/                    # List user teams
POST   /api/v1/teams/                    # Create team
GET    /api/v1/teams/{id}                # Get team details
POST   /api/v1/teams/{id}/members        # Add team member
DELETE /api/v1/teams/{id}/members/{uid}  # Remove member
```

### Cricket Matches

```text
GET  /api/v1/matches/              # List matches
POST /api/v1/matches/              # Create match
GET  /api/v1/matches/{id}          # Match details
POST /api/v1/matches/{id}/toss     # Record toss
POST /api/v1/matches/{id}/ball     # Record ball (scoring)
GET  /api/v1/matches/{id}/scorecard # Current scorecard
POST /api/v1/matches/{id}/complete # Complete match
```

### WebSocket

```text
WS /api/v1/matches/{id}/live       # Live score updates
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://kreeda:password@localhost:5432/kreeda_dev
REDIS_URL=redis://localhost:6379

# Supabase Authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Cloudflare R2 Storage (Optional)
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=kreeda-assets
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

## Database Setup

### Using Docker

The docker-compose.yml includes PostgreSQL setup. No manual configuration needed.

### Manual Setup

1. Install PostgreSQL 15+

   ```sql
   CREATE DATABASE kreeda_dev;
   CREATE USER kreeda WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE kreeda_dev TO kreeda;
   ```

2. Run migrations:

   ```bash
   alembic upgrade head
   ```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_auth.py -v
```

## Project Structure

```
kreeda-backend/
├── app/                   # Main application package
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Configuration and settings
│   ├── api/               # API route handlers
│   ├── auth/              # Authentication modules
│   ├── models/            # SQLAlchemy database models
│   ├── schemas/           # Pydantic data validation schemas
│   ├── services/          # Business logic services
│   └── utils/             # Utility functions and helpers
├── alembic/               # Database migrations
│   └── versions/          # Migration scripts
├── tests/                 # Test cases
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile             # Docker build configuration
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## Deployment

### Containerized Deployment

1. Build production image:

   ```bash
   docker build -t kreeda-backend:latest .
   ```

2. Run with environment variables:

   ```bash
   docker run -p 8000:8000 --env-file .env kreeda-backend:latest
   ```

### Standard Deployment

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run migrations:

   ```bash
   alembic upgrade head
   ```

3. Start with Gunicorn:

   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## Development Workflow

### Adding New Features

1. Create database models in `app/models/`
2. Define data schemas in `app/schemas/`
3. Implement service logic in `app/services/`
4. Create API routes in `app/api/`
5. Register routes in `app/main.py`
6. Create/run migrations with Alembic
7. Write tests in `tests/`

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email your-support-email or join our Discord community.

---

Created for Cricket Lovers
