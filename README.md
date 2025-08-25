# Kreeda Backend 🏏

**Digital cricket scoring made simple, fast, and reliable**

Built for MVP: Teams, matches, live scoring, and real-time updates. This backend powers the Kreeda mobile apps for Android and iOS.

## Quick Start

### Local Development

```bash
# Clone and setup
git clone <your-repo>
cd kreeda-backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your database credentials

# Start with Docker (recommended)
docker-compose up -d

# OR start manually
./start.sh
```

### API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **pgAdmin**: http://localhost:5050 (admin@kreeda.app / admin123)

## Cricket API Endpoints

### Team Management
- `POST /api/cricket/teams` - Create team
- `GET /api/cricket/teams/{id}` - Get team with players  
- `POST /api/cricket/teams/{id}/players` - Add player

### Match Management
- `POST /api/cricket/matches` - Create match
- `POST /api/cricket/matches/{id}/toss` - Set toss result
- `POST /api/cricket/matches/{id}/start` - Start match

### Live Scoring 🚀
- `POST /api/cricket/matches/{id}/ball` - Record ball (core functionality!)
- `GET /api/cricket/matches/{id}/live` - Get live score
- `DELETE /api/cricket/matches/{id}/last-ball` - Undo last ball

### WebSocket
- `ws://localhost:8000/ws/match/{match_id}` - Real-time match updates

## Database Schema

Built around cricket's core entities:
- **Users** - Captains and scorers
- **Teams** - Cricket teams with players
- **Players** - Team members with batting order
- **Matches** - Limited overs matches (10-20 overs)
- **Innings** - Individual innings within matches  
- **Balls** - Ball-by-ball records (the heart of scoring)

## Architecture Decisions

### Why This Stack?
- **FastAPI**: Fast, modern, automatic API docs
- **SQLAlchemy**: Robust ORM with good performance
- **PostgreSQL**: ACID compliance for cricket data integrity
- **Redis**: Real-time WebSocket management
- **Pydantic**: Type safety and validation

### Performance Focus
- **3-second rule**: Every scoring action must be under 3 seconds
- **Optimized queries**: Indexed lookups for live scoring
- **WebSocket**: Real-time updates without polling
- **Offline-capable**: Mobile apps can work without internet

## Development

### Project Structure
```
app/
├── api/          # FastAPI route handlers
├── core/         # Configuration and database setup
├── models/       # SQLAlchemy database models
├── schemas/      # Pydantic request/response models
└── services/     # Business logic (cricket scoring!)
```

### Key Files
- `app/services/cricket_scoring.py` - Core scoring logic
- `app/models/cricket.py` - Database schema
- `app/api/cricket.py` - API endpoints
- `app/main.py` - FastAPI application

### Running Tests
```bash
source .venv/bin/activate
pytest
```

## Deployment

### Environment Variables
```bash
DATABASE_URL="postgresql://user:pass@host:port/db"
REDIS_URL="redis://host:port"
SECRET_KEY="your-secret-key"
BACKEND_CORS_ORIGINS="http://localhost:3000,https://yourdomain.com"
```

### Docker Deployment
```bash
# Production build
docker build -t kreeda-backend .
docker run -p 8000:8000 kreeda-backend

# With docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## MVP Scope ✅

**What's Built:**
- Team and player management
- Match creation and toss handling
- Ball-by-ball scoring with automatic calculations
- Live score API with real-time stats
- WebSocket support for live updates
- Database schema optimized for cricket

**What's NOT Built (Yet):**
- User authentication (hardcoded for MVP)
- Tournament management
- Player statistics history
- Match highlights/photos
- Advanced analytics

## Cricket Rules Implemented

### Scoring Events
- Dot ball (0 runs)
- Singles, twos, threes
- Boundaries (4s and 6s)
- Extras (wides, byes, leg-byes, no-balls)
- Wickets (bowled, caught, lbw, run out, stumped)

### Automatic Calculations
- ✅ Run rate = Total runs ÷ Overs faced
- ✅ Required run rate (2nd innings)
- ✅ Strike rate = (Runs ÷ Balls) × 100
- ✅ Over progression (6 balls = 1 over)
- ✅ Match completion detection

### Match States
- `not_started` → `innings_1` → `innings_2` → `completed`
- Automatic innings transitions
- Winner determination with margin

## Contributing

1. **Test at real cricket matches** - This is critical!
2. **Focus on speed** - 3-second rule is sacred
3. **Handle edge cases** - Cricket has many weird scenarios
4. **Keep it simple** - MVP first, features later

## Next Steps

1. **Authentication system** (JWT-based)
2. **Undo functionality** (critical for real matches)
3. **Player statistics aggregation**
4. **Match export/import**
5. **Mobile app integration testing**

---

**Built with ❤️ for cricket lovers everywhere**

*"The best cricket scoring app is one that doesn't get in the way of the game"*
