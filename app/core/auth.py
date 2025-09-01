"""
Cognito-Only Authentication System
Uses AWS Cognito for all authentication, DynamoDB for user profiles
"""
import jwt
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.schemas.auth import UserResponse
from app.services.dynamodb_cricket_scoring import DynamoDBService


# JWT token scheme
security = HTTPBearer(auto_error=False)

# Global DynamoDB service instance
db_service = DynamoDBService()

# Cognito client setup - Required for this system
cognito_client = boto3.client(
    'cognito-idp',
    region_name=settings.COGNITO_REGION
)

# Cognito configuration
COGNITO_USER_POOL_ID = settings.COGNITO_USER_POOL_ID
COGNITO_CLIENT_ID = settings.COGNITO_CLIENT_ID
COGNITO_REGION = settings.COGNITO_REGION


def get_cognito_public_keys() -> Dict[str, Any]:
    """Fetch Cognito public keys for token verification"""
    try:
        # Get the JSON Web Key Set (JWKS) from Cognito
        jwks_url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        response = requests.get(jwks_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Cognito public keys: {str(e)}"
        )


def verify_cognito_token(token: str) -> Dict[str, Any]:
    """Verify and decode Cognito JWT token"""
    try:
        # Get the headers to find the key ID
        headers = jwt.get_unverified_header(token)
        kid = headers.get('kid')

        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing key ID"
            )

        # Get public keys
        jwks = get_cognito_public_keys()

        # Find the correct public key
        public_key = None
        for key in jwks['keys']:
            if key['kid'] == kid:
                # For now, use simplified verification
                # In production, implement full JWK to PEM conversion
                public_key = key
                break

        if not public_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: public key not found"
            )

        # For development: decode without signature verification
        # TODO: Implement full JWT signature verification in production
        payload = jwt.decode(token, options={"verify_signature": False})

        # Basic validation of token claims
        if payload.get('iss') != f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer"
            )

        if payload.get('aud') != COGNITO_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token audience"
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserResponse:
    """Get current authenticated user from Cognito JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Verify and decode Cognito token
        payload = verify_cognito_token(token)

        # Extract user ID from token
        cognito_sub = payload.get('sub')
        if not cognito_sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )

        # Get user profile from DynamoDB using Cognito sub as key
        user_profile = db_service.get_user_profile_by_cognito_sub(cognito_sub)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User profile not found"
            )

        return UserResponse(
            id=user_profile["id"],
            username=user_profile["username"],
            email=user_profile["email"],
            full_name=user_profile.get("full_name"),
            created_at=user_profile["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


def get_current_active_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Get current active user (placeholder for future use)"""
    return current_user


def create_user_profile(cognito_sub: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create user profile in DynamoDB using Cognito sub as key"""
    try:
        now = datetime.utcnow().isoformat()

        profile_data = {
            'cognito_sub': cognito_sub,
            'username': user_data.get('username'),
            'email': user_data.get('email'),
            'full_name': user_data.get('full_name'),
            'created_at': now,
            'updated_at': now,
            'is_active': True,
            'profile_data': {}  # For additional user-specific data
        }

        # Use the new method we'll add to DynamoDBService
        return db_service.create_user_profile(profile_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user profile: {str(e)}"
        )


def update_user_profile(cognito_sub: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update user profile in DynamoDB"""
    try:
        updates['updated_at'] = datetime.utcnow().isoformat()
        return db_service.update_user_profile(cognito_sub, updates)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        )


def delete_user_profile(cognito_sub: str) -> bool:
    """Delete user profile from DynamoDB"""
    try:
        return db_service.delete_user_profile(cognito_sub)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user profile: {str(e)}"
        )
