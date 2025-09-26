"""
Kreeda Backend Configuration

Centralized configuration management using Pydantic Settings
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # App Configuration
    APP_NAME: str = Field(default="Kreeda Backend", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    ENVIRONMENT: str = Field(default="development", description="Environment (development/staging/production)")
    DEBUG: bool = Field(default=True, description="Debug mode")
    PORT: int = Field(default=8000, description="Server port")

    # Security
    SECRET_KEY: str = Field(description="Secret key for JWT encoding")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration in days")
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080", "http://localhost:5173"],
        description="Allowed CORS origins"
    )

    # Database Configuration
    DATABASE_URL: str = Field(description="PostgreSQL database URL")
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Database connection pool overflow")

    # Redis Configuration
    REDIS_URL: str = Field(description="Redis URL for caching and sessions")
    REDIS_MAX_CONNECTIONS: int = Field(default=10, description="Redis connection pool size")
    
    # Upstash Redis (optional alternative)
    UPSTASH_REDIS_URL: Optional[str] = Field(default=None, description="Upstash Redis URL")
    UPSTASH_REDIS_TOKEN: Optional[str] = Field(default=None, description="Upstash Redis token")

    # Supabase Configuration
    SUPABASE_URL: str = Field(description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(description="Supabase anonymous key")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(description="Supabase service role key")

    # Cloudflare R2 Configuration
    R2_ACCOUNT_ID: Optional[str] = Field(default=None, description="Cloudflare R2 Account ID")
    R2_ACCESS_KEY_ID: Optional[str] = Field(default=None, description="Cloudflare R2 Access Key")
    R2_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, description="Cloudflare R2 Secret Key")
    R2_BUCKET_NAME: Optional[str] = Field(default=None, description="Cloudflare R2 Bucket Name")
    R2_PUBLIC_URL: Optional[str] = Field(default=None, description="Cloudflare R2 Public URL")

    # WebSocket Configuration
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(default=30, description="WebSocket heartbeat interval in seconds")
    WEBSOCKET_MAX_CONNECTIONS: int = Field(default=1000, description="Maximum WebSocket connections")

    # Cricket Specific Configuration
    CRICKET_MAX_OVERS_PER_INNINGS: int = Field(default=50, description="Maximum overs per innings")
    CRICKET_BALLS_PER_OVER: int = Field(default=6, description="Balls per over")
    CRICKET_MAX_WICKETS: int = Field(default=10, description="Maximum wickets per innings")

    # Scoring Integrity Configuration
    DUAL_SCORER_REQUIRED: bool = Field(default=True, description="Require dual scorers for matches")
    SCORE_SYNC_TIMEOUT_SECONDS: int = Field(default=30, description="Score synchronization timeout")
    DISPUTE_RESOLUTION_TIMEOUT_MINUTES: int = Field(default=5, description="Dispute resolution timeout")

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=100, description="Rate limit per minute per IP")
    RATE_LIMIT_BURST: int = Field(default=200, description="Rate limit burst capacity")

    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        """Validate environment values"""
        valid_environments = ['development', 'staging', 'production']
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {valid_environments}')
        return v

    @validator('ALLOWED_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT == "production"

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL (for Alembic)"""
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def effective_redis_url(self) -> str:
        """Get the effective Redis URL (prefer Upstash if available)"""
        if self.UPSTASH_REDIS_URL:
            return self.UPSTASH_REDIS_URL
        return self.REDIS_URL


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()