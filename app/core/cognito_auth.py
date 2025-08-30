"""
AWS Cognito OAuth2 Authentication Service
Supports Google, Apple, and Cognito authentication
"""
import os
import jwt
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


class CognitoOAuth2Service:
    """AWS Cognito OAuth2 service with social providers"""

    def __init__(self):
        self.user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        self.client_id = os.environ.get('COGNITO_CLIENT_ID')
        self.region = os.environ.get('AWS_REGION', 'us-east-1')

        if not all([self.user_pool_id, self.client_id]):
            raise ValueError("Cognito configuration missing")

        self.client = boto3.client('cognito-idp', region_name=self.region)

    def authenticate_google_oauth(self, id_token: str) -> Dict[str, Any]:
        """
        Authenticate user with Google OAuth ID token
        """
        try:
            # Verify Google ID token
            google_user_info = self._verify_google_token(id_token)

            # Check if user exists in Cognito
            cognito_user = self._find_cognito_user_by_email(google_user_info['email'])

            if not cognito_user:
                # Create new user in Cognito
                cognito_user = self._create_cognito_user_from_google(google_user_info)

            # Generate access token
            access_token = self._generate_cognito_token(cognito_user['Username'])

            return {
                'access_token': access_token,
                'token_type': 'bearer',
                'user_info': {
                    'sub': cognito_user['Username'],
                    'email': google_user_info['email'],
                    'name': google_user_info.get('name'),
                    'provider': 'google'
                }
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Google authentication failed: {str(e)}"
            )

    def authenticate_apple_oauth(self, authorization_code: str, code_verifier: str) -> Dict[str, Any]:
        """
        Authenticate user with Apple Sign-In
        """
        try:
            # Exchange authorization code for tokens
            token_response = self._exchange_apple_code(authorization_code, code_verifier)

            # Verify and decode ID token
            apple_user_info = self._verify_apple_token(token_response['id_token'])

            # Check if user exists in Cognito
            cognito_user = self._find_cognito_user_by_email(apple_user_info['email'])

            if not cognito_user:
                # Create new user in Cognito
                cognito_user = self._create_cognito_user_from_apple(apple_user_info)

            # Generate access token
            access_token = self._generate_cognito_token(cognito_user['Username'])

            return {
                'access_token': access_token,
                'token_type': 'bearer',
                'user_info': {
                    'sub': cognito_user['Username'],
                    'email': apple_user_info['email'],
                    'name': apple_user_info.get('name'),
                    'provider': 'apple'
                }
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Apple authentication failed: {str(e)}"
            )

    def authenticate_cognito_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with Cognito username/password
        """
        try:
            response = self.client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )

            if 'AuthenticationResult' in response:
                auth_result = response['AuthenticationResult']
                return {
                    'access_token': auth_result['AccessToken'],
                    'refresh_token': auth_result.get('RefreshToken'),
                    'token_type': 'bearer',
                    'expires_in': auth_result.get('ExpiresIn', 3600)
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed"
                )

        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

    def _verify_google_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Google OAuth ID token"""
        # Google OAuth verification
        google_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
        response = requests.get(google_cert_url)
        certs = response.json()

        # Decode and verify token
        header = jwt.get_unverified_header(id_token)
        cert = certs[header['kid']]

        payload = jwt.decode(
            id_token,
            cert,
            algorithms=['RS256'],
            audience=os.environ.get('GOOGLE_CLIENT_ID'),
            issuer='https://accounts.google.com'
        )

        return {
            'email': payload['email'],
            'name': payload.get('name'),
            'given_name': payload.get('given_name'),
            'family_name': payload.get('family_name'),
            'sub': payload['sub']
        }

    def _verify_apple_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Apple Sign-In ID token"""
        # Apple token verification (simplified)
        # In production, you'd verify against Apple's public keys
        payload = jwt.decode(id_token, options={"verify_signature": False})

        return {
            'email': payload.get('email'),
            'name': payload.get('name'),
            'sub': payload['sub']
        }

    def _exchange_apple_code(self, authorization_code: str, code_verifier: str) -> Dict[str, Any]:
        """Exchange Apple authorization code for tokens"""
        apple_token_url = "https://appleid.apple.com/auth/token"

        data = {
            'client_id': os.environ.get('APPLE_CLIENT_ID'),
            'client_secret': self._generate_apple_client_secret(),
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'code_verifier': code_verifier
        }

        response = requests.post(apple_token_url, data=data)
        return response.json()

    def _generate_apple_client_secret(self) -> str:
        """Generate Apple client secret for token exchange"""
        # Implementation would generate JWT with Apple's private key
        # This is a placeholder
        return "apple_client_secret_jwt"

    def _find_cognito_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find Cognito user by email"""
        try:
            response = self.client.list_users(
                UserPoolId=self.user_pool_id,
                Filter=f'email = "{email}"'
            )

            if response['Users']:
                return response['Users'][0]
            return None

        except ClientError:
            return None

    def _create_cognito_user_from_google(self, google_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create Cognito user from Google OAuth info"""
        username = f"google_{google_info['sub']}"

        self.client.admin_create_user(
            UserPoolId=self.user_pool_id,
            Username=username,
            UserAttributes=[
                {'Name': 'email', 'Value': google_info['email']},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'given_name', 'Value': google_info.get('given_name', '')},
                {'Name': 'family_name', 'Value': google_info.get('family_name', '')},
            ],
            MessageAction='SUPPRESS'  # Don't send welcome email
        )

        # Set permanent password
        self.client.admin_set_user_password(
            UserPoolId=self.user_pool_id,
            Username=username,
            Password=self._generate_temp_password(),
            Permanent=True
        )

        return {'Username': username}

    def _create_cognito_user_from_apple(self, apple_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create Cognito user from Apple Sign-In info"""
        username = f"apple_{apple_info['sub']}"

        self.client.admin_create_user(
            UserPoolId=self.user_pool_id,
            Username=username,
            UserAttributes=[
                {'Name': 'email', 'Value': apple_info['email']},
                {'Name': 'email_verified', 'Value': 'true'},
            ],
            MessageAction='SUPPRESS'
        )

        # Set permanent password
        self.client.admin_set_user_password(
            UserPoolId=self.user_pool_id,
            Username=username,
            Password=self._generate_temp_password(),
            Permanent=True
        )

        return {'Username': username}

    def _generate_cognito_token(self, username: str) -> str:
        """Generate JWT token for authenticated user"""
        # In production, you'd use Cognito's built-in JWT tokens
        # This is a simplified version
        payload = {
            'sub': username,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1),
            'token_use': 'access'
        }

        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

    def _generate_temp_password(self) -> str:
        """Generate temporary password for social auth users"""
        import secrets
        return secrets.token_urlsafe(16)

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            response = self.client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )

            if 'AuthenticationResult' in response:
                auth_result = response['AuthenticationResult']
                return {
                    'access_token': auth_result['AccessToken'],
                    'token_type': 'bearer',
                    'expires_in': auth_result.get('ExpiresIn', 3600)
                }

            # If no authentication result, raise exception
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        except ClientError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )


# FastAPI OAuth2 integration
oauth2_scheme = HTTPBearer()

async def get_current_user_from_oauth(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """Get current user from OAuth2 token"""
    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get('sub')

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        return {'username': username, 'user_id': username}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
