"""
Data Access Layer - Repositories

This package implements the Repository pattern for data access operations.
Each repository handles database operations for specific domain entities,
providing a clean abstraction layer between business logic and data persistence.

Repositories:
- user: User account and profile data operations
- team: Team management and membership data
- tournament: Tournament organization data
- match: Match scheduling and tracking data
- score: Scoring and statistics data

Features:
- Async/await support for database operations
- Transaction management and rollback handling
- Query optimization and caching strategies
- Type-safe database operations with SQLAlchemy
- Clean separation of concerns from business logic
"""

from .user import user_repository

__all__ = [
    "user_repository"
]
