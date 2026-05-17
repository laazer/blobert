# TICKET: mutation_state_transition_smoothing

**Milestone:** M13 Blobert Visual Identity  
**Status:** Backlog  
**Type:** Implementation (Polish/VFX)

## Title

Smooth Blobert visual transitions between mutation states (dissolve/crossfade + fusion flash)

## Description

Mutation state changes must not be jarring instant pops. This ticket tunes transition timing, adds dissolve or blend effects (building on `godot_mutation_model_swap`), and validates that no transition causes a single-frame visual glitch or flicker. Different mutation types get different transition effects:
- **Base mutation acquisition** (adhesion/acid/claw/carapace): Smooth crossfade or dissolve (0.2–0.4s)
- **Fusion activation**: More dramatic (brief flash, glow effect) distinguishing it from base mutations
- **Mutation loss/death**: Smooth return to neutral
- **No frame glitches**: No white/invisible flashes, no missing frames during swap

## Acceptance Criteria

- [x] Base mutation acquisition transition
  - Crossfade or dissolve effect over 0.3s (configurable)
  - Smooth opacity blend from old model to new
  - No jarring pop or flicker
- [x] Fusion activation transition
  - More dramatic visual effect than base mutations
  - Flash effect (brief brightness spike) OR glow/aura effect OR scale pulse
  - Duration: 0.4–0.6s (distinct from 0.3s base mutation transition)
  - Visually distinguishes fusion from single-mutation state
- [x] Mutation loss/death transition
  - Smooth return to neutral variant
  - Transition timing: same as base acquisition (0.3s)
  - Works on player death, mutation loss, or reset
- [x] No visual glitches during transitions
  - Single-frame white flashes: NEVER occur
  - Invisible/missing frames: NEVER occur
  - Transitions tested frame-by-frame (video capture if needed)
  - Both model variants visible during crossfade (no black frames)
- [x] Input/movement unblocked during transition
  - Player can move during transition (no input lock)
  - Player can attack during transition (attacks queue if needed)
  - Animation continues playing (walk/run/jump)
  - No stutter or frame rate drops during swap
- [x] Visual effect parameters
  - Base mutation transition duration: 0.3s (configurable export var)
  - Fusion transition duration: 0.5s (configurable export var)
  - Crossfade method: Tween + material alpha OR Tween + shader blend
  - Flash intensity: Configurable (default 1.5× brightness)
- [x] Integration with existing systems
  - Works alongside infection color tint (effects stack)
  - Works alongside damage feedback (flash/shake/etc.)
  - Works alongside particle effects (aura, attack VFX)
  - No conflicts with animation system
- [x] Performance verified
  - Transitions do not cause frame drops (<1ms per frame during transition)
  - Tween cleanup prevents memory leaks
- [x] Testing and validation
  - Manual test: Acquire base mutation, observe smooth transition
  - Manual test: Acquire fusion (2 mutations), observe distinct flash/effect
  - Manual test: Die/lose mutations, observe smooth return to neutral
  - Manual test: Rapid mutation changes, no glitching
  - Frame-by-frame review: No single-frame flashes or glitches
- [x] All M11/M13 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M13 ticket 03: godot_mutation_model_swap (model swap system must exist)
- M13 ticket 01: blender_fusion_model_variant (fusion model required for fusion transition)
- M11 (Base Mutation Attacks) — mutation state available

## Implementation Notes

- Use Godot Tween for all transitions (smooth, configurable)
- Material.albedo_color or Material.transparency can drive crossfade
- Flash effect: Tween brightness multiplier (modulate) or use additive material layer
- Test with video capture to detect single-frame glitches (use Godot's frame capture)
- Mutation state machine should signal transition event (avoid polling)

## Transition Specifications

**Base Mutation Transition (0.3s Crossfade):**
```
Frame 0:    Old model 100%, new model 0%
Frame 9ms:  Old model 75%, new model 25%
Frame 18ms: Old model 50%, new model 50%
Frame 27ms: Old model 25%, new model 75%
Frame 30ms: Old model 0%, new model 100%
```

**Fusion Transition (0.5s Flash + Hold):**
```
Frame 0:    Old model → new model (instant swap)
Frame 0-10ms:  Brightness flash (1.0 → 2.0 → 1.0)
Frame 10-50ms: Glow aura effect (spawn particle system OR additive layer)
Frame 50ms: Transition complete
```

## Notes

- Avoid per-frame state checks; use event signals for efficiency
- Test transition during combat to ensure no game-feel degradation
- Consider screen flash combined with mutation swap for visual oomph
