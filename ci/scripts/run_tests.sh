#!/usr/bin/env bash
# Canonical combined test entry (MAINT-TSGR / TSGR-1): Godot headless suite then
# asset_generation/python/tests/ via shared lefthook Python hook (TSGR-3 DRY).
#
# Import: timeout 120s, fail-fast, stderr visible (TSGR-2). Godot tests: timeout 300s (TSGR-4).
# Requires `godot` on PATH (headless wrapper; direnv adds bin/ per CLAUDE.md).

set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

timeout 120 godot --headless --import
timeout 300 godot --headless -s tests/run_tests.gd

# Python suite: asset_generation/python/tests/ (TSGR-3: same resolver as lefthook).
bash "$ROOT/.lefthook/scripts/py-tests.sh"
