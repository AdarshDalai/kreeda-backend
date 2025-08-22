"""
API Version 1

Version 1 of the Kreeda REST API, providing comprehensive sports management functionality.

Endpoints:
- /auth: Authentication and OAuth2 endpoints
- /users: User management and profiles
- /teams: Team creation and management
- /tournaments: Tournament organization
- /matches: Match scheduling and management
- /scores: Scoring and statistics

Features:
- OAuth2 2.0 compliance with multiple grant types
- Role-based access control
- Input validation with Pydantic
- Comprehensive error handling
- Real-time updates and notifications
- Pagination and filtering support
"""

from .api import api_router

__all__ = ["api_router"]
