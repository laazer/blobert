# TICKET: attack_input_and_cooldown_framework

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
