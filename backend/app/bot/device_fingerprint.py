"""
Device fingerprint for browser context (user-agent, viewport).
Reduces detection risk by consistent device profile.
"""
import random
from typing import Any, Dict, Optional

# Sample user agents (replace with your own list or load from file)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def get_device_profile(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a device profile for Playwright context."""
    profile = {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": {"width": 1920, "height": 1080},
        "locale": "en-US",
        "timezone_id": "America/New_York",
    }
    if overrides:
        profile.update(overrides)
    return profile
