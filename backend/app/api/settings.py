"""
Settings API: testing mode, Instagram reply-all, Comment-to-DM enabled posts.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import (
    get_testing_mode,
    set_testing_mode,
    get_instagram_reply_all,
    set_instagram_reply_all,
    get_instagram_reply_all_message,
    set_instagram_reply_all_message,
    get_instagram_require_follower,
    set_instagram_require_follower,
    get_instagram_non_follower_message,
    set_instagram_non_follower_message,
)
from app.core.deps import get_current_user
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.comment_dm_enabled_post import CommentDMEnabledPost
from app.models.instagram_dm_allowed_user import InstagramDMAllowedUser
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/settings", tags=["settings"])


class TestingModeResponse(BaseModel):
    testing_mode: bool


class TestingModeBody(BaseModel):
    testing_mode: bool


@router.get("/testing-mode", response_model=TestingModeResponse)
async def get_testing_mode_api(_: User = Depends(get_current_user)) -> TestingModeResponse:
    """Get current testing mode (bypass anti-ban limits)."""
    return TestingModeResponse(testing_mode=get_testing_mode())


@router.post("/testing-mode", response_model=TestingModeResponse)
async def set_testing_mode_api(
    body: TestingModeBody,
    _: User = Depends(get_current_user),
) -> TestingModeResponse:
    """Turn testing mode on/off. When on: no warm-up, no daily limits, no pause; short delays."""
    set_testing_mode(body.testing_mode)
    return TestingModeResponse(testing_mode=get_testing_mode())


class InstagramReplyAllResponse(BaseModel):
    reply_all: bool
    reply_all_message: str


class InstagramReplyAllBody(BaseModel):
    reply_all: bool
    reply_all_message: Optional[str] = None


@router.get("/instagram-reply-all", response_model=InstagramReplyAllResponse)
async def get_instagram_reply_all_api(_: User = Depends(get_current_user)) -> InstagramReplyAllResponse:
    """Get reply-to-all-comments setting: when on, every comment gets a DM with the message."""
    return InstagramReplyAllResponse(
        reply_all=get_instagram_reply_all(),
        reply_all_message=get_instagram_reply_all_message() or "Thanks for commenting! We've sent you a message.",
    )


@router.post("/instagram-reply-all", response_model=InstagramReplyAllResponse)
async def set_instagram_reply_all_api(
    body: InstagramReplyAllBody,
    _: User = Depends(get_current_user),
) -> InstagramReplyAllResponse:
    """Turn reply-to-all on/off and set the message sent in DMs for every comment."""
    set_instagram_reply_all(body.reply_all)
    if body.reply_all_message is not None:
        set_instagram_reply_all_message(body.reply_all_message)
    return InstagramReplyAllResponse(
        reply_all=get_instagram_reply_all(),
        reply_all_message=get_instagram_reply_all_message() or "Thanks for commenting! We've sent you a message.",
    )


# Comment-to-DM: allowlist of posts (media_id) that get auto-reply
class CommentDMEnabledPostsResponse(BaseModel):
    media_ids: List[str]


class CommentDMEnabledPostBody(BaseModel):
    media_id: str


@router.get("/comment-dm-enabled-posts", response_model=CommentDMEnabledPostsResponse)
async def get_comment_dm_enabled_posts(_: User = Depends(get_current_user)) -> CommentDMEnabledPostsResponse:
    """List media IDs (post IDs) that have Comment-to-DM auto-reply enabled."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CommentDMEnabledPost.media_id).order_by(CommentDMEnabledPost.created_at))
        media_ids = [str(r) for r in result.scalars().all() if r]
    return CommentDMEnabledPostsResponse(media_ids=media_ids)


@router.post("/comment-dm-enabled-posts", response_model=CommentDMEnabledPostsResponse)
async def add_comment_dm_enabled_post(
    body: CommentDMEnabledPostBody,
    _: User = Depends(get_current_user),
) -> CommentDMEnabledPostsResponse:
    """Add a post (by media_id) to the Comment-to-DM allowlist."""
    media_id = (body.media_id or "").strip()
    if not media_id:
        raise HTTPException(status_code=400, detail="media_id is required")
    async with AsyncSessionLocal() as db:
        try:
            db.add(CommentDMEnabledPost(media_id=media_id))
            await db.commit()
        except IntegrityError:
            await db.rollback()
        result = await db.execute(select(CommentDMEnabledPost.media_id).order_by(CommentDMEnabledPost.created_at))
        media_ids = [str(r) for r in result.scalars().all() if r]
    return CommentDMEnabledPostsResponse(media_ids=media_ids)


@router.delete("/comment-dm-enabled-posts/{media_id}", response_model=CommentDMEnabledPostsResponse)
async def remove_comment_dm_enabled_post(
    media_id: str,
    _: User = Depends(get_current_user),
) -> CommentDMEnabledPostsResponse:
    """Remove a post (by media_id) from the Comment-to-DM allowlist."""
    async with AsyncSessionLocal() as db:
        await db.execute(delete(CommentDMEnabledPost).where(CommentDMEnabledPost.media_id == media_id))
        await db.commit()
        result = await db.execute(select(CommentDMEnabledPost.media_id).order_by(CommentDMEnabledPost.created_at))
        media_ids = [str(r) for r in result.scalars().all() if r]
    return CommentDMEnabledPostsResponse(media_ids=media_ids)


# Comment-to-DM: only send link to followers (allowed user list); others get non_follower_message
class InstagramFollowerCheckResponse(BaseModel):
    require_follower: bool
    non_follower_message: str


class InstagramFollowerCheckBody(BaseModel):
    require_follower: bool
    non_follower_message: Optional[str] = None


@router.get("/instagram-comment-dm-follower", response_model=InstagramFollowerCheckResponse)
async def get_instagram_follower_check_api(_: User = Depends(get_current_user)) -> InstagramFollowerCheckResponse:
    """Get require-follower setting and message for non-followers."""
    return InstagramFollowerCheckResponse(
        require_follower=get_instagram_require_follower(),
        non_follower_message=get_instagram_non_follower_message()
        or "I think you're not following me! Please follow and comment again to get the link.",
    )


@router.post("/instagram-comment-dm-follower", response_model=InstagramFollowerCheckResponse)
async def set_instagram_follower_check_api(
    body: InstagramFollowerCheckBody,
    _: User = Depends(get_current_user),
) -> InstagramFollowerCheckResponse:
    """Turn require-follower on/off and set the message sent to non-followers."""
    set_instagram_require_follower(body.require_follower)
    if body.non_follower_message is not None:
        set_instagram_non_follower_message(body.non_follower_message)
    return InstagramFollowerCheckResponse(
        require_follower=get_instagram_require_follower(),
        non_follower_message=get_instagram_non_follower_message()
        or "I think you're not following me! Please follow and comment again to get the link.",
    )


# Allowed user IDs (treated as followers — they get the link when require_follower is on)
class InstagramDMAllowedUsersResponse(BaseModel):
    user_ids: List[str]


class InstagramDMAllowedUserBody(BaseModel):
    user_id: str


@router.get("/instagram-dm-allowed-users", response_model=InstagramDMAllowedUsersResponse)
async def get_instagram_dm_allowed_users(_: User = Depends(get_current_user)) -> InstagramDMAllowedUsersResponse:
    """List Instagram user IDs that get the link when require_follower is on."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(InstagramDMAllowedUser.user_id).order_by(InstagramDMAllowedUser.created_at))
        user_ids = [str(r) for r in result.scalars().all() if r]
    return InstagramDMAllowedUsersResponse(user_ids=user_ids)


@router.post("/instagram-dm-allowed-users", response_model=InstagramDMAllowedUsersResponse)
async def add_instagram_dm_allowed_user(
    body: InstagramDMAllowedUserBody,
    _: User = Depends(get_current_user),
) -> InstagramDMAllowedUsersResponse:
    """Add an Instagram user ID to the allowed list (they get the link when require_follower is on)."""
    user_id = (body.user_id or "").strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    async with AsyncSessionLocal() as db:
        try:
            db.add(InstagramDMAllowedUser(user_id=user_id))
            await db.commit()
        except IntegrityError:
            await db.rollback()
        result = await db.execute(select(InstagramDMAllowedUser.user_id).order_by(InstagramDMAllowedUser.created_at))
        user_ids = [str(r) for r in result.scalars().all() if r]
    return InstagramDMAllowedUsersResponse(user_ids=user_ids)


@router.delete("/instagram-dm-allowed-users/{user_id}", response_model=InstagramDMAllowedUsersResponse)
async def remove_instagram_dm_allowed_user(
    user_id: str,
    _: User = Depends(get_current_user),
) -> InstagramDMAllowedUsersResponse:
    """Remove an Instagram user ID from the allowed list."""
    async with AsyncSessionLocal() as db:
        await db.execute(delete(InstagramDMAllowedUser).where(InstagramDMAllowedUser.user_id == user_id))
        await db.commit()
        result = await db.execute(select(InstagramDMAllowedUser.user_id).order_by(InstagramDMAllowedUser.created_at))
        user_ids = [str(r) for r in result.scalars().all() if r]
    return InstagramDMAllowedUsersResponse(user_ids=user_ids)
