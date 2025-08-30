"""
OAuth2 Authentication API Routes
Google, Apple, and Cognito authentication endpoints
"""
import os
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from pydantic import BaseModel

from app.core.cognito_auth import CognitoOAuth2Service, get_current_user_from_oauth

router = APIRouter(prefix="/api/auth/oauth", tags=["oauth2"])

# Pydantic models for OAuth requests
class GoogleAuthRequest(BaseModel):
    id_token: str

class AppleAuthRequest(BaseModel):
    authorization_code: str
    code_verifier: str

class CognitoAuthRequest(BaseModel):
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Global OAuth2 service instance
oauth_service = CognitoOAuth2Service()

@router.post("/google", response_model=Dict[str, Any])
async def authenticate_google(auth_request: GoogleAuthRequest):
    """
    Authenticate with Google OAuth ID token
    """
    return oauth_service.authenticate_google_oauth(auth_request.id_token)

@router.post("/apple", response_model=Dict[str, Any])
async def authenticate_apple(auth_request: AppleAuthRequest):
    """
    Authenticate with Apple Sign-In
    """
    return oauth_service.authenticate_apple_oauth(
        auth_request.authorization_code,
        auth_request.code_verifier
    )

@router.post("/cognito", response_model=Dict[str, Any])
async def authenticate_cognito(auth_request: CognitoAuthRequest):
    """
    Authenticate with Cognito username/password
    """
    return oauth_service.authenticate_cognito_user(
        auth_request.username,
        auth_request.password
    )

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_access_token(refresh_request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    """
    return oauth_service.refresh_token(refresh_request.refresh_token)

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_oauth)
):
    """
    Get current authenticated user info
    """
    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "message": "Successfully authenticated"
    }

@router.post("/logout")
async def logout_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_oauth)
):
    """
    Logout user (client should discard tokens)
    """
    return {
        "message": "Successfully logged out",
        "user_id": current_user["user_id"]
    }

# OAuth2 configuration endpoints for mobile apps
@router.get("/config")
async def get_oauth_config():
    """
    Get OAuth2 configuration for mobile apps
    """
    return {
        "cognito": {
            "user_pool_id": os.environ.get('COGNITO_USER_POOL_ID'),
            "client_id": os.environ.get('COGNITO_CLIENT_ID'),
            "region": os.environ.get('AWS_REGION', 'us-east-1')
        },
        "google": {
            "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
            "redirect_uri": os.environ.get('GOOGLE_REDIRECT_URI')
        },
        "apple": {
            "client_id": os.environ.get('APPLE_CLIENT_ID'),
            "redirect_uri": os.environ.get('APPLE_REDIRECT_URI'),
            "team_id": os.environ.get('APPLE_TEAM_ID')
        }
    }
