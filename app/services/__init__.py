"""
Business Logic Services

This package contains all business logic services that handle complex operations
and coordinate between repositories, external APIs, and other services.

Services:
- auth: Authentication and authorization service with OAuth2 support
- oauth_service: Third-party OAuth providers (Google, Apple, etc.)
- user: User management and profile operations
- team: Team management and membership logic
- tournament: Tournament organization and management
- match: Match scheduling and game logic
- score: Scoring calculations and statistics
- notification: Real-time notifications and messaging

Each service encapsulates business rules, validation logic, and cross-cutting
concerns while maintaining clean separation from data access and API layers.
"""

from .auth import auth_service, oauth_service

__all__ = [
    "auth_service",
    "oauth_service"
]
