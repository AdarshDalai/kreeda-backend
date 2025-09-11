from supabase.client import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

from typing import Optional

# Initialize Supabase client
supabase: Optional[Client] = None

def get_supabase_client() -> Optional[Client]:
    """Get Supabase client instance"""
    global supabase
    if supabase is None:
        if not settings.supabase_url or not settings.supabase_anon_key:
            logger.warning("Supabase credentials not configured")
            return None
        
        try:
            supabase = create_client(
                settings.supabase_url,
                settings.supabase_anon_key
            )
            logger.info("Supabase client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return None
    
    return supabase


def verify_supabase_token(token: str) -> dict:
    """Verify Supabase JWT token"""
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
        raise Exception("Invalid or expired token")


async def register_user_with_supabase(email: str, password: str) -> dict:
    """Register user with Supabase"""
    try:
        client = get_supabase_client()
        if not client:
            raise Exception("Supabase client not available")
        
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "needs_confirmation": not response.user.email_confirmed_at
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
        
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user and response.session:
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_in": response.session.expires_in
            }
        else:
            raise Exception("Login failed")
            
    except Exception as e:
        logger.error(f"Supabase login failed: {e}")
        raise Exception("Invalid credentials")
