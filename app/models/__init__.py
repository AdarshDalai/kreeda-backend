"""
Database Models

SQLAlchemy ORM models representing the core entities of the Kreeda platform.
These models define the database schema, relationships, and constraints.

Models:
- User: User accounts, authentication, and profile information
- Team: Team management and membership tracking
- Tournament: Tournament organization and structure
- Match: Individual matches and game sessions
- Score: Scoring records and statistics

Features:
- Async SQLAlchemy support for high-performance database operations
- Comprehensive relationship definitions with proper foreign keys
- Database constraints and validation rules
- Audit fields for tracking creation and modification times
- Enum types for controlled vocabulary fields
- UUID primary keys for security and scalability
"""

# Import all models for easier access
from .user import User
from .team import Team
from .match import Match
from .tournament import Tournament
from .score import Score

__all__ = ["User", "Team", "Match", "Tournament", "Score"]
