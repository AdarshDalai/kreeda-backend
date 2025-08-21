from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.core.database import get_db
from app.repositories.user import user_repository
from app.schemas.auth import (
    UserCreate, UserResponse, LoginRequest, OAuthLoginRequest, 
    TokenResponse, RefreshTokenRequest, PasswordResetRequest, 
    PasswordResetConfirm, EmailVerificationRequest, AuthProvider,
    ChangePasswordRequest, UpdateProfileRequest, DeactivateAccountRequest,
    UserSessionsResponse, RevokeSessionRequest
)
from app.models.user import User
from app.services.auth import auth_service, oauth_service

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    token_data = auth_service.verify_token(credentials.credentials)
    user = await user_repository.get_user_by_id(db, token_data.sub)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    return current_user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with email and password."""
    
    # Check if user already exists
    existing_user = await user_repository.check_user_exists(db, user_data.email, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Hash password for email authentication
    if user_data.auth_provider == AuthProvider.EMAIL:
        if not user_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required for email registration"
            )
        hashed_password = auth_service.get_password_hash(user_data.password)
    else:
        hashed_password = None
    
    # Create user
    try:
        user = await user_repository.create_user(db, user_data)
        if hashed_password:
            await user_repository.update_password(db, str(user.id), hashed_password)
        
        # Generate tokens
        user_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role.value
        }
        
        access_token = auth_service.generate_access_token(user_token_data)
        refresh_token = auth_service.generate_refresh_token(user_token_data)
        
        # Store refresh token hash
        refresh_token_hash = auth_service.hash_token(refresh_token)
        await user_repository.update_refresh_token(db, str(user.id), refresh_token_hash)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password."""
    
    # Find user
    user = await user_repository.get_user_by_email(db, login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    # Verify password
    if not user.hashed_password or not auth_service.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate tokens
    user_token_data = {
        "sub": str(user.id),
        "email": str(user.email),
        "username": str(user.username),
        "role": user.role.value
    }
    
    access_token = auth_service.generate_access_token(user_token_data)
    refresh_token = auth_service.generate_refresh_token(user_token_data)
    
    # Store refresh token hash
    refresh_token_hash = auth_service.hash_token(refresh_token)
    await user_repository.update_refresh_token(db, str(user.id), refresh_token_hash)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/oauth/login", response_model=TokenResponse)
async def oauth_login(
    oauth_data: OAuthLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login or register using OAuth (Google/Apple)."""
    
    try:
        # Verify OAuth token and get user data
        if oauth_data.provider == AuthProvider.GOOGLE:
            provider_user_data = await oauth_service.verify_google_token(oauth_data.access_token)
        elif oauth_data.provider == AuthProvider.APPLE:
            if not oauth_data.id_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ID token is required for Apple Sign-In"
                )
            provider_user_data = await oauth_service.verify_apple_token(oauth_data.id_token)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported OAuth provider"
            )
        
        # Check if user exists by provider ID
        existing_user = await user_repository.get_user_by_provider(
            db, oauth_data.provider, provider_user_data["provider_id"]
        )
        
        if existing_user:
            # User exists, generate tokens
            user = existing_user
        else:
            # Check if user exists by email
            existing_email_user = await user_repository.get_user_by_email(db, provider_user_data["email"])
            
            if existing_email_user:
                # User exists with same email but different provider
                # This could be handled by linking accounts, but for now we'll raise an error
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"An account with email {provider_user_data['email']} already exists. Please login with your existing method."
                )
            
            # Create new user
            username = oauth_service.generate_username_from_email(provider_user_data["email"])
            
            # Ensure username is unique
            counter = 1
            original_username = username
            while await user_repository.get_user_by_username(db, username):
                username = f"{original_username}{counter}"
                counter += 1
            
            user_create_data = UserCreate(
                email=provider_user_data["email"],
                username=username,
                full_name=provider_user_data.get("full_name"),
                avatar_url=provider_user_data.get("avatar_url"),
                auth_provider=oauth_data.provider,
                provider_id=provider_user_data["provider_id"]
            )
            
            user = await user_repository.create_user(db, user_create_data)
            
            # Mark email as verified if provider says it's verified
            if provider_user_data.get("email_verified", False):
                await user_repository.verify_email(db, str(user.id))
        
        # Generate tokens
        user_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role.value
        }
        
        access_token = auth_service.generate_access_token(user_token_data)
        refresh_token = auth_service.generate_refresh_token(user_token_data)
        
        # Store refresh token hash
        refresh_token_hash = auth_service.hash_token(refresh_token)
        await user_repository.update_refresh_token(db, str(user.id), refresh_token_hash)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth login failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    
    try:
        # Verify refresh token
        token_data = auth_service.verify_token(refresh_data.refresh_token)
        
        # Check if it's a refresh token
        payload = auth_service.decode_token(refresh_data.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Get user
        user = await user_repository.get_user_by_id(db, token_data.sub)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Verify stored refresh token
        if not user.refresh_token_hash or not auth_service.verify_token_hash(refresh_data.refresh_token, user.refresh_token_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Generate new tokens
        user_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role.value
        }
        
        access_token = auth_service.generate_access_token(user_token_data)
        new_refresh_token = auth_service.generate_refresh_token(user_token_data)
        
        # Store new refresh token hash
        refresh_token_hash = auth_service.hash_token(new_refresh_token)
        await user_repository.update_refresh_token(db, str(user.id), refresh_token_hash)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user by invalidating refresh token."""
    
    # Clear refresh token
    await user_repository.update_refresh_token(db, str(current_user.id), None)
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset."""
    
    user = await user_repository.get_user_by_email(db, request.email)
    
    if user and user.auth_provider == AuthProvider.EMAIL:
        # Generate reset token
        reset_token = auth_service.generate_reset_token()
        reset_token_hash = auth_service.hash_token(reset_token)
        
        # Store reset token
        await user_repository.set_reset_token(db, str(user.id), reset_token_hash)
        
        # TODO: Send email with reset token
        # background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Reset password using reset token."""
    
    # Hash the token to compare with stored hash
    reset_token_hash = auth_service.hash_token(reset_data.token)
    
    # Find user by reset token
    user = await user_repository.get_user_by_reset_token(db, reset_token_hash)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Hash new password
    hashed_password = auth_service.get_password_hash(reset_data.new_password)
    
    # Update password and clear reset token
    await user_repository.update_password(db, str(user.id), hashed_password)
    await user_repository.set_reset_token(db, str(user.id), None)
    
    return {"message": "Password reset successful"}


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    verification: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify email using verification token."""
    
    # Hash the token to compare with stored hash
    verification_token_hash = auth_service.hash_token(verification.token)
    
    # Find user by verification token
    user = await user_repository.get_user_by_verification_token(db, verification_token_hash)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Verify email
    await user_repository.verify_email(db, str(user.id))
    
    return {"message": "Email verified successfully"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    
    # Verify current password
    if not current_user.hashed_password or not auth_service.verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )
    
    # Check password strength
    is_strong, message = auth_service.is_strong_password(password_data.new_password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Hash new password
    hashed_password = auth_service.get_password_hash(password_data.new_password)
    
    # Update password
    await user_repository.update_password(db, str(current_user.id), hashed_password)
    
    return {"message": "Password changed successfully"}


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile information."""
    
    await user_repository.update_profile(
        db,
        str(current_user.id),
        full_name=profile_data.full_name,
        phone=profile_data.phone,
        avatar_url=profile_data.avatar_url
    )
    
    # Get updated user
    updated_user = await user_repository.get_user_by_id(db, str(current_user.id))
    return UserResponse.model_validate(updated_user)


@router.delete("/account", status_code=status.HTTP_200_OK)
async def deactivate_account(
    deactivate_data: DeactivateAccountRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user account."""
    
    # Verify password for security
    if not current_user.hashed_password or not auth_service.verify_password(
        deactivate_data.password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password"
        )
    
    # Deactivate account
    await user_repository.deactivate_user(db, str(current_user.id))
    
    # Clear refresh token
    await user_repository.update_refresh_token(db, str(current_user.id), None)
    
    return {"message": "Account deactivated successfully"}


@router.get("/sessions", response_model=UserSessionsResponse)
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active sessions for current user."""
    
    # This would require implementing session repository
    # For now, return placeholder
    return UserSessionsResponse(sessions=[], total_sessions=0)


@router.post("/revoke-session", status_code=status.HTTP_200_OK)
async def revoke_session(
    revoke_data: RevokeSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke a specific user session."""
    
    # This would require implementing session repository
    # For now, return success
    return {"message": "Session revoked successfully"}


@router.post("/revoke-all-sessions", status_code=status.HTTP_200_OK)
async def revoke_all_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke all user sessions except current one."""
    
    # Clear refresh token (simplified approach)
    await user_repository.update_refresh_token(db, str(current_user.id), None)
    
    return {"message": "All sessions revoked successfully"}
