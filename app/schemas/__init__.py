"""
Data Schemas and Validation Models

This package contains all Pydantic models used for:
- Request/response serialization
- Data validation and type checking
- API documentation generation
- Database model validation

Modules:
- auth: Authentication and OAuth2 related schemas
- user: User profile and account schemas
- team: Team management schemas
- tournament: Tournament organization schemas
- match: Match scheduling and tracking schemas
- score: Scoring and statistics schemas

Features:
- Pydantic v2 compatibility
- Comprehensive validation rules
- Custom validators for business logic
- OAuth2 compliant token formats
- OpenAPI schema generation
"""

# Import commonly used base models
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# Common base classes that might be shared across schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        from_attributes = True
        use_enum_values = True
        populate_by_name = True


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""
    
    created_at: datetime
    updated_at: Optional[datetime] = None


class PaginationSchema(BaseModel):
    """Standard pagination response schema."""
    
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total: int = Field(ge=0, description="Total number of items")
    pages: int = Field(ge=0, description="Total number of pages")


class ResponseSchema(BaseSchema):
    """Standard API response wrapper."""
    
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


__all__ = [
    "BaseSchema",
    "TimestampSchema", 
    "PaginationSchema",
    "ResponseSchema"
]
