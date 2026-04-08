#!/usr/bin/env bash
# Run the full Godot test suite.
# Triggered by pre-push when any .gd, .tscn, .tres, or .gdshader file changed.
# Mirrors ci/scripts/run_tests.sh but uses bin/godot directly (direnv not active in hooks).
#
# Python diff-cover (lefthook py-tests hook) uses DIFF_COVER_FAIL_UNDER / DIFF_COVER_COMPARE_BRANCH;
# this script does not invoke pytest — env vars pass through from your shell when hooks run.
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

GODOT="$ROOT/bin/godot"
if [[ ! -x "$GODOT" ]]; then
  echo "pre-push: bin/godot wrapper not found or not executable at $GODOT" >&2
  exit 1
fi

echo "pre-push: running Godot test suite..."

# Reimport to rebuild class cache — catches missing preload() paths.
# Bounded + fail-fast; matches ci/scripts/run_tests.sh (TSGR-2/TSGR-6).
timeout 120 "$GODOT" --import

# Run the test suite. 5-minute timeout matches CI (TSGR-4).
timeout 300 "$GODOT" -s tests/run_tests.gd
