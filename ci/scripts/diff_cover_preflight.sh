#!/usr/bin/env bash
# diff-cover preflight — run before implementation handoff to catch coverage gaps early.
#
# Runs diff-cover against origin/main (or DIFF_COVER_COMPARE_BRANCH) in report-only mode
# and exits non-zero if coverage falls below DIFF_COVER_FAIL_UNDER (default 85%).
#
# Usage:
#   bash ci/scripts/diff_cover_preflight.sh
#
# Environment overrides:
#   DIFF_COVER_COMPARE_BRANCH=origin/my-base  (default: auto-detected origin/main)
#   DIFF_COVER_FAIL_UNDER=80                  (default: 85)
#   DIFF_COVER_SKIP_PYTEST=1                  (skip running pytest; use existing coverage.xml)
#
# Exit codes:
#   0  — coverage at or above threshold (or no Python changes detected)
#   1  — coverage below threshold
#   2  — setup error (missing tools, no coverage.xml, no compare branch)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY_ROOT="$ROOT/asset_generation/python"

DIFF_COVER_FAIL_UNDER="${DIFF_COVER_FAIL_UNDER:-85}"
DIFF_COVER_SKIP_PYTEST="${DIFF_COVER_SKIP_PYTEST:-0}"

# ---------------------------------------------------------------------------
# Detect compare branch
# ---------------------------------------------------------------------------
_compare_branch() {
  if [ -n "${DIFF_COVER_COMPARE_BRANCH:-}" ]; then
    echo "${DIFF_COVER_COMPARE_BRANCH}"
    return 0
  fi
  for b in origin/main origin/master main master; do
    if git -C "$ROOT" rev-parse --verify "$b" >/dev/null 2>&1; then
      echo "$b"
      return 0
    fi
  done
  return 1
}

# ---------------------------------------------------------------------------
# Check if there are any Python changes vs compare branch
# ---------------------------------------------------------------------------
_has_python_changes() {
  local compare="$1"
  git -C "$ROOT" diff --name-only "$compare"...HEAD -- '*.py' | grep -q . 2>/dev/null
}

# ---------------------------------------------------------------------------
# Resolve Python interpreter
# ---------------------------------------------------------------------------
_python() {
  if [ -x "$PY_ROOT/.venv/bin/python" ] && "$PY_ROOT/.venv/bin/python" -c "import pytest_cov, diff_cover" 2>/dev/null; then
    echo "$PY_ROOT/.venv/bin/python"
  elif command -v uv >/dev/null 2>&1; then
    echo "uv_run"
  else
    echo ""
  fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
compare=""
if ! compare="$(_compare_branch)"; then
  echo "diff-cover-preflight: no compare branch found." >&2
  echo "  Run: git fetch origin  or set DIFF_COVER_COMPARE_BRANCH=<ref>" >&2
  exit 2
fi

echo "diff-cover-preflight: compare branch = $compare, threshold = ${DIFF_COVER_FAIL_UNDER}%"

if ! _has_python_changes "$compare"; then
  echo "diff-cover-preflight: no Python file changes vs $compare — skipping."
  exit 0
fi

cd "$PY_ROOT"

PYTEST_COV_ARGS=(
  tests/ -q
  --cov=src
  --cov-config=pyproject.toml
  --cov-report=xml
  --tb=no -q
)

py="$(_python)"
if [ -z "$py" ]; then
  echo "diff-cover-preflight: no suitable Python env found." >&2
  echo "  Run: cd $PY_ROOT && uv sync --extra dev" >&2
  exit 2
fi

# Run pytest to generate fresh coverage.xml (unless skipped)
if [ "$DIFF_COVER_SKIP_PYTEST" != "1" ]; then
  echo "diff-cover-preflight: running pytest to generate coverage.xml..."
  if [ "$py" = "uv_run" ]; then
    uv run --extra dev pytest "${PYTEST_COV_ARGS[@]}"
  else
    "$py" -m pytest "${PYTEST_COV_ARGS[@]}"
  fi
fi

COV_XML="$PY_ROOT/coverage.xml"
if [ ! -f "$COV_XML" ]; then
  echo "diff-cover-preflight: coverage.xml not found at $COV_XML" >&2
  echo "  Run pytest with --cov first, or unset DIFF_COVER_SKIP_PYTEST." >&2
  exit 2
fi

echo "diff-cover-preflight: running diff-cover (fail-under=${DIFF_COVER_FAIL_UNDER}% vs ${compare})..."

set +e
if [ "$py" = "uv_run" ]; then
  uv run --extra dev python -m diff_cover.diff_cover_tool \
    "$COV_XML" \
    --compare-branch="$compare" \
    --fail-under="$DIFF_COVER_FAIL_UNDER"
else
  "$py" -m diff_cover.diff_cover_tool \
    "$COV_XML" \
    --compare-branch="$compare" \
    --fail-under="$DIFF_COVER_FAIL_UNDER"
fi
EXIT_CODE=$?
set -e

if [ $EXIT_CODE -eq 0 ]; then
  echo "diff-cover-preflight: PASS — coverage meets threshold."
else
  echo ""
  echo "diff-cover-preflight: FAIL — coverage below ${DIFF_COVER_FAIL_UNDER}% threshold."
  echo "  Add tests for the uncovered new lines listed above before handoff."
fi

exit $EXIT_CODE
