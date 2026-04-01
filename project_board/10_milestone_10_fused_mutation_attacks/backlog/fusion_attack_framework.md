# TICKET: fusion_attack_framework

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
