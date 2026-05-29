# SPEC: Fused Attack Database Integration

**Ticket:** M12-01 (`project_board/12_milestone_12_fused_mutation_attacks/backlog/01_fused_attack_database_integration.md`)
**Spec ID:** FADI
**Status:** Frozen
**Revision:** 1
**Author:** Spec Agent
**Spec Exit Type:** generic
**Date:** 2026-05-28

---

## 1. Overview

This spec documents and freezes the fused-attack dispatch system introduced in M12. The core implementation already exists in:

- `scripts/attacks/attack_database.gd` — `register_fused_attack()`, `get_fused_attack()`, `_make_fused_key()`
- `scripts/player/player_controller_3d.gd` lines 445–482 — `_try_attack()` fused dispatch path

The primary work defined by this spec is: (1) documenting the four frozen design decisions below, (2) defining the 6-combo matrix contract that tests must cover, and (3) clarifying the fallback cooldown-key asymmetry as intentional and correct design.

**Scope:** `AttackDatabaseNode` fused API, `PlayerController3D._try_attack()` fused path (both slots), composite cooldown key model, fallback key behavior, and combo matrix coverage. Does **not** cover: fused `.tres` resource creation (M12-02), enemy reactions to fused damage, HUD changes, or new effect types.

---

## 2. Evidence Sources

| Source | Path |
|--------|------|
| Ticket | `project_board/12_milestone_12_fused_mutation_attacks/backlog/01_fused_attack_database_integration.md` |
| AttackDatabase implementation | `scripts/attacks/attack_database.gd` |
| PlayerController3D implementation | `scripts/player/player_controller_3d.gd` lines 445–482 |
| Integration test (ADB-07) | `tests/scripts/attacks/test_attack_database_controller_integration.gd` lines 558–615 |
| Unit tests (ADB-5, ADB-6) | `tests/scripts/attacks/test_attack_database.gd` |
| M11 ADB spec | `project_board/specs/attack_database_integration_spec.md` |
| Planning checkpoint | `project_board/checkpoints/M12-01/2026-05-28T-plan-run.md` |

---

## 3. Frozen Design Decisions

These four decisions are normative. No implementation agent may deviate from them without a plan revision.

### FADI-DD-1: Composite-Key Shared Cooldown Model

**Decision:** The fused combo cooldown is tracked under a single **composite key** (e.g., `"acid_claw"`), not under both individual slot keys (`"acid"` and `"claw"` independently).

**Mechanism:** In `_try_attack()`, when a fused attack fires, the cooldown key is computed identically to the fused lookup key: alphabetical sort of the two mutation IDs joined by `"_"`. The cooldown timer entry `_mutation_cooldowns[composite_key]` is set to `attack_resource.cooldown`. No timer is set for `_mutation_cooldowns["acid"]` or `_mutation_cooldowns["claw"]` individually.

**Rationale:** A fused combo is a single combined action. Tracking it under one key avoids the complexity of coordinating two independent timers and prevents asymmetric partial-expiry bugs. The single composite-key timer is the correct and intentional design.

**Observable contract:** After a fused attack fires for combo `(X, Y)`:
- `_mutation_cooldowns["<sorted_x_y>"] == attack_resource.cooldown` (immediately post-fire)
- `_mutation_cooldowns.get("X", 0.0) == 0.0` (no individual timer set)
- `_mutation_cooldowns.get("Y", 0.0) == 0.0` (no individual timer set)

**Evidence:** `player_controller_3d.gd` lines 469–472 and 482:
```
var pair: Array = [a_id, b_id]
pair.sort()
cooldown_key = "%s_%s" % [pair[0], pair[1]]
...
_mutation_cooldowns[cooldown_key] = attack_resource.cooldown
```

### FADI-DD-2: Fallback Cooldown Key Asymmetry (Intentional)

**Decision:** When both mutation slots are filled but no fused attack is registered for that pair, `_try_attack()` falls back to slot A's base attack and uses slot A's mutation ID as the cooldown key. Slot B's cooldown key is neither read nor written.

**This is intentional.** Slot A is the "primary attacker" in the fallback case. The semantic interpretation: when the player has two mutations but no fused combo for them, the system fires slot A's base attack as if only slot A were active. Slot B's mutation does not contribute to the attack and its cooldown is unaffected.

**Implication for slot B:** Slot B's mutation-specific cooldown is not blocked by a fallback fire. A call to `get_base_attack(b_id)` during the same frame would succeed if `_mutation_cooldowns.get(b_id, 0.0) == 0.0`. However, `_try_attack()` will not fire slot B's base attack in the same frame — the function returns after dispatching slot A's base attack.

**Observable contract:** After a fallback fire where slot A = `"X"` and slot B = `"Y"` and no fused combo `(X, Y)` exists:
- `_mutation_cooldowns["X"] == attack_resource.cooldown` (slot A's cooldown set)
- `_mutation_cooldowns.get("Y", 0.0) == 0.0` (slot B's cooldown untouched)
- The fired `AttackResource` is the same object returned by `db.get_base_attack("X")`

**Evidence:** `player_controller_3d.gd` lines 473–474:
```
attack_resource = db.get_base_attack(a_id)
cooldown_key = a_id
```

### FADI-DD-3: Order-Independence Contract

**Decision:** `get_fused_attack(a, b)` and `get_fused_attack(b, a)` always return the same `AttackResource` for all valid (a, b) pairs. This is guaranteed by `_make_fused_key()` which alphabetically sorts the two IDs before forming the `"id1_id2"` composite key.

**Mechanism:** `_make_fused_key(id_a, id_b)` creates `Array [id_a, id_b]`, calls `.sort()` (lexicographic ascending), then returns `"%s_%s" % [pair[0], pair[1]]`. Both `register_fused_attack()` and `get_fused_attack()` call this method. Therefore the storage key is canonical regardless of argument order.

**Observable contract:**
- `register_fused_attack("X", "Y", res)` followed by `get_fused_attack("Y", "X")` returns `res`
- `register_fused_attack("Y", "X", res)` followed by `get_fused_attack("X", "Y")` returns `res`
- For any pair `(X, Y)` where `X != Y`: `get_fused_attack(X, Y) === get_fused_attack(Y, X)` (same reference or both null)

**Evidence:** `attack_database.gd` lines 173–177:
```
func _make_fused_key(id_a: String, id_b: String) -> String:
    var pair: Array = [id_a, id_b]
    pair.sort()
    return "%s_%s" % [pair[0], pair[1]]
```

### FADI-DD-4: 6-Combo Matrix Definition

**Decision:** The four canonical base mutation IDs are `"claw"`, `"acid"`, `"carapace"`, and `"adhesion"`. These produce exactly 6 unordered pairs (C(4,2) = 6):

| Combo | Sorted Key |
|-------|-----------|
| claw + acid | `"acid_claw"` |
| claw + carapace | `"carapace_claw"` |
| claw + adhesion | `"adhesion_claw"` |
| acid + carapace | `"acid_carapace"` |
| acid + adhesion | `"acid_adhesion"` |
| carapace + adhesion | `"adhesion_carapace"` |

Test coverage must exercise all 6 unordered pairs in both lookup direction and player-dispatch path. Tests use synthetic `AttackResource` instances (not real `.tres` files). Real `.tres` resource creation is the scope of ticket M12-02.

---

## 4. Requirements

---

### Requirement FADI-1: Fused Attack Registration API

#### 1. Spec Summary

- **Description:** `AttackDatabaseNode.register_fused_attack(slot_a_id: String, slot_b_id: String, resource: AttackResource) -> void` stores `resource` at a canonical key derived from alphabetical sort of `slot_a_id` and `slot_b_id`. The key format is `"<lower_id>_<higher_id>"`.
- **Constraints:** Both `slot_a_id` and `slot_b_id` must be non-empty strings and must differ from each other. `resource` must be non-null. Violations emit a `push_warning()` and do not store anything.
- **Assumptions:** Mutation IDs are lowercase ASCII strings (e.g., `"claw"`, `"acid"`). No whitespace normalization is performed.
- **Scope:** `AttackDatabaseNode` class in `scripts/attacks/attack_database.gd`.

#### 2. Acceptance Criteria

- **FADI-1a:** `register_fused_attack("claw", "acid", res)` causes `get_fused_attack("claw", "acid")` to return `res`.
- **FADI-1b:** `register_fused_attack("acid", "claw", res)` causes `get_fused_attack("claw", "acid")` to return `res` (reverse registration, same canonical key).
- **FADI-1c:** Calling `register_fused_attack("claw", "acid", r2)` after `register_fused_attack("claw", "acid", r1)` causes `get_fused_attack("claw", "acid")` to return `r2` (last-write-wins).
- **FADI-1d:** `register_fused_attack("", "acid", res)` does not store anything; `get_fused_attack("", "acid")` returns `null`.
- **FADI-1e:** `register_fused_attack("claw", "", res)` does not store anything; `get_fused_attack("claw", "")` returns `null`.
- **FADI-1f:** `register_fused_attack("claw", "claw", res)` does not store anything (self-fusion rejected); `get_fused_attack("claw", "claw")` returns `null`.
- **FADI-1g:** `register_fused_attack("claw", "acid", null)` does not store anything; `get_fused_attack("claw", "acid")` returns `null`.
- **FADI-1h:** All 6 canonical combos (FADI-DD-4) can be registered independently without interfering with each other.

#### 3. Risk & Ambiguity Analysis

- **Key collision risk:** Two different mutation IDs whose sorted concatenation is identical (e.g., hypothetical `"ab"` + `"c"` → `"ab_c"` vs `"a"` + `"bc"` → `"a_bc"`) would not collide because the separator `"_"` is always between the two sorted strings and mutation IDs are well-defined single words. Actual mutation IDs (`claw`, `acid`, `carapace`, `adhesion`) do not produce collisions with the current separator.
- **Overwrite without warning:** The last-write-wins behavior (FADI-1c) is silent; no warning is emitted on overwrite. This matches the base-attack overwrite behavior and is consistent.

#### 4. Clarifying Questions

None. Implementation is frozen. This AC set documents existing behavior.

---

### Requirement FADI-2: Fused Attack Lookup API

#### 1. Spec Summary

- **Description:** `AttackDatabaseNode.get_fused_attack(slot_a_id: String, slot_b_id: String) -> AttackResource` returns the registered `AttackResource` for the canonical key formed by sorting `slot_a_id` and `slot_b_id`. Returns `null` and emits `push_warning()` when no entry exists for that key.
- **Constraints:** Lookup is order-independent (FADI-DD-3). An empty string argument or an unregistered pair returns `null`. Does not modify `_fused_attacks`.
- **Assumptions:** No assumptions beyond FADI-DD-3.
- **Scope:** `AttackDatabaseNode.get_fused_attack()` in `scripts/attacks/attack_database.gd`.

#### 2. Acceptance Criteria

- **FADI-2a:** `get_fused_attack("X", "Y")` where `(X, Y)` is registered returns the registered resource (forward lookup).
- **FADI-2b:** `get_fused_attack("Y", "X")` where `(X, Y)` is registered returns the same resource (reverse lookup, order-independence).
- **FADI-2c:** `get_fused_attack("unknown_a", "unknown_b")` returns `null`.
- **FADI-2d:** `get_fused_attack("", "acid")` returns `null`.
- **FADI-2e:** Lookup for a pair `(X, Z)` where `(X, Y)` is registered and `Z != Y` returns `null` (no cross-combo contamination).
- **FADI-2f:** All 6 canonical combos (FADI-DD-4): forward lookup (`get_fused_attack(a, b)`) returns the registered resource for all 6 pairs.
- **FADI-2g:** All 6 canonical combos (FADI-DD-4): reverse lookup (`get_fused_attack(b, a)`) returns the same registered resource for all 6 pairs.

#### 3. Risk & Ambiguity Analysis

- **Null on unregistered pair:** M12-02 will register real fused resources at startup. Until M12-02 is integrated, `get_fused_attack()` for any real combo will return `null` in a fresh database instance without explicit registration. This is expected behavior — `_register_defaults()` registers base attacks only, not fused attacks.
- **No partial-match behavior:** Lookup is exact-key only. There is no substring or prefix fallback. This is unambiguous.

#### 4. Clarifying Questions

None. Implementation is frozen.

---

### Requirement FADI-3: Composite-Key Cooldown Model in _try_attack()

#### 1. Spec Summary

- **Description:** When `_try_attack()` fires a fused attack, it sets exactly one cooldown entry: `_mutation_cooldowns[composite_key] = attack_resource.cooldown`, where `composite_key` is the sorted `"<id1>_<id2>"` string. It does NOT set `_mutation_cooldowns[a_id]` or `_mutation_cooldowns[b_id]`.
- **Constraints:** `composite_key` is computed inline in `_try_attack()` using the same alphabetical sort as `_make_fused_key()`. The composite key must match the lookup key used earlier in the same call to `get_fused_attack()`.
- **Assumptions:** No external system modifies `_mutation_cooldowns` between the lookup and the fire in the same frame.
- **Scope:** `PlayerController3D._try_attack()` in `scripts/player/player_controller_3d.gd`.

#### 2. Acceptance Criteria

- **FADI-3a:** After a fused attack fires for combo `(a_id, b_id)`, `_mutation_cooldowns` contains an entry for the composite key `"<sorted_lower>_<sorted_higher>"` equal to `attack_resource.cooldown`.
- **FADI-3b:** After a fused attack fires for combo `(a_id, b_id)`, `_mutation_cooldowns` does NOT contain entries for `a_id` or `b_id` as individual keys (unless they were set by a prior independent base attack).
- **FADI-3c:** A subsequent call to `_try_attack()` while `_mutation_cooldowns[composite_key] > 0.0` does not fire any attack and does not modify `_mutation_cooldowns`.
- **FADI-3d:** After `_mutation_cooldowns[composite_key]` decrements to `0.0` (simulated via timer or direct mutation), `_try_attack()` can fire the fused attack again.
- **FADI-3e:** The cooldown value stored equals `attack_resource.cooldown` exactly (no scaling, no additive offset).

#### 3. Risk & Ambiguity Analysis

- **Key parity:** The composite key computed in `_try_attack()` is built inline (not via `_make_fused_key()`). If the two sort/join implementations diverge, the cooldown key and lookup key will not match, causing the cooldown gate to never block (because the check reads the wrong key). Tests must verify key parity.
- **Timer decrement not tested here:** Actual cooldown decrement is handled by a `_process()` loop (or `_physics_process()`). This spec does not require testing the timer tick rate — only that the stored value is correct and that the gate blocks on positive values.
- **No individual-slot cooldown set:** This is the core model (FADI-DD-1). A test that checks `_mutation_cooldowns["acid"]` is unset after a fused fire validates this invariant.

#### 4. Clarifying Questions

None. Implementation is frozen per FADI-DD-1.

---

### Requirement FADI-4: Fused Attack Priority Over Base in _try_attack()

#### 1. Spec Summary

- **Description:** When both mutation slots are filled and a fused attack is registered for `(slot_a_id, slot_b_id)`, `_try_attack()` fires the fused attack and does NOT fire any base attack for that invocation. Fused takes absolute priority.
- **Constraints:** The "both slots filled" check must evaluate `slot_a.is_filled() and slot_b.is_filled()`. Both slots must be filled for the fused path to activate. One filled + one unfilled slot always uses the single-slot base attack path.
- **Assumptions:** State-machine gating (`_input_policy.is_action_permitted(...)`) runs before the fused vs base decision. If the action is not permitted, neither fused nor base fires.
- **Scope:** `PlayerController3D._try_attack()` fused branch.

#### 2. Acceptance Criteria

- **FADI-4a:** Both slots filled + fused attack registered → the fired `AttackResource` is the fused resource, not either slot's base resource.
- **FADI-4b:** Both slots filled + fused attack registered → `_try_attack()` returns after dispatching the fused attack; no base attack `execute_attack()` call is made in the same invocation.
- **FADI-4c:** One slot filled, one slot unfilled → fused path is not entered; the filled slot's base attack fires normally.
- **FADI-4d:** Neither slot filled → `_try_attack()` returns without executing any attack.
- **FADI-4e:** Both slots filled, fused attack registered, fused composite cooldown active → `_try_attack()` returns without executing any attack.

#### 3. Risk & Ambiguity Analysis

- **Signal-based evidence:** `test_adb07_fused_when_both_slots` verifies the correct resource fires by capturing the `attack_started` signal from the `AttackExecutor`. This is the correct approach — behavioral signal evidence, not prose assertion.
- **Slot ordering:** Slot A is `_mutation_slot.get_slot(0)`, slot B is `_mutation_slot.get_slot(1)`. These are fixed indices in `MutationSlotManager`. Tests must use the same indices.

#### 4. Clarifying Questions

None. Implementation is frozen.

---

### Requirement FADI-5: Fallback to Slot A's Base Attack

#### 1. Spec Summary

- **Description:** When both mutation slots are filled but no fused attack is registered for `(slot_a_id, slot_b_id)`, `_try_attack()` falls back to firing slot A's base attack. Slot B's mutation is not used. Slot A's mutation ID is the cooldown key. Slot B's individual cooldown is not checked and not set.
- **Constraints:** The fallback path is slot-A-only by intentional design (FADI-DD-2). This behavior is correct and should not be treated as a bug.
- **Assumptions:** Slot A is consistently `_mutation_slot.get_slot(0)`. Slot B is consistently `_mutation_slot.get_slot(1)`. No assumption is made about which mutation is "more important" — the A/B ordering is structural (slot index), not semantic.
- **Scope:** `PlayerController3D._try_attack()` fallback branch within the both-slots-filled case.

#### 2. Acceptance Criteria

- **FADI-5a:** Both slots filled, no fused attack registered for `(a_id, b_id)` → `_try_attack()` fires slot A's base attack (`get_base_attack(a_id)`).
- **FADI-5b:** After a fallback fire, `_mutation_cooldowns[a_id]` equals the fired base attack's cooldown.
- **FADI-5c:** After a fallback fire, `_mutation_cooldowns.get(b_id, 0.0)` equals `0.0` (slot B's cooldown is not modified).
- **FADI-5d:** The fired `AttackResource` is the same object returned by `db.get_base_attack(a_id)`, not slot B's base attack.
- **FADI-5e:** If slot A's base attack cooldown is active (`_mutation_cooldowns[a_id] > 0.0`), the fallback path is blocked and no attack fires (the shared cooldown gate at line 479 blocks execution).

#### 3. Risk & Ambiguity Analysis

- **Asymmetry is intentional:** The fallback does not check slot B's cooldown before firing. If slot B is on cooldown, that cooldown is irrelevant to this dispatch. Slot B's individual cooldown only blocks slot B's base attack — which this path never fires anyway.
- **Slot B base attack not fired:** Slot B's base attack is unreachable through `_try_attack()` when both slots are filled (either fused fires, or slot A's base fires). This is a deliberate game design choice: slot B's mutation identity is relevant only when it contributes to a fused combo.
- **Test gap before this spec:** The AC checkbox "Tests validate combo matrix coverage (6 unordered combos)" was unchecked before this spec. FADI-5 with FADI-7 (matrix) closes this gap.

#### 4. Clarifying Questions

None. The asymmetry is frozen as intentional per FADI-DD-2.

---

### Requirement FADI-6: Combo Matrix — 6 Unordered Pairs

#### 1. Spec Summary

- **Description:** The four canonical base mutations (`"claw"`, `"acid"`, `"carapace"`, `"adhesion"`) produce exactly 6 unordered combos (C(4,2) = 6). The test suite must cover all 6 pairs both as direct `get_fused_attack()` lookups and as player-dispatch paths through `_try_attack()`. Synthetic `AttackResource` instances are used — real `.tres` files are not required.
- **Constraints:** Tests must use the canonical mutation ID strings defined in `attack_database.gd` (`"claw"`, `"acid"`, `"carapace"`, `"adhesion"`). Tests must exercise both argument orderings (forward and reverse) for each of the 6 pairs.
- **Assumptions:** Real `.tres` fused resources are M12-02's scope. Combo matrix tests must not depend on `_register_defaults()` registering any fused attacks (it does not).
- **Scope:** New test file `tests/scripts/attacks/test_fused_combo_matrix.gd`.

#### 2. Acceptance Criteria

The 6 combo pairs, their sorted composite keys, and required coverage:

| # | Pair | Sorted Key | Forward Lookup | Reverse Lookup | Player Dispatch |
|---|------|-----------|----------------|----------------|-----------------|
| 1 | claw + acid | `"acid_claw"` | FADI-6-1a | FADI-6-1b | FADI-6-1c |
| 2 | claw + carapace | `"carapace_claw"` | FADI-6-2a | FADI-6-2b | FADI-6-2c |
| 3 | claw + adhesion | `"adhesion_claw"` | FADI-6-3a | FADI-6-3b | FADI-6-3c |
| 4 | acid + carapace | `"acid_carapace"` | FADI-6-4a | FADI-6-4b | FADI-6-4c |
| 5 | acid + adhesion | `"acid_adhesion"` | FADI-6-5a | FADI-6-5b | FADI-6-5c |
| 6 | carapace + adhesion | `"adhesion_carapace"` | FADI-6-6a | FADI-6-6b | FADI-6-6c |

Per pair, the specific ACs are:

**Forward lookup (`FADI-6-Na`):** `register_fused_attack(first_id, second_id, res)` then `get_fused_attack(first_id, second_id)` returns `res`.

**Reverse lookup (`FADI-6-Nb`):** `register_fused_attack(first_id, second_id, res)` then `get_fused_attack(second_id, first_id)` returns `res`.

**Player dispatch (`FADI-6-Nc`):** Both mutation slots set to the two mutation IDs for this combo; fused resource registered; `_try_attack()` invoked; `attack_started` signal emitted with the fused resource. Test verifies: (1) fused resource — not a base resource — was fired, and (2) `_mutation_cooldowns[composite_key]` is set.

#### 3. Risk & Ambiguity Analysis

- **Isolation between combos:** Each combo test must use a fresh database instance (or scoped synthetic IDs). Using the shared autoload database without cleanup can cause cross-test contamination. The existing ADB-07 tests demonstrate the pattern (namespaced IDs like `"test_claw_07f"`).
- **Player dispatch setup complexity:** The `_try_attack()` path requires a full pipeline: `PlayerController3D`, `MutationSlotManager` with two filled slots, `AttackDatabase` autoload with the fused resource registered, and `AttackExecutor` with a connected signal. The `_setup_attack_pipeline` helper in the existing integration test must be reused or replicated with two slot IDs.
- **Test file naming:** Per project convention, the file must be named `test_fused_combo_matrix.gd` (behavior-descriptive, no milestone IDs in filename). Traceability (M12-01, FADI-6) belongs in a module docstring.

#### 4. Clarifying Questions

None. The 6-combo table is frozen per FADI-DD-4.

---

### Requirement FADI-7: State-Machine Gating for Fused Attacks

#### 1. Spec Summary

- **Description:** Fused attack dispatch is subject to the same `PlayerInputActionPolicy` state-machine gate as base attacks. `_try_attack()` checks `_input_policy.is_action_permitted(state, ACTION_ATTACK)` before any slot, fused, or base logic. If not permitted, no attack fires.
- **Constraints:** The gate runs on every `_try_attack()` call regardless of how many slots are filled. The fused path does not bypass or short-circuit the gate.
- **Assumptions:** No new player states are introduced for fused attacks (M12-01 scope). Fused attacks fire from the same permitted states as base attacks.
- **Scope:** `PlayerController3D._try_attack()` guard at lines 448–452.

#### 2. Acceptance Criteria

- **FADI-7a:** With both slots filled and a fused attack registered, calling `_try_attack()` while the state machine is in a non-permit state (e.g., `PlayerState.DEAD`) does not fire any attack.
- **FADI-7b:** With both slots filled and a fused attack registered, calling `_try_attack()` while the state machine is in a permit state (e.g., `PlayerState.IDLE`) fires the fused attack.
- **FADI-7c:** The state-machine gate check occurs before slot/fused resolution — no unnecessary `get_slot()` or `get_fused_attack()` calls are made when the gate blocks.

#### 3. Risk & Ambiguity Analysis

- **Gate order is already correct:** `player_controller_3d.gd` lines 448–452 gate before any slot logic. FADI-7c is a code-structure observation; it does not require a behavioral test (the observable outcome is identical regardless of call order when blocked). The behavioral tests FADI-7a and FADI-7b are sufficient.

#### 4. Clarifying Questions

None.

---

## 5. Non-Functional Requirements

### FADI-NF-1: No Fused Attack in _register_defaults()

`AttackDatabaseNode._register_defaults()` registers only the four base attacks. It does not register any fused combos. The `_fused_attacks` dictionary is empty after `_ready()`. Fused attacks are registered by callers (M12-02 will add real resources at runtime; tests use synthetic registration).

**Observable contract:** `get_fused_attack_count() == 0` immediately after `_ready()` on a fresh instance.

### FADI-NF-2: get_fused_attack() Warns on Miss, Does Not Crash

When `get_fused_attack()` finds no entry for a key, it calls `push_warning()` and returns `null`. It must not call `push_error()`, assert, or throw an exception. This is the M11 ADB behavior for base attacks and is consistent.

### FADI-NF-3: Cooldown Key Format Is Deterministic

The composite cooldown key format `"<id1>_<id2>"` (where `id1 < id2` lexicographically) is stable. No changes to this format are permitted without a breaking-change plan revision affecting all callers.

### FADI-NF-4: Self-Fusion Always Returns null

`get_fused_attack("X", "X")` always returns `null`. `_make_fused_key("X", "X")` produces `"X_X"`, but `register_fused_attack()` rejects self-fusion (slot_a == slot_b), so no entry is stored. The lookup behavior is correct by construction.

### FADI-NF-5: run_tests.sh Must Exit 0

All tests for M12-01 (combo matrix tests, adversarial tests, ADB-07) must pass. `bash ci/scripts/run_tests.sh` (or equivalent `timeout 300 godot --headless -s tests/run_tests.gd`) must exit 0 before ticket can advance to COMPLETE.

---

## 6. Edge Cases and Risks

| ID | Edge Case | Behavior | Risk Level |
|----|-----------|----------|-----------|
| FADI-EC-1 | Both slots filled, `a_id == b_id` (same mutation in both slots) | `_make_fused_key("X", "X")` → `"X_X"` which has no registration (self-fusion rejected). Falls back to slot A's base attack. | Low — same mutation in both slots is a game-design-level concern; the database protects against self-fusion registration. |
| FADI-EC-2 | Fused cooldown active; player attempts fused attack | Gate blocks at line 479; no attack fires. | Low — covered by FADI-3c. |
| FADI-EC-3 | Fused attack registered; slot A cooldown also active (from prior base fire) | Composite key is different from `a_id`; if `_mutation_cooldowns["acid_claw"] == 0.0`, fused fires even if `_mutation_cooldowns["claw"] > 0.0`. This is correct — independent keys mean independent timers. | Medium — may surprise developers expecting base cooldowns to block fused attempts. Document explicitly: individual-slot and composite-key cooldowns are independent. |
| FADI-EC-4 | `get_fused_attack()` called with one or both empty strings | Returns null; push_warning emitted. | Low — covered by FADI-2d. |
| FADI-EC-5 | One slot filled, one slot null (slot not initialized) | `b_filled = false` (null slot → is_filled() not called). Falls through to single-slot path. | Low — null guard already present at line 455. |
| FADI-EC-6 | Fused attack fires; base cooldown for `a_id` is 0.0 immediately after | Base cooldown for individual mutations is NOT set by the fused fire path (FADI-DD-1). Slot A's base attack can fire independently if the composite-key cooldown expires and a base path is entered. | Low — this is correct behavior by design. |
| FADI-EC-7 | Composite key collision via unusual IDs | E.g., `"ab"` + `"c"` produces key `"ab_c"`; `"a"` + `"bc"` produces `"a_bc"`. These do not collide. Current canonical IDs (`claw`, `acid`, `carapace`, `adhesion`) produce the 6 unique keys in FADI-DD-4 with no collisions. | Low — canonical IDs are controlled. Risk only if new mutations use names that could produce the same sorted concatenation. |

---

## 7. Test Strategy (for Test Designer Agent)

### Existing Tests That Satisfy Requirements

These tests already exist and must continue to pass:

| Test | File | Requirements Covered |
|------|------|---------------------|
| `test_adb05_register_and_get` | `tests/scripts/attacks/test_attack_database.gd` | FADI-1a |
| `test_adb05_order_independent` | `tests/scripts/attacks/test_attack_database.gd` | FADI-1b, FADI-2b |
| `test_adb05_self_fusion_rejected` | `tests/scripts/attacks/test_attack_database.gd` | FADI-NF-4 |
| `test_adb05_empty_slot_a_rejected` | `tests/scripts/attacks/test_attack_database.gd` | FADI-1d |
| `test_adb05_empty_slot_b_rejected` | `tests/scripts/attacks/test_attack_database.gd` | FADI-1e |
| `test_adb05_null_resource_rejected` | `tests/scripts/attacks/test_attack_database.gd` | FADI-1g |
| `test_adb05_overwrite_fused` | `tests/scripts/attacks/test_attack_database.gd` | FADI-1c |
| `test_adb06_found` | `tests/scripts/attacks/test_attack_database.gd` | FADI-2a |
| `test_adb06_order_independent` | `tests/scripts/attacks/test_attack_database.gd` | FADI-2b, FADI-DD-3 |
| `test_adb06_missing_returns_null` | `tests/scripts/attacks/test_attack_database.gd` | FADI-2c |
| `test_adb06_empty_slot_returns_null` | `tests/scripts/attacks/test_attack_database.gd` | FADI-2d |
| `test_adb07_fused_when_both_slots` | `tests/scripts/attacks/test_attack_database_controller_integration.gd` | FADI-4a, FADI-4b |
| `test_adb07_fused_fallback_to_base` | `tests/scripts/attacks/test_attack_database_controller_integration.gd` | FADI-5a, FADI-5d |

### New Tests Required

All new tests must live in `tests/scripts/attacks/test_fused_combo_matrix.gd`. Traceability in a module docstring: `M12-01, FADI-6`.

**Required new test cases (18 minimum):**

1. **Combo matrix forward lookups** (6 tests): For each of the 6 canonical pairs, register a synthetic resource with `register_fused_attack(a, b, res)` and assert `get_fused_attack(a, b) == res`.
2. **Combo matrix reverse lookups** (6 tests): For each of the 6 canonical pairs, register with `register_fused_attack(a, b, res)` and assert `get_fused_attack(b, a) == res`.
3. **Combo matrix player-dispatch paths** (6 tests): For each of the 6 canonical pairs, set up a full `_try_attack()` pipeline (slots filled with the pair's mutation IDs, fused resource registered, executor signal connected) and assert the fused resource was fired and the composite cooldown key was set.

**Additional required new test cases (adversarial, to be driven by Test Breaker):**

- Fallback cooldown key isolation: verify `_mutation_cooldowns[b_id]` is unset after fallback fire (FADI-5c).
- Composite key and individual key independence: verify `_mutation_cooldowns["acid"]` is unset after `"acid_claw"` composite fires (FADI-EC-3, FADI-3b).
- Both-slot fused cooldown blocks re-fire (FADI-3c).
- State-machine gate blocks fused attack in non-permit state (FADI-7a).
- Null database (no autoload) causes `_try_attack()` to return without crash (existing behavior, confirm survival).

---

## 8. Checkpoint Log Reference

Assumptions made during this spec run are logged at:
`project_board/checkpoints/M12-01/2026-05-28T-spec-run.md`

---

## 9. Revision History

| Revision | Date | Agent | Change |
|----------|------|-------|--------|
| 1 | 2026-05-28 | Spec Agent | Initial frozen spec |
