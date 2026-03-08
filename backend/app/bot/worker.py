"""
Celery app and automation task. Run with: celery -A app.bot.worker worker -l info
"""
from app.config import get_settings
from app.services.automation_service import AutomationService
from celery import Celery

settings = get_settings()

celery_app = Celery(
    "instagram_automation",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
    include=["app.bot.worker"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(bind=True, name="app.bot.worker.run_automation_task")
def run_automation_task(self, task_id: str) -> None:
    """Celery task: run automation for the given task id (sync wrapper around async)."""
    import asyncio
    asyncio.run(AutomationService.run_task(task_id))
