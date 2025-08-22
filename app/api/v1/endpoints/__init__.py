"""
API v1 Endpoints

Individual endpoint modules for different functional areas of the Kreeda platform.

Modules:
- auth: Authentication, OAuth2, and user session management
- oauth2: OAuth2 2.0 authorization server endpoints
- users: User profile and account management
- teams: Team creation, management, and membership
- tournaments: Tournament organization and management
- matches: Match scheduling, management, and tracking
- scores: Scoring system and statistics

Each module follows RESTful conventions and includes:
- CRUD operations where applicable
- Proper HTTP status codes
- Input validation and error handling
- OAuth2 scope-based authorization
- OpenAPI documentation
"""

# Import all endpoint routers for easy access
from . import auth, oauth2, users, teams, tournaments, matches, scores

__all__ = [
    "auth",
    "oauth2", 
    "users",
    "teams",
    "tournaments",
    "matches", 
    "scores"
]
