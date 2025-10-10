from datetime import datetime, timedelta
from uuid import uuid4
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.models.user_auth import UserAuth
from src.models.user_profile import UserProfile
from src.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, UserAnonymousRequest, 
    UserOTPRequest, UserOTPVerifyRequest, UserUpdateRequest,
    PasswordResetRequest, RefreshTokenRequest,
    AuthResponse, UserResponse, SessionResponse, UserIdentity, UserMetadata
)
from src.core.security import hash_password, verify_password, create_access_token, decode_access_token
from src.database.connection import get_db
from src.utils.validators import PasswordValidator
from src.utils.logger import logger
from src.utils.email import EmailService

class AuthService:
    @staticmethod
    def _build_user_response(user_auth: UserAuth, provider: str = "email") -> UserResponse:
        """Helper method to build UserResponse from UserAuth model"""
        return UserResponse(
            id=user_auth.user_id,
            app_metadata=UserMetadata(provider=provider, providers=[provider]),
            user_metadata={},
            email=user_auth.email,
            phone=user_auth.phone_number or "",
            created_at=user_auth.created_at,
            email_confirmed_at=user_auth.created_at if user_auth.is_email_verified else None,
            phone_confirmed_at=user_auth.created_at if user_auth.is_phone_verified else None,
            last_sign_in_at=user_auth.last_login or user_auth.created_at,
            identities=[
                UserIdentity(
                    id=str(user_auth.user_id),
                    user_id=str(user_auth.user_id),
                    identity_data={"email": user_auth.email, "sub": str(user_auth.user_id)},
                    provider=provider,
                    created_at=user_auth.created_at,
                    last_sign_in_at=user_auth.last_login or user_auth.created_at,
                    updated_at=user_auth.created_at,
                )
            ],
            updated_at=user_auth.created_at,
        )
    
    @staticmethod
    def _create_session(user_response: UserResponse, include_refresh: bool = True) -> SessionResponse:
        """Helper method to create session response with tokens"""
        access_token = create_access_token({"sub": str(user_response.id)})
        refresh_token = create_access_token(
            {"sub": str(user_response.id), "type": "refresh"},
            expires_delta=timedelta(days=30)
        ) if include_refresh else "refresh_token_placeholder"
        
        return SessionResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
            expires_at=int(datetime.utcnow().timestamp() + 3600),
            user=user_response,
        )

    @staticmethod
    async def register_user(request: UserRegisterRequest, db: AsyncSession) -> AuthResponse:
        # Validate password strength
        is_valid, errors = PasswordValidator.validate_password(request.password)
        if not is_valid:
            raise ValueError("; ".join(errors))
        
        # Check if email exists
        result = await db.execute(select(UserAuth).where(UserAuth.email == request.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ValueError("Email already registered")

        # Create UserAuth
        user_id = uuid4()
        hashed_password = hash_password(request.password)
        user_auth = UserAuth(
            user_id=user_id,
            email=request.email,
            password_hash=hashed_password,
            phone_number=request.phone_number,
            is_email_verified=False,  # Will be verified later
        )
        db.add(user_auth)

        # Create UserProfile
        user_profile = UserProfile(
            user_id=user_id,
            name=None,  # Can be updated later
        )
        db.add(user_profile)
        await db.commit()
        await db.refresh(user_auth)

        logger.info(f"New user registered: {request.email}")

        # Send verification email
        verification_token = EmailService.generate_verification_token(str(user_id))
        await EmailService.send_verification_email(request.email, verification_token)

        # Create response using helper
        user_response = AuthService._build_user_response(user_auth, "email")
        session_response = AuthService._create_session(user_response, include_refresh=True)

        return AuthResponse(user=user_response, session=session_response)

        return AuthResponse(user=user_response, session=session_response)

    @staticmethod
    async def login_user(request: UserLoginRequest, db: AsyncSession) -> AuthResponse:
        # Find user
        result = await db.execute(select(UserAuth).where(UserAuth.email == request.email))
        user_auth = result.scalar_one_or_none()
        if not user_auth:
            raise ValueError("Invalid credentials")
        
        # Verify password
        if not verify_password(request.password, user_auth.password_hash):
            raise ValueError("Invalid credentials")

        # Update last login
        now = datetime.utcnow()
        await db.execute(
            update(UserAuth)
            .where(UserAuth.user_id == user_auth.user_id)
            .values(last_login=now)
        )
        await db.commit()
        await db.refresh(user_auth)

        # Create response using helper
        user_response = AuthService._build_user_response(user_auth, "email")
        session_response = AuthService._create_session(user_response, include_refresh=True)

        return AuthResponse(user=user_response, session=session_response)

    @staticmethod
    async def create_anonymous_user(request: UserAnonymousRequest, db: AsyncSession) -> AuthResponse:
        """Create anonymous user (no email/password required)"""
        user_id = uuid4()
        user_auth = UserAuth(
            user_id=user_id,
            email=f"anonymous_{user_id}@example.com",
            password_hash=hash_password("anonymous"),
            is_email_verified=False,
            is_active=True,
        )
        db.add(user_auth)

        # Create UserProfile
        user_profile = UserProfile(
            user_id=user_id,
            name="Anonymous User",
        )
        db.add(user_profile)
        await db.commit()
        await db.refresh(user_auth)

        # Create response using helper
        user_response = AuthService._build_user_response(user_auth, "anonymous")
        user_response.user_metadata = request.options or {}
        session_response = AuthService._create_session(user_response, include_refresh=True)

        return AuthResponse(user=user_response, session=session_response)

    @staticmethod
    async def send_otp(request: UserOTPRequest, db: AsyncSession) -> dict:
        """Send OTP via email or SMS"""
        if not request.email and not request.phone:
            raise ValueError("Either email or phone must be provided")

        # In a real implementation, you would send actual OTP
        # For now, we'll simulate sending and return success
        otp_code = "123456"  # In production, generate random OTP
        
        if request.email:
            # Simulate sending email OTP
            print(f"Sending OTP {otp_code} to email: {request.email}")
        elif request.phone:
            # Simulate sending SMS OTP
            print(f"Sending OTP {otp_code} to phone: {request.phone}")

        return {"message": "OTP sent successfully"}

    @staticmethod
    async def verify_otp(request: UserOTPVerifyRequest, db: AsyncSession) -> AuthResponse:
        """Verify OTP and log in user"""
        # For demo purposes, accept any 6-digit token
        if len(request.token) != 6 or not request.token.isdigit():
            raise ValueError("Invalid OTP token")

        # Find or create user based on email/phone
        user_auth = None
        if request.email:
            result = await db.execute(select(UserAuth).where(UserAuth.email == request.email))
            user_auth = result.scalar_one_or_none()
        elif request.phone:
            result = await db.execute(select(UserAuth).where(UserAuth.phone_number == request.phone))
            user_auth = result.scalar_one_or_none()

        if not user_auth:
            # Create new user if doesn't exist
            user_id = uuid4()
            user_auth = UserAuth(
                user_id=user_id,
                email=request.email or f"phone_{request.phone}@example.com",
                password_hash=hash_password("otp_user"),
                phone_number=request.phone,
                is_email_verified=request.type == "email",
                is_phone_verified=request.type == "sms",
                is_active=True,
            )
            db.add(user_auth)

            user_profile = UserProfile(user_id=user_id)
            db.add(user_profile)
            await db.commit()
            await db.refresh(user_auth)

        # Create response using helper
        user_response = AuthService._build_user_response(user_auth, "otp")
        session_response = AuthService._create_session(user_response, include_refresh=True)

        return AuthResponse(user=user_response, session=session_response)

    @staticmethod
    async def get_user_from_token(token: str, db: AsyncSession) -> UserResponse:
        """Get user from access token"""
        payload = decode_access_token(token)
        if not payload:
            raise ValueError("Invalid token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
            
        return await AuthService.get_user(user_id, db)

    @staticmethod
    async def get_user(user_id: str, db: AsyncSession) -> UserResponse:
        """Get user by ID"""
        result = await db.execute(select(UserAuth).where(UserAuth.user_id == user_id))
        user_auth = result.scalar_one_or_none()
        
        if not user_auth:
            raise ValueError("User not found")

        return AuthService._build_user_response(user_auth, "email")

    @staticmethod
    async def update_user(user_id: str, request: UserUpdateRequest, db: AsyncSession) -> AuthResponse:
        """Update user information"""
        result = await db.execute(select(UserAuth).where(UserAuth.user_id == user_id))
        user_auth = result.scalar_one_or_none()
        
        if not user_auth:
            raise ValueError("User not found")

        # Update fields if provided
        update_data = {}
        if request.email:
            # Check if email already exists
            check_result = await db.execute(
                select(UserAuth).where(UserAuth.email == request.email, UserAuth.user_id != user_id)
            )
            if check_result.scalar_one_or_none():
                raise ValueError("Email already in use")
            update_data['email'] = request.email
            update_data['is_email_verified'] = False  # Require re-verification
        
        if request.password:
            update_data['password_hash'] = hash_password(request.password)
        
        if request.phone is not None:
            update_data['phone_number'] = request.phone
            if request.phone:
                update_data['is_phone_verified'] = False  # Require re-verification

        if update_data:
            await db.execute(
                update(UserAuth)
                .where(UserAuth.user_id == user_id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(user_auth)

        # Create response
        user_response = AuthService._build_user_response(user_auth, "email")
        if request.data:
            user_response.user_metadata = request.data
        session_response = AuthService._create_session(user_response, include_refresh=True)

        return AuthResponse(user=user_response, session=session_response)

    @staticmethod
    async def refresh_access_token(refresh_token: str, db: AsyncSession) -> AuthResponse:
        """Refresh access token using refresh token"""
        payload = decode_access_token(refresh_token)
        if not payload:
            raise ValueError("Invalid refresh token")
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise ValueError("Token is not a refresh token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
        
        # Get user
        result = await db.execute(select(UserAuth).where(UserAuth.user_id == user_id))
        user_auth = result.scalar_one_or_none()
        
        if not user_auth or not user_auth.is_active:
            raise ValueError("User not found or inactive")

        # Create new tokens
        user_response = AuthService._build_user_response(user_auth, "email")
        session_response = AuthService._create_session(user_response, include_refresh=True)

        return AuthResponse(user=user_response, session=session_response)

    @staticmethod
    async def request_password_reset(email: str, db: AsyncSession) -> dict:
        """Send password reset email"""
        result = await db.execute(select(UserAuth).where(UserAuth.email == email))
        user_auth = result.scalar_one_or_none()
        
        # Always return success to prevent email enumeration
        if user_auth:
            # In production, generate reset token and send email
            reset_token = create_access_token(
                {"sub": str(user_auth.user_id), "type": "password_reset"},
                expires_delta=timedelta(hours=1)
            )
            # TODO: Send email with reset link containing token
            print(f"Password reset token for {email}: {reset_token}")
        
        return {"message": "If the email exists, a password reset link has been sent"}

    @staticmethod
    async def reset_password(token: str, new_password: str, db: AsyncSession) -> dict:
        """Reset password using reset token"""
        payload = decode_access_token(token)
        if not payload or payload.get("type") != "password_reset":
            raise ValueError("Invalid or expired reset token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
        
        # Update password
        hashed_password = hash_password(new_password)
        await db.execute(
            update(UserAuth)
            .where(UserAuth.user_id == user_id)
            .values(password_hash=hashed_password)
        )
        await db.commit()
        
        return {"message": "Password reset successfully"}

    @staticmethod
    async def verify_email(token: str, db: AsyncSession) -> dict:
        """Verify user email with token"""
        payload = decode_access_token(token)
        if not payload or payload.get("type") != "email_verification":
            raise ValueError("Invalid or expired verification token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
        
        # Mark email as verified
        result = await db.execute(select(UserAuth).where(UserAuth.user_id == user_id))
        user_auth = result.scalar_one_or_none()
        
        if not user_auth:
            raise ValueError("User not found")
        
        if user_auth.is_email_verified:
            return {"message": "Email already verified"}
        
        await db.execute(
            update(UserAuth)
            .where(UserAuth.user_id == user_id)
            .values(is_email_verified=True)
        )
        await db.commit()
        
        logger.info(f"Email verified for user: {user_auth.email}")
        
        return {"message": "Email verified successfully"}
    
    @staticmethod
    async def resend_verification_email(email: str, db: AsyncSession) -> dict:
        """Resend verification email"""
        result = await db.execute(select(UserAuth).where(UserAuth.email == email))
        user_auth = result.scalar_one_or_none()
        
        if not user_auth:
            # Don't reveal if email exists
            return {"message": "If the email exists, a verification link has been sent"}
        
        if user_auth.is_email_verified:
            raise ValueError("Email is already verified")
        
        # Send verification email
        verification_token = EmailService.generate_verification_token(str(user_auth.user_id))
        await EmailService.send_verification_email(email, verification_token)
        
        return {"message": "Verification email sent"}

    @staticmethod
    async def sign_out(user_id: str, db: AsyncSession) -> dict:
        """Sign out user"""
        # In production, invalidate refresh tokens in Redis
        print(f"User {user_id} signed out")
        return {"message": "Signed out successfully"}
