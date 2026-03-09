# Instagram Automation Platform

## Quick start (with Docker)

If you have Docker installed:

```bash
docker compose up --build -d
```

- API: http://localhost:8000  
- Dashboard: http://localhost:3000  
- Docs: http://localhost:8000/docs  

## Local development (no Docker)

### 1. Database and Redis

Create the PostgreSQL database (if not using Docker):

```bash
# Using default postgres user (may need sudo or role creation)
createdb instagram_automation

# Or via psql (as a user with createdb permission)
psql -U postgres -c "CREATE DATABASE instagram_automation;"
```

Start Redis (e.g. `brew services start redis` or run `redis-server`).

### 2. Backend

**Option A – SQLite (no PostgreSQL):**  
In `backend/.env` set `USE_SQLITE=true`. Then:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Ensure USE_SQLITE=true in .env for no-PostgreSQL run

PYTHONPATH=. python run.py
```

**Option B – PostgreSQL:**  
Create DB (e.g. `createdb instagram_automation` or `python scripts/create_db.py`), then:

```bash
PYTHONPATH=. alembic upgrade head
PYTHONPATH=. python run.py
```

API: http://localhost:8000

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Dashboard: http://localhost:3000

### 4. Celery worker (optional, for automation tasks)

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. celery -A app.bot.worker worker -l info
```

## Makefile and scripts

From the project root:

- `make install-backend` – create venv and install Python deps  
- `make install-frontend` – npm install in frontend  
- `make migrate` – run Alembic migrations  
- `make backend` – start API (foreground)  
- `make frontend` – start Next.js (foreground)  
- `make register` – wait for backend, then POST `/auth/register` (default email/password in Makefile)  
- `make run` – start backend in background, wait for health, then run register  
- `make test-backend` – run backend smoke tests  

Override email/password:

```bash
make register REGISTER_EMAIL=you@example.com REGISTER_PASSWORD=yourpass
# or
./scripts/register.sh you@example.com yourpass
```

## Playwright (automation)

The app uses **Firefox** by default to avoid Chromium crashes (e.g. SEGV on macOS). Install it in the backend venv:

```bash
cd backend && source .venv/bin/activate && playwright install firefox
```

To use Chromium instead, set in backend `.env`: `PLAYWRIGHT_BROWSER=chromium` and run `playwright install chromium`.

## Anti-ban and safety

See **[docs/ANTI_BAN_AND_SAFETY.md](docs/ANTI_BAN_AND_SAFETY.md)** for proxy, device fingerprint, warm-up, action limits, block detection, and bulk-follow behaviour. After pulling, run migrations so new account columns exist:

```bash
cd backend && source .venv/bin/activate && PYTHONPATH=. alembic upgrade head
```

(SQLite: set `USE_SQLITE=true` and ensure `database_url` in config points to your SQLite file, or use `get_database_url()` in `alembic/env.py`.)

## Environment

- **Backend** `.env`: `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `JWT_SECRET`, `PLAYWRIGHT_BROWSER` (default `firefox`)
- **Frontend** `.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000`
