# Spec: Slot Consumption Rules
**Ticket:** `slot_consumption_rules.md`
**Epic:** Milestone 3 – Dual Mutation + Fusion
**Spec Stage:** SPECIFICATION
**Last Updated By:** Spec Agent
**Date:** 2026-03-13

---

## Context Summary

After a successful fusion event fires, the `MutationSlotManager` holding the two input mutations must be updated to a clean, well-defined state. This spec defines the single coordination function `consume_fusion_slots()` that the fusion trigger (owned by `fusion_rules_and_hybrid.md`) will call immediately after fusion succeeds. It also defines all invariants that must hold after that call, across all edge-case input states.

The `MutationSlotManager` API (`clear_all()`, `clear_slot(index)`, `fill_next_available(id)`, `any_filled()`, `get_slot_count()`, `get_slot(index)`) and the `MutationSlot` API (`is_filled()`, `get_active_mutation_id()`, `set_active_mutation_id(id)`, `clear()`) are frozen. This ticket adds exactly one new public method to `MutationSlotManager` and no other changes to those files.

The function name `consume_fusion_slots()` is the naming contract between this ticket and `fusion_rules_and_hybrid.md`. If that ticket uses a different calling convention, the conflict must be resolved before implementation begins (see SCR-1 Risk section).

---

## Out of Scope (Explicit)

The following are explicitly not covered by this spec:

- Deciding whether fusion should fire (that is `fusion_rules_and_hybrid.md`'s responsibility).
- The hybrid mutation outcome or hybrid mutation ID produced by fusion.
- Any UI or HUD update triggered by slot clearing (covered by the HUD ticket and `DSM-4`).
- Slot consumption for non-fusion events (e.g., manual player discard, timeout expiry).
- Partial slot consumption (one slot cleared, one retained) — the all-or-nothing rule is locked in.
- Save/load persistence of slot state across sessions.
- Any change to `MutationSlot` (`scripts/mutation/mutation_slot.gd`).

---

## Requirement SCR-1: `consume_fusion_slots()` Function Contract

### 1. Spec Summary

**Description:** A new public method `consume_fusion_slots() -> void` is added to `MutationSlotManager` in `scripts/mutation/mutation_slot_manager.gd`. This method is the single, canonical coordination point that the fusion trigger calls after a successful fusion event. Its entire implementation is a delegation to `clear_all()`.

**Exact signature:**
```
func consume_fusion_slots() -> void
```

**Constraints:**
- Return type is `void`. The caller (fusion trigger) receives no return value and must not rely on one.
- The method must be callable on a `MutationSlotManager` instance that `extends RefCounted`, with no scene tree, no Node parent, and no autoloads required. It is a pure-logic method.
- The method must not emit signals, modify any state outside of `MutationSlotManager`'s own `_slots` array, or introduce any Node or scene-tree dependency.
- The method must not call `push_error` under any normal or edge-case input condition (including when both slots are already empty). Silent success is correct behavior for all input states.
- The method must be documented with an inline comment stating its purpose and caller contract. Exact wording: `# Called by the fusion trigger after a successful fusion event. Clears both slots so the player can re-infect.`
- The method must delegate to `clear_all()` internally. It must not reimplement the clearing logic directly (e.g., must not call `_slots[0].clear()` directly), so that any future changes to `clear_all()` propagate automatically.

**Assumptions:**
- The fusion trigger will call `consume_fusion_slots()` exactly once per fusion event. Multiple calls in succession are allowed and must be safe (idempotent).
- The implementer does not need to guard against concurrent calls; GDScript is single-threaded.
- No logging, analytics, or side-effects beyond slot clearing are required by this ticket.

**Scope:** `scripts/mutation/mutation_slot_manager.gd` only. The method is added; no existing methods are modified.

### 2. Acceptance Criteria

- **SCR-1-AC-1:** `MutationSlotManager` has a callable method named `consume_fusion_slots` (verified via `manager.has_method("consume_fusion_slots") == true` on a freshly instantiated manager with no scene tree).
- **SCR-1-AC-2:** `consume_fusion_slots()` returns no value (the call does not produce a non-void result; calling it does not crash when its return is ignored).
- **SCR-1-AC-3:** `consume_fusion_slots()` can be called on a `MutationSlotManager` instance created via `load("res://scripts/mutation/mutation_slot_manager.gd").new()` without a running scene tree. No crash, no error.
- **SCR-1-AC-4:** After `consume_fusion_slots()` is called, the observable state of the manager is identical to the state after calling `clear_all()` directly (both slots empty, `any_filled()` returns `false`). This is verified by calling `clear_all()` on a reference manager and `consume_fusion_slots()` on an identically pre-filled manager, then asserting the same post-call state on both.
- **SCR-1-AC-5:** Calling `consume_fusion_slots()` twice in succession on the same manager does not crash and leaves both slots empty after both calls.
- **SCR-1-AC-6:** `timeout 120 godot --headless --check-only` exits 0 after the method is added.

### 3. Risk & Ambiguity Analysis

- **Risk — naming conflict with `fusion_rules_and_hybrid.md`:** If that ticket's fusion trigger calls a differently-named method (e.g., `clear_slots_after_fusion()`), the implementation will not be invoked. Resolution: confirm the name `consume_fusion_slots()` with the `fusion_rules_and_hybrid.md` author before Task 4 begins. The ticket's Notes section already flags this as a required pre-implementation check.
- **Risk — delegation vs. reimplementation:** If the implementer reimplements the clear loop instead of delegating to `clear_all()`, future changes to `clear_all()` (e.g., emitting a signal) will not propagate. The spec requires delegation explicitly.
- **Edge case — method called before `_init()` completes:** Not possible in GDScript; `_init()` runs synchronously before any external caller can reach the instance.

### 4. Clarifying Questions

None. The function name and delegation rule are locked in via CHECKPOINTS.md. The only open item is the cross-ticket naming confirmation described in the Risk section above; that is a pre-implementation coordination step, not a blocker for this spec.

---

## Requirement SCR-2: All-or-Nothing Clear Rule

### 1. Spec Summary

**Description:** When `consume_fusion_slots()` is called, both slot A (index 0) and slot B (index 1) are cleared atomically via the single `clear_all()` call. There is no partial consumption: it is never the case that one slot is cleared and the other is left filled after `consume_fusion_slots()` returns.

"Atomically" in this context means: within a single GDScript call frame, both slots are cleared before `consume_fusion_slots()` returns. Because GDScript is single-threaded, no interleaved reads can observe a state where one slot is cleared and the other is not.

The "all-or-nothing" design decision is permanent for this ticket. Partial consumption (e.g., clearing only the slot that contributed the weaker mutation) is explicitly out of scope and must not be implemented.

**Constraints:**
- After `consume_fusion_slots()` returns, `manager.get_slot(0).is_filled()` must be `false` regardless of what `get_slot(0)` held before the call.
- After `consume_fusion_slots()` returns, `manager.get_slot(1).is_filled()` must be `false` regardless of what `get_slot(1)` held before the call.
- Both constraints above must hold simultaneously, not sequentially. There is no observable intermediate state.
- The clearing is unconditional: the fusion trigger does not need to pre-check slot states before calling `consume_fusion_slots()`. The function handles all input states safely (see SCR-5).

**Assumptions:**
- The design rationale for all-or-nothing (from CHECKPOINTS.md): preserving one mutation post-fusion would introduce asymmetric slot state that complicates re-infection ordering and HUD display. The conservative choice is a clean slate.
- If the design evolves to partial consumption in a future ticket, the change will require a new spec revision and a method rename or overload to avoid silent behavior changes at existing call sites.

**Scope:** The behavioral guarantee of `consume_fusion_slots()` in `MutationSlotManager`. No changes to `MutationSlot`.

### 2. Acceptance Criteria

- **SCR-2-AC-1:** After `consume_fusion_slots()` on a manager where both slots are filled (slot A = `"mutation_a"`, slot B = `"mutation_b"`), `get_slot(0).is_filled()` is `false` and `get_slot(1).is_filled()` is `false`.
- **SCR-2-AC-2:** After `consume_fusion_slots()` on a manager where both slots are filled, `any_filled()` returns `false`.
- **SCR-2-AC-3:** After `consume_fusion_slots()` on a manager where slot A is filled (`"mutation_a"`) and slot B is empty, `get_slot(0).is_filled()` is `false` and `get_slot(1).is_filled()` is `false`. (One-filled case: slot A is cleared, slot B remains unaffected — already empty.)
- **SCR-2-AC-4:** After `consume_fusion_slots()` on a manager where slot A is empty and slot B is filled (`"mutation_b"`), `get_slot(0).is_filled()` is `false` and `get_slot(1).is_filled()` is `false`. (One-filled case: slot B is cleared, slot A remains unaffected — already empty.)
- **SCR-2-AC-5:** `consume_fusion_slots()` does not partially clear: there is no code path where `get_slot(0).is_filled()` is `false` and `get_slot(1).is_filled()` is `true` after the call, nor the reverse, when both were filled before the call.

### 3. Risk & Ambiguity Analysis

- **Risk — `clear_all()` future regression:** If `clear_all()` is later modified to skip a slot under some condition, `consume_fusion_slots()` will silently inherit the bug. Tests for SCR-2 must assert both slots independently to catch this, rather than only asserting `any_filled()`.
- **Edge case — slot B filled, slot A empty (out-of-normal-fill-order):** This state can arise if `clear_slot(0)` was called manually. `consume_fusion_slots()` must handle it correctly (both cleared). SCR-2-AC-4 covers this case.

### 4. Clarifying Questions

None.

---

## Requirement SCR-3: Re-Infection Allowed Post-Fusion

### 1. Spec Summary

**Description:** After `consume_fusion_slots()` is called and both slots are empty, the player must be able to re-fill slots by absorbing new infected enemies. The call to `consume_fusion_slots()` must not set any lock-out flag, internal state, or side-effect that prevents `fill_next_available(id)` from working normally on subsequent calls.

"Working normally" means the fill-order rule from DSM-2 applies in full: slot A is filled first, slot B second, and if both are full, slot B is overwritten. This behavior is identical to a freshly constructed `MutationSlotManager` with no prior history.

**Constraints:**
- After `consume_fusion_slots()`, the manager must be in a state functionally indistinguishable from a freshly instantiated `MutationSlotManager`. There is no "post-fusion" mode, "cooldown" field, or internal flag that `consume_fusion_slots()` sets.
- `fill_next_available("mutation_a")` called immediately after `consume_fusion_slots()` must fill slot A (index 0), not slot B.
- No guard in `fill_next_available()` or `consume_fusion_slots()` may prevent re-filling. If such a guard were needed (e.g., a fusion cooldown), it would be the responsibility of the caller (fusion trigger in `fusion_rules_and_hybrid.md`), not `MutationSlotManager`.
- `consume_fusion_slots()` must not modify `_slots` in any way other than calling `clear_all()`. It must not append, remove, or replace slot instances.

**Assumptions:**
- Re-infection is unlimited: the player can absorb, fuse, and re-absorb indefinitely within a session. No session-level cap on fusion count is defined by this ticket.
- If a fusion cooldown is desired, it will be implemented as state on the fusion trigger object, not on `MutationSlotManager`.

**Scope:** Post-call state of `MutationSlotManager` after `consume_fusion_slots()`. Incidentally covers `fill_next_available()` behavior, which is unchanged.

### 2. Acceptance Criteria

- **SCR-3-AC-1:** After `consume_fusion_slots()`, `fill_next_available("mutation_x")` fills slot A: `get_slot(0).get_active_mutation_id() == "mutation_x"` and `get_slot(1).is_filled() == false`.
- **SCR-3-AC-2:** After `consume_fusion_slots()` followed by `fill_next_available("mutation_x")` and `fill_next_available("mutation_y")`, slot A holds `"mutation_x"` and slot B holds `"mutation_y"` (normal fill-order resumes).
- **SCR-3-AC-3:** A full cycle — fill both slots, call `consume_fusion_slots()`, fill both slots again — produces slot A = `"mutation_c"` and slot B = `"mutation_d"` when called with those IDs in that order after the clear. Slot A is not `"mutation_a"` or `"mutation_b"` (the pre-fusion values).
- **SCR-3-AC-4:** Multiple full cycles (fill → consume → fill → consume → fill) do not accumulate state. After N cycles, the slot state after the final fill reflects only the most recent fills, not any prior-cycle data.
- **SCR-3-AC-5:** `MutationSlotManager` does not expose any `_post_fusion`, `_locked`, or equivalent field after `consume_fusion_slots()` (no new instance variable is introduced by the method).

### 3. Risk & Ambiguity Analysis

- **Risk — fusion-trigger-side lock-out:** The fusion trigger (`fusion_rules_and_hybrid.md`) may implement a cooldown that prevents re-infection at the trigger level, even though `MutationSlotManager` itself allows it. That is acceptable and out of scope for this spec. This spec only guarantees that `MutationSlotManager` does not block re-infection.
- **Edge case — `fill_next_available` called with `""` after `consume_fusion_slots()`:** This is already guarded by the DSM-2 `push_error` rule. Behavior is unchanged: `push_error` is called, slots remain empty, no crash.

### 4. Clarifying Questions

None.

---

## Requirement SCR-4: Ghost and Duplicate Prevention

### 1. Spec Summary

**Description:** After `consume_fusion_slots()` returns, both slots must be in a definitively empty state with no ghost IDs, no stale mutation ID strings, and no possibility of a slot falsely reporting itself as filled. "Ghost ID" is defined as any state where `get_active_mutation_id()` returns a non-empty string while `is_filled()` returns `false`, or where `is_filled()` returns `true` while `get_active_mutation_id()` returns `""`. Neither inversion may exist after `consume_fusion_slots()`.

Duplicate mutations are prevented by requiring that any `fill_next_available()` call after `consume_fusion_slots()` starts from a fully-cleared state. Because clearing is complete before any re-fill can occur (the two operations are in separate call frames driven by separate game events), there is no window in which a slot could be partially filled with a stale ID.

**Constraints:**
- After `consume_fusion_slots()`, for every slot index `i` in `{0, 1}`:
  - `get_slot(i).is_filled()` must be `false`.
  - `get_slot(i).get_active_mutation_id()` must equal `""` (empty string, not `null`, not any other sentinel).
- These two invariants must hold simultaneously and for both slots together.
- The `MutationSlot.clear()` implementation already guarantees that `_active_mutation_id = ""` sets both invariants correctly (from the frozen `mutation_slot.gd`). This spec relies on that guarantee being maintained.
- No new field, secondary ID store, or shadow variable may be introduced to `MutationSlot` or `MutationSlotManager` by this ticket that could hold a stale ID after clearing.

**Assumptions:**
- `MutationSlot.clear()` is the authoritative clearing mechanism. Its correctness is established by prior test suites (`test_mutation_slot_system_single.gd`) and is not re-verified here except through the post-`consume_fusion_slots()` assertions.
- Because `MutationSlot` is frozen, no ghost-ID regression can be introduced at that level by this ticket.

**Scope:** Post-call state invariants of both `MutationSlot` instances managed by `MutationSlotManager` after `consume_fusion_slots()`.

### 2. Acceptance Criteria

- **SCR-4-AC-1:** After `consume_fusion_slots()` on a fully-filled manager (both slots had non-empty IDs), `get_slot(0).get_active_mutation_id() == ""`.
- **SCR-4-AC-2:** After `consume_fusion_slots()` on a fully-filled manager, `get_slot(1).get_active_mutation_id() == ""`.
- **SCR-4-AC-3:** After `consume_fusion_slots()` on a fully-filled manager, `get_slot(0).is_filled() == false`.
- **SCR-4-AC-4:** After `consume_fusion_slots()` on a fully-filled manager, `get_slot(1).is_filled() == false`.
- **SCR-4-AC-5:** The two invariants are consistent per slot: `get_slot(0).is_filled() == false` AND `get_slot(0).get_active_mutation_id() == ""` simultaneously (no ghost ID inversion on slot A).
- **SCR-4-AC-6:** The two invariants are consistent per slot: `get_slot(1).is_filled() == false` AND `get_slot(1).get_active_mutation_id() == ""` simultaneously (no ghost ID inversion on slot B).
- **SCR-4-AC-7:** After `consume_fusion_slots()` followed immediately by `fill_next_available("mutation_new")`, `get_slot(0).get_active_mutation_id() == "mutation_new"` and `get_slot(1).get_active_mutation_id() == ""`. No pre-fusion ID (`"mutation_a"` or `"mutation_b"`) appears in either slot.
- **SCR-4-AC-8:** After multiple fill-and-consume cycles, no ID from a prior cycle appears in either slot after `consume_fusion_slots()` returns. (Example: cycle 1 fills `"x1"` and `"x2"`, cycle 2 fills `"x3"` and `"x4"`; after cycle 2's `consume_fusion_slots()`, neither `"x1"`, `"x2"`, `"x3"`, nor `"x4"` appears in either slot.)

### 3. Risk & Ambiguity Analysis

- **Risk — `get_active_mutation_id()` returns `null` instead of `""`:** The `MutationSlot` implementation stores `_active_mutation_id: String = ""` and `clear()` sets it to `""`. There is no path to `null` in the current implementation. Tests should assert `== ""` (not just falsy) to catch a future regression that returns `null`.
- **Risk — new shadow state:** If the implementer adds any caching, logging, or history field to `MutationSlotManager` as part of `consume_fusion_slots()`, a stale ID could live in that field. The spec prohibits this. Static QA must verify no new instance variables are introduced.
- **Edge case — slot object identity:** After `consume_fusion_slots()`, `get_slot(0)` and `get_slot(1)` must return the same object instances as before the call (slots are cleared in-place, not replaced). Tests may optionally verify object identity if object replacement is suspected.

### 4. Clarifying Questions

None.

---

## Requirement SCR-5: Edge Cases — Fusion Called With Fewer Than Two Slots Filled

### 1. Spec Summary

**Description:** `consume_fusion_slots()` must behave safely and correctly when called in states other than the normal "both slots filled" pre-condition. Specifically:

**Edge case A — One slot filled, one slot empty:**
The fusion trigger in `fusion_rules_and_hybrid.md` is responsible for verifying that both slots are filled before deciding to fire fusion. However, `consume_fusion_slots()` must not assume its pre-condition is met. If called with only one slot filled, it must clear both slots (leaving the non-filled slot in its already-empty state) without crashing or emitting an error.

**Edge case B — Both slots empty:**
If called when no slots are filled (e.g., the fusion trigger has a bug, or the method is called twice in succession), `consume_fusion_slots()` must complete silently. Both slots remain empty. No error is emitted.

**Rationale:** Because `consume_fusion_slots()` delegates entirely to `clear_all()`, and `clear_all()` iterates all slots and calls `clear()` on each, and `MutationSlot.clear()` sets `_active_mutation_id = ""` unconditionally (idempotent on an already-empty slot), both edge cases are naturally handled by the delegation without any additional guarding code. This spec formalizes that guarantee so that tests and callers can rely on it.

**Constraints:**
- `consume_fusion_slots()` must not contain any pre-condition check that would cause it to return early, push an error, or skip clearing when called with zero or one slot filled.
- `consume_fusion_slots()` must not crash when slot A is filled and slot B is empty, or vice versa, or when both are empty.
- After the call in any edge case, both `get_slot(0).is_filled()` and `get_slot(1).is_filled()` must be `false`.
- The behavior must be identical regardless of which slot was filled in the one-slot-filled case.

**Assumptions:**
- The fusion trigger (`fusion_rules_and_hybrid.md`) is responsible for checking `any_filled()` or slot count before deciding whether to fire fusion. This ticket does not add that guard to `consume_fusion_slots()`, by design.
- "Both slots empty before call, both slots empty after call" is the correct and expected result for edge case B. It is not an error condition from `MutationSlotManager`'s perspective.

**Scope:** Safety guarantees of `consume_fusion_slots()` under degenerate input states. No new code paths are required; the behavior follows from the delegation to `clear_all()`.

### 2. Acceptance Criteria

**Edge case A — One slot filled:**

- **SCR-5-AC-1:** `consume_fusion_slots()` called with only slot A filled (`"mutation_a"`) and slot B empty: no crash, no `push_error` call, method returns normally.
- **SCR-5-AC-2:** After the call in SCR-5-AC-1: `get_slot(0).is_filled() == false` and `get_slot(0).get_active_mutation_id() == ""`.
- **SCR-5-AC-3:** After the call in SCR-5-AC-1: `get_slot(1).is_filled() == false` and `get_slot(1).get_active_mutation_id() == ""` (slot B was already empty; it remains empty and is not erroneously modified to a non-empty value).
- **SCR-5-AC-4:** `consume_fusion_slots()` called with only slot B filled (`"mutation_b"`) and slot A empty: no crash, no `push_error` call, method returns normally.
- **SCR-5-AC-5:** After the call in SCR-5-AC-4: `get_slot(0).is_filled() == false` and `get_slot(1).is_filled() == false`.

**Edge case B — Both slots empty:**

- **SCR-5-AC-6:** `consume_fusion_slots()` called on a freshly instantiated manager (both slots empty from construction): no crash, no `push_error` call, method returns normally.
- **SCR-5-AC-7:** After the call in SCR-5-AC-6: `get_slot(0).is_filled() == false` and `get_slot(1).is_filled() == false` (state unchanged from before the call).
- **SCR-5-AC-8:** `consume_fusion_slots()` called twice in succession on any manager state (both-filled, one-filled, or both-empty): no crash, no error, and after the second call both slots are empty.
- **SCR-5-AC-9:** `any_filled()` returns `false` after `consume_fusion_slots()` regardless of the pre-call slot state (both-filled, one-filled, or both-empty).

### 3. Risk & Ambiguity Analysis

- **Risk — caller assumes pre-condition enforcement:** If the fusion trigger assumes `consume_fusion_slots()` will return early or emit an error when called with empty slots, and the implementer adds that guard, it would break edge case B (SCR-5-AC-6 through SCR-5-AC-9). This spec explicitly prohibits the guard.
- **Risk — test coverage gap:** Edge case A with slot B filled and slot A empty (SCR-5-AC-4, SCR-5-AC-5) can only arise if `clear_slot(0)` was called manually or if absorption logic has a bug. Tests must still cover it because `consume_fusion_slots()` is a general-purpose method, not one restricted to normal absorption sequences.
- **Edge case — slot index out of range:** `get_slot_count()` is always 2, so there are no slot indices beyond 0 and 1. No out-of-range slot index can be in scope for this method's behavior.

### 4. Clarifying Questions

None. Edge case behavior is fully determined by the delegation-to-`clear_all()` rule and the idempotency of `MutationSlot.clear()`.

---

## Non-Functional Requirements

### NFR-1: Pure-Logic Isolation

`consume_fusion_slots()` must be callable in a headless Godot process with no scene tree. All test suites for this ticket must be executable via `timeout 300 godot --headless -s tests/run_tests.gd`.

### NFR-2: Typed GDScript

The new method uses an explicit `-> void` return type annotation. No new untyped variables may be introduced.

### NFR-3: No Silent Failures on Invalid States

`consume_fusion_slots()` explicitly does NOT call `push_error` for any input state (including both-empty and one-filled). Silence on degenerate input is correct behavior per SCR-5. This is a deliberate exception to the project's general NFR-3 (push_error on invalid states); the rationale is that partial-fill and empty calls are valid caller states, not errors.

### NFR-4: No Magic Strings

`consume_fusion_slots()` does not reference any mutation ID strings. It delegates entirely to `clear_all()`, which in turn calls `clear()` on each `MutationSlot`. No new string literals are introduced.

### NFR-5: Godot Syntax Validity

After the method is added, `timeout 120 godot --headless --check-only` must exit 0.

### NFR-6: Test Suite Registration

Both `tests/system/test_slot_consumption_rules.gd` (primary suite, Test Designer Agent) and `tests/system/test_slot_consumption_rules_adversarial.gd` (adversarial suite, Test Breaker Agent) must be registered in `tests/run_tests.gd` under the `# --- system ---` section. The full suite `timeout 300 godot --headless -s tests/run_tests.gd` must exit 0 after implementation.

### NFR-7: No Node Dependencies

`MutationSlotManager` must remain `extends RefCounted`. `consume_fusion_slots()` must not introduce any `Node`, `SceneTree`, `get_node`, signal emission, or autoload reference.

---

## Requirement-to-Ticket AC Cross-Reference

| Ticket AC | Covered By Spec Requirement |
|-----------|----------------------------|
| After fusion, slot state is updated consistently (both cleared — all-or-nothing) | SCR-2 |
| Player can regain mutations via infection/absorb after fusion (no lock-out) | SCR-3 |
| Rules are documented and behavior is deterministic | SCR-1 (function contract), SCR-2 (all-or-nothing rule), SCR-5 (edge cases) |
| No duplicate or ghost mutations | SCR-4 |
| Slot consumption behavior is human-playable in-editor | SCR-3-AC-3 (observable re-infection cycle); full in-editor verification is human gate (Task 7 in ticket) |

---

## Implementation File Ownership Summary

| File | Owner Task | Change Type |
|------|-----------|-------------|
| `scripts/mutation/mutation_slot_manager.gd` | Task 4 (Core Simulation Agent) | Add `consume_fusion_slots()` method |
| `scripts/mutation/mutation_slot.gd` | None — FROZEN | No change |
| `tests/system/test_slot_consumption_rules.gd` | Task 2 (Test Designer Agent) | Create new |
| `tests/system/test_slot_consumption_rules_adversarial.gd` | Task 3 (Test Breaker Agent) | Create new |
| `tests/run_tests.gd` | Task 5 (Core Simulation Agent) | Register both new suites |
