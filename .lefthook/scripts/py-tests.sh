#!/usr/bin/env bash
# Run the Python test suite for asset_generation/python/.
# Triggered by pre-push when any .py file under asset_generation/python/ changed.
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/asset_generation/python"

if ! python3 -c "import pytest" 2>/dev/null; then
  echo "pre-push: pytest not found. Run: pip install -e '.[dev]' in asset_generation/python/" >&2
  exit 1
fi

echo "pre-push: running asset_generation Python tests..."
python3 -m pytest tests/ -q
