# TICKET: FEAT-20260328-mutation-active-color
Title: Mutation Active Color Feedback
Project: blobert
Created By: Human
Created On: 2026-03-28

---

## Description

While a mutation slot is active on the player, Blobert's mesh color shifts to visually indicate the mutation is running (e.g., tinted purple/magenta). When the mutation expires (slot empties), the color reverts to normal. If multiple mutations are stacked, the most prominent color wins or they blend. The effect should be driven by the existing MutationSlotSystem state, not a hardcoded timer.

---

## Acceptance Criteria

- AC-1: When zero mutation slots are filled, the player mesh `albedo_color` matches the baseline color `Color(0.4, 0.9, 0.6, 1)` (the scene default).
- AC-2: When exactly one slot is filled, the player mesh `albedo_color` is the mutation tint color (purple/magenta, e.g. `Color(0.8, 0.2, 0.9, 1)`).
- AC-3: When both slots are filled, the mesh `albedo_color` is the same mutation tint (single color wins — no blending required for v1; both-filled = same visual as one-filled).
- AC-4: Color reverts to baseline when all slots are cleared.
- AC-5: The color logic is driven by polling `MutationSlotManager.any_filled()` each `_process` tick; no separate timer is introduced.
- AC-6: The color change is applied to the `MeshInstance3D` at `SlimeVisual/MeshInstance3D` by modifying `material_override.albedo_color` at runtime.
- AC-7: The feature lives in `scripts/fx/slime_visual_state.gd` (the existing visual-state node already attached to `SlimeVisual`).
- AC-8: `SlimeVisual` node must be able to resolve a reference to `MutationSlotManager` via its parent (`PlayerController3D`) — the controller already holds `_mutation_slot`; `SlimeVisualState` must obtain the reference without reaching into private controller fields (use a new public accessor or pass the reference at ready time).
- AC-9: Pure-logic unit tests cover all AC-1 through AC-5 scenarios without instantiating a full scene.
- AC-10: No existing tests regress.

---

## Dependencies

- None (MutationSlotManager already exists and is wired into PlayerController3D)

---

## Specification

### Requirement MAC-1: Color Constants

#### 1. Spec Summary

- **Description:** Two `Color` constants define the complete visual state space. `COLOR_BASELINE` is the resting color applied when no mutation slots are filled. `COLOR_MUTATION_TINT` is the tint applied when one or more mutation slots are filled. Both constants are declared at the top of `scripts/fx/slime_visual_state.gd`.
- **Constraints:**
  - `COLOR_BASELINE` must equal exactly `Color(0.4, 0.9, 0.6, 1.0)`. This matches the `albedo_color` on `StandardMaterial3D_slime` as declared in `scenes/player/player_3d.tscn` line 15. No other value is acceptable.
  - `COLOR_MUTATION_TINT` must equal exactly `Color(0.8, 0.2, 0.9, 1.0)` (purple/magenta). Full alpha (1.0) is required; no semi-transparency.
  - Both constants must be declared as `const` (not `var`) in `SlimeVisualState`.
  - There is no v1 blending: when two slots are filled the color is identical to when one slot is filled — `COLOR_MUTATION_TINT` always applies regardless of fill count, provided fill count >= 1.
- **Assumptions:** The scene's `StandardMaterial3D_slime.albedo_color = Color(0.4, 0.9, 0.6, 1)` is the authoritative baseline. If the scene file changes that value in the future, `COLOR_BASELINE` must be updated to match.
- **Scope:** `scripts/fx/slime_visual_state.gd` only. `player_controller_3d.gd` and `mutation_slot_manager.gd` are not modified for this requirement.

#### 2. Acceptance Criteria

- MAC-1-AC-1: `SlimeVisualState.COLOR_BASELINE` equals `Color(0.4, 0.9, 0.6, 1.0)` (exact component match, no tolerance).
- MAC-1-AC-2: `SlimeVisualState.COLOR_MUTATION_TINT` equals `Color(0.8, 0.2, 0.9, 1.0)` (exact component match, no tolerance).
- MAC-1-AC-3: Both are declared as `const`, not `var`.
- MAC-1-AC-4: `COLOR_BASELINE` and `COLOR_MUTATION_TINT` are distinct colors (they must not be equal to each other).

#### 3. Risk & Ambiguity Analysis

- Risk: The scene file's `albedo_color` could be changed by a designer without updating `COLOR_BASELINE`. Mitigation: note is added in code comment; no runtime guard needed for v1.
- Edge case: Alpha component. The ticket AC says `Color(0.8, 0.2, 0.9, 1)` — the spec fixes all four components including alpha=1.0 explicitly, preventing accidental semi-transparent mutation tints.

#### 4. Clarifying Questions

- None. The ticket's AC-1 and AC-2 supply both values. This spec fixes them exactly.

---

### Requirement MAC-2: Material Duplication in _ready()

#### 1. Spec Summary

- **Description:** `SlimeVisualState._ready()` must call `material_override.duplicate()` on the `MeshInstance3D`'s material before any color write. `StandardMaterial3D_slime` in `player_3d.tscn` is declared as a sub-resource (`[sub_resource ...]`) and is therefore shared among all instances of the scene. Without duplication, setting `albedo_color` on one player instance modifies the shared resource, corrupting all other instances (including future instances created during a run restart) and potentially dirtying the `.tscn` on disk when Godot auto-serializes.
- **Constraints:**
  - The call sequence in `_ready()` must be:
    1. Resolve `_mesh` (see MAC-3).
    2. If `_mesh` is null: set `_mesh_ready = false`, log a push_error, return without duplicating.
    3. If `_mesh.material_override` is null: set `_mesh_ready = false`, log a push_error, return without duplicating.
    4. Assign `_mesh.material_override = _mesh.material_override.duplicate()`.
    5. Set `_mesh_ready = true`.
  - After duplication, `_mesh.material_override` is an independent `StandardMaterial3D` instance owned by this specific node in this specific scene tree instance.
  - `_mesh_ready: bool` is a private member variable (not a constant) initialized to `false`.
- **Assumptions:** `MeshInstance3D` at path `"MeshInstance3D"` relative to `SlimeVisualState` (i.e., child node) will always have a `material_override` assigned (confirmed in `player_3d.tscn` line 36). The null guard is defensive programming for test harness scenarios.
- **Scope:** `scripts/fx/slime_visual_state.gd` `_ready()` only.

#### 2. Acceptance Criteria

- MAC-2-AC-1: After `_ready()` executes with a valid mesh, `_mesh.material_override` is a different object identity than the original sub-resource (i.e., `is_same(original_material, _mesh.material_override)` returns `false`).
- MAC-2-AC-2: `_mesh_ready` is `true` after a successful `_ready()` with a valid mesh and material.
- MAC-2-AC-3: `_mesh_ready` is `false` if `_mesh` is null after resolution.
- MAC-2-AC-4: `_mesh_ready` is `false` if `_mesh.material_override` is null.
- MAC-2-AC-5: No `push_error` is emitted when the mesh and material are both valid.
- MAC-2-AC-6: A single `push_error` is emitted when `_mesh` is null.
- MAC-2-AC-7: A single `push_error` is emitted when `_mesh.material_override` is null.

#### 3. Risk & Ambiguity Analysis

- Risk: If Godot's headless test runner re-uses node instances across test cases without freeing them, the `material_override` duplication runs once per `_ready()` call. Tests must instantiate a fresh node for each test case to avoid cumulative state.
- Risk: `material_override.duplicate()` is a shallow copy in Godot 4 for `StandardMaterial3D` — all scalar properties (including `albedo_color`) are copied by value. Texture references remain shared, but `albedo_color` is a `Color` value type, so mutations to it are isolated. This is the correct and sufficient duplication depth for this feature.
- Edge case: If `SlimeVisualState` is instantiated outside the player scene (e.g., in a unit test), `_mesh` may be null. The null guard in step 2 above prevents a crash.

#### 4. Clarifying Questions

- None. The planner explicitly required `material_override.duplicate()` before any color mutation.

---

### Requirement MAC-3: MeshInstance3D Reference Resolution in _ready()

#### 1. Spec Summary

- **Description:** `SlimeVisualState` must locate the `MeshInstance3D` that carries the slime material. In the scene hierarchy, `SlimeVisualState` is the script attached to the `SlimeVisual` node (a `Node3D`), and `MeshInstance3D` is a direct child of that node (path `"MeshInstance3D"` relative to `self`).
- **Constraints:**
  - Resolution uses `get_node_or_null("MeshInstance3D") as MeshInstance3D`.
  - The result is stored in a private member variable `_mesh: MeshInstance3D` initialized to `null`.
  - If the result is null, the error handling described in MAC-2 applies (`_mesh_ready = false`, `push_error`).
  - No hardcoded absolute paths (e.g. `"/root/..."`) are used.
  - `_mesh` is resolved once in `_ready()` and cached; `_process()` must not re-resolve it each frame.
- **Assumptions:** The `MeshInstance3D` child node is named exactly `"MeshInstance3D"` (confirmed in `player_3d.tscn` line 34).
- **Scope:** `scripts/fx/slime_visual_state.gd` `_ready()` only.

#### 2. Acceptance Criteria

- MAC-3-AC-1: `_mesh` is non-null after `_ready()` when called in the full player scene tree.
- MAC-3-AC-2: `_mesh` is null when no child named `"MeshInstance3D"` exists (unit test scenario with a bare `SlimeVisualState` node).
- MAC-3-AC-3: The string `"MeshInstance3D"` appears exactly once in `slime_visual_state.gd` (the `get_node_or_null` call in `_ready()`), not duplicated across methods.

#### 3. Risk & Ambiguity Analysis

- Risk: If a designer renames the child node, resolution silently fails at runtime. The `push_error` in MAC-2 ensures the failure is visible in the Godot log.

#### 4. Clarifying Questions

- None.

---

### Requirement MAC-4: Public Accessor get_mutation_slot_manager() on PlayerController3D

#### 1. Spec Summary

- **Description:** `PlayerController3D` must expose a new public method `get_mutation_slot_manager() -> Object` that returns the `_mutation_slot` member variable. `SlimeVisualState` calls this method on its parent node in `_ready()` to obtain the `MutationSlotManager` reference without accessing `_mutation_slot` directly (a private field).
- **Constraints:**
  - Method signature: `func get_mutation_slot_manager() -> Object`
  - Return value: `_mutation_slot` as declared in `player_controller_3d.gd` (currently typed `var _mutation_slot: Object = null`).
  - Return type is `Object` (not `MutationSlotManager`) because `MutationSlotManager` extends `RefCounted`, not `Node`, and `PlayerController3D` already treats it as `Object` throughout. Using `Object` avoids a class-name dependency in the controller.
  - The method must not have side effects. It is a pure getter.
  - If `_mutation_slot` is null (e.g., the controller was not wired to an `InfectionInteractionHandler`), the method returns `null`. The caller (`SlimeVisualState`) must handle a null return.
  - This method is the only new addition to `player_controller_3d.gd` for this feature.
- **Assumptions:** `_mutation_slot` is set during `_ready()` of `PlayerController3D` by querying `InfectionInteractionHandler`. In the main game scene, it will always be non-null when the player is fully wired. In unit test scenarios for `SlimeVisualState`, the parent may not be a `PlayerController3D` and the method may not exist — see MAC-5 for null-safety contract.
- **Scope:** `scripts/player/player_controller_3d.gd` — one method added.

#### 2. Acceptance Criteria

- MAC-4-AC-1: `PlayerController3D` has a method named `get_mutation_slot_manager` with zero parameters and return type `Object`.
- MAC-4-AC-2: Calling `get_mutation_slot_manager()` on a freshly constructed `PlayerController3D` (before wiring) returns `null`.
- MAC-4-AC-3: After `_mutation_slot` is set (simulated by assigning a `MutationSlotManager` instance to it), `get_mutation_slot_manager()` returns that same instance.
- MAC-4-AC-4: The method has no side effects — calling it N times produces the same result without mutating any state.
- MAC-4-AC-5: No existing method signatures in `PlayerController3D` are modified.

#### 3. Risk & Ambiguity Analysis

- Risk: Another agent or future ticket may introduce a different wiring path that bypasses `InfectionInteractionHandler` and sets `_mutation_slot` differently. The getter is forward-compatible because it reads `_mutation_slot` unconditionally regardless of how it was set.
- Edge case: If `PlayerController3D._ready()` runs but `InfectionInteractionHandler` is absent, `_mutation_slot` remains null. `get_mutation_slot_manager()` returns null. `SlimeVisualState` must handle null gracefully (see MAC-5).

#### 4. Clarifying Questions

- None. The planner explicitly required a public accessor. Return type `Object` is consistent with the existing typing convention in `player_controller_3d.gd`.

---

### Requirement MAC-5: MutationSlotManager Reference Resolution in SlimeVisualState._ready()

#### 1. Spec Summary

- **Description:** `SlimeVisualState._ready()` must obtain a reference to the `MutationSlotManager` by calling `get_mutation_slot_manager()` on its parent node. The result is cached in a private member variable `_mutation_slot_manager: Object` initialized to `null`. All null cases must be handled without crash.
- **Constraints:**
  - Resolution sequence in `_ready()` (after MAC-3 mesh resolution):
    1. Call `var parent: Node = get_parent()`.
    2. If `parent == null`: set `_mutation_slot_manager = null`, log `push_error`, continue (do not return — mesh duplication may have already succeeded).
    3. If `parent` does not have method `"get_mutation_slot_manager"`: set `_mutation_slot_manager = null`, log `push_error`, continue.
    4. Otherwise: `_mutation_slot_manager = parent.call("get_mutation_slot_manager")`.
    5. If `_mutation_slot_manager == null`: log `push_warning` (not `push_error` — null is valid in test scenes where no `InfectionInteractionHandler` exists).
  - `_mutation_slot_manager` is checked for null in every `_process()` tick before calling `any_filled()`.
  - No direct field access to `parent._mutation_slot` is permitted.
  - `has_method("get_mutation_slot_manager")` is used (not duck-typing via `is`) to remain compatible with test stubs that are not `PlayerController3D` instances.
- **Assumptions:** In the full game scene, `get_parent()` on `SlimeVisualState` returns the `PlayerController3D` node (confirmed: `SlimeVisual` is a direct child of `Player3D` in `player_3d.tscn`). In unit tests, the parent may be a plain `Node` or a minimal stub.
- **Scope:** `scripts/fx/slime_visual_state.gd` `_ready()` and `_mutation_slot_manager` member.

#### 2. Acceptance Criteria

- MAC-5-AC-1: `_mutation_slot_manager` is non-null after `_ready()` when attached under a `PlayerController3D` that has been wired to a `MutationSlotManager`.
- MAC-5-AC-2: `_mutation_slot_manager` is null when `get_parent()` returns null.
- MAC-5-AC-3: `_mutation_slot_manager` is null when the parent does not have method `"get_mutation_slot_manager"`.
- MAC-5-AC-4: `_mutation_slot_manager` is null when `get_mutation_slot_manager()` returns null.
- MAC-5-AC-5: No crash occurs in any of the null cases above.
- MAC-5-AC-6: `push_error` is emitted when parent is null or lacks the method.
- MAC-5-AC-7: `push_warning` (not `push_error`) is emitted when parent has the method but it returns null.

#### 3. Risk & Ambiguity Analysis

- Risk: Using `parent.call("get_mutation_slot_manager")` returns `null` for two distinct cases — (a) method returns null because `_mutation_slot` was never set, and (b) method does not exist but `has_method` guard failed. The `has_method` check in step 3 ensures case (b) never reaches `call()`, keeping the null-from-call unambiguous as case (a).

#### 4. Clarifying Questions

- None.

---

### Requirement MAC-6: _process() Poll Logic and Color Assignment

#### 1. Spec Summary

- **Description:** `SlimeVisualState._process(delta)` polls `_mutation_slot_manager.any_filled()` each frame and conditionally sets `_mesh.material_override.albedo_color` to either `COLOR_MUTATION_TINT` or `COLOR_BASELINE`. A cached boolean `_current_tinted: bool` prevents redundant per-frame material property writes when the tint state has not changed.
- **Constraints:** The exact logical sequence for `_process(_delta: float)` is:

  1. If `not _mesh_ready` or `_mesh == null` or `not is_instance_valid(_mesh)`: return early (no color operation).
  2. If `_mutation_slot_manager == null` or `not is_instance_valid(_mutation_slot_manager)`: return early (no color operation). Do not log per-frame; this was already logged in `_ready()`.
  3. Evaluate: `var should_tint: bool = _mutation_slot_manager.any_filled()`.
  4. If `should_tint == _current_tinted`: return early (no material write).
  5. `_current_tinted = should_tint`.
  6. If `_current_tinted`: `_mesh.material_override.albedo_color = COLOR_MUTATION_TINT`.
  7. Else: `_mesh.material_override.albedo_color = COLOR_BASELINE`.

- **Constraints (additional):**
  - `_current_tinted: bool` is a private member variable initialized to `false`.
  - The equality check in step 4 is a strict boolean equality (`==`), not a Color comparison.
  - No `Tween` or animation is used for the color transition in v1 — the color snaps instantly.
  - No timer, counter, or accumulator is introduced.
  - `_delta` parameter is intentionally unused (prefix underscore convention already used in the stub).
  - `any_filled()` is called at most once per frame.
  - The color is written to `_mesh.material_override.albedo_color` directly, not via a tween or `set()` call.
- **Assumptions:** `_mutation_slot_manager` is a `MutationSlotManager` instance which extends `RefCounted`. `RefCounted` objects do not become invalid via `is_instance_valid()` checks in Godot 4 unless freed explicitly; however, the guard is included defensively.
- **Scope:** `scripts/fx/slime_visual_state.gd` `_process()` method and `_current_tinted` member.

#### 2. Acceptance Criteria

- MAC-6-AC-1: When `_mutation_slot_manager.any_filled()` returns `true` and `_current_tinted` was `false`, `_mesh.material_override.albedo_color` is set to `COLOR_MUTATION_TINT` and `_current_tinted` becomes `true`.
- MAC-6-AC-2: When `_mutation_slot_manager.any_filled()` returns `false` and `_current_tinted` was `true`, `_mesh.material_override.albedo_color` is set to `COLOR_BASELINE` and `_current_tinted` becomes `false`.
- MAC-6-AC-3: When `_mutation_slot_manager.any_filled()` returns `true` and `_current_tinted` is already `true`, `albedo_color` is NOT written (no material assignment call occurs). `_current_tinted` remains `true`.
- MAC-6-AC-4: When `_mutation_slot_manager.any_filled()` returns `false` and `_current_tinted` is already `false`, `albedo_color` is NOT written. `_current_tinted` remains `false`.
- MAC-6-AC-5: When `_mesh_ready` is `false`, `_process()` exits before any `any_filled()` call.
- MAC-6-AC-6: When `_mutation_slot_manager` is `null`, `_process()` exits before any `any_filled()` call.
- MAC-6-AC-7: `any_filled()` is called exactly once per `_process()` invocation (not zero, not two) when both `_mesh_ready` is `true` and `_mutation_slot_manager` is non-null and `should_tint != _current_tinted`.
- MAC-6-AC-8: `any_filled()` is called exactly once per `_process()` invocation when the state has changed (`should_tint != _current_tinted`). When state has NOT changed, `albedo_color` is not written but `any_filled()` is still called once (the poll always happens; only the write is skipped).
- MAC-6-AC-9 (AC-3 from ticket): Two filled slots produces the same `albedo_color` as one filled slot — `COLOR_MUTATION_TINT` in both cases. The poll uses only `any_filled()` with no slot-count awareness.

#### 3. Risk & Ambiguity Analysis

- Risk: The step-4 early-return skips the material write but `any_filled()` was already called in step 3. This is intentional — the poll is cheap (two `is_filled()` string comparisons in `MutationSlotManager`), and caching the poll result would add complexity for negligible gain.
- Edge case: The very first `_process()` frame before any mutation fills a slot. `_current_tinted` initializes to `false`. `any_filled()` returns `false`. `should_tint (false) == _current_tinted (false)` → no write. This is correct: the material already has `COLOR_BASELINE` from the scene file (before and after duplication, `albedo_color = Color(0.4, 0.9, 0.6, 1)`).
- Edge case: `_process()` is called before `_ready()` completes. `_mesh_ready` is `false` (initialized to `false`), so step 1 returns early. Safe.
- Risk: Godot calls `_process()` before `_ready()` in edge cases with `set_process(true)` called from a parent's `_ready()`. The `_mesh_ready` guard in step 1 handles this.

#### 4. Clarifying Questions

- None. The poll-then-equality-check pattern is fully specified by the planner and the ticket AC.

---

### Requirement MAC-7: SlimeVisualState Member Variable Inventory

#### 1. Spec Summary

- **Description:** Complete listing of all new member variables added to `SlimeVisualState` by this feature. Existing stub members are unchanged (none currently exist; the stub only has `_ready` and `_process` method stubs with `pass`).
- **Constraints:** The complete private member variable set required by this feature:

  | Variable | Type | Initial Value | Purpose |
  |---|---|---|---|
  | `_mesh` | `MeshInstance3D` | `null` | Cached reference to child MeshInstance3D |
  | `_mesh_ready` | `bool` | `false` | True iff mesh was resolved and material was duplicated |
  | `_mutation_slot_manager` | `Object` | `null` | Cached reference obtained via parent.get_mutation_slot_manager() |
  | `_current_tinted` | `bool` | `false` | Tracks current tint state to avoid redundant material writes |

  And two constants (MAC-1):

  | Constant | Value |
  |---|---|
  | `COLOR_BASELINE` | `Color(0.4, 0.9, 0.6, 1.0)` |
  | `COLOR_MUTATION_TINT` | `Color(0.8, 0.2, 0.9, 1.0)` |

- **Assumptions:** No other member variables are introduced by this feature.
- **Scope:** `scripts/fx/slime_visual_state.gd` class body.

#### 2. Acceptance Criteria

- MAC-7-AC-1: All four member variables are declared in the class body with the exact types and initial values listed above.
- MAC-7-AC-2: Both constants are declared with the exact values listed above.
- MAC-7-AC-3: No additional member variables beyond these four are introduced by this feature.

#### 3. Risk & Ambiguity Analysis

- None.

#### 4. Clarifying Questions

- None.

---

### Requirement MAC-8: Non-Functional — Performance

#### 1. Spec Summary

- **Description:** The color polling mechanism must not introduce measurable per-frame overhead beyond two boolean comparisons and a string emptiness check (the cost of `MutationSlotManager.any_filled()`).
- **Constraints:**
  - `material_override.albedo_color` is assigned at most once per state transition (not every frame). The `_current_tinted` cache enforces this.
  - No `Tween`, signal, or coroutine is introduced.
  - `get_node_or_null` is not called in `_process()` — `_mesh` and `_mutation_slot_manager` are cached in `_ready()`.
  - No per-frame string operations beyond those already inside `any_filled()` (which the controller already calls in `_physics_process`).
- **Assumptions:** No assumption. This is a hard constraint.
- **Scope:** Runtime behavior of `SlimeVisualState._process()`.

#### 2. Acceptance Criteria

- MAC-8-AC-1: `_process()` does not call `get_node_or_null`, `find_child`, or any scene-tree query method.
- MAC-8-AC-2: `material_override.albedo_color` is not assigned on frames where `should_tint == _current_tinted`.
- MAC-8-AC-3: No `Tween` nodes are created.

#### 3. Risk & Ambiguity Analysis

- No risks. This is a structural enforcement of the design spec.

#### 4. Clarifying Questions

- None.

---

### Requirement MAC-9: Non-Functional — Test Coverage Constraints

#### 1. Spec Summary

- **Description:** All new tests must be pure-logic unit tests — no full scene instantiation, no `SceneTree` required. Tests must use minimal stubs for `MeshInstance3D` (or a plain object with an `albedo_color` field) and `MutationSlotManager`.
- **Constraints:**
  - Tests live under `tests/` in a new file (path to be determined by Test Designer Agent).
  - Tests must not call `run_tests.sh` to validate; they join the existing test suite run via `timeout 300 godot -s tests/run_tests.gd`.
  - Each of the ticket's AC-1 through AC-5 must have at least one corresponding test case.
  - No existing test file is modified (AC-10).
  - Tests must be deterministic (no randomness, no frame-timing dependency).
- **Assumptions:** The existing test infrastructure (test runner at `tests/run_tests.gd`) supports pure GDScript unit tests without scene instantiation, consistent with the pattern established in other test files in the project.
- **Scope:** `tests/` directory, new file only.

#### 2. Acceptance Criteria

- MAC-9-AC-1: A test file exists that exercises MAC-6-AC-1 through MAC-6-AC-9 (the `_process` poll logic) using stubs.
- MAC-9-AC-2: Tests for the null-safety contract (MAC-5) exist.
- MAC-9-AC-3: Tests for material duplication behavior (MAC-2) exist.
- MAC-9-AC-4: All ticket AC-1 through AC-5 map to at least one test case each.
- MAC-9-AC-5: No test instantiates `player_3d.tscn` or any other `.tscn` file.
- MAC-9-AC-6: The new test file does not modify or import any existing test file.

#### 3. Risk & Ambiguity Analysis

- Risk: GDScript unit tests that stub `MeshInstance3D` behavior may require a custom lightweight object that has a `material_override` property with an `albedo_color` field. The Test Designer Agent must design these stubs carefully to avoid Godot's type system rejecting non-`MeshInstance3D` objects assigned to a typed variable. Recommendation: `_mesh` should be typed as `MeshInstance3D` in production code but accessed via an untyped wrapper in tests, or the test should construct an actual `MeshInstance3D` node in memory without adding it to the scene tree.
- Risk: The `is_instance_valid()` guard in `_process()` (step 1) may behave differently for in-memory vs. scene-tree nodes in headless mode. Tests must confirm the guard does not falsely invalidate a valid in-memory `MeshInstance3D`.

#### 4. Clarifying Questions

- None that block the spec. The Test Designer Agent must choose the stub strategy.

---

### Requirement MAC-10: Scope Boundary — Files Modified

#### 1. Spec Summary

- **Description:** Exactly two source files are modified by this feature. No scene files (.tscn) are modified.
- **Constraints:**
  - **Modified:** `scripts/fx/slime_visual_state.gd` — expanded with all logic described in MAC-1 through MAC-8.
  - **Modified:** `scripts/player/player_controller_3d.gd` — one new public method `get_mutation_slot_manager() -> Object` added (MAC-4). No other changes to this file.
  - **Not modified:** `scenes/player/player_3d.tscn` — the `material_override` sub-resource in the scene file is NOT changed. The duplication happens at runtime in `_ready()`.
  - **Not modified:** `scripts/mutation/mutation_slot_manager.gd` — no changes needed.
  - **Not modified:** `scripts/mutation/mutation_slot.gd` — no changes needed.
  - **New file created:** one test file under `tests/` (exact path assigned by Test Designer Agent).
- **Assumptions:** No other files are touched.
- **Scope:** Entire project.

#### 2. Acceptance Criteria

- MAC-10-AC-1: Git diff for this feature shows changes only in `scripts/fx/slime_visual_state.gd`, `scripts/player/player_controller_3d.gd`, and the new test file.
- MAC-10-AC-2: `scenes/player/player_3d.tscn` is unchanged in git diff.

#### 3. Risk & Ambiguity Analysis

- No risks.

#### 4. Clarifying Questions

- None.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_BREAK

## Revision
3

## Last Updated By
Test Designer Agent

## Validation Status
- Tests: Not Run
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/6_milestone_6_roguelike_run_structure/in_progress/FEAT-20260328-mutation-active-color.md",
  "spec_requirements": ["MAC-1","MAC-2","MAC-3","MAC-4","MAC-5","MAC-6","MAC-7","MAC-8","MAC-9","MAC-10"]
}
```

## Status
Proceed

## Reason
Primary behavioral test suite written at tests/scripts/fx/test_mutation_active_color.gd. 12 tests covering MAC-1 through MAC-9 plus bonus AC-3 and two guard cases. All 10 non-guard tests fail against the current stub (expected — implementation not written). 2 guard tests pass trivially (no side effects on stub). No existing tests regressed (pre-existing failures unchanged). Test Breaker Agent must attempt adversarial edge-case tests against this suite.
