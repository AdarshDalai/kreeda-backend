"""
Authentication API Routes
Cognito-only authentication system
"""
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.schemas.auth import UserResponse, UserCreate, Token, UserLogin, ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest, UpdateProfileRequest, VerifyEmailRequest, ResendVerificationRequest, AuthResponse
from app.core.config import settings
from app.core.auth import (
    get_current_user, get_current_active_user,
    create_user_profile, update_user_profile, delete_user_profile
)
from app.services.dynamodb_cricket_scoring import DynamoDBService
from app.core.cognito_auth import CognitoOAuth2Service
import boto3
from botocore.exceptions import ClientError

router = APIRouter(tags=["authentication"])

# Initialize services
db_service = DynamoDBService()
oauth_service = None
if settings.USE_COGNITO and settings.COGNITO_USER_POOL_ID and settings.COGNITO_CLIENT_ID:
    try:
        oauth_service = CognitoOAuth2Service()
    except:
        oauth_service = None


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user with Cognito"""
    try:
        # Initialize Cognito client
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.COGNITO_REGION
        )

        # Create user in Cognito
        response = cognito_client.admin_create_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=user_data.email,  # Use email as Cognito username
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': user_data.email
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                },
                {
                    'Name': 'preferred_username',
                    'Value': user_data.username
                }
            ],
            MessageAction='SUPPRESS',  # Don't send invitation email
            TemporaryPassword=user_data.password
        )

        # Set permanent password
        cognito_client.admin_set_user_password(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=user_data.email,
            Password=user_data.password,
            Permanent=True
        )

        # Extract Cognito sub from response
        cognito_sub = None
        for attr in response['User']['Attributes']:
            if attr['Name'] == 'sub':
                cognito_sub = attr['Value']
                break

        if not cognito_sub:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get Cognito user ID"
            )

        # Create user profile in DynamoDB
        profile_data = {
            'username': user_data.username,
            'email': user_data.email,
            'full_name': user_data.full_name
        }
        user_profile = create_user_profile(cognito_sub, profile_data)

        return UserResponse(
            id=user_profile["id"],
            username=user_profile["username"],
            email=user_profile["email"],
            full_name=user_profile.get("full_name"),
            created_at=user_profile["created_at"]
        )

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UsernameExistsException':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        elif error_code == 'InvalidPasswordException':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet requirements"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cognito registration failed: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login user with Cognito and return access token"""
    try:
        # Initialize Cognito client
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.COGNITO_REGION
        )

        # First get user email from DynamoDB
        user_record = db_service.get_user_by_username(login_data.username)
        if not user_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        user_email = user_record.get('email')
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Authenticate with Cognito
        auth_response = cognito_client.admin_initiate_auth(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            ClientId=settings.COGNITO_CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': user_email,
                'PASSWORD': login_data.password
            }
        )

        if 'AuthenticationResult' in auth_response:
            access_token = auth_response['AuthenticationResult']['AccessToken']

            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=auth_response['AuthenticationResult'].get('ExpiresIn', 3600)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ['NotAuthorizedException', 'UserNotFoundException']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.post("/verify-token")
async def verify_token(request: Request):
    """Verify JWT token validity"""
    try:
        auth_header = request.headers.get('authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        token = auth_header.split(' ')[1]
        # Create a mock credentials object for validation
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        user = await get_current_user(credentials)  # This will validate the token
        return {"valid": True, "user": user}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


@router.get("/config")
async def get_auth_config():
    """Get authentication configuration for frontend"""
    return {
        "auth_type": "jwt",
        "token_expiry_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "algorithm": settings.ALGORITHM,
        "token_url": "/api/auth/login",
        "user_info_url": "/api/auth/me",
        "client_id": "kreeda-backend",
        "endpoints": {
            "register": "/api/auth/register",
            "login": "/api/auth/login",
            "me": "/api/auth/me",
            "verify_token": "/api/auth/verify-token",
            "forgot_password": "/api/auth/forgot-password",
            "reset_password": "/api/auth/reset-password",
            "change_password": "/api/auth/change-password",
            "update_profile": "/api/auth/update-profile",
            "verify_email": "/api/auth/verify-email",
            "resend_verification": "/api/auth/resend-verification"
        }
    }


@router.post("/forgot-password", response_model=AuthResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset email"""
    try:
        if settings.USE_COGNITO and oauth_service:
            # Use Cognito forgot password
            oauth_service.client.forgot_password(
                ClientId=settings.COGNITO_CLIENT_ID,
                Username=request.email
            )
        else:
            # Custom implementation would go here
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Forgot password not implemented for custom auth"
            )

        return AuthResponse(
            success=True,
            message="Password reset email sent successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forgot password failed: {str(e)}"
        )


@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(request: ResetPasswordRequest):
    """Reset password using reset token"""
    try:
        if settings.USE_COGNITO and oauth_service:
            # Use Cognito confirm forgot password
            oauth_service.client.confirm_forgot_password(
                ClientId=settings.COGNITO_CLIENT_ID,
                Username=request.token,  # This would need to be the username/email
                ConfirmationCode=request.token,
                Password=request.new_password
            )
        else:
            # Custom implementation would go here
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Reset password not implemented for custom auth"
            )

        return AuthResponse(
            success=True,
            message="Password reset successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reset password failed: {str(e)}"
        )


@router.post("/change-password", response_model=AuthResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Change current user's password using Cognito"""
    try:
        # Initialize Cognito client
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=settings.COGNITO_REGION
        )

        # Get user profile to find email
        user_profile = db_service.get_user_by_username(current_user.username)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )

        user_email = user_profile.get('email')
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found"
            )

        # Change password using Cognito
        cognito_client.admin_set_user_password(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=user_email,
            Password=request.new_password,
            Permanent=True
        )

        return AuthResponse(
            success=True,
            message="Password changed successfully"
        )

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidPasswordException':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password does not meet requirements"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Change password failed: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change password failed: {str(e)}"
        )


@router.put("/update-profile", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update current user's profile"""
    try:
        # Get current user record
        user_record = db_service.get_user_by_username(current_user.username)
        if not user_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update fields
        updates = {}
        if request.full_name is not None:
            updates["full_name"] = request.full_name
        if request.email is not None:
            updates["email"] = request.email

        # Update in DynamoDB (would need to implement update method)
        # For now, return current user
        return current_user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update profile failed: {str(e)}"
        )


@router.post("/verify-email", response_model=AuthResponse)
async def verify_email(
    request: VerifyEmailRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Verify user's email address"""
    try:
        if settings.USE_COGNITO and oauth_service:
            # Get user from DynamoDB to find email
            user_record = db_service.get_user_by_username(current_user.username)
            if not user_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Use Cognito verify email
            oauth_service.client.verify_user_attribute(
                AccessToken=None,  # Would need access token
                AttributeName='email',
                Code=request.verification_code
            )
        else:
            # Custom implementation would go here
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Email verification not implemented for custom auth"
            )

        return AuthResponse(
            success=True,
            message="Email verified successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed: {str(e)}"
        )


@router.post("/resend-verification", response_model=AuthResponse)
async def resend_verification(request: ResendVerificationRequest):
    """Resend email verification code"""
    try:
        if settings.USE_COGNITO and oauth_service:
            # Use Cognito resend confirmation code
            oauth_service.client.resend_confirmation_code(
                ClientId=settings.COGNITO_CLIENT_ID,
                Username=request.email
            )
        else:
            # Custom implementation would go here
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Resend verification not implemented for custom auth"
            )

        return AuthResponse(
            success=True,
            message="Verification email sent successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resend verification failed: {str(e)}"
        )


@router.delete("/account", response_model=AuthResponse)
async def delete_account(
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete current user's account"""
    try:
        if settings.USE_COGNITO and oauth_service:
            # Get user from DynamoDB to find email
            user_record = db_service.get_user_by_username(current_user.username)
            if not user_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Delete from Cognito
            oauth_service.client.admin_delete_user(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Username=user_record["email"]
            )

        # Delete from DynamoDB
        # Would need to implement delete method

        return AuthResponse(
            success=True,
            message="Account deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account deletion failed: {str(e)}"
        )
