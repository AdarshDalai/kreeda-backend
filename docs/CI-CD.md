# CI/CD Documentation

## Overview
The Kreeda Backend project uses a comprehensive CI/CD pipeline built with GitHub Actions that includes testing, security scanning, performance testing, and automated deployment.

## Workflows

### 1. Main CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

This is the primary workflow that runs on every push and pull request.

#### Features:
- **Matrix Testing**: Tests across multiple Python versions (3.10, 3.11)
- **Multi-stage Testing**: Unit, Integration, API, and E2E tests
- **Security Scanning**: Integrated security checks with multiple tools
- **Performance Testing**: Load testing with realistic user scenarios
- **Docker Integration**: Multi-stage builds with security hardening
- **Deployment**: Automated deployment with health checks

#### Stages:
1. **Lint & Format**: Code quality checks with black, flake8, mypy
2. **Test**: Comprehensive test suite with coverage reporting
3. **Security**: Security scanning with results uploaded to GitHub Security tab
4. **Performance**: Load testing with performance metrics
5. **Build**: Docker image building and testing
6. **Deploy**: Automated deployment with smoke tests

### 2. Security Scanning (`.github/workflows/security.yml`)

Dedicated security workflow that runs daily and on code changes.

#### Tools Used:
- **Bandit**: Python security linter
- **Safety**: Python dependency vulnerability scanner
- **Semgrep**: Static analysis security testing (SAST)
- **pip-audit**: Python package auditing
- **Trivy**: Container and filesystem security scanner
- **Hadolint**: Dockerfile security linter
- **TruffleHog**: Secrets detection

#### SARIF Integration:
All security tools generate SARIF (Static Analysis Results Interchange Format) reports that are automatically uploaded to GitHub's Security tab for centralized vulnerability management.

### 3. Dependency Updates (`.github/workflows/dependency-updates.yml`)

Automated dependency management workflow.

#### Features:
- Weekly dependency updates
- Automated security patches
- Automated testing of updates
- PR creation for manual review

## Testing Strategy

### Test Types:
1. **Unit Tests**: Fast, isolated component tests
2. **Integration Tests**: Database and service integration
3. **API Tests**: Endpoint testing with various scenarios
4. **E2E Tests**: Full application workflow testing
5. **Performance Tests**: Load testing with Locust
6. **Smoke Tests**: Deployment validation tests

### Test Organization:
```
tests/
├── unit/              # Unit tests (fastest)
├── integration/       # Integration tests
├── api/              # API endpoint tests
├── e2e/              # End-to-end tests
├── performance/      # Load testing
└── smoke/           # Deployment validation
```

### Performance Testing:
- **Tool**: Locust for realistic load simulation
- **Scenarios**: Multiple user types (regular users, admin, mobile app)
- **Metrics**: Response time, throughput, error rates
- **Thresholds**: Configurable performance baselines

## Docker Setup

### Multi-stage Dockerfile:
1. **Base Stage**: Common dependencies and security updates
2. **Development Stage**: Development tools and debugging
3. **Testing Stage**: Test dependencies and test execution
4. **Production Stage**: Minimal production image

### Security Features:
- Non-root user execution
- Minimal attack surface
- Security-hardened base images
- Dependency vulnerability scanning

### Docker Compose Profiles:
- **Default**: Basic development environment
- **Testing**: Full test environment with database
- **Performance**: Load testing setup with monitoring
- **Monitoring**: Observability stack (Prometheus, Grafana)

## Development Workflow

### Prerequisites:
```bash
# Install dependencies
make install

# Set up pre-commit hooks
make setup-dev

# Start development environment
make dev
```

### Available Commands:
```bash
# Development
make dev              # Start development server
make test             # Run all tests
make test-unit        # Run unit tests only
make test-integration # Run integration tests
make lint             # Run linting
make format           # Format code

# Performance
make perf-test        # Run performance tests
make load-test        # Run load testing

# Docker
make build            # Build Docker image
make run              # Run in container
make clean            # Clean up containers

# Database
make db-migrate       # Run migrations
make db-reset         # Reset database
```

### Pre-commit Hooks:
Automated code quality checks on every commit:
- Black formatting
- Flake8 linting
- MyPy type checking
- Import sorting
- Security scanning
- Test validation

## Deployment

### Environments:
1. **Development**: Local development with hot reload
2. **Testing**: CI/CD test environment
3. **Staging**: Pre-production environment
4. **Production**: Live production environment

### Deployment Process:
1. Code push triggers CI/CD pipeline
2. All tests must pass
3. Security scans must be clean
4. Performance tests must meet thresholds
5. Docker image is built and tested
6. Deployment to staging with smoke tests
7. Manual approval for production deployment
8. Production deployment with health checks
9. Post-deployment validation

### Health Checks:
- Application health endpoint
- Database connectivity
- External service dependencies
- Performance baseline validation

## Monitoring & Observability

### Metrics Collection:
- Application performance metrics
- Business metrics (user engagement, feature usage)
- Infrastructure metrics (CPU, memory, disk)
- Error tracking and alerting

### Logging:
- Structured JSON logging
- Request/response logging
- Error logging with stack traces
- Performance logging

### Alerting:
- Critical error alerts
- Performance degradation alerts
- Security incident alerts
- Deployment status alerts

## Security

### Security Measures:
1. **Static Analysis**: Code security scanning
2. **Dependency Scanning**: Vulnerability detection in dependencies
3. **Container Scanning**: Docker image security analysis
4. **Secrets Detection**: Preventing credential leaks
5. **SARIF Integration**: Centralized security reporting

### Security Policies:
- No hardcoded secrets
- Regular dependency updates
- Security patch prioritization
- Vulnerability disclosure process

## Configuration

### Environment Variables:
```bash
# Database
DATABASE_URL=postgresql://...
DATABASE_TEST_URL=postgresql://...

# Authentication
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...

# Application
ENVIRONMENT=development|staging|production
DEBUG=true|false
LOG_LEVEL=INFO

# Performance
REDIS_URL=redis://...
WORKER_CONCURRENCY=4
```

### Secrets Management:
- GitHub Secrets for CI/CD
- Environment-specific configuration
- Secure credential rotation

## Troubleshooting

### Common Issues:

1. **Test Failures**:
   ```bash
   # Run specific test
   make test TEST_PATH=tests/test_specific.py
   
   # Debug with verbose output
   make test-debug
   ```

2. **Performance Issues**:
   ```bash
   # Run performance profiling
   make perf-profile
   
   # Check resource usage
   make monitor
   ```

3. **Security Alerts**:
   ```bash
   # Run security scan locally
   make security-scan
   
   # Update dependencies
   make update-deps
   ```

4. **Deployment Issues**:
   ```bash
   # Check deployment logs
   make logs
   
   # Run smoke tests
   make smoke-test
   ```

### Debugging:
- Comprehensive logging throughout the application
- Debug mode for development
- Performance profiling tools
- Error tracking and monitoring

## Best Practices

### Code Quality:
- Write comprehensive tests
- Follow PEP 8 style guidelines
- Use type hints consistently
- Document complex logic
- Keep functions small and focused

### Security:
- Never commit secrets
- Regularly update dependencies
- Follow security best practices
- Monitor security alerts

### Performance:
- Profile performance regularly
- Optimize database queries
- Use appropriate caching
- Monitor resource usage

### Deployment:
- Test thoroughly before deployment
- Use feature flags for risky changes
- Monitor deployments closely
- Have rollback procedures ready

## Getting Help

### Resources:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)

### Support:
- Check existing GitHub issues
- Review CI/CD logs for errors
- Run local debugging commands
- Contact the development team