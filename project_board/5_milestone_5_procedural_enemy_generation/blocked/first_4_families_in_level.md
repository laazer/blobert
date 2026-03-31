Title:
Place first 4 enemy families in prototype level
---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | BLOCKED |
| Revision | 12 |
| Last Updated By | Acceptance Criteria Gatekeeper Agent |
| Next Responsible Agent | Human |
| Validation Status | AC-1 — PASS: AdhesionBugEnemy, AcidSpitterEnemy, ClawCrawlerEnemy, CarapaceHuskEnemy confirmed in test_movement_3d.tscn lines 58-76 as enemy_infection_3d.tscn instances at positions (4,1,0), (-4,1,0), (0,1,4), (0,1,-4); covered by FESG-22 through FESG-26, FESG-29, FESG-30, FESG-31 (54 total tests pass). \| AC-2 — PASS by construction (ADR-1): all 4 enemies are EnemyInfection3D instances; _on_body_entered wires set_target_esm; InfectionInteractionHandler present at level root; architecture identical to previously working enemies; confirmed by FESG-31. \| AC-3 — PASS by static analysis: enemy_infection_3d.gd has @export var mutation_drop; level overrides set "adhesion"/"acid"/"claw"/"carapace" per instance; infection_interaction_handler.gd line 66 reads _target_enemy.mutation_drop directly; infection_absorb_resolver.gd uses mutation_id over DEFAULT_MUTATION_ID when non-empty; full call chain is statically unambiguous. \| AC-4 — PASS: FESG-9, ADV-FESG-2, ADV-FESG-3, ADV-FESG-20 verify collision/type correctness; FESG-26 confirms old nodes removed; FESG-29/30 verify positions; generate_enemy_scenes.gd confirmed extends SceneTree (not @tool); no debug prints in production code. \| AC-5 — BLOCKED: structural evidence present (no @tool, no debug-only nodes, no debug prints, valid enemy positions); human play session confirming the level is playable without debug tools has NOT been documented; per project convention (two_mutation_slots.md, player_hud.md, LEARNINGS.md line 63) this class of AC requires explicit human verification before COMPLETE. |
| Blocking Issues | AC-5 ("Playable without debug tools"): No human play session has been documented. A human must open test_movement_3d.tscn, run the scene, approach each of the 4 placed enemies, perform the weaken-infect-absorb sequence on at least one, and confirm the game is playable without debug overlays or debug tools active. Confirmation must be documented in this ticket's Blocking Issues (or a new revision) before Stage advances to COMPLETE. |

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
Human

## Required Input Schema
```json
{
  "action": "Manual play session verification for AC-5",
  "steps": [
    "1. Open Godot editor; load scenes/levels/sandbox/test_movement_3d.tscn as the main scene.",
    "2. Run the scene (F5 or play button).",
    "3. Confirm no debug overlays, no debug-only nodes, and no debug tools are required to play.",
    "4. Approach each of the 4 placed enemies (AdhesionBugEnemy, AcidSpitterEnemy, ClawCrawlerEnemy, CarapaceHuskEnemy).",
    "5. On at least one enemy: perform the full weaken-infect-absorb sequence and confirm the correct per-family mutation is granted.",
    "6. Confirm the level is playable end-to-end without debug assistance.",
    "7. Document confirmation in this ticket's Blocking Issues field, clearing the AC-5 block.",
    "8. If all clear: set Stage to COMPLETE, move ticket to done/ folder, set Next Responsible Agent to Human, Status to Proceed."
  ]
}
```

## Status
Needs Attention

## Reason
AC-1 through AC-4 are fully satisfied by automated tests and static code inspection (54 FESG tests pass; level file confirmed; per-family mutation call chain statically unambiguous; no regressions). AC-5 ("Playable without debug tools") requires a documented human play session per established project convention (see two_mutation_slots.md, player_hud.md, LEARNINGS.md). No such session has been documented. Ticket held at Stage INTEGRATION until human confirms and documents AC-5 sign-off.
