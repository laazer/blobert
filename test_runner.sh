#!/bin/bash
# Simple test runner for formatting_check tests

set -e

ROOT="/Users/jacobbrandt/workspace/blobert"
cd "$ROOT"

# Try to find pytest
if command -v pytest &> /dev/null; then
    PYTEST="pytest"
elif [ -f "asset_generation/python/.venv/bin/pytest" ]; then
    PYTEST="asset_generation/python/.venv/bin/pytest"
elif command -v python3 &> /dev/null; then
    PYTEST="python3 -m pytest"
elif command -v python &> /dev/null; then
    PYTEST="python -m pytest"
else
    echo "pytest not found. Please install pytest."
    exit 1
fi

echo "Using pytest: $PYTEST"
echo ""
echo "Running formatting_check tests..."
$PYTEST tests/ci/test_formatting_check.py -v
$PYTEST tests/ci/test_formatting_check_adversarial.py -v
$PYTEST tests/ci/test_formatting_check_mutation.py -v

echo ""
echo "All tests completed!"
