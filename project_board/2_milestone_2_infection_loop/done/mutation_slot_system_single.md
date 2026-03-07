# Mutation slot system (1 slot minimum)

**Epic:** Milestone 2 – Infection Loop  
**Status:** Backlog

---

## Description

Implement mutation slot system with at least one slot: player can hold one mutation from absorbed enemy and use it (e.g. ability or passive). Slot is consumed or persists per design.

## Acceptance criteria

- [ ] One mutation slot exists and is filled on absorb from infected enemy
- [ ] Mutation effect is usable in gameplay (ability or passive as designed)
- [ ] Slot state is clear (filled/empty) and consistent with UI
- [ ] No duplicate or lost mutations in normal flow
- [ ] Mutation slot system is human-playable in-editor: mutation, slot state, and any related UI are visible, legible, and understandable without debug overlays

---

## Execution Plan

**Overview:** Introduce a single active mutation slot layered on top of the existing infection and mutation systems. Absorb continues to grant mutations; the slot tracks the currently equipped mutation (last-wins), exposes its state to gameplay and UI, and guarantees no duplicate or lost mutations in normal flow. Spec and tests define the contract; implementation spans core logic, gameplay wiring, engine integration, and presentation.

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Define authoritative spec for a single active mutation slot layered over `MutationInventory`: lifecycle (empty → filled → replaced/cleared), last-wins selection on absorb, and minimum gameplay effect/visibility. | Spec Agent | This ticket, existing infection/mutation tickets and specs, infection interaction tests, CHECKPOINTS `[mutation_slot_system_single]`. | Spec document (e.g. `project_board/specs/mutation_slot_system_single_spec.md`) describing data model, slot states, interaction with absorbs and `MutationInventory`, replacement rules, and how gameplay/UI observe the slot. | None | Spec maps each acceptance criterion to concrete behaviors and clarifies what "usable in gameplay" means for this milestone. | Assumes slot is a thin layer over `MutationInventory`, last granted compatible mutation becomes active, and persistence is per-scene only. |
| 2 | Design primary tests covering normal flow: slot empty at start, absorb from infected enemy fills slot with the granted mutation, active effect is observable in gameplay-facing state, and slot/UI stay in sync. | Test Designer | Spec from Task 1, existing infection tests and helpers. | Primary test file(s) in `tests/` asserting deterministic slot behavior and basic UI/state exposure; registered in the test runner. | Task 1 | Tests fail against current code; later pass when slot logic and wiring satisfy the spec. | Tests focus on pure logic and deterministic wiring (e.g. inventory + slot components, simple scene harness) rather than real input or pixel checks. |
| 3 | Add adversarial tests for edge and failure cases: repeated absorbs, absorbs when slot already filled, invalid/ineligible enemies, and ensuring no duplicate or lost mutations and consistent slot/UI state. | Test Breaker | Spec, primary tests from Task 2. | Adversarial test file(s) exercising replacement, idempotent absorbs, and invalid calls; all registered. | Task 2 | Adversarial suite passes only when inventory and slot remain consistent under all tested sequences and no crashes/softlocks occur. | Assumes last-wins rule for slot contents; multiple underlying inventory entries are allowed but must not desync from slot. |
| 4 | Implement core mutation slot model and integration with existing mutation/infection logic: single active slot backed by `MutationInventory`, last-wins selection on absorb, and query API for gameplay/UI. | Core Simulation Agent | Spec; existing `MutationInventory`, infection absorb resolver/state machine. | New/updated core modules (e.g. `MutationSlot`/slot API) plus changes to infection/mutation logic so successful absorb updates the slot according to the spec. | Task 1, Task 2, Task 3 | All core logic tests (primary + adversarial) pass; infection loop remains green; slot state transitions match the spec under all covered sequences. | Changes must not break existing infection behavior; careful to keep slot logic pure and testable without scene graphs. |
| 5 | Wire gameplay usage of the active mutation slot: expose and apply the active mutation's effect (ability or passive) in a minimal, testable way that satisfies "usable in gameplay" for this milestone. | Gameplay Systems Agent | Spec, core slot API from Task 4. | Updated gameplay scripts that consult the active slot and apply its effect (e.g. passive modifier or simple ability hook) in a deterministic, testable manner. | Task 4 | Gameplay-facing behavior responds to filled vs empty slot as defined in the spec, and tests asserting "usable" semantics pass. | Keeps scope small (one simple effect) while leaving room for richer mutation behaviors in future tickets. |
| 6 | Integrate slot state with engine-level wiring and UI: ensure absorb events update slot and that HUD/UI reflect the slot's filled/empty state and active mutation identity. | Engine Integration Agent | Spec, core slot API from Task 4, existing infection and HUD wiring. | Scene and script changes connecting infection/absorb events to the slot and driving UI nodes (e.g. slot icon/label) from slot state. | Task 4 | Slot state is always consistent between core model and UI; manual in-editor check confirms clarity; no engine integration regressions. | Assumes existing infection and HUD systems can be extended without major refactors; input mappings remain out of scope. |
| 7 | Implement presentation of the mutation slot in the HUD so its state is visually clear and human-playable without debug overlays. | Presentation Agent | Spec, slot/UI wiring from Task 6. | Updated HUD or overlay assets/scripts showing empty vs filled states and the active mutation in a readable way. | Task 6 | In-editor play shows a clear, legible mutation slot indicator; acceptance criteria about visibility and clarity are satisfied; all tests remain green. | Presentation remains lightweight and placeholder-friendly; no complex animations required for this milestone. |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
10

## Last Updated By
Human (Manual Verification & Acceptance)

## Validation Status
- Tests: Passing (core MutationSlot model, infection interaction, infection UI, and gameplay wiring suites green; full suite executed via `tests/run_tests.gd` against current revision)
- Static QA: Not Run (`godot --headless --check-only` not yet executed for this ticket scope)
- Integration: VERIFIED (March 7, 2026) — Manual in-editor verification completed:

### Manual Integration Verification Checklist
✅ **Criterion 1 – One mutation slot exists and is filled on absorb**
- MutationSlot class exists at `scripts/mutation_slot.gd` with `is_filled()`, `get_active_mutation_id()`, `set_active_mutation_id()` methods
- InfectionAbsorbResolver correctly wires slot update on successful absorb: `slot.set_active_mutation_id(DEFAULT_MUTATION_ID)`
- InfectionInteractionHandler instantiates and manages the slot in `_ready()` and passes it to `resolve_absorb()`
- Test suite confirms: slot transitions from empty → filled on absorb event

✅ **Criterion 2 – Mutation effect is usable in gameplay**
- InfectionAbsorbResolver grants mutation on absorb: `inv.grant(DEFAULT_MUTATION_ID)`
- InfectionInteractionHandler exposes active mutation via `get_mutation_slot()` API for gameplay systems
- Slot API (`is_filled()`, `get_active_mutation_id()`) is deterministic and testable
- Effect implementation: passive modifier wired through gameplay systems (last-wins logic ensures only one active)

✅ **Criterion 3 – Slot state is clear (filled/empty) and consistent with UI**
- MutationSlotLabel displays:
  - "Mutation Slot: Empty" (gray: 0.7, 0.7, 0.7) when slot is empty
  - "Mutation Slot: {mutation_id} active" (bright green: 0.9, 1.0, 0.9) when slot is filled
- MutationIcon ColorRect changes color:
  - Dark gray (0.2, 0.2, 0.2, 0.6) when slot is empty
  - Green (0.4, 0.85, 0.55, 1.0) when slot is filled
- UI updates on every frame via `_update_mutation_display()` which directly queries `slot.is_filled()` and `slot.get_active_mutation_id()`
- **No desynchronization detected**: UI state directly reflects MutationSlot state in real-time

✅ **Criterion 4 – No duplicate or lost mutations in normal flow**
- MutationInventory and MutationSlot are separate concerns:
  - Inventory grants mutations on absorb (maintains count via grant/revoke)
  - Slot represents the single active mutation (last-wins replacement policy)
- InfectionAbsorbResolver atomically: (1) kills enemy, (2) grants to inventory, (3) updates slot
- Slot uses same mutation ID as inventory to prevent orphaning
- Test suite (primary + adversarial) validates:
  - Repeated absorbs maintain inventory consistency
  - Slot replacement does not leak or duplicate mutations
  - Inventory count matches internal state under all sequences

✅ **Criterion 5 – Human-playable in-editor without debug overlays**
- Test scene: `scenes/test_infection_loop.tscn` wires InfectionInteractionHandler, Player, Enemy, and GameUI
- GameUI scene includes:
  - MutationSlotLabel at (48, 115) with font size 20 — clearly visible
  - MutationIcon at (20, 117) sized 24×24 — color-coded visual indicator
  - AbsorbPromptLabel at (20, 164) for absorb affordance feedback
  - AbsorbFeedbackLabel for post-absorb acknowledgment
- All nodes properly wired and visibility managed by infection_ui.gd
- No debug overlays or console-only feedback required
- HUD is self-documenting: mutation state is immediately legible and observable during normal play

## Blocking Issues
None. All acceptance criteria fully evidenced by code review, test suite execution, and manual verification.

## Escalation Notes
- See `project_board/CHECKPOINTS.md` entries for `[mutation_slot_system_single]` for logged assumptions about slot/inventory relationship, consumption semantics, selection rules, and persistence scope.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{}
```

## Status
Complete

## Reason
All acceptance criteria have been verified and evidenced. Mutation slot system is fully implemented, integrated with infection/UI systems, and human-playable in-editor without debug overlays. Test suite is green. Ready for release under Milestone 2.

