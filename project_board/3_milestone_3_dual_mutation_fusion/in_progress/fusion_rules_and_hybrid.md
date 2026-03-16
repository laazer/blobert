# Fusion rules and hybrid creation

**Epic:** Milestone 3 – Dual Mutation + Fusion
**Status:** In Progress

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | TEST_BREAK |
| Revision | 5 |
| Last Updated By | Test Designer Agent |
| Next Responsible Agent | Test Breaker Agent |
| Validation Status | — |
| Blocking Issues | — |

## NEXT ACTION
Test Breaker Agent: review `tests/fusion/test_fusion_resolver.gd` (primary suite, 20 failing tests, 2 passing). Write adversarial suite at `tests/fusion/test_fusion_resolver_adversarial.gd` covering partial-slot guard (only A filled, only B filled, both empty), double-fuse, fuse with null player, and no crash on any invalid input path. All tests must be headless-safe and in TDD red-phase. Spec is at `agent_context/agents/2_spec/fusion_rules_and_hybrid_spec.md`.

---

## Description

Define and implement fusion rules: when two mutations are present, player can create a hybrid (e.g. combined ability or new effect). At least one fusion works end-to-end.

## Acceptance criteria

- [ ] Fusion is triggered by defined input/condition when two slots are filled
- [ ] At least one hybrid outcome is implemented and usable in gameplay
- [ ] Fusion consumes slots or applies slot consumption rules as designed
- [ ] No crash or undefined state; fusion is repeatable in play
- [ ] Fusion behavior is human-playable in-editor: hybrids, their effects, and any related UI are visible and understandable without debug overlays

---

## Execution Plan

### Overview

The fusion feature has five rule groups:

- **FRH-1 Input Action** — A new `"fuse"` input action is registered in `project.godot`.
- **FRH-2 Fusion Guard** — Fusion can only be triggered when both mutation slots are filled (`slot_manager.get_slot(0).is_filled() and slot_manager.get_slot(1).is_filled()`).
- **FRH-3 Fusion Resolver** — A new pure-logic script `scripts/fusion/fusion_resolver.gd` implements `can_fuse(slot_manager)` and `resolve_fusion(slot_manager, player_node)`.
- **FRH-4 Hybrid Effect** — The first hybrid outcome is a timed speed boost applied to `PlayerController3D` via a new `apply_fusion_effect(duration: float, multiplier: float)` method.
- **FRH-5 Slot Consumption** — On successful fusion, `slot_manager.consume_fusion_slots()` is called (already implemented on MutationSlotManager). Slots become empty; player can re-infect immediately.

### Architectural decisions (consumed by Spec Agent)

1. **FusionResolver** is a new `RefCounted` script at `scripts/fusion/fusion_resolver.gd`, analogous to `InfectionAbsorbResolver`. It has no Node or Input dependencies and is headless-testable.
2. **InfectionInteractionHandler** gains a `_fusion_resolver` field and calls `FusionResolver.can_fuse` / `resolve_fusion` from `_process` on `Input.is_action_just_pressed("fuse")`. No new Node is needed; the handler already owns the `_slot_manager` reference and a reference to the player can be obtained via `get_tree().get_first_node_in_group("player")`.
3. **PlayerController3D** gains a `apply_fusion_effect(duration: float, multiplier: float)` method that uses a delta counter (`_fusion_timer`) tracked in `_physics_process` and overrides `_simulation.max_speed` during the effect, then restores `_base_max_speed * _MUTATION_SPEED_MULTIPLIER` on expiry.
4. **InfectionUI** gains a `FusePromptLabel` Label node driven each frame in `_process`: visible when both slots are filled, hidden otherwise. Text shows the fuse key hint. Follows the `AbsorbPromptLabel` pattern exactly.
5. **Input action name:** `"fuse"`, mapped to the G key (physical_keycode 71). Registered in `project.godot` alongside existing actions. Spec Agent confirms or overrides.
6. **Hybrid effect parameters (defaults):** speed multiplier 1.5, duration 5.0 seconds. Spec Agent finalises.
7. **No cooldown.** Fusion is immediately repeatable after re-filling both slots.
8. **MutationSlotManager.both_filled()** — optional convenience method. Spec Agent decides; FusionResolver uses the two `get_slot().is_filled()` calls directly if the method is not added.

### Task table

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|---|---|---|---|---|---|---|
| 1 | Author fusion spec (`fusion_rules_and_hybrid_spec.md`) | Spec Agent | This ticket; execution plan above; `scripts/mutation/mutation_slot_manager.gd`; `scripts/infection/infection_interaction_handler.gd`; `scripts/player/player_controller_3d.gd`; `scripts/ui/infection_ui.gd` | Spec file at `agent_context/agents/2_spec/fusion_rules_and_hybrid_spec.md` defining FRH-1 through FRH-5 rule groups, all API contracts with typed signatures, and all acceptance criteria measurable by tests | None | Spec covers all five rule groups; every AC has at least one measurable test criterion; API contracts are fully typed | Spec Agent must confirm fuse key and hybrid effect parameters; log decisions to CHECKPOINTS.md |
| 2 | Write primary test suite (`test_fusion_resolver.gd`) | Test Design Agent | Spec from Task 1; `scripts/mutation/mutation_slot_manager.gd` (headless-safe) | `tests/fusion/test_fusion_resolver.gd` with TDD red-phase tests covering FRH-2 (guard: both-filled required), FRH-3 (resolver API), FRH-5 (consume called on success); all tests fail until Task 4 | Task 1 | All tests parse without errors and run headlessly; failing tests precisely enumerate unimplemented symbols | FusionResolver does not yet exist; tests must use `has_method` guards (same TDD pattern as slot_consumption_rules tests) |
| 3 | Write adversarial test suite (`test_fusion_resolver_adversarial.gd`) | Test Breaker Agent | Spec from Task 1; primary suite from Task 2 | `tests/fusion/test_fusion_resolver_adversarial.gd` with adversarial matrix: partial-slot guard (only slot A filled, only slot B filled, both empty), double-fuse, fuse with null player, no crash on any invalid input path | Tasks 1, 2 | Adversarial suite exposes at least 6 distinct failure modes that a naive implementation would miss | FusionResolver and both_filled guard not yet implemented; same TDD red-phase pattern applies |
| 4 | Implement `FusionResolver` (pure logic) | Core Simulation Agent | Spec from Task 1; failing tests from Tasks 2–3 | `scripts/fusion/fusion_resolver.gd` with `can_fuse(slot_manager: Object) -> bool` and `resolve_fusion(slot_manager: Object, player: Object) -> void`; optionally add `both_filled() -> bool` to `MutationSlotManager` if spec requires it | Tasks 1, 2, 3 | All fusion resolver tests (primary + adversarial) pass; full existing test suite remains green; `run_tests.sh` exits 0 | Must not modify MutationSlot or MutationSlotManager beyond adding `both_filled()` if spec requires; no Node dependencies in FusionResolver |
| 5 | Wire fuse input action in `project.godot` | Gameplay Systems Agent | Spec from Task 1 (confirmed key); existing `project.godot` input block | `project.godot` updated with `fuse` action entry; key follows spec | Task 1 | `Input.is_action_just_pressed("fuse")` resolves at runtime without error; no existing actions broken; `run_tests.sh` still exits 0 | Spec Agent must confirm key before this task runs; G key assumed unless overridden |
| 6 | Implement fusion effect on `PlayerController3D` and wire handler | Gameplay Systems Agent | Spec from Task 1; `FusionResolver` from Task 4; `scripts/player/player_controller_3d.gd`; `scripts/infection/infection_interaction_handler.gd` | `PlayerController3D.apply_fusion_effect(duration, multiplier)` implemented; `InfectionInteractionHandler._process` calls `FusionResolver.can_fuse` and `resolve_fusion` on fuse input; speed boost active during effect, restored after | Tasks 4, 5 | Speed boost measurably applies and expires; slots consumed after fusion; player can re-infect and fuse again; `run_tests.sh` exits 0 | Timer must not use `await` inside `_physics_process`; use a `_fusion_timer` delta counter pattern |
| 7 | Add `FusePromptLabel` to InfectionUI and drive from `_process` | Gameplay Systems Agent | Spec from Task 1; `scripts/ui/infection_ui.gd`; InfectionUI scene | `FusePromptLabel` Label node added to InfectionUI scene; `infection_ui.gd._process` drives visibility: visible iff both slots filled; text shows fuse key hint | Tasks 1, 6 | Label is visible in-editor when both slots are filled; hidden otherwise; no crash if node absent from scene; `run_tests.sh` exits 0 | Must use null-safe `get_node_or_null` pattern matching existing `_get_*_label()` helpers |
| 8 | Static QA pass | Static QA Agent | All modified files from Tasks 4–7 | QA report confirming: no `push_error` silenced, no dangling signals, no untyped return values on public methods, no `await` in physics loops, no leftover debug prints | Tasks 4, 5, 6, 7 | Zero CRITICAL issues; all WARNINGs documented with rationale | — |
| 9 | Integration verification (manual + automated) | Gameplay Systems Agent | Running game on `test_movement_3d.tscn`; `run_tests.sh` | Checklist: (a) both slots fill after absorbing two enemies, (b) FusePromptLabel appears, (c) fuse input triggers speed boost, (d) slots clear, (e) prompt disappears, (f) player can re-infect and fuse again, (g) full test suite green | Tasks 6, 7, 8 | All checklist items confirmed; `run_tests.sh` exits 0; ticket AC checkboxes all ticked | Human verification required for in-editor playability AC |

### File ownership map

| File | Owner task(s) |
|---|---|
| `agent_context/agents/2_spec/fusion_rules_and_hybrid_spec.md` | Task 1 (create) |
| `tests/fusion/test_fusion_resolver.gd` | Task 2 (create) |
| `tests/fusion/test_fusion_resolver_adversarial.gd` | Task 3 (create) |
| `scripts/fusion/fusion_resolver.gd` | Task 4 (create) |
| `scripts/mutation/mutation_slot_manager.gd` | Task 4 (optional: add `both_filled()`) |
| `project.godot` | Task 5 (modify: add fuse action) |
| `scripts/player/player_controller_3d.gd` | Task 6 (modify: add `apply_fusion_effect`) |
| `scripts/infection/infection_interaction_handler.gd` | Task 6 (modify: wire fuse input + resolver) |
| `scripts/ui/infection_ui.gd` | Task 7 (modify: add fuse prompt logic) |
| InfectionUI scene (`.tscn`) | Task 7 (modify: add FusePromptLabel node) |

### Risk register

| Risk | Mitigation |
|---|---|
| `apply_fusion_effect` timer conflicts with existing `_MUTATION_SPEED_MULTIPLIER` logic | Spec must define precedence: fusion multiplier overrides mutation multiplier during active effect; implementation uses a separate `_fusion_active: bool` flag and restores `_base_max_speed * _MUTATION_SPEED_MULTIPLIER` after expiry |
| `InfectionInteractionHandler` needs player reference at runtime | Use `get_tree().get_first_node_in_group("player")` consistent with InfectionUI's existing pattern |
| FusePromptLabel node absent from scene causes NullRef | All InfectionUI accessors use `get_node_or_null`; absence is a cosmetic miss, not a crash |
| `fuse` action missing from project.godot causes `is_action_just_pressed` to push_error at runtime | Task 5 must be completed before Task 6 ships; both assigned to Gameplay Systems Agent |
| Existing `slot_consumption_rules` tests interfere if `both_filled()` added to MutationSlotManager | Adding a new method is backwards-compatible; existing tests do not call `both_filled()` |
