"""
Device fingerprint for browser context (user-agent, viewport).
Reduces detection risk by consistent device profile per account.
"""
import random
from typing import Any, Dict, Optional

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

DEVICE_MODELS = ["Desktop", "Windows PC", "MacBook"]
OPERATING_SYSTEMS = ["Windows 10", "Windows 11", "Mac OS X 10.15", "Mac OS X 12"]
SCREEN_RESOLUTIONS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
]
TIMEZONES = ["America/New_York", "America/Los_Angeles", "Europe/London", "Asia/Kolkata", "UTC"]
LANGUAGES = ["en-US", "en-GB", "en"]


def generate_device_profile() -> Dict[str, Any]:
    """Generate a random device profile for first-time connect. Stored per account and reused."""
    viewport = random.choice(SCREEN_RESOLUTIONS)
    ua = random.choice(USER_AGENTS)
    return {
        "device_model": random.choice(DEVICE_MODELS),
        "operating_system": random.choice(OPERATING_SYSTEMS),
        "user_agent": ua,
        "screen_resolution": f"{viewport['width']}x{viewport['height']}",
        "timezone": random.choice(TIMEZONES),
        "language": random.choice(LANGUAGES),
        "viewport": viewport,
        "locale": random.choice(LANGUAGES),
        "timezone_id": random.choice(TIMEZONES),
    }


def get_device_profile(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a device profile for Playwright context (fallback when account has no stored profile)."""
    profile = generate_device_profile()
    if overrides:
        profile.update(overrides)
    return profile
