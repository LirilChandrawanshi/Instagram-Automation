#!/usr/bin/env bash
# Start backend in background, wait for it to be ready, then run registration.
# Usage: ./scripts/start-and-register.sh
#        EMAIL=user@example.com PASSWORD=secret ./scripts/start-and-register.sh

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="${API_URL:-http://localhost:8000}"
EMAIL="${EMAIL:-${REGISTER_EMAIL:-liril625@gmail.com}}"
PASSWORD="${PASSWORD:-${REGISTER_PASSWORD:-123456}}"

cd "$ROOT/backend"
if ! [ -d .venv ]; then
  echo "Run 'make install-backend' first."
  exit 1
fi

echo "Starting backend in background..."
PYTHONPATH=. .venv/bin/python run.py &
BACKEND_PID=$!
trap "kill $BACKEND_PID 2>/dev/null || true" EXIT

echo "Waiting for backend at $API_URL..."
for i in $(seq 1 30); do
  if curl -sf "$API_URL/health" >/dev/null 2>&1; then
    echo "Backend is up. Registering $EMAIL ..."
    curl -s -X POST "$API_URL/auth/register" \
      -H 'Content-Type: application/json' \
      -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"
    echo ""
    echo "Backend is still running (PID $BACKEND_PID). Stop with: kill $BACKEND_PID"
    trap - EXIT
    exit 0
  fi
  sleep 2
done

echo "Backend did not become ready in time."
kill $BACKEND_PID 2>/dev/null || true
exit 1
