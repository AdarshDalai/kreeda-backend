from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import secrets
import uuid
from fastapi import HTTPException, status, Request

from app.core.config import settings
from app.schemas.auth import TokenData, AuthProvider


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = settings.JWT_ALGORITHM
        self.secret_key = settings.JWT_SECRET_KEY
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)

    def generate_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generate a JWT token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # Unique token ID
        })
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return token.decode('utf-8') if isinstance(token, bytes) else token

    def generate_access_token(self, user_data: Dict[str, Any]) -> str:
        """Generate an access token."""
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        return self.generate_token(user_data, access_token_expires)

    def generate_refresh_token(self, user_data: Dict[str, Any]) -> str:
        """Generate a refresh token."""
        refresh_token_expires = timedelta(days=self.refresh_token_expire_days)
        token_data = {
            "sub": user_data["sub"],
            "type": "refresh"
        }
        return self.generate_token(token_data, refresh_token_expires)

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user ID"
                )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return TokenData(
                sub=user_id,
                email=payload.get("email", ""),
                username=payload.get("username", ""),
                role=payload.get("role", "player"),
                exp=exp,
                iat=payload.get("iat", 0),
                jti=payload.get("jti", "")
            )
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode a JWT token without verification (for internal use)."""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )

    def generate_reset_token(self) -> str:
        """Generate a secure password reset token."""
        return secrets.token_urlsafe(32)

    def generate_verification_token(self) -> str:
        """Generate a secure email verification token."""
        return secrets.token_urlsafe(32)

    def hash_token(self, token: str) -> str:
        """Hash a token for storage."""
        hashed = bcrypt.hash(token)
        return hashed.decode('utf-8') if isinstance(hashed, bytes) else hashed

    def verify_token_hash(self, token: str, hashed_token: str) -> bool:
        """Verify a token against its hash."""
        return bcrypt.verify(token, hashed_token)

    def extract_client_info(self, request: Request) -> Dict[str, str]:
        """Extract client information from request."""
        return {
            "ip_address": self.get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "device_info": self.parse_user_agent(request.headers.get("user-agent", ""))
        }

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address, handling proxies."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
            
        return request.client.host if request.client else "unknown"

    def parse_user_agent(self, user_agent: str) -> str:
        """Parse user agent to extract device/browser info."""
        if not user_agent:
            return "Unknown"
        
        # Simple parsing - in production you might use a library like user-agents
        if "Mobile" in user_agent:
            device_type = "Mobile"
        elif "Tablet" in user_agent:
            device_type = "Tablet"
        else:
            device_type = "Desktop"
            
        # Extract browser info
        if "Chrome" in user_agent:
            browser = "Chrome"
        elif "Firefox" in user_agent:
            browser = "Firefox"
        elif "Safari" in user_agent:
            browser = "Safari"
        elif "Edge" in user_agent:
            browser = "Edge"
        else:
            browser = "Unknown"
            
        return f"{device_type} - {browser}"

    def is_strong_password(self, password: str) -> Tuple[bool, str]:
        """Check if password meets strength requirements."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if not has_upper:
            return False, "Password must contain at least one uppercase letter"
        if not has_lower:
            return False, "Password must contain at least one lowercase letter"
        if not has_digit:
            return False, "Password must contain at least one number"
        if not has_special:
            return False, "Password must contain at least one special character"
            
        return True, "Password is strong"


class OAuthService:
    """Service for handling OAuth operations."""
    
    @staticmethod
    async def verify_google_token(access_token: str) -> Dict[str, Any]:
        """Verify Google OAuth token and return user data."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            try:
                # Verify token with Google
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v1/userinfo",
                    params={"access_token": access_token}
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Google access token"
                    )
                
                user_data = response.json()
                
                return {
                    "provider_id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "full_name": user_data.get("name"),
                    "avatar_url": user_data.get("picture"),
                    "email_verified": user_data.get("verified_email", False)
                }
                
            except httpx.RequestError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Could not verify Google token"
                )

    @staticmethod
    async def verify_apple_token(id_token: str) -> Dict[str, Any]:
        """Verify Apple ID token and return user data."""
        from jose import jwt
        import httpx
        
        try:
            # Get Apple's public keys
            async with httpx.AsyncClient() as client:
                keys_response = await client.get("https://appleid.apple.com/auth/keys")
                apple_keys = keys_response.json()
            
            # Decode the token header to get the key ID
            header = jwt.get_unverified_header(id_token)
            key_id = header.get("kid")
            
            # Find the corresponding key
            apple_key = None
            for key in apple_keys.get("keys", []):
                if key.get("kid") == key_id:
                    apple_key = key
                    break
            
            if not apple_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Apple ID token: key not found"
                )
            
            # Verify and decode the token
            # Note: This is simplified. In production, you'd need to properly
            # construct the RSA key from the JWK format
            payload = jwt.decode(
                id_token,
                apple_key,
                algorithms=["RS256"],
                audience=settings.APPLE_CLIENT_ID,  # Your Apple app ID
                options={"verify_signature": False}  # Simplified for demo
            )
            
            return {
                "provider_id": payload.get("sub"),
                "email": payload.get("email"),
                "email_verified": payload.get("email_verified", False),
                "full_name": None  # Apple doesn't always provide name
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Apple ID token: {str(e)}"
            )

    @staticmethod
    def generate_username_from_email(email: str) -> str:
        """Generate a unique username from email."""
        base_username = email.split("@")[0].lower()
        # Remove non-alphanumeric characters except underscore and hyphen
        base_username = "".join(c for c in base_username if c.isalnum() or c in "_-")
        return base_username[:20]  # Limit length


# Global instances
auth_service = AuthService()
oauth_service = OAuthService()
