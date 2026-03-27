#!/usr/bin/env bash
# Run the full Godot test suite.
# Triggered by pre-push when any .gd, .tscn, .tres, or .gdshader file changed.
# Mirrors ci/scripts/run_tests.sh but uses bin/godot directly (direnv not active in hooks).
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
"$GODOT" --import 2>/dev/null || true

# Run the test suite. 5-minute timeout matches CI.
timeout 300 "$GODOT" -s tests/run_tests.gd
