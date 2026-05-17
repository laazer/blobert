# TICKET: static_spikes_hazard

**Milestone:** M14 Advanced Terrain & Hazards  
**Status:** Backlog  
**Type:** Implementation (Hazard System)

## Title

Static spikes hazard — instant damage on contact (foundational spike implementation)

## Description

Create static spike geometry for floors and walls: fixed spikes that deal instant damage on player contact. Unlike triggered traps, these spikes are always "armed" and ready. Unlike continuous hazards (tar, lava), spikes inflict a single hit per contact with a brief immunity window—player must leave and re-enter to take damage again. This prevents damage-spam from slow or stuck movement. Self-contained placeable scene.

## Acceptance Criteria

- [x] Scene created: `scenes/hazards/static_spikes.tscn`
  - Self-contained, placeable in any room template
  - Node3D + Area3D for collision detection
  - Configurable via export variables (position, rotation, size)
- [x] Damage on contact
  - Player takes 15 damage on first contact
  - Damage applies immediately on Area3D collision
  - Knockback applied: 80.0 away from spike center
- [x] Immunity window prevents spam
  - After hit, 0.5s immunity period (configurable export var)
  - During immunity, further contact does NOT deal damage
  - Immunity tracked per-player (support multiple players)
  - Immunity timer resets on new contact after expiry
- [x] Visual clarity (looks dangerous)
  - Sharp spike geometry or sprite (3D mesh, not abstract shape)
  - Distinct visual from other hazards (not confused with walls)
  - High contrast color or metallic appearance
  - Scale: 1-2 units tall (visible threat, not oversized)
- [x] Orientation support
  - Placeable on floor (vertical spikes pointing up)
  - Placeable on walls (horizontal spikes pointing outward)
  - Scene inherits from Hazard base class (if applicable)
  - Orientation via scene Node3D rotation (no code changes needed)
- [x] Scene integration
  - No code changes required to place in room templates
  - Works with multiple instances in same room
  - Positioned via scene node transform (X/Y/Z + rotation)
- [x] Damage tracking
  - Separate immunity timer per-player contact
  - Dictionary/array tracks player→immunity_end_time
  - Expired immunity timers cleaned up periodically
- [x] Testing and validation
  - Manual test: Touch spikes, take 15 damage
  - Manual test: Touch again immediately (no damage during 0.5s)
  - Manual test: Wait 0.5s, touch again (damage applies)
  - Manual test: Knockback applied correctly
  - Manual test: Multiple spike instances work independently
- [x] All M1 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M4 (Prototype Level) — Hazard system foundation

## Implementation Notes

- Use Area3D for collision detection (trigger area, not physics body)
- Timer or timestamp system for immunity window per-player
- Knockback calculation: `(player.position - spike.position).normalized() * magnitude`
- Consider reusing spike geometry/material across instances (static meshes)

## Scene Structure

```
static_spikes (Node3D)
├── SpikeGeometry (MeshInstance3D) [spike visual mesh]
├── HitboxArea (Area3D) [collision detection]
└── [Optional] CollisionShape3D [hitbox shape]
```

## Example Configuration

```gdscript
@export var damage_amount: int = 15
@export var damage_cooldown: float = 0.5  # Immunity window after hit
@export var knockback_magnitude: float = 80.0
```

## Notes

- Immunity window is critical: too short causes frustration, too long makes spikes feel weak
- Visual design should match environment (cave spikes, dungeon spikes, etc.)
- Consider audio: brief "whoosh" or "spike hit" sound on contact
