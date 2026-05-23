# M11-01 Test Designer Run — 2026-05-23

**Run id:** `2026-05-23T-test-design-run`  
**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/backlog/01_player_state_machine.md`  
**Stage:** TEST_DESIGN → TEST_BREAK

---

## Outcome

- Primary tests: `tests/scripts/player/test_player_state_machine.gd` (34 test functions, 49 assertions — RED)
- Spec traceability: PSM-1..PSM-9 (unit); PSM-10 controller wiring deferred to implementation; PSM-11 enum-count only
- Adversarial suite: **deferred** to Test Breaker (`test_player_state_machine_adversarial.gd` per spec Test Strategy)
- Ticket stage: `TEST_BREAK`, revision 4
- Handoff: `handoff-latest.yaml` (test_designer → test_breaker)

---

## Test Evidence (RED — expected)

Command:

```bash
timeout 120 godot --headless --path . -s tests/run_tests.gd
```

Sample failures (module absent):

```
  FAIL: psm1_script_exists — res://scripts/player/player_state_machine.gd not found or not loadable; implement PlayerStateMachine per PSM-1
  FAIL: psm1_refcounted — res://scripts/player/player_state_machine.gd not found or not loadable; implement PlayerStateMachine per PSM-1
  ...
=== FAILURES: 49 test(s) failed ===
```

Suite section summary:

```
--- test_player_state_machine.gd ---
  Results: 0 passed, 49 failed
```

All failures stem from missing `scripts/player/player_state_machine.gd` — correct RED state before implementation.

---

## Spec ↔ Test Map

| Spec | Tests |
|------|-------|
| PSM-1 | `test_psm1_*` (load, RefCounted, class_name) |
| PSM-2 | `test_psm2_*` (IDLE initial, enum count 10) |
| PSM-3 | `test_psm3_*` (timer increment/reset/same-state/update(0)) |
| PSM-4 | `test_psm4_*` (G-DEAD, G-HURT, G-FLOAT, walk→dead) |
| PSM-5 | `test_psm5_*` (denied/allowed transition side effects) |
| PSM-6 | `test_psm6_*` (MIN_FLOAT_FROM_JUMP 0.04/0.05, MIN_HURT_SEC) |
| PSM-7 | `test_psm7_*` (derivation priority + kinematic splits) |
| PSM-8 | `test_psm8_*` (notify_damage, double HURT guard) |
| PSM-9 | `test_psm9_*` (reset from DEAD, sync sticky DEAD) |

---

## Gaps / Test Breaker Focus

- EC-1..EC-10 adversarial cases per spec Edge Cases table
- `MovementState` naming isolation (no conflation with `MovementSimulation.MovementState`)
- Timer epsilon at `MIN_FLOAT_FROM_JUMP_SEC` boundary
- `sync_from_context` + hurt latch consumption on following frame (AC-PSM-8.3)

---

## Workflow Transition Gates

```
transition=test_design_to_test_break ticket_id=M11-01
  todo_validation_check: PASS — All todos completed for Test Designer Agent.
  handoff_validation_check: PASS — Handoff checklist valid for test_designer→test_breaker.
```
