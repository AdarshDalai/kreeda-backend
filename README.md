# Kreeda Backend API

Digital Cricket Scorekeeping Platform - Backend API built with FastAPI.

## MVP Features

- ✅ User Authentication (Supabase Integration)
- ✅ Team Management  
- ✅ Cricket Match Creation
- ✅ Ball-by-Ball Scoring
- ✅ Real-time Scorecard Updates
- ✅ Match History

## Tech Stack

- **FastAPI 0.104+** - Modern Python web framework
- **PostgreSQL 15+** - Primary database
- **SQLAlchemy 2.0** - Async ORM
- **Supabase** - Authentication service
- **Redis** - Caching and pub/sub
- **Cloudflare R2** - File storage
- **WebSockets** - Real-time updates

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)

### Development Setup

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

### API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc  
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication
```
POST /api/v1/auth/register    # User registration
POST /api/v1/auth/login       # User login
GET  /api/v1/auth/me          # Current user info
POST /api/v1/auth/refresh     # Refresh token
```

### Teams
```
GET    /api/v1/teams/                    # List user teams
POST   /api/v1/teams/                    # Create team
GET    /api/v1/teams/{id}                # Get team details
POST   /api/v1/teams/{id}/members        # Add team member
DELETE /api/v1/teams/{id}/members/{uid}  # Remove member
```

### Cricket Matches
```
GET  /api/v1/matches/              # List matches
POST /api/v1/matches/              # Create match
GET  /api/v1/matches/{id}          # Match details
POST /api/v1/matches/{id}/toss     # Record toss
POST /api/v1/matches/{id}/ball     # Record ball (scoring)
GET  /api/v1/matches/{id}/scorecard # Current scorecard
POST /api/v1/matches/{id}/complete # Complete match
```

### WebSocket
```
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
2. Create database:
   ```sql
   CREATE DATABASE kreeda_dev;
   CREATE USER kreeda WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE kreeda_dev TO kreeda;
   ```
3. Run migrations:
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
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── auth/                # Authentication
│   ├── models/              # Database models
│   ├── schemas/             # API schemas
│   ├── api/                 # Route handlers
│   ├── services/            # Business logic
│   └── utils/               # Utilities
├── alembic/                 # Database migrations
├── tests/                   # Test cases
├── docker-compose.yml       # Docker setup
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Deployment

### Using Docker

1. Build production image:
   ```bash
   docker build -t kreeda-backend .
   ```

2. Run with environment:
   ```bash
   docker run -p 8000:8000 --env-file .env kreeda-backend
   ```

### Traditional Deployment

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

## Development

### Adding New Features

1. Create models in `app/models/`
2. Create schemas in `app/schemas/`
3. Implement service logic in `app/services/`
4. Create API routes in `app/api/`
5. Add routes to `app/main.py`
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

**Built with ❤️ for Cricket Lovers**
