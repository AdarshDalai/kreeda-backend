"""
Kreeda Backend Core Configuration
Built for speed, reliability, and cricket scoring accuracy
"""
import os
import secrets
from typing import List, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings with proper validation and environment support"""
    
    # App Info
    APP_NAME: str = "Kreeda Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://kreeda_user:kreeda_pass@localhost:5432/kreeda_db",
        description="PostgreSQL database URL"
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
    def validate_secret_key(cls, v):
        if v == "your-secret-key-change-this-in-production":
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError("Must set a proper SECRET_KEY in production")
        return v
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'postgresql+psycopg2://')):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v
    
    @validator('BACKEND_CORS_ORIGINS', pre=True)
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and not v.startswith('['):
            return [i.strip() for i in v.split(',')]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            return [v]
        return ["http://localhost:3000"]  # Safe default
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """Get application settings - properly testable"""
    return Settings()


# Global settings instance - but now it's a function call for testability
settings = get_settings()
settings = Settings()
