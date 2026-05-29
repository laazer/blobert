# Specification: Fusion Attack Dispatch — Route Attack Input to Active Fusion's Attack

**Ticket ID:** M12-03
**Ticket Path:** project_board/12_milestone_12_fused_mutation_attacks/in_progress/03_fusion_attack_framework.md
**Spec Version:** 1.0
**Status:** FROZEN
**Last Updated:** 2026-05-29 by Spec Agent
**Spec Type:** generic
**Depends On:** FADI spec at `project_board/specs/fused_attack_database_integration_spec.md` (normative)

---

## Frozen Design Decision: Routing Gate Definition

### FAF-DD-1: The Routing Gate Is "Both Mutation Slots Filled" — Not is_fusion_active()

**Decision (frozen, no deviation permitted):** Fused attack routing is gated by the dual-mutation slot condition — both `slot_a.is_filled()` and `slot_b.is_filled()` must be true. The `_fusion_active` field and its accessor `is_fusion_active()` are NOT the routing signal and are NOT consulted inside `_try_attack()`.

**Interpretation freeze:** The ticket AC reads: "`is_fusion_active()` on PlayerController3D is used to determine routing (no duplicate state)." After reading the existing code, the correct interpretation is:

- `is_fusion_active()` in the AC refers to the game-concept "the player is in a fusion-capable state" (both mutation slots are filled with distinct mutations), NOT to the speed-boost timer `_fusion_active` field set by `apply_fusion_effect()`.
- The method `is_fusion_active()` as defined at `player_controller_3d.gd` line 603 returns `_fusion_active`, which is the speed-boost timer — a distinct concept from "both slots filled."
- These two concepts are temporally exclusive: `is_fusion_active() == true` only AFTER `consume_fusion_slots()` has cleared both slots. At that moment both slots are EMPTY and `_try_attack()` would route to no attack (no filled slot = early return at line 457-458).

**Implementation implication:** The routing gate implemented in `_try_attack()` lines 464–474 uses `a_filled and b_filled`. This is the correct gate. No change to this logic is required. The AC's `is_fusion_active()` reference is satisfied by the interpretation above: the routing decision is made once, deterministically, from the single source-of-truth slot state — no duplicate state is maintained.

**Verification:** `player_controller_3d.gd` lines 445–482. The body of `_try_attack()` contains zero references to `_fusion_active` or `is_fusion_active()`.

**Evidence:**
- `player_controller_3d.gd` lines 464: `if a_filled and b_filled:` — this is the fused routing gate
- `player_controller_3d.gd` line 603: `func is_fusion_active() -> bool: return _fusion_active` — speed-boost timer only
- `fusion_resolver.gd` lines 56–64: `apply_fusion_effect()` called BEFORE `consume_fusion_slots()` — after `resolve_fusion()`, `is_fusion_active() == true` and both slots are EMPTY

---

## 1. Overview

This spec defines and freezes the fusion attack dispatch framework for M12-03. It establishes:

1. The definitive routing gate (FAF-DD-1 above — both slots filled, not speed-boost timer)
2. The observable contract for the fused route and base-route regression
3. The cooldown independence contract (confirming FADI-DD-1 satisfies AC-3 without new work)
4. How AC-4 (`is_fusion_active()` requirement) is satisfied by existing code
5. State gating requirements (already in place, confirmed operative for fused path)
6. What the Test Designer agent must cover for all 5 acceptance criteria

**Scope:** `PlayerController3D._try_attack()` routing logic, specifically the fused vs base dispatch decision tree. Does NOT cover: the speed-boost fusion effect, `FusionResolver.resolve_fusion()`, enemy reactions to fused damage, HUD changes, or `.tres` fused resource content (M12-02 scope).

**Key finding:** All 5 acceptance criteria of M12-03 are satisfied by existing code as of M12-01 COMPLETE. M12-03's work is to produce tests that verify this routing behavior as a regression suite, and to formally freeze the routing contract in this spec document. The Implementation Agent task is a verification pass, not a code-change task.

---

## 2. Evidence Sources

| Source | Path | Purpose |
|--------|------|---------|
| Ticket | `project_board/12_milestone_12_fused_mutation_attacks/in_progress/03_fusion_attack_framework.md` | 5 acceptance criteria |
| PlayerController3D | `scripts/player/player_controller_3d.gd` lines 445–482 | `_try_attack()` routing implementation |
| is_fusion_active() | `scripts/player/player_controller_3d.gd` lines 603–604 | Speed-boost timer field definition |
| FusionResolver | `scripts/fusion/fusion_resolver.gd` lines 51–66 | resolve_fusion() call order: effect then consume |
| PlayerInputActionPolicy | `scripts/player/player_input_action_policy.gd` | State-machine permit matrix |
| FADI Spec | `project_board/specs/fused_attack_database_integration_spec.md` | Normative: DD-1 through DD-4 |
| M12-01 done ticket | `project_board/12_milestone_12_fused_mutation_attacks/done/01_fused_attack_database_integration.md` | Confirms routing is COMPLETE |
| Planning checkpoint | `project_board/checkpoints/M12-03/2026-05-29T-plan-run.md` | Ambiguity analysis |

---

## 3. Functional Requirements

---

### Requirement FAF-1: Fused Attack Routing Gate

#### 1. Spec Summary

- **Description:** When `_try_attack()` is called and both mutation slots are filled (`slot_a.is_filled() == true` AND `slot_b.is_filled() == true`), the function attempts to dispatch a fused attack by calling `db.get_fused_attack(a_id, b_id)`. If a fused attack resource is returned (non-null), that fused resource is executed. This is the fused routing path.
- **Constraints:** The routing gate evaluates both slots simultaneously using slot indices 0 and 1. The routing decision is made from live slot state — no cached or secondary state variable is consulted. The fused routing path does not use `is_fusion_active()`, `_fusion_active`, `_fusion_timer`, or any other speed-boost state.
- **Assumptions:** `_mutation_slot` is bound via `PlayerMutationSlotBind.ensure_binding(self)` at the start of each `_try_attack()` call. `MutationSlotManager.get_slot(0)` returns slot A; `get_slot(1)` returns slot B. These indices are stable per FADI spec.
- **Scope:** `PlayerController3D._try_attack()` at `scripts/player/player_controller_3d.gd` lines 445–482.

#### 2. Acceptance Criteria

- **FAF-1a:** Both slots filled, fused attack registered for `(a_id, b_id)` in AttackDatabase → `_try_attack()` calls `execute_attack()` with the fused `AttackResource`, not either slot's base resource.
- **FAF-1b:** Both slots filled, fused attack registered, no active cooldown → `attack_started` signal (or equivalent) emits with the fused resource as argument.
- **FAF-1c:** Both slots filled, fused attack registered → the cooldown key set in `_mutation_cooldowns` after dispatch is the composite key `"<sorted_lower>_<sorted_higher>"` (per FADI-DD-1), not `a_id` or `b_id` individually.
- **FAF-1d:** Only one slot filled (slot A filled, slot B unfilled) → `_try_attack()` does NOT enter the fused path; routes to the single-slot base attack path for the filled slot.
- **FAF-1e:** Only one slot filled (slot A unfilled, slot B filled) → `_try_attack()` does NOT enter the fused path; routes to slot B's base attack.
- **FAF-1f:** Neither slot filled → `_try_attack()` returns immediately without executing any attack.
- **FAF-1g:** Both slots filled, but `db.get_fused_attack(a_id, b_id)` returns `null` (no combo registered) → falls back to slot A's base attack (FADI-DD-2, FADI-5).
- **FAF-1h:** The routing decision is made in a single `if a_filled and b_filled:` branch — no secondary calls to `is_fusion_active()` or reads of `_fusion_active` are needed or present.

#### 3. Risk & Ambiguity Analysis

- **AC wording vs implementation:** The ticket AC says "`is_fusion_active()` is used to determine routing." Code shows it is NOT. FAF-DD-1 freezes the correct interpretation: both-slots-filled is the routing gate. No implementation change required. The AC is satisfied by the interpretation that "fusion is active" semantically = "both slots are filled with mutations."
- **Post-resolve state:** After `FusionResolver.resolve_fusion()` is called, `is_fusion_active() == true` but both slots are EMPTY. In this state, `_try_attack()` correctly returns early at line 457 (neither slot filled). This means a fused attack cannot be fired AFTER the speed-boost has been granted — only BEFORE/during the dual-mutation window. This is the correct game-design behavior.
- **Slot A is always index 0:** Slot ordering is structural, not semantic. Tests must use `get_slot(0)` as slot A and `get_slot(1)` as slot B consistently.

#### 4. Clarifying Questions

None. Implementation is frozen per code evidence and FADI spec.

---

### Requirement FAF-2: Base Mutation Attack Regression (No Regression)

#### 1. Spec Summary

- **Description:** When `_try_attack()` is called and exactly one slot is filled, the function dispatches the base attack for that slot's mutation ID. This behavior is unchanged from M9. The fused routing code does not interfere with single-slot base attack dispatch.
- **Constraints:** Single-slot dispatch uses `db.get_base_attack(mutation_id)` and `cooldown_key = mutation_id`. No composite key computation occurs in the single-slot path.
- **Assumptions:** AttackDatabase has the base attack registered for the active mutation ID (per M9/M11 behavior).
- **Scope:** `PlayerController3D._try_attack()` lines 475–478 (the `else` branch).

#### 2. Acceptance Criteria

- **FAF-2a:** Slot A filled, slot B unfilled → `get_base_attack(a_id)` is called; `cooldown_key = a_id`; the base resource fires.
- **FAF-2b:** Slot A unfilled, slot B filled → `get_base_attack(b_id)` is called; `cooldown_key = b_id`; slot B's base resource fires.
- **FAF-2c:** Single-slot dispatch after a fused attack has fired (fused composite cooldown is active but individual slot cooldowns are 0.0) → single-slot base attack fires if called in the single-slot path (different routing condition, independent keys per FADI-EC-3).
- **FAF-2d:** Single-slot dispatch does not set or read any composite key in `_mutation_cooldowns`.
- **FAF-2e:** Fused routing code (lines 464–474) is not reached when only one slot is filled.

#### 3. Risk & Ambiguity Analysis

- **FADI-EC-3 applies:** Individual-slot cooldowns and composite-key cooldowns are fully independent. A fused fire does NOT place a cooldown on individual mutation IDs. After fused composite cooldown expires, a single-slot base attack for either mutation can fire immediately (if the player's slots change to single-slot state). This is correct behavior.
- **Regression risk is low:** The single-slot path (lines 475–478) is unchanged by M12-03. Tests must confirm this path is unaffected.

#### 4. Clarifying Questions

None.

---

### Requirement FAF-3: Cooldown Independence (Fused vs Base)

#### 1. Spec Summary

- **Description:** The fused attack's cooldown is tracked under a composite key (e.g., `"acid_claw"`), independent of the individual mutation cooldown keys (`"acid"`, `"claw"`). After a fused attack fires, individual mutation cooldowns are NOT set. After a base attack fires, the composite key cooldown is NOT set. This is the FADI-DD-1 model, confirmed operative for M12-03.
- **Constraints:** Composite key format: alphabetically sorted `"<lower_id>_<upper_id>"`. Key computation in `_try_attack()` (lines 469–471) and in `AttackDatabase._make_fused_key()` must produce identical results for the same pair.
- **Assumptions:** FADI-DD-1 through FADI-DD-4 are normative and unchanged. No new cooldown model is introduced by M12-03.
- **Scope:** `_mutation_cooldowns` dictionary state in `PlayerController3D`.

#### 2. Acceptance Criteria

- **FAF-3a:** After fused attack fires for combo `(a_id, b_id)`, `_mutation_cooldowns[composite_key] == attack_resource.cooldown` where `composite_key` is the sorted pair string.
- **FAF-3b:** After fused attack fires for combo `(a_id, b_id)`, `_mutation_cooldowns.get(a_id, 0.0) == 0.0` (no individual slot cooldown set).
- **FAF-3c:** After fused attack fires for combo `(a_id, b_id)`, `_mutation_cooldowns.get(b_id, 0.0) == 0.0` (no individual slot cooldown set).
- **FAF-3d:** While `_mutation_cooldowns[composite_key] > 0.0`, a subsequent call to `_try_attack()` with both slots still filled does not fire any attack.
- **FAF-3e:** The composite key stored as the cooldown key in `_try_attack()` is identical to the key produced by `AttackDatabase._make_fused_key(a_id, b_id)` for the same pair. Both use alphabetical sort + `"_"` separator.
- **FAF-3f:** The cooldown value stored is `attack_resource.cooldown` exactly (no scaling, no additive offset). Confirmed by FADI-3e.

#### 3. Risk & Ambiguity Analysis

- **Key parity between _try_attack() and AttackDatabase:** `_try_attack()` computes the composite key inline (lines 469–471), not via `_make_fused_key()`. If the two implementations diverge, the cooldown key will not match the lookup key. FADI-EC-3 and FADI-NF-3 freeze this as a risk that existing tests (adversarial suite) already cover.
- **FADI-DD-1 fully satisfies AC-3 of the ticket:** No additional cooldown model changes are needed for M12-03.

#### 4. Clarifying Questions

None. FADI-DD-1 is frozen and operative.

---

### Requirement FAF-4: is_fusion_active() Usage Contract

#### 1. Spec Summary

- **Description:** The ticket AC states "`is_fusion_active()` on PlayerController3D is used to determine routing (no duplicate state)." This requirement is satisfied by the existing code WITHOUT calling `is_fusion_active()` in `_try_attack()`. The satisfaction proof: the routing decision reads live slot state (the single source of truth for whether mutations are active); `is_fusion_active()` (the speed-boost timer) is a different concept with a different lifecycle, and consulting it inside `_try_attack()` would introduce, not remove, duplicate state handling. The "no duplicate state" constraint means: routing must derive from one authoritative state source. That source is the slot fill state, not a secondary speed-boost timer.
- **Constraints:** `is_fusion_active()` must NOT be added to the `_try_attack()` routing branch. The method remains unchanged: `func is_fusion_active() -> bool: return _fusion_active`. It is used correctly by other systems (e.g., movement multiplier logic) but not by attack routing.
- **Assumptions:** No caller of `_try_attack()` has a dependency on `is_fusion_active()` being consulted inside `_try_attack()`.
- **Scope:** `PlayerController3D._try_attack()` and `is_fusion_active()` at `player_controller_3d.gd`.

#### 2. Acceptance Criteria

- **FAF-4a:** `PlayerController3D._try_attack()` does not call or read `is_fusion_active()` or `_fusion_active` at any point in its body. (Verified by code inspection: zero such references at lines 445–482.)
- **FAF-4b:** The routing decision derives solely from `slot_a.is_filled()` and `slot_b.is_filled()` — the single authoritative slot state. No secondary boolean flag gates the fused route.
- **FAF-4c:** `is_fusion_active()` returns `true` only when the speed-boost timer is running (post `resolve_fusion()`, post slot consumption). During this window, both slots are EMPTY, and `_try_attack()` returns early (no attack). This is the correct temporal separation.
- **FAF-4d:** The Test Designer agent must include a test that confirms: when `is_fusion_active()` returns `true` (speed-boost window, both slots empty), `_try_attack()` fires no attack. This validates the temporal separation contract.

#### 3. Risk & Ambiguity Analysis

- **AC wording is misleading:** The ticket AC literally says `is_fusion_active()` "is used to determine routing." Spec Agent interpretation (frozen): this means the routing must not introduce duplicate state — and it does not. The slot state IS the fusion state for routing purposes. Calling `is_fusion_active()` would add, not remove, state duplication.
- **Speed-boost window attack gap:** During the speed-boost timer window (post-resolve, pre-expiry), the player cannot fire any attack via `_try_attack()` because both slots are empty. This is a deliberate consequence of the slot-consumption model. It is NOT a bug. If the game design later requires attacks during the speed-boost window, that requires a new spec and implementation (tracking last combo identity before slot consumption) — which is explicitly out of scope for M12-03.

#### 4. Clarifying Questions

None. The interpretation is frozen. Out-of-scope behavior (speed-boost-window attack) is deferred explicitly.

---

### Requirement FAF-5: State-Machine Gating for Fused Attack Dispatch

#### 1. Spec Summary

- **Description:** Fused attack dispatch is blocked by the same `PlayerInputActionPolicy` state-machine gate that blocks all attack input. The gate runs at lines 449–452, before any slot, fused, or base logic. When the player state is ABSORB, MUTATE, HURT, or DEAD, no attack (fused or base) fires regardless of slot state.
- **Constraints:** Gate check order is fixed: policy check → slot check → database lookup → cooldown check → execute. The fused routing code is never reached in a denied state.
- **Assumptions:** `PlayerInputActionPolicy._PERMIT_MATRIX` is stable: ACTION_ATTACK is `false` for ABSORB, MUTATE, HURT, and DEAD (absent from those state rows). This is confirmed by `player_input_action_policy.gd` lines 136–145.
- **Scope:** `PlayerController3D._try_attack()` lines 449–452 (policy guard) and `PlayerInputActionPolicy._PERMIT_MATRIX`.

#### 2. Acceptance Criteria

- **FAF-5a:** With both slots filled and a fused attack registered, `_try_attack()` called while player state is `PlayerState.ABSORB` → no attack fires; `_mutation_cooldowns` is unchanged.
- **FAF-5b:** With both slots filled and a fused attack registered, `_try_attack()` called while player state is `PlayerState.MUTATE` → no attack fires.
- **FAF-5c:** With both slots filled and a fused attack registered, `_try_attack()` called while player state is `PlayerState.HURT` → no attack fires.
- **FAF-5d:** With both slots filled and a fused attack registered, `_try_attack()` called while player state is `PlayerState.DEAD` → no attack fires.
- **FAF-5e:** With both slots filled and a fused attack registered, `_try_attack()` called while player state is `PlayerState.IDLE` → fused attack fires normally (gate permits).
- **FAF-5f:** State gating applies identically to fused and base attack paths — no special bypass for fused attacks in any state.
- **FAF-5g:** `run_tests.sh` exits 0 (no regression from M12-03 test additions).

#### 3. Risk & Ambiguity Analysis

- **Existing gate confirmed operative:** `player_input_action_policy.gd` lines 136–145 show ABSORB, MUTATE, HURT rows contain only `ACTION_MENU: true`. DEAD row is empty `{}`. ACTION_ATTACK is absent from all four denied states. `_matrix_allows()` returns `false` for absent keys. The gate is already correct.
- **Tests must verify fused path is also blocked:** Existing FADI-7a/7b tests test state gating for fused attacks. M12-03 tests must provide the same coverage for the complete set of denied states (all 4: ABSORB, MUTATE, HURT, DEAD) to satisfy FAF-5a through FAF-5d independently.

#### 4. Clarifying Questions

None. Policy matrix is frozen and confirmed.

---

### Requirement FAF-6: Test Suite Passes (run_tests.sh Exits 0)

#### 1. Spec Summary

- **Description:** After all M12-03 work (tests written and verified), `bash ci/scripts/run_tests.sh` (or equivalent `timeout 300 godot --headless -s tests/run_tests.gd`) must exit 0. No new test failures may be introduced. Existing passing tests must remain passing.
- **Constraints:** Test file names must be behavior-descriptive with no milestone IDs or ticket numbers embedded. Canonical names per planning checkpoint: `test_fusion_attack_routing.gd` and `test_fusion_attack_routing_adversarial.gd` under `tests/scripts/attacks/`.
- **Assumptions:** The implementation is already correct (M12-01 COMPLETE). All M12-03 tests should be GREEN on the current codebase (they are regression tests, not new-feature tests).
- **Scope:** Entire test suite; specific new tests are in scope.

#### 2. Acceptance Criteria

- **FAF-6a:** `bash ci/scripts/run_tests.sh` exits 0 with all M12-03 tests included.
- **FAF-6b:** New test file `tests/scripts/attacks/test_fusion_attack_routing.gd` is discovered and executed by the test runner.
- **FAF-6c:** New test file `tests/scripts/attacks/test_fusion_attack_routing_adversarial.gd` is discovered and executed by the test runner.
- **FAF-6d:** No pre-existing test that was GREEN before M12-03 work becomes RED after M12-03 work.

#### 3. Risk & Ambiguity Analysis

- **All new tests should be GREEN immediately:** Since M12-03 is a verification pass on existing code, all behavioral tests must pass against the current codebase. A RED test on existing code means either a test bug (fix the test) or an undiscovered regression (fix the code).
- **Test Breaker tests may intentionally fail if the implementation has a gap:** The Test Breaker is still tasked with adversarial tests. If the Test Breaker finds a genuine gap in the existing code, that test will be RED and the Implementation Agent must resolve it.

#### 4. Clarifying Questions

None.

---

## 4. Non-Functional Requirements

| Requirement | Specification | Rationale |
|---|---|---|
| **FAF-NF-1: Routing Determinism** | Given identical slot state and database state, `_try_attack()` always produces the same routing outcome (fused or base). No randomness, no ordering dependency other than slot index (0=A, 1=B). | CI repeatability; test isolation. |
| **FAF-NF-2: No Duplicate State** | The routing decision in `_try_attack()` must derive from slot fill state only. No secondary boolean, timer, or flag may serve as a second gating condition for fused routing. | FAF-DD-1; ticket AC-4 requirement. |
| **FAF-NF-3: Slot Index Stability** | Slot A is always `_mutation_slot.get_slot(0)`; Slot B is always `_mutation_slot.get_slot(1)`. Tests must use these indices. | Consistent with FADI spec and existing tests. |
| **FAF-NF-4: Composite Key Stability** | The `"<lower_id>_<higher_id>"` format (alphabetical sort, `"_"` separator) is stable. Per FADI-NF-3, no format change is permitted without a breaking-change plan revision. | Test correctness; key parity between routing and cooldown check. |
| **FAF-NF-5: No New Global Abstractions** | M12-03 does not introduce new GDScript classes, autoloads, singletons, or cross-cutting modules. All work is within the existing `PlayerController3D._try_attack()` boundary. | CLAUDE.md: avoid inventing global abstractions; follow local conventions. |
| **FAF-NF-6: Test File Naming** | New test files must use behavior-descriptive names: `test_fusion_attack_routing.gd` and `test_fusion_attack_routing_adversarial.gd`. No milestone IDs or ticket numbers in filenames. Traceability (M12-03, FAF spec section) belongs in a module docstring. | CLAUDE.md test naming convention. |

---

## 5. Failure Modes and Edge Cases

| ID | Scenario | Expected Behavior | Spec Reference |
|----|----------|-------------------|---------------|
| FAF-FM-1 | Both slots filled; `_mutation_slot` is null at call time | `PlayerMutationSlotBind.ensure_binding(self)` runs; if still null after bind, `_try_attack()` returns at line 447-448 without executing any attack. | `_try_attack()` line 447-448 guard. |
| FAF-FM-2 | `_get_attack_database()` returns null (no AttackDatabase autoload in scene) | `_try_attack()` returns at line 461 without executing any attack and without crashing. | `_try_attack()` line 459-461 guard. |
| FAF-FM-3 | Both slots filled; fused combo registered; `_attack_executor` is in active state (`_is_active == true`) | `execute_attack()` rejects the call internally (executor guard); no attack fires, `_mutation_cooldowns` is NOT set (because execute_attack returns false/blocked before the cooldown assignment). | AttackExecutor guard; not directly in `_try_attack()` flow. Verify: cooldown not set on executor-blocked dispatch. |
| FAF-FM-4 | Both slots filled; same mutation in both slots (e.g., `"claw"` in slot A and `"claw"` in slot B) | `get_fused_attack("claw", "claw")` returns null (FADI-NF-4: self-fusion rejected at registration). Falls back to slot A's base attack `get_base_attack("claw")`. | FADI-NF-4, FADI-EC-1. |
| FAF-FM-5 | `is_fusion_active() == true` (speed-boost timer running); player presses attack | Both slots are EMPTY at this point (consumed by resolve_fusion). `_try_attack()` returns early at line 457-458 (neither slot filled). No attack fires. | FAF-4c; this is correct behavior by design. |
| FAF-FM-6 | Fused composite cooldown active; player changes to single-slot state before cooldown expires | Single-slot path does not read the composite key. The composite cooldown continues to count down independently. Slot A's base attack fires freely if `_mutation_cooldowns.get(a_id, 0.0) == 0.0`. | FADI-EC-3; FAF-3 independence model. |
| FAF-FM-7 | `_input_policy` is null | `_try_attack()` returns at line 447-448 guard (`_input_policy == null`). No attack fires. | `_try_attack()` line 447-448 null guard. |
| FAF-FM-8 | Both slots filled; slot's `get_active_mutation_id()` returns empty string `""` | `get_fused_attack("", b_id)` returns null (per FADI-2d). Falls back to `get_base_attack("")` which returns null. Final null check at line 479 blocks execution. No crash. | FADI-2d; `_try_attack()` line 479. |

---

## 6. Schemas and Contracts

### `_try_attack()` Decision Tree (Complete, Frozen)

```
_try_attack()
├── ensure_binding
├── guard: _input_policy == null or _mutation_slot == null → return
├── guard: policy.is_action_permitted(state, ACTION_ATTACK) == false → return
├── slot_a = get_slot(0); slot_b = get_slot(1)
├── a_filled = slot_a != null and slot_a.is_filled()
├── b_filled = slot_b != null and slot_b.is_filled()
├── guard: not a_filled and not b_filled → return
├── db = _get_attack_database()
├── guard: db == null → return
├── if a_filled and b_filled:           ← FUSED ROUTING GATE (FAF-DD-1)
│   ├── a_id = slot_a.get_active_mutation_id()
│   ├── b_id = slot_b.get_active_mutation_id()
│   ├── attack_resource = db.get_fused_attack(a_id, b_id)
│   ├── if attack_resource != null:
│   │   └── cooldown_key = sorted(a_id, b_id) joined by "_"   ← composite key
│   └── else (fallback):
│       ├── attack_resource = db.get_base_attack(a_id)
│       └── cooldown_key = a_id                                ← slot A only
└── else (single slot):
    ├── mid = a_id if a_filled else b_id
    ├── attack_resource = db.get_base_attack(mid)
    └── cooldown_key = mid
    
FINAL GUARD: attack_resource == null or _mutation_cooldowns.get(cooldown_key, 0.0) > 0.0 → return

EXECUTE: _attack_executor.execute_attack(attack_resource)
SET:     _mutation_cooldowns[cooldown_key] = attack_resource.cooldown
```

### `_mutation_cooldowns` State Contract After Fused Fire

| Key | Expected Value | Notes |
|-----|---------------|-------|
| `"<sorted_lower>_<sorted_higher>"` | `attack_resource.cooldown` | Composite key set by fused fire |
| `a_id` (e.g., `"acid"`) | `0.0` (absent or explicitly zero) | Individual key NOT set by fused fire |
| `b_id` (e.g., `"claw"`) | `0.0` (absent or explicitly zero) | Individual key NOT set by fused fire |

### Permitted States for ACTION_ATTACK

| Player State | Attack Permitted? |
|---|---|
| IDLE | YES |
| WALK | YES |
| JUMP | YES |
| FALL | YES |
| FLOAT | YES |
| WALL_CLING | YES |
| ABSORB | NO |
| MUTATE | NO |
| HURT | NO |
| DEAD | NO |

---

## 7. Test Strategy (for Test Designer Agent)

### Context: This is a Regression Test Suite

All 5 ACs of M12-03 are satisfied by existing code as of M12-01 COMPLETE. The tests written for M12-03 are **regression tests** — they must be GREEN against the current codebase and must remain GREEN going forward. A RED test on the current codebase indicates a test authoring bug, not a missing feature.

### Test File Names

- `tests/scripts/attacks/test_fusion_attack_routing.gd` — behavioral regression tests
- `tests/scripts/attacks/test_fusion_attack_routing_adversarial.gd` — adversarial/boundary tests

Module docstring in each file must include: `# Traceability: M12-03, FAF spec (project_board/specs/fusion_attack_framework_spec.md)`

### Existing Tests That Satisfy M12-03 Requirements (Do Not Duplicate)

| Test | File | FAF Requirement Covered |
|------|------|------------------------|
| `test_adb07_fused_when_both_slots` | `test_attack_database_controller_integration.gd` | FAF-1a, FAF-1b |
| `test_adb07_fused_fallback_to_base` | `test_attack_database_controller_integration.gd` | FAF-1g, FAF-2a |
| FADI-7a state gate tests | `test_attack_database_controller_integration.gd` | FAF-5a/5e (partial) |
| FADI-3b/3c composite key isolation | `test_fused_combo_matrix_adversarial.gd` | FAF-3b, FAF-3c |

### New Tests Required for test_fusion_attack_routing.gd (Behavioral)

These tests must call `_try_attack()` directly and verify `attack_started` signal emission or `_mutation_cooldowns` state. No prose assertions.

1. **test_fused_route_fires_when_both_slots_filled** — Both slots filled, fused attack registered → fused resource fires (FAF-1a, FAF-1b)
2. **test_base_route_fires_when_only_slot_a_filled** — Slot A filled, slot B unfilled → slot A's base attack fires, not fused (FAF-1d, FAF-2a)
3. **test_base_route_fires_when_only_slot_b_filled** — Slot A unfilled, slot B filled → slot B's base attack fires (FAF-1e, FAF-2b)
4. **test_no_attack_when_no_slots_filled** — Neither slot filled → `_try_attack()` returns without executing (FAF-1f)
5. **test_fused_cooldown_key_is_composite_not_individual** — After fused fire, composite key set, individual keys unset (FAF-3a, FAF-3b, FAF-3c)
6. **test_fused_cooldown_blocks_repeat_fire** — While composite cooldown > 0.0, second `_try_attack()` call fires nothing (FAF-3d)
7. **test_no_attack_during_speed_boost_window** — `is_fusion_active() == true` (both slots empty), `_try_attack()` fires nothing (FAF-4c, FAF-4d)
8. **test_attack_blocked_in_absorb_state** — Both slots filled, fused registered, state=ABSORB → no attack (FAF-5a)
9. **test_attack_blocked_in_mutate_state** — Both slots filled, fused registered, state=MUTATE → no attack (FAF-5b)
10. **test_attack_blocked_in_hurt_state** — Both slots filled, fused registered, state=HURT → no attack (FAF-5c)
11. **test_attack_blocked_in_dead_state** — Both slots filled, fused registered, state=DEAD → no attack (FAF-5d)
12. **test_attack_permitted_in_idle_state** — Both slots filled, fused registered, state=IDLE → fused attack fires (FAF-5e)
13. **test_base_route_not_disrupted_by_fused_cooldown_on_different_key** — Composite key on cooldown; player enters single-slot state; base attack fires freely (FAF-2c, FADI-EC-3)
14. **test_fallback_to_slot_a_when_no_fused_registered** — Both slots filled, no fused registered → slot A's base fires, slot B cooldown unset (FAF-1g, FADI-5a, FADI-5c)

### New Tests Required for test_fusion_attack_routing_adversarial.gd (Adversarial)

1. **test_routing_boundary_one_slot_filled_does_not_enter_fused_path** — Slot A filled, slot B unfilled; confirm `get_fused_attack()` is NOT called (FAF-1d)
2. **test_null_mutation_slot_does_not_crash** — `_mutation_slot == null`; `_try_attack()` returns without exception (FAF-FM-1)
3. **test_null_attack_database_does_not_crash** — No AttackDatabase autoload; `_try_attack()` returns without exception (FAF-FM-2)
4. **test_same_mutation_in_both_slots_falls_back_to_base** — Both slots filled with same mutation ID; self-fusion rejected → slot A's base fires (FAF-FM-4)
5. **test_speed_boost_active_both_slots_empty_no_attack** — Set `_fusion_active = true` directly; both slots empty; `_try_attack()` fires nothing (FAF-FM-5)
6. **test_composite_key_is_order_independent** — Fused fire with slot A="claw"/slot B="acid" and slot A="acid"/slot B="claw" produce identical composite key `"acid_claw"` in `_mutation_cooldowns` (FADI-DD-3 in routing context)
7. **test_fused_cooldown_set_independently_of_individual_slot_cooldowns** — Set individual slot cooldowns to non-zero before firing fused; confirm fused fires and sets composite key (FADI-EC-3 adversarial)
8. **test_policy_null_returns_early** — `_input_policy == null`; `_try_attack()` returns without crash (FAF-FM-7)
9. **test_all_four_denied_states_block_independently** — Loop through ABSORB, MUTATE, HURT, DEAD; each independently blocks fused attack (FAF-5a through FAF-5d independence)
10. **test_empty_mutation_id_does_not_crash** — Slot returns `""` from `get_active_mutation_id()`; `_try_attack()` handles null resource at final guard and returns without crash (FAF-FM-8)

### Test Setup Pattern

Follow the `_setup_attack_pipeline` helper pattern from `tests/scripts/attacks/test_attack_database_controller_integration.gd`. For M12-03 tests, the pipeline must be configured with TWO filled slots:

```
PlayerController3D (headless, no scene)
  └─ _mutation_slot: MutationSlotManager
       ├─ slot(0): MutationSlot filled with a_id (e.g., "acid")
       └─ slot(1): MutationSlot filled with b_id (e.g., "claw")
  └─ _attack_executor: AttackExecutor (signal connected)
  └─ AttackDatabase autoload: registered fused attack for (a_id, b_id)
  └─ _player_state_machine: state set to IDLE (or target state)
  └─ _input_policy: PlayerInputActionPolicy instance
```

For speed-boost window tests (FAF-4c, FAF-FM-5): set slots to empty (unfilled) AND set `_fusion_active = true` directly on the controller instance.

---

## 8. Implementation Agent Guidance

### Interpretation B Is Frozen — No New Implementation Required

The Implementation Agent task for M12-03 is a **verification pass**, not a code-change task. The checklist:

1. Read `player_controller_3d.gd` lines 445–482 and confirm `_try_attack()` matches the frozen decision tree in Section 6.
2. Confirm zero references to `is_fusion_active()` or `_fusion_active` in `_try_attack()`.
3. Run `task hooks:gd-review -- scripts/player/player_controller_3d.gd` (static QA pass).
4. Run `timeout 300 godot --headless -s tests/run_tests.gd` and confirm exit 0.

If the verification pass uncovers any discrepancy between the code and this spec, route back to Planner.

### Out of Scope (Do Not Implement)

- Tracking `_last_fused_a_id` / `_last_fused_b_id` before slot consumption (Interpretation A/C)
- Fused attack dispatch during the speed-boost window (Interpretation C)
- Any changes to `FusionResolver.resolve_fusion()` or `apply_fusion_effect()`
- Any changes to `AttackDatabase` (M12-01 COMPLETE)
- Any changes to `.tres` fused resource files (M12-02 COMPLETE)

---

## 9. Deferred Scope

### Deferred to Future Milestone (Post-M12)

1. **Attack during speed-boost window:** If the game design requires the fused attack to be fireable during the speed-boost timer window (post-`resolve_fusion()`), a future ticket must define: (a) storage of the last fused combo identity before `consume_fusion_slots()`, (b) a new routing branch using `is_fusion_active()` to look up the stored combo, (c) slot state during that window, and (d) whether speed-boost-window fused attacks share or reset the composite cooldown. This is explicitly NOT in M12-03 scope.

2. **Fused attack visual/audio effects:** No HUD, animation, or sound changes are in scope for M12-03. Those are separate tickets in M12 or a later milestone.

3. **Enemy reactions to fused damage types:** Out of scope; enemy behavior is defined by enemy-side tickets.

---

## 10. Checkpoint Log Reference

Assumptions made during this spec run are logged at:
`project_board/checkpoints/M12-03/2026-05-29T-spec-run.md`

---

## 11. Revision History

| Revision | Date | Agent | Change |
|----------|------|-------|--------|
| 1.0 | 2026-05-29 | Spec Agent | Initial frozen spec; FAF-DD-1 frozen as Interpretation B |
