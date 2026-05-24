# Input Action Mapping Specification

**Ticket:** M11-03 — `03_input_action_mapping.md`  
**Milestone:** M11 Base Mutation Attacks (Prerequisite)  
**Spec revision:** 1  
**Spec exit type:** `generic`  
**Normative ID prefix:** `IAM-*`

---

## Document Summary

Freeze the **normative contract** for Godot `InputMap` action names, default keyboard bindings, per-`PlayerStateMachine.PlayerState` input permit rules, and **single-winner** consumption for mutually exclusive gameplay actions. Downstream M11 tickets (attack framework, mutation UX, settings UI) implement against this spec.

**Evidence sources (read-only for M11-03):**

| Asset | Path |
|-------|------|
| InputMap | `project.godot` `[input]` |
| Player input read (movement + detach + debug) | `scripts/player/player_controller_3d.gd` — `_read_player_input()` (PFO Step 0) |
| Infection / fusion input read | `scripts/infection/infection_interaction_handler.gd` — `_process()` |
| Gameplay FSM | `scripts/player/player_state_machine.gd`, `project_board/specs/player_state_machine_spec.md` |
| Physics frame order | `project_board/specs/player_physics_frame_order_spec.md` (PFO-2 Step 0) |

**Cross-references:**

- `project_board/specs/player_state_machine_spec.md` (PSM-*) — ten `PlayerState` values, derivation priority (ABSORB > MUTATE), DEAD terminal rules.
- `project_board/specs/player_physics_frame_order_spec.md` (PFO-2) — input read **before** `_player_state_machine.update(delta)`.
- M11-07 `to_update/07_attack_input_and_cooldown_framework.md` — consumes `attack` default binding frozen here.

---

## Deferred Boundary Statement

**In scope (M11-03):**

- This specification document only.
- Frozen `PlayerInputActionPolicy` **API contract** (pure `RefCounted`; no engine `Input` calls).
- Action catalog (current + planned), alias table, default bindings, state×action matrix, consumption rules, test strategy, edge cases.

**Out of scope (deferred; no edits in M11-03):**

- `project.godot` InputMap registration for planned actions (`attack`, `menu`).
- `PlayerController3D` wiring (`_read_player_input`, policy calls, state-gated polling).
- `InfectionInteractionHandler` migration from raw `Input.*` to policy-filtered actions.
- Rebinding UI / user settings persistence.
- Hold-to-float input (FLOAT state exists; float **input** is a later ticket).
- Attack cooldown framework implementation (M11-07).

**Implementation boundary:** First code ticket that adds `PlayerInputActionPolicy` and/or new InputMap entries must cite IAM-* IDs. M11-03 completion = spec AC + `spec_completeness_check.py --type generic` PASS + Test Designer RED tests (policy `.gd` may be absent).

---

## Test Strategy

| Tier | When | Location | What it proves |
|------|------|----------|----------------|
| **Spec completeness** | After Spec Agent | `python ci/scripts/spec_completeness_check.py project_board/specs/input_action_mapping_spec.md --type generic` | Required IAM sections present |
| **Runtime unit (primary)** | TEST_DESIGN+ | `tests/scripts/player/test_player_input_action_policy.gd` | `PlayerInputActionPolicy`: `is_action_permitted`, `normalize_action`, `resolve_consumed_actions` per matrix + consumption |
| **Runtime adversarial** | TEST_BREAK | `tests/scripts/player/test_player_input_action_policy_adversarial.gd` | Simultaneous `attack`+`absorb`+`infect`, DEAD/HURT deny-all, alias normalization, unknown action fail-closed, menu suppression |
| **InputMap integration** | Deferred impl | e.g. `tests/scripts/player/test_project_input_map_actions.gd` | `InputMap.has_action()` after `project.godot` updated |
| **Controller integration** | Deferred | — | Step 0 + handler use policy with live FSM state |
| **Regression** | Downstream COMPLETE | `timeout 300 ci/scripts/run_tests.sh` | Full suite green when policy + map land |

**Test realism:** Assert runtime policy API only. Do **not** assert markdown/spec prose. Instantiate via `PlayerInputActionPolicy.new()` without scene tree.

**Registration:** Both policy test files must be registered in `tests/run_tests.gd`.

**Representative test cases (non-exhaustive):**

- IDLE + `["attack","absorb"]` just-pressed edges → `resolve_consumed_actions` returns only `attack`.
- DEAD + any action → `is_action_permitted` false for all except `menu` (if ever permitted while dead — **denied** per IAM-5).
- `mutate` input normalized to `infect` before permit check.
- HURT + `jump` → not permitted.

---

## Edge Cases (Summary)

| ID | Case | Expected behavior |
|----|------|-------------------|
| EC-IAM-1 | Unknown action string | `is_action_permitted` → `false`; `normalize_action` → `""` or unchanged reject; never throw |
| EC-IAM-2 | `attack` + `absorb` + `infect` same frame (all permitted by state) | Single winner: `attack` (IAM-6) |
| EC-IAM-3 | `infect` + `absorb`, no `attack` | Winner: `infect` |
| EC-IAM-4 | `absorb` + `fuse`, no higher priority | Winner: `absorb` |
| EC-IAM-5 | `menu` just_pressed while `attack` pressed | Only `menu` in consumed set |
| EC-IAM-6 | DEAD state, any gameplay action | Denied; empty combat resolution |
| EC-IAM-7 | HURT state, movement keys | Denied (target M11 gating; matches matrix) |
| EC-IAM-8 | ABSORB state, `detach` just_pressed | Denied |
| EC-IAM-9 | `mutate` alias passed to API | Treated as `infect` |
| EC-IAM-10 | `swap_mutation` alias | Treated as `fuse` |
| EC-IAM-11 | `debug_kill` on release build | Always denied (`is_action_permitted` false) |
| EC-IAM-12 | `debug_kill` on debug build, IDLE | Permitted (does not participate in combat group) |
| EC-IAM-13 | `move_left` + `move_right` both held | Both permitted; axis merge is controller/sim responsibility, not policy |
| EC-IAM-14 | `detach` + `detach_2` same frame | Both may appear in consumed set (independent slots) |
| EC-IAM-15 | FLOAT state, `jump` | Permitted (exit float / wall-jump parity when float input lands) |
| EC-IAM-16 | MUTATE state, `fuse` | Denied (mutation mode locks meta actions) |
| EC-IAM-17 | Enemy movement root active (controller) | Controller zeroes axis/jump **before** policy; policy unchanged |
| EC-IAM-18 | Empty `actions_pressed` | `resolve_consumed_actions` → `[]` |

---

# Requirements

---

## Requirement IAM-1: Document Identity and Normative Vocabulary

### 1. Spec Summary

- **Description:** This file is the single source of truth for input action naming, bindings, state gating, and consumption for M11+ player gameplay.
- **Constraints:** Normative requirement IDs use prefix `IAM-*`. Action names in tables use **canonical InputMap string names** unless marked **alias**.
- **Assumptions:** Godot 4.x `InputMap` / `Input.is_action_*` APIs.
- **Scope:** Specification and `PlayerInputActionPolicy` contract only.

### 2. Acceptance Criteria

- **AC-IAM-1.1:** Spec declares `IAM-*` prefix and ticket M11-03 traceability.
- **AC-IAM-1.2:** Spec references `player_state_machine_spec.md` and `player_physics_frame_order_spec.md`.
- **AC-IAM-1.3:** All ten `PlayerStateMachine.PlayerState` enum members appear in the state-action matrix.

### 3. Risk & Ambiguity Analysis

- **R-IAM-1.1:** Split readers between ticket vocabulary (`mutate`) and InputMap (`infect`) — resolved in IAM-2 alias table.

### 4. Clarifying Questions

None.

---

## Requirement IAM-2: Action Catalog and Ticket Aliases

### 1. Spec Summary

- **Description:** Enumerate every gameplay input action: **registered today** in `project.godot`, **planned** for M11+, and **documentation aliases** from planner/ticket prose.
- **Constraints:** Canonical names are what `InputMap` and `PlayerInputActionPolicy` use after normalization. Aliases must not register duplicate InputMap entries in M11-03.
- **Assumptions:** No gamepad defaults in M11-03; keyboard defaults only.
- **Scope:** Catalog tables below.

### 2. Acceptance Criteria

- **AC-IAM-2.1:** Catalog lists exactly nine **current** InputMap actions with evidence in `project.godot`.
- **AC-IAM-2.2:** Catalog lists four **planned** actions: `attack`, `mutate` (alias), `swap_mutation` (alias), `menu` — with `attack` and `menu` as new InputMap names when implemented; `mutate` / `swap_mutation` alias-only until a future ticket splits names.
- **AC-IAM-2.3:** Alias table maps ticket → canonical as specified in IAM-2.3 table.
- **AC-IAM-2.4:** `debug_kill` flagged **debug-build only** (see IAM-10).

#### IAM-2.1 Current InputMap actions (`project.godot`)

| Canonical action | Category | Description | Read today |
|------------------|----------|-------------|------------|
| `move_left` | Movement (axis) | Horizontal intent −1 | `PlayerController3D._read_player_input` via `Input.get_axis` |
| `move_right` | Movement (axis) | Horizontal intent +1 | Same |
| `jump` | Movement (edge) | Jump press / buffer source | Same |
| `detach` | Chunk slot 0 | Detach chunk slot 0 | Same (`detach_just_pressed`) |
| `detach_2` | Chunk slot 1 | Detach chunk slot 1 | Same |
| `absorb` | Infection | Absorb weakened/infected enemy into mutation slot | `InfectionInteractionHandler._process` |
| `infect` | Infection | Apply infection to weakened target | Same |
| `fuse` | Fusion | Fuse two filled mutation slots | Same |
| `debug_kill` | Debug | Set player HP to `min_hp` | `PlayerController3D._read_player_input` when `OS.is_debug_build()` |

#### IAM-2.2 Planned M11 actions

| Name | Status | Canonical target | Notes |
|------|--------|------------------|-------|
| `attack` | **New InputMap entry (deferred)** | `attack` | Base mutation attack; M11-07 registers map + handler |
| `mutate` | **Alias only (M11-03)** | `infect` | Ticket/prose name; same binding as **F** today |
| `swap_mutation` | **Alias only (M11-03)** | `fuse` | Ticket/prose name; same binding as **G** today |
| `menu` | **New InputMap entry (deferred)** | `menu` | Pause / inventory / settings shell (behavior deferred) |

#### IAM-2.3 Alias normalization (normative)

| Ticket / docs name | Canonical action | Default key (see IAM-3) |
|--------------------|------------------|---------------------------|
| `mutate` | `infect` | F |
| `swap_mutation` | `fuse` | G |

`PlayerInputActionPolicy.normalize_action(name: StringName) -> StringName` must implement IAM-2.3. Unknown names pass through unchanged for catalog lookup; unknown canonical names fail closed (IAM-9).

### 3. Risk & Ambiguity Analysis

- **R-IAM-2.1:** Future ticket may introduce distinct `mutate` InputMap action — policy version bump or feature flag required; M11-03 alias table is frozen for M11 wave.

### 4. Clarifying Questions

None.

---

## Requirement IAM-3: Default Keyboard Bindings

### 1. Spec Summary

- **Description:** Default physical key bindings for all catalogued actions. Settings UI may override later; defaults must match current M1 where actions exist.
- **Constraints:** Document primary key + alternates where `project.godot` defines them.
- **Assumptions:** QWERTY; `physical_keycode` in project file is authoritative.
- **Scope:** Defaults table; implementation adds planned keys in a later ticket.

### 2. Acceptance Criteria

- **AC-IAM-3.1:** Current actions match `project.godot` `[input]` (A/Left, D/Right, Space, E, Q, R, F, G, K).
- **AC-IAM-3.2:** Planned `attack` default **J** (aligns M11-07; alternative **Z** noted as acceptable override in settings only, not dual default in map).
- **AC-IAM-3.3:** Planned `menu` default **Escape** (`KEY_ESCAPE` / physical 4194305).
- **AC-IAM-3.4:** Aliases `mutate` / `swap_mutation` inherit infect/fuse keys (F / G); no separate defaults.

#### IAM-3.1 Default bindings table

| Canonical action | Primary key | Alternate | InputMap today |
|------------------|-------------|-----------|----------------|
| `move_left` | A | Left arrow | Yes |
| `move_right` | D | Right arrow | Yes |
| `jump` | Space | — | Yes |
| `detach` | E | — | Yes |
| `detach_2` | Q | — | Yes |
| `absorb` | R | — | Yes |
| `infect` (`mutate`) | F | — | Yes |
| `fuse` (`swap_mutation`) | G | — | Yes |
| `debug_kill` | K | — | Yes (debug use only) |
| `attack` | **J** | — | **No** (deferred) |
| `menu` | **Escape** | — | **No** (deferred) |

### 3. Risk & Ambiguity Analysis

- **R-IAM-3.1:** J may conflict with future UI focus — acceptable for M11; document in M11-07 if changed.

### 4. Clarifying Questions

None.

---

## Requirement IAM-4: Input Phase in Physics Frame Order

### 1. Spec Summary

- **Description:** Align input polling with PFO-2: raw `InputMap` reads occur in **Step 0** (`_read_player_input()`), **before** Step 1 `_player_state_machine.update(delta)` and **before** Step 9 `sync_from_context`.
- **Constraints:** Policy uses gameplay state from **end of previous physics tick** (post–Step 9), i.e. `get_state()` at Step 0 reflects last frame’s derivation.
- **Assumptions:** M11-02 pipeline is implemented (numbered PFO-2 comments in `player_controller_3d.gd`).
- **Scope:** Integration contract for downstream wiring; no controller edits in M11-03.

### 2. Acceptance Criteria

- **AC-IAM-4.1:** Spec states Step 0 reads raw actions; Step 0.5 (future) applies `PlayerInputActionPolicy` with `state = _player_state_machine.get_state()` from previous frame.
- **AC-IAM-4.2:** Spec states `InfectionInteractionHandler` today polls in `_process` without FSM gating; **target** is poll in Step 0 or consume filtered edges from controller dictionary.
- **AC-IAM-4.3:** Enemy movement root suppression (`input_axis`, jump cleared) remains in controller Step 0 **before** policy (PFO-2.1).

#### IAM-4.1 Target Step 0 data flow (normative for implementers)

```text
Step 0a: Raw InputMap poll → edge set (just_pressed / held as needed)
Step 0b: Controller suppressions (enemy root, etc.)
Step 0c: policy.resolve_consumed_actions(state_prev, edges) → permitted edges
Step 0d: Build input Dictionary for movement/chunk/combat consumers
Steps 1–9: unchanged PFO-2 order
```

### 3. Risk & Ambiguity Analysis

- **R-IAM-4.1:** One-frame lag between kinematics and FSM state is intentional (PSM-10 runs Step 9); attack tickets must not read pre-sync stale state without documenting it.

### 4. Clarifying Questions

None.

---

## Requirement IAM-5: State–Action Permit Matrix

### 1. Spec Summary

- **Description:** For each `PlayerState`, define whether each canonical action is **permitted** (`true`) or **denied** (`false`) for `is_action_permitted(state, action)`. **○ Contextual** rows are permitted only when the listed predicate is true (predicates evaluated outside policy unless noted).
- **Constraints:** Matrix is **target M11 gating** (policy contract). **Current runtime** does not gate most actions by FSM (movement/detach ungated; infection handler ungated). Tests encode **target** behavior.
- **Assumptions:** `menu` permitted in all non-DEAD states; denied in DEAD. `debug_kill` per IAM-10.
- **Scope:** Full 10×N matrix.

### 2. Acceptance Criteria

- **AC-IAM-5.1:** Matrix covers all states: IDLE, WALK, JUMP, FALL, FLOAT, WALL_CLING, ABSORB, MUTATE, HURT, DEAD.
- **AC-IAM-5.2:** Matrix covers all canonical actions in IAM-2.1 plus `attack` and `menu`.
- **AC-IAM-5.3:** ABSORB and MUTATE rows deny movement, jump, chunk detach, combat, and infection actions except `menu`.
- **AC-IAM-5.4:** HURT and DEAD deny all gameplay actions; DEAD denies `menu`; HURT permits `menu` only.
- **AC-IAM-5.5:** FLOAT row documented separately from FALL (hold-to-float input deferred).

#### IAM-5.1 Legend

| Symbol | Meaning |
|--------|---------|
| ✓ | Permitted |
| ✗ | Denied |
| ○ | Permitted if predicate true |

**Predicates (evaluated by controller/handler, not policy):**

| ID | Predicate | Used for |
|----|-----------|----------|
| P-ABSORB | Target ESM in range and `can_absorb` | `absorb` |
| P-INFECT | Target ESM `weakened` | `infect` |
| P-FUSE | `can_fuse(slot_manager)` | `fuse` |
| P-ATTACK | Active mutation slot filled and attack off cooldown | `attack` |

#### IAM-5.2 State–action matrix (target)

Columns: `ML`=`move_left`, `MR`=`move_right`, `JP`=`jump`, `DT`=`detach`, `D2`=`detach_2`, `AT`=`attack`, `AB`=`absorb`, `IF`=`infect`, `FS`=`fuse`, `MN`=`menu`, `DK`=`debug_kill`

| State | ML | MR | JP | DT | D2 | AT | AB | IF | FS | MN | DK |
|-------|----|----|----|----|----|----|----|----|----|----|-----|
| IDLE | ✓ | ✓ | ✓ | ✓ | ✓ | ○ P-ATTACK | ○ P-ABSORB | ○ P-INFECT | ○ P-FUSE | ✓ | ✓ |
| WALK | ✓ | ✓ | ✓ | ✓ | ✓ | ○ | ○ | ○ | ○ | ✓ | ✓ |
| JUMP | ✓ | ✓ | ✗ | ✓ | ✓ | ○ | ✗ | ✗ | ○ | ✓ | ✓ |
| FALL | ✓ | ✓ | ✓ | ✓ | ✓ | ○ | ✗ | ✗ | ○ | ✓ | ✓ |
| FLOAT | ✓ | ✓ | ✓ | ✗ | ✗ | ○ | ✗ | ✗ | ○ | ✓ | ✓ |
| WALL_CLING | ✓ | ✓ | ✓ | ✓ | ✓ | ○ | ✗ | ✗ | ○ | ✓ | ✓ |
| ABSORB | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| MUTATE | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| HURT | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| DEAD | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Notes:**

- **FLOAT (current vs target):** PSM allows explicit `transition(FLOAT)` from JUMP/FALL/FLOAT; derivation does not auto-enter FLOAT (PSM-6). Matrix row is **target** for when float gameplay ships; until then tests use explicit FLOAT state transitions.
- **JUMP state / jump action:** Deny `jump` while in JUMP (no double-jump via policy); coyote/wall-jump remain sim/controller concerns using `jump_just_pressed` when state is FALL/WALL_CLING/IDLE.
- **ABSORB vs MUTATE:** Matches PSM derivation priority — chunk stuck (ABSORB) vs mutation-active (MUTATE) are exclusive states; both rows deny the same action set.
- **Ticket example alignment:** Ticket table for IDLE/WALK/JUMP/FALL/WALL_CLING/ABSORB/HURT/DEAD matches this matrix for movement, jump, attack, absorb, menu columns; this spec **extends** with FLOAT, MUTATE, detach, infect, fuse, debug_kill.

#### IAM-5.3 `is_action_permitted` contract

- Input `action` must be normalized via `normalize_action` before lookup.
- Return `false` for any action not in catalog (IAM-9).
- Contextual ○ cells: policy returns `true` (permit **attempt**); handler enforces predicate failure as no-op.

### 3. Risk & Ambiguity Analysis

- **R-IAM-5.1:** Denying movement in HURT changes feel vs today — intentional for M11 combat clarity; full suite regression when wired.
- **R-IAM-5.2:** Permitting `fuse` in air — matches current handler (no state check); matrix keeps ○ P-FUSE.

### 4. Clarifying Questions

None.

---

## Requirement IAM-6: Input Consumption and Priority Rules

### 1. Spec Summary

- **Description:** When multiple **conflicting** actions register `just_pressed` on the same physics frame, at most **one** combat/mutation winner is delivered. Non-conflicting actions may coexist in the consumed set.
- **Constraints:** Consumption is deterministic and total-order based.
- **Assumptions:** `resolve_consumed_actions` receives only actions that are `just_pressed` this frame (not held-state repeats) unless a test documents otherwise.
- **Scope:** Policy method `resolve_consumed_actions`.

### 2. Acceptance Criteria

- **AC-IAM-6.1:** **Menu suppression:** If `menu` is in the pressed set and permitted, return `["menu"]` only (no other actions).
- **AC-IAM-6.2:** **Combat/mutation group** (mutually exclusive, max one winner): `attack`, `infect`, `absorb`, `fuse`. Priority high → low: **`attack` > `infect` > `absorb` > `fuse`**.
- **AC-IAM-6.3:** Pressing `attack` must not leave `infect` or `absorb` in the consumed set (M11-07 AC alignment).
- **AC-IAM-6.4:** **Independent group:** `detach`, `detach_2`, `move_left`, `move_right`, `jump` may all appear together if each is permitted for the state.
- **AC-IAM-6.5:** `debug_kill` may coexist with non-menu gameplay actions when permitted; it is **not** in the combat group.
- **AC-IAM-6.6:** Aliases normalized before group logic (`mutate` competes as `infect`).

#### IAM-6.1 Resolution algorithm (normative)

```text
1. normalized ← map normalize_action over actions_pressed
2. permitted ← [a for a in normalized if is_action_permitted(state, a)]
3. if "menu" in permitted: return ["menu"]
4. result ← []
5. For each a in {move_left, move_right, jump, detach, detach_2}:
     if a in permitted: append a to result
6. combat_order ← [attack, infect, absorb, fuse]
7. winner ← first action in combat_order that is in permitted
8. if winner exists: append winner to result
9. if "debug_kill" in permitted: append debug_kill
10. return result (stable order: movement keys as listed, then combat winner, then debug_kill)
```

### 3. Risk & Ambiguity Analysis

- **R-IAM-6.1:** `fuse` losing to `absorb` on same frame is conservative; fusion is rarely intentional while absorbing same target.

### 4. Clarifying Questions

None.

---

## Requirement IAM-7: PlayerInputActionPolicy Module Contract

### 1. Spec Summary

- **Description:** Pure `RefCounted` policy module encodes IAM-5 and IAM-6 without `Input`, `Node`, or scene dependencies.
- **Constraints:** Single file target: `scripts/player/player_input_action_policy.gd`. `class_name PlayerInputActionPolicy`.
- **Assumptions:** `PlayerState` type is `PlayerStateMachine.PlayerState` (import/preload as tests do for PSM).
- **Scope:** Public API below; implementation deferred.

### 2. Acceptance Criteria

- **AC-IAM-7.1:** `PlayerInputActionPolicy.new()` succeeds headless.
- **AC-IAM-7.2:** Methods exist with signatures:

```gdscript
class_name PlayerInputActionPolicy
extends RefCounted

## IAM-2.3 alias map
func normalize_action(action: StringName) -> StringName

## IAM-5 matrix
func is_action_permitted(
    state: PlayerStateMachine.PlayerState,
    action: StringName,
) -> bool

## IAM-6; actions_pressed = just_pressed this frame (canonical or alias names)
func resolve_consumed_actions(
    state: PlayerStateMachine.PlayerState,
    actions_pressed: Array[StringName],
) -> Array[StringName]
```

- **AC-IAM-7.3:** `resolve_consumed_actions` returns canonical action names only (no aliases in output).
- **AC-IAM-7.4:** No `extends Node`; no `Input.*` calls in policy file.

### 3. Risk & Ambiguity Analysis

- **R-IAM-7.1:** Class name frozen for test imports and M11-07 handoff.

### 4. Clarifying Questions

None.

---

## Requirement IAM-8: Fail-Closed Unknown Actions

### 1. Spec Summary

- **Description:** Any action string not in the IAM-2.1/IAM-2.2 catalog (after normalization) is denied.
- **Constraints:** No exceptions, no default-permit.
- **Assumptions:** Catalog is closed for M11-03.
- **Scope:** `is_action_permitted` and normalization edge cases.

### 2. Acceptance Criteria

- **AC-IAM-8.1:** `is_action_permitted(state, &"unknown_action")` → `false` for all states.
- **AC-IAM-8.2:** `normalize_action(&"unknown_action")` returns `&"unknown_action"` (identity); permit check still false.
- **AC-IAM-8.3:** Empty `actions_pressed` → `resolve_consumed_actions` → `[]`.

### 3. Risk & Ambiguity Analysis

- **R-IAM-8.1:** Typos in controller action strings fail silently — tests should use shared constants in impl ticket.

### 4. Clarifying Questions

None.

---

## Requirement IAM-9: Debug-Only Actions

### 1. Spec Summary

- **Description:** `debug_kill` is permitted only when `OS.is_debug_build()` would be true at runtime; policy exposes explicit hook for tests.
- **Constraints:** Policy stores `var debug_actions_enabled: bool = false` settable in tests; controller sets from `OS.is_debug_build()` when wired.
- **Assumptions:** Release builds never permit `debug_kill`.
- **Scope:** `debug_kill` row in matrix; IAM-10 hook.

### 2. Acceptance Criteria

- **AC-IAM-9.1:** When `debug_actions_enabled == false`, `is_action_permitted(any_state, &"debug_kill")` → `false`.
- **AC-IAM-9.2:** When `debug_actions_enabled == true` and state is IDLE (and not DEAD), → `true`.
- **AC-IAM-9.3:** DEAD always denies `debug_kill`.

### 3. Risk & Ambiguity Analysis

- **R-IAM-9.1:** Tests must toggle `debug_actions_enabled`; no dependency on `OS` in unit tests.

### 4. Clarifying Questions

None.

---

## Requirement IAM-10: Catalog Constants (Implementation Hint)

### 1. Spec Summary

- **Description:** Recommend `const` `StringName` entries for each canonical action in policy module to avoid typos (optional for M11-03 impl ticket).
- **Constraints:** Non-normative names; tests may use string literals.
- **Assumptions:** None.
- **Scope:** Hint only.

### 2. Acceptance Criteria

- **AC-IAM-10.1:** Spec lists canonical action strings exactly as InputMap names (IAM-2.1 table).

### 3. Risk & Ambiguity Analysis

None.

### 4. Clarifying Questions

None.

---

## Appendix A: Current vs Target Runtime (Evidence)

| Behavior | Current | Target (post policy wire-up) |
|----------|---------|------------------------------|
| Movement / jump / detach | Always read Step 0; no FSM gate | Filtered by IAM-5 |
| absorb / infect / fuse | `InfectionInteractionHandler._process`, no FSM gate | Filtered edges from Step 0 / policy |
| attack | Not in InputMap | `attack` + policy + M11-07 |
| menu | Not in InputMap | `menu` + policy |
| FSM state at input time | Previous frame end state | Unchanged (IAM-4) |

---

## Appendix B: Downstream Consumers

| Ticket | Consumes |
|--------|----------|
| M11-07 attack input framework | `attack` binding (J), IAM-6 consumption, `PlayerInputActionPolicy` |
| M11 mutation / infection tickets | `infect`, `absorb`, `fuse` matrix rows, aliases |
| Settings / rebind (future) | IAM-3 defaults as factory preset |

---

**End of specification**
