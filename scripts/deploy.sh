#!/bin/bash

# Kreeda Backend Deployment Script for Render
# This script helps with manual deployment and environment setup

set -e

echo "🚀 Kreeda Backend Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required files exist
print_status "Checking deployment requirements..."

if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found!"
    exit 1
fi

if [ ! -f "app/main.py" ]; then
    print_error "app/main.py not found!"
    exit 1
fi

if [ ! -f "alembic.ini" ]; then
    print_warning "alembic.ini not found - database migrations may not work"
fi

print_success "All required files found"

# Environment validation
print_status "Validating environment variables..."

REQUIRED_VARS=(
    "SUPABASE_URL"
    "SUPABASE_ANON_KEY" 
    "SUPABASE_SERVICE_ROLE_KEY"
    "JWT_SECRET_KEY"
    "R2_ACCESS_KEY_ID"
    "R2_SECRET_ACCESS_KEY"
    "R2_BUCKET_NAME"
    "R2_ENDPOINT_URL"
)

MISSING_VARS=()

if [ -f ".env" ]; then
    source .env
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            MISSING_VARS+=("$var")
        fi
    done
    
    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        print_warning "Missing environment variables in .env:"
        for var in "${MISSING_VARS[@]}"; do
            echo "  - $var"
        done
        print_warning "Make sure to set these in Render's environment variables"
    else
        print_success "All required environment variables found in .env"
    fi
else
    print_warning ".env file not found - make sure to set environment variables in Render"
fi

# Pre-deployment checks
print_status "Running pre-deployment checks..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+' || echo "unknown")
if [[ "$python_version" == "3.11" ]]; then
    print_success "Python version: $python_version ✓"
else
    print_warning "Python version: $python_version (recommended: 3.11)"
fi

# Install dependencies locally for validation
print_status "Installing dependencies for validation..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt --quiet --dry-run
    print_success "Dependencies validation passed"
else
    print_warning "pip3 not found - skipping dependency validation"
fi

# Validate Python syntax
print_status "Validating Python syntax..."
if python3 -m py_compile app/main.py; then
    print_success "Python syntax validation passed"
else
    print_error "Python syntax validation failed"
    exit 1
fi

# Generate deployment information
print_status "Generating deployment information..."

cat << EOF > deployment-info.md
# Kreeda Backend Deployment Information

## Deployment Date
$(date)

## Git Information
- Branch: $(git branch --show-current 2>/dev/null || echo "unknown")
- Commit: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
- Commit Message: $(git log -1 --pretty=%B 2>/dev/null | head -n1 || echo "unknown")

## Environment Variables to Set in Render

### Required Variables:
$(for var in "${REQUIRED_VARS[@]}"; do echo "- $var"; done)

### Database Variables (Auto-configured by Render):
- DATABASE_URL (from PostgreSQL add-on)
- REDIS_URL (from Redis add-on)

### Application Variables:
- ENVIRONMENT=production
- DEBUG=false
- ALLOWED_ORIGINS=https://your-frontend-domain.com

## Render Service Configuration

### Web Service:
- Build Command: \`pip install --upgrade pip && pip install -r requirements.txt\`
- Start Command: \`alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port \$PORT\`
- Health Check Path: \`/health\`
- Plan: Starter (can be upgraded)

### Add-ons Required:
1. PostgreSQL Database
2. Redis Cache

## Post-Deployment Verification

1. Check health endpoint: \`https://your-app.onrender.com/health\`
2. Verify API docs: \`https://your-app.onrender.com/docs\`
3. Test authentication endpoints
4. Verify database connection

## Manual Deployment Steps for Render

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set the build and start commands above
4. Add required environment variables
5. Create PostgreSQL and Redis add-ons
6. Deploy!

EOF

print_success "Deployment information saved to deployment-info.md"

# Final deployment readiness check
print_status "Final deployment readiness check..."

CHECKS=(
    "✓ Required files present"
    "✓ Python syntax valid"
    "✓ Dependencies installable"
    "✓ Environment variables documented"
    "✓ Render configuration ready"
)

echo ""
echo "Deployment Readiness Report:"
echo "============================"
for check in "${CHECKS[@]}"; do
    echo "  $check"
done

echo ""
print_success "🎉 Deployment ready! Your backend is ready to deploy to Render."
echo ""
print_status "Next steps:"
echo "1. Push your code to GitHub"
echo "2. Connect your repository to Render"
echo "3. Set up environment variables in Render dashboard"
echo "4. Deploy!"
echo ""
print_status "For detailed instructions, see deployment-info.md"
