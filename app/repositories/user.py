from typing import Optional, List
from sqlalchemy import select, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from app.models.user import User, AuthProvider
from app.schemas.auth import UserCreate


class UserRepository:
    """Repository for user database operations."""
    
    async def create_user(self, db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            user = User(
                email=user_data.email,
                username=user_data.username,
                full_name=user_data.full_name,
                avatar_url=user_data.avatar_url,
                auth_provider=user_data.auth_provider,
                provider_id=user_data.provider_id,
                role=user_data.role
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("User with this email or username already exists")
    
    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            user_uuid = UUID(user_id)
            result = await db.execute(select(User).where(User.id == user_uuid))
            return result.scalar_one_or_none()
        except ValueError:
            return None
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    async def get_user_by_provider(
        self, 
        db: AsyncSession, 
        provider: AuthProvider, 
        provider_id: str
    ) -> Optional[User]:
        """Get user by OAuth provider and provider ID."""
        result = await db.execute(
            select(User).where(
                and_(
                    User.auth_provider == provider,
                    User.provider_id == provider_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def check_user_exists(
        self, 
        db: AsyncSession, 
        email: str, 
        username: str
    ) -> Optional[User]:
        """Check if user exists by email or username."""
        result = await db.execute(
            select(User).where(
                or_(
                    User.email == email,
                    User.username == username
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def update_password(self, db: AsyncSession, user_id: str, hashed_password: str) -> None:
        """Update user's password."""
        user_uuid = UUID(user_id)
        await db.execute(
            update(User)
            .where(User.id == user_uuid)
            .values(hashed_password=hashed_password)
        )
        await db.commit()
    
    async def update_refresh_token(self, db: AsyncSession, user_id: str, refresh_token_hash: Optional[str] = None) -> None:
        """Update user's refresh token hash."""
        user_uuid = UUID(user_id)
        await db.execute(
            update(User)
            .where(User.id == user_uuid)
            .values(refresh_token_hash=refresh_token_hash)
        )
        await db.commit()
    
    async def set_reset_token(self, db: AsyncSession, user_id: str, reset_token_hash: Optional[str] = None) -> None:
        """Set password reset token hash."""
        user_uuid = UUID(user_id)
        await db.execute(
            update(User)
            .where(User.id == user_uuid)
            .values(reset_token_hash=reset_token_hash)
        )
        await db.commit()
    
    async def get_user_by_reset_token(self, db: AsyncSession, reset_token_hash: str) -> Optional[User]:
        """Get user by password reset token hash."""
        result = await db.execute(
            select(User).where(User.reset_token_hash == reset_token_hash)
        )
        return result.scalar_one_or_none()
    
    async def set_verification_token(self, db: AsyncSession, user_id: str, verification_token_hash: str) -> None:
        """Set email verification token hash."""
        user_uuid = UUID(user_id)
        await db.execute(
            update(User)
            .where(User.id == user_uuid)
            .values(email_verification_token_hash=verification_token_hash)
        )
        await db.commit()
    
    async def get_user_by_verification_token(self, db: AsyncSession, verification_token_hash: str) -> Optional[User]:
        """Get user by email verification token hash."""
        result = await db.execute(
            select(User).where(User.email_verification_token_hash == verification_token_hash)
        )
        return result.scalar_one_or_none()
    
    async def verify_email(self, db: AsyncSession, user_id: str) -> None:
        """Mark user's email as verified."""
        user_uuid = UUID(user_id)
        await db.execute(
            update(User)
            .where(User.id == user_uuid)
            .values(
                is_email_verified=True,
                email_verification_token_hash=None
            )
        )
        await db.commit()
    
    async def update_profile(
        self, 
        db: AsyncSession, 
        user_id: str, 
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> None:
        """Update user profile information."""
        user_uuid = UUID(user_id)
        
        update_data = {}
        if full_name is not None:
            update_data["full_name"] = full_name
        if phone is not None:
            update_data["phone"] = phone
        if avatar_url is not None:
            update_data["avatar_url"] = avatar_url
        
        if update_data:
            await db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(**update_data)
            )
            await db.commit()
    
    async def deactivate_user(self, db: AsyncSession, user_id: str) -> None:
        """Deactivate a user account."""
        user_uuid = UUID(user_id)
        await db.execute(
            update(User)
            .where(User.id == user_uuid)
            .values(is_active=False)
        )
        await db.commit()
    
    async def activate_user(self, db: AsyncSession, user_id: str) -> None:
        """Activate a user account."""
        user_uuid = UUID(user_id)
        await db.execute(
            update(User)
            .where(User.id == user_uuid)
            .values(is_active=True)
        )
        await db.commit()


# Singleton instance
user_repository = UserRepository()
