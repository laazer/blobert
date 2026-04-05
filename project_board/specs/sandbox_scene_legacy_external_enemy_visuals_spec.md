# Spec: sandbox_scene_legacy_external_enemy_visuals (MAINT-SLEEV)

**Ticket:** `project_board/maintenance/in_progress/sandbox_scene_legacy_external_enemy_visuals.md`  
**Spec Date:** 2026-04-05  
**Spec Agent Revision:** 1  

**Authoritative source scene:** `res://scenes/levels/sandbox/test_movement_3d.tscn`  
**New scene path (normative):** `res://scenes/levels/sandbox/test_movement_3d_legacy_enemy_visual.tscn`

**Traceability (ticket acceptance criteria):**

| Ticket AC | Spec coverage |
|-----------|----------------|
| New sandbox scene loads without errors; instantiates cleanly in headless/editor | SLEEV-1 |
| Enemy count, names, transforms, `mutation_drop`; `model_scene` unset; default packaged mesh | SLEEV-2, SLEEV-3 |
| No regression: `run/main_scene` and tests (optional smoke test allowed) | SLEEV-4, SLEEV-5 |

---

## Background and Context

- **Purpose:** Devlog capture using the **legacy third-party** visual (`res://assets/Models/gobot/model/gobot.glb`) shipped as default `EnemyVisual` in `res://scenes/enemy/enemy_infection_3d.tscn`, without reverting git history.
- **Behavior contract:** `EnemyInfection3D` (`res://scripts/enemy/enemy_infection_3d.gd`) swaps `EnemyVisual` only when `@export var model_scene` is non-null; when null, deferred `_wire_and_notify_animation()` runs against the scene-packaged `EnemyVisual` (gobot).
- **Source level structure (baseline for duplication):** Root `TestMovement3D` (`Node3D`); children in order: `SceneVariantController`, `InfectionInteractionHandler`, `WorldEnvironment`, `DirectionalLight3D`, `Floor` (with `CollisionShape3D`, `MeshInstance3D`), `SpawnPosition`, four instanced enemies (`AdhesionBugEnemy`, `AcidSpitterEnemy`, `ClawCrawlerEnemy`, `CarapaceHuskEnemy` from `enemy_infection_3d.tscn`), `InfectionUI`, `RespawnZone` (with `CollisionShape3D`), `Player3D`; signal connection `RespawnZone.body_entered` → `_on_body_entered` on same node.
- **Per-enemy baseline (source):** Each enemy uses `physics_interpolation_mode = 1`, the transforms and `mutation_drop` values below, and **overrides** `model_scene` to a generated GLB:

| Node name | `transform` (translation) | `mutation_drop` | Source `model_scene` resource |
|-----------|---------------------------|-----------------|--------------------------------|
| `AdhesionBugEnemy` | `(4, 1, 0)` | `"adhesion"` | `res://assets/enemies/generated_glb/adhesion_bug_animated_00.glb` |
| `AcidSpitterEnemy` | `(-4, 1, 0)` | `"acid"` | `res://assets/enemies/generated_glb/acid_spitter_animated_00.glb` |
| `ClawCrawlerEnemy` | `(8, 1, 0)` | `"claw"` | `res://assets/enemies/generated_glb/claw_crawler_animated_00.glb` |
| `CarapaceHuskEnemy` | `(-8, 1, 0)` | `"carapace"` | `res://assets/enemies/generated_glb/carapace_husk_animated_00.glb` |

---

## Requirement SLEEV-1: New scene asset path and loadability

### 1. Spec Summary

**Description:** Add exactly **one** new Godot scene file at **`res://scenes/levels/sandbox/test_movement_3d_legacy_enemy_visual.tscn`**. The scene must be a **duplicate** of `test_movement_3d.tscn` subject to SLEEV-2–SLEEV-3 deltas only. Opening or packed-loading the scene in the project’s supported Godot version must **not** emit load errors (editor or headless instantiate path used elsewhere in tests).

**Constraints:** Do not replace or rename `test_movement_3d.tscn`. Do not register the new scene as the project main scene (see SLEEV-4).

**Assumptions:** Godot may rewrite `unique_id` values and `uid=` on save; those differences alone are not a spec violation if gameplay tree and properties match SLEEV-2–SLEEV-3.

**Scope:** New `.tscn` under `scenes/levels/sandbox/` only for this requirement; script changes are out of scope unless a separate ticket says otherwise.

### 2. Acceptance Criteria

- **SLEEV-1.1:** File exists at `res://scenes/levels/sandbox/test_movement_3d_legacy_enemy_visual.tscn`.
- **SLEEV-1.2:** Packed scene load (e.g. `load(path).instantiate()` or equivalent project pattern) completes without error and produces a single root `Node3D`.
- **SLEEV-1.3 (optional per ticket AC):** If tests are added, a **single** minimal smoke test that only asserts successful load/instantiate of this path is sufficient; **zero** new tests is also acceptable if gate documents “N/A” with rationale.

### 3. Risk & Ambiguity Analysis

- **Risk:** Stale `unique_id` collisions when copying `.tscn` text — mitigated by opening/saving in Godot or following project’s scene-edit workflow.
- **Edge case:** UID conflicts — new file should receive a distinct scene `uid` on first save.

### 4. Clarifying Questions

- None.

---

## Requirement SLEEV-2: Root identity and structural parity with source sandbox

### 1. Spec Summary

**Description:** The new scene’s **root node name** MUST differ from `TestMovement3D` for clarity (e.g. `TestMovement3DLegacyEnemyVisual`). All other top-level node **names**, **types**, **parent relationships**, and **ordering** MUST match `test_movement_3d.tscn` except for deltas explicitly listed in SLEEV-3.

**Constraints:** Preserve `SceneVariantController` script reference, `InfectionInteractionHandler`, environment/light/floor/spawn/UI/player/respawn subtree structure, and the `RespawnZone` signal connection as in the source file.

**Assumptions:** Non-enemy `ext_resource` and `sub_resource` blocks match the source unless removal of GLB `ext_resource` lines forces ID renumbering (content equivalence: same referenced paths and sub-resource definitions for everything except the four removed GLB packed scenes).

**Scope:** Full scene tree for the new file.

### 2. Acceptance Criteria

- **SLEEV-2.1:** Root node name ≠ `TestMovement3D`.
- **SLEEV-2.2:** Child node names under root match the source list: `SceneVariantController`, `InfectionInteractionHandler`, `WorldEnvironment`, `DirectionalLight3D`, `Floor`, `SpawnPosition`, `AdhesionBugEnemy`, `AcidSpitterEnemy`, `ClawCrawlerEnemy`, `CarapaceHuskEnemy`, `InfectionUI`, `RespawnZone`, `Player3D`.
- **SLEEV-2.3:** `Floor`, `RespawnZone`, and `Player3D` subtree structure and non-enemy properties match source (including `collision_mask` on `Floor`, floor mesh/material, respawn `spawn_point` path, light transform, environment subresource).

### 3. Risk & Ambiguity Analysis

- **Edge case:** Editor normalization of `Transform3D` formatting — compare logical transform, not whitespace.

### 4. Clarifying Questions

- None.

---

## Requirement SLEEV-3: Enemy instance parity — remove `model_scene` and generated GLB resources

### 1. Spec Summary

**Description:**

1. **Remove** from the new scene **all** `[ext_resource]` lines that reference these four paths (matching source sandbox):
   - `res://assets/enemies/generated_glb/adhesion_bug_animated_00.glb`
   - `res://assets/enemies/generated_glb/acid_spitter_animated_00.glb`
   - `res://assets/enemies/generated_glb/claw_crawler_animated_00.glb`
   - `res://assets/enemies/generated_glb/carapace_husk_animated_00.glb`

2. For each of the four enemy instances, **remove** the **`model_scene`** property override entirely so the instance does **not** assign `model_scene` (inherits default `null` from `enemy_infection_3d.gd` / unset instance override).

3. Preserve for each enemy: `physics_interpolation_mode = 1`, **`transform`** exactly as in the source table in Background, and **`mutation_drop`** string exactly as in the source table.

**Constraints:** Do not add alternate `model_scene` paths. Do not change `mutation_drop` values. Do not change enemy node names or sibling order.

**Assumptions:** Runtime visuals for enemies are the packaged gobot mesh from `enemy_infection_3d.tscn` when `model_scene` is unset; no spec requirement to assert mesh path string inside `.tscn` of the **level** file (that path lives on the enemy scene).

**Scope:** Enemy instances and scene-level `ext_resource` list for the new `.tscn` only.

### 2. Acceptance Criteria

- **SLEEV-3.1:** New scene contains **no** `ext_resource` whose `path=` is any of the four `generated_glb/*_animated_00.glb` files listed above.
- **SLEEV-3.2:** Each of `AdhesionBugEnemy`, `AcidSpitterEnemy`, `ClawCrawlerEnemy`, `CarapaceHuskEnemy` has **no** `model_scene =` line in the `.tscn` instance body.
- **SLEEV-3.3:** Each enemy retains `mutation_drop` values `"adhesion"`, `"acid"`, `"claw"`, `"carapace"` respectively and transforms `(4,1,0)`, `(-4,1,0)`, `(8,1,0)`, `(-8,1,0)` translations per source.
- **SLEEV-3.4:** At runtime, after `_ready` on each `EnemyInfection3D`, behavior matches “no swap” path: `model_scene` is null (inspector-equivalent: unset override).

### 3. Risk & Ambiguity Analysis

- **Risk:** Gobot visual may lack GLB animation libraries; `EnemyAnimationController` may behave differently than with generated meshes — **in scope** only as far as “scene loads and matches structural contract”; animation parity with GLB enemies is **not** required by this ticket.
- **Edge case:** Instance overrides in `.tscn` that explicitly set `model_scene` to empty — avoid; omission of property is the normative approach.

### 4. Clarifying Questions

- None.

---

## Requirement SLEEV-4: `project.godot` main scene unchanged (non-regression)

### 1. Spec Summary

**Description:** This work **must not** change `project.godot` `[application]` `run/main_scene` to `test_movement_3d_legacy_enemy_visual.tscn` or otherwise repoint the main scene as a consequence of adding the legacy sandbox.

**Ticket AC text** states `run/main_scene` must **still target** `res://scenes/levels/sandbox/test_movement_3d.tscn`. Implementation and gatekeeper SHALL verify that after the change set, `run/main_scene` equals **`res://scenes/levels/sandbox/test_movement_3d.tscn`**. If the repository baseline differs at merge time, **escalate to Planner** before closing the ticket (repository/ticket mismatch).

**Constraints:** No drive-by edits to other `project.godot` sections for this ticket.

**Assumptions:** None beyond ticket authority for the expected `main_scene` string.

**Scope:** `project.godot` `[application]` `run/main_scene` only.

### 2. Acceptance Criteria

- **SLEEV-4.1:** `run/main_scene` is not set to `res://scenes/levels/sandbox/test_movement_3d_legacy_enemy_visual.tscn`.
- **SLEEV-4.2:** `run/main_scene` == `res://scenes/levels/sandbox/test_movement_3d.tscn` **or** ticket is BLOCKED with documented Planner resolution if repo policy requires a different value.

### 3. Risk & Ambiguity Analysis

- **Risk:** Observed drift between ticket AC and current `project.godot` in some branches — SLEEV-4.2 explicitly allows BLOCKED + Planner note rather than silent wrong closure.

### 4. Clarifying Questions

- None (resolved by “match ticket AC or escalate”).

---

## Requirement SLEEV-5: Test suite and existing scene references

### 1. Spec Summary

**Description:** Full automated suite (`timeout 300 godot -s tests/run_tests.gd` or project-standard `ci/scripts/run_tests.sh`) MUST pass after implementation. Existing tests MUST continue to target `test_movement_3d.tscn` (or whatever paths they used pre-change) unless a **new** test is added **only** for optional SLEEV-1.3 smoke coverage; no existing test should be repointed to the legacy scene as the **primary** sandbox under test without a separate ticket.

**Constraints:** Do not change `run/main_scene` (see SLEEV-4). Do not bulk-replace project references from `test_movement_3d` to the legacy scene.

**Assumptions:** CI Godot version matches local.

**Scope:** `tests/**` and any CI entrypoints touched only as needed for optional smoke or unavoidable fixes.

### 2. Acceptance Criteria

- **SLEEV-5.1:** `run_tests` (project standard) exits 0 post-change.
- **SLEEV-5.2:** No required test file is updated to **require** the legacy scene as the default movement sandbox unless explicitly adding optional smoke per SLEEV-1.3.

### 3. Risk & Ambiguity Analysis

- **Edge case:** Global string search replacing scene paths — avoid; scope changes tightly.

### 4. Clarifying Questions

- None.

---

## Summary checklist (implementation / gatekeeper)

| ID | Verifiable outcome |
|----|--------------------|
| SLEEV-1 | New path exists; load/instantiate OK |
| SLEEV-2 | Root renamed; tree matches source minus SLEEV-3 |
| SLEEV-3 | No four GLB `ext_resource` lines; no `model_scene` on four enemies; transforms + `mutation_drop` preserved |
| SLEEV-4 | `run/main_scene` per ticket or BLOCKED |
| SLEEV-5 | Full test suite green; no unintended test repointing |
