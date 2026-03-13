#!/bin/bash

# Run Godot tests headless and exit with timeout to prevent hanging.
# Requires direnv (or bin/ on PATH) so that `godot` resolves to the headless wrapper.
godot --import 2>/dev/null
godot --check-only || exit 1
godot -s tests/run_tests.gd