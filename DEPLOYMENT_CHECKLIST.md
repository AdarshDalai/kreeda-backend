# Render Deployment Checklist for Kreeda Backend

## Pre-Deployment Checklist

- [ ] Code is pushed to master branch
- [ ] All tests are passing in CI/CD
- [ ] Environment variables template is reviewed
- [ ] Database migration scripts are ready

## Render Setup Steps

### 1. Account Setup
- [ ] Go to https://render.com and sign in with your GitHub account
- [ ] Verify your account if required

### 2. Create Web Service
- [ ] Click "New +" button and select "Web Service"
- [ ] Connect GitHub repository: `AdarshDalai/kreeda-backend`
- [ ] Select branch: `master`
- [ ] Name your service: `kreeda-backend`

### 3. Service Configuration
- [ ] Build Command: `pip install --upgrade pip && pip install -r requirements.txt`
- [ ] Start Command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Health Check Path: `/health`
- [ ] Plan: Starter (free tier)

### 4. Add Database Services
- [ ] Add PostgreSQL database (free tier)
- [ ] Add Redis cache (free tier)
- [ ] Note down the connection URLs

### 5. Environment Variables Setup
Copy from `.env.production.template` and set real values:

- [ ] ENVIRONMENT=production
- [ ] DEBUG=false
- [ ] SUPABASE_URL=your-actual-supabase-url
- [ ] SUPABASE_ANON_KEY=your-actual-anon-key
- [ ] SUPABASE_SERVICE_ROLE_KEY=your-actual-service-role-key
- [ ] JWT_SECRET_KEY=your-secure-32-char-secret
- [ ] R2_ACCESS_KEY_ID=your-cloudflare-access-key
- [ ] R2_SECRET_ACCESS_KEY=your-cloudflare-secret-key
- [ ] R2_BUCKET_NAME=kreeda-assets
- [ ] R2_ENDPOINT_URL=your-cloudflare-endpoint
- [ ] ALLOWED_ORIGINS=["https://your-frontend-domain.com"]

### 6. Deploy
- [ ] Click "Create Web Service" to start deployment
- [ ] Monitor build logs for any errors
- [ ] Wait for deployment to complete

## Post-Deployment Verification

### Health Checks
- [ ] Visit `https://your-app-name.onrender.com/health`
- [ ] Should return: `{"status": "healthy", "timestamp": "..."}`

### API Documentation
- [ ] Visit `https://your-app-name.onrender.com/docs`
- [ ] Swagger UI should load properly

### Database Connection
- [ ] Check application logs for successful database connection
- [ ] Verify Alembic migrations ran successfully

### Authentication Test
- [ ] Test user registration endpoint
- [ ] Test user login endpoint
- [ ] Verify JWT token generation

### File Upload Test
- [ ] Test file upload endpoints (if applicable)
- [ ] Verify R2 storage connection

## Troubleshooting

### Common Issues

1. **Build Fails**
   - Check Python version compatibility
   - Verify all dependencies in requirements.txt
   - Check build logs for specific error messages

2. **App Crashes on Start**
   - Verify environment variables are set correctly
   - Check database connection strings
   - Review application startup logs

3. **Database Connection Issues**
   - Ensure PostgreSQL add-on is properly configured
   - Verify DATABASE_URL is automatically set by Render
   - Check if migrations need to be run manually

4. **Authentication Issues**
   - Verify Supabase URLs and keys
   - Check JWT secret key is set
   - Ensure CORS origins include your frontend domain

### Log Monitoring
- [ ] Monitor logs in Render dashboard
- [ ] Set up log retention if needed
- [ ] Configure alerts for errors

## Security Checklist

- [ ] All sensitive data is in environment variables
- [ ] No hardcoded secrets in code
- [ ] CORS is properly configured
- [ ] JWT secrets are secure and random
- [ ] Database access is restricted

## Performance Monitoring

- [ ] Monitor response times
- [ ] Check memory usage
- [ ] Monitor database query performance
- [ ] Set up uptime monitoring

## Backup and Maintenance

- [ ] Set up database backups (if not using free tier)
- [ ] Plan for regular dependency updates
- [ ] Monitor for security vulnerabilities
- [ ] Set up staging environment for testing

---

**Note**: Keep this checklist updated as your deployment process evolves. Document any custom configurations or troubleshooting steps specific to your setup.
