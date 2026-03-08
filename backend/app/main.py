"""
FastAPI application entrypoint.
Mounts auth, accounts, tasks, and analytics routes.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.api.auth import router as auth_router
from app.api.accounts import router as accounts_router
from app.api.tasks import router as tasks_router
from app.api.analytics import router as analytics_router
from app.services.scheduler_service import SchedulerService

settings = get_settings()
SCHEDULER_INTERVAL_SEC = 60


async def _scheduled_tasks_loop() -> None:
    """Every N seconds run pending tasks that are due. Only used when RUN_TASKS_INLINE=true."""
    while True:
        await asyncio.sleep(SCHEDULER_INTERVAL_SEC)
        try:
            await SchedulerService.run_due_scheduled_tasks()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup. Start scheduler loop when running tasks inline."""
    await init_db()
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(tasks_router)
app.include_router(analytics_router)


@app.get("/health")
async def health() -> dict:
    """Health check for Docker/load balancers."""
    return {"status": "ok"}
