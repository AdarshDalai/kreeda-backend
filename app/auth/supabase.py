import logging
from typing import Any, Dict, Optional

from supabase.client import Client, create_client
from supabase.lib.client_options import ClientOptions

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Optional[Client] = None
admin_supabase: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """Get Supabase client instance with anon key"""
    global supabase
    if supabase is None:
        if not settings.supabase_url or not settings.supabase_anon_key:
            logger.warning("Supabase credentials not configured")
            return None

        try:
            supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
            logger.info("Supabase client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return None

    return supabase


def get_supabase_admin_client() -> Optional[Client]:
    """Get Supabase admin client instance with service role key"""
    global admin_supabase
    if admin_supabase is None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            logger.warning("Supabase admin credentials not configured")
            return None

        try:
            admin_supabase = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key,
                options=ClientOptions(auto_refresh_token=False, persist_session=False),
            )
            logger.info("Supabase admin client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase admin client: {e}")
            return None

    return admin_supabase


# Auth Functions
async def sign_up_with_email_password(
    email: str, password: str, user_metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """Sign up a new user with email and password"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")

        # Prepare sign up credentials
        credentials = {"email": email, "password": password}
        if user_metadata:
            credentials["options"] = {"data": user_metadata}

        response = client.auth.sign_up(credentials)

        if response.user:
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed_at": response.user.email_confirmed_at,
                    "user_metadata": response.user.user_metadata,
                    "created_at": response.user.created_at,
                },
                "session": (
                    {
                        "access_token": (
                            response.session.access_token if response.session else None
                        ),
                        "refresh_token": (
                            response.session.refresh_token if response.session else None
                        ),
                        "expires_at": (
                            response.session.expires_at if response.session else None
                        ),
                    }
                    if response.session
                    else None
                ),
            }
        else:
            raise Exception("User creation failed")

    except Exception as e:
        logger.error(f"Sign up failed: {e}")
        raise


async def sign_in_with_email_password(email: str, password: str) -> Dict[str, Any]:
    """Sign in user with email and password"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")

        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        if response.user and response.session:
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed_at": response.user.email_confirmed_at,
                    "user_metadata": response.user.user_metadata,
                    "last_sign_in_at": response.user.last_sign_in_at,
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at,
                    "token_type": response.session.token_type,
                },
            }
        else:
            raise Exception("Authentication failed")

    except Exception as e:
        logger.error(f"Sign in failed: {e}")
        raise


async def sign_in_with_oauth(
    provider: str, redirect_to: Optional[str] = None
) -> Dict[str, Any]:
    """Sign in with OAuth provider (Google, GitHub, etc.)"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")

        # Prepare OAuth credentials
        credentials = {"provider": provider}
        if redirect_to:
            credentials["options"] = {"redirect_to": redirect_to}

        response = client.auth.sign_in_with_oauth(credentials)

        return {"url": response.url if hasattr(response, "url") else ""}

    except Exception as e:
        logger.error(f"OAuth sign in failed: {e}")
        raise


async def refresh_session(refresh_token: str) -> Dict[str, Any]:
    """Refresh user session"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")

        response = client.auth.refresh_session(refresh_token)

        if response.user and response.session:
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed_at": response.user.email_confirmed_at,
                    "user_metadata": response.user.user_metadata,
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at,
                    "token_type": response.session.token_type,
                },
            }
        else:
            raise Exception("Token refresh failed")

    except Exception as e:
        logger.error(f"Session refresh failed: {e}")
        raise


async def sign_out(access_token: str) -> Dict[str, Any]:
    """Sign out user"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")

        # Set the session token for the client
        try:
            client.auth.set_session(access_token, "")
            client.auth.sign_out()
        except:
            # If setting session fails, still return success as the client-side token should be cleared
            pass

        return {"message": "Successfully signed out"}

    except Exception as e:
        logger.error(f"Sign out failed: {e}")
        raise


async def get_user_from_token(access_token: str) -> Dict[str, Any]:
    """Get user details from access token"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")

        response = client.auth.get_user(access_token)

        if response and response.user:
            return {
                "id": response.user.id,
                "email": response.user.email,
                "email_confirmed_at": response.user.email_confirmed_at,
                "phone": getattr(response.user, "phone", None),
                "phone_confirmed_at": getattr(
                    response.user, "phone_confirmed_at", None
                ),
                "user_metadata": response.user.user_metadata,
                "app_metadata": getattr(response.user, "app_metadata", {}),
                "created_at": response.user.created_at,
                "updated_at": getattr(response.user, "updated_at", None),
                "last_sign_in_at": getattr(response.user, "last_sign_in_at", None),
            }
        else:
            raise Exception("User not found")

    except Exception as e:
        logger.error(f"Get user failed: {e}")
        raise


async def update_user(
    access_token: str, user_attributes: Dict[str, Any]
) -> Dict[str, Any]:
    """Update user attributes"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")

        # Set the session token for the client
        client.auth.set_session(access_token, "")

        # Filter valid user attributes
        valid_attributes = {}
        if "email" in user_attributes:
            valid_attributes["email"] = user_attributes["email"]
        if "password" in user_attributes:
            valid_attributes["password"] = user_attributes["password"]
        if "phone" in user_attributes:
            valid_attributes["phone"] = user_attributes["phone"]
        if "data" in user_attributes:
            valid_attributes["data"] = user_attributes["data"]

        response = client.auth.update_user(valid_attributes)

        if response.user:
            return {
                "id": response.user.id,
                "email": response.user.email,
                "email_confirmed_at": response.user.email_confirmed_at,
                "phone": getattr(response.user, "phone", None),
                "user_metadata": response.user.user_metadata,
                "updated_at": getattr(response.user, "updated_at", None),
            }
        else:
            raise Exception("User update failed")

    except Exception as e:
        logger.error(f"User update failed: {e}")
        raise


async def reset_password_for_email(
    email: str, redirect_to: Optional[str] = None
) -> Dict[str, Any]:
    """Reset password for email"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")

        # Use the correct method name
        options = {"redirect_to": redirect_to} if redirect_to else None
        response = client.auth.reset_password_email(email, options)

        return {"message": "Password reset email sent"}

    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise


async def verify_otp(email: str, token: str, type: str = "signup") -> Dict[str, Any]:
    """Verify OTP token"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")

        # Prepare verification parameters
        verify_params = {"email": email, "token": token, "type": type}

        response = client.auth.verify_otp(verify_params)

        if response.user and response.session:
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed_at": response.user.email_confirmed_at,
                    "user_metadata": response.user.user_metadata,
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at,
                    "token_type": response.session.token_type,
                },
            }
        else:
            raise Exception("OTP verification failed")

    except Exception as e:
        logger.error(f"OTP verification failed: {e}")
        raise


# Admin functions using service role key
async def admin_get_user_by_id(user_id: str) -> Dict[str, Any]:
    """Get user by ID using admin client"""
    try:
        client = get_supabase_admin_client()
        if not client:
            raise Exception("Supabase admin client not available")

        response = client.auth.admin.get_user_by_id(user_id)

        if response.user:
            return {
                "id": response.user.id,
                "email": response.user.email,
                "email_confirmed_at": response.user.email_confirmed_at,
                "phone": getattr(response.user, "phone", None),
                "phone_confirmed_at": getattr(
                    response.user, "phone_confirmed_at", None
                ),
                "user_metadata": response.user.user_metadata,
                "app_metadata": getattr(response.user, "app_metadata", {}),
                "created_at": response.user.created_at,
                "updated_at": getattr(response.user, "updated_at", None),
                "last_sign_in_at": getattr(response.user, "last_sign_in_at", None),
            }
        else:
            raise Exception("User not found")

    except Exception as e:
        logger.error(f"Admin get user failed: {e}")
        raise


async def admin_list_users(page: int = 1, per_page: int = 50) -> Dict[str, Any]:
    """List users using admin client"""
    try:
        client = get_supabase_admin_client()
        if not client:
            raise Exception("Supabase admin client not available")

        response = client.auth.admin.list_users(page=page, per_page=per_page)

        users = []
        if hasattr(response, "users") and response.users:
            users = [
                {
                    "id": user.id,
                    "email": user.email,
                    "email_confirmed_at": user.email_confirmed_at,
                    "phone": getattr(user, "phone", None),
                    "user_metadata": user.user_metadata,
                    "created_at": user.created_at,
                    "last_sign_in_at": getattr(user, "last_sign_in_at", None),
                }
                for user in response.users
            ]

        return {"users": users, "total": len(users)}

    except Exception as e:
        logger.error(f"Admin list users failed: {e}")
        raise


async def admin_delete_user(user_id: str) -> Dict[str, Any]:
    """Delete user using admin client"""
    try:
        client = get_supabase_admin_client()
        if not client:
            raise Exception("Supabase admin client not available")

        client.auth.admin.delete_user(user_id)

        return {"message": "User deleted successfully"}

    except Exception as e:
        logger.error(f"Admin delete user failed: {e}")
        raise


def verify_supabase_token(token: str) -> dict:
    """Verify Supabase JWT token (keeping for backward compatibility)"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")

        # Get user from token
        response = client.auth.get_user(token)
        if response and getattr(response, "user", None):
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "email_verified": response.user.email_confirmed_at is not None,
            }
        else:
            raise Exception("Invalid token")

    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise Exception("Invalid or expired token")


async def register_user_with_supabase(email: str, password: str) -> dict:
    """Register user with Supabase"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")

        response = client.auth.sign_up({"email": email, "password": password})

        if response.user:
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "needs_confirmation": not response.user.email_confirmed_at,
            }
        else:
            raise Exception("Registration failed")

    except Exception as e:
        logger.error(f"Supabase registration failed: {e}")
        raise Exception(f"Registration failed: {str(e)}")


async def login_user_with_supabase(email: str, password: str) -> dict:
    """Login user with Supabase"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")

        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        if response.user and response.session:
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_in": response.session.expires_in,
            }
        else:
            raise Exception("Login failed")

    except Exception as e:
        logger.error(f"Supabase login failed: {e}")
        raise Exception("Invalid credentials")
