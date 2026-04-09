#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "=== Starting Blobert Asset Editor ==="

# Backend
cd "$BACKEND_DIR"
if [ ! -d ".venv" ]; then
  echo "Creating backend virtualenv..."
  if command -v python3.11 >/dev/null 2>&1; then
    python3.11 -m venv .venv
  else
    python3 -m venv .venv
  fi
  .venv/bin/pip install --quiet -r requirements.txt
fi
.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACK=$!
echo "Backend started (pid $BACK)"

# Frontend
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies (this may take a minute)..."
  npm install --silent
fi
npm run dev &
FRONT=$!
echo "Frontend started (pid $FRONT)"

trap 'echo "Shutting down..."; kill $BACK $FRONT 2>/dev/null; exit 0' INT TERM

echo ""
echo "Open http://localhost:5173"
echo "Press Ctrl+C to stop both servers."
echo ""

wait
