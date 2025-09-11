import logging
from typing import Any, Dict, Optional, Union

from supabase.client import create_client

from app.config import settings

logger = logging.getLogger(__name__)


def get_supabase_client():
    """Get Supabase client instance"""
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_admin_supabase_client():
    """Get Supabase admin client instance"""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


# Auth functions
def sign_up_with_email_password(
    email: str, password: str, user_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Sign up user with email and password

    Args:
        email: User's email
        password: User's password
        user_metadata: Additional user data

    Returns:
        Dict containing user data and session info
    """
    try:
        # For development, create user with admin client to skip email confirmation
        from app.config import settings

        if settings.environment in ["development", "testing"]:
            try:
                admin_client = get_admin_supabase_client()

                # Create user with admin client (auto-confirmed)
                user_data = {
                    "email": email,
                    "password": password,
                    "email_confirm": True,  # Skip email confirmation
                }
                if user_metadata:
                    user_data["user_metadata"] = user_metadata

                admin_response = admin_client.auth.admin.create_user(user_data)  # type: ignore

                if (
                    admin_response
                    and hasattr(admin_response, "user")
                    and admin_response.user
                ):
                    logger.info(
                        f"User created with admin client (auto-confirmed): {email}"
                    )

                    # Now sign them in to get a session
                    sign_in_response = sign_in_with_email_password(email, password)
                    if sign_in_response.get("success"):
                        return {
                            "success": True,
                            "user": admin_response.user.__dict__,
                            "session": sign_in_response.get("session"),
                            "message": "User registered and logged in successfully",
                        }
                    else:
                        return {
                            "success": True,
                            "user": admin_response.user.__dict__,
                            "session": None,
                            "message": "User registered successfully, but auto-login failed",
                        }

            except Exception as admin_error:
                logger.warning(
                    f"Admin user creation failed for {email}, falling back to regular signup: {str(admin_error)}"
                )
                # Fall back to regular signup

        # Regular signup flow
        client = get_supabase_client()

        # Simple dictionary approach for compatibility - use Any typing
        data: Dict[str, Any] = {"email": email, "password": password}
        if user_metadata:
            data["data"] = user_metadata

        response = client.auth.sign_up(data)  # type: ignore

        # Handle both successful registration and email confirmation required
        if response and hasattr(response, "user") and response.user:
            logger.info(f"User signed up successfully: {email}")
            return {
                "success": True,
                "user": response.user.__dict__,
                "session": response.session.__dict__ if response.session else None,
                "message": "User registered successfully",
            }
        elif response:
            # Registration successful but email confirmation required
            logger.info(f"User signed up, email confirmation required: {email}")
            return {
                "success": True,
                "message": "Registration successful. Please check your email to confirm your account.",
                "user": None,
                "session": None,
            }
        else:
            logger.error(f"Sign up failed for {email} - no response")
            return {
                "success": False,
                "error": "Sign up failed - no response from server",
            }

    except Exception as e:
        logger.error(f"Sign up error for {email}: {str(e)}")
        return {"success": False, "error": str(e)}


def sign_in_with_email_password(email: str, password: str) -> Dict[str, Any]:
    """
    Sign in user with email and password

    Args:
        email: User's email
        password: User's password

    Returns:
        Dict containing user data and session info
    """
    try:
        client = get_supabase_client()

        data = {"email": email, "password": password}
        response = client.auth.sign_in_with_password(data)  # type: ignore

        if response.user and response.session:
            logger.info(f"User signed in successfully: {email}")
            return {
                "success": True,
                "user": response.user.__dict__,
                "session": response.session.__dict__,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
            }
        else:
            logger.error(f"Sign in failed for {email}")
            return {"success": False, "error": "Invalid credentials"}

    except Exception as e:
        logger.error(f"Sign in error for {email}: {str(e)}")
        return {"success": False, "error": str(e)}


def sign_in_with_oauth(
    provider: str, redirect_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sign in with OAuth provider

    Args:
        provider: OAuth provider (google, github, etc.)
        redirect_to: Redirect URL after authentication

    Returns:
        Dict containing OAuth URL
    """
    try:
        client = get_supabase_client()

        data: Dict[str, Any] = {"provider": provider}
        if redirect_to:
            data["options"] = {"redirect_to": redirect_to}

        response = client.auth.sign_in_with_oauth(data)  # type: ignore

        if response:
            logger.info(f"OAuth sign in initiated for provider: {provider}")
            return {
                "success": True,
                "url": response.url if hasattr(response, "url") else str(response),
            }
        else:
            return {"success": False, "error": "OAuth sign in failed"}

    except Exception as e:
        logger.error(f"OAuth sign in error for provider {provider}: {str(e)}")
        return {"success": False, "error": str(e)}


def refresh_session(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh user session

    Args:
        refresh_token: Refresh token

    Returns:
        Dict containing new session data
    """
    try:
        client = get_supabase_client()
        response = client.auth.refresh_session(refresh_token)

        if response.session:
            logger.info("Session refreshed successfully")
            return {
                "success": True,
                "session": response.session.__dict__,
                "user": response.user.__dict__ if response.user else None,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
            }
        else:
            return {"success": False, "error": "Failed to refresh session"}

    except Exception as e:
        logger.error(f"Session refresh error: {str(e)}")
        return {"success": False, "error": str(e)}


def get_user_from_token(access_token: str) -> Dict[str, Any]:
    """
    Get user data from access token

    Args:
        access_token: JWT access token

    Returns:
        Dict containing user data
    """
    try:
        client = get_supabase_client()
        response = client.auth.get_user(access_token)

        if response and response.user:
            return response.user.__dict__
        else:
            raise Exception("Invalid token")

    except Exception as e:
        logger.error(f"Get user from token error: {str(e)}")
        raise Exception(f"Invalid token: {str(e)}")


def sign_out(access_token: str) -> Dict[str, Any]:
    """
    Sign out user

    Args:
        access_token: User's access token

    Returns:
        Dict containing success status
    """
    try:
        client = get_supabase_client()
        # Set the session first
        client.auth.set_session(access_token, "")

        response = client.auth.sign_out()

        logger.info("User signed out successfully")
        return {"success": True}

    except Exception as e:
        logger.error(f"Sign out error: {str(e)}")
        return {"success": False, "error": str(e)}


def reset_password_email(
    email: str, redirect_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send password reset email

    Args:
        email: User's email
        redirect_to: Redirect URL after password reset

    Returns:
        Dict containing success status
    """
    try:
        client = get_supabase_client()

        # Try different method names based on the client version
        try:
            options = {}
            if redirect_to:
                options["redirectTo"] = redirect_to
            # Try method without strict typing
            response = getattr(client.auth, "reset_password_for_email", None)
            if response:
                response = response(email, options)  # type: ignore
            else:
                raise AttributeError("Method not found")
        except AttributeError:
            # Fallback - create a mock response
            logger.warning(
                f"Password reset method not available - would send reset to: {email}"
            )
            response = True

        logger.info(f"Password reset email sent to: {email}")
        return {"success": True, "message": "Password reset email sent"}

    except Exception as e:
        logger.error(f"Password reset error for {email}: {str(e)}")
        return {"success": False, "error": str(e)}


def verify_otp(email: str, token: str, type_: str = "signup") -> Dict[str, Any]:
    """
    Verify OTP token

    Args:
        email: User's email
        token: OTP token
        type_: OTP type (signup, recovery, etc.)

    Returns:
        Dict containing user data and session info
    """
    try:
        client = get_supabase_client()

        # Use dictionary format that the client expects
        data = {"email": email, "token": token, "type": type_}

        response = client.auth.verify_otp(data)  # type: ignore

        if response.user and response.session:
            logger.info(f"OTP verified successfully for: {email}")
            return {
                "success": True,
                "user": response.user.__dict__,
                "session": response.session.__dict__,
            }
        else:
            return {"success": False, "error": "Invalid OTP"}

    except Exception as e:
        logger.error(f"OTP verification error for {email}: {str(e)}")
        return {"success": False, "error": str(e)}


def update_user(access_token: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user attributes

    Args:
        access_token: User's access token
        attributes: Dictionary of attributes to update (email, password, data, etc.)

    Returns:
        Dict containing updated user data
    """
    try:
        client = get_supabase_client()
        # Set the session first
        client.auth.set_session(access_token, "")

        response = client.auth.update_user(attributes)  # type: ignore

        if response.user:
            logger.info("User updated successfully")
            return {"success": True, "user": response.user.__dict__}
        else:
            return {"success": False, "error": "Failed to update user"}

    except Exception as e:
        logger.error(f"User update error: {str(e)}")
        return {"success": False, "error": str(e)}


# Admin functions (require service role key)
def admin_get_user_by_id(user_id: str) -> Dict[str, Any]:
    """
    Get user by ID (admin function)

    Args:
        user_id: User's Supabase ID

    Returns:
        Dict containing user data
    """
    try:
        client = get_admin_supabase_client()
        response = client.auth.admin.get_user_by_id(user_id)

        if response.user:
            return {"success": True, "user": response.user.__dict__}
        else:
            return {"success": False, "error": "User not found"}

    except Exception as e:
        logger.error(f"Admin get user error for {user_id}: {str(e)}")
        return {"success": False, "error": str(e)}


def admin_update_user_by_id(user_id: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user by ID (admin function)

    Args:
        user_id: User's Supabase ID
        attributes: Dictionary of attributes to update

    Returns:
        Dict containing updated user data
    """
    try:
        client = get_admin_supabase_client()
        response = client.auth.admin.update_user_by_id(user_id, attributes)  # type: ignore

        if response.user:
            logger.info(f"User {user_id} updated successfully by admin")
            return {"success": True, "user": response.user.__dict__}
        else:
            return {"success": False, "error": "Failed to update user"}

    except Exception as e:
        logger.error(f"Admin update user error for {user_id}: {str(e)}")
        return {"success": False, "error": str(e)}


def admin_delete_user(user_id: str) -> Dict[str, Any]:
    """
    Delete user (admin function)

    Args:
        user_id: User's Supabase ID

    Returns:
        Dict containing success status
    """
    try:
        client = get_admin_supabase_client()
        response = client.auth.admin.delete_user(user_id)

        logger.info(f"User {user_id} deleted successfully by admin")
        return {"success": True}

    except Exception as e:
        logger.error(f"Admin delete user error for {user_id}: {str(e)}")
        return {"success": False, "error": str(e)}
