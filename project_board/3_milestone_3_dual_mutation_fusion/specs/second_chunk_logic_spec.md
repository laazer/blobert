# Second Chunk Logic — Specification

**Ticket:** `project_board/3_milestone_3_dual_mutation_fusion/in_progress/second_chunk_logic.md`
**Epic:** Milestone 3 – Dual Mutation + Fusion
**Spec Author:** Spec Agent (via Autopilot)
**Date:** 2026-03-12

---

## Overview

Extend the chunk system to support a second, fully independent chunk. The second chunk follows the same detach/recall patterns as chunk 1, implemented via a new `has_chunk_2` field in `MovementState` and an extended `simulate()` signature. No mutation slot linkage is in scope; that belongs to `fusion_rules_and_hybrid.md`.

---

## SPEC-SCL-1 — `MovementState.has_chunk_2` field

**Requirement:** The `MovementState` inner class in `scripts/movement_simulation.gd` shall declare:

```gdscript
var has_chunk_2: bool = true
```

**Semantics:**
- `true` = chunk 2 is attached to the player (default state at game start)
- `false` = chunk 2 has been detached and is in the world
- Mirrors the existing `has_chunk: bool = true` field exactly (SPEC-46 pattern)

**Constraints:**
- The field must be declared in `MovementState`, not `MovementSimulation`
- Default value must be `true` (player starts with both chunks)
- The field is independent of `has_chunk`; any combination of `(has_chunk, has_chunk_2)` values is valid

---

## SPEC-SCL-2 — `has_chunk_2` default semantics and simulate() invariant

**Requirement:** `simulate()` shall never set `has_chunk_2 = true`. The only paths that restore `has_chunk_2` to `true` are external to `simulate()` (i.e., the `PlayerController3D` sets `has_chunk_2 = true` on recall completion).

**`simulate()` behavior for `has_chunk_2`:**
- If `detach_2_eligible` is true → `result.has_chunk_2 = false`
- Otherwise → `result.has_chunk_2 = prior_state.has_chunk_2` (carry-forward)

**Mirrors:** SPEC-47 (has_chunk carry-forward pattern)

---

## SPEC-SCL-3 — Detach step 2 (step 19 in simulate())

**Requirement:** After the existing HP reduction step (step 18), `simulate()` shall execute a chunk-2 detach step:

```
Step 19: Chunk 2 detach
  detach_2_eligible = detach_2_just_pressed AND prior_state.has_chunk_2
  if detach_2_eligible:
    result.has_chunk_2 = false
  else:
    result.has_chunk_2 = prior_state.has_chunk_2
  Reads:  detach_2_just_pressed, prior_state.has_chunk_2
  Writes: result.has_chunk_2 only — no other fields affected
```

**Mirrors:** SPEC-48 (chunk 1 detach step pattern)

---

## SPEC-SCL-4 — `simulate()` 9-argument signature

**Requirement:** The `simulate()` function shall accept `detach_2_just_pressed: bool = false` as the **9th and final positional argument**, after `delta: float`:

```gdscript
func simulate(
    prior_state: MovementState,
    input_axis: float,
    jump_pressed: bool,
    jump_just_pressed: bool,
    is_on_wall: bool,
    wall_normal_x: float,
    detach_just_pressed: bool,
    delta: float,
    detach_2_just_pressed: bool = false
) -> MovementState:
```

**Rationale:** GDScript 4 requires all parameters with default values to appear after all required parameters. `delta: float` has no default and must precede `detach_2_just_pressed: bool = false`. Placing `detach_2_just_pressed` last preserves all existing 8-argument call sites without modification.

**Existing call sites:** All existing `simulate(...)` calls with 8 arguments continue to work. The 9th argument defaults to `false`, which means step 19 is always a no-op at existing call sites.

**Mirrors:** SPEC-49/SPEC-50 (detach_just_pressed extension pattern)

---

## SPEC-SCL-5 — HP reduction step 2 (step 20)

**Requirement:** After the chunk-2 detach step (step 19), `simulate()` shall execute an HP reduction step for chunk 2:

```
Step 20: HP reduction for chunk 2 detach
  if detach_2_eligible:
    result.current_hp = max(min_hp, result.current_hp - hp_cost_per_detach)
  else:
    result.current_hp = result.current_hp  (no change from step 18 output)
  Reads:  detach_2_eligible, result.current_hp (output of step 18), hp_cost_per_detach, min_hp
  Writes: result.current_hp only
```

**Key detail:** Step 20 reads `result.current_hp` (the output of step 18), not `prior_state.current_hp`. This means that if both chunk 1 and chunk 2 are detached on the same frame, the HP reductions are cumulative: the player pays `2 * hp_cost_per_detach`, clamped at `min_hp` after each deduction.

**Example with defaults (hp_cost_per_detach=25.0, min_hp=0.0, prior_hp=100.0):**
- Detach chunk 1 only: result.current_hp = 75.0
- Detach chunk 2 only: result.current_hp = 75.0
- Detach both same frame: after step 18 → 75.0; after step 20 → 50.0

**Mirrors:** SPEC-56/SPEC-58 (HP reduction formula pattern)

---

## SPEC-SCL-6 — Independence invariant

**Requirement:** `has_chunk` and `has_chunk_2` are fully independent state fields. All four combinations are valid at any time:

| has_chunk | has_chunk_2 | Meaning |
|---|---|---|
| true | true | Both chunks attached (start state) |
| false | true | Chunk 1 detached, chunk 2 attached |
| true | false | Chunk 1 attached, chunk 2 detached |
| false | false | Both chunks detached |

**Constraint:** No step in `simulate()` shall read `has_chunk` to determine `has_chunk_2` behavior or vice versa. They are strictly independent.

---

## SPEC-SCL-7 — `detach_2` input action

**Requirement:** The `detach_2` input action shall be registered in `project.godot` with:
- Key: Q
- `physical_keycode`: 81
- `unicode`: 113
- Same `deadzone: 0.5` format as the existing `detach` action (key E, physical_keycode 69)

**Routing:** In `PlayerController3D`, the `detach_2` action follows the same dual-mode routing as `detach`:
- If chunk 2 is attached (`has_chunk_2 == true`): pressing `detach_2` fires a detach
- If chunk 2 is detached (`has_chunk_2 == false`): pressing `detach_2` initiates a recall

**No conflict check:** Q is not used by any existing action in the current `project.godot`.

---

## SPEC-SCL-8 — `PlayerController3D` controller fields and API

**Requirement:** `scripts/player_controller_3d.gd` shall add:

### New fields
```gdscript
var _chunk_node_2: RigidBody3D = null       # null when chunk 2 is attached
var _recall_in_progress_2: bool = false      # true during chunk 2 recall travel
var _recall_timer_2: float = 0.0             # time elapsed during recall
```

### New signals
```gdscript
signal detach_2_fired(player_position: Vector3, chunk_position: Vector3)
signal recall_2_started(player_position: Vector3, chunk_position: Vector3)
signal chunk_2_reabsorbed(player_position: Vector3)
```

### New public method
```gdscript
func has_chunk_2() -> bool:
    return _chunk_node_2 == null
```

### Behavior contract
- `_chunk_node_2 == null` → chunk 2 is attached (initial state)
- `_chunk_node_2 != null` → chunk 2 is in the world
- On `detach_2` pressed with chunk 2 attached: instantiate chunk scene at lob position, set `_chunk_node_2`, set `_sim_state.has_chunk_2 = false`, emit `detach_2_fired`
- On `detach_2` pressed with chunk 2 detached: set `_recall_in_progress_2 = true`, emit `recall_2_started`
- Recall completes after `_recall_timer_2 >= recall_travel_time`: free `_chunk_node_2`, set `_chunk_node_2 = null`, restore HP, set `_sim_state.has_chunk_2 = true`, emit `chunk_2_reabsorbed`
- Both `_chunk_node` and `_chunk_node_2` may be non-null simultaneously (both chunks in world at same time)
- Recall timers `_recall_timer` and `_recall_timer_2` are fully independent

### Reuse
- Same lob parameters as chunk 1 (lob velocity, direction)
- Same recall travel time as chunk 1
- Same HP restoration formula as chunk 1
- Reuses `chunk_3d.tscn` scene (distinct visuals deferred to `visual_clarity_hybrid_state.md`)

---

## SPEC-SCL-9 — Non-functional requirements

- **No engine API in `simulate()`**: All changes to `movement_simulation.gd` must use only pure GDScript (no `Node`, `Input`, `get_tree()`, etc.)
- **Typed fields**: All new fields and parameters must have explicit GDScript type annotations
- **No dead code**: No unused variables, no commented-out code blocks
- **Zero regressions**: All existing tests in `tests/run_tests.gd` must continue to pass after implementation
- **Syntax check**: `timeout 120 godot --headless --check-only` must exit 0 after all changes

---

## Out of scope

- Mutation slot linkage for chunk 2 → `fusion_rules_and_hybrid.md`
- Distinct visual for chunk 2 → `visual_clarity_hybrid_state.md`
- HP restoration formula changes (uses existing chunk 1 formula)
- Scene state machine integration
