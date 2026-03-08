#!/usr/bin/env bash
# Register a user via API. Requires backend running.
# Usage: ./scripts/register.sh [email] [password]
# Or:    EMAIL=user@example.com PASSWORD=secret ./scripts/register.sh

set -e

API_URL="${API_URL:-http://localhost:8000}"
EMAIL="${1:-${REGISTER_EMAIL:-liril625@gmail.com}}"
PASSWORD="${2:-${REGISTER_PASSWORD:-123456}}"

echo "Waiting for backend at $API_URL..."
for i in $(seq 1 15); do
  if curl -sf "$API_URL/health" >/dev/null 2>&1; then
    echo "Backend is up. Registering $EMAIL ..."
    curl -s -X POST "$API_URL/auth/register" \
      -H 'Content-Type: application/json' \
      -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"
    echo ""
    exit 0
  fi
  sleep 2
done

echo "Backend did not become ready. Start it with: make backend"
exit 1
