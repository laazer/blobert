# TICKET: mutation_state_transition_smoothing

Title: Smooth Blobert visual transitions between mutation states

## Description

Mutation state changes must not be jarring instant pops. This ticket tunes the transition timing, adds dissolve or blend effects, and validates that no transition causes a single-frame visual glitch. Builds on top of `godot_mutation_model_swap`.

## Acceptance Criteria

- Absorbing a mutation shows a smooth transition (crossfade, scale pulse, or dissolve) lasting 0.2–0.5s
- Fusion activation has a distinct transition (more dramatic than a base mutation swap — e.g. brief flash)
- Losing mutations on death transitions back to neutral smoothly, not instantly
- No single-frame white/invisible flash during any transition
- Transitions do not block player input or movement
- `run_tests.sh` exits 0

## Dependencies

- `godot_mutation_model_swap`
- `blender_fusion_model_variant`
