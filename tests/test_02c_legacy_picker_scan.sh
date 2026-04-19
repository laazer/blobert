#!/bin/bash

# Requirement 1: Code Inventory & Verification Scan
# Verify that no legacy or orphaned color picker references exist in the codebase.

set -e

FRONTEND_SRC="/Users/jacobbrandt/workspace/blobert/asset_generation/web/frontend/src"

echo "=== TEST 1.1: Grep scan for old picker component literals ==="
# A1.2: Grep scan returns zero matches for legacy picker keywords
LEGACY_KEYWORDS=("HexPickerComponent" "SimpleColorPicker" "BasicColorPicker" "LegacyColorPicker" "OldColorPicker")
FOUND_MATCHES=0

for keyword in "${LEGACY_KEYWORDS[@]}"; do
  COUNT=$(grep -r "$keyword" "$FRONTEND_SRC" --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l)
  if [ "$COUNT" -gt 0 ]; then
    echo "FAIL: Found $COUNT references to '$keyword'"
    grep -r "$keyword" "$FRONTEND_SRC" --include="*.ts" --include="*.tsx" 2>/dev/null || true
    FOUND_MATCHES=$((FOUND_MATCHES + COUNT))
  else
    echo "PASS: No references to '$keyword' found"
  fi
done

if [ "$FOUND_MATCHES" -gt 0 ]; then
  echo "FAIL: Legacy keyword scan found matches"
  exit 1
fi

echo ""
echo "=== TEST 1.2: Verify imports from ColorPickerUniversal only ==="
# A1.1: No imports of non-existent old picker files
# Check that all ColorPicker imports reference either ColorPickerUniversal or valid subdirectories (modes, common)
IMPORT_FILES=$(grep -r "import.*from.*[\"'].*ColorPicker" "$FRONTEND_SRC" --include="*.ts" --include="*.tsx" 2>/dev/null || true)

# Filter out valid imports: ColorPickerUniversal, ColorPicker/modes/*, ColorPicker/common/*, test files
INVALID_IMPORTS=$(echo "$IMPORT_FILES" | grep -v "ColorPickerUniversal" | grep -v "/ColorPicker/modes/" | grep -v "/ColorPicker/common/" | grep -v "/ColorPicker/color" | grep -v ".test.tsx" | grep -v ".test.ts" | grep -v "test files" || true)

if [ -n "$INVALID_IMPORTS" ]; then
  echo "FAIL: Found imports from non-universal ColorPicker files"
  echo "$INVALID_IMPORTS"
  exit 1
fi

echo "PASS: All ColorPicker imports are from ColorPickerUniversal or valid subdirectories"

echo ""
echo "=== TEST 1.3: Check for commented legacy code ==="
# A1.4: Remove all commented lines containing old picker references
COMMENT_PATTERNS=("// old picker" "// legacy color" "/\* ColorPicker \*/")
FOUND_COMMENTS=0

for pattern in "${COMMENT_PATTERNS[@]}"; do
  COUNT=$(grep -r "$pattern" "$FRONTEND_SRC" --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l || true)
  if [ "$COUNT" -gt 0 ]; then
    echo "FAIL: Found $COUNT comment lines matching '$pattern'"
    grep -r "$pattern" "$FRONTEND_SRC" --include="*.ts" --include="*.tsx" 2>/dev/null || true
    FOUND_COMMENTS=$((FOUND_COMMENTS + COUNT))
  else
    echo "PASS: No comments matching '$pattern'"
  fi
done

if [ "$FOUND_COMMENTS" -gt 0 ]; then
  echo "FAIL: Found legacy code comments"
  exit 1
fi

echo ""
echo "=== TEST 1.4: Verify clipboardHex utilities are actively used ==="
# A1.5: All clipboard hex functions are actively called from production code or used internally
CLIPBOARD_FUNCTIONS=("sanitizeHex" "hexForColorInput" "normalizeHexForBuildOption" "copyHexToClipboard" "readHexFromClipboard")

for func in "${CLIPBOARD_FUNCTIONS[@]}"; do
  # Check if function is imported/used in production code (excluding test files)
  # or if it's internal to clipboardHex module
  USAGE=$(grep -r "$func" "$FRONTEND_SRC" --include="*.tsx" --include="*.ts" | grep -v ".test.tsx" | grep -v ".test.ts" | head -1)

  if [ -z "$USAGE" ]; then
    echo "WARN: Function '$func' not used in any production code or tests"
  else
    echo "PASS: Function '$func' is used in production code or module"
  fi
done

echo ""
echo "=== TEST 1.5: Verify no orphaned snapshot directories ==="
# A1.6: Check that no __snapshots__ directories exist
SNAPSHOT_DIRS=$(find "$FRONTEND_SRC" -type d -name "__snapshots__" 2>/dev/null || true)

if [ -n "$SNAPSHOT_DIRS" ]; then
  echo "FAIL: Found snapshot directories:"
  echo "$SNAPSHOT_DIRS"
  exit 1
fi

echo "PASS: No __snapshots__ directories found"

echo ""
echo "=== ALL LEGACY PICKER SCAN TESTS PASSED ==="
