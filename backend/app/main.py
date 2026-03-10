"""
FastAPI application entrypoint.
Mounts auth, accounts, tasks, and analytics routes.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import (
    engine,
    init_db,
    ensure_task_result_message_column,
    ensure_comment_dm_sent_table,
    ensure_comment_dm_enabled_post_table,
    ensure_instagram_dm_allowed_user_table,
)
from app.api.auth import router as auth_router
from app.api.accounts import router as accounts_router
from app.api.tasks import router as tasks_router
from app.api.analytics import router as analytics_router
from app.api.settings import router as settings_router
from app.api.instagram_webhooks import router as instagram_webhooks_router
from app.api.instagram_graph import router as instagram_graph_router
from app.services.scheduler_service import SchedulerService

logger = logging.getLogger(__name__)
settings = get_settings()
SCHEDULER_INTERVAL_SEC = 60


async def _scheduled_tasks_loop() -> None:
    """Every N seconds run pending tasks that are due. Only used when RUN_TASKS_INLINE=true."""
    while True:
        await asyncio.sleep(SCHEDULER_INTERVAL_SEC)
        try:
            await SchedulerService.run_due_scheduled_tasks()
        except Exception as e:
            logger.warning("Scheduler run_due_scheduled_tasks failed: %s", e, exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup. Start scheduler loop when running tasks inline."""
    await init_db()
    for name, fn in [
        ("task_result_message_column", ensure_task_result_message_column),
        ("comment_dm_sent_table", ensure_comment_dm_sent_table),
        ("comment_dm_enabled_post_table", ensure_comment_dm_enabled_post_table),
        ("instagram_dm_allowed_user_table", ensure_instagram_dm_allowed_user_table),
    ]:
        try:
            await fn()
        except Exception as e:
            logger.warning("Startup ensure %s failed: %s", name, e)
    scheduler_task = None
    if settings.run_tasks_inline:
        scheduler_task = asyncio.create_task(_scheduled_tasks_loop())
    yield
    if scheduler_task is not None:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()] or ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(tasks_router)
app.include_router(analytics_router)
app.include_router(settings_router)
app.include_router(instagram_webhooks_router)
app.include_router(instagram_graph_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unhandled exceptions and return a safe 500 (detail only when debug)."""
    if isinstance(exc, (HTTPException, RequestValidationError)):
        raise exc
    logger.exception("Unhandled exception: %s", exc)
    detail = str(exc) if settings.debug else "Internal server error"
    return JSONResponse(status_code=500, content={"detail": detail})


@app.get("/health")
async def health(deep: bool = False) -> dict:
    """Health check for Docker/load balancers. Use ?deep=1 to probe DB."""
    out: dict = {"status": "ok"}
    if deep:
        try:
            from sqlalchemy import text
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            out["database"] = "ok"
        except Exception as e:
            logger.warning("Health deep check (db) failed: %s", e)
            out["database"] = "error"
            out["status"] = "degraded"
    return out
