# Slot consumption rules

**Epic:** Milestone 3 – Dual Mutation + Fusion
**Status:** In Progress

---

## Description

Implement slot consumption rules for fusion: after fusion, slots are cleared, refilled, or partially consumed per design so progression and balance are clear.

## Acceptance criteria

- [ ] After fusion, slot state is updated consistently (e.g. both cleared, hybrid in one slot)
- [ ] Player can regain mutations via infection/absorb after fusion
- [ ] Rules are documented and behavior is deterministic
- [ ] No duplicate or ghost mutations
- [ ] Slot consumption behavior is human-playable in-editor: changes to slots and mutations are visibly and clearly reflected in game objects and UI without debug overlays

---

## Execution Plan

### Overview

This ticket defines the state transitions of `MutationSlotManager` slots after a fusion event fires. The fusion trigger and hybrid outcome live in `fusion_rules_and_hybrid.md`. This ticket is exclusively concerned with: what happens to slot A and slot B contents after the fusion function runs, whether the player can re-infect after fusion, and that no invalid slot states (ghost or duplicate IDs) can result.

The `MutationSlotManager` API (`clear_all()`, `clear_slot(index)`, `fill_next_available(id)`, `any_filled()`, `get_slot_count()`, `is_slot_filled(index)`, `get_slot_id(index)`) is already implemented. This ticket adds a documented, tested consumption function that callers (fusion trigger code) will invoke after a successful fusion.

**Conservative design decisions (see CHECKPOINTS.md for full rationale):**
- After fusion: both slots are cleared (`clear_all()` — all-or-nothing consumption).
- Player CAN re-infect after fusion (no lock-out state).
- No ghost IDs: cleared slots are empty string, `is_filled()` returns false.
- No duplicate mutations: clearing is complete before any re-fill can occur.

---

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Write formal spec for slot consumption rules | Spec Agent | This ticket, `MutationSlotManager` API (`scripts/mutation_slot_manager.gd`), `two_mutation_slots_spec.md`, conservative assumptions from CHECKPOINTS.md | `project_board/3_milestone_3_dual_mutation_fusion/specs/slot_consumption_rules_spec.md` covering: (a) the `consume_fusion_slots()` function contract, (b) all-or-nothing clear rule, (c) re-infection allowed post-fusion, (d) ghost/duplicate prevention, (e) edge cases (one slot empty at fusion time, fusion called with no slots filled) | None | Spec file exists with numbered requirements SCR-1 through SCR-5; each has acceptance criteria that a Test Designer Agent can translate directly into headless test assertions | Risk: if `fusion_rules_and_hybrid` ticket defines a different consumption model than all-or-nothing, specs conflict. Assumption: all-or-nothing is the agreed conservative default; this spec is authoritative for slot state only. |
| 2 | Write primary behavioral test suite | Test Designer Agent | `slot_consumption_rules_spec.md` from Task 1 | `tests/system/test_slot_consumption_rules.gd` — headless GDScript suite covering all SCR-* acceptance criteria; test names match spec AC IDs | Task 1 | All tests parseable by `timeout 120 godot --headless --check-only`; test count matches number of AC assertions in spec; suite registered in `tests/run_tests.gd` under `# --- system ---` | Risk: if spec omits an edge case (e.g., fusion called when only one slot filled), tests will miss coverage. Spec Agent must be explicit about all edge cases. |
| 3 | Write adversarial (mutation/stress) test suite | Test Breaker Agent | `slot_consumption_rules_spec.md` from Task 1, primary suite from Task 2 | `tests/system/test_slot_consumption_rules_adversarial.gd` — adversarial cases: rapid repeated fusion calls, fill-after-clear ordering, fill with empty string post-fusion, concurrent clear and fill, ghost ID verification (slot returns empty string after clear), fill count invariant after multiple fusion cycles | Tasks 1, 2 | Adversarial suite registered in `tests/run_tests.gd`; suite is independently runnable headless; no test asserts a behavior contradicting the spec | Risk: if `MutationSlotManager.clear_all()` has a latent bug under certain call orderings, adversarial tests will surface it. Assumption: the existing `clear_all()` implementation is correct per prior test suites. |
| 4 | Implement `consume_fusion_slots()` on `MutationSlotManager` | Core Simulation Agent | `slot_consumption_rules_spec.md` from Task 1, primary + adversarial test suites from Tasks 2-3 | Modified `scripts/mutation_slot_manager.gd` with a new public method `consume_fusion_slots() -> void` that calls `clear_all()` internally; method is documented with a comment stating "Called by fusion trigger after a successful fusion event; clears both slots so the player can re-infect" | Tasks 1, 2, 3 | `timeout 120 godot --headless --check-only` exits 0; `timeout 300 godot --headless -s tests/run_tests.gd` exits 0 with 0 failures; `consume_fusion_slots()` is callable on a fresh `MutationSlotManager` instance without a scene tree | Risk: adding a new method may conflict with future fusion ticket that expects a different method name or signature. Assumption: `consume_fusion_slots()` is the agreed function name; fusion caller will invoke this exact method. |
| 5 | Register test suites in run_tests.gd | Core Simulation Agent | `tests/run_tests.gd` (current), test file paths from Tasks 2-3 | Updated `tests/run_tests.gd` with both new suites registered under `# --- system ---`; full suite continues to exit 0 | Tasks 2, 3, 4 | `timeout 300 godot --headless -s tests/run_tests.gd` exits 0 with 0 failures across all suites including the two new ones | Risk: if run_tests.gd has a fixed load order that conflicts with new files, registration may fail silently. Check that the runner iterates the system section without hardcoded counts. |
| 6 | Static QA review of implementation | Static QA Agent | `scripts/mutation_slot_manager.gd` (post-Task 4), spec, test suites | Written QA report (inline comment or checkpoint entry): confirm typed return types, no magic strings, `push_error` on invalid states per NFR-3, no Node dependencies introduced, no regressions to prior test suites | Task 4 | 0 blocking issues found; any warnings documented in CHECKPOINTS.md with confidence level; `timeout 120 godot --headless --check-only` exits 0 | Risk: implementer may add a scene-tree dependency to `consume_fusion_slots()` inadvertently (e.g., a signal emit). Must remain pure-logic (`extends RefCounted`). |
| 7 | Human in-editor playtest (AC5 gate) | Human | Integrated game scene `scenes/test_movement_3d.tscn` with `MutationSlotManager` wired; fusion trigger from `fusion_rules_and_hybrid.md` must be partially wired or stubbed to call `consume_fusion_slots()` | Playtest log or sign-off: (a) absorb two enemies, (b) trigger fusion (or stub), (c) observe both slot labels update to "Slot N: Empty" immediately, (d) re-absorb one enemy, (e) observe slot A fills again — no crash, no stale IDs visible | Tasks 4, 5, 6; fusion_rules_and_hybrid.md wiring (partial or stub acceptable) | AC5 signed off: human confirms slot state changes are visible in HUD without debug overlays, re-infection works post-fusion, no ghost IDs appear in UI | Risk: fusion trigger wiring may not be available yet (depends on `fusion_rules_and_hybrid.md` being in progress). If so, a manual test stub (call `consume_fusion_slots()` from a test button or GDScript console) is acceptable for AC5 verification. |

---

## Notes

- Tasks 1-6 are fully autonomous (no human interaction required).
- Task 7 is the only human-gated task (AC5 sign-off).
- Tasks 2 and 3 can be executed in parallel once Task 1 is complete.
- Task 4 can begin once Tasks 1, 2, and 3 are all complete (implementation follows spec + tests, not the reverse).
- This ticket does not implement the fusion trigger or the hybrid outcome — those live in `fusion_rules_and_hybrid.md`. The boundary is: `fusion_rules_and_hybrid.md` decides when and whether fusion fires; this ticket owns what happens to slot state immediately after.
- The `consume_fusion_slots()` method name is the coordination contract between these two tickets. If `fusion_rules_and_hybrid.md` uses a different calling convention, resolve the naming conflict before Task 4.

---

## WORKFLOW STATE

```
Stage:              COMPLETE
Revision:           5
Created By:         Human
Created On:         2026-03-12T00:00:00Z
Last Updated By:    Human
Last Updated On:    2026-03-14T00:00:00Z
Next Responsible Agent: None
Status:             Complete
Validation Status:  All AC satisfied. Tests: 640 passed, 0 failed (2026-03-14). Integration: human playtest confirmed 2026-03-14 — absorbed two enemies (both slot labels showed mutation IDs), triggered consume_fusion_slots() via debug key, both labels updated to empty immediately, re-absorbed one enemy (slot A filled, no crash, no stale IDs). AC1–AC5 all satisfied. Debug keybinding removed post sign-off.
Blocking Issues:    None.
```

---

## NEXT ACTION

**Agent:** None
**Action:** Complete.
**Reason:** All acceptance criteria satisfied. Debug stub removed.
**Blocking Issues:** None.
