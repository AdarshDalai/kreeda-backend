"""
User Management Service

Business logic for user management operations
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.modules.users.models import User, UserProfile, SportProfile
from app.modules.users.schemas import (
    UserCreate, UserUpdate, SportProfileCreate, SportProfileUpdate
)


class UserService:
    """Service class for user management operations"""

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user with profile"""
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username
        )
        db.add(user)
        await db.flush()  # Get the user ID

        # Create profile if additional data provided
        if any([user_data.full_name, user_data.bio, user_data.location, 
                user_data.date_of_birth, user_data.phone_number]):
            profile = UserProfile(
                user_id=user.id,
                full_name=user_data.full_name,
                bio=user_data.bio,
                location=user_data.location,
                date_of_birth=user_data.date_of_birth,
                phone_number=user_data.phone_number
            )
            db.add(profile)

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID with profile and sport profiles"""
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.profile),
                selectinload(User.sport_profiles)
            )
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_users(
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        sport_type: Optional[str] = None
    ) -> tuple[List[User], int]:
        """List users with filtering and pagination"""
        
        query = select(User).options(selectinload(User.profile))
        
        # Add filters
        filters = []
        if search:
            filters.append(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.profile.has(UserProfile.full_name.ilike(f"%{search}%"))
                )
            )
        
        if is_active is not None:
            filters.append(User.is_active == is_active)
            
        if sport_type:
            filters.append(
                User.sport_profiles.any(
                    and_(
                        SportProfile.sport_type == sport_type,
                        SportProfile.is_active == True
                    )
                )
            )

        if filters:
            query = query.where(and_(*filters))

        # Get total count
        count_query = select(func.count(User.id))
        if filters:
            count_query = count_query.where(and_(*filters))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.offset((page - 1) * per_page).limit(per_page).order_by(User.username)
        
        result = await db.execute(query)
        users = list(result.scalars().all())

        return users, total

    @staticmethod
    async def update_user(db: AsyncSession, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user and profile information"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return None

        # Update user fields
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.username is not None:
            user.username = user_data.username

        # Update or create profile
        profile_data = {
            k: v for k, v in user_data.model_dump().items() 
            if k in ['full_name', 'bio', 'location', 'date_of_birth', 'phone_number', 'avatar_url', 'preferences']
            and v is not None
        }

        if profile_data:
            if user.profile:
                # Update existing profile
                for key, value in profile_data.items():
                    setattr(user.profile, key, value)
            else:
                # Create new profile
                profile = UserProfile(user_id=user.id, **profile_data)
                db.add(profile)

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: str) -> bool:
        """Delete user (soft delete by setting is_active=False)"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return False

        user.is_active = False
        await db.commit()
        return True

    # Sport Profile methods
    @staticmethod
    async def create_sport_profile(
        db: AsyncSession, 
        user_id: str, 
        sport_data: SportProfileCreate
    ) -> Optional[SportProfile]:
        """Create a sport profile for a user"""
        # Check if user exists
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return None

        # Check if sport profile already exists
        existing = await db.execute(
            select(SportProfile).where(
                and_(
                    SportProfile.user_id == user_id,
                    SportProfile.sport_type == sport_data.sport_type
                )
            )
        )
        if existing.scalar_one_or_none():
            return None  # Already exists

        sport_profile = SportProfile(
            user_id=user_id,
            **sport_data.model_dump()
        )
        db.add(sport_profile)
        await db.commit()
        await db.refresh(sport_profile)
        return sport_profile

    @staticmethod
    async def get_sport_profile(
        db: AsyncSession, 
        user_id: str, 
        sport_type: str
    ) -> Optional[SportProfile]:
        """Get sport profile for user and sport type"""
        result = await db.execute(
            select(SportProfile).where(
                and_(
                    SportProfile.user_id == user_id,
                    SportProfile.sport_type == sport_type
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_sport_profile(
        db: AsyncSession,
        user_id: str,
        sport_type: str,
        sport_data: SportProfileUpdate
    ) -> Optional[SportProfile]:
        """Update sport profile"""
        sport_profile = await UserService.get_sport_profile(db, user_id, sport_type)
        if not sport_profile:
            return None

        update_data = sport_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(sport_profile, key, value)

        await db.commit()
        await db.refresh(sport_profile)
        return sport_profile