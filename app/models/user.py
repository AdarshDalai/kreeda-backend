from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, String as SQLString
import uuid
import enum
from datetime import datetime

from app.core.database import Base


class AuthProvider(str, enum.Enum):
    """Authentication providers supported by Kreeda."""
    EMAIL = "email"
    GOOGLE = "google"
    APPLE = "apple"


class UserRole(str, enum.Enum):
    """User roles in the system."""
    PLAYER = "player"
    SCOREKEEPER = "scorekeeper"
    ORGANIZER = "organizer"
    SPECTATOR = "spectator"
    ADMIN = "admin"


class StringEnum(TypeDecorator):
    """Custom type that ensures enums are always returned as strings."""
    impl = SQLString
    cache_ok = True
    
    def __init__(self, enum_class, *args, **kwargs):
        self.enum_class = enum_class
        super().__init__(*args, **kwargs)
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return value.value if hasattr(value, 'value') else str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return self.enum_class(value)


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    
    # Authentication fields
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    auth_provider = Column(StringEnum(AuthProvider), nullable=False, default=AuthProvider.EMAIL)
    provider_id = Column(String(255), nullable=True)  # ID from OAuth provider
    
    # Profile information
    full_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(Text, nullable=True)
    
    # User status and permissions
    role = Column(StringEnum(UserRole), nullable=False, default=UserRole.PLAYER)
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Security fields
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Token management (for refresh tokens, reset tokens, etc.)
    refresh_token_hash = Column(String(255), nullable=True)
    reset_token_hash = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    email_verification_token_hash = Column(String(255), nullable=True)
    email_verification_token_expires = Column(DateTime(timezone=True), nullable=True)

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email}, provider={self.auth_provider})>"
