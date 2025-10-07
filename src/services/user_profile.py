from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.models.user_profile import UserProfile
from src.schemas.user_profile import UserProfileCreateRequest, UserProfileUpdateRequest, UserProfileResponse

class UserProfileService:
    @staticmethod
    async def get_profile(user_id: str, db: AsyncSession) -> UserProfileResponse:
        """Get user profile by user_id"""
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise ValueError("Profile not found")
        
        return UserProfileResponse.from_orm(profile)

    @staticmethod
    async def create_profile(user_id: str, request: UserProfileCreateRequest, db: AsyncSession) -> UserProfileResponse:
        """Create user profile"""
        # Check if profile already exists
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        existing_profile = result.scalar_one_or_none()
        
        if existing_profile:
            raise ValueError("Profile already exists")

        profile = UserProfile(
            user_id=UUID(user_id),
            name=request.name,
            avatar_url=request.avatar_url,
            location=request.location,
            date_of_birth=request.date_of_birth,
            bio=request.bio,
            preferences=request.preferences,
            roles=request.roles,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        
        return UserProfileResponse.from_orm(profile)

    @staticmethod
    async def update_profile(user_id: str, request: UserProfileUpdateRequest, db: AsyncSession) -> UserProfileResponse:
        """Update user profile"""
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise ValueError("Profile not found")

        update_data = {}
        if request.name is not None:
            update_data['name'] = request.name
        if request.avatar_url is not None:
            update_data['avatar_url'] = request.avatar_url
        if request.location is not None:
            update_data['location'] = request.location
        if request.date_of_birth is not None:
            update_data['date_of_birth'] = request.date_of_birth
        if request.bio is not None:
            update_data['bio'] = request.bio
        if request.preferences is not None:
            update_data['preferences'] = request.preferences
        if request.roles is not None:
            update_data['roles'] = request.roles
        
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            await db.execute(
                update(UserProfile)
                .where(UserProfile.user_id == user_id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(profile)
        
        return UserProfileResponse.from_orm(profile)

    @staticmethod
    async def delete_profile(user_id: str, db: AsyncSession) -> dict:
        """Delete user profile"""
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise ValueError("Profile not found")
        
        await db.delete(profile)
        await db.commit()
        
        return {"message": "Profile deleted successfully"}