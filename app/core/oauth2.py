from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel
import secrets
from urllib.parse import urlencode, urlparse, parse_qs

from app.core.config import settings
from app.services.auth import auth_service
from app.models.user import User


class OAuth2Scope:
    """Define OAuth2 scopes for different access levels."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    PROFILE = "profile"
    EMAIL = "email"


class OAuth2Client(BaseModel):
    """OAuth2 client model."""
    client_id: str
    client_secret: str
    client_name: str
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    scopes: List[str]
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuthorizationCode(BaseModel):
    """OAuth2 authorization code model."""
    code: str
    client_id: str
    user_id: str
    redirect_uri: str
    scopes: List[str]
    expires_at: datetime
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None
    
    class Config:
        from_attributes = True


class OAuth2Token(BaseModel):
    """OAuth2 token response model."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    
    class Config:
        from_attributes = True


class OAuth2Service:
    """OAuth2 2.0 compliant service implementation."""
    
    def __init__(self):
        self.authorization_code_expire_minutes = 10
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        
        # In-memory storage for demo - in production, use database
        self._clients: Dict[str, OAuth2Client] = {}
        self._authorization_codes: Dict[str, AuthorizationCode] = {}
        self._access_tokens: Dict[str, Dict] = {}
        
        # Initialize default client
        self._init_default_client()
    
    def _init_default_client(self):
        """Initialize a default OAuth2 client for testing."""
        default_client = OAuth2Client(
            client_id="kreeda_mobile_app",
            client_secret="kreeda_mobile_secret_2024",
            client_name="Kreeda Mobile App",
            redirect_uris=["http://localhost:3000/auth/callback", "kreeda://auth/callback"],
            grant_types=["authorization_code", "refresh_token", "password"],
            response_types=["code", "token"],
            scopes=[OAuth2Scope.READ, OAuth2Scope.WRITE, OAuth2Scope.PROFILE, OAuth2Scope.EMAIL],
            created_at=datetime.utcnow()
        )
        self._clients[default_client.client_id] = default_client
    
    def get_client(self, client_id: str) -> Optional[OAuth2Client]:
        """Get OAuth2 client by ID."""
        return self._clients.get(client_id)
    
    def validate_client_credentials(self, client_id: str, client_secret: str) -> bool:
        """Validate OAuth2 client credentials."""
        client = self.get_client(client_id)
        return client is not None and client.client_secret == client_secret and client.is_active
    
    def validate_redirect_uri(self, client_id: str, redirect_uri: str) -> bool:
        """Validate redirect URI for client."""
        client = self.get_client(client_id)
        return client is not None and redirect_uri in client.redirect_uris
    
    def validate_scope(self, client_id: str, requested_scopes: List[str]) -> bool:
        """Validate requested scopes against client allowed scopes."""
        client = self.get_client(client_id)
        if not client:
            return False
        return all(scope in client.scopes for scope in requested_scopes)
    
    def generate_authorization_code(
        self, 
        client_id: str, 
        user_id: str, 
        redirect_uri: str, 
        scopes: List[str],
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None
    ) -> str:
        """Generate OAuth2 authorization code."""
        code = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=self.authorization_code_expire_minutes)
        
        auth_code = AuthorizationCode(
            code=code,
            client_id=client_id,
            user_id=user_id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            expires_at=expires_at,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )
        
        self._authorization_codes[code] = auth_code
        return code
    
    def validate_authorization_code(
        self, 
        code: str, 
        client_id: str, 
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Optional[AuthorizationCode]:
        """Validate and consume authorization code."""
        auth_code = self._authorization_codes.get(code)
        
        if not auth_code:
            return None
        
        # Check if code is expired
        if datetime.utcnow() > auth_code.expires_at:
            del self._authorization_codes[code]
            return None
        
        # Validate client and redirect URI
        if auth_code.client_id != client_id or auth_code.redirect_uri != redirect_uri:
            return None
        
        # Validate PKCE if used
        if auth_code.code_challenge:
            if not code_verifier:
                return None
            
            if auth_code.code_challenge_method == "S256":
                import hashlib
                import base64
                expected = base64.urlsafe_b64encode(
                    hashlib.sha256(code_verifier.encode()).digest()
                ).decode().rstrip('=')
                if expected != auth_code.code_challenge:
                    return None
            elif auth_code.code_challenge_method == "plain":
                if code_verifier != auth_code.code_challenge:
                    return None
        
        # Consume the code (one-time use)
        del self._authorization_codes[code]
        return auth_code
    
    def create_oauth2_tokens(
        self, 
        user: User, 
        client_id: str, 
        scopes: List[str]
    ) -> OAuth2Token:
        """Create OAuth2 compliant access and refresh tokens."""
        # Generate token data with OAuth2 claims
        token_data = {
            "sub": str(user.id),
            "client_id": client_id,
            "scope": " ".join(scopes),
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "aud": client_id,  # Audience
            "iss": settings.JWT_ISSUER if hasattr(settings, 'JWT_ISSUER') else "kreeda-api"  # Issuer
        }
        
        access_token = auth_service.generate_access_token(token_data)
        refresh_token = auth_service.generate_refresh_token({
            "sub": str(user.id),
            "client_id": client_id,
            "scope": " ".join(scopes)
        })
        
        # Store token info
        self._access_tokens[access_token] = {
            "user_id": str(user.id),
            "client_id": client_id,
            "scopes": scopes,
            "expires_at": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        }
        
        return OAuth2Token(
            access_token=access_token,
            token_type="Bearer",
            expires_in=self.access_token_expire_minutes * 60,
            refresh_token=refresh_token,
            scope=" ".join(scopes)
        )
    
    def build_authorization_url(
        self, 
        authorization_endpoint: str,
        client_id: str,
        redirect_uri: str,
        scopes: List[str],
        state: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None
    ) -> str:
        """Build OAuth2 authorization URL."""
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes)
        }
        
        if state:
            params["state"] = state
        
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = code_challenge_method or "S256"
        
        return f"{authorization_endpoint}?{urlencode(params)}"
    
    def validate_token_request(
        self, 
        grant_type: str, 
        client_id: str, 
        **kwargs
    ) -> bool:
        """Validate OAuth2 token request parameters."""
        client = self.get_client(client_id)
        if not client or not client.is_active:
            return False
        
        return grant_type in client.grant_types
    
    def introspect_token(self, token: str) -> Dict[str, Any]:
        """OAuth2 token introspection (RFC 7662)."""
        try:
            # Verify token
            token_data = auth_service.verify_token(token)
            token_info = self._access_tokens.get(token)
            
            if not token_info:
                return {"active": False}
            
            # Check if token is expired
            if datetime.utcnow() > token_info["expires_at"]:
                del self._access_tokens[token]
                return {"active": False}
            
            return {
                "active": True,
                "client_id": token_info["client_id"],
                "username": token_data.username,
                "scope": " ".join(token_info["scopes"]),
                "sub": token_data.sub,
                "aud": token_info["client_id"],
                "iss": "kreeda-api",
                "exp": int(token_info["expires_at"].timestamp()),
                "iat": token_data.iat
            }
            
        except Exception:
            return {"active": False}
    
    def revoke_token(self, token: str, token_type_hint: Optional[str] = None) -> bool:
        """OAuth2 token revocation (RFC 7009)."""
        try:
            # Remove from active tokens
            if token in self._access_tokens:
                del self._access_tokens[token]
                return True
            
            # Handle refresh token revocation
            # In a real implementation, you'd also revoke refresh tokens
            return True
            
        except Exception:
            return False


# OAuth2 password bearer for FastAPI dependency injection
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/oauth2/token",
    scopes={
        OAuth2Scope.READ: "Read access",
        OAuth2Scope.WRITE: "Write access", 
        OAuth2Scope.DELETE: "Delete access",
        OAuth2Scope.ADMIN: "Admin access",
        OAuth2Scope.PROFILE: "Access to user profile",
        OAuth2Scope.EMAIL: "Access to user email"
    }
)


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    """Extended OAuth2PasswordBearer that also checks cookies."""
    
    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        
        if not authorization or scheme.lower() != "bearer":
            # Check for token in cookies as fallback
            token = request.cookies.get("access_token")
            if token:
                return token
            
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        
        return param


# Global OAuth2 service instance
oauth2_service = OAuth2Service()

# Enhanced OAuth2 scheme with cookie support
oauth2_scheme_enhanced = OAuth2PasswordBearerWithCookie(
    tokenUrl="/api/v1/auth/oauth2/token",
    scopes={
        OAuth2Scope.READ: "Read access",
        OAuth2Scope.WRITE: "Write access",
        OAuth2Scope.DELETE: "Delete access", 
        OAuth2Scope.ADMIN: "Admin access",
        OAuth2Scope.PROFILE: "Access to user profile",
        OAuth2Scope.EMAIL: "Access to user email"
    }
)
