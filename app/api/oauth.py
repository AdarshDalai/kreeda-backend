"""
OAuth2 Authentication API Routes
Google, Apple, and Cognito authentication endpoints
"""
import os
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr

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

class CognitoRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    confirmation_code: str
    new_password: str

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


@router.post("/register", response_model=Dict[str, Any])
async def register_cognito(auth_request: CognitoRegisterRequest):
    """
    Register a new user with Cognito
    """
    try:
        # Create user in Cognito
        response = oauth_service.client.admin_create_user(
            UserPoolId=oauth_service.user_pool_id,
            Username=auth_request.email,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': auth_request.email
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                },
                {
                    'Name': 'preferred_username',
                    'Value': auth_request.username
                }
            ] + (
                [{'Name': 'name', 'Value': auth_request.full_name}]
                if auth_request.full_name else []
            ),
            MessageAction='SUPPRESS',
            TemporaryPassword=auth_request.password
        )

        # Set permanent password
        oauth_service.client.admin_set_user_password(
            UserPoolId=oauth_service.user_pool_id,
            Username=auth_request.email,
            Password=auth_request.password,
            Permanent=True
        )

        # Create user profile in DynamoDB
        from app.services.dynamodb_cricket_scoring import DynamoDBService
        from app.schemas.auth import UserCreate

        db_service = DynamoDBService()
        user_data = UserCreate(
            username=auth_request.username,
            email=auth_request.email,
            password=auth_request.password,  # This will be hashed by create_user
            full_name=auth_request.full_name
        )
        db_service.create_user(user_data)

        return {
            'message': 'User registered successfully',
            'user_id': response['User']['Username'],
            'email': auth_request.email,
            'username': auth_request.username
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
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


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Send password reset email for Cognito users
    """
    try:
        oauth_service.client.forgot_password(
            ClientId=oauth_service.client_id,
            Username=request.email
        )
        return {
            "message": "Password reset email sent successfully",
            "email": request.email
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Forgot password failed: {str(e)}"
        )


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using confirmation code
    """
    try:
        oauth_service.client.confirm_forgot_password(
            ClientId=oauth_service.client_id,
            Username=request.email,
            ConfirmationCode=request.confirmation_code,
            Password=request.new_password
        )
        return {
            "message": "Password reset successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reset password failed: {str(e)}"
        )

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
        },
        "endpoints": {
            "register": "/api/auth/oauth/register",
            "login": "/api/auth/oauth/cognito",
            "google_auth": "/api/auth/oauth/google",
            "apple_auth": "/api/auth/oauth/apple",
            "refresh": "/api/auth/oauth/refresh",
            "me": "/api/auth/oauth/me",
            "logout": "/api/auth/oauth/logout",
            "forgot_password": "/api/auth/oauth/forgot-password",
            "reset_password": "/api/auth/oauth/reset-password"
        }
    }
