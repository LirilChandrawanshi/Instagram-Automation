# Project improvement suggestions

Suggestions to harden, scale, and maintain the Instagram Automation platform. Items already applied in code are marked **Done**.

---

## Already applied (this session)

- **JWT expiry uses timezone-aware datetime** – Replaced deprecated `datetime.utcnow()` in `app/core/security.py` with `datetime.now(timezone.utc)` for Python 3.12+ compatibility.
- **Rate limiter uses fresh settings** – `app/utils/rate_limiter.py` now reads limits from `get_settings()` at check time so env/test overrides (e.g. `TESTING_MODE`) take effect without restart.
- **Startup and scheduler logging** – Lifespan table-ensure steps and the inline scheduler loop log warnings on failure instead of failing silently.

---

## Security & production readiness

1. **JWT secret**
   - Ensure `JWT_SECRET` is a long random value in production (e.g. 32+ bytes).
   - Add a startup check that fails if `JWT_SECRET` is still the default when `DEBUG=false`.

2. **CORS**
   - `main.py` only allows `localhost:3000`. For production, make origins configurable via env (e.g. `CORS_ORIGINS`) and avoid `*` with credentials.

3. **Frontend token storage**
   - JWT in `localStorage` is XSS-visible. For higher security, consider httpOnly cookies for the API (with SameSite and Secure in production).

4. **Sensitive env in .env.example**
   - Keep `.env.example` free of real secrets; document required vars and use placeholders (already in good shape).

---

## Observability & debugging

5. **Structured logging**
   - Use the existing `app/utils/logger.py` in bot, automation_service, and API routes (e.g. task created/completed, account connect, errors) with consistent fields (e.g. `task_id`, `account_id`).

6. **Request ID / correlation ID**
   - Add middleware to attach a request ID to each request and log it so you can trace a single task or request across API, worker, and logs.

7. **Health checks**
   - Extend `/health` to optionally check DB and Redis connectivity (e.g. simple query / ping) and return 503 if unhealthy, for Docker/K8s readiness.

---

## Testing

8. **Backend tests**
   - Add tests for: auth (login/register, invalid token), task creation and ownership, rate limiter (`get_today_count` / `can_perform_action`), and key automation_service branches (e.g. warm-up, limit reached).
   - Use pytest-asyncio and a test DB (e.g. SQLite in-memory or a test DB URL) so tests don’t touch dev data.

9. **E2E / Playwright**
   - Optional: a minimal E2E that logs in to the dashboard and creates a task to catch regressions in the full stack.

---

## Configuration & env

10. **Config validation on startup**
    - Validate critical env (e.g. `DATABASE_URL`, `REDIS_URL` when not `RUN_TASKS_INLINE`) and fail fast with clear messages instead of failing later in a request or worker.

11. **CORS and allowed hosts**
    - Read CORS origins and any “allowed host” list from env so production domains can be added without code changes.

---

## Robustness

12. **Celery enqueue fallback**
    - In `SchedulerService.create_and_enqueue`, when Celery `apply_async` fails, you already fall back to inline execution; log the failure and consider alerting if Celery is intended to be the primary path.

13. **Swallowed exceptions**
    - Several `except Exception: pass` (or equivalent) exist in bot actions, webhooks, and comment_to_dm_service. Prefer logging at minimum (with `exc_info=True` where useful) and, where it makes sense, retries or partial failure reporting instead of silent ignore.

14. **DB session in long-running tasks**
    - Ensure automation tasks use a fresh session per run and don’t hold a session across long Playwright operations to avoid timeouts and connection issues.

---

## API & backend structure

15. **Global exception handler**
    - Add a FastAPI exception handler for unhandled exceptions that logs the error and returns a generic 500 message (and a detailed one only when `DEBUG=true`).

16. **Pagination**
    - For `GET /tasks` and `GET /accounts`, add optional `limit`/`offset` (or cursor) so large accounts don’t load thousands of rows at once.

17. **OpenAPI tags and descriptions**
    - Group and document endpoints (e.g. tags for accounts, tasks, Instagram Graph, webhooks) so `/docs` is easier to use for teammates and integrations.

---

## Frontend

18. **Error handling and toasts**
    - Show user-friendly toasts or inline messages for API errors (e.g. “Account not found”, “Daily limit reached”) instead of only failing silently or showing a generic error.

19. **Loading states**
    - Use loading indicators or disabled buttons for connect account, check session, and bulk operations so users know the app is working.

20. **Env validation**
    - Validate `NEXT_PUBLIC_API_URL` at build or runtime and show a clear message if it’s missing or invalid so misconfiguration is obvious.

---

## Optional features

21. **Audit log**
    - Optional table or log stream for sensitive actions (account connect/delete, task creation, settings changes) for debugging and compliance.

22. **Metrics**
    - Optional Prometheus metrics (e.g. tasks_created, tasks_completed_by_type, accounts_connected) for dashboards and alerts.

23. **Retry policy for Celery**
    - Configure retries and backoff for `run_automation_task` so transient failures (e.g. network, Instagram timeout) are retried a few times before marking the task failed.

---

## Quick reference: files touched for improvements

| File | Change |
|------|--------|
| `backend/app/core/security.py` | JWT expiry: `datetime.now(timezone.utc)` |
| `backend/app/utils/rate_limiter.py` | Limits from `get_settings()` per check |
| `backend/app/main.py` | Logging for scheduler loop and startup table ensures |
