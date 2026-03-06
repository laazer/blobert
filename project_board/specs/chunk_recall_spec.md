# Chunk Recall Specification
# M1-007 — chunk_recall.md
# SPEC-62 through SPEC-70
#
# Prerequisite specs: SPEC-1 through SPEC-61
#   SPEC-1  through SPEC-14: movement_controller.md / M1-001
#   SPEC-15 through SPEC-24: jump_tuning.md / M1-002
#   SPEC-25 through SPEC-36: wall_cling.md / M1-003
#   SPEC-37 through SPEC-45: basic_camera_follow.md / M1-004
#   SPEC-46 through SPEC-53: chunk_detach.md / M1-005
#   SPEC-54 through SPEC-61: hp_reduction_on_detach.md / M1-006
# Continuing numbering from SPEC-61.
#
# Files affected:
#   /Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd (read-only
#     verification only — implementation already present)
#   /Users/jacobbrandt/workspace/blobert/tests/test_chunk_recall_simulation.gd
#     (corrected — 4 failing tests fixed)
#   /Users/jacobbrandt/workspace/blobert/tests/test_chunk_recall_simulation_adversarial.gd
#     (corrected — 8 failing tests fixed)
#
# Files NOT affected by this ticket:
#   /Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd
#     (simulate() signature and MovementState fields are UNCHANGED — see SPEC-69)
#   /Users/jacobbrandt/workspace/blobert/tests/run_tests.gd
#     (no new test suites registered — recall suites already registered)

---

## Requirement SPEC-62: Recall Input Routing

### 1. Spec Summary

- **Description:** The "detach" input action (E key, defined in `project.godot` as the `"detach"` action, established by M1-005) serves a dual purpose in `player_controller.gd`. On each physics frame, the controller reads `Input.is_action_just_pressed("detach")` and routes the press to one of three outcomes based on the current state:

  - **Detach path** (existing behavior, M1-005): When `_current_state.has_chunk == true`. The press is passed to `simulate()` as `detach_just_pressed = true`, which triggers the detach step (step 17) inside `simulate()`. The chunk spawns on that frame via the controller's `prev_has_chunk` / `_current_state.has_chunk` transition guard.

  - **Recall path** (new behavior, M1-007): When all four conditions are simultaneously true:
    1. `_current_state.has_chunk == false` (chunk is detached — `prev_has_chunk` is read from the pre-simulate state)
    2. `detach_just_pressed == true` (fresh press on this frame)
    3. `_chunk_node != null` (a chunk node reference exists)
    4. `is_instance_valid(_chunk_node) == true` (the chunk node is alive in the scene tree)
    AND `_recall_in_progress == false` (no recall is already running).

    When all conditions are met, `_recall_in_progress` is set to `true` and `_recall_timer` is reset to `0.0` on this frame.

  - **No-op path**: Any press that satisfies neither the detach path nor the recall path conditions is silently discarded. This includes: pressing while `has_chunk == false` and `_chunk_node == null`; pressing while `has_chunk == false` and `_chunk_node` is invalid; pressing while recall is already in progress.

- **Constraints:**
  1. Routing occurs inside `_physics_process(delta)` in `player_controller.gd`. The `detach_just_pressed` variable is read via `Input.is_action_just_pressed("detach")` once per frame.
  2. The detach path is handled by the `simulate()` call (step 17 inside `MovementSimulation`). The recall path is handled by controller-level logic after the `simulate()` call returns.
  3. The `has_chunk == false` guard on the recall path is evaluated from the pre-simulate state (`prev_has_chunk`), captured before `simulate()` is called (see SPEC-63 for the precise ordering).
  4. The guard `not _recall_in_progress` prevents stacking: a second press during an active recall is a no-op. A new recall cannot be initiated until the current one completes or is cancelled.
  5. The `is_instance_valid(_chunk_node)` guard is required in addition to the `!= null` check because a chunk node may have had `queue_free()` called on it by external code (e.g., a kill volume), which marks it as freed without immediately setting the reference to null.
  6. No changes to the `simulate()` call-site or its 8 arguments are introduced by M1-007. The `detach_just_pressed` argument passed to `simulate()` is the same value read from `Input.is_action_just_pressed("detach")`. When the controller routes the press as "recall", `simulate()` still receives `detach_just_pressed = true` — but because `prior_state.has_chunk == false` on that frame, `detach_eligible` in step 17 of `simulate()` evaluates to `false`, making the detach a no-op inside the simulation.

- **Assumptions:**
  1. The "detach" action is bound to the E key in `project.godot` and was established as part of M1-005.
  2. `_recall_in_progress` is initialized to `false` and `_chunk_node` is initialized to `null` in the controller's member variable declarations. No `_ready()` initialization of these fields is required.
  3. "just pressed" semantics match Godot's definition: `is_action_just_pressed()` returns `true` on exactly one frame per discrete key-down event.

- **Scope / Context:** Applies exclusively to `_physics_process(delta)` in `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd`. No changes to `movement_simulation.gd` or any test file routing logic.

### 2. Acceptance Criteria

- **AC-62.1:** When `prior_state.has_chunk == true` and `detach_just_pressed == true`, the press is routed to the detach path: `simulate()` receives `detach_just_pressed = true`, and `_recall_in_progress` remains `false`. `_chunk_node` becomes non-null after the frame via the spawn block.
  - Example: Player starts with `has_chunk = true`, presses E → `_current_state.has_chunk` transitions to `false`; `_chunk_node` is assigned; `_recall_in_progress` remains `false`.

- **AC-62.2:** When `prior_state.has_chunk == false`, `_chunk_node != null`, `is_instance_valid(_chunk_node) == true`, and `detach_just_pressed == true`, and `_recall_in_progress == false`, the press is routed to the recall path: `_recall_in_progress` is set to `true` and `_recall_timer` is set to `0.0` on this frame. `_current_state.has_chunk` remains `false` (the chunk is not immediately reabsorbed).
  - Example: Player has detached chunk, presses E → `_recall_in_progress = true`; `_recall_timer = 0.0` (before delta accumulation); `has_chunk` still `false`.

- **AC-62.3:** When `prior_state.has_chunk == false` and `_chunk_node == null`, a detach press is a no-op for both detach and recall: `_recall_in_progress` remains `false`, `_current_state.has_chunk` remains `false`, no new chunk is spawned.
  - Example: Player detached chunk, chunk was externally destroyed (`_chunk_node = null`), player presses E → no state change.

- **AC-62.4:** When `_recall_in_progress == true` and `detach_just_pressed == true`, the press is discarded: `_recall_in_progress` remains `true`, `_recall_timer` continues accumulating. A second press does not restart, accelerate, or stack the recall.

- **AC-62.5:** When `prior_state.has_chunk == false`, `_chunk_node != null`, but `is_instance_valid(_chunk_node) == false` (the chunk node has been freed but the reference not yet cleared), a detach press is a no-op for recall: `_recall_in_progress` remains `false`.

- **AC-62.6:** On the frame that recall is initiated, `simulate()` receives `detach_just_pressed = true` but the simulation's detach step produces no state change because `prior_state.has_chunk == false` makes `detach_eligible = false`. Thus `result.has_chunk` carries forward as `false` and `result.current_hp` carries forward unchanged.

### 3. Risk & Ambiguity Analysis

- **Risk R-62.1 — prev_has_chunk timing:** The recall eligibility check uses `prev_has_chunk` (the pre-simulate value of `has_chunk`) to evaluate whether the chunk is detached. If this were instead read from `next_state.has_chunk` (the post-simulate value), the check would be off by one frame for the detach-to-recall transition. The implementation correctly reads `prev_has_chunk` from `_current_state.has_chunk` before `simulate()` is called.

- **Risk R-62.2 — Simultaneous detach-and-recall guard:** On the frame immediately after a detach, `prev_has_chunk == false` (set at the end of the previous frame via copy-back) and `_chunk_node != null`. If the player presses E rapidly, this frame correctly routes as recall rather than detach. The guard `and (not prev_has_chunk)` in the recall routing ensures this.

- **Risk R-62.3 — is_instance_valid vs null check:** Only checking `_chunk_node != null` is insufficient because `queue_free()` marks the node for deletion without immediately nullifying the reference. Both guards must be present.

### 4. Clarifying Questions

None. All routing logic is fully specified by the existing `player_controller.gd` implementation and the ticket context. No further clarification is required.

---

## Requirement SPEC-63: Recall Timer and Travel Time

### 1. Spec Summary

- **Description:** When recall is initiated (SPEC-62), the controller tracks the elapsed recall duration using `_recall_timer: float` and the constant `_RECALL_TRAVEL_TIME: float = 0.25`. The timer is frame-rate independent: it accumulates real elapsed time via `delta` values rather than counting frames.

  The precise sequencing within `_physics_process(delta)` on the initiation frame:
  1. `_recall_in_progress` is set to `true`.
  2. `_recall_timer` is set to `0.0`.
  3. Later in the same `_physics_process(delta)` call, the `if _recall_in_progress:` block runs and adds `delta` to `_recall_timer`. So after the initiation frame completes, `_recall_timer == delta` (not `0.0`).

  On all subsequent frames while `_recall_in_progress == true`:
  - `_recall_timer += delta` is executed each frame before the completion check.
  - Recall completes when `_recall_timer >= _RECALL_TRAVEL_TIME`.

  At the default 60 FPS (delta ≈ 0.016s), accumulation pattern:
  - After initiation frame: `_recall_timer ≈ 0.016`
  - After 15 additional frames: `_recall_timer ≈ 0.256 >= 0.25` → recall completes.
  - Minimum frames to complete (at 60 FPS): the initiation frame + 15 additional frames = 16 total `_physics_process` calls.

- **Constraints:**
  1. `_RECALL_TRAVEL_TIME` is a `const float = 0.25` declared as a member of `PlayerController`. It is not `@export`-able and cannot be changed at runtime without modifying the source. Making it an `@export var` is out of scope for M1-007.
  2. `_recall_timer` accumulates via `_recall_timer += delta` (where `delta` is the raw physics delta, not clamped or sanitized). Godot's physics delta is guaranteed positive by the engine.
  3. The completion check uses `>=` (greater-than-or-equal): `_recall_timer >= _RECALL_TRAVEL_TIME`. Recall triggers the moment the accumulated time meets or exceeds 0.25 seconds.
  4. The timer is reset to `0.0` only when a new recall is initiated. It is not reset on cancellation (external chunk destruction sets `_recall_in_progress = false` without resetting `_recall_timer`). After cancellation, `_recall_timer` retains its last value but is irrelevant because `_recall_in_progress == false`.
  5. The initiation frame's `delta` is counted toward the recall duration. A frame with `delta = 0.25` would complete recall in a single frame (initiation and completion in one `_physics_process` call).

- **Assumptions:**
  1. Godot 4's physics delta is positive and determined by the physics frame rate (default 60 Hz → delta ≈ 0.016667s). Variable-physics or low-FPS scenarios produce larger deltas.
  2. The `if _recall_in_progress:` block runs on the same frame as the initiation block because they are sequential statements in `_physics_process()`. No deferred or coroutine call separates them.

- **Scope / Context:** Applies to the recall timer logic inside `_physics_process(delta)` in `player_controller.gd`. The timer is entirely self-contained: it is not read by `simulate()`, not exposed via `@export`, and not visible to any external system.

### 2. Acceptance Criteria

- **AC-63.1:** `_RECALL_TRAVEL_TIME` is exactly `0.25` (a `const float`). Verified by reading the member declaration: `const _RECALL_TRAVEL_TIME: float = 0.25`.

- **AC-63.2:** On the frame that recall is initiated, `_recall_timer` is set to `0.0` first, then incremented by `delta`. After the initiation frame, `_recall_timer == delta` (not `0.0`).
  - Example: Initiation frame with `delta = 0.016` → `_recall_timer == 0.016` after the frame completes.

- **AC-63.3:** At standard 60 FPS (delta = 0.016), recall completes after no more than 16 `_physics_process` calls total (the initiation call plus at most 15 subsequent calls). Verified by: `16 * 0.016 = 0.256 >= 0.25`.

- **AC-63.4:** Recall does NOT complete in 10 `_physics_process` calls at delta = 0.016. `10 * 0.016 = 0.160 < 0.25`. Tests that step only 10 frames after initiating recall will observe `has_chunk` still `false` and `_recall_in_progress` still `true`.

- **AC-63.5:** With `delta = 0.25`, recall completes within the initiation frame itself (first `_physics_process` call): `_recall_timer = 0.0 + 0.25 = 0.25 >= 0.25`. Both initiation and completion occur in the same frame.

- **AC-63.6:** With `delta = 1.0` (extreme slow frame), recall completes within the initiation frame: `_recall_timer = 0.0 + 1.0 = 1.0 >= 0.25`. No crash, no multiple HP restoration events.

- **AC-63.7:** The timer uses `>=` (not `>`): a `_recall_timer` that lands exactly on `0.25` (within floating-point precision) triggers completion. Tests should not rely on exact equality; the `>=` comparison is the governing condition.

- **AC-63.8:** Recall is frame-rate independent: the same detach+recall input sequence (measured in wall-clock seconds) produces the same outcome at 30 FPS (delta ≈ 0.033) and 60 FPS (delta ≈ 0.016). Both accumulate past 0.25s within approximately 0.25 seconds of real time.

### 3. Risk & Ambiguity Analysis

- **Risk R-63.1 — Frame count vs. time threshold mismatch in tests:** Tests that use `_step_player(player, N, 0.016)` after recall initiation may fail if N is too small. Specifically, 10 additional frames (N=10) is insufficient at 0.016 delta: 0.016 (initiation) + 10 * 0.016 = 0.176s < 0.25s. Tests must use at least 15 additional frames (total 16 including initiation) or use a larger delta.

- **Risk R-63.2 — Delta accumulation on initiation frame:** The initiation frame sets `_recall_timer = 0.0` and then increments by `delta` in the same call. Tests that assert `_recall_timer == 0.0` immediately after calling `_recall_once()` (which calls `_physics_process` once) will fail: the timer is `delta`, not `0.0`.

- **Risk R-63.3 — Single large delta completing recall immediately:** With delta >= 0.25 (e.g., a severe frame hitch or a test using large delta values), recall initiates and completes within one frame. The HP restoration and reabsorption logic runs on that same frame. This is correct behavior and is not a bug.

### 4. Clarifying Questions

None. The timer behavior is fully deterministic from the implementation and the ticket context. No further clarification is required.

---

## Requirement SPEC-64: Reabsorption Completion

### 1. Spec Summary

- **Description:** When `_recall_timer >= _RECALL_TRAVEL_TIME` (0.25 seconds accumulated), the recall completes. On the completion frame, within `_physics_process(delta)`, the following five operations occur in this exact order:

  1. `_recall_in_progress = false`
  2. HP restoration: `_current_state.current_hp = minf(_simulation.max_hp, _current_state.current_hp + _simulation.hp_cost_per_detach)`
  3. `_current_state.has_chunk = true`
  4. `_chunk_node.queue_free()` (guarded by `_chunk_node != null and is_instance_valid(_chunk_node)`)
  5. `_chunk_node = null`

  These operations are performed on `_current_state` directly (not on the result of `simulate()`). They occur after `simulate()` has already been called and its state copy-backs have been applied.

  Movement simulation continues normally on the completion frame: `simulate()` is called with the same inputs as any other frame, and `move_and_slide()` applies the result velocity. The reabsorption is purely a state update; it does not modify the velocity computed by `simulate()`.

- **Constraints:**
  1. The five operations occur in the exact order listed above, as a single sequential block within the `if _recall_in_progress:` / `elif _recall_timer >= _RECALL_TRAVEL_TIME:` branch of `_physics_process(delta)`.
  2. HP restoration uses `minf()` (GDScript's float-specific min function, equivalent to `min()` for floats), not `min()` with an int operand.
  3. HP restoration reads `_current_state.current_hp` as the "prior HP" at the moment of reabsorption — this is the HP value after the detach HP cost was applied on the detach frame, and after any carry-forward frames since then. It is NOT the HP value at the time of detach.
  4. HP restoration reads `_simulation.hp_cost_per_detach` from the `MovementSimulation` instance — this is the same cost that was subtracted on the detach frame.
  5. HP restoration reads `_simulation.max_hp` from the `MovementSimulation` instance as the upper bound.
  6. The `queue_free()` call is guarded: `if _chunk_node != null and is_instance_valid(_chunk_node): _chunk_node.queue_free()`. If the chunk node is already null or invalid (destroyed between the timer check and this point), `queue_free()` is not called.
  7. `_chunk_node` is always set to `null` after the reabsorption block, regardless of whether `queue_free()` was called.
  8. `simulate()` is called before the reabsorption block runs. The reabsorption block does not re-enter or call `simulate()`.

- **Assumptions:**
  1. At the time of reabsorption, `_current_state.current_hp` reflects the HP after detach reduction, which is `prior_detach_hp - hp_cost_per_detach` (clamped to `min_hp` by simulate()). If the player was at `max_hp` before detaching, `_current_state.current_hp` will be `max_hp - hp_cost_per_detach` at reabsorption. Adding `hp_cost_per_detach` back and clamping to `max_hp` restores to `max_hp`.
  2. No other source modifies `_current_state.current_hp` between the detach frame and the recall completion frame (it is carried forward unchanged by `simulate()` on non-detach frames).
  3. The `_simulation` instance is always valid at this point (initialized in `_ready()`).

- **Scope / Context:** Applies to the reabsorption completion block inside the `if _recall_in_progress:` branch of `_physics_process(delta)` in `player_controller.gd`.

### 2. Acceptance Criteria

- **AC-64.1:** On the completion frame, `_recall_in_progress` is set to `false` before any other reabsorption operation. Verified by: after recall completes, `_recall_in_progress == false`.

- **AC-64.2:** `_current_state.has_chunk` is set to `true` on the completion frame. Verified by: after recall completes (≥16 frames at 60 FPS), `player._current_state.has_chunk == true`.

- **AC-64.3:** `_chunk_node` is `null` after the completion frame (either `queue_free()` was called or it was already null/invalid). Verified by: `player._chunk_node == null or not is_instance_valid(player._chunk_node)`.

- **AC-64.4:** HP restoration formula: `result_hp = minf(max_hp, prior_hp_at_recall + hp_cost_per_detach)`.
  - Example A: `max_hp = 100.0`, `hp_cost_per_detach = 25.0`, HP after detach = `75.0` → restored HP = `minf(100.0, 75.0 + 25.0) = minf(100.0, 100.0) = 100.0`.
  - Example B: `max_hp = 100.0`, `hp_cost_per_detach = 25.0`, starting HP = `90.0`, HP after detach = `max(0.0, 90.0 - 25.0) = 65.0` → restored HP = `minf(100.0, 65.0 + 25.0) = minf(100.0, 90.0) = 90.0` (HP-neutral, returns to pre-detach value).
  - Example C: `max_hp = 100.0`, `hp_cost_per_detach = 25.0`, starting HP = `100.0` (max), HP after detach = `75.0` → restored HP = `minf(100.0, 75.0 + 25.0) = 100.0` (HP-neutral at max).

- **AC-64.5:** The single-detach-plus-recall cycle is HP-neutral when starting at `max_hp`: `current_hp` before detach equals `current_hp` after recall, provided starting HP equals `max_hp`.

- **AC-64.6:** The single-detach-plus-recall cycle is HP-neutral when starting below `max_hp`: `current_hp` before detach equals `current_hp` after recall, provided `starting_hp - hp_cost_per_detach >= min_hp`.

- **AC-64.7:** HP restoration is capped at `max_hp`. Recall cannot raise HP above `max_hp`. Verified by: `_current_state.current_hp <= _simulation.max_hp` after recall completes (given standard operating conditions).

- **AC-64.8:** `simulate()` is called and produces its normal velocity output before the reabsorption block runs. Horizontal velocity and jump behavior are unaffected by reabsorption on the completion frame.

- **AC-64.9:** After reabsorption, `_current_state.has_chunk == true`. A subsequent detach press (next frame) is again routed to the detach path (not recall), because `prev_has_chunk == true` on that frame.

### 3. Risk & Ambiguity Analysis

- **Risk R-64.1 — "prior HP at recall" vs. "HP at detach time":** The HP restoration formula adds back `hp_cost_per_detach` to the HP at the moment of recall completion, not to the HP at the moment of detach. If no other HP modification occurs between detach and recall, these are equivalent. If a future system modifies HP during the recall window (e.g., damage taken), the restored HP would be relative to the modified value. This spec does not address such interactions, which are out of scope for M1-007.

- **Risk R-64.2 — queue_free guard order:** The spec requires `queue_free()` to be guarded before calling it but `_chunk_node = null` unconditionally after. An implementation that only nulls `_chunk_node` without calling `queue_free()` would leak the node from the scene tree. The guard must call `queue_free()` when the node is valid, then null the reference.

- **Risk R-64.3 — minf vs min:** `minf()` is the GDScript built-in for float minimum. Using `min()` with float arguments also works in GDScript 4, but `minf()` is semantically precise and matches the spec intent.

### 4. Clarifying Questions

None. The reabsorption formula and operation ordering are fully specified by the ticket context and the existing implementation. No further clarification is required.

---

## Requirement SPEC-65: Chunk Destroyed Mid-Recall

### 1. Spec Summary

- **Description:** If the `_chunk_node` becomes null or invalid while `_recall_in_progress == true` (before the timer reaches `_RECALL_TRAVEL_TIME`), the recall is cancelled without restoring HP or reattaching the chunk.

  The cancellation check runs on every `_physics_process(delta)` frame while `_recall_in_progress == true`. The check is evaluated before the timer completion check (`_recall_timer >= _RECALL_TRAVEL_TIME`), so a chunk destroyed on the completion frame also results in cancellation (not completion).

  Cancellation effects:
  - `_recall_in_progress` is set to `false`.
  - `_recall_timer` is NOT reset (it retains its accumulated value but is irrelevant after cancellation).
  - `_current_state.has_chunk` remains `false` (the chunk is gone; the player does not regain it).
  - `_current_state.current_hp` is NOT restored (the HP cost from the original detach is permanent when the chunk is destroyed).
  - `_chunk_node` remains whatever it was set to by external code (either `null` or an invalid freed reference). The cancellation block does not modify `_chunk_node`.

  The cancellation guard is: `if _chunk_node == null or not is_instance_valid(_chunk_node): _recall_in_progress = false`.

- **Constraints:**
  1. The cancellation check occurs inside the `if _recall_in_progress:` block, before the `elif _recall_timer >= _RECALL_TRAVEL_TIME:` completion block.
  2. The check covers both `== null` (reference explicitly cleared) and `not is_instance_valid()` (reference exists but node is freed).
  3. On the frame that cancellation occurs, `simulate()` has already been called normally (no special handling by the simulation layer).
  4. Cancellation does not produce any side effects beyond setting `_recall_in_progress = false`. No signals are emitted, no animations are stopped.
  5. After cancellation, the player is in state: `has_chunk == false`, `_chunk_node == null` (or invalid), `_recall_in_progress == false`. This is the same state as if a chunk had been destroyed before recall was initiated.

- **Assumptions:**
  1. External chunk destruction refers to any mechanism that calls `queue_free()` on `_chunk_node` from outside `player_controller.gd` (e.g., a kill zone script, physics body out-of-bounds detection, or test code directly calling `queue_free()`). In all such cases, `is_instance_valid()` will return `false` on the next or same frame.
  2. In test code that manually sets `player._chunk_node = null`, the `null` check (`_chunk_node == null`) immediately triggers cancellation on the next `_physics_process` call.

- **Scope / Context:** Applies to the cancellation guard within the `if _recall_in_progress:` block of `_physics_process(delta)` in `player_controller.gd`.

### 2. Acceptance Criteria

- **AC-65.1:** When `_chunk_node` becomes `null` during an active recall (`_recall_in_progress == true`), the recall is cancelled on the next `_physics_process` call: `_recall_in_progress` becomes `false`.

- **AC-65.2:** When `_chunk_node` has been freed (via `queue_free()`) and `is_instance_valid(_chunk_node) == false` during an active recall, the recall is cancelled on the next `_physics_process` call: `_recall_in_progress` becomes `false`.

- **AC-65.3:** After cancellation, `_current_state.has_chunk` remains `false`. The chunk is not reattached.

- **AC-65.4:** After cancellation, `_current_state.current_hp` is not restored. It retains the reduced value from the original detach.
  - Example: `max_hp = 100.0`, `hp_cost_per_detach = 25.0`, HP after detach = `75.0`. Chunk destroyed during recall. After cancellation, `current_hp == 75.0` (not restored to `100.0`).

- **AC-65.5:** If the chunk is destroyed on the exact frame that `_recall_timer >= _RECALL_TRAVEL_TIME`, the cancellation check (evaluated first) takes priority: recall is cancelled, not completed. HP is not restored, `has_chunk` remains `false`.

- **AC-65.6:** After cancellation, `_recall_in_progress == false`. A subsequent `detach_just_pressed` event when a new chunk is present can initiate a fresh recall (i.e., cancellation does not permanently disable recall).

### 3. Risk & Ambiguity Analysis

- **Risk R-65.1 — Check ordering:** The cancellation guard must evaluate before the completion check (`>= _RECALL_TRAVEL_TIME`). If the order were reversed, a chunk destroyed on the completion frame would trigger reabsorption (HP restore, `has_chunk = true`) with a null or invalid `_chunk_node`. The guarded `queue_free()` in the reabsorption block would skip the call, but `has_chunk` would incorrectly be set to `true` without a live chunk. The implementation in `player_controller.gd` lines 262-264 correctly places the null/invalid check before the timer check.

- **Risk R-65.2 — Test code nulling _chunk_node directly:** In test scenarios, `player._chunk_node = null` is set directly (not via `queue_free()`). The cancellation guard checks `_chunk_node == null`, so this is correctly detected. Tests must step at least one more `_physics_process` frame after nulling `_chunk_node` to observe the cancellation effect.

- **Risk R-65.3 — Chunk freed by external call in same frame:** If external code calls `_chunk_node.queue_free()` during the same `_physics_process` call (e.g., a signal callback) between when recall sets `_recall_in_progress = true` and when the cancellation guard runs, Godot defers actual freeing to the end of the frame. `is_instance_valid()` may still return `true` on this frame. Cancellation would be detected on the NEXT frame. This is acceptable behavior.

### 4. Clarifying Questions

None. The cancellation behavior is fully specified by the ticket context. No further clarification is required.

---

## Requirement SPEC-66: Non-Blocking Movement During Recall

### 1. Spec Summary

- **Description:** While recall is in progress (`_recall_in_progress == true`), all movement and jump inputs continue to be processed normally by `MovementSimulation.simulate()` without any input-lock, velocity override, or speed penalty. The player can move, jump, wall-cling, and wall-jump during the recall travel window as if no recall were happening.

  This is guaranteed by the architecture: `simulate()` is called every `_physics_process(delta)` frame regardless of the recall state. The `_recall_in_progress` flag is not passed to `simulate()`, is not read by `simulate()`, and has no effect on the simulation's velocity computation.

  Additionally, `detach_just_pressed` is NOT passed as `true` on recall-subsequent frames (i.e., frames after the recall was initiated but before it completes). During those frames, `Input.is_action_just_pressed("detach")` returns `false` (the key press was a single event on the initiation frame; subsequent frames see the key held or released, not just-pressed). This means `simulate()` receives `detach_just_pressed = false` on non-initiation recall frames, so the simulation's detach step (step 17) evaluates `detach_eligible = false` and produces no state change for `has_chunk`.

- **Constraints:**
  1. No new input-lock flag is introduced in `movement_simulation.gd` or `player_controller.gd` for M1-007.
  2. `simulate()` is called exactly once per `_physics_process(delta)` frame, before the recall advancement block. This ordering is unchanged from M1-006 and prior tickets.
  3. `move_and_slide()` is called exactly once per `_physics_process(delta)` frame, after `simulate()`, applying the computed velocity. This is unchanged.
  4. The `_recall_in_progress` flag must not be used as any sort of velocity multiplier, speed cap, or movement gate within `_physics_process(delta)`.

- **Assumptions:**
  1. The player has valid physics geometry (floor or air) available during recall travel for movement inputs to have effect.
  2. Holding `move_right` during recall will produce positive horizontal velocity growth via `simulate()`'s acceleration formula, same as outside of recall.

- **Scope / Context:** Applies to the entire `_physics_process(delta)` function in `player_controller.gd`. No changes to `movement_simulation.gd`.

### 2. Acceptance Criteria

- **AC-66.1:** While `_recall_in_progress == true`, holding `move_right` produces positive `velocity.x` in `player._current_state.velocity` (or `player.velocity` post-slide). Holding `move_left` produces negative `velocity.x`. These are the same results as in non-recall frames.

- **AC-66.2:** While `_recall_in_progress == true`, releasing all horizontal input causes `velocity.x` to decelerate toward 0.0 via the friction/air-deceleration formula. No instant velocity zeroing occurs.

- **AC-66.3:** While `_recall_in_progress == true` on the ground, a jump input produces the same upward impulse as a normal jump. The jump is not disabled, reduced, or delayed.

- **AC-66.4:** `simulate()` receives the same 8 arguments on recall frames as on non-recall frames: `prior_state`, `input_axis` (from horizontal input), `jump_pressed`, `jump_just_pressed`, `is_on_wall`, `wall_normal_x`, `detach_just_pressed` (from current frame's `is_action_just_pressed`, typically `false` on frames after initiation), `delta`.

- **AC-66.5:** On the recall initiation frame, after `simulate()` runs with `detach_just_pressed = true` and `prior_state.has_chunk = false`, the result has `has_chunk = false` (carry-forward in simulate, since `detach_eligible = false`) and normal velocity output. Horizontal velocity is not zeroed by the recall initiation.

- **AC-66.6:** The `_recall_in_progress` flag is not read by `simulate()` at any point. It does not appear in `movement_simulation.gd`. Verified by: `godot --headless --check-only` on the codebase; `movement_simulation.gd` does not contain the string `_recall_in_progress`.

### 3. Risk & Ambiguity Analysis

- **Risk R-66.1 — detach_just_pressed on recall frames:** On the recall initiation frame, `detach_just_pressed = true` is passed to `simulate()`. Because `prior_state.has_chunk == false` on that frame, the simulation's detach step is a no-op (`detach_eligible = false`). This is not a bug; it is the intentional design described in SPEC-62, AC-62.6.

- **Risk R-66.2 — Rapid re-press during recall:** If the player releases and re-presses E during recall (producing a new `is_action_just_pressed` = true), the second press is routed to the recall no-op path (AC-62.4: `_recall_in_progress == true` suppresses a second recall initiation). The `detach_just_pressed = true` is still passed to `simulate()`, but `detach_eligible = false` because `has_chunk == false`. Movement is unaffected.

### 4. Clarifying Questions

None. Non-blocking behavior is guaranteed by the architectural separation between controller and simulation. No further clarification is required.

---

## Requirement SPEC-67: HP Restoration Formula

### 1. Spec Summary

- **Description:** On the recall completion frame (SPEC-64), `_current_state.current_hp` is updated via the formula:

  ```
  _current_state.current_hp = minf(_simulation.max_hp, _current_state.current_hp + _simulation.hp_cost_per_detach)
  ```

  This formula has the following properties:

  1. **Additive restoration:** It adds `hp_cost_per_detach` back to the current HP — the same amount that was subtracted on the detach frame by `simulate()`.
  2. **Upper-bound cap:** `minf()` prevents the restored value from exceeding `max_hp`. Recall cannot be used as an HP source that increases HP beyond the maximum.
  3. **HP-neutral cycle:** A single detach+recall cycle starting from `max_hp` is HP-neutral:
     - Before detach: `hp = max_hp`.
     - After detach: `hp = max(min_hp, max_hp - cost)`.
     - After recall: `hp = minf(max_hp, (max_hp - cost) + cost) = minf(max_hp, max_hp) = max_hp`. Net change: 0.
  4. **HP-neutral cycle from below max_hp:** A single detach+recall cycle starting from `starting_hp < max_hp` (where `starting_hp - cost >= min_hp`):
     - After detach: `hp = starting_hp - cost`.
     - After recall: `hp = minf(max_hp, (starting_hp - cost) + cost) = minf(max_hp, starting_hp) = starting_hp` (since `starting_hp < max_hp`). Net change: 0.
  5. **Farm prevention:** Repeated detach+recall cycles starting from `max_hp` never increase HP above `max_hp`. `minf(max_hp, max_hp)` always equals `max_hp`.

  The formula is applied to `_current_state` (the controller's persistent state), not to `next_state` (the output of `simulate()`). It reads:
  - `_current_state.current_hp` as the "prior HP at recall moment"
  - `_simulation.hp_cost_per_detach` as the amount to restore
  - `_simulation.max_hp` as the cap

- **Constraints:**
  1. The formula uses `minf()` (GDScript's `float`-specific minimum). The argument order is `minf(_simulation.max_hp, _current_state.current_hp + _simulation.hp_cost_per_detach)`.
  2. The formula reads `_current_state.current_hp` (the HP value at the moment of reabsorption) — NOT the HP value at the time the chunk was detached.
  3. `max_hp` is not enforced by `simulate()`. It is only enforced here (in the recall completion block) as an upper-bound cap.
  4. If the detach formula (SPEC-56) applied `min_hp` clamping (i.e., HP went to `min_hp` because the cost exceeded the remaining HP), then restoration adds `hp_cost_per_detach` back to `min_hp`. Example: `starting_hp = 10.0`, `cost = 25.0`, `min_hp = 0.0` → after detach: `hp = 0.0`. After recall: `hp = minf(100.0, 0.0 + 25.0) = 25.0`. This is NOT HP-neutral for sub-min cases — the player recovers more than they "lost" (they lost 10.0 HP to the floor, but recall restores 25.0). This is an accepted edge case for M1-007.
  5. HP restoration occurs exactly once per successful recall. It is not applied on cancelled recalls (SPEC-65) or on no-op recall attempts.

- **Assumptions:**
  1. Between detach and recall, `_current_state.current_hp` is not modified by any other mechanism. `simulate()` carries HP forward unchanged on non-detach frames (SPEC-57). If a future system damages the player during the recall window, the restored value will reflect the post-damage HP (not the pre-detach HP). This is a future-ticket concern.
  2. `hp_cost_per_detach` is the same value used during the detach frame. It is not changed between detach and recall (it is a configuration var, not a per-frame input).

- **Scope / Context:** Applies to the HP restoration assignment within the reabsorption block of `_physics_process(delta)` in `player_controller.gd`. Not in `movement_simulation.gd`.

### 2. Acceptance Criteria

- **AC-67.1:** Standard cycle (max_hp start): `max_hp = 100.0`, `hp_cost_per_detach = 25.0`, `starting_hp = 100.0`. After detach: `current_hp == 75.0`. After recall: `current_hp == 100.0`.

- **AC-67.2:** Below-max start: `max_hp = 100.0`, `hp_cost_per_detach = 25.0`, `starting_hp = 90.0`. After detach: `current_hp == 65.0`. After recall: `current_hp == 90.0` (HP-neutral, not raised above starting value).

- **AC-67.3:** Max-hp cap enforcement: `max_hp = 100.0`, `hp_cost_per_detach = 25.0`, if `_current_state.current_hp` were `80.0` at recall time (some hypothetical). `minf(100.0, 80.0 + 25.0) = minf(100.0, 105.0) = 100.0`. Result capped at `max_hp`.

- **AC-67.4:** Repeated cycles are not an HP farm: starting at `max_hp = 100.0`, performing N detach+recall cycles, `current_hp == 100.0` after each cycle (no net gain).

- **AC-67.5:** Custom cost: `max_hp = 100.0`, `hp_cost_per_detach = 10.0`, `starting_hp = 100.0`. After detach: `current_hp == 90.0`. After recall: `current_hp == minf(100.0, 90.0 + 10.0) = 100.0`. Formula uses the current configured `hp_cost_per_detach`, not a hardcoded `25.0`.

- **AC-67.6:** The formula does not enforce a lower-bound clamp: if `_current_state.current_hp + hp_cost_per_detach < 0.0` (theoretically impossible under normal operation but defensible), the result would be negative. The spec accepts this without additional clamping.

- **AC-67.7:** HP restoration is not applied on the recall initiation frame or on any intermediate recall frame — only on the completion frame (`_recall_timer >= _RECALL_TRAVEL_TIME`).

### 3. Risk & Ambiguity Analysis

- **Risk R-67.1 — Sub-min HP restoration inconsistency:** When the player's HP is clamped to `min_hp` on detach (because `starting_hp - cost < min_hp`), the restoration formula adds back the full `hp_cost_per_detach`, not the actual HP that was lost. This means restoration may overshoot in these cases (e.g., starting at 10 HP, cost 25, clamped to 0, restored to `minf(max_hp, 0 + 25) = 25`). This is documented as an accepted edge case and is not addressed in M1-007.

- **Risk R-67.2 — minf argument order:** `minf(max_hp, current_hp + cost)` is the correct order. `minf(current_hp + cost, max_hp)` is mathematically equivalent but does not match the spec literal. The spec prescribes the exact argument order for readability.

### 4. Clarifying Questions

None. The formula is explicitly defined in the ticket context and the existing implementation. No further clarification is required.

---

## Requirement SPEC-68: Visual Placeholder — Chunk Visible During Recall Travel

### 1. Spec Summary

- **Description:** During the recall travel window (`_recall_in_progress == true`, `_recall_timer < _RECALL_TRAVEL_TIME`), the `_chunk_node` remains present in the scene tree and is visible at its last physics position. It is not animated, not moved toward the player, and not faded. The chunk simply sits in place until `queue_free()` is called on the completion frame.

  This behavior satisfies the ticket acceptance criterion: "Tendril visibly stretches then snaps (or minimal visual feedback if placeholder)". The parenthetical permits a placeholder. The chunk remaining visible for ~0.25 seconds before instant removal constitutes "minimal visual feedback" for Milestone 1.

  No additional visual effects are required for M1-007:
  - No `Line2D` tendril between player and chunk.
  - No `Tween` or `AnimationPlayer` controlling chunk scale or position.
  - No shader effect on the chunk during recall.
  - No UI indicator that recall is in progress.

  This decision is formally logged in CHECKPOINTS.md ([M1-007] Planner — tendril visual: placeholder acceptable or must be visible?).

- **Constraints:**
  1. `_chunk_node` must remain a valid, scene-tree-active node during the recall travel window. The controller must not call `queue_free()` until the completion frame.
  2. The chunk is positioned at the world-space location where it was when the player pressed E to initiate recall. The controller does not move it toward the player during travel.
  3. On the completion frame, `queue_free()` is called on `_chunk_node` (or skipped if it was already destroyed). The removal is instant: no fade or death animation.
  4. If a human reviewer determines after the fact that an animated tendril is required (rather than the chunk-static placeholder), this must be filed as a separate ticket and does not block M1-007 completion.

- **Assumptions:**
  1. The `_chunk_node` is a `RigidBody2D`. During the recall travel window, it is subject to normal physics (gravity, collision). This means the chunk may move due to physics during the travel window. The spec accepts this behavior: the chunk is not "frozen" in place.
  2. The `_CHUNK_SCENE` and the `chunk.tscn` scene have appropriate visual representation (sprite or placeholder mesh) that makes the chunk visible to the human reviewer.

- **Scope / Context:** Applies to the behavior of `_chunk_node` during `_recall_in_progress == true` in `player_controller.gd`. No changes to `chunk.tscn`, no new scene files, no new scripts.

### 2. Acceptance Criteria

- **AC-68.1:** During the recall travel window (frames between recall initiation and completion), `_chunk_node` is non-null and `is_instance_valid(_chunk_node) == true` (absent external destruction).

- **AC-68.2:** The controller does not call `_chunk_node.queue_free()` or modify `_chunk_node.visible`, `_chunk_node.position`, or any other `_chunk_node` property during the recall travel window (prior to the completion frame).

- **AC-68.3:** On the completion frame, `_chunk_node.queue_free()` is called (subject to the validity guard). After the completion frame, the chunk is removed from the scene tree.

- **AC-68.4:** The tick count (frames) in which the chunk is visible during recall is `floor(_RECALL_TRAVEL_TIME / delta)` + 1 frames (approximately 16 frames at 60 FPS), consistent with the timer accumulation described in SPEC-63.

- **AC-68.5:** No `Line2D` node, no tendril visual, no animation player, and no tween is created or modified by the recall system in M1-007.

### 3. Risk & Ambiguity Analysis

- **Risk R-68.1 — Human reviewer rejection:** The "minimal visual feedback" interpretation may be rejected by the human reviewer during in-editor play-testing. If so, a new ticket must be created for tendril animation. M1-007 is not blocked by this potential future decision.

- **Risk R-68.2 — Chunk physics during travel:** Because `_chunk_node` is a `RigidBody2D` and physics continue during recall, the chunk may slide, fall, or roll during the ~0.25s travel window. This is acceptable for a placeholder. If the chunk falls into a kill volume during this window, SPEC-65 (cancellation) handles the case.

### 4. Clarifying Questions

None. The placeholder decision is formally logged in CHECKPOINTS.md. No further clarification is required.

---

## Requirement SPEC-69: No Changes to `movement_simulation.gd`

### 1. Spec Summary

- **Description:** `movement_simulation.gd` — including its `MovementState` inner class, all configuration variables, and the `simulate()` function — is unchanged by M1-007. No new fields are added to `MovementState`. No new parameters are added to `simulate()`. No new configuration variables are added to `MovementSimulation`. No existing field, parameter, or formula is modified.

  This constraint is established by the architectural boundary defined in SPEC-47: `simulate()` never sets `result.has_chunk = true`. The `has_chunk` false→true transition is the exclusive responsibility of `player_controller.gd` after the recall timer fires. This boundary is preserved by M1-007.

  All recall logic (timer, cancellation guard, HP restoration, chunk freeing, `has_chunk` restoration) is implemented in `player_controller.gd`. The simulation layer remains a pure, engine-agnostic, 8-argument function that computes velocity and state from input.

- **Constraints:**
  1. `simulate()` signature remains: `func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, is_on_wall: bool, wall_normal_x: float, detach_just_pressed: bool, delta: float) -> MovementState:` (8 arguments, unchanged from SPEC-49 / M1-005).
  2. `MovementState` fields remain exactly: `velocity: Vector2`, `is_on_floor: bool`, `coyote_timer: float`, `jump_consumed: bool`, `is_wall_clinging: bool`, `cling_timer: float`, `has_chunk: bool`, `current_hp: float`. No 9th field is added.
  3. The 18-step normative order-of-operations comment block at the top of `simulate()` is unchanged.
  4. The spec coverage comment at the top of `movement_simulation.gd` is not updated to add M1-007 SPEC numbers (because no code in the file changes).
  5. All existing call-sites of `simulate()` in `player_controller.gd` and all test files remain valid without any argument changes.

- **Assumptions:**
  1. The `_recall_in_progress` flag, `_recall_timer`, and `_RECALL_TRAVEL_TIME` are members of `PlayerController` only. They are not visible to, readable by, or writable by `MovementSimulation`.
  2. Future tickets (e.g., chunk physics interactions, tendril animation) may extend `movement_simulation.gd`. Such extensions are out of scope for M1-007.

- **Scope / Context:** Applies to the entire `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd` file. The file must be byte-for-byte identical before and after M1-007 implementation (subject to whitespace normalization).

### 2. Acceptance Criteria

- **AC-69.1:** `movement_simulation.gd` contains no reference to `_recall_in_progress`, `_recall_timer`, or `_RECALL_TRAVEL_TIME`. Verified by text search: these strings do not appear anywhere in the file.

- **AC-69.2:** The `simulate()` function has exactly 8 parameters after M1-007. Verified by reading the function declaration line.

- **AC-69.3:** `MovementState` has exactly 8 fields after M1-007: `velocity`, `is_on_floor`, `coyote_timer`, `jump_consumed`, `is_wall_clinging`, `cling_timer`, `has_chunk`, `current_hp`.

- **AC-69.4:** All pre-existing tests that call `simulate()` continue to pass with zero regressions after M1-007. No call-site migration is required.

- **AC-69.5:** `godot --headless --check-only` passes on `movement_simulation.gd` with no errors or warnings after M1-007.

- **AC-69.6:** `simulate()` does not set `result.has_chunk = true` on any code path. The `has_chunk` field in a freshly allocated `MovementState` starts as `true` by its default initializer, but `simulate()` never explicitly assigns `true` to `result.has_chunk`. The only assignments to `result.has_chunk` in `simulate()` are: (a) `result.has_chunk = false` on detach frames; (b) `result.has_chunk = prior_state.has_chunk` on non-detach frames.

### 3. Risk & Ambiguity Analysis

- **Risk R-69.1 — Inadvertent modification:** An implementer fixing the 12 failing tests might incorrectly attempt to add a new `MovementState` field or `simulate()` parameter to support recall. The spec explicitly prohibits this. Any such change is out of scope for M1-007 and must be reverted.

- **Risk R-69.2 — Stale SPEC coverage comment:** If `movement_simulation.gd` is accidentally modified to add M1-007 coverage comments without code changes, the "unchanged" invariant is still satisfied at the behavioral level. However, the spec coverage comment must only reference spec numbers for which code changes were made. No M1-007 spec numbers should appear in the coverage comment.

### 4. Clarifying Questions

None. The unchanged constraint is fully established by the ticket context and CHECKPOINTS.md. No further clarification is required.

---

## Requirement SPEC-70: Headless Testability Pattern

### 1. Spec Summary

- **Description:** `player_controller.gd` uses `Input.is_action_just_pressed("detach")` to detect recall input. In a headless test environment where `_physics_process(delta)` is called directly (without a running SceneTree main loop dispatching input events), `Input.is_action_just_pressed()` may not correctly reflect a freshly simulated key press.

  The existing test helper `_recall_once()` (in both test files) uses `Input.action_press("detach")` followed by `controller._physics_process(delta)` followed by `Input.action_release("detach")`. This pattern relies on `action_press` registering the action as "just pressed" within the single `_physics_process` call, which is the correct pattern for Godot 4 headless testing.

  However, investigations by prior agents (CHECKPOINTS.md [M1-007] Planner — test failures root cause) identified that several tests fail due to:

  1. **Insufficient frame count:** Tests that call `_recall_once()` then `_step_player(player, 10, 0.016)` only accumulate 0.176s total, which is below the 0.25s threshold. The fix is to use at least 15 additional frames (total ≥16 frames) or a larger delta value.

  2. **Input action routing conflict:** When `_recall_once()` is called with `has_chunk == true`, `Input.action_press("detach")` causes `simulate()` to detach the chunk (not a recall). This happens in `tb_cr_005` where the test presses "detach" without first detaching, causing a detach (HP cost) rather than a recall no-op.

  The following patterns are approved for headless controller-level recall tests:

  **Pattern A (Preferred — input simulation):**
  ```
  Input.action_press("detach")
  controller._physics_process(delta)
  Input.action_release("detach")
  ```
  This is the established `_recall_once()` pattern. It correctly simulates a single-frame detach press because Godot's `Input.action_press()` makes `is_action_just_pressed()` return `true` for one frame.

  **Pattern B (Direct state injection for timer-bypass tests):**
  ```
  player._recall_in_progress = true
  player._recall_timer = 0.0
  ```
  Direct state injection bypasses the input routing layer and is appropriate for tests that focus on timer-driven behavior (e.g., verifying that HP is restored after exactly 0.25s of timer accumulation) rather than on the input-triggered recall initiation.

  **Pattern C (Large delta for single-frame completion):**
  ```
  _recall_once(player, 0.25)
  ```
  Using delta = 0.25 causes the recall to initiate and complete within the same `_physics_process` call (since 0.0 + 0.25 = 0.25 >= `_RECALL_TRAVEL_TIME`). This is appropriate for tests that only care about the final state after recall, not the intermediate state during travel.

  **Anti-patterns to avoid:**
  - Calling `_recall_once()` when `_current_state.has_chunk == true`: this triggers a detach, not a recall. Correct sequence: detach first, then recall.
  - Calling `_step_player(player, 10, 0.016)` after recall initiation at 60 FPS: insufficient (0.176s < 0.25s). Use ≥15 additional frames or a larger delta.

- **Constraints:**
  1. Tests must always call `Input.action_release("detach")` after a simulated press, before the next `_physics_process` call, to prevent the action from being held across frames (which would not trigger `is_action_just_pressed` again).
  2. Pattern B (direct state injection) should only be used when the test's subject is the timer behavior, not the input routing. Tests that use Pattern B cannot verify that the input routing correctly initiates recall.
  3. Pattern C (large delta) is acceptable for recall-completion tests. Tests using Pattern C must not assume the chunk is visible during a travel window (the travel window is effectively zero duration).

- **Assumptions:**
  1. Godot 4's `Input.action_press()` simulates a "just pressed" state that `Input.is_action_just_pressed()` correctly detects in the immediately following call.
  2. The test runner (`run_tests.gd`) invokes test classes' `run_all()` methods in a single-threaded headless environment without a running game loop.
  3. All test class instances and scene instances are manually managed (instantiated, run, and freed by test methods).

- **Scope / Context:** Applies to `tests/test_chunk_recall_simulation.gd` and `tests/test_chunk_recall_simulation_adversarial.gd`. These are the only files that test recall at the controller level.

### 2. Acceptance Criteria

- **AC-70.1:** Tests that use `_recall_once()` (Pattern A) and then need recall to complete must call `_step_player(player, N, 0.016)` with N ≥ 15 additional frames (or equivalent delta accumulation ≥ 0.234s remaining after the initiation frame) to ensure `_recall_timer >= 0.25`.

- **AC-70.2:** Tests that call `_recall_once()` must do so only after `_current_state.has_chunk == false` and `_chunk_node != null`. If called when `has_chunk == true`, the press triggers a detach (not a recall), invalidating the test scenario.

- **AC-70.3:** Tests that use Pattern B (direct state injection) must set both `_recall_in_progress = true` and `_recall_timer = 0.0` together, then call `_step_player()` with sufficient delta to complete the timer.

- **AC-70.4:** `_cleanup_input()` must be called before each `_recall_once()` or `_detach_once()` call to release any previously held actions and ensure clean per-frame input state.

- **AC-70.5:** The `_recall_once()` helper (in both test files) must call `Input.action_release("detach")` after `controller._physics_process(delta)`. This is already the pattern in the current implementation; any modified version must preserve it.

- **AC-70.6:** Tests r5 and r6 in `test_chunk_recall_simulation.gd` must use at least 16 total `_physics_process` calls (including the recall initiation call) to verify HP restoration after recall. The current `_step_player(player, 10, 0.016)` call (which produces only 0.176s) must be replaced with `_step_player(player, 20, 0.016)` or equivalent to ensure timer completion.

- **AC-70.7:** Test `tb_cr_005` in `test_chunk_recall_simulation_adversarial.gd` must exercise the no-op recall scenario (pressing "detach" when `has_chunk == false` and `_chunk_node == null`) rather than the scenario where `has_chunk == true`. The test setup must reach `has_chunk == false` with `_chunk_node == null` before pressing "detach".

### 3. Risk & Ambiguity Analysis

- **Risk R-70.1 — Input.action_press timing in headless Godot 4:** The behavior of `Input.action_press()` in headless mode with direct `_physics_process()` calls (without `_process()`) has been empirically identified as working for some tests but unreliable for others. If Pattern A fails despite correct frame sequencing, Pattern B (direct state injection) should be used as the fallback for input-routing tests.

- **Risk R-70.2 — test_r2 failure root cause:** `test_r2` uses 60 `_step_player` frames (~1 second) after `_recall_once()`, which is more than sufficient for timer completion. If r2 still fails after the frame-count fix for r5/r6 is applied, the root cause is likely the `Input.action_press` not correctly triggering `is_action_just_pressed` on the `_recall_once` frame. In that case, Pattern B or a two-frame approach (press on one frame, process on the next) should be investigated.

- **Risk R-70.3 — tb_cr_001 through tb_cr_004 and tb_cr_006:** These adversarial tests use `_recall_once()` and `_step_player()` patterns similar to r5/r6. They may be failing because recall is never initiated (if `_recall_once()` is not correctly triggering `is_action_just_pressed`). The Engine Integration Agent must verify whether the root cause is the frame count, the input detection, or both.

### 4. Clarifying Questions

None. The root causes are documented in CHECKPOINTS.md. The Engine Integration Agent is responsible for diagnosing the exact failure mode and selecting the appropriate fix pattern. No design decisions remain unresolved for the spec.

---

## Non-Functional Requirements

The following non-functional constraints apply to the M1-007 implementation as a whole.

### NFR-70.A: Typed GDScript Throughout

**Description:** All code in M1-007 scope uses GDScript static typing. Member variables, local variables in `_physics_process()`, and test file variables must have explicit type annotations where a type can be determined.

**Acceptance Criteria:**
- `var _recall_in_progress: bool = false` — typed.
- `var _recall_timer: float = 0.0` — typed.
- `const _RECALL_TRAVEL_TIME: float = 0.25` — typed.
- Any local variable introduced in the recall block of `_physics_process()` is typed.

### NFR-70.B: No Movement Math in `player_controller.gd`

**Description:** The recall system does not introduce any velocity computation, movement formula, or physics calculation in `player_controller.gd`. The HP restoration formula (`minf()`) is controller-level HP bookkeeping, not movement math. The `_recall_timer += delta` accumulation is a timing mechanism, not movement math. Neither violates this constraint.

**Acceptance Criteria:**
- `player_controller.gd` does not contain any new horizontal or vertical velocity computation beyond the existing `simulate()` call.
- No `move_toward`, `lerp`, or spring-physics formula is added to `player_controller.gd` for recall homing.

### NFR-70.C: Frame-Rate Independence

**Description:** The recall mechanic is frame-rate independent. The timer uses real elapsed time (`_recall_timer += delta`) rather than frame counts. Recall completes in approximately 0.25 seconds of real time regardless of frame rate.

**Acceptance Criteria:**
- At 30 FPS (delta ≈ 0.033): recall completes in ~8 frames (8 * 0.033 = 0.264s ≥ 0.25s).
- At 60 FPS (delta ≈ 0.016): recall completes in ~16 frames (16 * 0.016 = 0.256s ≥ 0.25s).
- At 120 FPS (delta ≈ 0.008): recall completes in ~32 frames (32 * 0.008 = 0.256s ≥ 0.25s).

### NFR-70.D: No New Test Files, No run_tests.gd Changes

**Description:** M1-007 does not introduce new test files. The existing `test_chunk_recall_simulation.gd` and `test_chunk_recall_simulation_adversarial.gd` are already registered in `run_tests.gd`. Only the content of these two files is modified (to fix the 12 failing tests).

**Acceptance Criteria:**
- `tests/run_tests.gd` is not modified by M1-007 (no new registrations).
- No new test files are created in `tests/`.
- All 12 currently failing tests in the two existing recall test files are fixed to pass.

---

## Summary Table

| SPEC | Subject | File(s) Affected | Key AC |
|------|---------|-----------------|--------|
| SPEC-62 | Recall input routing (dual-purpose detach action) | `player_controller.gd` | AC-62.1, AC-62.2, AC-62.3, AC-62.4, AC-62.5 |
| SPEC-63 | Recall timer and travel time (0.25s, frame-rate independent) | `player_controller.gd` | AC-63.1, AC-63.2, AC-63.3, AC-63.5, AC-63.8 |
| SPEC-64 | Reabsorption completion (5-step sequence, HP restore, has_chunk=true) | `player_controller.gd` | AC-64.1, AC-64.2, AC-64.3, AC-64.4, AC-64.5 |
| SPEC-65 | Chunk destroyed mid-recall (cancel without HP restore) | `player_controller.gd` | AC-65.1, AC-65.3, AC-65.4, AC-65.5 |
| SPEC-66 | Non-blocking movement during recall | `player_controller.gd` | AC-66.1, AC-66.4, AC-66.6 |
| SPEC-67 | HP restoration formula (minf, hp-neutral cycle, farm prevention) | `player_controller.gd` | AC-67.1, AC-67.2, AC-67.3, AC-67.4 |
| SPEC-68 | Visual placeholder — chunk visible during travel window | `player_controller.gd` | AC-68.1, AC-68.2, AC-68.3, AC-68.5 |
| SPEC-69 | No changes to `movement_simulation.gd` | `movement_simulation.gd` | AC-69.1, AC-69.2, AC-69.3, AC-69.5 |
| SPEC-70 | Headless testability pattern and known test failure fixes | `test_chunk_recall_simulation.gd`, `test_chunk_recall_simulation_adversarial.gd` | AC-70.1, AC-70.2, AC-70.6, AC-70.7 |
