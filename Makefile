# Makefile for Kreeda Backend Development and CI/CD
.PHONY: help install dev test test-unit test-integration test-api test-performance test-coverage clean lint format security build deploy docker-build docker-up docker-down docker-test migrate seed docs

# Default target
help: ## Show this help message
	@echo "Kreeda Backend - Available Commands:"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development Setup
install: ## Install dependencies
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .

install-dev: ## Install development dependencies
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .

dev: ## Start development server
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-debug: ## Start development server with debug logging
	DEBUG=true LOG_LEVEL=DEBUG uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Testing
test: ## Run all tests
	pytest tests/ -v --tb=short

test-unit: ## Run unit tests only
	pytest tests/test_auth.py tests/test_users.py tests/test_user_profile.py -v --tb=short

test-integration: ## Run integration tests
	pytest tests/test_e2e_integration.py tests/test_teams.py tests/test_tournaments.py -v --tb=short

test-api: ## Run API tests
	pytest tests/test_cricket.py tests/test_statistics.py tests/test_stats_api.py tests/test_notifications.py -v --tb=short

test-smoke: ## Run smoke tests for deployment validation
	pytest tests/smoke/ -v --tb=short

test-performance: ## Run performance tests
	cd tests/performance && locust -f locustfile.py --headless -u 10 -r 2 -t 60s --host=http://localhost:8000

test-coverage: ## Run tests with coverage report
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml

test-watch: ## Run tests in watch mode
	pytest-watch tests/ -- -v --tb=short

# Code Quality
lint: ## Run linting
	flake8 app/ tests/ --count --show-source --statistics
	mypy app/ --ignore-missing-imports

format: ## Format code
	black app/ tests/
	isort app/ tests/ --profile black

format-check: ## Check code formatting without making changes
	black --check --diff app/ tests/
	isort --check-only --diff app/ tests/ --profile black

security: ## Run security checks
	bandit -r app/ -f json -o bandit-report.json
	bandit -r app/ --severity-level medium
	safety check --json
	pip-audit --desc

quality: format-check lint security ## Run all code quality checks

# Database
migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create MESSAGE="description")
	alembic revision --autogenerate -m "$(MESSAGE)"

migrate-downgrade: ## Downgrade database by one revision
	alembic downgrade -1

migrate-history: ## Show migration history
	alembic history

seed: ## Seed database with sample data
	python scripts/seed_database.py

# Docker Operations
docker-build: ## Build Docker image
	docker build -t kreeda-backend .

docker-build-dev: ## Build Docker image for development
	docker build --target builder -t kreeda-backend:dev .

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-up-build: ## Start services with Docker Compose and rebuild
	docker-compose up -d --build

docker-down: ## Stop Docker Compose services
	docker-compose down

docker-down-volumes: ## Stop Docker Compose services and remove volumes
	docker-compose down -v

docker-test: ## Run tests in Docker
	docker-compose --profile test up --build --abort-on-container-exit

docker-performance: ## Run performance tests in Docker
	docker-compose --profile performance up --build

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-shell: ## Get shell access to the app container
	docker-compose exec app bash

docker-db-shell: ## Get shell access to the database
	docker-compose exec postgres psql -U kreeda -d kreeda_dev

# Deployment
deploy-staging: ## Deploy to staging environment
	./scripts/deploy.sh staging

deploy-production: ## Deploy to production environment
	./scripts/deploy.sh production

# Documentation
docs: ## Generate API documentation
	python -c "
import json
from app.main import app
with open('openapi.json', 'w') as f:
    json.dump(app.openapi(), f, indent=2)
print('OpenAPI spec generated: openapi.json')
"

docs-serve: ## Serve documentation locally
	python -m http.server 8080 &
	@echo "Documentation available at http://localhost:8080/docs"

# Monitoring and Debugging
logs: ## Show application logs (requires running container)
	docker-compose logs -f app

monitor: ## Start monitoring stack
	docker-compose --profile monitoring up -d

monitor-down: ## Stop monitoring stack
	docker-compose --profile monitoring down

# Database Utilities
db-reset: ## Reset database (DESTRUCTIVE - for development only)
	@echo "⚠️  This will destroy all data in the development database!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up -d postgres redis; \
		sleep 10; \
		alembic upgrade head; \
		echo "✅ Database reset complete"; \
	else \
		echo "❌ Database reset cancelled"; \
	fi

db-backup: ## Backup database
	@echo "Creating database backup..."
	docker-compose exec postgres pg_dump -U kreeda kreeda_dev > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup created"

# Cleaning
clean: ## Clean up temporary files and caches
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .mypy_cache/ .tox/
	rm -f bandit-report.json coverage.xml

clean-docker: ## Clean up Docker images and containers
	docker system prune -f
	docker volume prune -f

# CI/CD Helpers
ci-install: ## Install CI dependencies
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov pytest-xdist pytest-timeout
	pip install black isort flake8 mypy bandit safety pip-audit

ci-test: ## Run CI test suite
	pytest tests/ -v --cov=app --cov-report=xml --cov-report=term-missing --maxfail=5 --tb=short

ci-quality: ## Run CI quality checks
	black --check app/ tests/
	isort --check-only app/ tests/ --profile black
	flake8 app/ tests/ --count --show-source
	mypy app/ --ignore-missing-imports
	bandit -r app/ --severity-level medium
	safety check

# Local development helpers
local-env: ## Set up local environment file
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from .env.example"; \
		echo "📝 Please update .env with your local configuration"; \
	else \
		echo "⚠️  .env file already exists"; \
	fi

requirements: ## Generate requirements.txt from current environment
	pip freeze > requirements.txt
	@echo "✅ Requirements updated"

# Health checks
health: ## Check application health
	@curl -f http://localhost:8000/health || echo "❌ Application not responding"

api-health: ## Check API health
	@curl -f http://localhost:8000/api/v1/health || echo "❌ API not responding"

# Version management
version: ## Show current version
	@python -c "from app.main import app; print(f'Version: {app.version}')"

# All-in-one commands
setup: local-env install-dev migrate ## Complete local setup
	@echo "🎉 Setup complete! Run 'make dev' to start the development server"

full-test: quality test-coverage ## Run complete test suite with quality checks

all: clean setup full-test ## Clean, setup, and run full test suite