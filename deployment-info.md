# Kreeda Backend Deployment Information

## Deployment Date
Thu Sep 11 20:11:52 IST 2025

## Git Information
- Branch: production-config
- Commit: 4c6ed3fa7ffd8120175d31bba3099583a020368b
- Commit Message: updated codes with supabase fix and user settings added; almost ready for prod

## Environment Variables to Set in Render

### Required Variables:
- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY
- JWT_SECRET_KEY
- R2_ACCESS_KEY_ID
- R2_SECRET_ACCESS_KEY
- R2_BUCKET_NAME
- R2_ENDPOINT_URL

### Database Variables (Auto-configured by Render):
- DATABASE_URL (from PostgreSQL add-on)
- REDIS_URL (from Redis add-on)

### Application Variables:
- ENVIRONMENT=production
- DEBUG=false
- ALLOWED_ORIGINS=https://your-frontend-domain.com

## Render Service Configuration

### Web Service:
- Build Command: `pip install --upgrade pip && pip install -r requirements.txt`
- Start Command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`
- Plan: Starter (can be upgraded)

### Add-ons Required:
1. PostgreSQL Database
2. Redis Cache

## Post-Deployment Verification

1. Check health endpoint: `https://your-app.onrender.com/health`
2. Verify API docs: `https://your-app.onrender.com/docs`
3. Test authentication endpoints
4. Verify database connection

## Manual Deployment Steps for Render

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set the build and start commands above
4. Add required environment variables
5. Create PostgreSQL and Redis add-ons
6. Deploy!

