"""
Human-like random delays to avoid detection.
"""
import asyncio
import random
from typing import Tuple


def random_delay(min_sec: float = 2.0, max_sec: float = 8.0) -> float:
    """Return a random delay in seconds between min_sec and max_sec."""
    return random.uniform(min_sec, max_sec)


async def async_random_delay(
    min_sec: float = 2.0,
    max_sec: float = 8.0,
) -> None:
    """Sleep for a random duration (human behavior simulation)."""
    delay = random_delay(min_sec, max_sec)
    await asyncio.sleep(delay)


def scroll_delay() -> Tuple[float, float]:
    """Return (min, max) seconds for scroll simulation between actions."""
    return (0.5, 2.0)
