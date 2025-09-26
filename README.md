# Kreeda Backend 🏏

> **Digital Sports Scorekeeping Platform with Progressive Scoring Integrity**

Kreeda is a comprehensive sports scorekeeping platform designed to ensure scoring accuracy through innovative consensus mechanisms, offline-first architecture, and real-time broadcasting capabilities. Starting with Cricket MVP.

## 🌟 Key Features

- **Progressive Scoring Integrity**: Multi-layer validation with dual scorers and consensus mechanisms
- **Offline-First Architecture**: Bluetooth mesh networking for local scoring with cloud sync
- **Real-time Broadcasting**: Live scorecards with different visibility levels
- **Multi-Sport Support**: Extensible plugin-based architecture (starting with Cricket)
- **Comprehensive Analytics**: Player and team performance insights

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/AdarshDalai/kreeda-backend.git
   cd kreeda-backend
   ```

2. **Set up environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Update .env with your configuration
   # - Database credentials
   # - Supabase keys
   # - Redis URL
   ```

3. **Start with Docker (Recommended)**
   ```bash
   # Start all services
   docker-compose -f docker/docker-compose.dev.yml up -d
   
   # View logs
   docker-compose -f docker/docker-compose.dev.yml logs -f api
   ```

4. **Or start manually**
   ```bash
   # Run the development script
   ./scripts/run-dev.sh
   ```

5. **Verify installation**
   ```bash
   # Check health endpoint
   curl http://localhost:8000/health
   
   # Access API documentation
   open http://localhost:8000/docs
   ```

## 📋 Development Workflow

### Project Structure

```
kreeda-backend/
├── app/
│   ├── api/v1/           # API endpoints
│   ├── core/             # Core configuration
│   ├── db/               # Database configuration
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── utils/            # Utility functions
│   └── tests/            # Test files
├── docker/               # Docker configuration
├── docs/                 # Documentation
├── requirements/         # Python dependencies
└── scripts/              # Utility scripts
```

### Development Commands

```bash
# Run tests
pytest app/tests/ -v

# Code formatting
black app/
isort app/

# Type checking
mypy app/

# Run with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/auth/register` | POST | User registration |
| `/api/v1/auth/me` | GET | Current user info |

## 🏏 Cricket Features (MVP)

### Core Functionality
- Ball-by-ball scoring system
- Dual scorer consensus mechanism
- Real-time score updates via WebSocket
- Match state management
- Player and team statistics

### Scoring Integrity
- **Dual Scorers**: Two independent scorers per match
- **Consensus Validation**: Automatic conflict detection
- **Dispute Resolution**: Escalation and voting mechanisms
- **Audit Trail**: Complete scoring history

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15 with SQLAlchemy
- **Cache**: Redis 7
- **Authentication**: Supabase
- **Real-time**: WebSockets
- **Containerization**: Docker
- **Testing**: Pytest

## 📊 Database Schema

Key entities:
- **Users**: Players, scorers, spectators
- **Teams**: Cricket teams and player rosters
- **Matches**: Match metadata and configuration
- **CricketScorecards**: Ball-by-ball scoring data
- **Scorers**: Dual scorer assignments and consensus

## 🔐 Environment Variables

```bash
# App Configuration
APP_NAME=Kreeda Backend
ENVIRONMENT=development
DEBUG=true
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/kreeda

# Redis
REDIS_URL=redis://localhost:6379

# Supabase Authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Security
SECRET_KEY=your-secret-key
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
```

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running in development mode
- **Architecture**: See `docs/architecture/` for detailed system design
- **Database Schema**: See `docs/database/` for data models
- **Development Guide**: See `docs/planning/` for development workflow

## 🚢 Deployment

### Production Deployment

```bash
# Build production image
docker build -f docker/Dockerfile --target production -t kreeda-backend:latest .

# Run with production compose
docker-compose -f docker/docker-compose.prod.yml up -d
```

### Environment-specific Configuration

- **Development**: Hot reload, debug logging, test data
- **Staging**: Production-like environment for testing
- **Production**: Optimized for performance and security

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Standards

- Follow PEP 8 style guide
- Write comprehensive tests
- Update documentation
- Use type hints
- Follow commit message conventions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: [docs.kreeda.app](https://docs.kreeda.app)
- **Issues**: [GitHub Issues](https://github.com/AdarshDalai/kreeda-backend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AdarshDalai/kreeda-backend/discussions)

## 🗺️ Roadmap

### Phase 1 (Current): Cricket MVP
- ✅ Core API infrastructure
- ✅ Authentication system
- 🚧 Cricket scoring engine
- 🚧 Dual scorer consensus
- 📋 WebSocket real-time updates

### Phase 2: Mobile Integration
- 📋 Flutter mobile app
- 📋 Offline scoring capabilities
- 📋 Bluetooth mesh networking
- 📋 Advanced UI/UX

### Phase 3: Advanced Features
- 📋 Tournament management
- 📋 Performance analytics
- 📋 Multi-sport support
- 📋 Broadcasting features

---

**Built with ❤️ for cricket lovers and sports enthusiasts**