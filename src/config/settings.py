from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App environment
    app_env: str = "development"
    
    # Database configuration
    database_url: str = "postgresql+asyncpg://kreeda_user:kreeda_pass@localhost:5432/kreeda_db"
    db_host: Optional[str] = "localhost"
    db_port: Optional[str] = "5432"
    db_name: Optional[str] = "kreeda_db"
    db_user: Optional[str] = "kreeda_user"
    db_pass: Optional[str] = "kreeda_pass"
    db_pool_size: Optional[int] = 20
    db_max_overflow: Optional[int] = 50
    db_pool_timeout: Optional[int] = 30
    
    # Redis configuration
    redis_url: str = "redis://localhost:6379"
    
    # JWT configuration
    jwt_secret: str = "default-secret-change-this"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour
    
    # Security settings
    password_reset_token_expire_hours: Optional[int] = 1
    email_verification_token_expire_hours: Optional[int] = 24
    rate_limit_per_minute: Optional[int] = 60
    
    # Email configuration
    smtp_server: Optional[str] = ""
    smtp_port: Optional[int] = 587
    smtp_username: Optional[str] = ""
    smtp_password: Optional[str] = ""
    from_email: Optional[str] = "noreply@kreeda.app"
    
    # CORS origins
    allowed_origins: Optional[str] = "http://localhost:3000,http://localhost:3001"
    
    # Logging
    log_level: Optional[str] = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env

settings = Settings()