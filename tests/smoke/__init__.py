"""
Smoke test configuration and utilities
"""

# Default timeouts for smoke tests
DEFAULT_TIMEOUT = 10
EXTENDED_TIMEOUT = 30

# Expected response times (in seconds)
HEALTH_CHECK_MAX_TIME = 2
API_RESPONSE_MAX_TIME = 5

# Test data
TEST_ENDPOINTS = [
    "/health",
    "/api/v1/health", 
    "/docs",
    "/redoc",
    "/openapi.json"
]

AUTH_REQUIRED_ENDPOINTS = [
    "/api/v1/teams/",
    "/api/v1/cricket/matches",
    "/api/v1/statistics/players/stats",
    "/api/v1/tournaments/",
    "/api/v1/notifications/",
    "/api/v1/users/"
]