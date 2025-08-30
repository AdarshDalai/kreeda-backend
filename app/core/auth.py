"""
Authentication and Authorization System
JWT-based authentication for secure access - DynamoDB Version
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.schemas.auth import UserResponse, UserCreate
from app.services.dynamodb_cricket_scoring import DynamoDBService


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer(auto_error=False)  # Don't auto-raise errors

# Global DynamoDB service instance
db_service = DynamoDBService()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plaintext password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserResponse:
    """Get current authenticated user from JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    try:
        payload = verify_token(token)
    except HTTPException:
        raise

    if payload is None:
        raise credentials_exception

    username: Optional[str] = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"],
        created_at=user["created_at"]
    )


def get_current_active_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Get current active user (not disabled)"""
    # For now, assume all users are active
    # In the future, we can add an is_active field to the user schema
    return current_user


def authenticate_user(username: str, password: str) -> Optional[UserResponse]:
    """Authenticate user with username and password"""
    user = db_service.get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"],
        created_at=user["created_at"]
    )


def register_user(user_data: UserCreate) -> UserResponse:
    """Register a new user"""
    # Check if user already exists
    existing_user = db_service.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Hash the password
    hashed_password = get_password_hash(user_data.password)

    # Create user in database (modify user_data to include hashed password)
    user_with_hashed_password = UserCreate(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        password=hashed_password  # Use hashed password
    )

    user_record = db_service.create_user(user_with_hashed_password)

    return UserResponse(
        id=user_record["id"],
        username=user_record["username"],
        email=user_record["email"],
        full_name=user_record["full_name"],
        created_at=user_record["created_at"]
    )
