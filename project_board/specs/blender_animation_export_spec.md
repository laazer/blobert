# Spec: blender_animation_export (M7-BAE)

**Ticket:** `project_board/7_milestone_7_enemy_animation_wiring/in_progress/blender_animation_export.md`
**Spec Date:** 2026-04-02
**Spec Agent Revision:** 1
**Scope:** Tasks 1 and 2 only (pipeline Python changes). Tasks 3-5 are covered by the ticket's execution plan directly.

---

## Background and Context

The Blender Python pipeline at `asset_generation/python/src/` generates enemy 3D models and
animates them via `create_all_animations()` in `animation_system.py`. The function creates 13
Blender actions per armature (`animation_set='all'`) but exports only the last-set active action
to GLB, not all clips. The implemented `EnemyAnimationController` (ticket M7-ACS, complete)
expects Godot `AnimationPlayer` clips named exactly: `Idle`, `Walk`, `Hit`, `Death`. The
pipeline currently names all actions in lowercase snake_case (`idle`, `move`, `damage`, `death`).

Two changes are required:
1. Push all created actions into individual NLA tracks so the GLTF exporter emits all clips.
2. Rename actions and NLA strips using an export-name mapping so clip names in the GLB
   match what the Godot controller expects.

---

## Requirement BAE-1: NLA Strip Wiring in `create_all_animations()`

### 1. Spec Summary

**Description:**
`create_all_animations()` in `asset_generation/python/src/animations/animation_system.py`
must, after creating all animation actions, push each action into its own NLA track on the
armature and then set the armature to NLA-driven mode (no active action) before returning.
The GLTF exporter reads NLA tracks when `armature.animation_data.action` is `None`; without
this, only the single active action is exported.

**Constraints:**
- NLA tracks must be created in OBJECT mode. Blender raises a context error if
  `nla_tracks.new()` is called while the armature is in POSE mode.
- Each action must occupy its own distinct NLA track (one track per action). Multiple strips
  on one track risk additive blending and may cause exporter clip merging.
- Each NLA strip must cover exactly the frame range of its action:
  - `strip.action_frame_start = 1`
  - `strip.action_frame_end = action.frame_range[1]`
  - `strip.frame_start = 0` (NLA timeline position; relative offset, not action frame)
- After all NLA strips are created, `armature.animation_data.action` must be set to `None`
  so the GLTF exporter uses NLA mode rather than a single active action.
- The existing keyframe creation logic, bone iteration, and `AnimationConfig.get_length()`
  lookups must not be modified. Only the post-loop block and mode transitions change.
- The existing `export_enemy()` call in `base_enemy.py` must also pass
  `export_nla_strips=True` to `bpy.ops.export_scene.gltf()`. If the installed Blender
  version does not accept this keyword argument (Blender 4.x changed the parameter name),
  the implementer must detect the version at runtime and omit the parameter while relying on
  `action = None` to trigger NLA export.

**Assumptions:**
- Blender version is 3.6 LTS or 4.x. Both support NLA-driven GLTF export via
  `action = None` when NLA strips are present.
- The armature's `animation_data` will be present by the time NLA wiring runs, because
  `armature.animation_data_create()` is called inside the loop for each action.
- `use_fake_user = True` on each action (already set) prevents garbage collection before
  the strip references the action.

**Scope:**
- `asset_generation/python/src/animations/animation_system.py`: `create_all_animations()`
- `asset_generation/python/src/enemies/base_enemy.py`: `export_enemy()`
- No other files.

### 2. Acceptance Criteria

**BAE-1.1 — Mode switch before NLA wiring:**
Before any `nla_tracks.new()` call, `bpy.ops.object.mode_set(mode='OBJECT')` is called
with the armature set as `bpy.context.view_layer.objects.active`. Verified by reading the
source: the mode switch appears after the keyframing loop closes and before the first NLA
call.

**BAE-1.2 — One track per action:**
For each action in `created_actions` (N actions total), exactly N distinct NLA tracks are
created on `armature.animation_data.nla_tracks`. Each track is created via
`armature.animation_data.nla_tracks.new()`. No action is skipped.

**BAE-1.3 — One strip per track with correct frame range:**
For each track created in BAE-1.2, exactly one strip is added via
`track.strips.new(name, start, action)` where:
- `name` is the export name of the action (see BAE-2 for the mapping)
- `start` is `0` (integer, NLA timeline frame)
- `action` is the corresponding `bpy.data.actions` object
After strip creation, the following attributes are set on the strip:
- `strip.action_frame_start = 1`
- `strip.action_frame_end = action.frame_range[1]`

**BAE-1.4 — NLA-driven mode on return:**
The final statement (or the statement immediately before `return`) of
`create_all_animations()` sets `armature.animation_data.action = None`. No code after this
line (re)sets `armature.animation_data.action` to a non-None value within this function.

**BAE-1.5 — export_enemy passes NLA export flag:**
`bpy.ops.export_scene.gltf()` in `export_enemy()` includes `export_nla_strips=True` as a
keyword argument, OR the code contains a runtime Blender version check that passes this
argument only on supported versions and falls back to relying on `action = None` on
unsupported versions. The fallback must be documented with an inline comment explaining the
version-specific behavior.

**BAE-1.6 — Existing Python unit tests continue to pass:**
`cd asset_generation/python && python -m pytest tests/ -q` exits 0 after the change. The
test in `tests/animations/test_attack_frames.py` mocks `bpy` and tests keyframe logic only;
it must not be broken by the NLA wiring addition.

**BAE-1.7 — No action is left without a corresponding NLA strip:**
The count of NLA strips across all tracks on the armature equals the count of created
actions. A `print()` statement logging `f"NLA: {len(created_actions)} strips wired"`
confirms this at runtime (visible in Blender stdout).

### 3. Risk & Ambiguity Analysis

**Risk R1.1 — Blender version parameter name for NLA export:**
`export_nla_strips` exists in Blender 3.6. In Blender 4.0+, the GLTF exporter's parameter
was refactored; the parameter may be gone (NLA export is automatic when `action = None`).
If the implementer passes an unknown keyword to `bpy.ops.export_scene.gltf()`, Blender
raises `TypeError` and the GLB is not written. Mitigation: wrap in try/except or inspect
the operator's `bl_rna.properties` at runtime to check if the parameter exists.

**Risk R1.2 — Context mode when `create_all_animations` is called from `build()`:**
`build()` in `base_enemy.py` calls `create_all_animations()` immediately after
`ensure_mesh_integrity()`. The armature may be in any mode at that point. The function
already sets POSE mode at line 23; the new NLA wiring code must explicitly switch to OBJECT
mode even if it believes the current mode is already OBJECT, to avoid context errors from
intermediate calls.

**Risk R1.3 — NLA track mutation while looping:**
The implementation must not iterate over `nla_tracks` while simultaneously adding to it.
Build the NLA wiring from `created_actions` list (which is fully populated before any NLA
call), not from `nla_tracks`.

**Risk R1.4 — `action.frame_range` is read-only until the action has at least one keyframe:**
The existing code already sets `action.frame_range = (1, length)` explicitly. This
assignment must remain before the NLA strip creation block that reads `action.frame_range[1]`.

### 4. Clarifying Questions

None. All ambiguities resolved via checkpoint assumptions above.

---

## Requirement BAE-2: Export Name Mapping in `constants.py` and `animation_system.py`

### 1. Spec Summary

**Description:**
`AnimationTypes` in `asset_generation/python/src/utils/constants.py` must be extended with
a `get_export_name(internal_name: str) -> str` classmethod that returns the PascalCase GLB
clip name for a given internal animation name. `create_all_animations()` must use this
method to name each created action and each NLA strip with the export name rather than the
internal name. The export names are the string literals that Godot's `AnimationPlayer` will
expose; they must exactly match what `EnemyAnimationController` requests.

**Constraints:**
- The 4 required export names are non-negotiable: `"Idle"`, `"Walk"`, `"Hit"`, `"Death"`.
  Any deviation breaks the wired controller.
- The mapping must be a static dictionary, not computed dynamically, so the values are
  inspectable without running Blender.
- The existing class constants (`IDLE`, `MOVE`, `ATTACK`, `DAMAGE`, `DEATH`, etc.) must
  not be renamed or removed; only a new classmethod is added.
- `get_export_name()` must accept any internal name string and return a string. If the
  internal name is not in the map, the fallback is mechanical PascalCase conversion:
  split on `_`, title-case each word, concatenate. This ensures extended clips are exported
  consistently without requiring the map to enumerate all 13 entries explicitly.
- The action name in `bpy.data.actions.new(name=...)` must use the export name (not the
  internal name). This is the string that will appear as the clip name in the exported GLB.
- The `print()` log line currently says `f"Created {anim_name} animation: frames 1-{length}"`;
  it should continue to log the export name (which is the new `anim_name` value after the
  mapping is applied at the start of the loop, or the log can explicitly show both).

**Assumptions:**
- The full export name mapping for all 13 internal names is:

  | Internal name    | Export name      |
  |-----------------|-----------------|
  | `idle`          | `Idle`          |
  | `move`          | `Walk`          |
  | `attack`        | `Attack`        |
  | `damage`        | `Hit`           |
  | `death`         | `Death`         |
  | `spawn`         | `Spawn`         |
  | `special_attack`| `SpecialAttack` |
  | `damage_heavy`  | `DamageHeavy`   |
  | `damage_fire`   | `DamageFire`    |
  | `damage_ice`    | `DamageIce`     |
  | `stunned`       | `Stunned`       |
  | `celebrate`     | `Celebrate`     |
  | `taunt`         | `Taunt`         |

- `get_export_name("idle") == "Idle"` is the canonical test shape.
- The `AnimationConfig.get_length()` lookup continues to use the internal name
  (the `LENGTHS` dict key is still `AnimationTypes.IDLE` = `"idle"`), not the export name.
  The internal name is used only for length lookups and body_type dispatch; the export name
  is used only for action naming and NLA strip naming.

**Scope:**
- `asset_generation/python/src/utils/constants.py`: `AnimationTypes` class, add `get_export_name()`
- `asset_generation/python/src/animations/animation_system.py`: `create_all_animations()`,
  the action-naming call and the NLA strip name argument

### 2. Acceptance Criteria

**BAE-2.1 — `get_export_name` classmethod exists on `AnimationTypes`:**
`AnimationTypes.get_export_name` is callable as a classmethod with one positional argument
(the internal name string). It returns a `str`. Verified by direct call in a unit test
without mocking.

**BAE-2.2 — Required 4 clips map to exact expected strings:**
- `AnimationTypes.get_export_name("idle") == "Idle"`
- `AnimationTypes.get_export_name("move") == "Walk"`
- `AnimationTypes.get_export_name("damage") == "Hit"`
- `AnimationTypes.get_export_name("death") == "Death"`
Each verified independently.

**BAE-2.3 — Additional explicit mappings:**
- `AnimationTypes.get_export_name("attack") == "Attack"`
- `AnimationTypes.get_export_name("spawn") == "Spawn"`
- `AnimationTypes.get_export_name("special_attack") == "SpecialAttack"`
- `AnimationTypes.get_export_name("damage_heavy") == "DamageHeavy"`
- `AnimationTypes.get_export_name("damage_fire") == "DamageFire"`
- `AnimationTypes.get_export_name("damage_ice") == "DamageIce"`
- `AnimationTypes.get_export_name("stunned") == "Stunned"`
- `AnimationTypes.get_export_name("celebrate") == "Celebrate"`
- `AnimationTypes.get_export_name("taunt") == "Taunt"`
Each verified independently.

**BAE-2.4 — Fallback for unknown internal names:**
`AnimationTypes.get_export_name("some_new_anim") == "SomeNewAnim"` (mechanical PascalCase
conversion: split on `_`, title-case each word, join without separator). Verified by unit test
with at least one synthetic unknown name.

**BAE-2.5 — Existing class constants unchanged:**
`AnimationTypes.IDLE == "idle"`, `AnimationTypes.MOVE == "move"`,
`AnimationTypes.DAMAGE == "damage"`, `AnimationTypes.DEATH == "death"`.
None of the existing string constants are modified. Verified by unit test.

**BAE-2.6 — Action names in `create_all_animations` use export names:**
In `animation_system.py`, the call `bpy.data.actions.new(name=...)` uses the return value
of `AnimationTypes.get_export_name(anim_name)` as the `name` argument, not `anim_name`
directly. Verified by reading the source: there is no `bpy.data.actions.new(name=anim_name)`
call remaining after the change.

**BAE-2.7 — `AnimationConfig.get_length` lookups remain on internal names:**
The internal `anim_name` loop variable (e.g. `"idle"`, `"move"`) continues to be passed to
`AnimationConfig.get_length(anim_name)`. No call to `get_length` passes an export name.
Verified by reading source: `get_length` receives the loop variable before export-name
translation is applied.

**BAE-2.8 — Python pytest exits 0 after both changes:**
`cd asset_generation/python && python -m pytest tests/ -q` exits 0 with all existing tests
passing. The new `get_export_name` tests (written by Test Designer) also pass.

### 3. Risk & Ambiguity Analysis

**Risk R2.1 — `AnimationConfig.get_length` key collision:**
`AnimationConfig.LENGTHS` uses the internal name string `"idle"`, `"move"`, etc. as keys.
If an implementer accidentally renames these keys to export names (`"Idle"`, `"Walk"`, etc.),
`get_length("idle")` will return the default `24` instead of the configured value, silently
producing wrong frame counts. The spec explicitly prohibits modifying `LENGTHS` keys.

**Risk R2.2 — Body type dispatch in `create_all_animations` uses internal names:**
The `if anim_name == AnimationTypes.IDLE:` chain dispatches to the correct `body_type`
method using the loop variable. If the export name is substituted for the loop variable
before this chain runs, all branches fail (e.g. `"Idle" == AnimationTypes.IDLE` →
`"Idle" == "idle"` → `False`). The spec requires the export name translation to occur only
at the point of action naming, not earlier. The internal name must remain in scope for the
entire dispatch chain.

**Risk R2.3 — Existing test references to action names:**
No existing test in `tests/animations/` inspects action names directly (verified by reading
`test_attack_frames.py`). However, if a future test creates actions and checks their names,
it will find PascalCase names after this change. Test Designer should be aware that action
names are now export names, not internal names.

**Risk R2.4 — `get_export_name` callable without `bpy`:**
The method is defined on a pure-Python class (`AnimationTypes`) in `constants.py` which has
no `bpy` import. It must remain callable in the unit test environment (outside Blender) with
only the standard library. The implementation must not import `bpy` inside `get_export_name`.

### 4. Clarifying Questions

None. All ambiguities resolved via checkpoint assumptions above.

---

## Requirement BAE-3: Godot Test — AnimationPlayer Clip Presence (Task 4)

### 1. Spec Summary

**Description:**
A new GDScript test file at
`tests/scenes/enemies/test_enemy_animation_clips.gd` must verify, for each of the 4 target
enemy families, that the regenerated GLB at
`res://assets/enemies/generated_glb/<family>_animated_00.glb` loads as a PackedScene,
instantiates without error, contains an `AnimationPlayer` node, and that the `AnimationPlayer`
reports all 4 required clip names in `get_animation_list()`.

**Constraints:**
- The file must extend `"res://tests/utils/test_utils.gd"` (same pattern as
  `test_enemy_scene_generation.gd`).
- Class-level constants must name the 4 families and the 4 required clip names.
- The `AnimationPlayer` must be found by type search (`find_children("*", "AnimationPlayer",
  true, false)` or equivalent), not by hardcoded node path, because the GLB scene hierarchy
  is generated by Blender and may vary.
- If a GLB file does not exist, the test for that family must print a `SKIP` diagnostic and
  not increment the fail count. The test suite must not crash.
- Test IDs run from `BAE-01` through `BAE-16`: 4 asserts per family, 4 families.
  - BAE-01..04: `adhesion_bug`
  - BAE-05..08: `acid_spitter`
  - BAE-09..12: `claw_crawler`
  - BAE-13..16: `carapace_husk`
- `run_all()` must return the fail count as an `int`.

**Assumptions:**
- GLBs are located at `res://assets/enemies/generated_glb/<family>_animated_00.glb`. This
  path mirrors the output of `export_enemy()` with `export_dir` pointing to
  `assets/enemies/generated_glb/` (verified against the existing 12 GLBs listed in
  `test_enemy_scene_generation.gd`'s `GENERATED_BASENAMES` constant).
- Godot 4.x `AnimationPlayer.get_animation_list()` returns an `Array[StringName]`. The
  `in` operator works for membership checks against this array.
- The test runs in headless mode without a SceneTree root; `PackedScene.instantiate()` is
  used and the returned node is freed after assertion.

**Scope:**
- New file: `tests/scenes/enemies/test_enemy_animation_clips.gd`
- `tests/run_tests.gd` must be updated to include the new test (Task 5, not this requirement,
  but the Test Designer must produce the new test file ready to be wired in).

### 2. Acceptance Criteria

**BAE-3.1 — File parses in Godot headless mode without error:**
`timeout 300 godot -s tests/run_tests.gd` exits without a GDScript parse error referencing
`test_enemy_animation_clips.gd`.

**BAE-3.2 — AnimationPlayer found for each family:**
For each of the 4 families, if the GLB exists, the test finds at least one node of type
`AnimationPlayer` in the instantiated scene tree. Failure prints `FAIL [BAE-0N]: AnimationPlayer
null for <family>`.

**BAE-3.3 — All 4 required clip names present:**
For each family, the following 4 assertions pass independently:
- `"Idle"` is in `animation_player.get_animation_list()`
- `"Walk"` is in `animation_player.get_animation_list()`
- `"Hit"` is in `animation_player.get_animation_list()`
- `"Death"` is in `animation_player.get_animation_list()`

**BAE-3.4 — Missing GLB produces SKIP, not FAIL:**
If `ResourceLoader.exists("res://assets/enemies/generated_glb/<family>_animated_00.glb")`
returns `false`, the test prints `SKIP [BAE-NN..NN]: <family> GLB not found` and does not
call `_fail()`. The fail count for the run is unaffected.

**BAE-3.5 — run_all() return value:**
`run_all()` returns an `int` equal to the number of `_fail()` calls made during the run.
A fully passing run (all 4 GLBs present and correct) returns `0`.

**BAE-3.6 — Test IDs are correct and sequential:**
The 16 test IDs `BAE-01` through `BAE-16` appear in the test output in order, with families
in the order: `adhesion_bug`, `acid_spitter`, `claw_crawler`, `carapace_husk`.

### 3. Risk & Ambiguity Analysis

**Risk R3.1 — `find_children` signature in Godot 4.x:**
`Node.find_children(pattern, type, recursive, owned)` is the correct Godot 4 signature.
The `type` argument must be the exact string `"AnimationPlayer"`. If the GLB scene root is
not a Node (e.g., if it is a MeshInstance3D), `find_children` must be called on the
instantiated root, not cast to a specific type first.

**Risk R3.2 — GLB AnimationPlayer path depth:**
Blender-exported GLBs typically embed the AnimationPlayer as a sibling or child of the
armature node, not always at the scene root. The recursive search (`true` for recursive)
handles this.

**Risk R3.3 — `get_animation_list()` vs `has_animation()`:**
Either `"Idle" in animation_player.get_animation_list()` or
`animation_player.has_animation("Idle")` is acceptable. `has_animation` is preferred for
clarity. The spec accepts either form.

**Risk R3.4 — StringName vs String comparison:**
`get_animation_list()` returns `PackedStringArray` in Godot 4.x (not `Array[StringName]`).
`"Idle" in packed_string_array` works correctly in GDScript. No casting is required.

### 4. Clarifying Questions

None. All ambiguities resolved via checkpoint assumptions above.

---

## Requirement BAE-4: Test Runner Integration and Full Suite Pass (Task 5)

### 1. Spec Summary

**Description:**
`tests/run_tests.gd` must be updated to instantiate and run
`test_enemy_animation_clips.gd`. The full test suite (`run_tests.sh`) must exit 0 with all
BAE-01 through BAE-16 reporting PASS.

**Constraints:**
- The test class is added to `run_tests.gd` following the same pattern used for
  `test_enemy_scene_generation.gd` (load the script, instantiate, call `run_all()`,
  accumulate fail count).
- No existing tests may be removed or skipped.
- The addition must not change the exit behavior for any previously passing test.

**Scope:**
- `tests/run_tests.gd`

### 2. Acceptance Criteria

**BAE-4.1 — test_enemy_animation_clips is listed in run_tests.gd:**
The string `"test_enemy_animation_clips"` (or the full res:// path) appears in
`run_tests.gd`.

**BAE-4.2 — run_tests.sh exits 0:**
`cd /Users/jacobbrandt/workspace/blobert && run_tests.sh` exits with code 0.

**BAE-4.3 — BAE tests pass in output:**
The output of `run_tests.sh` contains `PASS: BAE-01` through `PASS: BAE-16`.

**BAE-4.4 — No pre-existing test regressions:**
No test that previously reported PASS reports FAIL after this change.

### 3. Risk & Ambiguity Analysis

**Risk R4.1 — GLBs must exist before tests are run:**
BAE-4.2 and BAE-4.3 require that the regenerated GLBs from Task 3 are already present in
`assets/enemies/generated_glb/`. This is a sequencing dependency: Task 3 must be complete
before Task 5 can pass. If Task 5 runs before Task 3, all 16 BAE tests will SKIP (not FAIL),
and `run_tests.sh` may still exit 0, but BAE-4.3 cannot be satisfied.

### 4. Clarifying Questions

None.

---

## Non-Functional Requirements

### NFR-1 — No regressions in existing Python pytest suite
All tests under `asset_generation/python/tests/` continue to pass after Tasks 1 and 2.
The bpy-mocked test infrastructure (`sys.modules.setdefault('bpy', MagicMock())`) is
unaffected by the new NLA and naming logic, because those are Blender API calls that run
only inside Blender.

### NFR-2 — All export names are deterministic for a given input
`AnimationTypes.get_export_name(name)` must return the same string for the same `name` on
every call (pure function, no global state). The fallback PascalCase conversion must be
deterministic.

### NFR-3 — GLB file sizes increase after NLA wiring
Each regenerated GLB must be materially larger than its pre-animation predecessor (rough
indicator: at minimum 2x the pre-animation file size for the same variant). This is a
sanity check that animation data was embedded, not a hard threshold.

### NFR-4 — Blender exits 0 for all 4 family regeneration runs
`blender --background --python src/generator.py -- <family> 3` must exit with return code
0 for each of the 4 target families. Any non-zero exit code indicates a pipeline error that
must be resolved before handoff to the Godot test step.

---

## Full Export Name Mapping Reference

Authoritative table for all 13 internal animation names and their required GLB export names.
This table is the single source of truth for the `get_export_name` implementation.

| Internal name    | Export name      | Required for Godot controller |
|-----------------|-----------------|-------------------------------|
| `idle`          | `Idle`          | Yes                           |
| `move`          | `Walk`          | Yes                           |
| `attack`        | `Attack`        | No (extra clip)               |
| `damage`        | `Hit`           | Yes                           |
| `death`         | `Death`         | Yes                           |
| `spawn`         | `Spawn`         | No                            |
| `special_attack`| `SpecialAttack` | No                            |
| `damage_heavy`  | `DamageHeavy`   | No                            |
| `damage_fire`   | `DamageFire`    | No                            |
| `damage_ice`    | `DamageIce`     | No                            |
| `stunned`       | `Stunned`       | No                            |
| `celebrate`     | `Celebrate`     | No                            |
| `taunt`         | `Taunt`         | No                            |

---

## NLA Wiring Implementation Pattern (Reference, not code)

The following pseudo-code describes the required structural pattern for the NLA wiring
block that must be added to `create_all_animations()` after the action-creation loop.
This is for the Test Designer and Implementer to reference; the exact Blender API calls
are prescribed by the acceptance criteria above.

```
# After all actions created and keyframed:
# 1. Return to OBJECT mode
switch armature to OBJECT mode

# 2. Wire each action into its own NLA track
for each action in created_actions:
    new_track = armature.animation_data.nla_tracks.new()
    new_strip = new_track.strips.new(action.name, 0, action)
    new_strip.action_frame_start = 1
    new_strip.action_frame_end = action.frame_range[1]

# 3. Set NLA-driven mode (no active action)
armature.animation_data.action = None
```

And for `export_enemy()` in `base_enemy.py`, the GLTF export call must include:
```
export_nla_strips=True  # required for Blender 3.6; omit or detect on 4.x
```

---

## Spec Traceability

| Spec ID   | Task | File(s) changed                                         |
|-----------|------|---------------------------------------------------------|
| BAE-1.1   | 1    | `animation_system.py`                                   |
| BAE-1.2   | 1    | `animation_system.py`                                   |
| BAE-1.3   | 1    | `animation_system.py`                                   |
| BAE-1.4   | 1    | `animation_system.py`                                   |
| BAE-1.5   | 1    | `base_enemy.py`                                         |
| BAE-1.6   | 1    | (no test file change; regression guard)                 |
| BAE-1.7   | 1    | `animation_system.py`                                   |
| BAE-2.1   | 2    | `constants.py`                                          |
| BAE-2.2   | 2    | `constants.py`                                          |
| BAE-2.3   | 2    | `constants.py`                                          |
| BAE-2.4   | 2    | `constants.py`                                          |
| BAE-2.5   | 2    | `constants.py` (nothing changes, verified unchanged)    |
| BAE-2.6   | 2    | `animation_system.py`                                   |
| BAE-2.7   | 2    | `animation_system.py` (nothing changes, verified)       |
| BAE-2.8   | 2    | (no test file change; regression guard)                 |
| BAE-3.1   | 4    | `test_enemy_animation_clips.gd`                         |
| BAE-3.2   | 4    | `test_enemy_animation_clips.gd`                         |
| BAE-3.3   | 4    | `test_enemy_animation_clips.gd`                         |
| BAE-3.4   | 4    | `test_enemy_animation_clips.gd`                         |
| BAE-3.5   | 4    | `test_enemy_animation_clips.gd`                         |
| BAE-3.6   | 4    | `test_enemy_animation_clips.gd`                         |
| BAE-4.1   | 5    | `run_tests.gd`                                          |
| BAE-4.2   | 5    | `run_tests.gd`                                          |
| BAE-4.3   | 5    | `run_tests.gd` + GLBs from Task 3                       |
| BAE-4.4   | 5    | (no test file change; regression guard)                 |
