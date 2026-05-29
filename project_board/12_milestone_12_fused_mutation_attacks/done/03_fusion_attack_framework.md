# TICKET: M12-03
Title: Fusion attack dispatch — route attack input to the active fusion's attack

## Description

Extend the attack input framework (M9) so that when a fusion is active, pressing the attack input fires the fusion-specific attack instead of either base mutation attack. Each fusion combination maps to a unique attack. This ticket creates the routing layer; individual fusion attacks are separate tickets.

## Acceptance Criteria

- When fusion is active, `attack` input routes to the fusion attack for that combination
- When fusion is not active, `attack` input routes to the base mutation attack as before (no regression)
- Fusion attack has its own cooldown independent of the base mutation cooldowns
- `is_fusion_active()` on PlayerController3D is used to determine routing (no duplicate state)
- `run_tests.sh` exits 0

## Dependencies

- `attack_input_and_cooldown_framework` (M9)
- M3 (Dual Mutation + Fusion) — fusion state must be readable

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_GENERALIST

## Revision
6

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: 1 adversarial FAIL (FAF-ADV2-1 exposes spec gap FAF-FM-3 — see checkpoint log)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Gameplay Systems Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/12_milestone_12_fused_mutation_attacks/in_progress/03_fusion_attack_framework.md",
  "spec_path": "project_board/specs/fusion_attack_framework_spec.md",
  "checkpoint_log": "project_board/checkpoints/M12-03/2026-05-29T-test-break-run.md",
  "test_files": [
    "tests/scripts/attacks/test_fusion_attack_routing.gd",
    "tests/scripts/attacks/test_fusion_attack_routing_adversarial.gd",
    "tests/scripts/attacks/test_fusion_attack_routing_adversarial2.gd"
  ]
}
```

## Status
Proceed

## Reason
Test Breaker added 9 adversarial tests (28 assertions) in test_fusion_attack_routing_adversarial2.gd. Found 1 real spec gap: FAF-FM-3 violation — when AttackExecutor._is_active=true rejects execute_attack(), _try_attack() still writes _mutation_cooldowns[cooldown_key] unconditionally (line 482 of player_controller_3d.gd). Spec says cooldown must NOT be set in this case. Test FAF-ADV2-1 confirms this with FAIL: expected 0.0, got 2.0. Implementation Agent (Gameplay Systems Agent) must verify existing code satisfies spec, fix the FAF-FM-3 gap if needed, and run static QA. All other 27 new assertions and all 44 pre-existing assertions remain GREEN.
