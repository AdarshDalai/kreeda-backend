"""
Kreeda Backend Base Model

SQLAlchemy declarative base and common model functionality
"""

from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all database models
    
    Provides common functionality:
    - Automatic table naming
    - Common timestamp fields
    - Utility methods
    """
    
    # Generate table name automatically from class name
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        import re
        # Convert CamelCase to snake_case
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        cls.__tablename__ = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


class BaseModel(Base):
    """
    Base model with common fields and functionality
    
    All application models should inherit from this class
    """
    __abstract__ = True

    # Common timestamp fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary
        
        Returns:
            Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """
        Update model fields from dictionary
        
        Args:
            data: Dictionary with field values to update
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """String representation of the model"""
        class_name = self.__class__.__name__
        
        # Try to use id, name, or title for representation
        identity = None
        for attr in ['id', 'name', 'title', 'username', 'email']:
            if hasattr(self, attr):
                identity = getattr(self, attr)
                break
        
        if identity:
            return f"<{class_name}({identity})>"
        else:
            return f"<{class_name}>"