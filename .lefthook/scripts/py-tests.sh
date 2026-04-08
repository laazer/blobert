#!/usr/bin/env bash
# Run the Python test suite for asset_generation/python/.
# Triggered by pre-push when any .py file under asset_generation/python/ changed.
#
# After pytest + coverage XML, diff-cover gates changed lines vs a compare branch (default
# origin/main). Override: DIFF_COVER_COMPARE_BRANCH=origin/my-base DIFF_COVER_FAIL_UNDER=85
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY_ROOT="$ROOT/asset_generation/python"
cd "$PY_ROOT"

# Repo root for git diff (coverage.xml lives in PY_ROOT).
GIT_ROOT="$ROOT"

_run_ruff() {
  echo "pre-push: running Ruff (src, tests, main.py)..."
  if [ -x "$PY_ROOT/.venv/bin/ruff" ]; then
    "$PY_ROOT/.venv/bin/ruff" check src tests main.py
  elif command -v uv >/dev/null 2>&1; then
    uv run --extra dev ruff check src tests main.py
  elif command -v ruff >/dev/null 2>&1; then
    ruff check src tests main.py
  else
    echo "pre-push: ruff not found. From asset_generation/python run: uv sync --extra dev" >&2
    exit 1
  fi
}

PYTEST_COV_ARGS=(
  tests/ -q
  --cov=src
  --cov-config=pyproject.toml
  --cov-report=term-missing:skip-covered
  --cov-report=xml
)

DIFF_COVER_FAIL_UNDER="${DIFF_COVER_FAIL_UNDER:-85}"

_ensure_pytest_cov() {
  local py="$1"
  if ! "$py" -c "import pytest_cov" 2>/dev/null; then
    echo "pre-push: pytest-cov is required. From asset_generation/python run: uv sync --extra dev" >&2
    exit 1
  fi
}

_ensure_diff_cover() {
  local py="$1"
  if ! "$py" -c "import diff_cover" 2>/dev/null; then
    echo "pre-push: diff-cover is required. From asset_generation/python run: uv sync --extra dev" >&2
    exit 1
  fi
}

_diff_cover_compare_branch() {
  if [ -n "${DIFF_COVER_COMPARE_BRANCH:-}" ]; then
    echo "${DIFF_COVER_COMPARE_BRANCH}"
    return 0
  fi
  local b
  for b in origin/main origin/master main master; do
    if git -C "$GIT_ROOT" rev-parse --verify "$b" >/dev/null 2>&1; then
      echo "$b"
      return 0
    fi
  done
  return 1
}

_run_diff_cover() {
  local py="$1"
  local cov_xml="$PY_ROOT/coverage.xml"
  if [ ! -f "$cov_xml" ]; then
    echo "pre-push: missing $cov_xml after pytest" >&2
    exit 1
  fi
  local compare
  if ! compare="$(_diff_cover_compare_branch)"; then
    echo "pre-push: diff-cover needs a git compare branch (try: git fetch origin). Set DIFF_COVER_COMPARE_BRANCH to override." >&2
    exit 1
  fi
  echo "pre-push: diff-cover (fail-under=${DIFF_COVER_FAIL_UNDER}% vs ${compare})..."
  "$py" -m diff_cover.diff_cover_tool "$cov_xml" --compare-branch="$compare" --fail-under="$DIFF_COVER_FAIL_UNDER"
}

_run_pytest() {
  local py="$1"
  echo "pre-push: running asset_generation Python tests (pytest + coverage XML)..."
  "$py" -m pytest "${PYTEST_COV_ARGS[@]}"
}

# Prefer project .venv when it already has pytest (no index fetch; works behind broken mirrors).
if [ -x "$PY_ROOT/.venv/bin/python" ] && "$PY_ROOT/.venv/bin/python" -c "import pytest" 2>/dev/null; then
  echo "pre-push: running asset_generation Python tests (.venv)..."
  _run_ruff
  _ensure_pytest_cov "$PY_ROOT/.venv/bin/python"
  _ensure_diff_cover "$PY_ROOT/.venv/bin/python"
  _run_pytest "$PY_ROOT/.venv/bin/python"
  _run_diff_cover "$PY_ROOT/.venv/bin/python"
elif command -v uv >/dev/null 2>&1; then
  echo "pre-push: running asset_generation Python tests (uv run --extra dev)..."
  _run_ruff
  if ! uv run --extra dev python -c "import pytest_cov, diff_cover" 2>/dev/null; then
    echo "pre-push: pytest-cov and diff-cover required. From asset_generation/python run: uv sync --extra dev" >&2
    exit 1
  fi
  uv run --extra dev pytest "${PYTEST_COV_ARGS[@]}"
  compare="$(_diff_cover_compare_branch)" || {
    echo "pre-push: diff-cover needs a git compare branch (try: git fetch origin). Set DIFF_COVER_COMPARE_BRANCH to override." >&2
    exit 1
  }
  echo "pre-push: diff-cover (fail-under=${DIFF_COVER_FAIL_UNDER}% vs ${compare})..."
  uv run --extra dev python -m diff_cover.diff_cover_tool "$PY_ROOT/coverage.xml" --compare-branch="$compare" --fail-under="$DIFF_COVER_FAIL_UNDER"
else
  echo "pre-push: need $PY_ROOT/.venv (with pytest) or uv on PATH — same env as hooks (see ci/scripts/asset_python.sh)." >&2
  echo "Run: cd $PY_ROOT && uv sync --extra dev" >&2
  exit 1
fi
