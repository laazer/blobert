# TICKET: MAINT-20260328-test-utility-consolidation
Title: Consolidate repeated test utility code across test suite
Project: blobert
Created By: Human
Created On: 2026-03-28T00:00:00Z

---

## Description

60 test files each define their own `_pass`, `_fail`, and `_assert_*` helper functions. This is duplicated boilerplate repeated in every test file. The goal is to extract a shared `TestBase` or `TestRunner` utility that all tests extend or load, eliminating the repetition and making future test authoring faster and more consistent.

Additionally, perform a broader DRY audit across the codebase (not just tests) to identify any other patterns of significant repetition that should be consolidated.

Scope:
- Primary focus: test utility helpers (`_pass`, `_fail`, `_assert_true`, `_assert_eq`, etc.)
- Secondary: any other repeated patterns found in tests (scene loading boilerplate, common setup/teardown)
- Stretch: brief DRY scan of `scripts/` for repeated non-test patterns

Constraints:
- All existing tests must continue to pass after refactoring
- No changes to test logic or assertions — only the utility infrastructure
- Must remain compatible with the headless `run_tests.gd` auto-discovery runner

---

## Acceptance Criteria

- [ ] A shared test utility script exists under `tests/` (e.g. `tests/test_base.gd`) that provides the common `_pass`, `_fail`, and `_assert_*` helpers used across the suite.
- [ ] At least the majority of test files are updated to use the shared utility instead of defining their own copies (full migration preferred; partial migration acceptable if any files have meaningfully diverged helpers).
- [ ] All tests continue to pass after the refactoring (`run_tests.sh` exits 0, no new failures).
- [ ] A brief DRY audit note is added to this ticket's Validation Status documenting any other significant repetition found in `scripts/` or `tests/` (even if not fixed in this ticket).

---

## Dependencies

- None

---

## Execution Plan

### Project: Test Utility Consolidation — MAINT-20260328-test-utility-consolidation
**Description:** Extract shared `tests/test_base.gd` from 58 duplicated test helper blocks; migrate all test files; perform DRY audit of `scripts/`.

#### Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Produce specification for `test_base.gd` API and migration rules | Spec Agent | This ticket; CHECKPOINTS.md planning entries; 58 test files in `tests/`; `tests/run_tests.gd`; workflow_enforcement_v1.md | Spec doc at `agent_context/agents/2_spec/test_base_spec.md` covering: (a) exact method signatures for `_pass`, `_pass_test`, `_fail`, `_fail_test`, `_assert_true`, `_assert_false`, `_assert_eq_int`, `_assert_eq_string`, `_assert_approx`, `_assert_vec2_approx`, `_begin_suite`, `_end_suite`; (b) `_pass_count`/`_fail_count` ownership; (c) no `class_name` on `test_base.gd`; (d) `extends Object` on `test_base.gd`; (e) alias strategy for `_pass`/`_pass_test` dual naming; (f) migration rules for each file category; (g) exclusion list for files that need no migration; (h) DRY audit scope definition for `scripts/` | None | Spec doc exists; all named method signatures present; alias strategy documented; migration rules unambiguous | Risk: some test files use `_assert_approx` and `_assert_vec2_approx` which are not universal — spec must decide whether these are in base or stay local. Assumption: spec will include all helpers found in 3+ files |
| 2 | Author `tests/test_base.gd` and migrate all test files | Generalist Agent | Spec from Task 1; all 58 test files at `/Users/jacobbrandt/workspace/blobert/tests/`; `tests/run_tests.gd` (read-only); workflow_enforcement_v1.md | (a) New file `tests/test_base.gd` with all shared helpers; (b) all 58 test files with `extends Object` replaced by `extends "res://tests/test_base.gd"` and local helper blocks removed; (c) `run_tests.gd` unchanged | Task 1 | `tests/test_base.gd` exists; zero test files still define their own `_pass`/`_fail`/`_pass_test`/`_fail_test` functions (unless spec-excluded); `run_tests.sh` exits 0 | Risk: `test_base.gd` is auto-discovered by the runner because it starts with `test_`. Mitigation: rename to `test_base.gd` is fine since the runner calls `script.new().run_all()` and `test_base.gd` must NOT define `run_all()` — the runner will crash on it. Spec must explicitly address this. See risk note below. |
| 3 | Run test suite and verify no regressions | Generalist Agent | Modified repo from Task 2; `run_tests.sh` | Console output showing 0 new failures; exit code 0 | Task 2 | `run_tests.sh` exits 0; no test that previously passed now fails; output shows same or fewer total failures than pre-migration baseline | Risk: pre-existing failures (RSM-SIGNAL-1..6, ADV-RSM-02) must not be counted as regressions. Agent must establish pre-migration baseline first. |
| 4 | DRY audit of `scripts/` and update Validation Status | Generalist Agent | All files in `scripts/` at `/Users/jacobbrandt/workspace/blobert/scripts/`; this ticket file | Validation Status block in this ticket updated with a bullet-point DRY audit note identifying 2-5 high-value consolidation candidates in `scripts/` (pattern descriptions, file names, approximate line counts) | Task 3 | Validation Status contains a DRY audit note; note identifies at least one concrete candidate; note is factual (not speculative) | Risk: `scripts/` has 31 files — audit should be grep/pattern-level only, not a full structural rewrite |

#### CRITICAL Risk — auto-discovery of test_base.gd
The `run_tests.gd` runner discovers every file matching `test_*.gd` under `tests/` and calls `script.new().run_all()`. If `test_base.gd` does not define `run_all()`, the runner will `push_error` and quit with exit 1. Resolution options (Spec Agent must choose one):
- **Option A:** Name the shared utility `tests/test_utils.gd` (does not match `test_*.gd` pattern) — no runner change needed.
- **Option B:** Keep the name `tests/test_base.gd` and add a no-op `run_all() -> int: return 0` to it — runner discovers it harmlessly.
- **Option C:** Add `test_base.gd` to a subdirectory like `tests/_base/test_base.gd` — still matches the glob pattern, same issue as Option B.

Spec Agent must document the chosen option and confirm runner compatibility.

---

## Specification

### Requirement MAINT-TUC-1: Shared Test Utility File

#### 1. Spec Summary

**Description:** A single GDScript file at `tests/utils/test_utils.gd` provides all shared helper functions used across the test suite. Every migratable test file extends this file using `extends "res://tests/utils/test_utils.gd"` in place of `extends Object`. The file is discovered by `run_tests.gd` (because the runner recursively scans all subdirectories under `tests/` and matches `test_*.gd`) but is handled safely because it defines a no-op `run_all() -> int: return 0`. The runner will call `run_all()`, receive 0, and continue.

**Resolution of the auto-discovery naming conflict:** Option B variant — the file is named `tests/utils/test_utils.gd`. The name begins with `test_`, so the runner does discover it. The file defines `run_all() -> int: return 0` (no-op), so the runner adds 0 failures and proceeds. This choice preserves the name `test_utils.gd` (clearer than `test_base.gd` for a utility), requires no changes to `run_tests.gd`, and the no-op `run_all()` makes discovery harmless. The `tests/utils/` subdirectory is not special; the runner recurses into it normally.

**Constraints:**
- `tests/utils/test_utils.gd` MUST NOT declare a `class_name`. A `class_name` would pollute the global registry and could conflict with any existing test file that declares a `class_name` (the runner loads scripts by path, not by class name).
- `tests/utils/test_utils.gd` MUST use `extends Object` as its own base.
- `tests/utils/test_utils.gd` MUST define `run_all() -> int: return 0` to satisfy the runner.
- `tests/utils/test_utils.gd` MUST NOT define `_pass_count` or `_fail_count` as instance variables. These counters are test-suite-specific and must remain in each individual test file (see Requirement MAINT-TUC-3). The helpers `_pass` and `_pass_test` call into `_pass_count` which the subclass owns; GDScript will resolve them at runtime against the subclass instance.
- `run_tests.gd` MUST NOT be modified. It is the runner and is read-only for this ticket.

**Assumptions:**
- GDScript resolves `_pass_count` and `_fail_count` lookups against the instantiated subclass, so the base class helpers can reference those variables even though they are declared in the subclass. This is standard GDScript inheritance behavior (dynamic dispatch on instance variables).
- A file can declare `class_name SomeName` while also using `extends "res://tests/utils/test_utils.gd"`. Existing test files that declare `class_name` (e.g. `class_name MovementSimulationTests`) may keep their `class_name` after migration.

**Scope:** Applies to the new `tests/utils/test_utils.gd` file only.

#### 2. Acceptance Criteria

- AC-1.1: The file `tests/utils/test_utils.gd` exists.
- AC-1.2: The file begins with `extends Object`. No other `extends` clause is present.
- AC-1.3: The file does NOT contain a `class_name` declaration.
- AC-1.4: The file defines `func run_all() -> int: return 0`.
- AC-1.5: When `run_tests.gd` runs, `tests/utils/test_utils.gd` is discovered, `run_all()` returns 0, and the runner adds 0 failures from it.
- AC-1.6: All methods listed in Requirement MAINT-TUC-2 are present with the exact signatures specified.

#### 3. Risk & Ambiguity Analysis

- Risk: if the runner's `push_error` branch fires (script not loadable), the suite exits 1. `test_utils.gd` must parse cleanly. Any syntax error in it will crash the entire suite.
- Risk: if `_pass_count`/`_fail_count` are defined in the base, they would be shared state across all test instances that do not redeclare them — but since each test file creates a fresh instance (`script.new()`), shared base-class variables would be per-instance anyway. However, to stay unambiguous and consistent with the existing codebase convention, these counters remain in each individual test file and are NOT in `test_utils.gd`.
- Edge case: `test_utils.gd` is itself a `test_*.gd` file; after migration, its `run_all()` will be called by the runner. It must return 0 and print nothing, so it does not pollute the test output.

#### 4. Clarifying Questions

None. The discovery behavior of `run_tests.gd` is confirmed by reading the source (line 35: `entry.begins_with("test_") and entry.ends_with(".gd")`; line 56: `script.new().run_all()`).

---

### Requirement MAINT-TUC-2: Exact API of `test_utils.gd`

#### 1. Spec Summary

**Description:** `tests/utils/test_utils.gd` exposes the following methods. Method bodies are specified exactly; no alternate implementations are permitted. The Generalist Agent must copy these bodies verbatim.

All `_pass`/`_pass_test` and `_fail`/`_fail_test` methods print with the standard prefix format `"  PASS: " + name` and `"  FAIL: " + name + " — " + message` used across the existing suite.

**Threshold rule for inclusion:** A helper is included in `test_utils.gd` if it appears in 3 or more test files with an identical or near-identical body (same logic, same print format). Helpers appearing in fewer than 3 files, or with meaningfully divergent implementations, are excluded and remain local.

**Constraints:** All parameter names and types must be exactly as specified. Optional parameters use GDScript default argument syntax.

**Assumptions:** The `_approx_eq` private helper is an implementation detail used internally by `_assert_approx` and `_assert_vec2_approx`. It is included in `test_utils.gd` because those assertions depend on it and the same body appears identically in all files that define it. The tolerance constant `1e-4` is the canonical value used in all files that define `_approx_eq`.

**Scope:** Applies to the body of `tests/utils/test_utils.gd`.

#### 2. Acceptance Criteria — Method Signatures and Bodies

**Group A — Core pass/fail reporters (aliases for dual-naming convention)**

These four methods form two alias pairs. `_pass` and `_pass_test` are identical in behavior; `_fail` and `_fail_test` are identical in behavior. Both names exist so that files using either convention can migrate without changing call sites.

```
func _pass(test_name: String) -> void:
    _pass_count += 1
    print("  PASS: " + test_name)

func _pass_test(test_name: String) -> void:
    _pass_count += 1
    print("  PASS: " + test_name)

func _fail(test_name: String, message: String) -> void:
    _fail_count += 1
    print("  FAIL: " + test_name + " — " + message)

func _fail_test(test_name: String, message: String) -> void:
    _fail_count += 1
    print("  FAIL: " + test_name + " — " + message)
```

AC-2.1: `_pass(test_name)` increments `_pass_count` by 1 and prints `"  PASS: " + test_name`.
AC-2.2: `_pass_test(test_name)` has identical behavior to `_pass(test_name)`.
AC-2.3: `_fail(test_name, message)` increments `_fail_count` by 1 and prints `"  FAIL: " + test_name + " — " + message`.
AC-2.4: `_fail_test(test_name, message)` has identical behavior to `_fail(test_name, message)`.

**Group B — Boolean assertion helpers**

```
func _assert_true(condition: bool, test_name: String, fail_msg: String = "expected true, got false") -> void:
    if condition:
        _pass(test_name)
    else:
        _fail(test_name, fail_msg)

func _assert_false(condition: bool, test_name: String, fail_msg: String = "expected false, got true") -> void:
    if not condition:
        _pass(test_name)
    else:
        _fail(test_name, fail_msg)
```

AC-2.5: `_assert_true(true, name)` calls `_pass(name)`. `_assert_true(false, name)` calls `_fail(name, "expected true, got false")`.
AC-2.6: `_assert_true(false, name, "custom msg")` calls `_fail(name, "custom msg")`.
AC-2.7: `_assert_false(false, name)` calls `_pass(name)`. `_assert_false(true, name)` calls `_fail(name, "expected false, got true")`.
AC-2.8: `_assert_false(true, name, "custom msg")` calls `_fail(name, "custom msg")`.

Note on `fail_msg` parameter: The majority of the codebase (files under `tests/levels/`, `tests/rooms/`) uses `_assert_true` with an optional third argument. The minority (files under `tests/scripts/`, `tests/chunk/`, etc.) uses only two arguments. Adding `fail_msg` with a default value is backward-compatible: two-argument call sites continue to work unchanged, and three-argument call sites (which require migration from `_pass_test`/`_fail_test` callers) also work.

**Group C — Typed equality helpers**

```
func _assert_eq_int(expected: int, actual: int, test_name: String) -> void:
    if actual == expected:
        _pass(test_name)
    else:
        _fail(test_name, "expected " + str(expected) + ", got " + str(actual))

func _assert_eq_string(expected: String, actual: String, test_name: String) -> void:
    if actual == expected:
        _pass(test_name)
    else:
        _fail(test_name, "expected '" + expected + "', got '" + actual + "'")

func _assert_eq_float(expected: float, actual: float, test_name: String) -> void:
    if absf(actual - expected) < 0.0001:
        _pass(test_name)
    else:
        _fail(test_name, "expected " + str(expected) + ", got " + str(actual))

func _assert_eq(expected: Variant, actual: Variant, test_name: String) -> void:
    if actual == expected:
        _pass(test_name)
    else:
        _fail(test_name, "expected " + str(expected) + ", got " + str(actual))

func _assert_eq_str(actual: String, expected: String, test_name: String) -> void:
    if actual == expected:
        _pass(test_name)
    else:
        _fail(test_name, "expected \"" + expected + "\", got \"" + actual + "\"")
```

AC-2.9: `_assert_eq_int` parameter order is `(expected: int, actual: int, test_name: String)`. Fail message format: `"expected " + str(expected) + ", got " + str(actual)`.
AC-2.10: `_assert_eq_string` parameter order is `(expected: String, actual: String, test_name: String)`. Fail message format uses single-quote delimiters: `"expected '" + expected + "', got '" + actual + "'"`.
AC-2.11: `_assert_eq_float` parameter order is `(expected: float, actual: float, test_name: String)`. Tolerance is exactly `0.0001` (same as `absf(actual - expected) < 0.0001`). This matches all 5 files that define `_assert_eq_float`.
AC-2.12: `_assert_eq` parameter order is `(expected: Variant, actual: Variant, test_name: String)`. Fail message format: `"expected " + str(expected) + ", got " + str(actual)`.
AC-2.13: `_assert_eq_str` parameter order is `(actual: String, expected: String, test_name: String)` — note: `actual` is first, `expected` is second. This matches the two files (`test_room_templates.gd`, `test_procedural_run.gd`) that define it. Fail message uses double-quote delimiters: `"expected \"" + expected + "\", got \"" + actual + "\""`.

Note on `_assert_eq_string` vs `_assert_eq_str`: These are two distinct methods with different parameter order conventions. Both are present in `test_utils.gd`. Migration must preserve call sites unchanged. Files using `_assert_eq_string` (with `expected` first) must keep calling `_assert_eq_string`. Files using `_assert_eq_str` (with `actual` first) must keep calling `_assert_eq_str`.

**Group D — Float and vector approximate equality**

```
func _approx_eq(a: float, b: float) -> bool:
    return abs(a - b) < 1e-4

func _assert_approx(a: float, b: float, test_name: String) -> void:
    if _approx_eq(a, b):
        _pass(test_name)
    else:
        _fail(test_name, "got " + str(a) + " expected " + str(b) + " (delta " + str(abs(a - b)) + ")")

func _assert_vec2_approx(a: Vector2, b: Vector2, test_name: String) -> void:
    if _approx_eq(a.x, b.x) and _approx_eq(a.y, b.y):
        _pass(test_name)
    else:
        _fail(test_name, "got " + str(a) + " expected " + str(b))
```

AC-2.14: `_approx_eq(a, b)` returns `true` iff `abs(a - b) < 1e-4`. This is an internal helper; it is not itself a test assertion but is called by `_assert_approx` and `_assert_vec2_approx`.
AC-2.15: `_assert_approx` parameter order is `(a: float, b: float, test_name: String)`. Fail message format: `"got " + str(a) + " expected " + str(b) + " (delta " + str(abs(a - b)) + ")"`.
AC-2.16: `_assert_vec2_approx` parameter order is `(a: Vector2, b: Vector2, test_name: String)`. Fail message format: `"got " + str(a) + " expected " + str(b)`.

**Group E — Vector3 approximate equality (included: appears in 2 files with identical body, and the pattern is high-value)**

```
func _near(a: float, b: float, tol: float) -> bool:
    return absf(a - b) <= tol

func _assert_vec3_near(actual: Vector3, expected: Vector3, tol: float, test_name: String) -> void:
    var ok: bool = _near(actual.x, expected.x, tol) \
        and _near(actual.y, expected.y, tol) \
        and _near(actual.z, expected.z, tol)
    if ok:
        _pass(test_name)
    else:
        _fail(test_name, "expected ~" + str(expected) + " (tol " + str(tol) + "), got " + str(actual))
```

AC-2.17: `_near(a, b, tol)` returns `true` iff `absf(a - b) <= tol`.
AC-2.18: `_assert_vec3_near` parameter order is `(actual: Vector3, expected: Vector3, tol: float, test_name: String)`. Fail message format: `"expected ~" + str(expected) + " (tol " + str(tol) + "), got " + str(actual)`.

Note: `_near` appears in `test_room_templates.gd`, `test_room_templates_adversarial.gd`, and `test_procedural_run.gd`. `_assert_vec3_near` appears in `test_room_templates.gd` and `test_procedural_run.gd`. These are included in `test_utils.gd` because `_near` appears in 3 files and `_assert_vec3_near` is coupled to it. The threshold rule (3+ files) is met for `_near`; `_assert_vec3_near` is included as its natural companion.

**Group F — No-op runner compatibility**

```
func run_all() -> int:
    return 0
```

AC-2.19: `run_all()` returns `int` and returns exactly `0`. It prints nothing.

#### 3. Risk & Ambiguity Analysis

- Risk: `_assert_eq_int` and `_assert_eq` overlap — any `int` comparison could use either. The canonical choice is: use `_assert_eq_int` when the type is known to be `int` at the call site, and use `_assert_eq` for `Variant` comparisons. Existing call sites are not changed; only the definitions are centralized.
- Risk: `_assert_eq_float` (tolerance `0.0001`) and `_assert_approx` (tolerance `1e-4`) have the same effective tolerance. They are kept as separate methods because they appear at different call sites and have different parameter orders / message formats.
- Ambiguity: `_assert_approx_v3` and `_assert_approx_f` appear only in `tests/system/test_soft_death_and_restart.gd` (1 file). These are excluded from `test_utils.gd` and remain local. See Requirement MAINT-TUC-4.

#### 4. Clarifying Questions

None. All signatures have been extracted from the actual source files.

---

### Requirement MAINT-TUC-3: Counter Ownership

#### 1. Spec Summary

**Description:** Each individual test file retains its own `var _pass_count: int = 0` and `var _fail_count: int = 0` instance variable declarations. These are NOT declared in `test_utils.gd`. The helpers in `test_utils.gd` reference `_pass_count` and `_fail_count` via GDScript's dynamic dispatch — at runtime, `self._pass_count` resolves to the subclass's declared variable.

**Constraints:** If `_pass_count` or `_fail_count` were declared in `test_utils.gd`, they would still be per-instance (not shared across instances) because GDScript is not a class-based language with static fields. The reason to keep them in each test file is consistency with the existing pattern and to avoid the Generalist Agent having to reason about inheritance shadowing.

**Assumptions:** GDScript permits `extends "path/to/file.gd"` and the subclass can declare member variables that the base class references by name. The base class methods will find those variables on `self`.

**Scope:** Applies to all individual test files that are migrated.

#### 2. Acceptance Criteria

- AC-3.1: `tests/utils/test_utils.gd` contains no `var _pass_count` or `var _fail_count` declarations.
- AC-3.2: Every migrated test file retains `var _pass_count: int = 0` and `var _fail_count: int = 0` as instance variables.
- AC-3.3: Every migrated test file's `run_all()` function continues to reset these counters to 0 at the start of `run_all()`, as in the existing pattern (`_pass_count = 0; _fail_count = 0`).
- AC-3.4: Every migrated test file's `run_all()` function continues to return `_fail_count` as its final statement.

#### 3. Risk & Ambiguity Analysis

- Risk: if an implementer places `_pass_count`/`_fail_count` in `test_utils.gd`, the runner still works because instances are separate. However, this diverges from the convention and makes reasoning harder. The spec prohibits it for clarity.

#### 4. Clarifying Questions

None.

---

### Requirement MAINT-TUC-4: Migration Rules

#### 1. Spec Summary

**Description:** Each test file falls into one of three migration categories: FULL MIGRATE, PARTIAL MIGRATE, or EXCLUDE. The Generalist Agent must apply the rule for each file exactly as specified below.

**FULL MIGRATE** means: change `extends Object` to `extends "res://tests/utils/test_utils.gd"`, remove the local definitions of all helpers that are now in `test_utils.gd`, and keep everything else unchanged (including `class_name`, all test functions, `run_all()`, local constants, and any local helpers not in `test_utils.gd`).

**PARTIAL MIGRATE** means: change `extends Object` to `extends "res://tests/utils/test_utils.gd"`, remove only the helpers that are in `test_utils.gd`, and keep any local helpers that are file-specific (not in `test_utils.gd`).

**EXCLUDE** means: do not change the file. Reason is documented below.

**Constraints:** No test logic, no assertion values, no `run_all()` body, and no test function names may change. Only the boilerplate helper block is removed and the extends clause is updated.

**Assumptions:** All files currently use `extends Object` as their base (confirmed by reading the source files).

**Scope:** All 60 files discovered by `tests/run_tests.gd` under `tests/**/*.gd`, plus the new `tests/utils/test_utils.gd` file itself.

#### 2. Acceptance Criteria — Migration Table

**EXCLUDE list (3 files — do not modify):**

| File | Reason |
|------|--------|
| `tests/run_tests.gd` | The runner itself. Read-only for this ticket. |
| `tests/scripts/mutation/test_mutation_slot_system_single_adversarial.gd` | Stub file. Defines no helpers at all (counters are local inside `run_all()`, not instance variables). Migrating would require restructuring `run_all()` to add instance variables; the risk outweighs the gain for a stub with no tests. |
| `tests/utils/test_utils.gd` | The utility file itself. It is the migration target, not a source. |

**PARTIAL MIGRATE list (files with one or more local helpers NOT in `test_utils.gd`):**

These files are migrated normally (extends clause changed, shared helpers removed), but the following local helpers are retained as-is:

| File | Local helpers to retain (not in test_utils.gd) |
|------|------------------------------------------------|
| `tests/scripts/movement/test_movement_simulation.gd` | `_make_state_with(vx, vy, on_floor)` — test-specific factory |
| `tests/scripts/movement/test_movement_simulation_adversarial.gd` | `_make_state_with(vx, vy, on_floor)` — test-specific factory |
| `tests/system/test_soft_death_and_restart.gd` | `_assert_approx_v3(expected, actual, test_name)` and `_assert_approx_f(expected, actual, test_name)` — appear only in this file |
| `tests/levels/test_procedural_run.gd` | `_load_scene() -> Node` and `_count_nodes_of_class(node, class_name_str)` — scene-loading helpers specific to this file's scene path |
| `tests/levels/test_procedural_run_adversarial.gd` | Same pattern as `test_procedural_run.gd` — retain any scene-loading helpers specific to this file |
| `tests/levels/test_start_finish_flow.gd` | `_load_packed_scene(scene_path)` and `_load_level_scene()` — scene-loading helpers specific to this file |
| `tests/levels/test_mutation_tease_room.gd` | Scene-loading helpers specific to this file |
| `tests/levels/test_mini_boss_encounter.gd` | Scene-loading helpers specific to this file |
| `tests/levels/test_mini_boss_encounter_adversarial.gd` | Scene-loading helpers specific to this file |
| `tests/levels/test_light_skill_check.gd` | Scene-loading helpers specific to this file |
| `tests/levels/test_light_skill_check_adversarial.gd` | Scene-loading helpers specific to this file |
| `tests/levels/test_fusion_opportunity_room.gd` | Scene-loading helpers and `_load_resolver_script()` specific to this file |
| `tests/levels/test_fusion_opportunity_room_adversarial.gd` | Scene-loading helpers specific to this file |
| `tests/levels/test_containment_hall_01.gd` | Scene-loading helpers specific to this file |
| `tests/rooms/test_room_templates.gd` | `_load_packed(scene_path, test_prefix)`, `_instantiate(packed, test_prefix)`, and any other scene-loading helpers specific to this file |
| `tests/rooms/test_room_templates_adversarial.gd` | Same as `test_room_templates.gd` |
| `tests/rooms/test_room_chain_generator.gd` | `_make_generator(test_id)` — test-specific factory |
| `tests/rooms/test_room_chain_generator_adversarial.gd` | `_make_generator(test_id)` — test-specific factory |
| `tests/rooms/test_room_chain_generator_adversarial_2.gd` | `_make_generator(test_id)` — test-specific factory |
| `tests/fusion/test_fusion_resolver.gd` | `_load_resolver_script()`, `_load_manager_script()` — test-specific loaders; inner class `PlayerDouble` — not a helper function |
| `tests/fusion/test_fusion_resolver_adversarial.gd` | Same as `test_fusion_resolver.gd` |
| `tests/scripts/system/test_run_state_manager.gd` | `_load_rsm_script()`, `_make_rsm()` — test-specific factories |
| `tests/scripts/system/test_run_state_manager_adversarial.gd` | Same as `test_run_state_manager.gd` |
| `tests/scenes/levels/test_3d_scene.gd` | `_load_3d_scene()`, `_find_player_3d(root)` — test-specific scene helpers |
| `tests/scenes/levels/test_scene_state_integration_3d.gd` | Any scene-loading helpers specific to this file |
| `tests/scripts/player/test_base_physics_entity_3d.gd` | No extra helpers to retain (only `_pass`, `_fail`, `_assert_true` which migrate). Note: this file uses `cond` as the parameter name instead of `condition` in `_assert_true`; after migration the local definition is removed and the base's `condition` parameter name is used — this has no behavioral effect. |
| `tests/scripts/system/test_logging.gd` | No extra helpers beyond what migrates. Note: uses `class_name LoggingTests` — keep. Note: `_pass` calls `_pass_count` which is an instance variable. After migration, `_pass` will call the subclass's `_pass_count`. |

**FULL MIGRATE list (all remaining files — no local helpers beyond what `test_utils.gd` provides):**

All files not in the EXCLUDE or PARTIAL MIGRATE lists above are fully migrated. This includes:
- All files under `tests/chunk/` except those in the partial list
- All files under `tests/scripts/enemy/`
- All files under `tests/scripts/infection/`
- All files under `tests/scripts/movement/` (except `test_movement_simulation*.gd` which are partial)
- All files under `tests/scripts/mutation/` (except `test_mutation_slot_system_single_adversarial.gd` which is excluded)
- All files under `tests/scripts/system/` (except `test_run_state_manager*.gd` which are partial)
- All files under `tests/system/` (except `test_soft_death_and_restart.gd` which is partial)
- All files under `tests/ui/`
- All files under `tests/asset_generation/`
- `tests/bugfix/test_player_controller_preload_path.gd`

AC-4.1: After migration, `grep -r "func _pass\b" tests/` returns only results from `tests/utils/test_utils.gd` and `tests/scripts/mutation/test_mutation_slot_system_single_adversarial.gd` (the excluded stub whose `_pass_count` is a local variable inside `run_all()`, not a helper function). No other file defines `func _pass(`.
AC-4.2: After migration, `grep -r "func _fail\b" tests/` returns only results from `tests/utils/test_utils.gd` and the excluded stub.
AC-4.3: After migration, `grep -r "func _pass_test\b\|func _fail_test\b" tests/` returns only results from `tests/utils/test_utils.gd`.
AC-4.4: After migration, all migrated files have `extends "res://tests/utils/test_utils.gd"` as their extends clause.
AC-4.5: `run_tests.sh` exits 0 (or exits with the same non-zero count as the pre-migration baseline, with no new failures).

#### 3. Risk & Ambiguity Analysis

- Risk: `test_mutation_slot_system_single_adversarial.gd` is a stub whose counters are declared as `var _pass_count: int = 0` and `var _fail_count: int = 0` inside `run_all()` as local variables, not instance variables. If this file were migrated to extend `test_utils.gd`, the `_pass_count`/`_fail_count` references in `test_utils.gd` helpers would fail to resolve because the stubs' counters are local to `run_all()`. This is the primary reason this file is excluded. If in the future tests are added to this stub, it must be restructured to use instance variables before migration.
- Risk: the `_assert_true` in `test_base_physics_entity_3d.gd` uses `cond` as its parameter name rather than `condition`. After migration the local definition is deleted; this is a behavioral no-op (parameter names are not part of the call signature in GDScript).
- Risk: some files in `tests/levels/` use `_pass_test`/`_fail_test` (not `_pass`/`_fail`). After migration, the call sites continue to call `_pass_test`/`_fail_test`, which are now aliases defined in `test_utils.gd`. No call site changes are needed.
- Edge case: `test_room_chain_generator.gd` and its adversarial variants use `test_id` as the parameter name in `_pass(test_id)` and `_fail(test_id, reason)` rather than `test_name`/`message`. After migration, these call `test_utils.gd`'s `_pass(test_name)` and `_fail(test_name, message)` — the parameter names differ but the behavior is identical (both print the same format). No call site change is needed.

#### 4. Clarifying Questions

None.

---

### Requirement MAINT-TUC-5: DRY Audit Scope for `scripts/`

#### 1. Spec Summary

**Description:** The Generalist Agent performing Task 4 must execute a pattern-level scan of all files under `scripts/` and document findings in the Validation Status block of this ticket. No consolidation of `scripts/` code is performed in this ticket. The goal is identification only.

**Constraints:** The audit must be grep/pattern-level only — not a full structural rewrite analysis. It must identify 2-5 concrete candidates with file names and approximate line counts. It must be factual (based on observed code patterns, not speculative).

**Assumptions:** The DRY audit for `scripts/` is informational only. The output goes into Validation Status, not a separate document.

**Scope:** All `.gd` files under `scripts/` in the repo root.

#### 2. Acceptance Criteria

- AC-5.1: After Task 4 completes, the Validation Status block in this ticket contains a bullet-point list titled "DRY Audit — scripts/" with 2-5 entries.
- AC-5.2: Each entry names at least one specific file, describes the repeated pattern in one sentence, and states an approximate line count or file count for the repetition.
- AC-5.3: The patterns searched for must include at minimum: (a) null-guard + `return null` after a `load()` call, (b) `push_error` + early return patterns, (c) repeated `_rsm` / RunStateManager initialization sequences, (d) repeated signal connection boilerplate.

#### 3. Risk & Ambiguity Analysis

- Low risk: the audit is read-only. No files in `scripts/` are modified.

#### 4. Clarifying Questions

None.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: Pass — full test suite exits 0. ADV-TU-28 and ADV-TU-32 were fixed (previously documented GDScript type-coercion edge cases, now corrected). 28 SMOKE tests pass; all ADV-TU tests pass. 59 migrated test files use `extends "res://tests/utils/test_utils.gd"` (confirmed by grep count).
- Static QA: Pass — `tests/utils/test_utils.gd` confirmed: begins with `extends Object`, no `class_name`, defines `run_all() -> int: return 0`, all Group A–F methods present with exact specified signatures, no `var _pass_count`/`var _fail_count` declarations (counters appear in comments only). All migrated files parse cleanly.
- Integration: Pass — `func _pass\b` and `func _fail\b` exist only in `tests/utils/test_utils.gd`, `tests/utils/test_utils_smoke.gd`, and `tests/utils/test_utils_adversarial.gd`. The smoke and adversarial files intentionally use `extends Object` because they test `test_utils.gd` from outside; extending it would be circular. This is an accepted structural exception consistent with the spec's intent (AC-4.1/4.2 are satisfied in substance: no migrated test file retains its own `func _pass`/`func _fail`). `func _pass_test\b|func _fail_test\b` found only in `tests/utils/test_utils.gd` (AC-4.3 satisfied). The excluded stub (`test_mutation_slot_system_single_adversarial.gd`) has no `func _pass` or `func _fail` at all.
- Manual verification required: None. All acceptance criteria are objectively verifiable via code inspection and automated test run.

**DRY Audit — scripts/**
- `scripts/player/player_controller_3d.gd`: 13 null-guard patterns (`if ... == null: return`) and 9 signal `connect`/`disconnect` calls. The null-guard pattern `var x = get_node_or_null(...); if x == null: push_error(...)` repeats 6+ times; candidate for a `_require_node(path)` helper.
- `scripts/system/death_restart_coordinator.gd` + `scripts/system/run_scene_assembler.gd`: Both repeat `_rsm` / RunStateManager initialization and signal subscription sequences (9 references in DRC, 6 in RSA). A shared `_connect_rsm_signals(rsm)` helper could reduce duplication across these two files.
- `scripts/ui/infection_ui.gd`: 21 `get_node_or_null` / `.get_node(` calls — the highest count in the codebase. Most follow an identical guard pattern `var n = get_node_or_null(path); if n == null: push_error(...); return`. This file is a strong candidate for a local `_require_child(name)` helper.
- `push_error` appears 19 times across `scripts/` — concentrated in `player_controller_3d.gd` (10), `death_restart_coordinator.gd` (7), and `run_scene_assembler.gd` (5). Each use follows the same `push_error("ClassName: description")` format. Not an immediate refactor target but worth a shared logging convention if the codebase grows.
- `get_state_id`, `get_config`, `apply_event` appear in both `scripts/system/scene_state_machine.gd` and `scripts/system/run_state_manager.gd` — both are state machine implementations. A shared `StateMachineBase` interface or protocol could unify the API surface, but this is a design-level concern outside this ticket's scope.

## Blocking Issues
None.

## Escalation Notes
Prior blocking issues (AC-4.1/4.2 literal grep mismatch; ADV-TU-28/ADV-TU-32 test failures) have been resolved. ADV-TU-28 and ADV-TU-32 were fixed. The smoke/adversarial infrastructure files defining their own `func _pass`/`func _fail` are an accepted structural exception — they cannot extend the file they are testing, and no migrated production test file retains its own helpers. All acceptance criteria are now fully evidenced.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "ticket_path": "project_board/maintenance/done/test_utility_consolidation.md"
}
```

## Status
Proceed

## Reason
All acceptance criteria have explicit test or integration coverage. AC-1.1–1.6: tests/utils/test_utils.gd confirmed to exist with correct extends clause, no class_name, run_all() -> int: return 0, and all Group A–F method signatures. AC-2.1–2.19: all method signatures verified by direct file read. AC-3.1: no _pass_count/_fail_count declarations in test_utils.gd (confirmed). AC-3.2–3.4: 59 migrated files retain their counters and the suite exits 0 (implicit confirmation). AC-4.1/4.2: func _pass/func _fail appear only in test_utils.gd and the two self-contained infrastructure files (smoke/adversarial) that intentionally cannot extend the file they test — accepted structural exception. AC-4.3: func _pass_test/func _fail_test found only in test_utils.gd. AC-4.4: 59 files confirmed using correct extends clause. AC-4.5: full suite exits 0. AC-5.1–5.3: DRY audit documented in Validation Status with 5 concrete entries. Ticket is ready for human review and closure.
