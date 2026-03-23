Title:
Build Blender primitive parts library
---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | TEST_BREAK |
| Revision | 5 |
| Last Updated By | Test Designer Agent |
| Next Responsible Agent | Test Breaker Agent |
| Validation Status | Not started |
| Blocking Issues | None |

---


Description:
Create enemy_parts.blend with the core reusable mesh components: BaseBlob, BaseSphere,
BaseCapsule, EyeNode, Spike, Claw, Shell, Tentacle, Wing, OrbCore, Blade.
Each piece should be extremely simple (under 100 triangles). Organized in a Parts collection.

Acceptance Criteria:
- All parts exist in a single enemy_parts.blend file
- Each part is under 100 triangles
- Parts are logically named and organized in a Blender collection
- File is committed to assets/enemies/parts/

---

## Execution Plan

### Task 1 — Write Blender Python generation script
**Assigned Agent:** Core Simulation Agent
**Input:** This ticket; existing blender_utils conventions in `asset_generation/python/src/core/blender_utils.py`
**Expected Output:** `/Users/jacobbrandt/workspace/blobert/asset_generation/python/src/enemies/build_parts_library.py` — a self-contained Blender Python script executable via `blender --background --python <script>` that:
  - Clears the default Blender scene
  - Creates a Collection named "Parts"
  - Creates 11 named mesh objects inside that collection: BaseBlob, BaseSphere, BaseCapsule, EyeNode, Spike, Claw, Shell, Tentacle, Wing, OrbCore, Blade
  - Each mesh uses low-poly primitives (icosphere, UV sphere, cylinder, cone, torus, plane, cube) with subdivision levels chosen so triangle count stays under 100
  - Saves the result as `assets/enemies/parts/enemy_parts.blend` (path computed relative to the script file so it resolves correctly from any working directory)
  - Prints a summary line per part: `[BPL] <name>: <triangle_count> triangles` and a final `[BPL] Done: enemy_parts.blend`
**Dependencies:** None
**Success Criteria:** Script runs without error when invoked as `blender --background --python asset_generation/python/src/enemies/build_parts_library.py`; output .blend file is created; all 11 summary lines appear in stdout.

---

### Task 2 — Write pure-Python tests for the generation script (no Blender required)
**Assigned Agent:** Test Designer Agent
**Input:** Task 1 output (the script file); pytest conventions from `asset_generation/python/tests/`
**Expected Output:** `/Users/jacobbrandt/workspace/blobert/asset_generation/python/tests/enemies/test_build_parts_library.py` — pytest test file (no `bpy` import) with test classes:
  - `TestScriptExists` — asserts the script file exists at its expected path
  - `TestOutputPathConstant` — imports the OUTPUT_PATH constant (or equivalent) from the script and asserts it ends with `assets/enemies/parts/enemy_parts.blend`
  - `TestPartNamesConstant` — imports the PART_NAMES list and asserts it contains all 11 expected names in any order
  - `TestTriangleBudgetConstants` — asserts MAX_TRIANGLES_PER_PART constant equals 100
  - Note: Tests that require `bpy` (Blender's Python API) are explicitly excluded from this file; those belong in the Blender-invocation integration test (Task 4)
**Dependencies:** Task 1 (script must exist and expose importable constants)
**Success Criteria:** `python -m pytest asset_generation/python/tests/enemies/test_build_parts_library.py -v` passes with no failures and no bpy import errors.

---

### Task 3 — Create output directory and run the script headlessly
**Assigned Agent:** Core Simulation Agent
**Input:** Task 1 script; `asset_generation/python/bin/find_blender.py` for Blender path resolution
**Expected Output:**
  - Directory `assets/enemies/parts/` created (with a `.gitkeep` if empty before the script runs, removed after)
  - File `assets/enemies/parts/enemy_parts.blend` present on disk
  - Console output captured confirming all 11 `[BPL] <name>: <N> triangles` lines appeared and all N < 100
**Execution command:** `blender --background --python /Users/jacobbrandt/workspace/blobert/asset_generation/python/src/enemies/build_parts_library.py`
**Dependencies:** Task 1
**Success Criteria:** `.blend` file exists and is non-zero bytes; no `Error` or `Traceback` in stdout/stderr from Blender; all 11 part summary lines are present.

---

### Task 4 — Write Blender-invocation integration test
**Assigned Agent:** Test Designer Agent
**Input:** Task 1 script path; Task 3 output `.blend` file path; `asset_generation/python/bin/find_blender.py`
**Expected Output:** `/Users/jacobbrandt/workspace/blobert/asset_generation/python/tests/enemies/test_parts_library_integration.py` — pytest test file with:
  - `TestBlendFileExists` — asserts `assets/enemies/parts/enemy_parts.blend` exists and size > 0
  - `TestBlenderInvocationSucceeds` — calls `blender --background --python <script>` via subprocess; asserts returncode == 0
  - `TestPartSummaryLinesInOutput` — parses stdout for all 11 `[BPL] <name>:` lines; asserts each is present and the triangle count < 100
  - `TestPartsCollectionVerification` — calls a separate Blender verification script (inline via `--python-expr` or temp file) that opens `enemy_parts.blend`, checks the "Parts" collection exists, counts its objects, asserts count == 11, asserts all 11 expected names are present; asserts all mesh triangle counts < 100
  - All subprocess calls must use a timeout of 120 seconds
  - Test is marked `@pytest.mark.integration` so pure-Python CI can skip it
**Dependencies:** Tasks 1, 2, 3
**Success Criteria:** `python -m pytest asset_generation/python/tests/enemies/test_parts_library_integration.py -v -m integration` passes with all assertions green.

---

### Task 5 — Commit output and update ticket
**Assigned Agent:** Core Simulation Agent
**Input:** Tasks 1–4 outputs
**Expected Output:**
  - All new files committed: script, tests, `.blend` file, `assets/enemies/parts/` directory
  - Commit message: `feat: build_parts_library script + enemy_parts.blend (11 mesh primitives)`
  - Ticket advanced per workflow: Stage → next appropriate stage after Spec Agent processes it
**Dependencies:** Tasks 1–4
**Success Criteria:** `git log --oneline -1` shows the commit; `git status` shows clean working tree; ticket WORKFLOW STATE updated.

---

## Spec Reference

Full functional and non-functional specification:
`project_board/5_milestone_5_procedural_enemy_generation/backlog/spec_build_parts_library.md`

### Key Constants (normative)

| Constant | Value |
|---|---|
| `OUTPUT_PATH` | `Path(__file__).resolve().parents[4] / "assets/enemies/parts/enemy_parts.blend"` |
| `MAX_TRIANGLES_PER_PART` | `100` (int) |
| `PART_NAMES` | See table below |

### Canonical PART_NAMES (in order)

```python
PART_NAMES = [
    "BaseBlob",
    "BaseSphere",
    "BaseCapsule",
    "EyeNode",
    "Spike",
    "Claw",
    "Shell",
    "Tentacle",
    "Wing",
    "OrbCore",
    "Blade",
]
```

### Primitive Call Table (normative)

| Part Name | Primitive Call | Expected Triangle Count |
|---|---|---|
| `BaseBlob` | `primitive_uv_sphere_add(segments=8, ring_count=4)` | 64 |
| `BaseSphere` | `primitive_ico_sphere_add(subdivisions=1)` | 80 |
| `BaseCapsule` | `primitive_cylinder_add(vertices=8, depth=2.0)` | 32 |
| `EyeNode` | `primitive_uv_sphere_add(segments=6, ring_count=3)` | 36 |
| `Spike` | `primitive_cone_add(vertices=8, depth=2.0)` | 16 |
| `Claw` | `primitive_cone_add(vertices=6, depth=1.5)` | 12 |
| `Shell` | `primitive_torus_add(major_segments=8, minor_segments=4)` | 64 |
| `Tentacle` | `primitive_cylinder_add(vertices=6, depth=3.0)` | 24 |
| `Wing` | `primitive_plane_add(size=2.0)` | 2 |
| `OrbCore` | `primitive_ico_sphere_add(subdivisions=1)` | 80 |
| `Blade` | `primitive_cube_add(size=1.0)` | 12 |

All counts strictly < 100. Maximum count: 80 triangles (BaseSphere, OrbCore).

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input Schema
```json
{
  "ticket_path": "string — absolute path to this ticket file",
  "spec_path": "string — absolute path to spec_build_parts_library.md",
  "script_output_path": "string — asset_generation/python/src/enemies/build_parts_library.py",
  "pure_python_test_path": "string — asset_generation/python/tests/enemies/test_build_parts_library.py",
  "integration_test_path": "string — asset_generation/python/tests/enemies/test_parts_library_integration.py",
  "blend_output_path": "string — assets/enemies/parts/enemy_parts.blend",
  "part_names": ["BaseBlob","BaseSphere","BaseCapsule","EyeNode","Spike","Claw","Shell","Tentacle","Wing","OrbCore","Blade"],
  "max_triangles": 100
}
```

## Status
Proceed

## Reason
Tests authored by Test Designer Agent. Both test files are in place:
- `asset_generation/python/tests/enemies/test_build_parts_library.py` — 18 pure-Python pytest tests across TestScriptExists, TestOutputPathConstant, TestPartNamesConstant, TestTriangleBudgetConstants. Currently RED (build_parts_library.py does not exist).
- `asset_generation/python/tests/enemies/test_parts_library_integration.py` — 15 integration tests marked @pytest.mark.integration across TestBlendFileExists, TestBlenderInvocationSucceeds, TestPartSummaryLinesInOutput, TestPartsCollectionVerification. Currently RED (blend file and script do not exist).
Test Breaker Agent should verify tests are RED, then hand off to Core Simulation Agent for Tasks 1, 3, 5 (implementation).
