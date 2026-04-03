# TICKET: blender_animation_export

Title: Update Blender pipeline to export named animation clips per family

## Description

The existing Blender Python pipeline (`asset_generation/python/`) exports static GLBs. Update it to bake and export named NLA animation clips — Idle, Walk, Hit, Death — for each enemy family. Each clip must be named consistently so Godot's AnimationPlayer can reference them by name without per-file configuration.

## Acceptance Criteria

- Blender script exports at minimum 4 named clips per GLB: `Idle`, `Walk`, `Hit`, `Death`
- Clip names are consistent across all 4 families (same string names)
- GLBs load in Godot without import errors
- AnimationPlayer node is present on the imported scene root and contains all 4 clips
- Existing GLBs in `assets/enemies/generated_glb/` are regenerated with animation data
- `run_tests.sh` exits 0 (no regressions from reimport)

## Dependencies

- M5 (Blender pipeline and parts library) must be complete — it is

---

## Execution Plan

### Task 1 — Update `animation_system.py`: push all actions into NLA strips

**Agent:** Generalist Agent
**Input:** `/Users/jacobbrandt/workspace/blobert/asset_generation/python/src/animations/animation_system.py`
**Expected Output:** Modified `animation_system.py` where `create_all_animations()` pushes every created action into an NLA track on the armature, then sets the armature back to NLA-driven mode (no active action override) before returning. The GLTF exporter must see all NLA tracks.
**Dependencies:** None
**Success Criteria:**
- Each action created by the loop is pushed to a new NLA strip via `armature.animation_data.nla_tracks.new()` / `track.strips.new()`
- After loop, `armature.animation_data.action = None` (NLA drives export, not a single active action)
- Existing unit tests in `asset_generation/python/tests/animations/` pass
- Existing Python test suite (`cd asset_generation/python && python -m pytest tests/ -q`) exits 0
**Risks:** Blender's NLA API may require the scene to be in OBJECT mode; must ensure mode is set correctly before creating strips.

---

### Task 2 — Update `constants.py` and `animation_system.py`: map internal names to PascalCase export names

**Agent:** Generalist Agent
**Input:**
- `/Users/jacobbrandt/workspace/blobert/asset_generation/python/src/utils/constants.py`
- `/Users/jacobbrandt/workspace/blobert/asset_generation/python/src/animations/animation_system.py`
**Expected Output:**
- A mapping in `AnimationTypes` or `AnimationConfig` from internal name → export name: `idle`→`Idle`, `move`→`Walk`, `damage`→`Hit`, `death`→`Death`, `attack`→`Attack` (remaining clips use title-cased internal name as fallback)
- `create_all_animations()` names each created action using the export name (not the internal name)
- The NLA strip name also uses the export name
**Dependencies:** Task 1 (NLA wiring must already exist to know the strip-naming API)
**Success Criteria:**
- `AnimationTypes.get_export_name("idle") == "Idle"` (or equivalent dict lookup)
- `AnimationTypes.get_export_name("move") == "Walk"`
- `AnimationTypes.get_export_name("damage") == "Hit"`
- `AnimationTypes.get_export_name("death") == "Death"`
- Python pytest exits 0

---

### Task 3 — Regenerate all 4 enemy family GLBs with animation data

**Agent:** Generalist Agent
**Input:**
- Updated pipeline from Tasks 1 and 2
- `/Users/jacobbrandt/workspace/blobert/asset_generation/python/main.py` (entry point)
- Blender binary available on PATH via `direnv` as `bin/godot` wrapper equivalent (`blender`)
**Expected Output:**
- 12 regenerated GLBs (3 variants × 4 families) in `/Users/jacobbrandt/workspace/blobert/assets/enemies/generated_glb/`: `adhesion_bug_animated_00..02.glb`, `acid_spitter_animated_00..02.glb`, `claw_crawler_animated_00..02.glb`, `carapace_husk_animated_00..02.glb`
- Each GLB file size is materially larger than the pre-animation version (rough indicator of embedded animation data)
- Blender exits 0 for each run
**Command to run:** `cd /Users/jacobbrandt/workspace/blobert/asset_generation/python && python main.py animated all --count 3` (or family-by-family if `all` does not include the 4 target families; check `EnemyTypes.get_animated()`)
**Dependencies:** Tasks 1 and 2 complete
**Success Criteria:**
- All 12 GLB files exist in `assets/enemies/generated_glb/`
- No Blender error lines in stdout/stderr

---

### Task 4 — Write Godot headless test: AnimationPlayer clip presence

**Agent:** Test Design Agent
**Input:**
- `/Users/jacobbrandt/workspace/blobert/tests/scenes/enemies/test_enemy_scene_generation.gd` (reference pattern)
- `/Users/jacobbrandt/workspace/blobert/tests/utils/test_utils.gd`
- Regenerated GLBs from Task 3
**Expected Output:**
- New GDScript test file at `/Users/jacobbrandt/workspace/blobert/tests/scenes/enemies/test_enemy_animation_clips.gd`
- Class `EnemyAnimationClipsTests extends "res://tests/utils/test_utils.gd"`
- For each of the 4 families (adhesion_bug, acid_spitter, claw_crawler, carapace_husk), the test:
  1. Loads `res://assets/enemies/generated_glb/<family>_animated_00.glb` as a PackedScene
  2. Instantiates the scene
  3. Finds the `AnimationPlayer` node (search by type, not hardcoded path)
  4. Asserts `AnimationPlayer != null`
  5. Asserts `"Idle"` is in `animation_player.get_animation_list()`
  6. Asserts `"Walk"` is in `animation_player.get_animation_list()`
  7. Asserts `"Hit"` is in `animation_player.get_animation_list()`
  8. Asserts `"Death"` is in `animation_player.get_animation_list()`
- Test IDs: `BAE-01` through `BAE-16` (4 asserts × 4 families; BAE-01..04 = adhesion_bug, etc.)
- `run_all()` method returns fail count
**Dependencies:** Task 3 (GLBs must exist with animation data); Task 1 and 2 define expected clip names
**Success Criteria:**
- File parses in Godot headless mode without error
- Test degrades gracefully if a GLB is missing (skip + diagnostic, not crash)

---

### Task 5 — Wire new test into test runner and verify full suite passes

**Agent:** Generalist Agent
**Input:**
- `/Users/jacobbrandt/workspace/blobert/tests/run_tests.gd`
- `/Users/jacobbrandt/workspace/blobert/tests/scenes/enemies/test_enemy_animation_clips.gd` (from Task 4)
- Regenerated GLBs from Task 3
**Expected Output:**
- `run_tests.gd` includes the new test class
- `run_tests.sh` exits 0
- All existing tests continue to pass
- New BAE tests pass (AnimationPlayer present, all 4 clip names present)
**Command:** `cd /Users/jacobbrandt/workspace/blobert && run_tests.sh`
**Dependencies:** Tasks 3 and 4 complete
**Success Criteria:**
- Exit code 0 from `run_tests.sh`
- BAE-01 through BAE-16 all report PASS in output

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | COMPLETE |
| Revision | 6 |
| Last Updated By | Engine Integration Agent |
| Next Responsible Agent | — |
| Status | COMPLETE |
| Validation Status | All AC met |
| Blocking Issues | — |

## OUTCOME

Implementation complete. All acceptance criteria met:
- 12 GLBs regenerated with 13 named animation clips each (Idle, Walk, Hit, Death + 9 extended)
- Clip names consistent across all 4 families
- All BAE-01..BAE-16 GDScript tests PASS
- All ADV-BAE-G-01..ADV-BAE-G-10 adversarial GDScript tests PASS
- All 329 Python tests PASS (70 animation export specific)
- `run_tests.sh` exits 0

## PREVIOUS NEXT ACTION NOTE

**Python adversarial suite** (30 tests, `asset_generation/python/tests/utils/test_animation_export_names_adversarial.py`):
- 6 pass (check invariants already true in unmodified code: export_animations=True, export_format=GLB, None-input safety, source contains `action=None`)
- 24 fail red (require implementation of Tasks 1 and 2)

**Primary Python suite** (`test_animation_export_names.py`, 40 tests):
- 8 pass, 32 fail red (unchanged from Test Designer handoff)

**GDScript adversarial suite** (new file `tests/scenes/enemies/test_enemy_animation_clips_adversarial.gd`):
- All tests SKIP until Task 3 GLBs are regenerated

**GDScript primary suite** (`test_enemy_animation_clips.gd`, BAE-01..BAE-16):
- All SKIP until Task 3 GLBs are regenerated

**Coverage gaps exposed by adversarial suite (will FAIL after implementation if incorrectly done):**
- `get_export_name` fallback edge cases: empty string, all-underscore, numeric, consecutive underscores, leading/trailing underscores, ALL_CAPS input, naive-title-case-of-whole-string trap
- Return type exactness: `type(result) is str` (not MagicMock subclass)
- Mutation targets: `"move"` → `"Walk"` (not `"Move"`); `"damage"` → `"Hit"` (not `"Damage"`)
- NLA strip `name` attribute must equal export name (not internal name)
- NLA wiring for `animation_set='extended'` set (8 tracks, not 5 or 13)
- Active-action leak: source must not contain `animation_data.action = created_actions[0]`
- `export_nla_strips=True` in `bpy.ops.export_scene.gltf()` (bmesh mock fixed in adversarial file)
- No map mutation: required mappings stable after unknown-name lookups
- Partial export guard: all 4 GLB families present
- Duplicate AnimationPlayer detection
- Lowercase/wrong-case clip names absent from GLB
- Title-case-fallback trap clips absent ("Move", "Damage")
- Clip names do not carry family-name prefix
