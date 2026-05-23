#!/usr/bin/env bash
# One-off profiler for py-tests.sh steps (wall-clock per phase).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY_ROOT="$ROOT/asset_generation/python"
GIT_ROOT="$ROOT"
MYPY_CHECK="$ROOT/.lefthook/scripts/mypy-scoped-check.sh"

cd "$PY_ROOT"

if [[ -x "$PY_ROOT/.venv/bin/python" ]] && "$PY_ROOT/.venv/bin/python" -c "import pytest" 2>/dev/null; then
  PY_MODE="venv"
  PY_BIN="$PY_ROOT/.venv/bin/python"
else
  PY_MODE="uv"
  PY_BIN=""
fi

_py_invoke() {
  if [[ "$PY_MODE" = "uv" ]]; then
    uv run --extra dev python "$@"
  else
    "$PY_BIN" "$@"
  fi
}

_run_pytest_ci() {
  (cd "$GIT_ROOT" && _py_invoke -m pytest tests/ci -q)
}

_step() {
  local label="$1"
  shift
  local start end
  start="$(date +%s)"
  echo ""
  echo ">>> START: $label ($(date -Iseconds))"
  "$@"
  end="$(date +%s)"
  echo "<<< END:   $label (wall $((end - start))s)"
}

echo "profile-py-tests: PY_MODE=$PY_MODE"
echo "profile-py-tests: HEAD=$(git -C "$GIT_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"

_step "ruff" bash -c '
  if [[ -x "'"$PY_ROOT"'/.venv/bin/ruff" ]]; then
    "'"$PY_ROOT"'/.venv/bin/ruff" check src tests main.py
  else
    uv run --directory "'"$PY_ROOT"'" --extra dev ruff check src tests main.py
  fi
'

_step "mypy-scoped" bash "$MYPY_CHECK"

_step "pytest-run-contract" _py_invoke -m pytest tests/api/test_run_contract.py -q

_step "pytest-tests-ci" _run_pytest_ci

_step "pytest-asset-no-cov" _py_invoke -m pytest tests/ -q --ignore=tests/api/test_run_contract.py

_step "pytest-asset-cov" _py_invoke -m pytest tests/ -q \
  --ignore=tests/api/test_run_contract.py \
  --cov=src --cov-config=pyproject.toml \
  --cov-report=term-missing:skip-covered --cov-report=xml

compare=""
for b in origin/main origin/master main master; do
  if git -C "$GIT_ROOT" rev-parse --verify "$b" >/dev/null 2>&1; then
    compare="$b"
    break
  fi
done
if [[ -f "$PY_ROOT/coverage.xml" ]]; then
  _step "diff-cover" _py_invoke -m diff_cover.diff_cover_tool \
    "$PY_ROOT/coverage.xml" --compare-branch="${compare:-origin/main}" --fail-under=85
else
  echo "SKIP diff-cover: no coverage.xml"
fi

echo ""
echo "profile-py-tests: done"
