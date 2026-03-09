"""
Instagram Graph API: read and moderate comments on posts.
Uses official Instagram Comment API (Business/Creator accounts).
"""
import logging
import time
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def _graph_base() -> str:
    s = get_settings()
    return f"https://graph.facebook.com/{s.instagram_api_version}"


def _access_token() -> Optional[str]:
    return get_settings().instagram_page_access_token


async def _graph_get(endpoint: str) -> dict[str, Any]:
    token = _access_token()
    if not token:
        raise ValueError("INSTAGRAM_PAGE_ACCESS_TOKEN not set")
    url = f"{_graph_base()}/{endpoint}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params={"access_token": token}, timeout=30.0)
    if resp.status_code == 429:
        raise Exception("Rate limited; retry later")
    if resp.status_code != 200:
        logger.warning("Instagram graph_get %s failed: %s %s", endpoint, resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json()


async def _graph_post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    token = _access_token()
    if not token:
        raise ValueError("INSTAGRAM_PAGE_ACCESS_TOKEN not set")
    url = f"{_graph_base()}/{endpoint}"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, params={"access_token": token}, json=payload, timeout=30.0)
    if resp.status_code == 429:
        raise Exception("Rate limited; retry later")
    if resp.status_code != 200:
        logger.warning("Instagram graph_post %s failed: %s %s", endpoint, resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json() if resp.content else {}


async def _graph_delete(endpoint: str) -> None:
    token = _access_token()
    if not token:
        raise ValueError("INSTAGRAM_PAGE_ACCESS_TOKEN not set")
    url = f"{_graph_base()}/{endpoint}"
    async with httpx.AsyncClient() as client:
        resp = await client.delete(url, params={"access_token": token}, timeout=30.0)
    if resp.status_code == 429:
        raise Exception("Rate limited; retry later")
    if resp.status_code not in (200, 204):
        logger.warning("Instagram graph_delete %s failed: %s %s", endpoint, resp.status_code, resp.text)
        resp.raise_for_status()


async def get_post_comments(media_id: str) -> dict[str, Any]:
    """Get comments on a post. media_id is the Instagram media ID from Graph API."""
    return await _graph_get(f"{media_id}/comments")


async def reply_to_comment(comment_id: str, message: str) -> dict[str, Any]:
    """Reply to a comment."""
    return await _graph_post(f"{comment_id}/replies", {"message": message})


async def hide_comment(comment_id: str) -> dict[str, Any]:
    """Hide a comment from the post."""
    return await _graph_post(comment_id, {"hidden": True})


async def delete_comment(comment_id: str) -> None:
    """Delete a comment."""
    await _graph_delete(comment_id)
