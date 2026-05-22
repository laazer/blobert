#!/usr/bin/env bash
# Repo-root tests/ci (gate + ci/scripts contracts). Pre-push only when ci/scripts or tests/ci change.
set -e

# shellcheck source=hook-noninteractive.sh
source "$(cd "$(dirname "$0")" && pwd)/hook-noninteractive.sh"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY_ROOT="$ROOT/asset_generation/python"
GIT_ROOT="$ROOT"

cd "$PY_ROOT"

_py_invoke() {
  if [[ -x "$PY_ROOT/.venv/bin/python" ]] && "$PY_ROOT/.venv/bin/python" -c "import pytest" 2>/dev/null; then
    "$PY_ROOT/.venv/bin/python" "$@"
  elif command -v uv >/dev/null 2>&1; then
    uv run --extra dev python "$@"
  else
    echo "pre-push: need $PY_ROOT/.venv (with pytest) or uv on PATH." >&2
    exit 1
  fi
}

echo "pre-push: running repo-root tests/ci (gate + ci/scripts contracts)..."
(cd "$GIT_ROOT" && _py_invoke -m pytest tests/ci -q)
