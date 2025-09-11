from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.config import settings
from app.utils.database import get_db
from app.models.user import User
from app.auth.supabase_auth import get_user_from_token

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# JWT Functions (for backwards compatibility)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"user_id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user - prioritizes Supabase token verification"""
    token = credentials.credentials
    
    try:
        # First try to verify as Supabase token
        try:
            supabase_user_data = get_user_from_token(token)
            supabase_id = supabase_user_data.get("id")
            
            if supabase_id:
                # Find user by supabase_id
                result = await db.execute(
                    select(User).where(User.supabase_id == supabase_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    # Create user if doesn't exist in local db
                    user = User(
                        supabase_id=supabase_id,
                        email=supabase_user_data.get("email", ""),
                        username=supabase_user_data.get("user_metadata", {}).get("username", 
                                                                                 supabase_user_data.get("email", "").split("@")[0]),
                        full_name=supabase_user_data.get("user_metadata", {}).get("full_name", "")
                    )
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)
                    logger.info(f"Created new user from Supabase token: {user.email}")
                
                return user
        
        except Exception as e:
            logger.debug(f"Supabase token verification failed, trying local JWT: {e}")
            
            # Fall back to local JWT verification
            try:
                payload = verify_token(token)
                user_id = payload.get("user_id")
                
                if user_id:
                    result = await db.execute(
                        select(User).where(User.id == user_id)
                    )
                    user = result.scalar_one_or_none()
                    
                    if not user:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found"
                        )
                    
                    return user
            except Exception as jwt_error:
                logger.debug(f"Local JWT verification also failed: {jwt_error}")
                pass  # Will raise the final exception below
        
        # If we get here, both token types failed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not getattr(current_user, 'is_active', True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
