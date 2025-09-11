from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App Configuration
    app_name: str = "Kreeda Backend"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    port: int = 8000

    # Database
    database_url: str = "postgresql://kreeda:password@localhost:5432/kreeda_dev"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Security & JWT
    secret_key: str = "your-secret-key"
    jwt_secret_key: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Cloudflare R2
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_account_id: str = ""
    r2_bucket_name: str = "kreeda-assets"
    r2_endpoint_url: str = ""

    # CORS
    backend_cors_origins: str = '["http://localhost:3000", "http://localhost:8080"]'
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # WebSocket
    ws_heartbeat_interval: int = 30

    # API
    api_v1_str: str = "/api/v1"
    project_name: str = "Kreeda API"
    project_version: str = "1.0.0"

    @property
    def allowed_origins(self) -> List[str]:
        """Parse CORS origins from string to list"""
        try:
            return json.loads(self.backend_cors_origins)
        except (json.JSONDecodeError, TypeError):
            # Fallback to default if parsing fails
            return ["http://localhost:3000", "http://localhost:8080"]


settings = Settings()
