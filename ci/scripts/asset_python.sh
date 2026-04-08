#!/usr/bin/env bash
# Run Python using the asset_generation/python project environment only.
#
# Resolution order:
#   1) asset_generation/python/.venv/bin/python if present and executable
#   2) uv run --extra dev python (from that project) if uv is on PATH
#
# Hooks and Taskfile should use this instead of bare python3 so Ruff/pytest/py_compile
# match the same interpreter and wheel architecture as uv sync.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY_ROOT="$REPO_ROOT/asset_generation/python"

if [[ ! -d "$PY_ROOT" ]]; then
  echo "asset_python: missing $PY_ROOT" >&2
  exit 127
fi

if [[ -x "$PY_ROOT/.venv/bin/python" ]]; then
  exec "$PY_ROOT/.venv/bin/python" "$@"
fi

if command -v uv >/dev/null 2>&1; then
  cd "$PY_ROOT"
  exec uv run --extra dev python "$@"
fi

echo "asset_python: no venv at $PY_ROOT/.venv and uv not on PATH." >&2
echo "Create the env: cd $PY_ROOT && uv sync --extra dev" >&2
exit 127
