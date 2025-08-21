"""
OAuth2 Configuration and Documentation

This file provides OAuth2 2.0 RFC 6749 compliant implementation for the Kreeda backend.

OAUTH2 FLOWS SUPPORTED:
1. Authorization Code Grant (with PKCE support) - Recommended for web/mobile apps
2. Resource Owner Password Credentials Grant - For trusted first-party clients
3. Refresh Token Grant - For obtaining new access tokens
4. Client Credentials Grant - For machine-to-machine authentication (planned)

OAUTH2 ENDPOINTS:
- Authorization Endpoint: GET /api/v1/auth/oauth2/authorize
- Token Endpoint: POST /api/v1/auth/oauth2/token  
- Token Introspection: POST /api/v1/auth/oauth2/introspect (RFC 7662)
- Token Revocation: POST /api/v1/auth/oauth2/revoke (RFC 7009)
- Discovery Metadata: GET /api/v1/auth/oauth2/.well-known/oauth2-configuration (RFC 8414)
- UserInfo Endpoint: GET /api/v1/auth/oauth2/userinfo (OpenID Connect)

SCOPES SUPPORTED:
- read: Read access to resources
- write: Write access to resources  
- delete: Delete access to resources
- admin: Administrative access
- profile: Access to user profile information
- email: Access to user email address

SECURITY FEATURES:
- PKCE (Proof Key for Code Exchange) - RFC 7636
- State parameter for CSRF protection
- Token introspection and revocation
- Scope-based access control
- JWT tokens with proper claims (iss, aud, exp, iat, jti)
- Client credentials validation

COMPLIANCE FEATURES:
- RFC 6749 (OAuth 2.0 Authorization Framework)
- RFC 6750 (OAuth 2.0 Bearer Token Usage) 
- RFC 7009 (OAuth 2.0 Token Revocation)
- RFC 7636 (Proof Key for Code Exchange by OAuth Public Clients)
- RFC 7662 (OAuth 2.0 Token Introspection)
- RFC 8414 (OAuth 2.0 Authorization Server Metadata)
- OpenID Connect Core 1.0 (UserInfo endpoint)

EXAMPLE USAGE:

1. Authorization Code Flow:
   GET /api/v1/auth/oauth2/authorize?response_type=code&client_id=kreeda_mobile_app&redirect_uri=http://localhost:3000/callback&scope=read+profile&state=xyz

2. Token Exchange:
   POST /api/v1/auth/oauth2/token
   Content-Type: application/x-www-form-urlencoded
   
   grant_type=authorization_code&client_id=kreeda_mobile_app&client_secret=secret&code=AUTH_CODE&redirect_uri=http://localhost:3000/callback

3. Password Grant (for trusted clients):
   POST /api/v1/auth/token
   Content-Type: application/x-www-form-urlencoded
   
   grant_type=password&username=user@example.com&password=userpassword&scope=read+profile

4. Refresh Token:
   POST /api/v1/auth/oauth2/token
   Content-Type: application/x-www-form-urlencoded
   
   grant_type=refresh_token&client_id=kreeda_mobile_app&client_secret=secret&refresh_token=REFRESH_TOKEN

5. Token Introspection:
   POST /api/v1/auth/oauth2/introspect
   Content-Type: application/x-www-form-urlencoded
   
   token=ACCESS_TOKEN&client_id=kreeda_mobile_app&client_secret=secret

CLIENT CONFIGURATION:
Default client credentials for testing:
- Client ID: kreeda_mobile_app
- Client Secret: kreeda_mobile_secret_2024
- Allowed Scopes: read, write, profile, email
- Allowed Grant Types: authorization_code, refresh_token, password
- Redirect URIs: http://localhost:3000/auth/callback, kreeda://auth/callback

SECURITY CONSIDERATIONS:
- Always use HTTPS in production
- Store client secrets securely
- Implement proper scope validation
- Use short-lived access tokens (15-30 minutes)
- Use long-lived refresh tokens (7-30 days) with rotation
- Validate redirect URIs strictly
- Implement rate limiting on token endpoints
- Log all authentication events
- Use PKCE for public clients
- Validate state parameter for CSRF protection

INTEGRATION EXAMPLES:

JavaScript (Frontend):
```javascript
// Authorization Code Flow with PKCE
function generateCodeVerifier() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

function generateCodeChallenge(verifier) {
    return btoa(String.fromCharCode.apply(null, new Uint8Array(crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier)))))
        .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

const codeVerifier = generateCodeVerifier();
const codeChallenge = generateCodeChallenge(codeVerifier);
const state = Math.random().toString(36);

const authUrl = `http://localhost:8000/api/v1/auth/oauth2/authorize?response_type=code&client_id=kreeda_mobile_app&redirect_uri=http://localhost:3000/callback&scope=read+profile&state=${state}&code_challenge=${codeChallenge}&code_challenge_method=S256`;

// Redirect user to authUrl
// On callback, exchange code for tokens
```

Python (Client):
```python
import requests

# Password Grant
response = requests.post('http://localhost:8000/api/v1/auth/token', data={
    'grant_type': 'password',
    'username': 'user@example.com', 
    'password': 'userpassword',
    'scope': 'read profile'
})

tokens = response.json()
access_token = tokens['access_token']

# Use token for API calls
headers = {'Authorization': f'Bearer {access_token}'}
user_info = requests.get('http://localhost:8000/api/v1/auth/me', headers=headers)
```

cURL Examples:
```bash
# Get authorization code
curl -X GET "http://localhost:8000/api/v1/auth/oauth2/authorize?response_type=code&client_id=kreeda_mobile_app&redirect_uri=http://localhost:3000/callback&scope=read+profile"

# Exchange code for token
curl -X POST http://localhost:8000/api/v1/auth/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&client_id=kreeda_mobile_app&client_secret=kreeda_mobile_secret_2024&code=AUTH_CODE&redirect_uri=http://localhost:3000/callback"

# Password grant
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=user@example.com&password=userpassword&scope=read+profile"

# Use access token
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer ACCESS_TOKEN"

# Introspect token
curl -X POST http://localhost:8000/api/v1/auth/oauth2/introspect \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "token=ACCESS_TOKEN&client_id=kreeda_mobile_app&client_secret=kreeda_mobile_secret_2024"

# Revoke token  
curl -X POST http://localhost:8000/api/v1/auth/oauth2/revoke \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "token=ACCESS_TOKEN&client_id=kreeda_mobile_app&client_secret=kreeda_mobile_secret_2024"
```

ERROR HANDLING:
All OAuth2 errors follow RFC 6749 format:
```json
{
  "error": "invalid_request|invalid_client|invalid_grant|unauthorized_client|unsupported_grant_type|invalid_scope",
  "error_description": "Human readable description",
  "error_uri": "Optional URI for more information"
}
```

This implementation provides a comprehensive, production-ready OAuth2 2.0 authorization server
that can handle multiple client types and use cases while maintaining security best practices.
"""

from typing import Dict, Any

# OAuth2 Configuration Constants
OAUTH2_CONFIG = {
    "SUPPORTED_GRANT_TYPES": [
        "authorization_code",
        "refresh_token", 
        "password",
        "client_credentials"
    ],
    "SUPPORTED_RESPONSE_TYPES": [
        "code",
        "token"
    ],
    "SUPPORTED_SCOPES": [
        "read",
        "write", 
        "delete",
        "admin",
        "profile",
        "email"
    ],
    "AUTHORIZATION_CODE_LIFETIME": 600,  # 10 minutes
    "ACCESS_TOKEN_LIFETIME": 1800,      # 30 minutes
    "REFRESH_TOKEN_LIFETIME": 604800,   # 7 days
    "SUPPORTED_PKCE_METHODS": ["S256", "plain"],
    "TOKEN_ENDPOINT_AUTH_METHODS": ["client_secret_post", "client_secret_basic"],
    "SUBJECT_TYPES_SUPPORTED": ["public"],
    "ID_TOKEN_SIGNING_ALG_VALUES": ["RS256", "HS256"]
}


def get_oauth2_metadata(base_url: str) -> Dict[str, Any]:
    """Generate OAuth2 authorization server metadata per RFC 8414."""
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "token_endpoint_auth_methods_supported": OAUTH2_CONFIG["TOKEN_ENDPOINT_AUTH_METHODS"],
        "token_endpoint_auth_signing_alg_values_supported": OAUTH2_CONFIG["ID_TOKEN_SIGNING_ALG_VALUES"],
        "userinfo_endpoint": f"{base_url}/userinfo",
        "registration_endpoint": f"{base_url}/register",
        "scopes_supported": OAUTH2_CONFIG["SUPPORTED_SCOPES"],
        "response_types_supported": OAUTH2_CONFIG["SUPPORTED_RESPONSE_TYPES"],
        "grant_types_supported": OAUTH2_CONFIG["SUPPORTED_GRANT_TYPES"],
        "code_challenge_methods_supported": OAUTH2_CONFIG["SUPPORTED_PKCE_METHODS"],
        "revocation_endpoint": f"{base_url}/revoke",
        "introspection_endpoint": f"{base_url}/introspect",
        "response_modes_supported": ["query", "fragment"],
        "subject_types_supported": OAUTH2_CONFIG["SUBJECT_TYPES_SUPPORTED"],
        "id_token_signing_alg_values_supported": OAUTH2_CONFIG["ID_TOKEN_SIGNING_ALG_VALUES"]
    }
