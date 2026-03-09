# Instagram Graph API (Messaging + Comments)

This feature uses **official Instagram APIs** for Business/Creator accounts:

- **Direct Messages** – receive via webhook, send via API
- **Comments** – get comments on a post, reply, hide, delete

---

## Prerequisites

- Instagram **Business** or **Creator** account
- Connected **Facebook Page**
- **Meta Developer App** with:
  - Instagram Graph API
  - Instagram Messaging API
- Permissions: `instagram_basic`, `instagram_manage_comments`, `instagram_manage_messages`, `pages_manage_metadata`, `pages_read_engagement`

---

## Environment variables

Add to `backend/.env`:

```env
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret
INSTAGRAM_PAGE_ACCESS_TOKEN=your_page_access_token
INSTAGRAM_VERIFY_TOKEN=your_webhook_verify_token
INSTAGRAM_API_VERSION=v19.0
```

Base URL: `https://graph.facebook.com/v19.0`

---

## Webhook

- **Verification (GET):** `GET /webhooks/instagram`  
  Meta sends `hub.mode`, `hub.verify_token`, `hub.challenge`. If `hub.verify_token` matches `INSTAGRAM_VERIFY_TOKEN`, respond with `hub.challenge`.

- **Receive events (POST):** `POST /webhooks/instagram`  
  Instagram sends messages, comments, mentions. The backend parses them and can auto-reply (e.g. keyword "price" → reply with product link).

Your backend URL must be HTTPS for production (e.g. ngrok for local testing).

---

## App usage

1. Open **Instagram API** in the sidebar.
2. **Send DM** – enter Instagram User ID (from webhook or Graph API) and message.
3. **Get comments** – enter Media ID (from Graph API) to list comments.
4. **Reply / Hide / Delete** – use Comment ID from the list or API.

---

## Backend services

- `app/services/instagram_messaging_service.py` – `send_dm()`, `handle_incoming_message()`
- `app/services/instagram_comment_service.py` – `get_post_comments()`, `reply_to_comment()`, `hide_comment()`, `delete_comment()`
- `app/api/instagram_webhooks.py` – GET/POST webhook
- `app/api/instagram_graph.py` – authenticated REST endpoints
