# Kreeda Backend - Quick Commands Reference

## 🚀 Docker Commands

### Start System
```bash
docker-compose up -d
```

### Stop System
```bash
docker-compose down
```

### Rebuild & Restart
```bash
docker-compose up --build -d
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f db
docker-compose logs -f redis
```

### Container Shell Access
```bash
# App container
docker-compose exec app bash

# Database
docker-compose exec db psql -U kreeda_user -d kreeda_db

# Redis
docker-compose exec redis redis-cli
```

## 🧪 Testing Commands

### Run All Tests
```bash
docker-compose exec app pytest tests/ -v
```

### Run Specific Test File
```bash
docker-compose exec app pytest tests/test_auth.py -v
```

### Run with Coverage
```bash
docker-compose exec app pytest --cov=src --cov-report=html
```

### Run Endpoint Tests (Bash Script)
```bash
./test_endpoints_v2.sh
```

## 🗄️ Database Commands

### Run Migrations
```bash
docker-compose exec app alembic upgrade head
```

### Create New Migration
```bash
docker-compose exec app alembic revision --autogenerate -m "description"
```

### Check Current Migration
```bash
docker-compose exec app alembic current
```

### View Migration History
```bash
docker-compose exec app alembic history
```

### Rollback Migration
```bash
docker-compose exec app alembic downgrade -1
```

### Database Queries
```bash
# Count users
docker-compose exec db psql -U kreeda_user -d kreeda_db -c "SELECT COUNT(*) FROM user_auth;"

# List all users
docker-compose exec db psql -U kreeda_user -d kreeda_db -c "SELECT email, created_at FROM user_auth;"

# View tables
docker-compose exec db psql -U kreeda_user -d kreeda_db -c "\dt"
```

## 🔧 Development Commands

### Install New Package
1. Add package to `requirements.txt`
2. Rebuild container:
```bash
docker-compose up --build -d
```

### Format Code (if Black is installed)
```bash
docker-compose exec app black src/
```

### Lint Code (if Flake8 is installed)
```bash
docker-compose exec app flake8 src/
```

## 📝 API Testing Commands

### Register User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test@123456",
    "phone_number": "+1234567890",
    "name": "Test User"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/auth/signin/password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test@123456"
  }'
```

### Get Current User
```bash
TOKEN="your-access-token-here"
curl -X GET "http://localhost:8000/auth/user" \
  -H "Authorization: Bearer $TOKEN"
```

### Refresh Token
```bash
REFRESH_TOKEN="your-refresh-token-here"
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
```

## 🔍 Debugging Commands

### Check Container Status
```bash
docker-compose ps
```

### Check Container Health
```bash
docker inspect kreeda-backend-app-1 | jq '.[0].State'
```

### View Application Logs (Last 100 lines)
```bash
docker-compose logs --tail=100 app
```

### Check for Errors
```bash
docker-compose logs app | grep -i error
```

### Interactive Python Shell
```bash
docker-compose exec app python
```

### Check Redis Keys
```bash
docker-compose exec redis redis-cli KEYS '*'
```

### Monitor Redis Commands
```bash
docker-compose exec redis redis-cli MONITOR
```

## 🛠️ Maintenance Commands

### Clean Up Docker
```bash
# Remove all containers and volumes
docker-compose down -v

# Remove unused images
docker image prune -a

# Remove all unused resources
docker system prune -a --volumes
```

### Backup Database
```bash
docker-compose exec db pg_dump -U kreeda_user kreeda_db > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
docker-compose exec -T db psql -U kreeda_user kreeda_db < backup_20241010.sql
```

### Export Environment Variables
```bash
export DATABASE_URL="postgresql+asyncpg://kreeda_user:kreeda_pass@db:5432/kreeda_db"
export REDIS_URL="redis://redis:6379"
export JWT_SECRET="your-secret-key"
```

## 📚 Useful URLs

- **API Docs (Swagger)**: http://localhost:8000/api/docs
- **API Docs (ReDoc)**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🚨 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs app

# Rebuild from scratch
docker-compose down -v
docker-compose up --build -d
```

### Database Connection Issues
```bash
# Check if database is running
docker-compose ps db

# Test connection
docker-compose exec app python -c "from src.database.connection import engine; print('OK')"
```

### Migration Issues
```bash
# Reset migrations
docker-compose exec db psql -U kreeda_user -d kreeda_db -c "DELETE FROM alembic_version;"
docker-compose exec app alembic upgrade head
```

### Redis Connection Issues
```bash
# Check Redis
docker-compose exec redis redis-cli ping

# Should return: PONG
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

## 📊 Performance Monitoring

### Check Database Connections
```bash
docker-compose exec db psql -U kreeda_user -d kreeda_db -c "SELECT count(*) FROM pg_stat_activity;"
```

### Check Redis Memory Usage
```bash
docker-compose exec redis redis-cli INFO memory
```

### Monitor Container Resources
```bash
docker stats
```

## 🔐 Security Commands

### Generate New JWT Secret
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Check Environment Variables
```bash
docker-compose exec app env | grep -E "DATABASE_URL|REDIS_URL|JWT_SECRET"
```

### List Active Sessions (Redis)
```bash
docker-compose exec redis redis-cli KEYS "session:*"
```
