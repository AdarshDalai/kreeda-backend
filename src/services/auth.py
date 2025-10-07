from datetime import datetime, timedelta
from uuid import uuid4
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

class AuthService:
    @staticmethod
    async def register_user(request: UserRegisterRequest, db: AsyncSession) -> AuthResponse:
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
            is_email_verified=False,  # In real app, send verification email
        )
        db.add(user_auth)

        # Create UserProfile
        user_profile = UserProfile(
            user_id=user_id,
            name=None,  # Can be updated later
        )
        db.add(user_profile)
        await db.commit()

        # Create response mimicking Supabase
        user_response = UserResponse(
            id=user_id,
            app_metadata=UserMetadata(provider="email", providers=["email"]),
            user_metadata={},
            email=request.email,
            phone=request.phone_number or "",
            created_at=datetime.utcnow(),
            email_confirmed_at=None,  # Not verified yet
            identities=[
                UserIdentity(
                    id=str(user_id),
                    user_id=str(user_id),
                    identity_data={"email": request.email, "sub": str(user_id)},
                    provider="email",
                    created_at=datetime.utcnow(),
                    last_sign_in_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            ],
            updated_at=datetime.utcnow(),
        )

        access_token = create_access_token({"sub": str(user_id)})
        session_response = SessionResponse(
            access_token=access_token,
            refresh_token="refresh_token_placeholder",  # Implement refresh tokens later
            expires_in=3600,
            expires_at=int((datetime.utcnow().timestamp() + 3600)),
            user=user_response,
        )

        return AuthResponse(user=user_response, session=session_response)

    @staticmethod
    async def login_user(request: UserLoginRequest, db: AsyncSession) -> AuthResponse:
        # Find user
        result = await db.execute(select(UserAuth).where(UserAuth.email == request.email))
        user_auth = result.scalar_one_or_none()
        if not user_auth or not verify_password(request.password, user_auth.password_hash):
            raise ValueError("Invalid credentials")

        # Update last login
        user_auth.last_login = datetime.utcnow()
        await db.commit()

        # Create response
        user_response = UserResponse(
            id=user_auth.user_id,
            app_metadata=UserMetadata(provider="email", providers=["email"]),
            user_metadata={},
            email=user_auth.email,
            phone=user_auth.phone_number or "",
            created_at=user_auth.created_at,
            email_confirmed_at=user_auth.created_at if user_auth.is_email_verified else None,
            last_sign_in_at=user_auth.last_login,
            identities=[
                UserIdentity(
                    id=str(user_auth.user_id),
                    user_id=str(user_auth.user_id),
                    identity_data={"email": user_auth.email, "sub": str(user_auth.user_id)},
                    provider="email",
                    created_at=user_auth.created_at,
                    last_sign_in_at=user_auth.last_login or user_auth.created_at,
                    updated_at=user_auth.created_at,
                )
            ],
            updated_at=user_auth.created_at,
        )

        access_token = create_access_token({"sub": str(user_auth.user_id)})
        session_response = SessionResponse(
            access_token=access_token,
            refresh_token="refresh_token_placeholder",
            expires_in=3600,
            expires_at=int((datetime.utcnow().timestamp() + 3600)),
            user=user_response,
        )

        return AuthResponse(user=user_response, session=session_response)

    @staticmethod
    async def create_anonymous_user(request: UserAnonymousRequest, db: AsyncSession) -> AuthResponse:
        """Create anonymous user (no email/password required)"""
        user_id = uuid4()
        user_auth = UserAuth(
            user_id=user_id,
            email=f"anonymous_{user_id}@example.com",  # Placeholder email
            password_hash=hash_password("anonymous"),  # Placeholder password
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

        # Generate response similar to register
        user_response = UserResponse(
            id=user_id,
            app_metadata=UserMetadata(provider="anonymous", providers=["anonymous"]),
            user_metadata=request.options or {},
            email=f"anonymous_{user_id}@example.com",
            phone="",
            created_at=datetime.utcnow(),
            identities=[
                UserIdentity(
                    id=str(user_id),
                    user_id=str(user_id),
                    identity_data={"sub": str(user_id)},
                    provider="anonymous",
                    created_at=datetime.utcnow(),
                    last_sign_in_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            ],
            updated_at=datetime.utcnow(),
        )

        access_token = create_access_token({"sub": str(user_id)})
        session_response = SessionResponse(
            access_token=access_token,
            refresh_token="refresh_token_placeholder",
            expires_in=3600,
            expires_at=int((datetime.utcnow().timestamp() + 3600)),
            user=user_response,
        )

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
                password_hash=hash_password("otp_user"),  # Placeholder
                phone_number=request.phone,
                is_email_verified=request.type == "email",
                is_phone_verified=request.type == "sms",
                is_active=True,
            )
            db.add(user_auth)

            user_profile = UserProfile(user_id=user_id)
            db.add(user_profile)
            await db.commit()

        # Generate auth response
        user_response = UserResponse(
            id=user_auth.user_id,
            app_metadata=UserMetadata(provider="otp", providers=["otp"]),
            user_metadata={},
            email=user_auth.email,
            phone=user_auth.phone_number or "",
            created_at=user_auth.created_at,
            email_confirmed_at=user_auth.created_at if user_auth.is_email_verified else None,
            phone_confirmed_at=user_auth.created_at if user_auth.is_phone_verified else None,
            identities=[
                UserIdentity(
                    id=str(user_auth.user_id),
                    user_id=str(user_auth.user_id),
                    identity_data={"email": user_auth.email, "sub": str(user_auth.user_id)},
                    provider="otp",
                    created_at=user_auth.created_at,
                    last_sign_in_at=datetime.utcnow(),
                    updated_at=user_auth.created_at,
                )
            ],
            updated_at=user_auth.created_at,
        )

        access_token = create_access_token({"sub": str(user_auth.user_id)})
        session_response = SessionResponse(
            access_token=access_token,
            refresh_token="refresh_token_placeholder",
            expires_in=3600,
            expires_at=int((datetime.utcnow().timestamp() + 3600)),
            user=user_response,
        )

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

        user_response = UserResponse(
            id=user_auth.user_id,
            app_metadata=UserMetadata(provider="email", providers=["email"]),
            user_metadata={},
            email=user_auth.email,
            phone=user_auth.phone_number or "",
            created_at=user_auth.created_at,
            email_confirmed_at=user_auth.created_at if user_auth.is_email_verified else None,
            last_sign_in_at=user_auth.last_login,
            identities=[
                UserIdentity(
                    id=str(user_auth.user_id),
                    user_id=str(user_auth.user_id),
                    identity_data={"email": user_auth.email, "sub": str(user_auth.user_id)},
                    provider="email",
                    created_at=user_auth.created_at,
                    last_sign_in_at=user_auth.last_login or user_auth.created_at,
                    updated_at=user_auth.created_at,
                )
            ],
            updated_at=user_auth.created_at,
        )

        return user_response

    @staticmethod
    async def sign_out(user_id: str, db: AsyncSession) -> dict:
        """Sign out user"""
        # In production, invalidate refresh tokens
        print(f"User {user_id} signed out")
        return {"message": "Signed out successfully"}