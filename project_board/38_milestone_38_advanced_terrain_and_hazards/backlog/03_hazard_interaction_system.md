# TICKET: 03_hazard_interaction_system

**Milestone:** M38 Advanced Terrain & Hazards  
**Status:** Backlog  
**Type:** Implementation

## Title

Hazard Interaction System — damage, cooldown, and mutation resistance

## Description

Implement hazard damage system: contact with SpikeTrap/FireTrap applies damage per tick (configurable interval). Acid/Carapace mutations grant immunity or resistance. Damage cooldown prevents repeat hits on same collision.

## Acceptance Criteria

- [x] Hazard damage dealt every `damage_tick_rate` seconds (default 0.5s)
- [x] Per-hazard type damage amount (Spike 15 dmg, Fire 8 dmg/sec)
- [x] Acid mutation: immune to Acid traps, takes normal fire damage
- [x] Carapace mutation: 50% reduction to all hazard damage
- [x] Cooldown per hazard: player can't take damage again within 0.5s of last hit
- [x] Tests verify damage ticking and immunity logic
- [x] `run_tests.sh` exits 0

## Dependencies

- M38:01 (hazard templates)
- M2–M13 (mutation system)

## Implementation Notes

**Hazard damage logic:**
```gdscript
func _on_hazard_contact(player: PlayerController):
    if not player.has_mutation("acid") or hazard_type != "acid_trap":
        var damage = get_damage(hazard_type)
        if player.has_mutation("carapace"):
            damage *= 0.5
        player.take_damage(damage)
```

## Scope Notes

- No knockback from hazards (separate feature)
- No visual damage indicator beyond existing health system

