"""
Kreeda Backend Core Configuration
Built for speed, reliability, and cricket scoring accuracy
"""
import os
import secrets
from typing import List, Any, Optional
from pydantic import BaseModel, Field, validator


class Settings(BaseModel):
    """Application settings with proper validation and environment support"""
    
    # App Info
    APP_NAME: str = "Kreeda Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    
    # Database - DynamoDB Configuration (NoSQL)
    DYNAMODB_ENDPOINT_URL: Optional[str] = Field(
        default=None,
        description="DynamoDB endpoint URL for local development"
    )
    DYNAMODB_TABLE: str = Field(
        default="kreeda-cricket-data",
        description="DynamoDB table name for cricket data"
    )
    
    # AWS Configuration for DynamoDB
    AWS_REGION: str = Field(
        default="us-east-1",
        description="AWS region for DynamoDB"
    )
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        default=None,
        description="AWS Access Key ID"
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default=None,
        description="AWS Secret Access Key"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="JWT secret key"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, le=1440)
    
    # Authentication settings
    USE_COGNITO: bool = Field(default=False, description="Use AWS Cognito for authentication")
    COGNITO_USER_POOL_ID: Optional[str] = Field(default=None, description="Cognito User Pool ID")
    COGNITO_CLIENT_ID: Optional[str] = Field(default=None, description="Cognito Client ID")
    COGNITO_REGION: str = Field(default="us-east-1", description="Cognito region")
    
    # CORS - More restrictive by default
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000", 
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080"
        ],
        description="Allowed CORS origins"
    )
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, ge=10, le=300)
    WS_MAX_CONNECTIONS_PER_MATCH: int = Field(default=100, ge=1, le=1000)
    
    # API Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=1)
    
    # Cricket Specific Settings
    MAX_OVERS_PER_INNINGS: int = Field(default=50, ge=1, le=50)
    MAX_RUNS_PER_BALL: int = Field(default=6, ge=0, le=6)
    
    @validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v):
        if v == "your-secret-key-change-this-in-production":
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError("Must set a proper SECRET_KEY in production")
        return v
    
    # Environment-specific settings
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")
    
    # CORS - Environment-specific configuration
    @validator('BACKEND_CORS_ORIGINS', pre=True)
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and not v.startswith('['):
            return [i.strip() for i in v.split(',')]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            return [v]
        
        # Environment-specific defaults
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production":
            # Production: Only allow specific domains
            return [
                "https://kreeda.cloudsbay.com",
                "https://www.kreeda.cloudsbay.com",
                "https://app.kreeda.cloudsbay.com"
            ]
        else:
            # Development: Allow localhost
            return [
                "http://localhost:3000", 
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
                "http://localhost:5173",  # Vite dev server
                "http://localhost:5174"   # Alternative Vite port
            ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in environment


def get_settings() -> Settings:
    """Get application settings - properly testable"""
    # Load from environment variables
    env_data = {}
    for field_name in Settings.__fields__:
        env_value = os.getenv(field_name)
        if env_value is not None:
            env_data[field_name] = env_value
    
    return Settings(**env_data)


# Global settings instance - but now it's a function call for testability
settings = get_settings()
