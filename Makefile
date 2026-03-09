# Instagram Automation Platform - common tasks
# Usage: make <target>

BACKEND_DIR := backend
FRONTEND_DIR := frontend
API_URL ?= http://localhost:8000
REGISTER_EMAIL ?= liril625@gmail.com
REGISTER_PASSWORD ?= 123456

.PHONY: install-backend install-frontend migrate backend frontend worker register run dev stop health test-backend

# Install backend deps (venv + pip)
install-backend:
	cd $(BACKEND_DIR) && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
	@echo "Copy $(BACKEND_DIR)/.env.example to $(BACKEND_DIR)/.env if needed."

# Install frontend deps
install-frontend:
	cd $(FRONTEND_DIR) && npm install

# Run DB migrations (requires PostgreSQL and DATABASE_URL in backend/.env)
migrate:
	cd $(BACKEND_DIR) && PYTHONPATH=. .venv/bin/alembic upgrade head

# Start backend (foreground)
backend:
	cd $(BACKEND_DIR) && PYTHONPATH=. .venv/bin/python run.py

# Start frontend (foreground)
frontend:
	cd $(FRONTEND_DIR) && npm run dev

# Start Celery worker (foreground)
worker:
	cd $(BACKEND_DIR) && PYTHONPATH=. .venv/bin/celery -A app.bot.worker worker -l info

# Wait for backend to be up, then POST /auth/register. Set REGISTER_EMAIL and REGISTER_PASSWORD if needed.
register:
	@echo "Waiting for backend at $(API_URL)..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if curl -sf "$(API_URL)/health" > /dev/null; then \
			echo "Backend is up. Registering..."; \
			curl -s -X POST "$(API_URL)/auth/register" \
				-H 'Content-Type: application/json' \
				-d "{\"email\":\"$(REGISTER_EMAIL)\",\"password\":\"$(REGISTER_PASSWORD)\"}" | python3 -m json.tool; \
			exit 0; \
		fi; \
		sleep 2; \
	done; \
	echo "Backend did not become ready. Start it with: make backend"; exit 1

# Start backend in background, wait for health, then run register (see scripts/start-and-register.sh)
run:
	@chmod +x scripts/start-and-register.sh 2>/dev/null || true
	@./scripts/start-and-register.sh

# Start both backend and frontend together (foreground)
dev:
	@echo "Starting backend and frontend..."
	@trap 'kill 0' EXIT; \
	(cd $(BACKEND_DIR) && PYTHONPATH=. .venv/bin/python run.py) & \
	(cd $(FRONTEND_DIR) && npm run dev) & \
	wait

# Stop all running dev processes
stop:
	@echo "Stopping backend and frontend..."
	@-pkill -f "$(BACKEND_DIR)/run.py" 2>/dev/null || true
	@-pkill -f "next dev" 2>/dev/null || true
	@echo "Stopped."

# Check backend health
health:
	@curl -sf "$(API_URL)/health" && echo " OK" || (echo "Backend not reachable at $(API_URL)"; exit 1)

# Run backend tests
test-backend:
	cd $(BACKEND_DIR) && .venv/bin/python -m pytest -q
