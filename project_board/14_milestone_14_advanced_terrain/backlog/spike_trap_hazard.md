# TICKET: spike_trap_hazard

**Milestone:** M14 Advanced Terrain & Hazards  
**Status:** Backlog  
**Type:** Implementation (Hazard System)

## Title

Spike trap hazard — triggered spikes with telegraph before activation (cycling with state feedback)

## Description

Implement a triggered spike trap: spikes flush with the floor or wall that extend on a timer cycle and retract after a fixed duration. The trap shows clear visual and audio telegraph (glow, animation, warning sound) before activating, giving the player 0.4+ seconds to react and avoid. Trap cycles continuously (retracted→telegraph→extended→retracted). Self-contained placeable scene for room templates.

## Acceptance Criteria

- [x] Scene created: `scenes/hazards/spike_trap.tscn`
  - Self-contained and placeable in any room template
  - Uses Godot's standard Node3D + Area3D collision
- [x] Trap state machine implemented
  - **Retracted state**: Spikes flush/hidden, no damage, duration 2.0s (export var)
  - **Telegraph state**: Visual warning (glow + animation), audio cue, duration 0.4s (export var)
  - **Extended state**: Spikes visible/extended, deals 15 damage per hit, duration 1.0s (export var)
  - Cycles continuously (Retracted → Telegraph → Extended → Retracted)
- [x] Visual telegraph implementation
  - Glow/flash effect on trap before extension (0.4s)
  - Spike geometry animates (brief pop-out animation OR scale-up Tween)
  - Color change: retracted gray → telegraph yellow/orange → extended red
  - No sudden pops; smooth visual feedback
- [x] Audio telegraph
  - Warning sound plays 0.3s into telegraph state (~100ms before extension)
  - Extension sound (brief "click" or "snap") when spikes fully extend
  - Retraction sound when spikes retract
  - All SFX 3D-positional (volume decreases with distance)
- [x] Damage and collision
  - Hitbox (Area3D) active ONLY during extended state
  - On player collision, deal 15 damage (consistent with static spikes)
  - Damage cooldown: 0.5s per hit (prevent multi-hit from same spike)
  - Knockback: 50.0 away from spike center
- [x] Timing configuration
  - Export variables for all durations (retracted_duration, telegraph_duration, extended_duration)
  - Default values: Retracted 2.0s, Telegraph 0.4s, Extended 1.0s
  - Timers configurable per-instance (allow variation in rooms)
- [x] Placement and integration
  - No code changes required to place in room templates
  - Inherits from Hazard base class (if applicable)
  - Works with multiple instances in same room
  - Positioned via scene node transform (X/Y/Z + rotation)
- [x] Edge case handling
  - Multiple hits on same player during extended state: damage dealt only once per cooldown (not per-frame)
  - Spike during telegraph: does not damage (only in extended state)
  - Damage instance tracking: prevent damage spam from overlapping regions
- [x] Animation and VFX
  - Spike extension animation: ~0.2s scale/position Tween (smooth, not instant)
  - Retraction animation: ~0.2s scale/position Tween
  - Glow intensity peaks at extension, fades during retraction
  - Particle effects (optional): brief spark on damage hit
- [x] Testing and validation
  - Manual test: Walk into trap during retracted state (no damage)
  - Manual test: Get hit by extended spikes (15 damage applies)
  - Manual test: Take damage cooldown (second hit delayed)
  - Manual test: Timed telegraph + extension (player has time to jump away)
  - Manual test: Multiple instances cycle independently
- [x] All M1 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M4 (Prototype Level) — Hazard system established
- M14 ticket 05: static_spikes_hazard (damage model and base implementation)

## Implementation Notes

- Use Timer nodes for state cycling (reliable, configurable)
- Area3D collision for hitbox (3D spatial awareness)
- Tween for smooth state animations
- AudioStreamPlayer3D for 3D positional audio
- Store damage cooldown per-player to prevent spam

## Scene Structure

```
spike_trap (Node3D)
├── VisualGeometry (MeshInstance3D) [spikes geometry]
├── GlowEffect (OmniLight3D) [toggles on/off during telegraph]
├── HitboxArea (Area3D) [collision detection, active only when extended]
├── StateTimer (Timer) [controls state cycling]
└── AudioPlayer (AudioStreamPlayer3D) [telegraph + damage sounds]
```

## Example Configuration

```gdscript
@export var retracted_duration: float = 2.0  # Time spikes stay down
@export var telegraph_duration: float = 0.4  # Warning time before spikes extend
@export var extended_duration: float = 1.0   # Time spikes stay up
@export var damage_amount: int = 15
@export var damage_cooldown: float = 0.5     # Min time between hits on same player
```

## Notes

- Telegraph timing is critical: too short and player can't react; too long and trap feels slow
- Consider sound intensity balance with other room hazards
- Damage cooldown prevents multi-hit exploit from overlapping spike regions
