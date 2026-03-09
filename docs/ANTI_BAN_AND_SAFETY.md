# Instagram Automation Anti-Ban and Account Safety Guide

**Objective:** Minimize the risk of Instagram accounts getting blocked or banned. The system simulates human behaviour and enforces strict safety limits.

---

## Proxy Management

- **One proxy per account** – Each account must use a dedicated proxy.
- Proxy should remain stable; location should match the account's typical location.
- If proxy fails, pause the account instead of rotating instantly.
- Implementation: `proxy_id` on account; proxy attached when launching the automation browser.

---

## Device Fingerprint System

Each account must have a **fixed** device fingerprint. Stored fields:

- `device_model`
- `operating_system`
- `user_agent`
- `screen_resolution`
- `timezone`
- `language`

**Rules:**

- Reuse the same fingerprint on every login.
- Generate randomly when the account is first connected; never change unless the account is reinitialized.
- Stored in `device_profile` (JSON) on the account.

---

## Session Management

- Login once and store session cookies; reuse for future automation.
- Only perform login again if session expires.
- Store session cookies (including `session_id`, `csrftoken`, `device_id` via cookie JSON).

---

## Account Warm-Up System

New accounts go through a warm-up period before full automation.

| Period   | Allowed actions                          |
|----------|------------------------------------------|
| Day 1–2  | Login, scroll feed, watch stories        |
| Day 3–5  | Like 5–10 posts                          |
| Day 6–10 | Follow a few users                      |
| Day 10+  | Automation can start gradually          |

The system tracks `connected_at` and derives warm-up stage; automation is restricted by stage.

---

## Action Limit System

Default safe daily limits:

- **Likes:** 80
- **Follows:** 40
- **Comments:** 10
- **DMs:** 20

**Rules:**

- Distribute actions throughout the day.
- Never execute in bursts; enforce cooldowns between actions (e.g. 20–60 seconds).

---

## Human Behaviour Simulation

- Random delays between actions (configurable 20–60 s).
- Feed scrolling before interactions.
- Random wait times and random action order.
- One active task per account at a time; tasks spread with randomized scheduled times.

---

## Action Block Detection

If the system detects:

- "Action blocked"
- "Try again later"

Then:

- Pause the account for 24 hours (`paused_until`).
- Increment `action_block_count`.
- Do not run tasks for that account until `paused_until` has passed.

---

## Account Health (Optional / Phase 2)

Track: `login_success_rate`, `action_block_count`, `captcha_triggers`, `automation_failures`. If thresholds exceeded, temporarily disable automation and optionally notify the user.

---

## Bulk Follow with All Accounts

- "Follow [username] with all accounts" creates **one** FOLLOW_USER task **per account**.
- Each task gets a **random** `scheduled_time` in the next 24 hours so actions are spread.
- Only one task runs per account at a time; daily limits are enforced per account.

---

## System Architecture

- Each worker should handle a limited number of accounts (e.g. max 10 per worker).
- All automation services enforce the safety mechanisms above to reduce the risk of bans.
