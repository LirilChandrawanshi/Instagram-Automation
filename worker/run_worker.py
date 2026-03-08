"""
Celery worker entrypoint. From project root:
  celery -A app.bot.worker worker -l info

Or from backend directory with PYTHONPATH=.:
  celery -A app.bot.worker worker -l info
"""
# This file exists so the worker process can be started from the worker/ directory.
# In Docker, use: CMD ["celery", "-A", "app.bot.worker", "worker", "-l", "info"]
# with working directory set to backend (or project root with PYTHONPATH=backend).
