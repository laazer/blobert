# M25-MTE Checkpoint Log — Test Designer Agent

## [M25-MTE] TEST_DESIGN — Initial Discovery & Assumptions

**Would have asked:** 
1. What is the exact import path for Blender stubs in conftest.py? Does it register a fake `bpy` module, or do tests patch individual functions like `create_eye_mesh` directly?
2. For frontend tests, does the existing test setup use Vitest with jsdom environment already configured, or do I need to verify the test file will be discovered by the test runner?
3. Are there any existing constants for mouth/tail shape options in `animated_build_options.py` that I should reference (e.g., `_MOUTH_SHAPE_OPTIONS`), or should I assume they don't exist yet and write tests against hardcoded lists?

**Assumption made:** 
1. Tests will patch at the module level where the enemy builders import from (`src.enemies.animated_spider.create_mouth_mesh`, etc.), following the pattern in `test_eye_shape_pupil_geometry.py`. The conftest.py stubs are sufficient via function-level mocking.
2. Frontend test file follows the same Vitest setup as other frontend tests (jsdom environment, existing store mocks). Test runner will discover `*.mouthTail.test.tsx` files automatically.
3. Mouth/tail control helpers `_mouth_control_defs()` and `_tail_control_defs()` don't exist yet in implementation — I'll write tests that will be RED until Task 2 adds them, following the ESPS pattern where test file is written before implementation (MTE-1-AC-7).

**Confidence:** Medium

---

## [M25-MTE] TEST_DESIGN — Test File Structure Decisions

**Would have asked:** 
Should I include test coverage for all 6 animated slugs in the geometry tests, or focus on a representative subset (spider, slug) similar to ESPS which tested spider/slug/claw_crawler?

**Assumption made:** 
I'll follow the ESPS pattern and cover all 6 geometry-wired slugs (spider, slug, claw_crawler, imp, spitter, carapace_husk) in both mouth and tail tests. This matches MTE-7 which explicitly states ALL six animated enemies are geometry-wired.

**Confidence:** High

---

## [M25-MTE] TEST_DESIGN — Control Ordering Tests

**Would have asked:** 
The spec mandates a specific control ordering (mouth_enabled, mouth_shape, tail_enabled, tail_shape in non-float block; tail_length in float block). Should I write explicit index-order tests like `TestControlOrdering` in ESPS?

**Assumption made:** 
Yes — I'll include `TestControlOrdering` class testing that the four non-float controls appear before any float control, and that they appear after eye/pupil controls. This matches MTE-1-AC-8 and follows the ESPS pattern exactly.

**Confidence:** High

---

## [M25-MTE] TEST_DESIGN — Frontend Test Labels

**Would have asked:** 
The frontend tests use label text to find control rows (e.g., "Pupil shape"). The spec defines labels: "Mouth", "Mouth shape", "Tail", "Tail shape", "Tail length". Should I verify these exact labels exist in the test setup?

**Assumption made:** 
I'll use the exact labels from the spec:
- `mouth_enabled` → label: "Mouth"
- `mouth_shape` → label: "Mouth shape"  
- `tail_enabled` → label: "Tail"
- `tail_shape` → label: "Tail shape"
- `tail_length` → label: "Tail length"

These match MTE-1-AC-2 through MTE-1-AC-6 in the spec.

**Confidence:** High

---

## [M25-MTE] TEST_DESIGN — Tail Length Range Tests

**Would have asked:** 
Should I test tail_length clamping at exact boundaries (0.5, 3.0) and beyond (0.0, 5.0), or just representative values? The spec MTE-2-AC-10 through MTE-2-AC-14 explicitly lists boundary tests.

**Assumption made:** 
I'll include explicit boundary tests for tail_length:
- `tail_length: 0.0` → clamped to `0.5` (MTE-2-AC-10)
- `tail_length: 0.5` → stays `0.5` (MTE-2-AC-13, boundary min)
- `tail_length: 1.5` → stays `1.5` (valid value, MTE-2-AC-12)
- `tail_length: 3.0` → stays `3.0` (MTE-2-AC-14, boundary max)
- `tail_length: 5.0` → clamped to `3.0` (MTE-2-AC-11)

This covers all MTE-2-AC-10 through MTE-2-AC-14 acceptance criteria.

**Confidence:** High

---

## Index Update

**Added pointers to:**
- `/Users/jacobbrandt/workspace/blobert/project_board/checkpoints/M25-MTE/run-2026-04-15T02-00-00Z-test-design.md` (this file)

**Next action:** Write three test files:
1. `asset_generation/python/tests/utils/test_mouth_tail_controls.py` (Task 4)
2. `asset_generation/python/tests/enemies/test_mouth_tail_geometry.py` (Task 5)
3. `asset_generation/web/frontend/src/components/Preview/BuildControls.mouthTail.test.tsx` (Task 7)
