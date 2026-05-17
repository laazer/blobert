# TICKET: godot_mutation_model_swap

**Milestone:** M13 Blobert Visual Identity  
**Status:** Backlog  
**Type:** Implementation

## Title

Wire Blobert model swap to active mutation state in Godot (smooth crossfade on mutation change)

## Description

Implement real-time model swapping in Godot's player controller. When the player's active mutation state changes, Blobert's visible 3D mesh swaps to the corresponding visual variant (adhesion, acid, claw, carapace, or neutral). The swap should be smooth (crossfade or brief dissolve effect) over 0.2–0.4s rather than an instant/jarring pop. This extends the existing model node in `scenes/player/player_3d.tscn` without breaking any existing systems (color tint, infection effects, animations).

Implementation hooks into the mutation state machine (M11 ticket 01) to detect mutation changes and trigger model swaps.

## Acceptance Criteria

- [x] Mutation model variants loaded at startup
  - All 5 GLB variants preloaded as ResourceCache or on-demand
  - Paths: `res://assets/player/blobert_variants/{neutral,adhesion,acid,claw,carapace}.glb`
  - No errors on load; models available during gameplay
- [x] Model swap triggered on mutation change
  - Mutation state change detected via PlayerStateMachine or MutationController
  - Swap executes immediately when mutation acquired (absorption)
  - Swap executes immediately when mutation lost/cleared
  - Swap works for all 4 mutations + neutral state
- [x] Smooth transition implemented
  - Crossfade (blending between old and new) OR dissolve effect
  - Transition duration: configurable default 0.3s
  - Uses Tween for smooth animation (no jarring pops)
  - Both old and new models visible during transition (crossfade), or old fades to new (dissolve)
- [x] Mutation to model mapping implemented
  - MUTATION_ADHESION → adhesion.glb
  - MUTATION_ACID → acid.glb
  - MUTATION_CLAW → claw.glb
  - MUTATION_CARAPACE → carapace.glb
  - No mutations / NEUTRAL → neutral.glb
- [x] Edge case handling verified
  - Swap works during movement/animation (no animation breaking)
  - Swap works during combat (attacks continue uninterrupted)
  - Mutation change during transition: queue next swap (don't interrupt) or apply immediately
  - Death/reset returns to neutral smoothly
- [x] Visual feedback integration
  - Infection state color tint still applies over swapped model (compatible)
  - Damage feedback (flash/shake) works across model swaps
  - Particle effects (mutation auras, attack VFX) compatible with new model
  - No Z-fighting or mesh clipping during swap
- [x] Animation compatibility ensured
  - Current animations continue playing on new model (same skeleton)
  - Walk/run/jump/idle animations playback correctly on all variants
  - No retargeting or bone remapping needed (all variants share rig)
- [x] Performance verified
  - Model preloading does not cause stutter at startup
  - Swap (Tween + mesh change) completes in <16ms
  - Memory usage reasonable (max 5 models × ~2MB = <10MB)
- [x] All M11 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M13 ticket 02: blender_mutation_model_variants (models must be created first)
- M11 ticket 01: player_state_machine (mutation state detection)
- M4 (Prototype Level) — Mutation system established

## Implementation Notes

- Use ResourceCache or manual preload() for GLB files
- Crossfade: use Material.albedo_color lerp or material transparency
- Dissolve: use shader-based alpha blend or material swap with transparency curve
- Store current mutation variant as state variable to avoid redundant swaps
- Test framework: verify model changes on mutation acquisition/loss

## Example Swap Trigger

```gdscript
# Pseudocode: Listen for mutation state change
func _on_mutation_changed(old_mutation: int, new_mutation: int):
    var old_model = MUTATION_TO_MODEL_MAP.get(old_mutation)
    var new_model = MUTATION_TO_MODEL_MAP.get(new_mutation)
    
    if old_model != new_model:
        _swap_model_smooth(old_model, new_model, 0.3)  # 0.3s crossfade

func _swap_model_smooth(old: String, new: String, duration: float):
    # Create Tween for smooth transition
    var tween = create_tween()
    tween.tween_callback(func(): _set_model(new))
    tween.set_trans(Tween.TRANS_SMOOTH)
    tween.set_ease(Tween.EASE_IN_OUT)
    tween.tween_property(player_mesh, "material:alpha", 0.0, duration / 2)
    tween.tween_property(player_mesh, "material:alpha", 1.0, duration / 2)
```

## Notes

- Avoid hard-swapping meshes mid-animation (use Tween + alpha blending)
- Consider visual feedback (particle/glow during transition) for polish
- Per-combination model variants (fusion) are separate future scope
