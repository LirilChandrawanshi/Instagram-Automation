"""
Comment-to-DM: process webhook comment events, dedup, send Private Reply + optional public reply.
Runs in background after webhook returns 200. Only comments on enabled posts (allowlist) get a reply.
Optional: require follower — only users in allowed list get the link; others get non_follower_message.
"""
import logging
from typing import Set

from sqlalchemy import select
from sqlalchemy.exc import DatabaseError

from app.config import (
    get_instagram_require_follower,
    get_instagram_non_follower_message,
)
from app.database import AsyncSessionLocal
from app.models.comment_dm_sent import CommentDMSent
from app.models.comment_dm_enabled_post import CommentDMEnabledPost
from app.models.instagram_dm_allowed_user import InstagramDMAllowedUser
from app.services.instagram_messaging_service import (
    get_comment_reply_text,
    send_private_reply,
)
from app.services.instagram_comment_service import reply_to_comment

logger = logging.getLogger(__name__)


async def get_enabled_media_ids() -> Set[str]:
    """Return set of media_ids (post IDs) that have Comment-to-DM enabled. Empty = no auto-reply."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CommentDMEnabledPost.media_id))
        rows = result.scalars().all()
        return {str(r) for r in rows if r}


async def get_allowed_user_ids() -> Set[str]:
    """Return set of Instagram user IDs treated as followers (get the link when require_follower is on)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(InstagramDMAllowedUser.user_id))
        rows = result.scalars().all()
        return {str(r) for r in rows if r}


async def process_comment_events(events: list) -> None:
    """
    For each comment event on an enabled post: dedup by comment_id, get reply text (keyword or reply-all),
    send Private Reply, optionally public reply, then mark sent. Runs in background.
    Skips events whose media_id is not in the enabled-posts allowlist; if allowlist is empty, skips all.
    """
    enabled = await get_enabled_media_ids()
    if not enabled:
        return
    allowed_user_ids = await get_allowed_user_ids()
    require_follower = get_instagram_require_follower()
    non_follower_message = get_instagram_non_follower_message() or "I think you're not following me! Please follow and comment again to get the link."
    for ev in events:
        media_id = ev.get("media_id")
        if not media_id or str(media_id) not in enabled:
            continue
        comment_id = ev.get("id") or ev.get("comment_id")
        text = (ev.get("text") or "").strip()
        commenter_user_id = ev.get("commenter_user_id")
        if not comment_id:
            continue
        try:
            async with AsyncSessionLocal() as db:
                existing = (await db.execute(select(CommentDMSent.comment_id).where(CommentDMSent.comment_id == comment_id))).scalar_one_or_none()
                if existing:
                    continue
                reply_text = get_comment_reply_text(text)
                if not reply_text:
                    continue
                # If require_follower is on: only send link to users in allowed list; others get non_follower_message.
                if require_follower and commenter_user_id and str(commenter_user_id) not in allowed_user_ids:
                    message_to_send = non_follower_message
                else:
                    message_to_send = reply_text
                await send_private_reply(comment_id, message_to_send)
                try:
                    await reply_to_comment(comment_id, "We've sent it to your DMs! Check your inbox.")
                except Exception:
                    pass
                db.add(CommentDMSent(comment_id=comment_id))
                await db.commit()
        except DatabaseError as e:
            logger.warning("Comment-to-DM dedup/insert failed for %s: %s", comment_id, e)
        except Exception as e:
            logger.warning("Comment-to-DM failed for %s: %s", comment_id, e)
