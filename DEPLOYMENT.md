# 🚀 Kreeda Backend - CI/CD and Render Deployment Guide

This guide will help you set up continuous integration/continuous deployment (CI/CD) with GitHub Actions and deploy your Kreeda backend to Render.

## 📋 Prerequisites

- GitHub repository with your code
- Render account (free tier available)
- Environment variables from your `.env` file

## 🔧 CI/CD Pipeline Features

Our GitHub Actions workflow includes:

### ✅ Automated Testing
- Code quality checks (Black, isort, flake8)
- Unit tests with coverage reporting
- Security scanning (Safety, Bandit)
- PostgreSQL and Redis service containers

### 🔒 Security Features
- Dependency vulnerability scanning
- Code security analysis
- Coverage reporting with Codecov integration

### 🚀 Automated Deployment
- Deploys on push to `main`, `master`, or `production-config` branches
- Health checks after deployment
- API documentation updates
- Postman collection generation

## 📝 Setup Instructions

### 1. GitHub Repository Setup

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Add CI/CD pipeline and Render deployment config"
   git push origin production-config
   ```

2. **Set up GitHub Secrets:**
   Go to your repository → Settings → Secrets and variables → Actions

   Add these secrets:
   ```
   RENDER_SERVICE_ID=your-render-service-id
   RENDER_API_KEY=your-render-api-key
   RENDER_APP_URL=https://your-app-name.onrender.com
   CODECOV_TOKEN=your-codecov-token (optional)
   ```

### 2. Render Deployment Setup

#### Option A: Using Render Blueprint (Recommended)

1. **Connect GitHub to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Select the repository with your code

2. **Deploy with Blueprint:**
   - Render will read the `render.yaml` file
   - It will automatically create:
     - Web service (your API)
     - PostgreSQL database
     - Redis cache
   - Click "Apply" to deploy

#### Option B: Manual Setup

1. **Create PostgreSQL Database:**
   - New → PostgreSQL
   - Name: `kreeda-db`
   - Plan: Free tier
   - Note the connection string

2. **Create Redis Cache:**
   - New → Redis
   - Name: `kreeda-redis`  
   - Plan: Free tier
   - Note the connection string

3. **Create Web Service:**
   - New → Web Service
   - Connect your GitHub repository
   - Configure:
     - **Name:** `kreeda-backend`
     - **Runtime:** Python 3
     - **Build Command:** `pip install --upgrade pip && pip install -r requirements.txt`
     - **Start Command:** `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - **Health Check Path:** `/health`

### 3. Environment Variables Configuration

In your Render web service, add these environment variables:

#### 🔐 Required Secrets (from your .env file):
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Cloudflare R2 Storage
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=kreeda-assets
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### 🔄 Auto-configured by Render:
```bash
DATABASE_URL=postgresql://... (from PostgreSQL add-on)
REDIS_URL=redis://... (from Redis add-on)
```

#### 🛠️ Application Settings:
```bash
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://your-app.onrender.com
PYTHON_VERSION=3.11.12
```

### 4. Deployment Validation

Run the deployment readiness script:
```bash
./scripts/deploy.sh
```

This will:
- ✅ Check all required files
- ✅ Validate Python syntax
- ✅ Check dependencies
- ✅ Generate deployment information
- ✅ Provide next steps

## 🔄 Deployment Workflow

### Automatic Deployment (CI/CD)
1. Push code to `main`, `master`, or `production-config` branch
2. GitHub Actions automatically:
   - Runs tests and quality checks
   - Performs security scans
   - Deploys to Render (if tests pass)
   - Runs health checks
   - Updates API documentation

### Manual Deployment
1. Push code to GitHub
2. Render auto-deploys on code changes
3. Or manually trigger deployment in Render dashboard

## 📊 Monitoring and Health Checks

### Health Check Endpoint
Your app will be available at: `https://your-app-name.onrender.com`

**Health Check:** `GET /health`
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "environment": "production",
    "version": "1.0.0"
  }
}
```

### API Documentation
- **OpenAPI Docs:** `https://your-app-name.onrender.com/docs`
- **ReDoc:** `https://your-app-name.onrender.com/redoc`
- **OpenAPI JSON:** `https://your-app-name.onrender.com/openapi.json`

## 🐛 Troubleshooting

### Common Issues

1. **Build Failures:**
   - Check `requirements.txt` syntax
   - Verify Python version compatibility
   - Review build logs in Render dashboard

2. **Database Connection Issues:**
   - Ensure PostgreSQL add-on is attached
   - Verify `DATABASE_URL` environment variable
   - Check database connectivity

3. **Environment Variable Issues:**
   - Double-check all required variables are set
   - Ensure no trailing spaces in values
   - Verify secret keys are correct

4. **Health Check Failures:**
   - Check application logs
   - Verify `/health` endpoint works locally
   - Ensure dependencies are properly installed

### Logs and Debugging

**View Logs:**
- Render Dashboard → Your Service → Logs
- Real-time log streaming available

**Local Testing:**
```bash
# Test with production-like settings
docker-compose up --build
curl http://localhost:8000/health
```

## 🔐 Security Considerations

1. **Environment Variables:**
   - Never commit `.env` files to Git
   - Use strong, unique JWT secret keys
   - Rotate keys regularly

2. **Database Security:**
   - Use connection pooling
   - Enable SSL connections
   - Regular backups (Render handles this)

3. **API Security:**
   - CORS properly configured
   - Rate limiting implemented
   - Input validation on all endpoints

## 📈 Performance Optimization

1. **Render Scaling:**
   - Start with free tier
   - Upgrade to paid plans for production
   - Enable auto-scaling if needed

2. **Database Optimization:**
   - Use connection pooling
   - Index frequently queried fields
   - Regular performance monitoring

3. **Caching:**
   - Redis for session management
   - API response caching
   - Static file caching

## 🚀 Going Live

### Final Checklist
- [ ] All environment variables configured
- [ ] Database migrations applied
- [ ] Health check passes
- [ ] API documentation accessible
- [ ] SSL certificate active (automatic on Render)
- [ ] Domain configured (if using custom domain)
- [ ] Monitoring set up

### Custom Domain (Optional)
1. Add custom domain in Render dashboard
2. Update DNS records as instructed
3. SSL certificate will be automatically provisioned

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Supabase Documentation](https://supabase.com/docs)

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Render and GitHub Actions logs
3. Consult the deployment information generated by `./scripts/deploy.sh`

---

**Happy Deploying! 🎉**

Your Kreeda backend will be live and ready to serve your cricket scoring application!
