import json
import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App Configuration
    app_name: str
    app_version: str
    environment: str
    debug: bool
    port: int

    # Database
    database_url: str

    # Redis Configuration
    redis_url: str
    upstash_redis_url: str
    upstash_redis_token: str

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Security & JWT
    secret_key: str
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int
    jwt_refresh_token_expire_days: int

    # Cloudflare R2
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_account_id: str
    r2_bucket_name: str
    r2_endpoint_url: str

    # CORS
    backend_cors_origins: str

    # Logging
    log_level: str
    log_format: str

    # WebSocket
    ws_heartbeat_interval: int

    # API
    api_v1_str: str
    project_name: str
    project_version: str

    @property
    def allowed_origins(self) -> List[str]:
        """Parse CORS origins from string to list"""
        try:
            return json.loads(self.backend_cors_origins)
        except (json.JSONDecodeError, TypeError):
            # Fallback to default if parsing fails
            return ["http://localhost:3000", "http://localhost:8080"]


settings = Settings()  # type: ignore
