"""
Instagram webhook: verification (GET) and receive events (POST).
No auth; Meta calls these endpoints. Comment-to-DM: parse comments, return 200, process async.
"""
import asyncio
import hashlib
import hmac
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings
from app.services.instagram_messaging_service import handle_incoming_message, send_dm
from app.services.comment_to_dm_service import process_comment_events

router = APIRouter(tags=["webhooks"])


def _verify_signature(raw_body: bytes, signature_header: Optional[str], secret: Optional[str]) -> bool:
    """Verify X-Hub-Signature-256 (sha256=hex) with HMAC-SHA256(raw_body, secret)."""
    if not secret or not signature_header or not raw_body:
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected = signature_header[7:].strip().lower()
    computed = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest().lower()
    return hmac.compare_digest(computed, expected)


@router.get("/webhooks/instagram")
async def verify_webhook(request: Request):
    """Meta verification: hub.mode=subscribe, hub.verify_token must match, return hub.challenge."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    verify_token = get_settings().instagram_verify_token
    if mode == "subscribe" and verify_token and token == verify_token and challenge:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhooks/instagram")
async def receive_webhook(request: Request):
    """Receive Instagram webhook events (messages, comments). Return 200 immediately; process comments async."""
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    secret = get_settings().instagram_app_secret
    if secret and not _verify_signature(raw_body, signature, secret):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        body = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {"status": "received"}

    if "entry" not in body:
        return {"status": "received"}

    comment_events: list[dict] = []

    for entry in body.get("entry", []):
        for event in entry.get("messaging", []):
            sender_id = (event.get("sender") or {}).get("id")
            if not sender_id:
                continue
            if "message" in event:
                text = (event["message"].get("text") or "").strip()
                reply = handle_incoming_message(event)
                if reply:
                    try:
                        await send_dm(sender_id, reply)
                    except Exception:
                        pass

        for change in entry.get("changes", []):
            if change.get("field") != "comments":
                continue
            value = change.get("value") or {}
            cid = value.get("id")
            text = (value.get("text") or "").strip()
            from_obj = value.get("from") or {}
            commenter_user_id = from_obj.get("id") if isinstance(from_obj, dict) else None
            if cid:
                media_obj = value.get("media")
                media_id = media_obj.get("id") if isinstance(media_obj, dict) else None
                comment_events.append({
                    "id": cid,
                    "comment_id": cid,
                    "text": text,
                    "media_id": media_id,
                    "commenter_user_id": str(commenter_user_id) if commenter_user_id else None,
                })

    if comment_events:
        asyncio.create_task(process_comment_events(comment_events))

    return {"status": "received"}
