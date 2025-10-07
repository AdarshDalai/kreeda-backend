from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from src.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, UserAnonymousRequest,
    UserOTPRequest, UserOTPVerifyRequest, UserUpdateRequest,
    PasswordResetRequest, RefreshTokenRequest,
    AuthResponse, UserResponse
)
from src.services.auth import AuthService
from src.database.connection import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

# Authentication endpoints
@router.post("/signup", response_model=AuthResponse, summary="Create a new user")
async def signup(request: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user account with email and password."""
    try:
        return await AuthService.register_user(request, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/register", response_model=AuthResponse, summary="Create a new user (alias)")
async def register(request: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Alias for signup endpoint."""
    try:
        return await AuthService.register_user(request, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/signin/password", response_model=AuthResponse, summary="Sign in with password")
async def signin_with_password(request: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    """Sign in with email and password."""
    try:
        return await AuthService.login_user(request, db)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/login", response_model=AuthResponse, summary="Sign in with password (alias)")
async def login(request: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    """Alias for signin with password endpoint."""
    try:
        return await AuthService.login_user(request, db)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/signin/anonymous", response_model=AuthResponse, summary="Create anonymous user")
async def signin_anonymous(request: UserAnonymousRequest, db: AsyncSession = Depends(get_db)):
    """Create an anonymous user session."""
    try:
        return await AuthService.create_anonymous_user(request, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/signin/otp", summary="Send OTP")
async def signin_with_otp(request: UserOTPRequest, db: AsyncSession = Depends(get_db)):
    """Send OTP to email or phone for passwordless sign-in."""
    try:
        return await AuthService.send_otp(request, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify", response_model=AuthResponse, summary="Verify OTP")
async def verify_otp(request: UserOTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and complete sign-in."""
    try:
        return await AuthService.verify_otp(request, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/signout", summary="Sign out")
async def signout(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    """Sign out the current user."""
    try:
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            user = await AuthService.get_user_from_token(token, db)
            return await AuthService.sign_out(str(user.id), db)
        else:
            return {"message": "No active session"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user", response_model=UserResponse, summary="Get current user")
async def get_user(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    """Get the current user's information."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        token = authorization.split(" ")[1]
        return await AuthService.get_user_from_token(token, db)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.put("/user", response_model=AuthResponse, summary="Update user")
async def update_user(
    request: UserUpdateRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Update the current user's information."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        token = authorization.split(" ")[1]
        user = await AuthService.get_user_from_token(token, db)
        # Note: This endpoint needs to be implemented in AuthService
        raise HTTPException(status_code=501, detail="Update user not yet implemented")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/recover", summary="Send password reset email")
async def recover_password(request: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """Send password reset email."""
    try:
        # Note: This endpoint needs to be implemented in AuthService
        raise HTTPException(status_code=501, detail="Password recovery not yet implemented")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/token", response_model=AuthResponse, summary="Refresh access token")
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    try:
        # Note: This endpoint needs to be implemented in AuthService
        raise HTTPException(status_code=501, detail="Token refresh not yet implemented")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))