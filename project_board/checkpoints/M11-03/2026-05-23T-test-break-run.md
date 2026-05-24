# M11-03 Test Breaker checkpoint

**Agent:** Test Breaker Agent  
**Date:** 2026-05-24  
**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/in_progress/03_input_action_mapping.md`

## Artifacts

| Artifact | Path |
|----------|------|
| Adversarial tests | `tests/scripts/player/test_player_input_action_policy_adversarial.gd` |
| Primary tests | `tests/scripts/player/test_player_input_action_policy.gd` |
| Policy impl | `scripts/player/player_input_action_policy.gd` (present; debug_kill matrix gap) |
| Spec | `project_board/specs/input_action_mapping_spec.md` |

## Adversarial coverage

| EC-IAM | Tests |
|--------|-------|
| EC-IAM-1 | `ec_iam1_unknown_*` (permit all sampled states; resolve strips unknown) |
| EC-IAM-2 | `ec_iam2_combat_winner_*` (6 press-order permutations + mutate vs attack) |
| EC-IAM-3 | `ec_iam3_infect_over_absorb` |
| EC-IAM-4 | `ec_iam4_absorb_over_fuse_and_alias` |
| EC-IAM-5 | `ec_iam5_menu_*` (movement+combat suppressed; HURT menu-only) |
| EC-IAM-6 | `ec_iam6_dead_*` |
| EC-IAM-7 | `ec_iam7_hurt_*` (9 gameplay denies + empty resolve) |
| EC-IAM-8 | `ec_iam8_absorb_only_menu_survives` |
| EC-IAM-12 | `ec_iam12_debug_kill_with_attack_when_enabled` (**RED**) |
| EC-IAM-14 | `ec_iam14_detach_*` |
| EC-IAM-16 | `ec_iam16_mutate_menu_only` |
| FALL/WALL_CLING absorb | `ec_iam_fall_*`, `ec_iam_wall_*` |

**Adversarial test methods:** 21 (`run_all` invocations)  
**Adversarial assertions:** 38 (37 PASS, 1 FAIL)

## Test execution evidence

```text
$ timeout 300 godot --headless -s tests/run_tests.gd 2>&1 | grep -A 45 "test_player_input_action_policy_adversarial"
--- test_player_input_action_policy_adversarial.gd ---
  ... 37x PASS ...
  FAIL: ec_iam12_debug_after_combat_winner — size expected 2, got 1 — expected ["attack", "debug_kill"], got [&"attack"]
  Results: 37 passed, 1 failed
```

Primary suite (same run):

```text
FAIL: iam9_debug_kill_permitted_idle_when_enabled — state 0 action 'debug_kill' expected permitted=true, got false
```

**Root cause (for implementation):** `_PERMIT_MATRIX` IDLE/WALK rows omit `debug_kill`; `is_action_permitted` calls `_matrix_allows` after `debug_actions_enabled` check, so IAM-9.2 / EC-IAM-12 cannot pass until matrix or debug branch grants non-DEAD gameplay states.

## Handoff

Stage → **IMPLEMENTATION_GAMEPLAY**; Next → **Gameplay Systems Agent** (fix `debug_kill` permit + resolve coexistence per IAM-9 / EC-IAM-12).
