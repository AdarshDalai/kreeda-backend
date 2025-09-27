"""
User Management Module

This module handles user accounts, profiles, and sport-specific data
"""

from .models import User, UserProfile, SportProfile
from .schemas import (
    User as UserSchema, UserCreate, UserUpdate, UserSummary, UserListResponse,
    UserWithProfile, SportProfile as SportProfileSchema, SportProfileCreate, 
    SportProfileUpdate
)
from .service import UserService
from .endpoints import router as user_router

__all__ = [
    # Models
    "User", "UserProfile", "SportProfile",
    
    # Schemas
    "UserSchema", "UserCreate", "UserUpdate", "UserSummary", "UserListResponse",
    "UserWithProfile", "SportProfileSchema", "SportProfileCreate", "SportProfileUpdate",
    
    # Service
    "UserService",
    
    # Router
    "user_router"
]