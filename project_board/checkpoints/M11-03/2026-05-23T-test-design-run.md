# M11-03 Test Designer checkpoint

**Agent:** Test Designer Agent  
**Date:** 2026-05-24  
**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/in_progress/03_input_action_mapping.md`

## Artifacts

| Artifact | Path |
|----------|------|
| Primary tests | `tests/scripts/player/test_player_input_action_policy.gd` |
| Spec | `project_board/specs/input_action_mapping_spec.md` |
| Policy impl (deferred) | `scripts/player/player_input_action_policy.gd` — **absent** |

## Registration

`tests/run_tests.gd` auto-discovers `test_*.gd` under `res://tests/` (no explicit registration; same as `test_player_state_machine.gd`).

## Test execution evidence

```text
$ timeout 300 godot --headless -s tests/run_tests.gd 2>&1 | grep -A 35 "test_player_input_action_policy"
--- test_player_input_action_policy.gd ---
  FAIL: iam7_script_loads — res://scripts/player/player_input_action_policy.gd missing
  ... (26 more _fail_missing_module lines) ...
  Results: 0 passed, 28 failed
```

**Expected RED count (policy `.gd` missing):** **28** failures (one per `run_all()` test invocation).

## Spec coverage map

| Spec ID | Tests |
|---------|-------|
| IAM-2.3 | `iam2_mutate_to_infect`, `iam2_swap_mutation_to_fuse`, `iam5_mutate_alias`, `iam6_canonical_output` |
| IAM-5 | IDLE attack/move; JUMP deny jump; HURT deny attack/move + permit menu; DEAD deny attack/menu/jump; ABSORB/MUTATE/FLOAT rows |
| IAM-6 | attack>infect>absorb; menu suppresses attack |
| IAM-7 | load, API surface, RefCounted path |
| IAM-8 | unknown passthrough + deny; empty resolve |
| IAM-9 | debug_kill disabled/enabled/DEAD |

## Gaps for Test Breaker

- Simultaneous edges adversarial file (`test_player_input_action_policy_adversarial.gd`) per IAM test strategy
- `detach`+`detach_2` coexistence (EC-IAM-14)
- WALL_CLING / FALL matrix rows
- `debug_kill` coexistence with combat winner (EC-IAM-12)

## Handoff

Stage → **TEST_BREAK**; Next → **Test Breaker Agent**.
