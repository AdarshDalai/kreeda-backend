"""
Authentication API Routes
JWT-based authentication for secure access
"""
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.schemas.auth import UserResponse, UserCreate, Token, UserLogin
from app.core.config import settings
from app.core.auth import (
    get_current_user, authenticate_user, register_user,
    create_access_token, get_current_active_user
)

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        user = register_user(user_data)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login user and return access token"""
    try:
        user = authenticate_user(login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "email": user.email, "full_name": user.full_name},
            expires_delta=access_token_expires
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.post("/verify-token")
async def verify_token(request: Request):
    """Verify JWT token validity"""
    try:
        auth_header = request.headers.get('authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        token = auth_header.split(' ')[1]
        # Create a mock credentials object for validation
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        user = await get_current_user(credentials)  # This will validate the token
        return {"valid": True, "user": user}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


@router.get("/config")
async def get_auth_config():
    """Get authentication configuration for frontend"""
    return {
        "auth_type": "jwt",
        "token_expiry_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "algorithm": settings.ALGORITHM,
        "token_url": "/api/auth/login",
        "user_info_url": "/api/auth/me",
        "client_id": "kreeda-backend",
        "endpoints": {
            "register": "/api/auth/register",
            "login": "/api/auth/login",
            "me": "/api/auth/me",
            "verify_token": "/api/auth/verify-token"
        }
    }
