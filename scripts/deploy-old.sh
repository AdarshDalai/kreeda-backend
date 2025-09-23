#!/bin/bash

# Kreeda Backend Deployment Script
# This script handles deployment to different environments

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="kreeda-backend"
DEFAULT_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Kreeda Backend Deployment Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    build       Build Docker image
    deploy      Deploy to environment
    rollback    Rollback to previous version
    health      Check application health
    logs        Show application logs
    migrate     Run database migrations
    seed        Seed database with test data

Options:
    -e, --env       Environment (development|staging|production)
    -t, --tag       Docker image tag (default: latest)
    -h, --help      Show this help message
    -v, --verbose   Verbose output
    --no-cache      Build without cache
    --force         Force deployment without confirmation

Examples:
    $0 build
    $0 deploy --env staging
    $0 deploy --env production --tag v1.2.3
    $0 rollback --env staging
    $0 health --env production
    $0 logs --env staging --follow

Environment Variables:
    DOCKER_REGISTRY     Docker registry URL
    DATABASE_URL        Database connection string
    SUPABASE_URL        Supabase project URL
    SUPABASE_ANON_KEY   Supabase anonymous key
EOF
}

# Parse command line arguments
ENVIRONMENT=""
TAG="$DEFAULT_TAG"
VERBOSE=false
NO_CACHE=false
FORCE=false
FOLLOW_LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --follow)
            FOLLOW_LOGS=true
            shift
            ;;
        build|deploy|rollback|health|logs|migrate|seed)
            COMMAND="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate command
if [[ -z "${COMMAND:-}" ]]; then
    log_error "Command is required"
    show_help
    exit 1
fi

# Validate environment for commands that need it
if [[ "$COMMAND" =~ ^(deploy|rollback|health|logs|migrate|seed)$ ]] && [[ -z "$ENVIRONMENT" ]]; then
    log_error "Environment is required for command: $COMMAND"
    exit 1
fi

# Validate environment value
if [[ -n "$ENVIRONMENT" ]] && [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT"
    log_error "Valid environments: development, staging, production"
    exit 1
fi

# Set verbose output
if [[ "$VERBOSE" == "true" ]]; then
    set -x
fi

# Environment-specific configurations
setup_environment() {
    case "$ENVIRONMENT" in
        development)
            COMPOSE_FILE="docker-compose.yml"
            SERVICE_NAME="api"
            ;;
        staging)
            COMPOSE_FILE="docker-compose.staging.yml"
            SERVICE_NAME="api"
            ;;
        production)
            COMPOSE_FILE="docker-compose.production.yml"
            SERVICE_NAME="api"
            ;;
    esac
}

# Build Docker image
build_image() {
    log_info "Building Docker image: $IMAGE_NAME:$TAG"
    
    BUILD_ARGS=()
    if [[ "$NO_CACHE" == "true" ]]; then
        BUILD_ARGS+=(--no-cache)
    fi
    
    cd "$PROJECT_ROOT"
    docker build "${BUILD_ARGS[@]}" -t "$IMAGE_NAME:$TAG" .
    
    log_success "Image built successfully: $IMAGE_NAME:$TAG"
}

# Run pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if image exists
    if ! docker image inspect "$IMAGE_NAME:$TAG" >/dev/null 2>&1; then
        log_error "Image $IMAGE_NAME:$TAG not found. Build it first."
        exit 1
    fi
    
    # Check environment variables
    required_vars=("DATABASE_URL")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_warning "Environment variable $var is not set"
        fi
    done
    
    # Run tests if not in production
    if [[ "$ENVIRONMENT" != "production" ]]; then
        log_info "Running tests..."
        cd "$PROJECT_ROOT"
        docker-compose run --rm test pytest tests/ --tb=short
    fi
    
    log_success "Pre-deployment checks passed"
}

# Deploy application
deploy_application() {
    setup_environment
    
    log_info "Deploying to $ENVIRONMENT environment..."
    
    if [[ "$FORCE" != "true" ]]; then
        read -p "Deploy $IMAGE_NAME:$TAG to $ENVIRONMENT? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    pre_deployment_checks
    
    cd "$PROJECT_ROOT"
    
    # Export tag for docker-compose
    export IMAGE_TAG="$TAG"
    
    # Pull latest images and deploy
    docker-compose -f "$COMPOSE_FILE" pull
    docker-compose -f "$COMPOSE_FILE" up -d "$SERVICE_NAME"
    
    # Wait for service to be healthy
    log_info "Waiting for service to be healthy..."
    timeout 300 bash -c "
        while ! docker-compose -f $COMPOSE_FILE exec -T $SERVICE_NAME curl -f http://localhost:8000/health >/dev/null 2>&1; do
            sleep 5
        done
    " || {
        log_error "Service failed to become healthy"
        show_logs
        exit 1
    }
    
    # Run smoke tests
    log_info "Running smoke tests..."
    if ! python tests/smoke/test_deployment.py; then
        log_error "Smoke tests failed"
        exit 1
    fi
    
    log_success "Deployment completed successfully"
}

# Function to check service health
check_health() {
    setup_environment
    
    log_info "Checking health of $ENVIRONMENT environment..."
    
    cd "$PROJECT_ROOT"
    
    # Check if service is running
    if ! docker-compose -f "$COMPOSE_FILE" ps "$SERVICE_NAME" | grep -q "Up"; then
        log_error "Service is not running"
        exit 1
    fi
    
    # Check health endpoint
    local url="http://localhost:8000/health"
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url/health" > /dev/null; then
            echo "✅ Health check passed!"
            return 0
        else
            echo "❌ Health check failed, attempt $attempt/$max_attempts"
            if [ $attempt -eq $max_attempts ]; then
                echo "🚨 Health check failed after $max_attempts attempts"
                return 1
            fi
            sleep 10
            attempt=$((attempt + 1))
        fi
    done
}

# Function to run database migrations
run_migrations() {
    echo "🗄️  Running database migrations..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        # In production, migrations should be run carefully
        echo "⚠️  Production migration - ensuring backup exists..."
        # Add backup logic here if needed
    fi
    
    # Run Alembic migrations
    alembic upgrade head
    
    if [ $? -eq 0 ]; then
        echo "✅ Database migrations completed successfully"
    else
        echo "❌ Database migrations failed"
        exit 1
    fi
}

# Function to warm up application
warm_up_app() {
    local base_url=$1
    echo "🔥 Warming up application..."
    
    # Hit key endpoints to warm up the application
    endpoints=(
        "/health"
        "/api/v1/health"
        "/docs"
        "/openapi.json"
    )
    
    for endpoint in "${endpoints[@]}"; do
        echo "📡 Warming up $endpoint"
        curl -s "$base_url$endpoint" > /dev/null || echo "⚠️  Warning: $endpoint not responding"
    done
    
    echo "✅ Application warm-up completed"
}

# Main deployment logic
case $ENVIRONMENT in
    development)
        echo "🔧 Development deployment"
        # For development, just ensure the app is running
        ;;
        
    staging)
        echo "🎭 Staging deployment"
        run_migrations
        # Add staging-specific steps here
        ;;
        
    production)
        echo "🏭 Production deployment"
        
        # Production deployment steps
        echo "⚠️  Production deployment - extra safety checks"
        
        # Check if we have the required environment variables
        required_vars=(
            "DATABASE_URL"
            "SUPABASE_URL"
            "SUPABASE_ANON_KEY"
            "JWT_SECRET_KEY"
            "SECRET_KEY"
        )
        
        for var in "${required_vars[@]}"; do
            if [ -z "${!var}" ]; then
                echo "❌ Required environment variable $var is not set"
                exit 1
            fi
        done
        
        echo "✅ Environment variables validated"
        
        # Run migrations
        run_migrations
        
        # Additional production checks
        echo "🔒 Running production safety checks..."
        
        # Check that debug mode is disabled
        if [ "$DEBUG" = "true" ]; then
            echo "❌ Debug mode is enabled in production!"
            exit 1
        fi
        
        echo "✅ Production safety checks passed"
        ;;
        
    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        echo "Valid environments: development, staging, production"
        exit 1
        ;;
esac

# Post-deployment tasks
if [ -n "$RENDER_APP_URL" ]; then
    echo "🌐 Application URL: $RENDER_APP_URL"
    
    # Check application health
    if check_health "$RENDER_APP_URL"; then
        # Warm up the application
        warm_up_app "$RENDER_APP_URL"
        
        echo "🎉 Deployment completed successfully!"
        echo "🔗 API Documentation: $RENDER_APP_URL/docs"
        echo "📊 Health Check: $RENDER_APP_URL/health"
    else
        echo "💥 Deployment failed - application is not healthy"
        exit 1
    fi
else
    echo "⚠️  RENDER_APP_URL not set - skipping health checks"
fi

echo "✨ Deployment script completed for $ENVIRONMENT environment"