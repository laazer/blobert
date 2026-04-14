# M25-ESPS Test Design Run — 2026-04-14T20-00-00Z

### [M25-ESPS] TEST_DESIGN — geometry test: what baseline part count to assert against

**Would have asked:** The spider `build_mesh_parts` baseline part count depends on `eye_count` and leg segment counts. The spec says "pupil_enabled=True increases part count by N_eyes vs baseline". Should tests pin a specific eye_count to make the delta deterministic, or compute baseline dynamically?
**Assumption made:** Tests use a fixed eye_count (e.g., 2) so that baseline and delta are fully deterministic. The assertion checks that `len(parts_with_pupils) == len(parts_without_pupils) + eye_count`, not an absolute count. This is strictly defensible from ESPS-4-AC-7.
**Confidence:** High

### [M25-ESPS] TEST_DESIGN — geometry test: `create_eye_mesh` is not yet implemented

**Would have asked:** `create_eye_mesh` and `create_pupil_mesh` in `blender_utils.py` do not yet exist (implementation is in future tasks). Tests that call `build_mesh_parts` will fail at import/call time because the builder will still reference `create_sphere`. Should the geometry tests be written against the post-implementation API?
**Assumption made:** Yes. Tests are written against the spec-mandated final state: `build_mesh_parts` uses `create_eye_mesh` (from `blender_utils`), patched via `unittest.mock.patch`. The tests will break (red) until the implementation is in place — this is the intended TEST_BREAK behavior.
**Confidence:** High

### [M25-ESPS] TEST_DESIGN — geometry test: slug stalk eye loop uses `for side in [-1, 1]` giving N_eyes=2 always

**Would have asked:** AnimatedSlug always has exactly 2 eyes (one per side). Is this safe to hard-code in tests?
**Assumption made:** Yes; spec ESPS-4-AC-7 confirms "slug always gains 2". Tests assert delta == 2.
**Confidence:** High

### [M25-ESPS] TEST_DESIGN — geometry test: claw_crawler peripheral_eyes=1 for minimal test case

**Would have asked:** ClawCrawler's peripheral_eyes count is configurable (0..3). The test should set it to 1 so delta is exactly 1 when pupil_enabled=True.
**Assumption made:** Tests instantiate with `peripheral_eyes=1` so the pupil delta is 1. A separate subtest confirms delta == N for N=2.
**Confidence:** High

### [M25-ESPS] TEST_DESIGN — frontend test: `buildControlDisabled` is not yet exported

**Would have asked:** `buildControlDisabled` in `BuildControls.tsx` is currently a module-internal function (not exported). Tests would need to either render the full component and inspect DOM opacity, or the function needs to be exported for unit testing.
**Assumption made:** Write tests that render the component with specific store state and inspect the `style.opacity` and `pointerEvents` of the rendered `pupil_shape` control row. This tests observable behavior (DOM opacity) rather than internals. An alternative approach is to also test that `buildControlDisabled` is exported — but the strictest defensible test is behavioral DOM inspection.
**Confidence:** Medium — if implementation exports `buildControlDisabled`, a direct unit test is also valid. DOM test is always valid per spec ESPS-8.

### [M25-ESPS] TEST_DESIGN — controls-only slug test: which slugs exactly

**Would have asked:** ESPS-7 mentions imp, spitter, carapace_husk as controls-only. player_slime is mentioned in ESPS-1 as also receiving controls. Tests should cover all four.
**Assumption made:** All four (imp, spitter, carapace_husk, player_slime) are tested for control declaration and correct options_for_enemy return.
**Confidence:** High
