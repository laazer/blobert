Title:
Per-Part Rotation Controls

Description:
Add X/Y/Z rotation inputs to the part properties panel so users can orient individual body parts (head, torso, limbs). Currently parts can be positioned but not rotated, which forces unnatural default poses and limits design variation. This ticket adds cosmetic rotation of the primitive shape — it is not joint rotation or skeletal posing.

Acceptance Criteria:
- Each selectable part exposes X, Y, Z rotation inputs in the properties panel
- Inputs accept numeric values in degrees; valid range is -180 to 180
- Values outside the valid range are clamped or rejected with inline feedback
- A "Reset Rotation" button restores the part to 0/0/0
- Rotation changes reflect immediately in the 3D preview
- Rotation values serialize correctly to enemy config JSON alongside position and scale

Scope Notes:
- Numeric inputs only — no 3D viewport rotation gizmo
- This is cosmetic orientation of the shape primitive, not joint/skeletal rotation
- No rotation constraints or limits tied to part type
- Does not affect collision or gameplay hitbox geometry

## Web Editor Implementation

**Python (`asset_generation/python/src/utils/animated_build_options.py`)**
- Add per-part rotation float controls using the existing `RIG_` prefix convention so they appear in the Rig float table: `RIG_HEAD_ROT_X`, `RIG_HEAD_ROT_Y`, `RIG_HEAD_ROT_Z`, `RIG_BODY_ROT_X`, `RIG_BODY_ROT_Y`, `RIG_BODY_ROT_Z` (degrees; min -180, max 180, default 0, step 1)
- Add to all animated slugs that expose explicit head/body parts; document which slugs are excluded (e.g. slug has no distinct head part)
- `options_for_enemy()` must clamp values to [-180, 180] during coercion

**Frontend (`asset_generation/web/frontend/src/`)**
- No `BuildControls.tsx` changes required; `RIG_` float controls automatically appear in the existing "Rig" float table section with filter support
- Verify that `RIG_HEAD_ROT_X` etc. appear under the Rig section header (the `d.key.startsWith("RIG_")` filter in `BuildControls.tsx:353`) — no code change needed if the naming convention is followed
- A "Reset Rotation" button is out of scope for the Rig table (individual cell reset is not part of the existing float table pattern); the existing per-key default coercion on re-generate serves as reset

**Tests**
- Python: `test_part_rotation_controls.py` — all target slugs expose `RIG_HEAD_ROT_X/Y/Z` and `RIG_BODY_ROT_X/Y/Z`; value 200 is clamped to 180; value -200 is clamped to -180; defaults are 0
- Frontend (Vitest): confirm `RIG_HEAD_ROT_X` appears in the Rig section filter (covered by existing `BuildControls.meta_load.test.tsx` pattern — extend that test file rather than creating a new one)

## Execution Plan

### Task 1 — Define `_rig_rotation_control_defs()` in `animated_build_options.py`
**Agent:** Spec Agent (for specification) → Generalist Implementation Agent (for code)
**File:** `asset_generation/python/src/utils/animated_build_options.py`
**Input:** This plan; existing `_tail_control_defs()` as the structural template.
**Output:** New module-level function `_rig_rotation_control_defs() -> list[dict[str, Any]]` returning 6 defs: `RIG_HEAD_ROT_X`, `RIG_HEAD_ROT_Y`, `RIG_HEAD_ROT_Z`, `RIG_BODY_ROT_X`, `RIG_BODY_ROT_Y`, `RIG_BODY_ROT_Z`. Each def: `type="float"`, `min=-180.0`, `max=180.0`, `step=1.0`, `default=0.0`, with label and unit strings. Constants `_RIG_ROT_MIN = -180.0`, `_RIG_ROT_MAX = 180.0`, `_RIG_ROT_STEP = 1.0` defined at module level.
**Dependencies:** None.
**Success Criteria:** `_rig_rotation_control_defs()` returns a list of exactly 6 dicts; each dict has the correct keys/types/bounds; the function can be called independently without Blender stubs.

### Task 2 — Wire rotation defs into `animated_build_controls_for_api()`, `_defaults_for_slug()`, and `options_for_enemy()`
**Agent:** Generalist Implementation Agent
**File:** `asset_generation/python/src/utils/animated_build_options.py`
**Input:** Task 1 output; existing wiring pattern for `_tail_control_defs()` as reference.
**Output:**
- `animated_build_controls_for_api()`: `_rig_rotation_control_defs()` inserted in `merged` list after `static_float` and before `_mesh_float_control_defs(slug)` — so rotation controls appear at the top of the Rig section alongside other non-mesh floats. Insertion is conditional: only for `slug in AnimatedEnemyBuilder.ENEMY_CLASSES` (excludes `player_slime`).
- `_defaults_for_slug()`: loop over `_rig_rotation_control_defs()` and set each key to its default (0.0).
- `options_for_enemy()`: add all 6 keys to `allowed_non_mesh` set.
**Dependencies:** Task 1.
**Success Criteria:** `options_for_enemy("imp", {})` returns a dict containing `RIG_HEAD_ROT_X=0.0`; `options_for_enemy("imp", {"RIG_HEAD_ROT_X": 45.0})` returns `RIG_HEAD_ROT_X=45.0`.

### Task 3 — Wire rotation defs into `coerce_validate_enemy_build_options()`
**Agent:** Generalist Implementation Agent
**File:** `asset_generation/python/src/utils/animated_build_options_validate.py`
**Input:** Task 1 output; existing `static_defs.extend(m._tail_control_defs())` pattern.
**Output:** `static_defs.extend(m._rig_rotation_control_defs())` call added inside `coerce_validate_enemy_build_options()`.
**Dependencies:** Task 1.
**Success Criteria:** `options_for_enemy("imp", {"RIG_HEAD_ROT_X": 200.0})` returns `RIG_HEAD_ROT_X=180.0`; `options_for_enemy("imp", {"RIG_BODY_ROT_Z": -200.0})` returns `RIG_BODY_ROT_Z=-180.0`.

### Task 4 — Apply rotation to head and body mesh objects in each animated enemy's `build_mesh_parts()`
**Agent:** Generalist Implementation Agent
**Files:**
- `asset_generation/python/src/enemies/animated_slug.py`
- `asset_generation/python/src/enemies/animated_imp.py`
- `asset_generation/python/src/enemies/animated_spider.py`
- `asset_generation/python/src/enemies/animated_claw_crawler.py`
- `asset_generation/python/src/enemies/animated_spitter.py`
- `asset_generation/python/src/enemies/animated_carapace_husk.py`
**Input:** Tasks 1–3; Blender `mathutils.Euler` and `math.radians`; the mesh object returned by `create_sphere()` / `create_cylinder()` (already assigned to `self.parts`).
**Output:** After each head mesh and body mesh is created and appended to `self.parts`, read `RIG_HEAD_ROT_X/Y/Z` (or `RIG_BODY_ROT_X/Y/Z`) from `self.build_options` with default 0.0, convert to radians, and assign `obj.rotation_euler = mathutils.Euler((rx, ry, rz), 'XYZ')`. Pattern per slug:
```python
import math
from mathutils import Euler
rx = math.radians(float(self.build_options.get("RIG_BODY_ROT_X", 0.0)))
ry = math.radians(float(self.build_options.get("RIG_BODY_ROT_Y", 0.0)))
rz = math.radians(float(self.build_options.get("RIG_BODY_ROT_Z", 0.0)))
body.rotation_euler = Euler((rx, ry, rz), 'XYZ')
```
Repeat for head object using `RIG_HEAD_ROT_X/Y/Z`.
**Dependencies:** Tasks 1–3.
**Success Criteria:** When `build_options` contains `RIG_BODY_ROT_Z=90`, the body mesh object's `rotation_euler[2]` equals `math.pi / 2`. No crash when all rotation values are 0.0 (default no-op).

### Task 5 — Write Python test suite `test_part_rotation_controls.py`
**Agent:** Test Designer Agent (design) → Test Breaker Agent (adversarial hardening)
**File:** `asset_generation/python/tests/utils/test_part_rotation_controls.py`
**Input:** Tasks 1–4 spec; existing test file `test_animated_build_options_offset_xyz.py` as structural reference.
**Output:** Test file covering:
- All 6 control keys exist in `animated_build_controls_for_api()` for every animated slug
- Each control def has `type="float"`, `min=-180.0`, `max=180.0`, `step=1.0`, `default=0.0`
- `options_for_enemy(slug, {"RIG_HEAD_ROT_X": 200})` returns 180.0 (clamp upper)
- `options_for_enemy(slug, {"RIG_BODY_ROT_Z": -200})` returns -180.0 (clamp lower)
- `options_for_enemy(slug, {})` returns all 6 keys with default 0.0
- `options_for_enemy(slug, {"RIG_HEAD_ROT_Y": 0.0})` returns 0.0 (identity, no NaN/inf)
- Boundary: value 180.0 passes through unchanged; -180.0 passes through unchanged
- `player_slime` excluded: `animated_build_controls_for_api()["player_slime"]` does not contain `RIG_HEAD_ROT_X` (player_slime not in `AnimatedEnemyBuilder.ENEMY_CLASSES`; verify it is either absent or explicitly excluded)
- Constants `_RIG_ROT_MIN`, `_RIG_ROT_MAX`, `_RIG_ROT_STEP` exist and have correct types and values
**Dependencies:** Tasks 1–3 (tests are RED until implemented).
**Success Criteria:** All tests pass after Tasks 1–4 are implemented; `bash .lefthook/scripts/py-tests.sh` exits 0.

### Task 6 — Verify frontend Rig section renders `RIG_HEAD_ROT_X` (no code change expected)
**Agent:** Generalist Implementation Agent (verification only)
**File:** `asset_generation/web/frontend/src/components/Preview/BuildControls.meta_load.test.tsx` (extend if needed)
**Input:** Task 2 output; existing `BuildControls.tsx` Rig section filter `d.key.startsWith("RIG_")`.
**Output:** A test assertion (in the existing meta_load test file or a targeted new describe block within it) that a mock API response containing `RIG_HEAD_ROT_X` as a float control results in the control appearing under the "Rig" section in the rendered `BuildControls` component. If the existing filter already covers this by convention, document that no new test case is needed and add a code comment in the test file referencing this ticket.
**Dependencies:** Task 2.
**Success Criteria:** `npm test` passes; the Rig section assertion exists or is explicitly noted as covered by existing tests.

### Task 7 — AC Gate: run full Python test suite + diff-cover preflight
**Agent:** Generalist Implementation Agent (or Orchestrator)
**Commands:**
```bash
bash .lefthook/scripts/py-tests.sh
bash ci/scripts/diff_cover_preflight.sh
```
**Input:** All tasks complete.
**Output:** Both commands exit 0. If diff-cover threshold is not met, route back to implementation agent to add test coverage.
**Dependencies:** Tasks 1–6.
**Success Criteria:** `py-tests.sh` exits 0; `diff_cover_preflight.sh` exits 0.

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | IMPLEMENTATION_PYTHON_COMPLETE |
| Revision | 6 |
| Last Updated By | Generalist Implementation Agent |
| Next Responsible Agent | Acceptance Criteria Gatekeeper Agent |
| Status | Proceed |
| Validation Status | All 1906 Python tests pass (including all 80+ in test_part_rotation_controls.py). Diff-cover 99% (threshold 85%). 533 frontend tests pass. Checkpoint logged at `project_board/checkpoints/M25-04/run-2026-04-18T11-52-04Z-impl.md` for `RIG_HEAD_SCALE` TB-test assumption (TB-test assumed a pre-existing key that didn't exist; resolved by adding `RIG_HEAD_SCALE` to `_ANIMATED_BUILD_CONTROLS["imp"]` as a legitimate rig-level float). |
| Blocking Issues | — |

## NEXT ACTION

Acceptance Criteria Gatekeeper Agent: verify all AC from the ticket description are met by the implementation. Python test suite at `asset_generation/python/tests/utils/test_part_rotation_controls.py` is green. Frontend Rig section filter `d.key.startsWith("RIG_")` in `BuildControls.tsx:353` already covers the new rotation keys by naming convention (no code change needed). If all AC pass, advance Stage to COMPLETE and move ticket to `done/`.
