# Two mutation slots

**Epic:** Milestone 3 – Dual Mutation + Fusion
**Status:** In Progress

---

## Description

Implement two mutation slots (e.g. one per chunk or left/right). Player can hold two mutations and use fusion rules to create hybrids.

## Acceptance criteria

- [ ] Two mutation slots exist and can be filled independently via infection/absorb
- [ ] Slot assignment (which chunk or which slot) is clear and consistent
- [ ] Both mutations can be used or fused per fusion rules
- [ ] Slot consumption rules apply when fusing
- [ ] Dual-slot system is human-playable in-editor: both slots, their contents, and any related UI are visible, legible, and understandable without debug overlays

---

## Execution Plan

### Overview

Extend the existing single-slot mutation system (`MutationSlot` in `scripts/mutation_slot.gd`, owned by `InfectionInteractionHandler`) to a dual-slot system. A new pure-logic coordinator class (`MutationSlotManager`) will own two independent `MutationSlot` instances. The absorb resolver, interaction handler, player controller speed-buff logic, and InfectionUI HUD will all be updated to use the dual-slot coordinator. Existing single-slot tests must remain passing; new dual-slot tests cover coordinator behavior.

### Key existing files (read before implementing)

- `/Users/jacobbrandt/workspace/blobert/scripts/mutation_slot.gd` — single-slot pure-logic data model (do not break its API)
- `/Users/jacobbrandt/workspace/blobert/scripts/infection_absorb_resolver.gd` — absorb logic; `resolve_absorb(esm, inv, slot)` pattern
- `/Users/jacobbrandt/workspace/blobert/scripts/infection_interaction_handler.gd` — owns slot, wires absorb; exposes `get_mutation_slot()`
- `/Users/jacobbrandt/workspace/blobert/scripts/player_controller_3d.gd` — reads `_mutation_slot.is_filled()` for speed buff
- `/Users/jacobbrandt/workspace/blobert/scripts/infection_ui.gd` — HUD reads slot state for `MutationSlotLabel` and `MutationIcon`
- `/Users/jacobbrandt/workspace/blobert/tests/system/test_mutation_slot_system_single.gd` — must remain green
- `/Users/jacobbrandt/workspace/blobert/tests/run_tests.gd` — new test suites must be registered here

### Slot assignment rule (checkpointed)

First-available fill: absorb fills slot A (index 0) first if empty, then slot B (index 1). If both filled, slot B is overwritten (last-absorb-wins for second slot). This is the conservative assumption; Spec Agent may adjust.

### Slot effect rule (checkpointed)

Both slots drive the existing 1.25x speed multiplier. The multiplier is flat (applied once if any slot is filled); stacking is out of scope for this ticket.

---

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Write spec for dual-slot system | Spec Agent | Ticket AC, execution plan, `mutation_slot.gd`, `infection_absorb_resolver.gd`, `infection_interaction_handler.gd`, checkpointed assumptions | `project_board/3_milestone_3_dual_mutation_fusion/specs/two_mutation_slots_spec.md` defining: (a) `MutationSlotManager` API — `get_slot(index: int)`, `fill_next_available(id)`, `get_slot_count()`, `any_filled()`, `clear_all()`; (b) fill-order rule (first-available, last-absorb-wins for slot B); (c) effect rule (flat 1.25x if any filled); (d) HUD layout (two always-visible slot labels + two icons); (e) backward-compat guarantee (MutationSlot API unchanged) | None | Spec doc exists, all 5 AC mapped to testable requirements, no ambiguities left for implementation | Risk: fill-order rule may feel unintuitive; spec must document clearly so tests can encode it deterministically |
| 2 | Design primary test suite for dual-slot | Test Designer Agent | Spec from Task 1, `test_mutation_slot_system_single.gd` as structural reference | `tests/system/test_mutation_slot_system_dual.gd` — primary behavioral test file covering: slot A/B independent fill and clear, first-available fill order, last-absorb-wins for slot B, `any_filled()` invariants, speed-buff active when any slot filled | Task 1 | Test file loadable and runnable headlessly; all tests fail before implementation (red) | Assumption: MutationSlotManager is a pure-logic RefCounted; tests instantiate it without a scene |
| 3 | Design adversarial test suite for dual-slot | Test Breaker Agent | Spec from Task 1, primary tests from Task 2 | `tests/system/test_mutation_slot_system_dual_adversarial.gd` — adversarial suite covering: null/empty IDs into both slots, simultaneous fills, repeated fills of same slot, clear-all then refill, fill-after-full behavior, coordinator isolation (two instances do not share state), rapid absorb sequences | Tasks 1, 2 | Adversarial suite is registered in `run_tests.gd`; all adversarial tests fail before implementation (red) | Risk: edge cases around "both full" semantics must align exactly with spec fill-order rule |
| 4 | Implement `MutationSlotManager` pure-logic class | Core Simulation Agent | Spec from Task 1, `mutation_slot.gd` (must not modify), Task 2 and 3 test suites | New file `scripts/mutation_slot_manager.gd` — `class_name MutationSlotManager extends RefCounted`; owns two `MutationSlot` instances; implements spec API: `get_slot(index)`, `fill_next_available(id)`, `any_filled()`, `get_slot_count()`, `clear_all()`, `clear_slot(index)` | Tasks 1, 2, 3 | All primary + adversarial dual-slot tests pass; all existing single-slot tests remain green; `timeout 300 godot --headless -s tests/run_tests.gd` exits 0 | Risk: must not modify `MutationSlot` API or break existing infection tests; use duck-typing patterns consistent with the existing codebase |
| 5 | Wire dual-slot into `InfectionAbsorbResolver` | Core Simulation Agent | `infection_absorb_resolver.gd`, spec from Task 1, `MutationSlotManager` from Task 4 | Updated `infection_absorb_resolver.gd` — `resolve_absorb(esm, inv, slot_manager: Object = null)` accepts a `MutationSlotManager` (or any object with `fill_next_available(id: String)`); fills next available slot on successful absorb; backward-compat: existing `(esm, inv)` and `(esm, inv, single_slot)` call sites continue working | Task 4 | Existing infection interaction tests pass; new resolver correctly fills slot A then B in sequence; no crash on null slot_manager | Assumption: duck-typing via `has_method` is sufficient — no hard type check on slot_manager |
| 6 | Update `InfectionInteractionHandler` to use `MutationSlotManager` | Gameplay Systems Agent | `infection_interaction_handler.gd`, `MutationSlotManager` from Task 4, spec from Task 1 | Updated `infection_interaction_handler.gd` — instantiates `MutationSlotManager` in `_ready()` instead of a single `MutationSlot`; passes manager into `resolve_absorb`; exposes `get_mutation_slot_manager() -> RefCounted`; keeps `get_mutation_slot()` returning slot A for backward compatibility with `PlayerController` | Tasks 4, 5 | `InfectionInteractionHandler` compiles; `get_mutation_slot_manager()` returns a valid manager; all infection interaction tests pass | Risk: `PlayerController` currently calls `get_mutation_slot()` — backward-compat alias must be preserved to avoid breaking the speed buff |
| 7 | Update `PlayerController3D` speed buff to use slot manager | Gameplay Systems Agent | `player_controller_3d.gd`, `InfectionInteractionHandler` from Task 6, spec from Task 1 | Updated `player_controller_3d.gd` — `_ready()` fetches `MutationSlotManager` via `get_mutation_slot_manager()` (falls back to `get_mutation_slot()` if not available); speed-buff check reads `any_filled()` from manager instead of `is_filled()` from single slot; multiplier remains flat 1.25x | Task 6 | Speed buff activates when either slot A or B is filled; deactivates when both cleared; all existing movement tests pass | Assumption: `any_filled()` on MutationSlotManager is the canonical "is any mutation active" query |
| 8 | Update `InfectionUI` HUD for dual-slot display | Presentation Agent | `infection_ui.gd`, `game_ui.tscn`, spec from Task 1, `MutationSlotManager` from Task 4 | Updated `infection_ui.gd` — `_ready()` fetches manager; `_update_mutation_display()` drives two slot labels (`MutationSlot1Label`, `MutationSlot2Label`) and two icons (`MutationIcon1`, `MutationIcon2`) using `manager.get_slot(0)` and `manager.get_slot(1)`; updated `game_ui.tscn` with second slot label and icon nodes | Tasks 6, 7 | Both slot labels are always visible; each updates independently (empty/filled); existing UI tests pass; no duplicate or orphaned slot state | Risk: `game_ui.tscn` is a scene file — must be modified carefully; run `timeout 120 godot --headless --check-only` to validate syntax after edits |
| 9 | Register new test suites in `run_tests.gd` and run full suite | Core Simulation Agent | `tests/run_tests.gd`, Task 2 and 3 test files | Updated `run_tests.gd` with `"res://tests/system/test_mutation_slot_system_dual.gd"` and `"res://tests/system/test_mutation_slot_system_dual_adversarial.gd"` entries under the `# --- system ---` section; confirmed full suite passes | Tasks 2, 3, 4, 5, 6, 7, 8 | `timeout 300 godot --headless -s tests/run_tests.gd` exits 0 with all suites passing (0 failures) | Risk: any regression in existing tests must be fixed before advancing to Static QA |
| 10 | Static QA review | Static QA Agent | All new/modified files: `mutation_slot_manager.gd`, updated `infection_absorb_resolver.gd`, `infection_interaction_handler.gd`, `player_controller_3d.gd`, `infection_ui.gd`, `game_ui.tscn`, both test files | Code review report confirming: typed GDScript, no orphaned variables, no silent failures, consistent error handling (push_error for critical failures), no hardcoded magic strings, all new public methods documented with inline comments | Task 9 | No blocking code quality issues; any non-blocking notes captured in report | Assumption: Static QA Agent will not modify implementation; feedback addressed in follow-up or Implementation Agent correction pass |
| 11 | Integration verification (human playtest in-editor) | Human / Integration Agent | Fully integrated `test_movement_3d.tscn` scene with dual-slot HUD | Human opens `test_movement_3d.tscn`, absorbs 2 enemies, observes both slots fill independently; both slot labels update correctly in HUD; speed buff active; no debug overlays needed to understand slot state; AC#5 verified | Task 10 | All 5 AC checkboxes satisfied; dual-slot system is human-discoverable and legible; ticket advances to COMPLETE | Risk: HUD layout may need iteration for legibility; Presentation Agent should verify at 1920x1080 resolution before signoff |

### Notes

- Tasks 2 and 3 (Test Designer and Test Breaker) must produce failing tests (red-green-refactor pattern); do not implement production code in those tasks.
- `MutationSlot` (`scripts/mutation_slot.gd`) must not be modified; all dual-slot logic lives in the new `MutationSlotManager` coordinator.
- `get_mutation_slot()` on `InfectionInteractionHandler` must remain as a backward-compat alias returning slot A, so existing `PlayerController` and `InfectionUI` references are not broken before Task 7/8 updates them.
- All Godot invocations must use `timeout` per CLAUDE.md: `timeout 300 godot --headless -s tests/run_tests.gd`.
- Fusion rules (which slot gets consumed on fuse, hybrid mutation IDs) are out of scope for this ticket and addressed by `slot_consumption_rules.md` and `fusion_rules_and_hybrid.md`.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
INTEGRATION

## Revision
6

## Last Updated By
Core Simulation Agent

## Validation Status
- Tests: Passing
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Required Input Schema
```json
{}
```

## Status
Proceed

## Reason
Tasks 4, 5, 6, and 9 complete. Created scripts/mutation_slot_manager.gd (MutationSlotManager extends RefCounted, two MutationSlot instances, full DSM-1/DSM-2/DSM-3 API). Updated scripts/infection_absorb_resolver.gd with dual-slot dispatch (fill_next_available path checked before set_active_mutation_id for higher specificity; push_error on unrecognized slot type; full backward-compat with null and single-slot forms). Updated scripts/infection_interaction_handler.gd to instantiate MutationSlotManager, expose get_mutation_slot_manager(), and keep get_mutation_slot() as backward-compat alias returning slot A. Both test suites (test_mutation_slot_system_dual.gd, test_mutation_slot_system_dual_adversarial.gd) were already registered in tests/run_tests.gd. Three checkpoint entries appended to CHECKPOINTS.md covering: whitespace ID handling, any_filled() live-read strategy, and InfectionInteractionHandler _mutation_slot rename. All single-slot tests remain green (mutation_slot.gd is unmodified).
