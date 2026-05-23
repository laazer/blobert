# M11-01 Test Breaker Run — 2026-05-23

**Run id:** `2026-05-23T-test-break-run`  
**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/backlog/01_player_state_machine.md`  
**Stage:** TEST_BREAK → IMPLEMENTATION_GENERALIST

---

## Outcome

- Adversarial suite: `tests/scripts/player/test_player_state_machine_adversarial.gd` (33 test functions)
- Coverage: EC-1..EC-10 (spec Edge Cases table) + ADV-001..ADV-007 (naming isolation, epsilon boundaries, hurt exit, guard consistency, stress/isolation)
- Ticket stage: `IMPLEMENTATION_GENERALIST`, revision 5
- Handoff: `handoff-latest.yaml` (test_breaker → implementation / Gameplay Systems Agent)

---

## Test Evidence (RED — expected)

Command:

```bash
timeout 120 godot --headless --path . -s tests/run_tests.gd
```

Adversarial section (module absent):

```
  FAIL: adv_denied_timer — res://scripts/player/player_state_machine.gd not found or not loadable; implement PlayerStateMachine per PSM-1

  Results: 0 passed, 45 failed
```

Primary suite (same run, excerpt):

```
--- test_player_state_machine.gd ---
  FAIL: psm1_script_exists — res://scripts/player/player_state_machine.gd not found or not loadable; implement PlayerStateMachine per PSM-1
  ...
  Results: 0 passed, 31 failed
```

Combined RED state is correct before `scripts/player/player_state_machine.gd` exists.

---

## EC Traceability

| EC | Adversarial tests |
|----|-------------------|
| EC-1 | `test_ec1_*` (DEAD terminal, same-state no-op, reset required) |
| EC-2 | `test_ec2_*` (double notify / HURT re-entry) |
| EC-3 | `test_ec3_*` (DEAD overrides JUMP/FALL derivation) |
| EC-4 | `test_ec4_*` (ABSORB > MUTATE) |
| EC-5 | `test_ec5_*` (landing vs cling precedence) |
| EC-6 | `test_ec6_*` (same-state no-op all states) |
| EC-7 | `test_ec7_*` (update(0.0) repeated) |
| EC-8 | `test_ec8_*` (reset clears hurt latch) |
| EC-9 | `test_ec9_*` (FLOAT denied from IDLE/groundish) |
| EC-10 | `test_ec10_*` (HURT flash vs DEAD at zero HP) |

---

## Gaps Documented (for implementation)

| Gap | Conservative assumption encoded in tests |
|-----|------------------------------------------|
| HURT exit frame | `test_adv_hurt_exits_next_sync_without_new_damage` — second `sync_from_context` without new damage returns IDLE when `MIN_HURT_SEC == 0` |
| FLOAT epsilon | `test_adv_float_from_jump_blocked_at_epsilon_below_min` uses `MIN_FLOAT_FROM_JUMP_SEC - 1e-6` |
| Naming | `test_adv_movement_state_class_distinct_from_player_state_enum` — `MovementSimulation` must not define `PlayerState` enum |
| Guard API | `test_adv_can_transition_matches_transition_denials` — `can_transition_to` must match `transition()` per fresh machine from DEAD/HURT |

---

## Workflow Transition Gates

```
transition=test_break_to_implementation ticket_id=M11-01
  (run after handoff/todos update)
```
