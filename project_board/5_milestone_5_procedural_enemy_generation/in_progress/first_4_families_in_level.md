Title:
Place first 4 enemy families in prototype level
---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | IMPLEMENTATION_ENGINE_INTEGRATION_COMPLETE |
| Revision | 8 |
| Last Updated By | Engine Integration Agent (GDScript review pass) |
| Next Responsible Agent | Acceptance Criteria Gatekeeper Agent |
| Validation Status | Not started |
| Blocking Issues | None |

---


Description:
Place at least one variant from each of the first 4 families (adhesion, acid, claw, carapace)
in the prototype level. Verify mutation drops, collision, weakening, and infection all work
end-to-end with the generated scenes.

Acceptance Criteria:
- One variant each of adhesion_bug, acid_spitter, claw_crawler, carapace_husk placed in level
- Each enemy can be weakened and infected via existing infection loop
- Correct mutation is granted on absorption
- No visual or collision regressions
- Playable without debug tools

---

# EXECUTION PLAN

## Project: Place First 4 Enemy Families in Level
**Description:** Generate .tscn scenes from the 12 existing GLBs headlessly, create placement wrapper scenes for each family, place one per family in the prototype level, and verify the end-to-end infection loop with headless tests.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Write spec for headless scene generator and placement wrapper design | Spec Agent | `scripts/asset_generation/load_assets.gd`, `scripts/enemies/enemy_base.gd`, `scenes/enemy/enemy_infection_3d.tscn`, checkpoint decisions at `project_board/checkpoints/first_4_families_in_level/run-2026-03-30-01.md` | `project_board/specs/first_4_families_in_level_spec.md` defining: (a) headless generator script contract (`generate_enemy_scenes.gd`), (b) generated .tscn node structure, (c) placement wrapper scene contract, (d) level modification spec, (e) test contract | None | Spec file exists; covers all 5 sub-contracts; no ambiguous inputs remain for implementation | AABB may be zero in headless if MeshInstance3D not in scene tree — spec must define fallback shape; spec must confirm whether wrapper scenes are needed or generated scenes can be used directly |
| 2 | Implement `scripts/asset_generation/generate_enemy_scenes.gd` (headless tool) | Generalist Agent | `project_board/specs/first_4_families_in_level_spec.md` (Task 1 output), `scripts/asset_generation/load_assets.gd` (reference), `scripts/asset_generation/enemy_name_utils.gd`, 12 GLBs at `assets/enemies/generated_glb/` | New file `scripts/asset_generation/generate_enemy_scenes.gd` — `extends SceneTree`, `func _init()` entry point; runnable via `timeout 300 godot -s scripts/asset_generation/generate_enemy_scenes.gd`; writes 12 .tscn files to `scenes/enemies/generated/` | Task 1 | Script exits with code 0; `scenes/enemies/generated/` contains exactly 12 .tscn files named after each GLB basename; each .tscn has root CharacterBody3D with EnemyBase script, CollisionShape3D, Visual/Model subtree, Hurtbox Area3D, Marker3D nodes | AABB via `mesh.get_aabb()` without global transform — spec must determine whether to use local_aabb directly (no global_transform multiplication) since nodes are not in scene tree; ResourceSaver.save() to res:// paths requires project to be open — verify this works in headless mode |
| 3 | Run headless generator and commit the 12 generated .tscn files | Generalist Agent | `scripts/asset_generation/generate_enemy_scenes.gd` (Task 2 output) | 12 .tscn files committed to `scenes/enemies/generated/`; verified parseable by Godot | Task 2 | `run_tests.sh` passes with no new failures; all 12 files loadable via `load("res://scenes/enemies/generated/<name>.tscn")` in a test | If ResourceSaver fails headlessly, fallback: write a minimal .tscn serializer as a GDScript string builder — spec (Task 1) must include this as a fallback path |
| 4 | Create placement wrapper scenes for 4 families | Generalist Agent | `project_board/specs/first_4_families_in_level_spec.md`, 4 generated .tscn files (one per family: `adhesion_bug_animated_00.tscn`, `acid_spitter_animated_00.tscn`, `claw_crawler_animated_00.tscn`, `carapace_husk_animated_00.tscn`), `scenes/enemy/enemy_infection_3d.tscn` (reference for infection node structure) | 4 .tscn files in `scenes/enemies/placed/`: `enemy_adhesion_bug.tscn`, `enemy_acid_spitter.tscn`, `enemy_claw_crawler.tscn`, `enemy_carapace_husk.tscn` — each wraps the generated scene + adds EnemyInfection3D child, InteractionArea, correct collision layers | Task 3 | Each wrapper .tscn instantiates without error; has EnemyBase properties set; has CollisionShape3D; has Area3D named InteractionArea | Collision layer values must match existing enemy_infection_3d.tscn (layer 2, mask 1) — spec must confirm; if generated scenes already embed a viable infection node, wrapper may be unnecessary — spec resolves this |
| 5 | Modify level scene to place 4 family enemies | Generalist Agent | `scenes/levels/sandbox/test_movement_3d.tscn`, 4 wrapper .tscn files from Task 4, `project_board/specs/first_4_families_in_level_spec.md` | Updated `scenes/levels/sandbox/test_movement_3d.tscn` with 4 enemy instances (one per family) placed at spread positions on the floor; existing generic Enemy/Enemy2 nodes replaced or supplemented per spec | Task 4 | Level scene loads without error; `run_tests.sh` passes; 4 enemy nodes present under scene root at named paths; no regressions in existing test_3d_scene.gd tests | Existing Enemy/Enemy2 nodes reference `scenes/enemy/enemy_infection_3d.tscn` — removing them may break existing tests; spec must decide: replace or supplement; preserve existing test coverage |
| 6 | Write headless tests for generated scenes and level placement | Generalist Agent | `project_board/specs/first_4_families_in_level_spec.md`, `tests/scenes/levels/test_3d_scene.gd` (style reference), `tests/utils/test_utils.gd` | Two new test files: `tests/scenes/enemies/test_enemy_scene_generation.gd` (primary) and `tests/scenes/enemies/test_enemy_scene_generation_adversarial.gd`; registered in `tests/run_tests.gd` | Task 5 | All tests pass under `run_tests.sh`; tests cover: all 4 generated .tscn files load; each has correct enemy_id, enemy_family, mutation_drop; each has CollisionShape3D; level scene has 4 enemy nodes; infection loop integration test skips gracefully if no physics space | Tests must not hang — use the SKIP pattern from test_3d_scene.gd for any physics-dependent checks; `tests/scenes/enemies/` directory does not exist — agent must `mkdir -p` before writing |
| 7 | Register new test files in run_tests.gd | Generalist Agent | `tests/run_tests.gd`, two new test files from Task 6 | Updated `tests/run_tests.gd` with both new test classes loaded and their `run_all()` called | Task 6 | `run_tests.sh` discovers and runs both new test files; total failure count reported correctly | Match existing registration pattern in run_tests.gd exactly |
| 8 | Static QA pass | Static QA Agent | All new/modified .gd files from Tasks 2, 4, 6, 7; all new/modified .tscn files from Tasks 3, 4, 5 | QA report; no new lint errors; style matches existing codebase | Task 7 | `run_tests.sh` passes clean; no orphaned nodes in .tscn files; no `@tool` or `extends EditorScript` in headless scripts; no debug prints left in production code | N/A |

---

## Artifact Paths
- Ticket:   `project_board/5_milestone_5_procedural_enemy_generation/in_progress/first_4_families_in_level.md`
- Spec:     `project_board/specs/first_4_families_in_level_spec.md`
- Scripts:  `scripts/asset_generation/generate_enemy_scenes.gd`
- Scenes (generated, by headless tool): `scenes/enemies/generated/adhesion_bug_animated_00.tscn` through `carapace_husk_animated_02.tscn` (12 files) (NEW DIR: `scenes/enemies/generated/`)
- Scenes (placement wrappers): NOT PRODUCED — see ADR-1 in spec
- Level (modified): `scenes/levels/sandbox/test_movement_3d.tscn`
- Tests:    `tests/scenes/enemies/test_enemy_scene_generation.gd` (NEW DIR: `tests/scenes/enemies/`)
            `tests/scenes/enemies/test_enemy_scene_generation_adversarial.gd`
- Test runner: `tests/run_tests.gd` (NOT modified — auto-discovery handles new tests)

---

## Notes
- The headless generator (`generate_enemy_scenes.gd`) must NOT use `@tool` or `extends EditorScript`. It must use `extends SceneTree` with `func _init()` as the entry point. It must call `quit()` at the end.
- All GLBs already have `.import` files; no `godot --import` step required before running the generator, but if ResourceSaver fails to find the res:// project, the agent must run `godot --import` first and document this in the spec.
- Do NOT use `godot --check-only` at any point — it hangs in this project.
- All timeout-guarded Godot invocations use `timeout 300 godot -s <script>`.
- Existing `Enemy` and `Enemy2` nodes in `test_movement_3d.tscn` are REMOVED and replaced with 4 new family-named instances of enemy_infection_3d.tscn. Confirmed safe: test_3d_scene.gd has zero references to nodes named "Enemy" or "Enemy2".
- The `scenes/enemies/` directory does not currently exist; Task 2/3 agent must create it.
- AABB computation: `load_assets.gd` uses `mesh_instance.global_transform` but in headless generation nodes are not added to a scene tree, so `global_transform` is identity. This is acceptable — the AABB will be in local space, which is correct for a freshly instantiated root. Confirmed in spec ADR-3.
- Checkpoint log for this run: `project_board/checkpoints/first_4_families_in_level/run-2026-03-30-01.md`
- Placement wrappers NOT produced: EnemyInfection3D extends CharacterBody3D and cannot be composed as a child of another CharacterBody3D. Level instances enemy_infection_3d.tscn directly. See ADR-1 in spec.

---

# NEXT ACTION

## Next Responsible Agent
Engine Integration Agent

## Required Input Schema
```json
{
  "ticket": "project_board/5_milestone_5_procedural_enemy_generation/in_progress/first_4_families_in_level.md",
  "spec": "project_board/specs/first_4_families_in_level_spec.md",
  "checkpoint_log": "project_board/checkpoints/first_4_families_in_level/run-2026-03-30-01.md",
  "primary_tests": "tests/scenes/enemies/test_enemy_scene_generation.gd",
  "adversarial_tests": "tests/scenes/enemies/test_enemy_scene_generation_adversarial.gd",
  "generator_script": "scripts/asset_generation/generate_enemy_scenes.gd",
  "level_scene": "scenes/levels/sandbox/test_movement_3d.tscn"
}
```

## Status
Proceed

## Reason
Engine Integration Agent implemented generate_enemy_scenes.gd, ran the headless generator to produce all 12 .tscn files in scenes/enemies/generated/, and modified test_movement_3d.tscn to replace Enemy/Enemy2 with 4 family instances (AdhesionBugEnemy, AcidSpitterEnemy, ClawCrawlerEnemy, CarapaceHuskEnemy) at Y=1.0 positions. All 32 primary (FESG-1 through FESG-32) and 22 adversarial (ADV-FESG-1 through ADV-FESG-22) tests pass. run_tests.sh exits clean.

GDScript review pass (Revision 8): applied 5 fixes to generate_enemy_scenes.gd — file header comment, str() Variant coercion, typed Array[MeshInstance3D] for meshes/_gather_mesh_instances, no-op AABB corner simplification, _ensure_dir return-value check. All tests continue to pass.
