# Comment-to-DM Automation – Reference Blueprint

Condensed from the architectural blueprint for building Instagram **Comment-to-DM** automation using **official Meta APIs** (Graph API + Messenger for Instagram). Use this as a technical reference; our stack is FastAPI/Python, not Node.js.

---

## 1. Why Comment-to-DM

- **Lower friction** than "link in bio" (fewer drop-offs).
- **Algorithm boost**: public reply + private DM = double engagement signal → more reach.
- **Lead capture** at peak intent (e.g. "Comment EBOOK" → auto-send guide in DMs).

**Rule:** Use only **official Meta APIs**. No scraping, no unofficial bots, no password/session automation for this flow. Business/Creator account + linked Facebook Page required.

---

## 2. Event Flow (High Level)

1. User comments a **keyword** on a Post/Reel.
2. Meta sends **webhook POST** to our endpoint (comment event).
3. We **return 200 OK immediately** (no heavy work in request).
4. **Background worker** parses comment, checks keyword/intent.
5. If match → call **Private Replies API** (DM tied to that comment).
6. Optionally **public reply** to the same comment (e.g. "Sent to your DMs!").
7. Log in DB for dedup and analytics.

---

## 3. Webhook Endpoint (Same URL, Two Methods)

### GET – Verification (Meta subscription)

- Query params: `hub.mode`, `hub.verify_token`, `hub.challenge`.
- If `hub.mode == "subscribe"` and `hub.verify_token == INSTAGRAM_VERIFY_TOKEN` → return **body = hub.challenge** (integer or string), status 200.
- No JSON wrapper; raw challenge only.

### POST – Events

- **Must return 200 quickly** so Meta doesn’t time out and disable the subscription.
- Do **not** do full processing in the request handler; enqueue and process async.
- Body is JSON; structure depends on subscription type (comments vs messaging).

---

## 4. Webhook Payload Shapes

### Messaging (inbound DMs)

- Path: `entry[]` → `messaging[]`.
- Each event: `sender.id`, `message.text`, etc.
- We already handle this for **inbound messages** (open 24h window).

### Comments (for Comment-to-DM)

- Path: `entry[]` → `changes[]`.
- Filter where `field == "comments"`.
- `value` contains:
  - `id` – **comment_id** (required for Private Reply).
  - `text` – comment text.
  - `media_id` – post/reel id.
- May see variations for ads (e.g. `ad_id`, `ad_title`); handle and dedupe.

---

## 5. Signature Verification (Security)

- Meta signs POST body with **HMAC SHA-256** using **App Secret**.
- Header: `X-Hub-Signature-256` (e.g. `sha256=<hex>`).
- We must:
  - Keep **raw request body** (before JSON parse) for hashing.
  - Compute `HMAC-SHA256(raw_body, APP_SECRET)` and compare with header (constant-time).
- If we parse JSON first and re-serialize, Unicode/emoji can change bytes and break verification. So: read raw body, verify, then parse.

---

## 6. Private Replies API (Critical for Comment-to-DM)

**First message triggered by a comment** must use **Private Reply**, not the normal “send by user id” endpoint.

- **Endpoint:** `POST https://graph.facebook.com/v19.0/{PAGE_ID}/messages`
- **Body:**
  - `recipient`: `{ "comment_id": "<COMMENT_ID>" }`  (not `id` with IGSID).
  - `message`: `{ "text": "..." }`.
- **Access token:** Page Access Token (query or header).

Constraints:

- **One** private message per comment (no follow-up from this comment alone).
- **comment_id** valid ~**7 days** for standard posts/reels; after that, private reply not allowed.
- For **Live** comments, private reply only while the live is active.
- If user doesn’t follow, message goes to **Requests** folder (lower visibility).

**Hybrid pattern:** Send Private Reply **and** a **public** reply to the comment (e.g. “We’ve sent the link to your DMs!”) so the user checks Requests and we get extra engagement signal.

---

## 7. Intent Detection

- **Regex:** Fast, cheap, good for fixed keywords (e.g. "EBOOK", "LINK"). Use word boundaries and case-insensitivity; handle typos/punctuation.
- **LLM:** For semantic intent (e.g. “Where can I buy this?”). More flexible, more cost/latency; needs fallback for unknown input.

---

## 8. 24-Hour Messaging Window

- **Private Reply** does **not** open the 24h window by itself.
- When the **user replies** to that DM, a **messaging** webhook fires and **then** the 24h window opens.
- Within 24h we can send more messages; each user reply **resets** the 24h.
- After 24h of no user reply, we can’t send (unless using approved message tags).
- **Human handoff:** Must offer a clear way to “talk to a human”; when user asks, pause automation and route to a human (or tag as human-only). Meta expects this.

---

## 9. Rate Limits and Best Practices

- ~200 automated DMs per hour per account (approximate; respect headers).
- Use a queue (e.g. Celery + Redis) to throttle and retry with backoff.
- Dedupe by `comment_id` so we don’t reply twice to the same comment.
- Log all comment_id → DM sends for support and Meta review.

---

## 10. Meta App Review (Advanced Access)

- **instagram_manage_messages** (and related) need **Advanced Access** for public users.
- In Development mode, only Testers can receive DMs.
- For review: provide a **screencast** of real flow (real account, real comment, DM received), **Privacy Policy** URL, and **fallback** replies for any unrecognized input so the experience never “dead-ends”.

---

## 11. Mapping to Our Stack (FastAPI/Python)

| Blueprint concept        | Our project (current)                          | To build Comment-to-DM              |
|--------------------------|-------------------------------------------------|-------------------------------------|
| Webhook GET verify       | Yes – `GET /webhooks/instagram`, challenge      | Keep; already correct.              |
| Webhook POST             | Yes – but only `entry[].messaging` (DMs)        | Add handling for `entry[].changes` (comments). |
| Return 200 immediately   | We process inline                               | Return 200, then enqueue (e.g. Celery) for comment handling. |
| Signature verification   | No                                              | Add: raw body + HMAC vs `X-Hub-Signature-256`. |
| Send DM by user id       | Yes – `send_dm(ig_user_id, text)`               | Keep for 24h-window replies.        |
| Private Reply by comment | No                                              | Add: `POST /{PAGE_ID}/messages` with `recipient: { comment_id }`. |
| Comment public reply     | Yes – `reply_to_comment(comment_id, message)`    | Use after sending Private Reply.    |
| Intent (keyword/LLM)     | Simple keyword in `handle_incoming_message`     | Extend for comment text (regex or LLM). |
| Queue / async            | Celery/Redis for automation tasks               | Reuse for comment-to-DM jobs.       |
| Dedup / logging          | Not for comments                                | Store comment_id → sent flag; log. |

---

## 12. Can We Build This in Our Project?

**Yes.** The blueprint fits our stack with these additions:

1. **Webhook**
   - Preserve **raw body** for signature verification; verify `X-Hub-Signature-256` with App Secret before parsing.
   - In POST handler: parse JSON, detect **comments** in `entry[].changes[]` (field `"comments"`), enqueue payload to Celery (or similar); return 200 immediately.

2. **Private Replies**
   - New function (e.g. in `instagram_messaging_service`): `send_private_reply(comment_id: str, message: str)` calling `POST {GRAPH_API}/{PAGE_ID}/messages` with `recipient: {"comment_id": comment_id}` and `message: {"text": message}`.
   - Use **Page ID** (from token or config), not Instagram Business Account ID, for the path.

3. **Comment-to-DM flow (async worker)**
   - Worker receives: `comment_id`, `comment_text`, `media_id` (and optional metadata).
   - Check DB: already replied for this `comment_id`? If yes, skip.
   - Intent: regex (e.g. `\b(LINK|EBOOK)\b`) or optional LLM call.
   - If match: call `send_private_reply(comment_id, reply_text)`; optionally call `reply_to_comment(comment_id, "We've sent it to your DMs!")`; mark comment_id as processed in DB.

4. **Config / env**
   - Add `INSTAGRAM_APP_SECRET` for signature verification.
   - Add `INSTAGRAM_PAGE_ID` (or derive from token) for Private Reply URL.

5. **Optional**
   - DB table for comment_id → (sent_at, reply_text) for dedup and analytics.
   - Rate limiting (e.g. Redis) for outbound DMs.
   - Human-escalation flag and pause logic when user says “human” / “support”.

**Summary:** We already have verification, messaging webhook, and comment reply API. To support Comment-to-DM we need: **signature verification**, **comment webhook parsing**, **async processing**, **Private Replies API**, and **dedup/logging**. All of this is implementable in the current FastAPI/Python project.
