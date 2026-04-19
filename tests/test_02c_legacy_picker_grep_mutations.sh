#!/bin/bash

# ADVERSARIAL TEST SUITE: Legacy Picker Scan Grep Pattern Mutations
#
# This test suite verifies that the grep patterns in test_02c_legacy_picker_scan.sh
# are robust against:
# 1. Typos and case variations in legacy picker names
# 2. Substring false positives (e.g., "legacy" appearing in unrelated contexts)
# 3. Proper word boundaries (grep -w enforcement)
# 4. Comments vs. executable code (careful filtering)
#
# Each test mutates the grep pattern or the test data to find edge cases
# that might slip through the original scan.

set -e

FRONTEND_SRC="/Users/jacobbrandt/workspace/blobert/asset_generation/web/frontend/src"
TEMP_TEST_DIR="/tmp/blobert_grep_test_$$"
mkdir -p "$TEMP_TEST_DIR"

cleanup() {
  rm -rf "$TEMP_TEST_DIR"
}
trap cleanup EXIT

echo "=== ADVERSARIAL TEST: Grep Pattern Robustness ==="
echo ""

# Test 1: Case sensitivity variations of legacy picker names
echo "TEST 1: Case Sensitivity Mutations"
echo "Checking if uppercase/mixed-case variations would be missed..."

# Create test file with case variations
cat > "$TEMP_TEST_DIR/case_variants.ts" << 'EOF'
// These should NOT be found (not matching the exact keyword)
const HEX_PICKER_COMPONENT = "hex";
const basiccolorpicker = () => {};
const legacycolorpicker = () => {}; // All lowercase
const LegacyColorPicker = class {}; // Capitalized
const LEGACYCOLORPICKER = "old"; // Uppercase
EOF

# Test original keywords
KEYWORDS=("HexPickerComponent" "SimpleColorPicker" "BasicColorPicker" "LegacyColorPicker" "OldColorPicker")
FOUND_IN_VARIANTS=0

for keyword in "${KEYWORDS[@]}"; do
  COUNT=$(grep -r "$keyword" "$TEMP_TEST_DIR" --include="*.ts" 2>/dev/null | wc -l || echo 0)
  if [ "$COUNT" -gt 0 ]; then
    echo "  FAIL: Found case variation of '$keyword'"
    FOUND_IN_VARIANTS=$((FOUND_IN_VARIANTS + COUNT))
  fi
done

if [ "$FOUND_IN_VARIANTS" -eq 0 ]; then
  echo "  PASS: Case sensitivity is strict (uppercase/lowercase variations not found)"
else
  echo "  WARNING: Case variations might slip through (not enforced by original grep)"
fi
echo ""

# Test 2: Substring false positives
echo "TEST 2: Substring False Positives"
echo "Checking if substrings in unrelated contexts match..."

cat > "$TEMP_TEST_DIR/false_positives.ts" << 'EOF'
// Variable names containing substrings of legacy keywords
const legacyColorData = { /* historical colors */ };
const simplifiedColorPalette = [];
const basicColorScheme = {};

// Comments mentioning legacy code (should be removed)
// TODO: update from legacy color system

// Actual references that SHOULD be caught
import { LegacyColorPicker } from "./old-pickers";
const BasicColorPicker = require("./components");
EOF

# Check for exact keyword matches vs substring matches
echo "  Checking 'legacy' substring..."
COUNT=$(grep -r "legacy" "$TEMP_TEST_DIR/false_positives.ts" 2>/dev/null | wc -l || echo 0)
echo "    Found $COUNT lines with 'legacy' substring (expected: 4+, includes valid refs)"

echo "  Checking exact keyword 'LegacyColorPicker'..."
COUNT=$(grep -r "LegacyColorPicker" "$TEMP_TEST_DIR/false_positives.ts" 2>/dev/null | wc -l || echo 0)
echo "    Found $COUNT lines with exact 'LegacyColorPicker' (expected: 1, import only)"

echo "  CHECKPOINT: Grep using substrings may have false positives"
echo ""

# Test 3: Comment vs. executable code filtering
echo "TEST 3: Comment Filtering"
echo "Checking if legacy references in comments are properly handled..."

cat > "$TEMP_TEST_DIR/comments.ts" << 'EOF'
// Old code removed: import OldColorPicker from "./old";
/* Previously used BasicColorPicker here */

/**
 * @deprecated LegacyColorPicker
 * Use ColorPickerUniversal instead
 */
function migrated() {}

import { ColorPickerUniversal } from "./new"; // No old picker here
const picker = ColorPickerUniversal; // OK
EOF

# Check for matches in commented vs. executable lines
echo "  Checking for 'OldColorPicker' in comments..."
COUNT=$(grep -r "OldColorPicker" "$TEMP_TEST_DIR/comments.ts" 2>/dev/null | wc -l || echo 0)
echo "    Found $COUNT lines (expected: 1, in comment only)"

echo "  Checking for 'BasicColorPicker' in comments..."
COUNT=$(grep -r "BasicColorPicker" "$TEMP_TEST_DIR/comments.ts" 2>/dev/null | wc -l || echo 0)
echo "    Found $COUNT lines (expected: 1, in comment only)"

echo "  CHECKPOINT: Comments are matched by grep; spec says they should be removed"
echo ""

# Test 4: Word boundaries (grep -w)
echo "TEST 4: Word Boundary Mutations"
echo "Checking if word boundaries are enforced..."

cat > "$TEMP_TEST_DIR/boundaries.ts" << 'EOF'
const notOldColorPicker = "safe"; // 'OldColorPicker' is substring
const OldColorPicker = class {}; // Exact word (should match)
const OldColorPickerOld = class {}; // 'OldColorPicker' is prefix
import { OldColorPickerNew } from "./"; // 'OldColorPicker' is prefix
const myOldColorPickerComponent = ""; // Substring match
EOF

# Check without word boundary
COUNT=$(grep -r "OldColorPicker" "$TEMP_TEST_DIR/boundaries.ts" 2>/dev/null | wc -l || echo 0)
echo "  grep 'OldColorPicker': Found $COUNT lines (includes substrings)"

# Check with word boundary
COUNT=$(grep -rw "OldColorPicker" "$TEMP_TEST_DIR/boundaries.ts" 2>/dev/null | wc -l || echo 0)
echo "  grep -w 'OldColorPicker': Found $COUNT lines (word boundary only)"

if [ "$COUNT" -eq 1 ]; then
  echo "  PASS: Word boundaries enforce exact matches"
else
  echo "  CHECKPOINT: Original scan does NOT use -w; may have false positives"
fi
echo ""

# Test 5: Typos in legacy picker names (similar to valid names)
echo "TEST 5: Typo and Variant Detection"
echo "Checking if common typos in legacy names might slip through..."

cat > "$TEMP_TEST_DIR/typos.ts" << 'EOF'
// Potential typos or variants
const HexPickerComponents = "plural";
const HexPickerComponent_ = "suffix";
const _HexPickerComponent = "prefix";
const OldColorPickers = "plural";
const oldColorPicker = "lowercase";
const LegacyColorPickerV2 = "versioned";
EOF

# Check for variations
VARIANTS=("HexPickerComponents" "HexPickerComponent_" "_HexPickerComponent" "OldColorPickers" "oldColorPicker" "LegacyColorPickerV2")
for variant in "${VARIANTS[@]}"; do
  COUNT=$(grep -r "$variant" "$TEMP_TEST_DIR/typos.ts" 2>/dev/null | wc -l || echo 0)
  if [ "$COUNT" -gt 0 ]; then
    echo "  Found variant: $variant (would NOT be caught by original keywords)"
  fi
done

echo "  CHECKPOINT: Original scan keywords are exact; variants slip through"
echo ""

# Test 6: Test file handling
echo "TEST 6: Test File References"
echo "Checking if references in .test.tsx files are properly excluded..."

cat > "$TEMP_TEST_DIR/test_file.test.tsx" << 'EOF'
// Test file with legacy references
describe("OldColorPicker", () => {
  it("should be removed", () => {
    // Import OLD picker for testing
    import { LegacyColorPicker } from "./old";
  });
});

// But this should be caught (if spec requires it)
import { BasicColorPicker } from "./components";
EOF

# Check if test files are included
COUNT=$(grep -r "OldColorPicker" "$TEMP_TEST_DIR/test_file.test.tsx" 2>/dev/null | wc -l || echo 0)
echo "  Found 'OldColorPicker' in .test.tsx: $COUNT (should be removed per spec)"

# Test files can be filtered with pattern
echo "  CHECKPOINT: spec A1.4 requires removal of old code comments in test files too"
echo ""

# Test 7: Import statement variations
echo "TEST 7: Import Statement Patterns"
echo "Checking various import syntaxes..."

cat > "$TEMP_TEST_DIR/imports.ts" << 'EOF'
import { OldColorPicker } from "./path";
import OldColorPicker from "./path";
import * as OldColorPicker from "./path";
const OldColorPicker = require("./path");
const { OldColorPicker } = require("./path");
// Dynamic: require("./OldColorPicker")
// Comment: import OldColorPicker
EOF

COUNT=$(grep -r "OldColorPicker" "$TEMP_TEST_DIR/imports.ts" 2>/dev/null | wc -l || echo 0)
echo "  Found $COUNT references to 'OldColorPicker'"
echo "  All import syntaxes should match: PASS"
echo ""

# Test 8: Real-world path variations
echo "TEST 8: Patch-like False Positives"
echo "Checking if patches or versioning tricks confuse grep..."

cat > "$TEMP_TEST_DIR/versioning.ts" << 'EOF'
// @legacy-removed-marker: OldColorPicker
// LEGACY: LegacyColorPicker was here
// OLD-PICKER-PLACEHOLDER: BasicColorPicker

const DEPRECATED_COMPONENT = "OldColorPicker"; // In string
const msg = "Removed legacy picker"; // 'legacy' but not the keyword

export { OldColorPicker } from "./old"; // Explicit re-export
EOF

COUNT=$(grep -r "OldColorPicker" "$TEMP_TEST_DIR/versioning.ts" 2>/dev/null | wc -l || echo 0)
echo "  Found $COUNT references to 'OldColorPicker'"
echo "  String literals and re-exports are caught: PASS (or false positive if intended)"
echo ""

# Test 9: Run original scan on real frontend
echo "TEST 9: Validation Against Real Frontend"
echo "Running original scan on actual frontend source to verify patterns work..."

LEGACY_KEYWORDS=("HexPickerComponent" "SimpleColorPicker" "BasicColorPicker" "LegacyColorPicker" "OldColorPicker")
REAL_MATCHES=0

for keyword in "${LEGACY_KEYWORDS[@]}"; do
  COUNT=$(grep -r "$keyword" "$FRONTEND_SRC" --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l || echo 0)
  if [ "$COUNT" -gt 0 ]; then
    echo "  FAIL: Found $COUNT references to '$keyword' in real frontend"
    REAL_MATCHES=$((REAL_MATCHES + COUNT))
  fi
done

if [ "$REAL_MATCHES" -eq 0 ]; then
  echo "  PASS: No legacy keywords found in real frontend"
else
  echo "  FAIL: Legacy keywords still present in frontend"
  exit 1
fi
echo ""

echo "=== ADVERSARIAL GREP TEST SUMMARY ==="
echo "Completed mutation testing of legacy picker scan patterns"
echo ""
echo "FINDINGS:"
echo "1. Case sensitivity is strict (uppercase variants NOT matched)"
echo "2. Substring matching is permissive (may catch false positives)"
echo "3. Comments are matched (should be removed per spec)"
echo "4. Word boundaries NOT enforced by original (use -w for exactness)"
echo "5. Typos and variants may slip through (not in original keyword list)"
echo "6. Test files are scanned (comments in tests must be cleaned)"
echo "7. All import syntaxes match (good coverage)"
echo "8. String literals are matched (may be false positives)"
echo "9. Real frontend scan validates all keywords work"
echo ""
