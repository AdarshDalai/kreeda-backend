#!/bin/bash

# Kreeda Backend Deployment Script for Render
# This script helps automate the deployment process

echo "🚀 Kreeda Backend Deployment to Render"
echo "======================================"

# Check if git is clean
if [[ -n $(git status --porcelain) ]]; then
    echo "❌ You have uncommitted changes. Please commit or stash them first."
    git status
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# Check if we're on master or production-config
if [[ "$CURRENT_BRANCH" != "master" && "$CURRENT_BRANCH" != "production-config" ]]; then
    echo "⚠️  Warning: You're not on master or production-config branch."
    echo "   Consider switching to a production-ready branch."
fi

# Show recent commits
echo ""
echo "📝 Recent commits:"
git log --oneline -5

echo ""
echo "✅ Pre-deployment checks completed!"
echo ""
echo "🎯 Next Steps:"
echo "1. Go to https://render.com and sign in"
echo "2. Click 'New +' and select 'Web Service'"
echo "3. Connect your GitHub repository: AdarshDalai/kreeda-backend"
echo "4. Use these settings:"
echo "   - Name: kreeda-backend"
echo "   - Branch: $CURRENT_BRANCH"
echo "   - Build Command: pip install --upgrade pip && pip install -r requirements.txt"
echo "   - Start Command: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
echo "   - Plan: Starter (free)"
echo ""
echo "5. Add the following Add-ons:"
echo "   - PostgreSQL (Starter plan)"
echo "   - Redis (Starter plan)"
echo ""
echo "6. Set Environment Variables (from .env.production.template):"
echo "   - ENVIRONMENT=production"
echo "   - DEBUG=false"
echo "   - SUPABASE_URL=<your-supabase-url>"
echo "   - SUPABASE_ANON_KEY=<your-supabase-anon-key>"
echo "   - SUPABASE_SERVICE_ROLE_KEY=<your-supabase-service-role-key>"
echo "   - R2_ACCESS_KEY_ID=<your-r2-access-key>"
echo "   - R2_SECRET_ACCESS_KEY=<your-r2-secret-key>"
echo "   - R2_BUCKET_NAME=kreeda-assets"
echo "   - R2_ENDPOINT_URL=<your-r2-endpoint>"
echo "   - JWT_SECRET_KEY=<secure-random-string>"
echo "   - ALLOWED_ORIGINS=[\"https://your-frontend-domain.com\"]"
echo ""
echo "7. Deploy!"
echo ""
echo "📋 After deployment, verify:"
echo "   - Health check: https://your-app.onrender.com/health"
echo "   - API docs: https://your-app.onrender.com/docs"
echo ""
echo "💡 Note: DATABASE_URL and REDIS_URL will be automatically set by Render add-ons"
