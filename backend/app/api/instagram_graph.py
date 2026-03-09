"""
Instagram Graph API: send DM, get comments, reply, hide, delete.
Requires auth. Uses INSTAGRAM_PAGE_ACCESS_TOKEN from env.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.models.user import User
from app.services.instagram_comment_service import (
    delete_comment,
    get_post_comments,
    hide_comment,
    reply_to_comment,
)
from app.services.instagram_messaging_service import send_dm as send_dm_service

router = APIRouter(prefix="/instagram-api", tags=["instagram-graph"])


class SendDMBody(BaseModel):
    user_id: str
    message: str


@router.post("/send-dm")
async def send_dm_endpoint(
    body: SendDMBody,
    _: User = Depends(get_current_user),
):
    """Send a direct message to an Instagram user (Graph API)."""
    try:
        result = await send_dm_service(body.user_id, body.message)
        return result
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/comments/{media_id}")
async def get_comments_endpoint(
    media_id: str,
    _: User = Depends(get_current_user),
):
    """Get comments on a post. media_id = Instagram media ID from Graph API."""
    try:
        return await get_post_comments(media_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ReplyBody(BaseModel):
    message: str


@router.post("/comments/{comment_id}/reply")
async def reply_comment_endpoint(
    comment_id: str,
    body: ReplyBody,
    _: User = Depends(get_current_user),
):
    """Reply to a comment."""
    try:
        return await reply_to_comment(comment_id, body.message)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/comments/{comment_id}/hide")
async def hide_comment_endpoint(
    comment_id: str,
    _: User = Depends(get_current_user),
):
    """Hide a comment."""
    try:
        return await hide_comment(comment_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/comments/{comment_id}")
async def delete_comment_endpoint(
    comment_id: str,
    _: User = Depends(get_current_user),
):
    """Delete a comment."""
    try:
        await delete_comment(comment_id)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
