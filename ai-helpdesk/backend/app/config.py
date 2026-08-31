from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AI Helpdesk"
    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    database_url: str = "sqlite:///./helpdesk.db"

    ai_provider: str = "mock"
    ai_model: str = "mock-v1"
    ai_api_key: str = ""
    ai_timeout_seconds: int = 30

    ai_validation_threshold: float = 0.80
    ai_duplicate_threshold: float = 0.90
    default_it_queue: str = "general"
    notification_enabled: bool = True

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
