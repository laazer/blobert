#!/usr/bin/env bash
# Run the Python test suite for asset_generation/python/.
# Triggered by pre-push when any .py file under asset_generation/python/ changed.
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY_ROOT="$ROOT/asset_generation/python"
cd "$PY_ROOT"

_run_pytest() {
  local py="$1"
  echo "pre-push: running asset_generation Python tests..."
  "$py" -m pytest tests/ -q
}

# Prefer project .venv when it already has pytest (no index fetch; works behind broken mirrors).
if [ -x "$PY_ROOT/.venv/bin/python" ] && "$PY_ROOT/.venv/bin/python" -c "import pytest" 2>/dev/null; then
  echo "pre-push: running asset_generation Python tests (.venv)..."
  _run_pytest "$PY_ROOT/.venv/bin/python"
elif command -v uv >/dev/null 2>&1; then
  echo "pre-push: running asset_generation Python tests (uv run --extra dev)..."
  uv run --extra dev pytest tests/ -q
elif python3 -c "import pytest" 2>/dev/null; then
  _run_pytest python3
else
  echo "pre-push: pytest not found. From asset_generation/python run: uv sync --extra dev" >&2
  exit 1
fi
