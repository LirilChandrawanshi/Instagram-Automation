# Feature ideas for Instagram Automation

Suggestions for **new features** and **feature improvements** (not infra/code quality). Grouped by effort and impact.

---

## Current feature set (summary)

- **Accounts:** Connect (session cookie), list, check session, delete  
- **Tasks:** Single create + bulk follow / like / comment / view reel; list (filter by account/status), delete  
- **Task types:** Like post, Follow user, Send DM, Comment, Upload post, View reel  
- **Analytics:** Overview (counts by status/type)  
- **Settings:** Testing mode, Comment-to-DM (reply-all, keywords, enabled posts, follower check, allowed users)  
- **Instagram Graph API:** Send DM, get/reply/hide/delete comments  
- **Webhooks:** Comment-to-DM automation (keyword → private reply)

---

## Quick wins (1–2 days each)

### 1. **Bulk DM**
- **What:** API + UI to create “Send DM” tasks in bulk (e.g. same message to 10 usernames, one task per account/user).
- **Why:** You have single-task DM; many use cases need “DM this list” (e.g. new followers, list from CSV).
- **Backend:** New endpoint e.g. `POST /tasks/bulk-dm` with `targets: list[str]`, `message: str`; create one `SEND_DM` task per (account, target) with spread schedule.
- **Frontend:** Section on Automation page: “Bulk DM” with textarea for usernames (one per line) + message.

### 2. **Retry failed tasks**
- **What:** “Retry” on a failed task: same account, type, target, payload; new `scheduled_time` (or immediate in testing mode).
- **Why:** Transient failures (network, block) are common; one-click retry improves UX.
- **Backend:** `POST /tasks/{task_id}/retry` → create new task from failed one, optional delete or keep old for history.
- **Frontend:** Retry button in task row when `status === "failed"`.

### 3. **Pause / resume account**
- **What:** Toggle “pause this account” so no new tasks run for it until resumed. You already have `paused_until` (anti-ban); expose it in the API and UI.
- **Why:** Users need to temporarily stop automation per account (travel, manual use, etc.).
- **Backend:** `PATCH /accounts/{id}` or dedicated `POST /accounts/{id}/pause`, `POST /accounts/{id}/resume` setting `paused_until` (e.g. null = resume, or 30 days = pause).
- **Frontend:** Pause/Resume on each account card; show “Paused until …” when set.

### 4. **Export tasks (CSV)**
- **What:** Export current task list (with filters) as CSV: id, account_username, task_type, target, status, result_message, scheduled_time, completed_at.
- **Why:** Reporting, debugging, sharing with others.
- **Backend:** Either same `GET /tasks` with `Accept: text/csv` or `GET /tasks/export?format=csv&...` returning CSV.
- **Frontend:** “Export CSV” button next to filters; trigger download.

### 5. **Schedule / calendar view**
- **What:** View “when” tasks run: list or simple calendar of `scheduled_time` (and completed) for next 7 days.
- **Why:** See spread of bulk actions and avoid clustering.
- **Backend:** Reuse `GET /tasks` with `status_filter=pending` and optional `scheduled_after`, `scheduled_before`.
- **Frontend:** “Schedule” tab or section: list or week view of scheduled tasks by day/hour (optional).

---

## Medium effort (3–5 days each)

### 6. **Unfollow user / bulk unfollow**
- **What:** New task type `UNFOLLOW_USER` (target = username). Optionally “bulk unfollow” from a list (e.g. users who don’t follow back, or after X days).
- **Why:** Common after follow campaigns; keeps following list clean.
- **Backend:** New action in `actions.py` (open profile, click “Following” → “Unfollow”), rate limit (e.g. daily unfollow cap), `POST /tasks/bulk-unfollow` with list of usernames.
- **Frontend:** “Unfollow” in single-task form; “Bulk unfollow” with textarea of usernames.

### 7. **Like/follow from hashtag**
- **What:** “Like N posts from hashtag #xyz” or “Follow N users who posted in #xyz”. One task per like/follow, spread over time.
- **Why:** Growth and engagement from hashtag feeds.
- **Backend:** New task type e.g. `LIKE_FROM_HASHTAG` / `FOLLOW_FROM_HASHTAG` with target = hashtag and payload `{ "limit": 10 }`. Bot opens `instagram.com/explore/tags/xyz`, scrolls, likes/follows with existing limits and delays.
- **Frontend:** “Hashtag” section: hashtag input + “Like X posts” / “Follow X users” + optional account selector.

### 8. **Bulk like/comment on multiple URLs**
- **What:** Paste multiple post/reel URLs; create one like (or comment) task per URL, spread across accounts and time.
- **Why:** Campaigns on many posts without creating tasks one by one.
- **Backend:** Extend `bulk-like` / `bulk-comment` to accept `targets: list[str]` (URLs); create tasks for each (account × URL) with spread.
- **Frontend:** Textarea “One URL per line” for bulk like and bulk comment.

### 9. **Comment-to-DM dashboard**
- **What:** Dedicated page or section: “Comment-to-DM” stats — comments received (from webhook), DMs sent, keyword matches, last 50 events with time/comment text/media id.
- **Why:** Visibility into how the automation is performing.
- **Backend:** Store webhook events (or at least comment_id, media_id, text, sent_dm_at) in DB; `GET /analytics/comment-dm` or `GET /comment-dm-events`.
- **Frontend:** “Comment-to-DM” in nav; table or cards of recent events + simple counts.

### 10. **Task templates / presets**
- **What:** Save a “preset” (e.g. “Follow 5 from #fitness”, “Like 10 posts from URL list”) and run again with one click (maybe change hashtag/URL).
- **Why:** Repeat common workflows without re-entering everything.
- **Backend:** New model e.g. `TaskPreset` (name, task_type, default target pattern, payload template, spread options); “Run preset” creates tasks from template.
- **Frontend:** “Presets” section: create, list, “Run” with optional override.

---

## Larger / strategic

### 11. **Story view (warm-up)**
- **What:** Task type `VIEW_STORY` (target = username). Used in warm-up (docs already mention “watch stories”).
- **Why:** Completes warm-up behaviour and optional ongoing engagement.
- **Backend:** Bot opens profile, opens story, waits a few seconds, next story or close. Add to warm-up allowed actions and daily limit.
- **Frontend:** Expose in single-task form; optional “Warm-up: view 5 stories” preset.

### 12. **Scheduled post (upload)**
- **What:** Full flow for “Upload post at time”: image (URL or upload), caption, optional location. You have `UPLOAD_POST`; wire it to a proper scheduler and media.
- **Why:** Content calendar without leaving the app.
- **Backend:** Accept image URL (or S3/local upload), caption, `scheduled_time`; at run time bot uploads via Instagram’s create flow.
- **Frontend:** “Schedule post” form: date/time, image upload/URL, caption.

### 13. **Multi-account groups / tags**
- **What:** Tag accounts (e.g. “main”, “backup”, “niche”) and run bulk actions only for “main” or “niche”.
- **Why:** Many accounts; different strategies per group.
- **Backend:** Account tags (array or many-to-many); filter in bulk endpoints by `tag` or `account_ids`.
- **Frontend:** Tags on account cards; bulk action: “Apply to accounts with tag …”.

### 14. **Unfollow non-followers**
- **What:** “Unfollow users who don’t follow back (after 7 days)”. Requires fetching following list and comparing to followers (or a manual list).
- **Why:** Common growth tactic; high demand but also high risk (Instagram may limit or ban).
- **Note:** Use with caution; consider daily cap and clear disclaimer in UI.

### 15. **Activity log (audit trail)**
- **What:** Per-account or global log: “Account X liked post Y at Z”, “DM sent to @user at Z”, with optional filters.
- **Why:** Debugging and transparency.
- **Backend:** Either derive from `tasks` (completed_at + result_message) or new `activity_log` table; `GET /activity` with account_id, date range, action type.
- **Frontend:** “Activity” page with filters and export.

---

## Summary table

| Feature              | Effort   | Impact | Notes                          |
|----------------------|----------|--------|--------------------------------|
| Bulk DM              | Quick    | High   | Very common ask                |
| Retry failed tasks   | Quick    | Medium | Better UX                      |
| Pause/resume account | Quick    | High   | Uses existing paused_until      |
| Export CSV           | Quick    | Medium | Reporting                      |
| Schedule view        | Quick    | Medium | Visibility                     |
| Unfollow / bulk      | Medium   | High   | New action + limits            |
| Hashtag like/follow  | Medium   | High   | Growth                         |
| Multi-URL bulk       | Medium   | Medium | Extend existing bulk            |
| Comment-to-DM dashboard | Medium | Medium | Observability                  |
| Task presets         | Medium   | Medium | Repeat workflows               |
| Story view           | Larger   | Medium | Warm-up + engagement           |
| Scheduled post       | Larger   | High   | Content calendar               |
| Account groups/tags  | Larger   | Medium | Scale                          |
| Unfollow non-followers | Larger | High   | Risky; cap + disclaimer         |
| Activity log         | Larger   | Medium | Audit / debug                  |

If you tell me which feature you want first (e.g. “Bulk DM” or “Pause account”), I can outline exact API shapes and UI changes step by step.
