"""
Application configuration via environment variables.
Uses pydantic-settings for validation and type coercion.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Instagram Automation API"
    debug: bool = False

    # Database (set USE_SQLITE=1 for local dev without PostgreSQL)
    use_sqlite: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/instagram_automation"

    def get_database_url(self) -> str:
        if self.use_sqlite:
            return "sqlite+aiosqlite:///./instagram_automation.db"
        return self.database_url

    # Redis & Celery (set RUN_TASKS_INLINE=true to run tasks in API process, no Redis needed)
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    run_tasks_inline: bool = False

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Daily action limits (human behavior simulation)
    daily_limit_likes: int = 80
    daily_limit_follows: int = 40
    daily_limit_dms: int = 20
    daily_limit_comments: int = 20

    # Optional: Playwright (use "firefox" if Chromium crashes on macOS)
    playwright_headless: bool = True
    playwright_browser: str = "firefox"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
