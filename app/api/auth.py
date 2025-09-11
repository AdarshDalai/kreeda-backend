import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import supabase_auth
from app.auth.middleware import get_current_active_user
from app.config import settings
from app.models.user import User
from app.schemas.auth import (
    OAuthProvider,
    OTPVerification,
    PasswordResetRequest,
    RefreshTokenRequest,
    Token,
    UserLogin,
    UserRegister,
    UserUpdate,
)
from app.schemas.user import UserResponse
from app.utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def auth_health():
    """Health check for auth endpoints"""
    return {"success": True, "message": "Auth service is healthy"}


@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user with Supabase Auth"""
    try:
        # Check if username already exists in local database
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        # Create user in Supabase Auth
        user_metadata = {
            "username": user_data.username,
            "full_name": user_data.full_name,
        }

        auth_response = supabase_auth.sign_up_with_email_password(
            email=user_data.email,
            password=user_data.password,
            user_metadata=user_metadata,
        )

        # Check if Supabase sign up was successful
        if not auth_response.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {auth_response.get('error', 'Unknown error')}",
            )

        # Create user in local database with Supabase ID
        supabase_user = auth_response["user"]
        new_user = User(
            supabase_id=supabase_user["id"],
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"User registered successfully: {user_data.email}")

        # Return token from Supabase
        session_data = auth_response.get("session")
        if session_data:
            return Token(
                access_token=session_data["access_token"],
                token_type="bearer",
                expires_in=3600,  # 1 hour default
                refresh_token=session_data["refresh_token"],
            )
        else:
            # If no session (email confirmation required), return a message
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Registration successful. Please check your email to confirm your account.",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user with Supabase Auth"""
    try:
        # Authenticate with Supabase
        auth_response = supabase_auth.sign_in_with_email_password(
            email=user_credentials.email, password=user_credentials.password
        )

        # Get or create user in local database
        supabase_user = auth_response["user"]
        result = await db.execute(
            select(User).where(User.supabase_id == supabase_user["id"])
        )
        user = result.scalar_one_or_none()

        if not user:
            # Create user if doesn't exist in local db
            user = User(
                supabase_id=supabase_user["id"],
                email=supabase_user["email"],
                username=supabase_user.get("user_metadata", {}).get(
                    "username", supabase_user["email"].split("@")[0]
                ),
                full_name=supabase_user.get("user_metadata", {}).get("full_name", ""),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        session_data = auth_response["session"]

        logger.info(f"User logged in successfully: {user_credentials.email}")
        return Token(
            access_token=session_data["access_token"],
            token_type=session_data["token_type"],
            expires_in=3600,  # 1 hour default
            refresh_token=session_data["refresh_token"],
        )

    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )


@router.post("/oauth/{provider}")
async def oauth_login(provider: str, oauth_data: OAuthProvider):
    """Initiate OAuth login with provider"""
    try:
        response = supabase_auth.sign_in_with_oauth(
            provider=provider, redirect_to=oauth_data.redirect_to
        )

        return {"auth_url": response["url"]}

    except Exception as e:
        logger.error(f"OAuth login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth login failed: {str(e)}",
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        auth_response = supabase_auth.refresh_session(refresh_data.refresh_token)

        if not auth_response.get("success"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        session_data = auth_response["session"]
        return Token(
            access_token=session_data["access_token"],
            token_type="bearer",
            expires_in=3600,
            refresh_token=session_data["refresh_token"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.post("/dev-confirm-user")
async def dev_confirm_user(email_data: dict):
    """Development endpoint to confirm a user's email (bypasses email confirmation)"""
    try:
        from app.config import settings

        if settings.environment not in ["development", "testing"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This endpoint is only available in development mode",
            )

        email = email_data.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required"
            )

        # Use admin client to confirm the user
        admin_client = supabase_auth.get_admin_supabase_client()

        # List users to find the one with this email
        users_response = admin_client.auth.admin.list_users()  # type: ignore
        users = (
            users_response
            if isinstance(users_response, list)
            else getattr(users_response, "data", [])
        )

        target_user = None
        for user in users:
            if hasattr(user, "email") and user.email == email:
                target_user = user
                break

        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Confirm the user
        confirm_response = admin_client.auth.admin.update_user_by_id(
            target_user.id, {"email_confirm": True}
        )  # type: ignore

        logger.info(f"Manually confirmed user for development: {email}")

        return {
            "success": True,
            "message": f"User {email} has been confirmed. You can now log in.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dev confirm user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Confirmation failed: {str(e)}",
        )


@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_active_user)):
    """Logout user"""
    try:
        # Sign out from Supabase (token would need to be passed in real implementation)
        supabase_auth.sign_out("")

        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return {"message": "Logged out successfully"}  # Always return success


@router.post("/reset-password")
async def reset_password(reset_data: PasswordResetRequest):
    """Send password reset email"""
    try:
        response = supabase_auth.reset_password_email(
            email=reset_data.email, redirect_to=reset_data.redirect_to
        )

        return {"message": "Password reset email sent"}

    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send password reset email",
        )


@router.post("/verify-otp", response_model=Token)
async def verify_otp(otp_data: OTPVerification, db: AsyncSession = Depends(get_db)):
    """Verify OTP token"""
    try:
        auth_response = supabase_auth.verify_otp(
            email=otp_data.email, token=otp_data.token, type_=otp_data.type
        )

        # Ensure user exists in local database
        supabase_user = auth_response["user"]
        result = await db.execute(
            select(User).where(User.supabase_id == supabase_user["id"])
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                supabase_id=supabase_user["id"],
                email=supabase_user["email"],
                username=supabase_user.get("user_metadata", {}).get(
                    "username", supabase_user["email"].split("@")[0]
                ),
                full_name=supabase_user.get("user_metadata", {}).get("full_name", ""),
            )
            db.add(user)
            await db.commit()

        session_data = auth_response["session"]

        return Token(
            access_token=session_data["access_token"],
            token_type=session_data["token_type"],
            expires_in=3600,
            refresh_token=session_data["refresh_token"],
        )

    except Exception as e:
        logger.error(f"OTP verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """Get current authenticated user"""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile"""
    try:
        # Prepare update data for Supabase
        supabase_updates = {}

        if user_update.email:
            supabase_updates["email"] = user_update.email
        if user_update.password:
            supabase_updates["password"] = user_update.password
        if user_update.phone:
            supabase_updates["phone"] = user_update.phone
        if user_update.data:
            supabase_updates["data"] = user_update.data

        # Update in Supabase if there are updates
        if supabase_updates:
            # This would need the access token - implement token passing
            supabase_auth.update_user("", supabase_updates)

        # Update local database
        if user_update.email:
            setattr(current_user, "email", str(user_update.email))

        if user_update.data:
            for key, value in user_update.data.items():
                if key == "username" and value:
                    setattr(current_user, "username", str(value))
                elif key == "full_name" and value:
                    setattr(current_user, "full_name", str(value))

        await db.commit()
        await db.refresh(current_user)

        return current_user

    except Exception as e:
        logger.error(f"User update failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user profile",
        )
