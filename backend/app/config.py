"""
Application configuration via environment variables.
Uses pydantic-settings for validation and type coercion.
"""
import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# In-memory override for testing mode (bypass anti-ban). Reset on server restart.
_testing_mode_override: Optional[bool] = None
# In-memory override for Instagram comment reply-all (reply to every comment). Reset on server restart.
_instagram_reply_all_override: Optional[bool] = None
_instagram_reply_all_message_override: Optional[str] = None
# Require follower for Comment-to-DM: only users in allowed list get the link; others get non_follower_message.
_instagram_require_follower_override: Optional[bool] = None
_instagram_non_follower_message_override: Optional[str] = None


def get_testing_mode() -> bool:
    """True = bypass warm-up, daily limits, paused_until; use short delays. For testing only."""
    if _testing_mode_override is not None:
        return _testing_mode_override
    return os.getenv("TESTING_MODE", "false").lower() in ("1", "true", "yes")


def set_testing_mode(enabled: bool) -> None:
    """Set testing mode (used by API toggle)."""
    global _testing_mode_override
    _testing_mode_override = enabled


def get_instagram_reply_all() -> bool:
    """True = reply to every comment with reply_all_message."""
    if _instagram_reply_all_override is not None:
        return _instagram_reply_all_override
    return os.getenv("INSTAGRAM_COMMENT_REPLY_ALL", "false").lower() in ("1", "true", "yes")


def set_instagram_reply_all(enabled: bool) -> None:
    global _instagram_reply_all_override
    _instagram_reply_all_override = enabled


def get_instagram_reply_all_message() -> Optional[str]:
    if _instagram_reply_all_message_override is not None:
        return _instagram_reply_all_message_override
    return os.getenv("INSTAGRAM_COMMENT_REPLY_ALL_MESSAGE") or None


def set_instagram_reply_all_message(message: Optional[str]) -> None:
    global _instagram_reply_all_message_override
    _instagram_reply_all_message_override = message


def get_instagram_require_follower() -> bool:
    """True = only send link to users in allowed list; others get non_follower_message."""
    if _instagram_require_follower_override is not None:
        return _instagram_require_follower_override
    return os.getenv("INSTAGRAM_COMMENT_DM_REQUIRE_FOLLOWER", "false").lower() in ("1", "true", "yes")


def set_instagram_require_follower(enabled: bool) -> None:
    global _instagram_require_follower_override
    _instagram_require_follower_override = enabled


def get_instagram_non_follower_message() -> Optional[str]:
    """Message to send when require_follower is on and commenter is not in allowed list."""
    if _instagram_non_follower_message_override is not None:
        return _instagram_non_follower_message_override
    return os.getenv("INSTAGRAM_COMMENT_DM_NON_FOLLOWER_MESSAGE") or (
        "I think you're not following me! Please follow and comment again to get the link."
    )


def set_instagram_non_follower_message(message: Optional[str]) -> None:
    global _instagram_non_follower_message_override
    _instagram_non_follower_message_override = message


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
    # CORS: comma-separated origins (e.g. https://app.example.com,https://www.example.com)
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

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
    daily_limit_comments: int = 10
    daily_limit_reel_views: int = 9999  # per account per day; one account can produce many views
    daily_limit_story_views: int = 30  # per account per day (warm-up / engagement)

    # Delay between actions (seconds) to mimic human behavior
    delay_between_actions_min_sec: int = 20
    delay_between_actions_max_sec: int = 60

    # Optional: Playwright (use "firefox" if Chromium crashes on macOS)
    playwright_headless: bool = True
    playwright_browser: str = "firefox"

    # Instagram Graph API (Business/Creator: DMs + Comments). Optional.
    instagram_app_id: Optional[str] = None
    instagram_app_secret: Optional[str] = None
    instagram_page_access_token: Optional[str] = None
    instagram_page_id: Optional[str] = None  # Facebook Page ID for Private Reply endpoint
    instagram_verify_token: Optional[str] = None
    instagram_api_version: str = "v19.0"
    # Comment-to-DM: keyword-only vs reply-to-all
    instagram_comment_reply_all: bool = False  # True = reply to every comment with reply_all_message
    instagram_comment_reply_all_message: str = "Thanks for commenting! We've sent you a message."
    # When reply_all=False: only reply when comment matches this regex
    instagram_comment_dm_keywords: str = r"\b(LINK|EBOOK|PRICE|DM)\b"
    instagram_comment_dm_reply: str = "We've sent the link to your DMs! Check your inbox."
    # When require_follower=True, only users in allowed list get the link; others get non_follower_message.
    instagram_comment_dm_require_follower: bool = False
    instagram_comment_dm_non_follower_message: str = (
        "I think you're not following me! Please follow and comment again to get the link."
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
