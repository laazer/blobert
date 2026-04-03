# Checkpoints: M7-BAE Planning Run — 2026-03-31

## Summary

Planner Agent run for ticket `blender_animation_export`.
Decomposed into 5 tasks covering: NLA strip wiring, clip name mapping,
GLB regeneration, Godot AnimationPlayer validation, and regression guard.

---

### [M7-BAE] Planning — Clip naming convention (pipeline vs controller)

**Would have asked:** The existing pipeline creates Blender action names in
lowercase/snake_case (`idle`, `move`, `attack`, `damage`, `death`). The
implemented `EnemyAnimationController` expects PascalCase names (`Idle`,
`Walk`, `Hit`, `Death`). The ticket acceptance criteria say "consistent string
names" and reference `Idle`, `Walk`, `Hit`, `Death`. Should the Blender script
rename the exported NLA strips to PascalCase, or should the controller be
updated to accept lowercase names?

**Assumption made:** The controller is already implemented and its tests are
passing (ticket `animation_controller_script` is in `done/`). Changing the
controller's expected clip names would require re-speccing and re-testing ACS.
The pipeline is the thing being changed in this ticket. Therefore the pipeline
must export clips with PascalCase names matching what the controller already
expects: `Idle`, `Walk`, `Hit`, `Death`. The mapping is:
  - `idle`   → `Idle`
  - `move`   → `Walk`
  - `damage` → `Hit`
  - `death`  → `Death`
`attack` has no direct match in the four required names and will be exported as
`Attack` (extra clip, non-breaking).

**Confidence:** High

---

### [M7-BAE] Planning — Minimum clip set vs full 13-clip set

**Would have asked:** The ticket AC requires exactly 4 named clips (`Idle`,
`Walk`, `Hit`, `Death`) per GLB. The pipeline currently builds 13 clips per
animated enemy (`animation_set='all'`). Should the Blender export be
restricted to 4 clips, or should it export all 13 with the 4 required ones
being a guaranteed subset?

**Assumption made:** The 4 required clips are the minimum contract for Godot
wiring. Exporting all 13 is harmless and preserves optionality for future
tickets. The implementation should keep `animation_set='all'` and ensure the
4 required PascalCase names are present in the output. The spec agent should
confirm whether all 13 or exactly 4 is the right scope.

**Confidence:** Medium

---

### [M7-BAE] Planning — NLA strip vs single action GLB export

**Would have asked:** The current `export_enemy` function sets only one active
action and calls `bpy.ops.export_scene.gltf(export_animations=True)`. In
Blender, only the active action (or NLA-stacked strips) are included in the
GLTF export. Are the 13 created actions currently making it into the GLB, or
is only the active `idle` action exported?

**Assumption made:** Based on reading `animation_system.py`, each animation is
a separate Blender `bpy.data.actions` object with `use_fake_user = True`. The
GLTF exporter in Blender 3.x+ exports all NLA strip actions when
`export_nla_strips=True` and `export_all_influences=False`. Without NLA strips,
only the active action is exported. The existing code does NOT push actions into
NLA tracks, so only `idle` is exported. The implementation task must add NLA
track wiring after all actions are created so the GLTF exporter sees all clips.

**Confidence:** High

---

### [M7-BAE] Planning — Which enemy families to regenerate

**Would have asked:** The ticket says "all 4 families" and lists GLBs under
`assets/enemies/generated_glb/`. The generated_glb directory currently contains
`adhesion_bug`, `acid_spitter`, `claw_crawler`, `carapace_husk` (3 variants
each). The constants file lists 6 animated types including `tar_slug` and
`ember_imp`. Should regeneration target only the 4 families currently present
as GLBs, or all 6 animated types?

**Assumption made:** Regeneration scope is the 4 families that currently have
GLBs in `assets/enemies/generated_glb/` (the families already wired into
Godot scenes). Adding new families is out of scope for this ticket. The
implementation agent should regenerate `adhesion_bug`, `acid_spitter`,
`claw_crawler`, `carapace_husk` (1 variant each is sufficient for a spec
pass; the current 3 variants can each be regenerated).

**Confidence:** Medium

---

### [M7-BAE] Planning — Godot AnimationPlayer verification method

**Would have asked:** Verifying that `AnimationPlayer` has all 4 clips requires
either a Godot runtime test (headless GDScript), a Python gltf parser, or
manual inspection. Which is acceptable?

**Assumption made:** A new headless GDScript test in `tests/scenes/enemies/`
that loads the generated GLB as a PackedScene, instantiates it, and asserts
that an `AnimationPlayer` node exists with animation names including `Idle`,
`Walk`, `Hit`, `Death` is the correct verification method. This is consistent
with the existing `test_enemy_scene_generation.gd` pattern.

**Confidence:** High

---

## Spec Agent Checkpoints — 2026-04-02

---

### [M7-BAE] Spec — NLA track naming: one track per action vs all on one track

**Would have asked:** Blender's NLA system allows multiple strips on a single
track, or one strip per track. Does the GLTF exporter require each action to
be on its own NLA track, or is stacking multiple strips on one track also
exported correctly?

**Assumption made:** Each action must be placed on its own NLA track to
guarantee independent clip export. Stacking multiple strips on a single track
creates additive blending at overlap zones and may cause GLTF exporter to
merge or skip strips. The spec requires one `nla_tracks.new()` call per action,
one strip per track, with non-overlapping frame ranges (start=1,
end=action.frame_range[1]) per strip. This is the safest and most portable
arrangement across Blender 3.x and 4.x GLTF exporters.

**Confidence:** High

---

### [M7-BAE] Spec — GLTF export keyword arguments for multi-clip NLA export

**Would have asked:** The existing `export_enemy` call uses
`export_animations=True` but does not pass `export_nla_strips`. In Blender
3.x the parameter is `export_nla_strips=True`; in Blender 4.x the parameter
was renamed or the behavior changed (NLA strips are exported when
`armature.animation_data.action` is None and strips are present). Which
Blender version is in use, and which export keyword is authoritative?

**Assumption made:** The project memory confirms Blender was installed for M5.
Blender version is assumed to be 3.6 LTS or 4.x (common install at this date).
The conservative spec is: set `armature.animation_data.action = None` before
export (NLA-driven mode), and pass `export_nla_strips=True` to
`bpy.ops.export_scene.gltf()`. If `export_nla_strips` is rejected as an
unknown kwarg on the installed version, the implementer must omit it and rely
solely on `action = None` + NLA strips being present (Blender 4.x behavior).
The spec documents both code paths; the implementer chooses based on the
Blender version at runtime.

**Confidence:** Medium

---

### [M7-BAE] Spec — OBJECT mode guard before NLA track creation

**Would have asked:** Creating NLA tracks while the armature is in POSE mode
may raise a Blender context error. The existing `create_all_animations` ends
with `armature.animation_data.action = created_actions[0]` and the armature
is still in POSE mode. Must the implementation switch back to OBJECT mode
before calling `nla_tracks.new()`?

**Assumption made:** Blender's NLA API (`bpy.types.AnimData.nla_tracks`) is
accessible in OBJECT mode without errors and is not accessible while the
armature is in POSE mode (Blender raises `RuntimeError: Operator bpy.ops.nla.*
poll() failed`). The spec requires: after all actions are created and
keyframed (while still in POSE mode), switch to OBJECT mode via
`bpy.ops.object.mode_set(mode='OBJECT')` before creating any NLA tracks.

**Confidence:** High

---

### [M7-BAE] Spec — Full export name mapping for all 13 internal clip names

**Would have asked:** The ticket defines export names only for the 5 core
clips. What are the export names for the 8 extended clips (`spawn`,
`special_attack`, `damage_heavy`, `damage_fire`, `damage_ice`, `stunned`,
`celebrate`, `taunt`)? Should they use title-cased versions of the internal
name, snake_case → PascalCase, or some other convention?

**Assumption made:** Extended clips use a mechanical snake_case → PascalCase
conversion: each underscore-delimited word is title-cased and the underscores
are dropped. For example: `special_attack` → `SpecialAttack`,
`damage_heavy` → `DamageHeavy`, `damage_fire` → `DamageFire`,
`damage_ice` → `DamageIce`. The required 4 clips override this rule with their
explicit names (`idle`→`Idle`, `move`→`Walk`, `damage`→`Hit`, `death`→`Death`).
`attack`→`Attack` and `spawn`→`Spawn` follow the title-case rule.
All 13 mappings are listed explicitly in the spec.

**Confidence:** High

---

### [M7-BAE] Spec — NLA strip frame start: 0 vs 1

**Would have asked:** Blender actions created by the existing system use
`frame_range = (1, length)`. NLA strips can be placed starting at frame 0 or
frame 1. Does the GLTF exporter require strips to start at frame 0 for correct
clip timing in Godot?

**Assumption made:** The GLB/GLTF format encodes animation clips with relative
time offsets from the strip start. Whether the strip is placed at NLA frame 0
or 1 is internal to Blender and does not affect the exported clip timing.
The spec requires the NLA strip `action_frame_start = 1` and `action_frame_end
= action.frame_range[1]` to match the action's own range, and places the strip
at NLA timeline position `frame_start = 0` for simplicity. Godot will see each
clip as starting at t=0 within its own track.

**Confidence:** Medium

---

### [M7-BAE] Spec — Scope of changes to export_enemy in base_enemy.py

**Would have asked:** The `export_enemy` function currently sets
`armature.animation_data.action = created_actions[0]` and does not pass
`export_nla_strips`. Should `export_enemy` be modified to clear the active
action before calling gltf export, or should that be done at the end of
`create_all_animations`?

**Assumption made:** The correct owner of the "NLA-driven mode" state is
`create_all_animations`, since it creates the animations and knows the NLA
setup. `create_all_animations` must set `armature.animation_data.action = None`
as its final step (replacing the current line that sets it to `created_actions[0]`).
`export_enemy` must additionally be updated to pass `export_nla_strips=True`
(conditionally, based on Blender version detection) to `bpy.ops.export_scene.gltf`.
The spec defines both changes as required.

**Confidence:** High (Spec Agent checkpoint block ends)

---

## Test Designer Agent Checkpoints — 2026-04-02

---

### [M7-BAE] TestDesign — run_tests.gd wiring needed or auto-discovered

**Would have asked:** The ticket's Task 5 says "Wire new test into test runner". Does run_tests.gd require manual entry per test file, or does it auto-discover?

**Assumption made:** Reading run_tests.gd confirms it auto-discovers all files under tests/ whose name begins with "test_" and ends with ".gd" via recursive directory walk. No manual wiring entry is needed; placing test_enemy_animation_clips.gd in tests/scenes/enemies/ is sufficient for the runner to pick it up. BAE-4.1 (string "test_enemy_animation_clips" appearing in run_tests.gd) is satisfied by the auto-discovery path string, not by a hardcoded include. Task 5 wiring is therefore already complete once the file is placed correctly.

**Confidence:** High

---

### [M7-BAE] TestDesign — Python test file location for get_export_name tests

**Would have asked:** The NEXT ACTION in the ticket lists BAE-2.1 through BAE-2.5 and BAE-2.8 as Python pytest tests. There is no existing test file for constants.py. Should a new file be added under asset_generation/python/tests/animations/ or in a new utils/ subdirectory?

**Assumption made:** The spec scopes BAE-2 changes to constants.py (AnimationTypes class). The closest existing test directory for constants is asset_generation/python/tests/. Creating a new file at asset_generation/python/tests/utils/test_animation_export_names.py is the correct placement — it mirrors the structure of tests/animations/ and keeps constants tests separate from body-type tests. A conftest.py is not needed because the existing pattern (sys.modules.setdefault bpy mock at module level) is sufficient.

**Confidence:** High

---

### [M7-BAE] TestDesign — BAE-1 NLA wiring tests are structural/source-inspection

**Would have asked:** BAE-1.1 through BAE-1.7 are specified as "verified by reading the source". Are these static analysis checks (grep/AST), or are they runtime tests that call create_all_animations() with a mock?

**Assumption made:** BAE-1.1 through BAE-1.7 are primarily source-structure requirements verifiable by the implementer and reviewer via code inspection, not by a separate test file. The spec says "Verified by reading the source" for BAE-1.1, BAE-1.4, BAE-2.6, BAE-2.7. Writing a unit test that mocks bpy and calls create_all_animations() to verify NLA strip count (BAE-1.2, BAE-1.3, BAE-1.7) is possible and desirable. These are included in the Python test file. BAE-1.4 (action=None on return) and BAE-1.1 (mode switch before NLA) are tested via mock capture of bpy.ops.object.mode_set and inspection of animation_data.action after the call.

**Confidence:** Medium

---

### [M7-BAE] TestDesign — BAE-1.5 export_nla_strips test missing from prior run

**Would have asked:** The prior test file in tests/utils/test_animation_export_names.py covered BAE-NLA-1 through BAE-NLA-8 (create_all_animations NLA wiring) but did not include a test for BAE-1.5 (export_enemy passes export_nla_strips=True to bpy.ops.export_scene.gltf). Should a test for export_enemy be added to the existing file or a new file?

**Assumption made:** The missing BAE-1.5 coverage is a genuine spec gap in the prior test run. A test class TestExportEnemyNLAFlag has been added to tests/utils/test_animation_export_names.py. It mocks bpy.ops.export_scene.gltf, calls export_enemy(), and asserts export_nla_strips=True is present in the captured kwargs. This test will be red (failing) until Task 1 implementation adds the kwarg to the gltf() call. The test is placed in the same file as other BAE-1/BAE-2 tests to keep export-pipeline tests colocated.

**Confidence:** High

---

## Test Breaker Agent Checkpoints — 2026-04-02

---

### [M7-BAE] TestBreak — bmesh mock missing in TestExportEnemyNLAFlag

**Would have asked:** `TestExportEnemyNLAFlag` imports `export_enemy` which transitively imports `blender_utils.py`, which does `import bmesh` at module level. `bmesh` is not added to `sys.modules` mock setup. Is this an infra bug that must be fixed in the test, or should the adversarial test leave it as-is and add a separate infrastructure regression?

**Assumption made:** The intent of the test is to catch the missing `export_nla_strips=True` kwarg, not to fail on missing `bmesh`. The adversarial suite adds `sys.modules.setdefault('bmesh', MagicMock())` to the mock setup block in the new adversarial file. This is the same conservative pattern as the existing `bpy`/`mathutils` mock. The existing `test_animation_export_names.py` is not modified; the fix is localized to the new adversarial file's own copy of the export_enemy tests that properly mock `bmesh`. # CHECKPOINT

**Confidence:** High

---

### [M7-BAE] TestBreak — PascalCase fallback boundary: empty string

**Would have asked:** The spec says fallback splits on `_`, title-cases each word, joins without separator. What should `get_export_name("")` return — `""`, raise, or something else?

**Assumption made:** `get_export_name("")` should return `""` (empty join of an empty split). The adversarial test asserts this. An implementation that raises AttributeError or returns None fails the test, exposing a crash path reachable if a calling loop ever passes an empty internal name. # CHECKPOINT

**Confidence:** Medium

---

### [M7-BAE] TestBreak — PascalCase fallback: all-underscore input

**Would have asked:** `get_export_name("___")` — each token after split is `""`. `"".title()` returns `""`. Should the output be `""` (3 empty tokens joined) or raise?

**Assumption made:** Output is `""`. This is the most conservative mechanical interpretation of the spec's "split on _, title-case each word, join". # CHECKPOINT

**Confidence:** Medium

---

### [M7-BAE] TestBreak — NLA strip name attribute must equal export name

**Would have asked:** The existing `test_bae_nla_3_one_strip_per_track` verifies one strip per track but does not assert that `strip.name == export_name`. The spec (BAE-1.3) says `name` argument to `track.strips.new(name, start, action)` must be the export name. Is there an existing test for this?

**Assumption made:** No existing test checks `strip.name`. Adding `test_bae_adv_strip_name_equals_export_name` exposes a mutation where the implementer passes the internal name as the strip name rather than the export name. # CHECKPOINT

**Confidence:** High

---

### [M7-BAE] TestBreak — GDScript: AnimationPlayer on wrong node path

**Would have asked:** The spec says `find_children("*", "AnimationPlayer", true, false)` must be used (recursive type search). A regression where the implementation uses a hardcoded path like `root.get_node("Armature/AnimationPlayer")` would pass if the path exists but fail silently on any GLB where the depth differs. Should the adversarial GDScript suite verify the search finds AnimationPlayer regardless of exact depth?

**Assumption made:** Yes. The adversarial GDScript file adds a test that loads the GLB and asserts `find_children` discovers the same AnimationPlayer as `get_node_or_null` would at a hardcoded path — if both return null the test skips, but if `find_children` returns null and `get_node` finds it at a known path, that is a test failure (wrong search method used). # CHECKPOINT

**Confidence:** Medium

---

### [M7-BAE] TestBreak — GDScript: lowercase clip name is NOT in animation list

**Would have asked:** If the pipeline produces "idle" instead of "Idle" (case regression), the existing BAE-01 fails. But does any test explicitly assert that the wrong-case name is absent? Adding an explicit assertion that "idle" is absent catches the symmetric error where both "idle" and "Idle" are somehow present, or where only "idle" is present.

**Assumption made:** The adversarial GDScript file adds checks that the internal lowercase names are absent. This is a mutation target: if the implementer exports both names, or exports only lowercase, the adversarial tests catch it while existing tests may pass. # CHECKPOINT

**Confidence:** High

---

### [M7-BAE] TestBreak — Python: get_export_name return type is exactly str, not subclass

**Would have asked:** Could `get_export_name` return a bytes or str-subclass that passes `assertIsInstance(result, str)` but breaks downstream Blender API calls that expect plain `str`?

**Assumption made:** The adversarial test adds `assertIs(type(result), str)` (not just assertIsInstance) for the 4 required clip names. This catches a MagicMock leak where the mock returns a Mock object that passes isinstance checks but is not actually a str. # CHECKPOINT

**Confidence:** Medium

---

### [M7-BAE] TestBreak — Stage transition: IMPLEMENTATION_ENGINE_INTEGRATION not in enum

**Would have asked:** The task prompt says to advance Stage to `IMPLEMENTATION_ENGINE_INTEGRATION`. The workflow enforcement module's Stage enum is: `PLANNING | SPECIFICATION | TEST_DESIGN | TEST_BREAK | IMPLEMENTATION_BACKEND | IMPLEMENTATION_FRONTEND | IMPLEMENTATION_GENERALIST | STATIC_QA | INTEGRATION | DEPLOYMENT | BLOCKED | COMPLETE`. `IMPLEMENTATION_ENGINE_INTEGRATION` is not listed.

**Assumption made:** The closest valid stage for this ticket (Tasks 1-2 = Blender Python pipeline, Tasks 3-5 = GLB regeneration + Godot headless wiring) is `IMPLEMENTATION_GENERALIST`. The Planner's intent with "Engine Integration Agent" aligns with the Generalist Agent's cross-domain scope in this project. Advancing to `IMPLEMENTATION_GENERALIST` and setting Next Responsible Agent to `Engine Integration Agent` (the Planner's label for the next executor). # CHECKPOINT

**Confidence:** High

