# Instagram Automation Backend
FROM python:3.12-slim

WORKDIR /app

# Install Playwright dependencies and system libs for PostgreSQL/async
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (optional; can be skipped if worker runs separately)
RUN playwright install chromium
RUN playwright install-deps chromium || true

COPY . .
ENV PYTHONPATH=/app
EXPOSE 8000

# Default: run API. Override in docker-compose for worker.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
