from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://kreeda_user:kreeda_pass@localhost:5432/kreeda_db"
    redis_url: str = "redis://localhost:6379"
    jwt_secret: str = "default-secret-change-this"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour
    app_env: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()