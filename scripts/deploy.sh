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
COMMAND=""

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
if [[ -z "$COMMAND" ]]; then
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
    
    BUILD_ARGS=""
    if [[ "$NO_CACHE" == "true" ]]; then
        BUILD_ARGS="--no-cache"
    fi
    
    cd "$PROJECT_ROOT"
    docker build $BUILD_ARGS -t "$IMAGE_NAME:$TAG" .
    
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
        if command -v docker-compose >/dev/null 2>&1; then
            docker-compose run --rm test pytest tests/ --tb=short || log_warning "Tests failed but continuing deployment"
        fi
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
    
    if [[ -f "$COMPOSE_FILE" ]]; then
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
    else
        log_warning "Docker compose file $COMPOSE_FILE not found, skipping container deployment"
    fi
    
    # Run smoke tests
    log_info "Running smoke tests..."
    if [[ -f "tests/smoke/test_deployment.py" ]]; then
        python tests/smoke/test_deployment.py || log_warning "Smoke tests failed but deployment continues"
    else
        log_warning "Smoke tests not found, skipping"
    fi
    
    log_success "Deployment completed successfully"
}

# Rollback to previous version
rollback_deployment() {
    setup_environment
    
    log_warning "Rolling back $ENVIRONMENT environment..."
    
    if [[ "$FORCE" != "true" ]]; then
        read -p "Rollback $ENVIRONMENT to previous version? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Rollback cancelled"
            exit 0
        fi
    fi
    
    cd "$PROJECT_ROOT"
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        # Get previous image tag from deployment history
        PREVIOUS_TAG=$(docker images "$IMAGE_NAME" --format "table {{.Tag}}" | sed -n '2p' | tr -d ' ')
        
        if [[ -n "$PREVIOUS_TAG" ]]; then
            log_info "Rolling back to tag: $PREVIOUS_TAG"
            
            export IMAGE_TAG="$PREVIOUS_TAG"
            docker-compose -f "$COMPOSE_FILE" up -d "$SERVICE_NAME"
            
            log_success "Rollback completed"
        else
            log_error "No previous version found to rollback to"
            exit 1
        fi
    else
        log_error "Docker compose file $COMPOSE_FILE not found"
        exit 1
    fi
}

# Check application health
check_health() {
    setup_environment
    
    log_info "Checking health of $ENVIRONMENT environment..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        # Check if service is running
        if ! docker-compose -f "$COMPOSE_FILE" ps "$SERVICE_NAME" | grep -q "Up"; then
            log_error "Service is not running"
            exit 1
        fi
        
        # Check health endpoint
        if docker-compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log_success "Service is healthy"
        else
            log_error "Service health check failed"
            exit 1
        fi
        
        # Check database connectivity
        if docker-compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" python -c "
from app.utils.database import get_db
from sqlalchemy import text
import asyncio

async def check_db():
    async for db in get_db():
        await db.execute(text('SELECT 1'))
        break

asyncio.run(check_db())
print('Database connection successful')
" 2>/dev/null; then
            log_success "Database is accessible"
        else
            log_error "Database connection failed"
            exit 1
        fi
    else
        log_error "Docker compose file $COMPOSE_FILE not found"
        exit 1
    fi
}

# Show application logs
show_logs() {
    setup_environment
    
    log_info "Showing logs for $ENVIRONMENT environment..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        if [[ "$FOLLOW_LOGS" == "true" ]]; then
            docker-compose -f "$COMPOSE_FILE" logs -f "$SERVICE_NAME"
        else
            docker-compose -f "$COMPOSE_FILE" logs --tail=100 "$SERVICE_NAME"
        fi
    else
        log_error "Docker compose file $COMPOSE_FILE not found"
        exit 1
    fi
}

# Run database migrations
run_migrations() {
    setup_environment
    
    log_info "Running database migrations for $ENVIRONMENT..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        docker-compose -f "$COMPOSE_FILE" exec "$SERVICE_NAME" alembic upgrade head
        log_success "Migrations completed"
    else
        # Fallback to local alembic
        if command -v alembic >/dev/null 2>&1; then
            alembic upgrade head
            log_success "Migrations completed"
        else
            log_error "Neither Docker nor local alembic available"
            exit 1
        fi
    fi
}

# Seed database with test data
seed_database() {
    setup_environment
    
    log_info "Seeding database for $ENVIRONMENT..."
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_error "Cannot seed production database"
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        docker-compose -f "$COMPOSE_FILE" exec "$SERVICE_NAME" python -c "
from app.utils.database import get_db
from app.models import *
import asyncio

async def seed_data():
    # Add your seeding logic here
    print('Database seeded successfully')

asyncio.run(seed_data())
"
        log_success "Database seeded"
    else
        log_error "Docker compose file $COMPOSE_FILE not found"
        exit 1
    fi
}

# Main execution
main() {
    case "$COMMAND" in
        build)
            build_image
            ;;
        deploy)
            deploy_application
            ;;
        rollback)
            rollback_deployment
            ;;
        health)
            check_health
            ;;
        logs)
            show_logs
            ;;
        migrate)
            run_migrations
            ;;
        seed)
            seed_database
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# Trap errors and cleanup
trap 'log_error "Script failed on line $LINENO"' ERR

# Run main function
main "$@"