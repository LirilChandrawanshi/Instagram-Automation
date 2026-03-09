"""
Instagram Graph API: send DMs, Private Reply (comment-to-DM), and handle webhook messages.
Uses official Instagram Messaging API (Business/Creator accounts).
"""
import logging
import re
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def _graph_base() -> str:
    s = get_settings()
    return f"https://graph.facebook.com/{s.instagram_api_version}"


def _access_token() -> Optional[str]:
    return get_settings().instagram_page_access_token


def _page_id() -> Optional[str]:
    return get_settings().instagram_page_id


async def send_dm(user_id: str, message: str) -> dict[str, Any]:
    """Send a direct message to an Instagram user via Graph API (use when 24h window is open)."""
    token = _access_token()
    if not token:
        raise ValueError("INSTAGRAM_PAGE_ACCESS_TOKEN not set")
    url = f"{_graph_base()}/me/messages"
    payload = {
        "recipient": {"id": user_id},
        "message": {"text": message},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, params={"access_token": token}, json=payload, timeout=30.0)
    if resp.status_code != 200:
        logger.warning("Instagram send_dm failed: %s %s", resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json()


async def send_private_reply(comment_id: str, message: str) -> dict[str, Any]:
    """
    Send a Private Reply (DM) tied to an Instagram comment. Required for comment-to-DM.
    Uses POST /{PAGE_ID}/messages with recipient.comment_id.
    """
    token = _access_token()
    pid = _page_id()
    if not token:
        raise ValueError("INSTAGRAM_PAGE_ACCESS_TOKEN not set")
    if not pid:
        raise ValueError("INSTAGRAM_PAGE_ID not set (required for Private Reply)")
    url = f"{_graph_base()}/{pid}/messages"
    payload = {
        "recipient": {"comment_id": comment_id},
        "message": {"text": message},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, params={"access_token": token}, json=payload, timeout=30.0)
    if resp.status_code != 200:
        logger.warning("Instagram send_private_reply failed: %s %s", resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json()


def comment_matches_keyword(text: str) -> Optional[str]:
    """
    Check comment text against configured regex keywords. Returns reply message if match, else None.
    """
    s = get_settings()
    pattern = getattr(s, "instagram_comment_dm_keywords", r"\b(LINK|EBOOK|PRICE|DM)\b") or r"\b(LINK|EBOOK|PRICE|DM)\b"
    default_reply = getattr(s, "instagram_comment_dm_reply", "We've sent the link to your DMs! Check your inbox.")
    if re.search(pattern, (text or ""), re.IGNORECASE):
        return default_reply
    return None


def get_comment_reply_text(comment_text: str) -> Optional[str]:
    """
    Reply text for a comment: if reply_all is on, return reply_all_message for any comment;
    otherwise return message only when keyword matches.
    """
    from app.config import get_instagram_reply_all, get_instagram_reply_all_message, get_settings
    if get_instagram_reply_all():
        msg = get_instagram_reply_all_message()
        return msg or "Thanks for commenting! We've sent you a message."
    return comment_matches_keyword(comment_text)


def handle_incoming_message(event: dict[str, Any]) -> Optional[str]:
    """
    Parse webhook event; return optional auto-reply text.
    Caller should send the reply if returned.
    """
    sender_id = (event.get("sender") or {}).get("id")
    if not sender_id:
        return None
    message = event.get("message") or {}
    text = (message.get("text") or "").strip().lower()
    if not text:
        return None
    # Example auto-reply rules
    if "price" in text:
        return "Here is the product link"
    if "where to buy" in text or "where to buy?" in text:
        return "Check our website link in bio."
    return None
