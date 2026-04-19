#!/bin/bash

# Requirement 6: Full Build & Test Verification
# Verify that the frontend application builds successfully and all tests pass.

set -e

FRONTEND_DIR="/Users/jacobbrandt/workspace/blobert/asset_generation/web/frontend"

echo "=== TEST 6.1: Run all tests ==="
# A6.1: npm test runs and all tests pass (exit code 0)
cd "$FRONTEND_DIR"

echo "Running npm test..."
if npm test 2>&1 | tee test-output.log; then
  echo "PASS: All tests passed"
  TEST_PASSED=1
else
  echo "FAIL: Tests failed"
  TEST_PASSED=0
fi

# Verify test output contains success indicator
if grep -q -E "passed|succeed" test-output.log; then
  echo "PASS: Test output contains success summary"
else
  echo "WARN: Could not find explicit success summary in test output"
fi

if [ "$TEST_PASSED" -ne 1 ]; then
  exit 1
fi

echo ""
echo "=== TEST 6.2: Build frontend application ==="
# A6.2: npm run build completes without errors and generates dist/
echo "Running npm run build..."
if npm run build 2>&1 | tee build-output.log; then
  echo "PASS: Build completed successfully"
  BUILD_PASSED=1
else
  echo "FAIL: Build failed"
  BUILD_PASSED=0
fi

if [ "$BUILD_PASSED" -ne 1 ]; then
  exit 1
fi

# Verify dist directory was created
if [ -d "$FRONTEND_DIR/dist" ]; then
  echo "PASS: dist/ directory created"
  DIST_FILES=$(find "$FRONTEND_DIR/dist" -type f | head -5)
  if [ -n "$DIST_FILES" ]; then
    echo "PASS: dist/ contains files"
  else
    echo "FAIL: dist/ directory is empty"
    exit 1
  fi
else
  echo "FAIL: dist/ directory not created"
  exit 1
fi

echo ""
echo "=== TEST 6.3: Build output warnings check ==="
# A6.3: Build output does not contain warnings about missing color picker components
WARN_COUNT=$(grep -i "missing\|deprecated.*color.*picker" build-output.log | wc -l || true)

if [ "$WARN_COUNT" -gt 0 ]; then
  echo "FAIL: Found warnings about missing/deprecated color picker components:"
  grep -i "missing\|deprecated.*color.*picker" build-output.log || true
  exit 1
fi

echo "PASS: No warnings about missing color picker components"

echo ""
echo "=== TEST 6.4: Console errors related to ColorPicker/HexStr ==="
# A6.4: No console.warn/error logs related to ColorPicker or HexStr components
CONSOLE_ERRORS=$(grep -i "console\.\(warn\|error\).*\(ColorPicker\|HexStr\)" test-output.log | wc -l || true)

if [ "$CONSOLE_ERRORS" -gt 0 ]; then
  echo "FAIL: Found console.warn/error logs related to color picker:"
  grep -i "console\.\(warn\|error\).*\(ColorPicker\|HexStr\)" test-output.log || true
  exit 1
fi

echo "PASS: No ColorPicker/HexStr console errors found"

echo ""
echo "=== TEST 6.5: Tree-shaking and circular import detection ==="
# A6.5: Vite build does not fail on tree-shaking or circular import detection
TREE_SHAKE_ERRORS=$(grep -i "circular\|tree.shake" build-output.log | grep -i "error" | wc -l || true)

if [ "$TREE_SHAKE_ERRORS" -gt 0 ]; then
  echo "FAIL: Found tree-shaking or circular import errors:"
  grep -i "circular\|tree.shake" build-output.log || true
  exit 1
fi

echo "PASS: No tree-shaking or circular import errors detected"

echo ""
echo "=== Cleanup ==="
rm -f "$FRONTEND_DIR/test-output.log" "$FRONTEND_DIR/build-output.log"

echo ""
echo "=== ALL BUILD AND TEST VERIFICATION TESTS PASSED ==="
