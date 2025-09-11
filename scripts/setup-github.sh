#!/bin/bash

# GitHub Repository Setup for CI/CD
# This script helps prepare your repository for GitHub Actions and Render deployment

set -e

echo "🔧 GitHub Repository Setup for CI/CD"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository! Please run 'git init' first."
    exit 1
fi

print_status "Setting up GitHub repository for CI/CD deployment..."

# Check current branch
current_branch=$(git branch --show-current 2>/dev/null || echo "main")
print_status "Current branch: $current_branch"

# Add all files
print_status "Adding deployment files to git..."
git add .github/
git add render.yaml
git add scripts/deploy.sh
git add DEPLOYMENT.md
git add requirements-prod.txt

# Check if there are changes to commit
if git diff --staged --quiet; then
    print_warning "No new changes to commit"
else
    print_status "Committing CI/CD setup files..."
    git commit -m "Add CI/CD pipeline and Render deployment configuration

    - GitHub Actions workflow for automated testing and deployment
    - Render configuration with PostgreSQL and Redis
    - Deployment scripts and documentation
    - Production requirements file
    - Comprehensive deployment guide"
    
    print_success "CI/CD files committed successfully"
fi

# Check remote origin
if git remote get-url origin > /dev/null 2>&1; then
    origin_url=$(git remote get-url origin)
    print_status "Remote origin: $origin_url"
    
    # Ask if user wants to push
    echo ""
    read -p "Push changes to GitHub? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Pushing to origin/$current_branch..."
        git push origin "$current_branch"
        print_success "Code pushed to GitHub successfully!"
    else
        print_warning "Skipped pushing to GitHub"
    fi
else
    print_warning "No remote origin configured"
    echo "To add a remote origin:"
    echo "  git remote add origin https://github.com/yourusername/kreeda-backend.git"
fi

# Display next steps
echo ""
print_success "🎉 Repository setup complete!"
echo ""
echo "Next steps for deployment:"
echo "=========================="
echo ""
echo "1. 📱 GitHub Repository Setup:"
echo "   - Go to your repository on GitHub"
echo "   - Navigate to Settings → Secrets and variables → Actions"
echo "   - Add these secrets:"
echo "     * RENDER_SERVICE_ID=your-render-service-id"
echo "     * RENDER_API_KEY=your-render-api-key"  
echo "     * RENDER_APP_URL=https://your-app-name.onrender.com"
echo "     * CODECOV_TOKEN=your-codecov-token (optional)"
echo ""
echo "2. 🚀 Render Deployment:"
echo "   - Go to https://dashboard.render.com"
echo "   - Click 'New' → 'Blueprint'"
echo "   - Connect your GitHub repository"
echo "   - Render will read render.yaml and create all services"
echo ""
echo "3. ⚙️ Environment Variables:"
echo "   - Copy your .env file contents"
echo "   - Add them to Render's environment variables section"
echo "   - Don't forget to set ENVIRONMENT=production"
echo ""
echo "4. 🔍 Verification:"
echo "   - Check https://your-app-name.onrender.com/health"
echo "   - Visit https://your-app-name.onrender.com/docs"
echo ""
echo "📚 For detailed instructions, see DEPLOYMENT.md"
echo ""
print_status "Happy deploying! 🚀"
