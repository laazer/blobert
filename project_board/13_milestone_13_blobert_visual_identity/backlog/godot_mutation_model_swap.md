# TICKET: godot_mutation_model_swap

Title: Wire Blobert model swap to active mutation state in Godot

## Description

When the player's active mutation changes, Blobert's visible mesh swaps to the corresponding variant. The swap should be smooth (crossfade or brief dissolve) rather than a hard pop. This extends the existing model node in `scenes/player/player_3d.tscn`.

## Acceptance Criteria

- Absorbing an adhesion mutation → Blobert visually becomes the adhesion variant
- Absorbing an acid mutation → Blobert visually becomes the acid variant
- Absorbing a claw mutation → Blobert visually becomes the claw variant
- Absorbing a carapace mutation → Blobert visually becomes the carapace variant
- Losing all mutations (death/reset) → Blobert returns to neutral variant
- Model swap is not instant — crossfade or brief dissolve lasts 0.2–0.4s
- Does not conflict with existing infection state color feedback (tint can still apply over the new model)
- `run_tests.sh` exits 0

## Dependencies

- `blender_mutation_model_variants`
- M11 (Base Mutation Attacks) — mutation identity fully established
