# M25-PTP TEST_DESIGN run — 2026-04-16T14-00-00Z

## Summary

Test Designer Agent. Authored two test files:
- `asset_generation/python/tests/utils/test_texture_controls.py` (PTP-6)
- `asset_generation/web/frontend/src/components/Preview/BuildControls.texture.test.tsx` (PTP-7)

All tests will be RED until implementation Tasks 1-4 complete.

---

### [M25-PTP] TEST_DESIGN — import path for `_texture_control_defs`
**Would have asked:** Should tests import `_texture_control_defs` from `animated_build_options_appendage_defs` directly or via `animated_build_options`?
**Assumption made:** Import via `src.utils.animated_build_options` using `hasattr`/getattr, consistent with how `test_mouth_tail_controls.py` imports `_mouth_control_defs` and `_tail_control_defs` from `src.utils.animated_build_options` (the re-export location). Also import directly from appendage_defs for the helper-function-level tests.
**Confidence:** High

### [M25-PTP] TEST_DESIGN — frontend: direct function call vs DOM rendering
**Would have asked:** Should the frontend tests call `buildControlDisabled` directly (unit) or render `BuildControls` and inspect the DOM (integration)?
**Assumption made:** `buildControlDisabled` is not exported from `BuildControls.tsx`. Tests render `BuildControls` and inspect DOM, matching the pattern in `BuildControls.mouthTail.test.tsx`. No unit tests against the unexported function.
**Confidence:** High

### [M25-PTP] TEST_DESIGN — ordering test: zone_extra keys
**Would have asked:** Should the ordering test scan for the actual extra_zone_* key pattern or use a known sentinel key?
**Assumption made:** The ordering test verifies that `placement_seed` appears after all 10 texture keys. It does not assert relative position to zone_extra keys (which may be slug-dependent). This is sufficient for PTP-6-AC-14 and PTP-8-AC-4.
**Confidence:** High
