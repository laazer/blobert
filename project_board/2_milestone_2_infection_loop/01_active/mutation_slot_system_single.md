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
INTEGRATION

## Revision
9

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: Passing (core MutationSlot model, infection interaction, infection UI, and gameplay wiring suites green; full suite executed via `tests/run_tests.gd` against current revision)
- Static QA: Not Run (`godot --headless --check-only` not yet executed for this ticket scope)
- Integration: Not Run – no documented manual in-editor play session verifying mutation slot behavior, UI clarity, and absence of duplicate or lost mutations across normal infection flows.

## Blocking Issues
- Manual in-editor verification is not yet documented for the following acceptance criteria: one mutation slot exists and is filled on absorb from infected enemies; mutation effect is usable in gameplay; slot state is clear (filled/empty) and consistent with UI; no duplicate or lost mutations in normal flow; mutation slot system is human-playable in-editor with mutation, slot state, and related UI visible and understandable without debug overlays.

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
Needs Attention

## Reason
Automated tests and updated HUD presentation provide strong evidence for mutation slot behavior and UI wiring, but there is no documented manual in-editor integration check yet for the human-playable and no-duplicates acceptance criteria; holding the ticket in Stage INTEGRATION and routing to a Human to perform and record a short play session that explicitly confirms all acceptance criteria before this ticket can be advanced to COMPLETE.

