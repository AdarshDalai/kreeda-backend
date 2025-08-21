# Kreeda Backend API

🏏 **Mobile-first sports scorekeeping and tournament management platform for the Indian sports community**

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Git

### 1. Clone and Setup
```bash
git clone <repository-url>
cd kreeda-backend
cp .env.example .env
```

### 2. Configure Environment
Edit `.env` file with your configuration:
- Add your Supabase credentials
- Set JWT secret key
- Configure other settings as needed

### 3. Run with Docker
```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

### 4. Access the Application
- **API Documentation**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **PgAdmin**: http://localhost:5050

## 🏗️ Project Structure

```
kreeda-backend/
├── app/
│   ├── api/v1/           # API routes
│   ├── core/             # Core functionality
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── main.py           # FastAPI app
├── scripts/              # Database scripts
├── docker-compose.yml    # Docker services
├── Dockerfile            # Container config
└── requirements.txt      # Dependencies
```

## 🏏 Core Features

### Sports Supported
- **Cricket** (T20, ODI formats)
- **Football** (Soccer)
- **Field Hockey**

### Key Functionality
- Real-time digital scorekeeping
- Live score broadcasting
- Team creation and management
- Tournament organization
- Multi-role support (players, scorekeepers, spectators)

## 🛠️ Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: Supabase PostgreSQL
- **Cache**: Upstash Redis
- **Authentication**: Supabase Auth (JWT)
- **Real-time**: WebSockets + Server-Sent Events
- **Deployment**: Vercel Serverless Functions
- **Container**: Docker & Docker Compose

## 📝 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token

### Users
- `GET /api/v1/users/` - Get all users
- `GET /api/v1/users/{id}` - Get user by ID

### Teams
- `GET /api/v1/teams/` - Get all teams
- `POST /api/v1/teams/` - Create team

### Matches
- `GET /api/v1/matches/` - Get all matches
- `POST /api/v1/matches/` - Create match
- `GET /api/v1/matches/{id}/live` - Live match data

### Tournaments
- `GET /api/v1/tournaments/` - Get tournaments
- `POST /api/v1/tournaments/` - Create tournament

### Scores
- `GET /api/v1/scores/{match_id}` - Get match score
- `POST /api/v1/scores/{match_id}/update` - Update score

## 🧪 Development

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Management
```bash
# Access PostgreSQL
docker exec -it kreeda-postgres psql -U postgres -d kreeda_db

# View logs
docker-compose logs -f kreeda-api

# Restart services
docker-compose restart
```

## 🚀 Deployment

This API is designed for deployment on Vercel Serverless Functions with:
- Supabase for database and authentication
- Upstash Redis for caching
- Vercel for hosting and CI/CD

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ for the Indian sports community**
