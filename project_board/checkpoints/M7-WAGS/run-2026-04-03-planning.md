# M7-WAGS Checkpoint Log — run-2026-04-03-planning

Ticket: `project_board/7_milestone_7_enemy_animation_wiring/in_progress/wire_animations_to_generated_scenes.md`
Run started: 2026-04-03
Stage: PLANNING

## Resume
Autopilot picking up fresh ticket from backlog. Dependencies satisfied (M7-ACS + M7-BAE both COMPLETE).

---

### [M7-WAGS] Planning — AnimationPlayer empty in existing .tscn files
**Would have asked:** The 12 generated .tscn files already contain an `AnimationPlayer` node and an `EnemyAnimationController` node. However, reading the raw .tscn files confirms the `AnimationPlayer` nodes are empty (no `libraries` entries, no animation tracks). The GLB animations are embedded inside the instantiated `Visual/Model` subtree (the GLB's own internal AnimationPlayer), not the root-level `AnimationPlayer`. Does the ticket require regenerating the scenes so the root `AnimationPlayer` can reference the GLB animation library?
**Assumption made:** Yes — the scenes must be regenerated. `generate_enemy_scenes.gd` must be updated to wire the root-level `AnimationPlayer`'s `libraries` property to the animation library extracted from the loaded GLB (via `AnimationPlayer` found inside the instantiated GLB scene), so the root `AnimationPlayer` exposes the named clips `Idle`, `Walk`, `Hit`, `Death` to `EnemyAnimationController`. Without this wiring the `EnemyAnimationController.find_child("AnimationPlayer")` resolves to the empty root-level player, which has no clips, and the Idle animation will never play.
**Confidence:** High

### [M7-WAGS] Planning — state_machine null blocks _ready_ok
**Would have asked:** `EnemyAnimationController._ready_ok` is set to `true` only when `animation_player`, `state_machine`, AND `_parent_body` are all non-null. The generator calls `setup(null)` on the controller. Does the "idle animation playing in-editor" AC require wiring a stub state machine, or should the controller's null-state behavior be changed to allow idle playback without a state machine?
**Assumption made:** The ticket AC says "shows idle animation playing in-editor (not a T-pose)" but `_ready_ok = false` when `state_machine` is null — the controller will not dispatch any animation. To satisfy the AC with minimal scope and without changing the already-complete `EnemyAnimationController` script, `generate_enemy_scenes.gd` should be updated to wire an `EnemyStateMachine` stub (or a minimal compatible object) that returns `"idle"` as its state and `Vector3.ZERO` as velocity, so `_ready_ok = true` and the Idle clip plays at load. The alternative — changing the controller to allow null state machine — is out of scope (M7-ACS is COMPLETE and has 39 tests). The stub must conform to the `get_state() -> String` interface expected by the controller.
**Confidence:** Medium — the AC is explicit ("not a T-pose") but the mechanism for achieving it without modifying the completed controller requires a stub or a real ESM instance. Spec Agent should validate this interpretation and choose the minimal approach.

### [M7-WAGS] Planning — scope of testing for the wired .tscn scenes
**Would have asked:** The existing `test_enemy_animation_clips.gd` tests the GLB directly (that the GLB contains an AnimationPlayer with Idle/Walk/Hit/Death). There is no test that loads the generated `.tscn` files and verifies the root `AnimationPlayer` has the clips wired (not the GLB's internal player). Should a new test be written for this?
**Assumption made:** Yes — a new GDScript test file `tests/scenes/enemies/test_enemy_scene_animation_wiring.gd` is needed to verify: (1) each generated .tscn scene has an `AnimationPlayer` at the root level with the 4 required clips available, and (2) an `EnemyAnimationController` child node is present. This directly maps to the ticket ACs "All 12 generated .tscn files contain an EnemyAnimationController node" and "Each controller correctly resolves the AnimationPlayer sibling at _ready()". The `run_tests.gd` auto-discovers `test_*.gd` files so no manual registration is needed.
**Confidence:** High

### [M7-WAGS] Planning — generate_enemy_scenes.gd GLB animation library wiring mechanism
**Would have asked:** In Godot 4, to expose a GLB's embedded animations through a root-level `AnimationPlayer`, the generator can use `AnimationPlayer.add_animation_library(name, library)` where the library is obtained by instantiating the GLB, finding its internal `AnimationPlayer`, and calling `get_animation_library("")`. Is this the correct approach at scene-generation time (in `_generate_scene_for_glb`)?
**Assumption made:** Yes — at generation time (the script runs under `SceneTree` with full Godot resource loading), the generator can instantiate the GLB, find its internal `AnimationPlayer` via `find_child("*", "AnimationPlayer", true, false)`, call `get_animation_library("")` to get the library resource, and then call `anim_player.add_animation_library("", library)` on the root-level player. The library should be obtained by `duplicate()` to avoid shared resource mutation. The Spec Agent should verify the exact Godot 4 API for this pattern and whether `add_animation_library` is available in the SceneTree context used by the generator. An alternative is to use `AnimationMixer.capture_library` or reference the path; Spec Agent owns this decision.
**Confidence:** Medium — the API exists in Godot 4 but headless generator context constraints must be confirmed.

### [M7-WAGS] Planning — whether to regenerate all 12 scenes or patch via scene editing
**Would have asked:** Should we update `generate_enemy_scenes.gd` and re-run it to regenerate all 12 scenes, or should we write a separate one-off migration script that patches the existing `.tscn` files?
**Assumption made:** Update `generate_enemy_scenes.gd` and re-run. The generator is the single source of truth for generated scenes. A migration/patch script would create two divergent sources of truth. Re-running the generator overwrites all 12 scenes with the correct structure.
**Confidence:** High

---

## Resume: 2026-04-03T12:00:00Z (ap-continue)
Ticket: `project_board/7_milestone_7_enemy_animation_wiring/in_progress/wire_animations_to_generated_scenes.md`
Resuming at Stage: PLANNING (planning decisions already recorded above)
Next Agent: Spec Agent → implementation

### [M7-WAGS] Planning correction — setup(null) does not serialize
**Would have asked:** Generator-only `setup(stub)` runs before `PackedScene.pack()` but `state_machine` is not an `@export`; it is not saved in `.tscn`. Is a persistent stub required in the scene tree?
**Assumption made:** Add a named child node under `EnemyAnimationController` with a tiny script implementing `get_state() -> String` returning `"idle"`, and extend `EnemyAnimationController._ready()` to assign `state_machine` from `find_child` when `setup()` was never called with a real ESM. This preserves existing EAC tests (no stub child there) and satisfies in-editor idle for generated scenes.
**Confidence:** High
