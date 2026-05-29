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
TEST_BREAK

## Revision
5

## Last Updated By
Test Designer Agent

## Validation Status
- Tests: Not Run
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/12_milestone_12_fused_mutation_attacks/in_progress/03_fusion_attack_framework.md",
  "spec_path": "project_board/specs/fusion_attack_framework_spec.md",
  "checkpoint_log": "project_board/checkpoints/M12-03/2026-05-29T-spec-run.md",
  "test_files": [
    "tests/scripts/attacks/test_fusion_attack_routing.gd",
    "tests/scripts/attacks/test_fusion_attack_routing_adversarial.gd"
  ]
}
```

## Status
Proceed

## Reason
Test suite complete. 14 behavioral tests in test_fusion_attack_routing.gd and 10 adversarial tests in test_fusion_attack_routing_adversarial.gd. All 44 assertions GREEN against current codebase (regression-only suite). All FAF-1 through FAF-5 requirements and all FAF-FM failure modes covered. Full test suite exits 0. Test Breaker Agent should write adversarial tests that would fail if the routing gate, cooldown keys, state-gating, or fallback logic were broken.
