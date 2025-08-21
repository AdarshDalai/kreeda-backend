from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from urllib.parse import urlparse, parse_qs
import logging

from app.core.database import get_db
from app.core.oauth2 import oauth2_service, OAuth2Token, OAuth2Scope
from app.repositories.user import user_repository
from app.schemas.auth import UserResponse
from app.services.auth import auth_service
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/authorize")
async def authorize_endpoint(
    response_type: str = Query(..., description="Must be 'code'"),
    client_id: str = Query(..., description="OAuth2 client identifier"),
    redirect_uri: str = Query(..., description="Client redirect URI"),
    scope: str = Query("read", description="Requested scopes"),
    state: Optional[str] = Query(None, description="State parameter for CSRF protection"),
    code_challenge: Optional[str] = Query(None, description="PKCE code challenge"),
    code_challenge_method: Optional[str] = Query("S256", description="PKCE code challenge method"),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 Authorization Endpoint (RFC 6749 Section 3.1)
    
    This endpoint is used to obtain authorization from the resource owner.
    """
    try:
        # Validate response type
        if response_type != "code":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="unsupported_response_type"
            )
        
        # Validate client
        client = oauth2_service.get_client(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid_client"
            )
        
        # Validate redirect URI
        if not oauth2_service.validate_redirect_uri(client_id, redirect_uri):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_redirect_uri"
            )
        
        # Parse and validate scopes
        requested_scopes = scope.split() if scope else []
        if not oauth2_service.validate_scope(client_id, requested_scopes):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_scope"
            )
        
        # In a real application, you would:
        # 1. Check if user is authenticated
        # 2. Show consent screen if needed
        # 3. Handle user approval/denial
        
        # For demo purposes, return a simple HTML form for user authentication
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Kreeda OAuth2 Authorization</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .form-group {{ margin: 15px 0; }}
                input {{ width: 100%; padding: 8px; margin: 5px 0; box-sizing: border-box; }}
                button {{ background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }}
                .scope {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <h2>Authorize {client.client_name}</h2>
            <p>This application is requesting permission to access your account.</p>
            
            <div>
                <h3>Requested Permissions:</h3>
                {"".join([f'<div class="scope">• {scope}</div>' for scope in requested_scopes])}
            </div>
            
            <form method="post" action="/api/v1/auth/oauth2/authorize">
                <input type="hidden" name="response_type" value="{response_type}">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="scope" value="{scope}">
                <input type="hidden" name="state" value="{state or ''}">
                <input type="hidden" name="code_challenge" value="{code_challenge or ''}">
                <input type="hidden" name="code_challenge_method" value="{code_challenge_method or ''}">
                
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label>Password:</label>
                    <input type="password" name="password" required>
                </div>
                
                <button type="submit" name="action" value="approve">Authorize</button>
                <button type="submit" name="action" value="deny" style="background: #dc3545; margin-left: 10px;">Deny</button>
            </form>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authorization endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="server_error"
        )


@router.post("/authorize")
async def authorize_post(
    request: Request,
    response_type: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form("read"),
    state: Optional[str] = Form(None),
    code_challenge: Optional[str] = Form(None),
    code_challenge_method: Optional[str] = Form("S256"),
    email: str = Form(...),
    password: str = Form(...),
    action: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle OAuth2 authorization form submission.
    """
    try:
        # Check if user denied authorization
        if action == "deny":
            error_params = "error=access_denied"
            if state:
                error_params += f"&state={state}"
            return RedirectResponse(f"{redirect_uri}?{error_params}")
        
        # Authenticate user
        user = await user_repository.get_user_by_email(db, email)
        if not user or not user.hashed_password or not auth_service.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Generate authorization code
        requested_scopes = scope.split() if scope else []
        auth_code = oauth2_service.generate_authorization_code(
            client_id=client_id,
            user_id=str(user.id),
            redirect_uri=redirect_uri,
            scopes=requested_scopes,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )
        
        # Redirect to client with authorization code
        redirect_params = f"code={auth_code}"
        if state:
            redirect_params += f"&state={state}"
            
        return RedirectResponse(f"{redirect_uri}?{redirect_params}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authorization post error: {str(e)}")
        error_params = "error=server_error"
        if state:
            error_params += f"&state={state}"
        return RedirectResponse(f"{redirect_uri}?{error_params}")


@router.post("/token", response_model=OAuth2Token)
async def token_endpoint(
    grant_type: str = Form(..., description="Grant type (authorization_code, refresh_token, password)"),
    client_id: str = Form(..., description="OAuth2 client identifier"),
    client_secret: str = Form(..., description="OAuth2 client secret"),
    code: Optional[str] = Form(None, description="Authorization code (for authorization_code grant)"),
    redirect_uri: Optional[str] = Form(None, description="Redirect URI (for authorization_code grant)"),
    refresh_token: Optional[str] = Form(None, description="Refresh token (for refresh_token grant)"),
    username: Optional[str] = Form(None, description="Username (for password grant)"),
    password: Optional[str] = Form(None, description="Password (for password grant)"),
    scope: Optional[str] = Form(None, description="Requested scope"),
    code_verifier: Optional[str] = Form(None, description="PKCE code verifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 Token Endpoint (RFC 6749 Section 3.2)
    
    This endpoint is used by the client to obtain an access token.
    """
    try:
        # Validate client credentials
        if not oauth2_service.validate_client_credentials(client_id, client_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid_client",
                headers={"WWW-Authenticate": "Basic"}
            )
        
        # Validate grant type
        if not oauth2_service.validate_token_request(grant_type, client_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="unsupported_grant_type"
            )
        
        user = None
        requested_scopes = []
        
        if grant_type == "authorization_code":
            # Authorization Code Grant (RFC 6749 Section 4.1)
            if not code or not redirect_uri:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="invalid_request"
                )
            
            # Validate authorization code
            auth_code_data = oauth2_service.validate_authorization_code(
                code, client_id, redirect_uri, code_verifier
            )
            
            if not auth_code_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="invalid_grant"
                )
            
            # Get user
            user = await user_repository.get_user_by_id(db, auth_code_data.user_id)
            requested_scopes = auth_code_data.scopes
            
        elif grant_type == "refresh_token":
            # Refresh Token Grant (RFC 6749 Section 6)
            if not refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="invalid_request"
                )
            
            try:
                # Verify refresh token
                token_data = auth_service.verify_token(refresh_token)
                payload = auth_service.decode_token(refresh_token)
                
                if payload.get("type") != "refresh":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="invalid_grant"
                    )
                
                # Get user
                user = await user_repository.get_user_by_id(db, token_data.sub)
                
                # Use requested scope or original scope
                if scope:
                    requested_scopes = scope.split()
                else:
                    requested_scopes = payload.get("scope", "read").split()
                    
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="invalid_grant"
                )
        
        elif grant_type == "password":
            # Resource Owner Password Credentials Grant (RFC 6749 Section 4.3)
            if not username or not password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="invalid_request"
                )
            
            # Authenticate user
            user = await user_repository.get_user_by_email(db, username)
            if not user or not user.hashed_password or not auth_service.verify_password(password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="invalid_grant"
                )
            
            # Use requested scope or default
            requested_scopes = scope.split() if scope else [OAuth2Scope.READ, OAuth2Scope.PROFILE]
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="unsupported_grant_type"
            )
        
        # Validate user
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_grant"
            )
        
        # Validate scopes
        if not oauth2_service.validate_scope(client_id, requested_scopes):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid_scope"
            )
        
        # Create tokens
        token_response = oauth2_service.create_oauth2_tokens(user, client_id, requested_scopes)
        
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="server_error"
        )


@router.post("/introspect")
async def token_introspection(
    token: str = Form(..., description="Token to introspect"),
    token_type_hint: Optional[str] = Form(None, description="Hint about token type"),
    client_id: str = Form(..., description="OAuth2 client identifier"),
    client_secret: str = Form(..., description="OAuth2 client secret")
):
    """
    OAuth2 Token Introspection Endpoint (RFC 7662)
    
    This endpoint allows authorized clients to query the authorization 
    server to determine the set of metadata for a given token.
    """
    try:
        # Validate client credentials
        if not oauth2_service.validate_client_credentials(client_id, client_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid_client"
            )
        
        # Introspect token
        introspection_response = oauth2_service.introspect_token(token)
        
        return introspection_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token introspection error: {str(e)}")
        return {"active": False}


@router.post("/revoke")
async def token_revocation(
    token: str = Form(..., description="Token to revoke"),
    token_type_hint: Optional[str] = Form(None, description="Hint about token type"),
    client_id: str = Form(..., description="OAuth2 client identifier"),
    client_secret: str = Form(..., description="OAuth2 client secret")
):
    """
    OAuth2 Token Revocation Endpoint (RFC 7009)
    
    This endpoint allows clients to notify the authorization server 
    that a given token is no longer needed.
    """
    try:
        # Validate client credentials
        if not oauth2_service.validate_client_credentials(client_id, client_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid_client"
            )
        
        # Revoke token
        success = oauth2_service.revoke_token(token, token_type_hint)
        
        # According to RFC 7009, the revocation endpoint responds with HTTP 200
        # regardless of whether the token was successfully revoked
        return {"success": success}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token revocation error: {str(e)}")
        return {"success": False}


@router.get("/.well-known/oauth2-configuration")
async def oauth2_discovery():
    """
    OAuth2 Authorization Server Metadata (RFC 8414)
    
    This endpoint provides metadata about the OAuth2 authorization server.
    """
    base_url = "http://localhost:8000/api/v1/auth/oauth2"  # In production, use proper URL
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
        "token_endpoint_auth_signing_alg_values_supported": ["RS256", "HS256"],
        "userinfo_endpoint": f"{base_url}/userinfo",
        "registration_endpoint": f"{base_url}/register",
        "scopes_supported": [
            OAuth2Scope.READ,
            OAuth2Scope.WRITE,
            OAuth2Scope.DELETE,
            OAuth2Scope.ADMIN,
            OAuth2Scope.PROFILE,
            OAuth2Scope.EMAIL
        ],
        "response_types_supported": ["code", "token"],
        "grant_types_supported": ["authorization_code", "refresh_token", "password", "client_credentials"],
        "code_challenge_methods_supported": ["S256", "plain"],
        "revocation_endpoint": f"{base_url}/revoke",
        "introspection_endpoint": f"{base_url}/introspect",
        "response_modes_supported": ["query", "fragment"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256", "HS256"]
    }


@router.get("/userinfo", response_model=UserResponse)
async def userinfo_endpoint(
    current_user: User = Depends(lambda: None),  # TODO: Implement OAuth2 user dependency
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 UserInfo Endpoint (OpenID Connect Core 1.0)
    
    This endpoint returns claims about the authenticated user.
    """
    # This is a placeholder - you would implement proper OAuth2 token validation here
    # For now, return an error since we haven't implemented the OAuth2 user dependency
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="UserInfo endpoint not yet implemented with OAuth2 token validation"
    )
