"""
Authentication API Routes - Version 1
Cognito-based authentication for AWS serverless deployment
"""
import os
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.auth import UserResponse
from app.core.config import settings

router = APIRouter(tags=["authentication-v1"])

# AWS Cognito configuration
COGNITO_REGION = os.environ.get('AWS_REGION', 'us-east-1')
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """Get current user from Cognito JWT token with proper error handling and caching - Version 1"""
    try:
        import jwt
        import requests
        from datetime import datetime
        import time
        from functools import lru_cache

        token = credentials.credentials

        # Cache JWKS keys to avoid repeated requests
        @lru_cache(maxsize=1)
        def get_jwks_keys(user_pool_id: str, region: str):
            """Cached JWKS keys retrieval with timeout"""
            try:
                keys_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
                response = requests.get(keys_url, timeout=5)  # 5 second timeout
                response.raise_for_status()
                return response.json()['keys']
            except requests.RequestException as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch JWKS keys: {str(e)}"
                )

        # Get cached keys
        keys = get_jwks_keys(COGNITO_USER_POOL_ID, COGNITO_REGION)

        # Decode JWT header to get key ID
        try:
            header = jwt.get_unverified_header(token)
            key_id = header['kid']
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token format")

        # Find the correct key
        public_key = None
        for key in keys:
            if key['kid'] == key_id:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                break

        if not public_key:
            raise HTTPException(status_code=401, detail="Invalid token: key not found")

        # Verify and decode token with proper error handling
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=COGNITO_CLIENT_ID,
                issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}",
                options={
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True
                }
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidAudienceError:
            raise HTTPException(status_code=401, detail="Invalid token audience")
        except jwt.InvalidIssuerError:
            raise HTTPException(status_code=401, detail="Invalid token issuer")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

        # Additional validation
        current_time = datetime.utcnow().timestamp()
        if payload.get('exp', 0) <= current_time:
            raise HTTPException(status_code=401, detail="Token has expired")

        if payload.get('iat', 0) > current_time:
            raise HTTPException(status_code=401, detail="Token issued in the future")

        return UserResponse(
            id=payload['sub'],
            username=payload.get('cognito:username', payload['sub']),
            email=payload.get('email', ''),
            full_name=payload.get('name', ''),
            created_at=str(payload.get('iat', ''))
        )

    except HTTPException:
        raise
    except Exception as e:
        # Log unexpected errors but don't expose details
        print(f"Authentication error: {str(e)}")  # Replace with proper logging
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """Get current user profile - Version 1"""
    return current_user


@router.post("/verify-token")
async def verify_token(request: Request):
    """Verify JWT token validity - Version 1"""
    try:
        auth_header = request.headers.get('authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        token = auth_header.split(' ')[1]
        user = await get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
        return {"valid": True, "user": user}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


@router.get("/config")
async def get_auth_config():
    """Get authentication configuration for frontend - Version 1"""
    return {
        "region": COGNITO_REGION,
        "userPoolId": COGNITO_USER_POOL_ID,
        "userPoolWebClientId": COGNITO_CLIENT_ID,
        "oauth": {
            "domain": f"kreeda-users.auth.{COGNITO_REGION}.amazoncognito.com",
            "scope": ["email", "profile", "openid"],
            "redirectSignIn": "https://yourdomain.com/auth/callback",
            "redirectSignOut": "https://yourdomain.com/logout",
            "responseType": "code"
        }
    }
