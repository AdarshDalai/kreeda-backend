from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
import logging

from app.models.user import User
from app.schemas.user import UserUpdate
from app.auth import supabase_auth

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user-related operations"""
    
    @staticmethod
    async def get_users(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """
        Get list of users with optional filtering
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search term for username, email, or full_name
            is_active: Filter by active status
            
        Returns:
            List of User objects
        """
        try:
            query = select(User)
            
            # Apply filters
            conditions = []
            
            if search:
                search_filter = or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
                conditions.append(search_filter)
            
            if is_active is not None:
                conditions.append(User.is_active == is_active)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await db.execute(query)
            users = result.scalars().all()
            
            logger.info(f"Retrieved {len(users)} users with filters: search={search}, is_active={is_active}")
            return list(users)
            
        except Exception as e:
            logger.error(f"Error retrieving users: {e}")
            raise Exception(f"Failed to retrieve users: {str(e)}")
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User object or None
        """
        try:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                logger.info(f"Retrieved user: {user.username}")
            else:
                logger.warning(f"User not found with ID: {user_id}")
                
            return user
            
        except Exception as e:
            logger.error(f"Error retrieving user by ID {user_id}: {e}")
            raise Exception(f"Failed to retrieve user: {str(e)}")
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            User object or None
        """
        try:
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if user:
                logger.info(f"Retrieved user by email: {user.username}")
            else:
                logger.warning(f"User not found with email: {email}")
                
            return user
            
        except Exception as e:
            logger.error(f"Error retrieving user by email {email}: {e}")
            raise Exception(f"Failed to retrieve user: {str(e)}")
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """
        Get user by username
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            User object or None
        """
        try:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if user:
                logger.info(f"Retrieved user by username: {user.username}")
            else:
                logger.warning(f"User not found with username: {username}")
                
            return user
            
        except Exception as e:
            logger.error(f"Error retrieving user by username {username}: {e}")
            raise Exception(f"Failed to retrieve user: {str(e)}")
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        username: str,
        full_name: str,
        supabase_id: Optional[str] = None
    ) -> User:
        """
        Create a new user
        
        Args:
            db: Database session
            email: User email
            username: Username
            full_name: Full name
            supabase_id: Supabase user ID
            
        Returns:
            Created User object
        """
        try:
            # Check if user already exists
            existing_user = await UserService.get_user_by_email(db, email)
            if existing_user:
                raise Exception(f"User with email {email} already exists")
            
            existing_username = await UserService.get_user_by_username(db, username)
            if existing_username:
                raise Exception(f"Username {username} already exists")
            
            # Create new user
            new_user = User(
                email=email,
                username=username,
                full_name=full_name,
                supabase_id=supabase_id,
                is_active=True
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            logger.info(f"Created new user: {username} ({email})")
            return new_user
            
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            await db.rollback()
            raise Exception(f"Failed to create user: {str(e)}")
    
    @staticmethod
    async def update_user(
        db: AsyncSession,
        user: User,
        user_update: UserUpdate
    ) -> User:
        """
        Update user information
        
        Args:
            db: Database session
            user: User object to update
            user_update: Update data
            
        Returns:
            Updated User object
        """
        try:
            # Update local fields
            update_data = user_update.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                if field == "data" and value:
                    # Handle nested data updates
                    for key, val in value.items():
                        if key == "username":
                            setattr(user, 'username', str(val))
                        elif key == "full_name":
                            setattr(user, 'full_name', str(val))
                elif hasattr(user, field):
                    setattr(user, field, value)
            
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Updated user: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Error updating user {user.username}: {e}")
            await db.rollback()
            raise Exception(f"Failed to update user: {str(e)}")
    
    @staticmethod
    async def soft_delete_user(db: AsyncSession, user: User) -> User:
        """
        Soft delete a user (mark as inactive)
        
        Args:
            db: Database session
            user: User to delete
            
        Returns:
            Updated User object
        """
        try:
            setattr(user, 'is_active', False)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Soft deleted user: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Error soft deleting user {user.username}: {e}")
            await db.rollback()
            raise Exception(f"Failed to delete user: {str(e)}")
    
    @staticmethod
    async def hard_delete_user(db: AsyncSession, user: User) -> bool:
        """
        Hard delete a user (permanent removal)
        
        Args:
            db: Database session
            user: User to delete
            
        Returns:
            True if successful
        """
        try:
            username = user.username
            await db.delete(user)
            await db.commit()
            
            logger.info(f"Hard deleted user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error hard deleting user {user.username}: {e}")
            await db.rollback()
            raise Exception(f"Failed to delete user: {str(e)}")
    
    @staticmethod
    async def activate_user(db: AsyncSession, user: User) -> User:
        """
        Activate a user
        
        Args:
            db: Database session
            user: User to activate
            
        Returns:
            Updated User object
        """
        try:
            setattr(user, 'is_active', True)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Activated user: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Error activating user {user.username}: {e}")
            await db.rollback()
            raise Exception(f"Failed to activate user: {str(e)}")
    
    @staticmethod
    async def sync_with_supabase(
        db: AsyncSession,
        supabase_user_data: Dict[str, Any]
    ) -> User:
        """
        Sync user data with Supabase
        
        Args:
            db: Database session
            supabase_user_data: User data from Supabase
            
        Returns:
            User object
        """
        try:
            supabase_id = supabase_user_data.get("id")
            email = supabase_user_data.get("email", "")
            user_metadata = supabase_user_data.get("user_metadata", {})
            
            # Try to find existing user by supabase_id
            result = await db.execute(
                select(User).where(User.supabase_id == supabase_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Try to find by email
                result = await db.execute(
                    select(User).where(User.email == email)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    # Update existing user with supabase_id
                    setattr(user, 'supabase_id', supabase_id)
                else:
                    # Create new user
                    username_default = "unknown_user"
                    if email:
                        username_default = email.split("@")[0]
                    elif supabase_id:
                        username_default = f"user_{supabase_id[:8]}"
                    
                    user = User(
                        supabase_id=supabase_id,
                        email=email,
                        username=user_metadata.get("username", username_default),
                        full_name=user_metadata.get("full_name", ""),
                        is_active=True
                    )
                    db.add(user)
            
            # Update user data from Supabase
            if email and user.email != email:
                setattr(user, 'email', email)
            
            if user_metadata.get("full_name") and user.full_name != user_metadata["full_name"]:
                setattr(user, 'full_name', user_metadata["full_name"])
            
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Synced user with Supabase: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Error syncing user with Supabase: {e}")
            await db.rollback()
            raise Exception(f"Failed to sync user: {str(e)}")
