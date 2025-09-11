# Render Environment Variables Checklist

Copy these environment variables from your `.env` file to Render's environment variables section:

## 🔐 Required Secrets (Critical)
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=kreeda-assets
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
```

## 🛠️ Application Settings
```
ENVIRONMENT=production
DEBUG=false
PYTHON_VERSION=3.11.12
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://your-app.onrender.com
```

## 🔄 Auto-configured by Render (Don't set these manually)
```
DATABASE_URL=postgresql://... (from PostgreSQL add-on)
REDIS_URL=redis://... (from Redis add-on)
PORT=10000 (automatically set by Render)
```

## 📝 How to add these in Render:

1. Go to your web service in Render dashboard
2. Click on "Environment" tab
3. Click "Add Environment Variable"
4. Copy each variable name and value from above
5. Click "Save Changes"

⚠️ **Important Notes:**
- Never commit these values to Git
- Keep your JWT_SECRET_KEY secure and unique
- Update ALLOWED_ORIGINS to match your actual domains
- Render will automatically provide DATABASE_URL and REDIS_URL when you add PostgreSQL and Redis services
