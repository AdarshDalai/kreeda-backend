from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, and_, or_, update, func, text, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from datetime import datetime, timedelta
import math

from app.models.user import User, AuthProvider, UserRole
from app.schemas.auth import UserCreate
from app.schemas.users import UserSearchFilters, UserBulkAction


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
    
    # Advanced user management methods
    
    async def search_users(
        self, 
        db: AsyncSession,
        filters: UserSearchFilters,
        page: int = 1,
        size: int = 20,
        order_by: str = "created_at",
        order_dir: str = "desc"
    ) -> Tuple[List[User], int]:
        """Search users with filters and pagination."""
        query = select(User)
        count_query = select(func.count(User.id))
        
        # Build where conditions
        conditions = []
        
        if filters.query:
            search_term = f"%{filters.query.lower()}%"
            conditions.append(
                or_(
                    func.lower(User.username).like(search_term),
                    func.lower(User.full_name).like(search_term),
                    func.lower(User.email).like(search_term)
                )
            )
        
        if filters.role is not None:
            conditions.append(User.role == filters.role)
            
        if filters.is_active is not None:
            conditions.append(User.is_active == filters.is_active)
            
        if filters.email_verified is not None:
            conditions.append(User.email_verified == filters.email_verified)
            
        if filters.auth_provider is not None:
            conditions.append(User.auth_provider == filters.auth_provider)
            
        if filters.created_after:
            conditions.append(User.created_at >= filters.created_after)
            
        if filters.created_before:
            conditions.append(User.created_at <= filters.created_before)
            
        if filters.last_login_after:
            conditions.append(User.last_login >= filters.last_login_after)
            
        if filters.last_login_before:
            conditions.append(User.last_login <= filters.last_login_before)
        
        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Apply ordering
        order_column = getattr(User, order_by, User.created_at)
        if order_dir.lower() == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        # Execute queries
        users_result = await db.execute(query)
        count_result = await db.execute(count_query)
        
        users = list(users_result.scalars().all())
        total = count_result.scalar() or 0
        
        return users, total
    
    async def get_users_by_ids(self, db: AsyncSession, user_ids: List[str]) -> List[User]:
        """Get multiple users by their IDs."""
        user_uuids = [UUID(uid) for uid in user_ids]
        result = await db.execute(
            select(User).where(User.id.in_(user_uuids))
        )
        return list(result.scalars().all())
    
    async def get_user_stats(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """Get user statistics (placeholder for now)."""
        # This would integrate with teams, tournaments, matches tables
        # For now, return basic stats
        user_uuid = UUID(user_id)
        
        # Get user
        user_result = await db.execute(select(User).where(User.id == user_uuid))
        user = user_result.scalar_one_or_none()
        
        if not user:
            return {}
        
        return {
            "teams_count": 0,  # TODO: Count from teams table
            "tournaments_count": 0,  # TODO: Count from tournaments table
            "matches_played": 0,  # TODO: Count from matches table
            "matches_won": 0,  # TODO: Count wins from matches table
            "total_score": 0,  # TODO: Sum from scores table
            "win_rate": 0.0,  # TODO: Calculate from matches
            "last_activity": user.last_login,
            "account_age_days": (datetime.utcnow() - user.created_at).days
        }
    
    async def update_last_login(self, db: AsyncSession, user_id: str) -> None:
        """Update user's last login timestamp."""
        user_uuid = UUID(user_id)
        await db.execute(
            update(User)
            .where(User.id == user_uuid)
            .values(last_login=datetime.utcnow())
        )
        await db.commit()
    
    async def increment_failed_attempts(self, db: AsyncSession, user_id: str) -> None:
        """Increment failed login attempts and potentially lock account."""
        user_uuid = UUID(user_id)
        
        # Get current attempts
        result = await db.execute(
            select(User.failed_login_attempts).where(User.id == user_uuid)
        )
        current_attempts = result.scalar_one_or_none() or 0
        new_attempts = current_attempts + 1
        
        # Lock account if too many attempts
        update_data: Dict[str, Any] = {"failed_login_attempts": new_attempts}
        if new_attempts >= 5:  # Lock after 5 failed attempts
            update_data["locked_until"] = datetime.utcnow() + timedelta(minutes=30)
        
        await db.execute(
            update(User)
            .where(User.id == user_uuid)
            .values(**update_data)
        )
        await db.commit()
    
    async def reset_failed_attempts(self, db: AsyncSession, user_id: str) -> None:
        """Reset failed login attempts and unlock account."""
        user_uuid = UUID(user_id)
        await db.execute(
            update(User)
            .where(User.id == user_uuid)
            .values(failed_login_attempts=0, locked_until=None)
        )
        await db.commit()
    
    async def bulk_action_users(
        self, 
        db: AsyncSession, 
        user_ids: List[str], 
        action: UserBulkAction
    ) -> Dict[str, Any]:
        """Perform bulk action on multiple users."""
        user_uuids = [UUID(uid) for uid in user_ids]
        success_count = 0
        failed_users = []
        
        try:
            if action == UserBulkAction.ACTIVATE:
                result = await db.execute(
                    update(User)
                    .where(User.id.in_(user_uuids))
                    .values(is_active=True)
                )
                success_count = result.rowcount
                
            elif action == UserBulkAction.DEACTIVATE:
                result = await db.execute(
                    update(User)
                    .where(User.id.in_(user_uuids))
                    .values(is_active=False)
                )
                success_count = result.rowcount
                
            elif action == UserBulkAction.VERIFY_EMAIL:
                result = await db.execute(
                    update(User)
                    .where(User.id.in_(user_uuids))
                    .values(email_verified=True)
                )
                success_count = result.rowcount
                
            elif action == UserBulkAction.RESET_FAILED_ATTEMPTS:
                result = await db.execute(
                    update(User)
                    .where(User.id.in_(user_uuids))
                    .values(failed_login_attempts=0, locked_until=None)
                )
                success_count = result.rowcount
                
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            failed_users = [{"user_id": uid, "error": str(e)} for uid in user_ids]
        
        return {
            "success_count": success_count,
            "failed_count": len(failed_users),
            "failed_users": failed_users
        }
    
    async def admin_update_user(
        self, 
        db: AsyncSession, 
        user_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[User]:
        """Admin-level user update with more permissions."""
        user_uuid = UUID(user_id)
        
        # Remove None values
        clean_data = {k: v for k, v in update_data.items() if v is not None}
        
        if clean_data:
            await db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(**clean_data)
            )
            await db.commit()
        
        # Return updated user
        return await self.get_user_by_id(db, user_id)
    
    async def get_user_activity_summary(
        self, 
        db: AsyncSession, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user activity summary for the last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # New users in period
        new_users_result = await db.execute(
            select(func.count(User.id))
            .where(User.created_at >= cutoff_date)
        )
        new_users = new_users_result.scalar()
        
        # Active users (logged in during period)
        active_users_result = await db.execute(
            select(func.count(User.id))
            .where(User.last_login >= cutoff_date)
        )
        active_users = active_users_result.scalar()
        
        # Total users
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        # Locked users
        locked_users_result = await db.execute(
            select(func.count(User.id))
            .where(User.locked_until > datetime.utcnow())
        )
        locked_users = locked_users_result.scalar()
        
        return {
            "total_users": total_users,
            "new_users_last_{}_days".format(days): new_users,
            "active_users_last_{}_days".format(days): active_users,
            "locked_users": locked_users,
            "period_days": days
        }


# Singleton instance
user_repository = UserRepository()
