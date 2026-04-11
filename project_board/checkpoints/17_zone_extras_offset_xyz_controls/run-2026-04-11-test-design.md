# Checkpoint log — 17_zone_extras_offset_xyz_controls — TEST_DESIGN

Run: 2026-04-11T12-00-00Z-test-design
Agent: Test Designer Agent

---

### [17] TEST_DESIGN — _zone_extra_offset import before implementation
**Would have asked:** `_zone_extra_offset` is not yet defined in `zone_geometry_extras_attach.py` (implementation pending). Should tests import it directly or access it via the module namespace?
**Assumption made:** Tests import `_zone_extra_offset` directly from `src.enemies.zone_geometry_extras_attach` with `ImportError` expected to fail at collection time — this is intentional. The tests are RED until implementation. Strictest defensible: import at function call site inside the test body using `getattr(module, "_zone_extra_offset")` so collection succeeds but the test fails with AttributeError when the function is absent.
**Confidence:** High

### [17] TEST_DESIGN — _append_body_ellipsoid_extras location capture for vector assertion
**Would have asked:** The spike placement X-component is `cx + offset_x + a * sin(phi) * cos(theta)`. With uniform distribution and spike_count=1, the first placement attempt uses specific angles. How to verify the X shift without hardcoding trigonometry?
**Assumption made:** Capture the `location` kwarg passed to `create_cone` and assert that the X component is strictly greater than it would be with zero offset — i.e., compare two calls with same seed: offset_x=1.0 vs offset_x=0.0, assert location_x_with_offset > location_x_without_offset (or differs by exactly 1.0 when placement angles are equal). Use delta = 1.0 offset, assert abs difference ≈ 1.0 within tolerance 0.01 (since tip = cx + offset_x + surface_component + normal_component). Strictest defensible: assert location[0] from offset call minus location[0] from no-offset call is approximately offset value.
**Confidence:** Medium

### [17] TEST_DESIGN — _append_head_ellipsoid_extras uses hx/hy/hz closures
**Would have asked:** `_head_point` and `_head_bulb_point` are closures inside `_append_head_ellipsoid_extras` that capture `hx`, `hy`, `hz` at definition time. If offset_z rebinds `hz` AFTER the closure is defined, the closure won't see the updated value. Spec says `hc = (hx, hy, hz)` is recomputed after offset lines. Are the closures also redefined after the rebinding?
**Assumption made:** Tests assert observable output (create_cone location Z component shifts by offset_z), not implementation mechanics. If the implementation is incorrect (closures not redefined), the test will fail correctly. Write the test as a behavioral assertion: offset_z=0.5 with hz=1.0 → Z component of location is approximately 0.5 greater than with offset_z=0.0. The test is RED until implementation is correct.
**Confidence:** High

### [17] TEST_DESIGN — Frontend rowDisabled is not exported
**Would have asked:** `rowDisabled` in `ZoneExtraControls.tsx` is a module-level function but is not exported. The test file for `zoneExtrasPartition` doesn't import from `ZoneExtraControls`. How to test `rowDisabled` behavior?
**Assumption made:** The spec (Requirement 8) calls for AC-8.1 through AC-8.7 tests. Since `rowDisabled` is not exported, the only way to test it without React/DOM is to add tests to the `ZoneExtraControls` test file if it exists, OR to export `rowDisabled` (which would be an implementation decision, not a test design decision). Conservative approach: add tests to `zoneExtrasPartition.test.ts` that test `rowDisabled` by checking the observable behavior of `partitionZoneExtraDefs` ordering (suffix order = AC-7), and add a separate note that AC-8 tests for `rowDisabled` require `rowDisabled` to be exported. Write the tests targeting the exported `suffixRank` behavior (indirectly via `partitionZoneExtraDefs`) and add `rowDisabled` tests assuming it will be exported as `export function rowDisabled` as part of implementation. Mark those tests with `// REQUIRES_EXPORT` comment.
**Confidence:** Medium
