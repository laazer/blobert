#!/usr/bin/env bash
# Run Python test suites: asset_generation/python (cov + diff-cover) and repo-root tests/ci.
# Triggered by pre-push when Python under asset_generation/python/, ci/scripts/, or tests/ci/ changed.
#
# After pytest + coverage XML, diff-cover gates changed lines vs a compare branch (default
# origin/main). Override: DIFF_COVER_COMPARE_BRANCH=origin/my-base DIFF_COVER_FAIL_UNDER=85
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY_ROOT="$ROOT/asset_generation/python"
GIT_ROOT="$ROOT"
MYPY_CHECK="$ROOT/.lefthook/scripts/mypy-scoped-check.sh"

cd "$PY_ROOT"

PYTEST_COV_ARGS=(
  tests/ -q
  --ignore=tests/api/test_run_contract.py
  --cov=src
  --cov-config=pyproject.toml
  --cov-report=term-missing:skip-covered
  --cov-report=xml
)

DIFF_COVER_FAIL_UNDER="${DIFF_COVER_FAIL_UNDER:-85}"

_run_ruff() {
  echo "pre-push: running Ruff (src, tests, main.py)..."
  local ruff_targets=(src tests main.py)
  if [ -x "$PY_ROOT/.venv/bin/ruff" ]; then
    "$PY_ROOT/.venv/bin/ruff" check "${ruff_targets[@]}"
  elif command -v uv >/dev/null 2>&1; then
    uv run --extra dev ruff check "${ruff_targets[@]}"
  elif command -v ruff >/dev/null 2>&1; then
    ruff check "${ruff_targets[@]}"
  else
    echo "pre-push: ruff not found. From asset_generation/python run: uv sync --extra dev" >&2
    exit 1
  fi
}

_py_invoke() {
  if [ "$PY_MODE" = "uv" ]; then
    uv run --extra dev python "$@"
  else
    "$PY_BIN" "$@"
  fi
}

_ensure_pytest_cov() {
  if ! _py_invoke -c "import pytest_cov" 2>/dev/null; then
    echo "pre-push: pytest-cov is required. From asset_generation/python run: uv sync --extra dev" >&2
    exit 1
  fi
}

_ensure_diff_cover() {
  if ! _py_invoke -c "import diff_cover" 2>/dev/null; then
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
  _py_invoke -m diff_cover.diff_cover_tool "$cov_xml" --compare-branch="$compare" --fail-under="$DIFF_COVER_FAIL_UNDER"
}

_run_pytest_cov() {
  echo "pre-push: running asset_generation Python tests (pytest + coverage XML)..."
  _py_invoke -m pytest "${PYTEST_COV_ARGS[@]}"
}

_run_pytest_run_contract_no_cov() {
  echo "pre-push: running /api/run contract tests without coverage (SSE/async tracer isolation)..."
  _py_invoke -m pytest tests/api/test_run_contract.py -q
}

_run_pytest_ci_scripts() {
  echo "pre-push: running repo-root tests/ci (gate + ci/scripts contracts)..."
  (cd "$GIT_ROOT" && _py_invoke -m pytest tests/ci -q)
}

_run_mypy_scoped() {
  bash "$MYPY_CHECK"
}

_run_all() {
  _run_ruff
  _run_mypy_scoped
  _ensure_pytest_cov
  _ensure_diff_cover
  _run_pytest_run_contract_no_cov
  _run_pytest_ci_scripts
  _run_pytest_cov
  _run_diff_cover
}

if [ -x "$PY_ROOT/.venv/bin/python" ] && "$PY_ROOT/.venv/bin/python" -c "import pytest" 2>/dev/null; then
  echo "pre-push: running Python checks (.venv)..."
  PY_MODE="venv"
  PY_BIN="$PY_ROOT/.venv/bin/python"
  _run_all
elif command -v uv >/dev/null 2>&1; then
  echo "pre-push: running Python checks (uv run --extra dev)..."
  PY_MODE="uv"
  PY_BIN=""
  _run_all
else
  echo "pre-push: need $PY_ROOT/.venv (with pytest) or uv on PATH — same env as hooks (see ci/scripts/asset_python.sh)." >&2
  echo "Run: cd $PY_ROOT && uv sync --extra dev" >&2
  exit 1
fi
