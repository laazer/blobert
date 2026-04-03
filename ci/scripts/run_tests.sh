#!/bin/bash

# Run Godot tests headless and exit with timeout to prevent hanging.
# Requires direnv (or bin/ on PATH) so that `godot` resolves to the headless wrapper.
#
# Note: --check-only is intentionally omitted. In Godot 4.6.1 headless mode,
# --check-only initializes the main scene which runs physics-enabled scripts
# (no collision resolution), causing the process to hang indefinitely.
# The test runner below catches parse errors directly — any syntax error causes
# script load to fail with an explicit error before run_all() is called.
# Import is bounded: unbounded `godot --import` can hang indefinitely in CI.
timeout 120 godot --headless --import 2>/dev/null || true
timeout 300 godot --headless -s tests/run_tests.gd
exit $?