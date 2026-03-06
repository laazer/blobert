#!/bin/bash

# Run Godot tests headless and exit with timeout to prevent hanging
gtimeout 300 godot --headless -s tests/run_tests.gd