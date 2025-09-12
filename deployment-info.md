# Kreeda Backend Deployment Information

## Latest Deployment Date

Thu Sep 12 21:15:00 IST 2025

## Git Information

- Branch: master
- Commit: 1c28bc6
- Commit Message: Add Render deployment configuration and scripts

## Environment Variables to Set in Render

### Required Variables

- ENVIRONMENT=production
- DEBUG=false
- SUPABASE_URL=your-supabase-project-url
- SUPABASE_ANON_KEY=your-supabase-anon-key
- SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
- JWT_SECRET_KEY=secure-random-string-min-32-chars
- R2_ACCESS_KEY_ID=your-cloudflare-r2-access-key
- R2_SECRET_ACCESS_KEY=your-cloudflare-r2-secret-key
- R2_BUCKET_NAME=kreeda-assets
- R2_ENDPOINT_URL=your-cloudflare-r2-endpoint-url
- ALLOWED_ORIGINS=["https://your-frontend-domain.com"]

### Database Variables (Auto-configured by Render)

- DATABASE_URL (from PostgreSQL add-on)
- REDIS_URL (from Redis add-on)

## Render Service Configuration

### Web Service

- **Name**: kreeda-backend
- **Repository**: AdarshDalai/kreeda-backend
- **Branch**: master
- **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command**: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/health`
- **Plan**: Starter (free tier)

### Add-ons Required

1. PostgreSQL Database
   - Plan: Free tier for testing
   - Database Name: kreeda_db

2. Redis Instance
   - Plan: Free tier for testing
   - Use: Caching and session storage

## Deployment Steps

1. Push latest code to master branch
2. Connect GitHub repository to Render
3. Create web service with above configuration
4. Add PostgreSQL and Redis add-ons
5. Set all required environment variables
6. Deploy and verify health endpoint

## Post-Deployment Verification

- Check health endpoint: `https://your-app-name.onrender.com/health`
- Verify database connection in logs
- Test API endpoints with sample requests
- Monitor application logs for any errors

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

