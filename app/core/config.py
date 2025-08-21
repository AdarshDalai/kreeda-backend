from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import os


class Settings(BaseSettings):
    """Application settings configuration."""
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Kreeda API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Mobile-first sports scorekeeping and tournament management platform"
    
    # Database Configuration
    DATABASE_URL: str
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Compatibility aliases for auth service
    @property
    def SECRET_KEY(self) -> str:
        return self.JWT_SECRET_KEY
    
    @property
    def ALGORITHM(self) -> str:
        return self.JWT_ALGORITHM
    
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    
    @property
    def REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        return self.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_PRIVATE_KEY: Optional[str] = None
    APPLE_KEY_ID: Optional[str] = None
    APPLE_TEAM_ID: Optional[str] = None
    
    # Email Configuration (for verification and password reset)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://kreeda.vercel.app"
    ]
    
    # Security
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
