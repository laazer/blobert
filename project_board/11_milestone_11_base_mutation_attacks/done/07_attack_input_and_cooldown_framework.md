# TICKET: 07_attack_input_and_cooldown_framework

Title: Mutation attack input binding and per-mutation cooldown framework

## Description

Create the input and cooldown infrastructure that all 4 base mutation attacks share. Bind an attack action to a single input (e.g. `attack`) that triggers the active mutation's attack. Each mutation has its own cooldown timer; switching mutations does not reset another mutation's cooldown.

## Acceptance Criteria

- `attack` action is registered in Godot's Input Map (keyboard default: `J` or `Z`, configurable)
- Pressing `attack` with no active mutation does nothing (no crash, no error)
- Pressing `attack` with an active mutation fires that mutation's attack if not on cooldown
- Each mutation tracks its own cooldown independently
- Cooldown remaining is accessible for HUD display (expose a `get_attack_cooldown_remaining(mutation_id)` method)
- Input is consumed — pressing `attack` does not also trigger infect/absorb actions
- `run_tests.sh` exits 0

## Dependencies

- M2 (Infection Loop) — mutation slot system must be in place
- M3 (Dual Mutation + Fusion) — active mutation identity per slot must be readable

## Resolution

**Closed as superseded.** All acceptance criteria are covered by the following completed tickets:
- M11-03 (`input_action_mapping`) — `attack` action registered in Input Map
- M11-04 (`attack_resource`) — configurable attack data including cooldown
- M11-05 (`attack_executor_handlers`) — MELEE_SWIPE + PROJECTILE_SPIT execution
- M11-06 (`attack_database_integration`) — mutation → attack lookup pipeline
- M11-12 (`verify_cooldown_behavior`) — per-mutation cooldown independence, death reset, cross-state verification
