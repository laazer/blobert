#!/bin/bash

# Run Godot tests headless and exit with timeout to prevent hanging.
# Requires direnv (or bin/ on PATH) so that `godot` resolves to the headless wrapper.
#
# Note: --check-only is intentionally omitted. In Godot 4.6.1 headless mode,
# --check-only initializes the main scene which runs physics-enabled scripts
# (no collision resolution), causing the process to hang indefinitely.
# The test runner below catches parse errors directly — any syntax error causes
# script load to fail with an explicit error before run_all() is called.
godot --import 2>/dev/null
godot -s tests/run_tests.gd