#!/usr/bin/env bash
# Restart both backend and frontend with a single command.
# Usage: ./scripts/restart.sh
#   or:  make restart

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"

# ─── Colors ───
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}⏳ Stopping existing processes...${NC}"

# Kill any running backend (uvicorn / python run.py)
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "  ✓ Backend stopped" || echo "  – No backend running"
pkill -f "python run.py" 2>/dev/null || true

# Kill any running frontend (next dev)
pkill -f "next dev" 2>/dev/null && echo "  ✓ Frontend stopped" || echo "  – No frontend running"
pkill -f "next-router-worker" 2>/dev/null || true

# Small wait for ports to free up
sleep 1

# ─── Start Backend ───
echo ""
echo -e "${GREEN}🚀 Starting Backend (port 8000)...${NC}"
cd "$BACKEND_DIR"
if [ ! -d .venv ]; then
  echo -e "${RED}❌ Backend venv not found. Run: make install-backend${NC}"
  exit 1
fi
PYTHONPATH=. .venv/bin/python run.py &
BACKEND_PID=$!
echo "  PID: $BACKEND_PID"

# ─── Start Frontend ───
echo -e "${GREEN}🚀 Starting Frontend (port 3000)...${NC}"
cd "$FRONTEND_DIR"
if [ ! -f node_modules/.package-lock.json ]; then
  echo -e "${YELLOW}📦 Running npm install first...${NC}"
  npm install --silent
fi
npm run dev &
FRONTEND_PID=$!
echo "  PID: $FRONTEND_PID"

# ─── Wait for backend health ───
echo ""
echo -e "${YELLOW}⏳ Waiting for backend to be ready...${NC}"
for i in $(seq 1 20); do
  if curl -sf "http://localhost:8000/health" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is ready!${NC}"
    break
  fi
  if [ "$i" -eq 20 ]; then
    echo -e "${RED}⚠️  Backend took too long. Check logs.${NC}"
  fi
  sleep 1
done

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ All services running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  🔗 API:       http://localhost:8000"
echo -e "  🔗 Dashboard: http://localhost:3000"
echo -e "  🔗 Docs:      http://localhost:8000/docs"
echo ""
echo -e "  Backend PID:  $BACKEND_PID"
echo -e "  Frontend PID: $FRONTEND_PID"
echo ""
echo -e "  To stop:  ${YELLOW}make stop${NC}"
echo ""

# Keep script running so both processes stay alive
# Ctrl+C will kill everything
trap "echo ''; echo -e '${RED}Stopping all services...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
