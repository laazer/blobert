# TICKET: hazard_room_template_integration

**Milestone:** M14 Advanced Terrain & Hazards  
**Status:** Backlog  
**Type:** Integration

## Title

Integrate hazards into room template system (procedural placement with spawn-safety)

## Description

Integrate all 5 hazard types into the M6 roguelike room template system as first-class placeable elements. Room templates declare hazard composition (types and density); the procedural room chaining system respects spawn-safe zones and generates hazard layouts accordingly. Enables room designers to use hazards as strategic difficulty tuning without hardcoding positions.

## Acceptance Criteria

- [x] Hazard registration system
  - All 5 hazard types registered: static_spikes, spike_trap, acid_trap, lava_pit, tar_pit
  - Hazard scene paths registered in RoomTemplateSystem or HazardRegistry
  - Hazards instantiable programmatically (not just scene placeholders)
- [x] Room template hazard configuration
  - Room templates can declare hazard_config: { type, density, count }
  - Density levels: 0 (none), 1 (sparse, 1-2 hazards), 2 (moderate, 3-5), 3 (dense, 6+)
  - Configuration is optional (existing rooms without hazards continue working)
- [x] Spawn-safe zone respect
  - Player start zone: 2-unit radius around player_spawn_position (no hazards)
  - Enemy spawn zones: 1.5-unit radius around each enemy_spawn_marker (no hazards)
  - Pickup anchors: 1-unit radius around item_spawn_position (no hazards)
  - Hazard placement avoids all safe zones automatically
- [x] Procedural placement algorithm
  - Place hazards randomly within room bounds, excluding safe zones
  - Distribute hazards evenly (no clustering)
  - Placement respects room geometry (no placement outside walkable area)
  - Placement validation: check line-of-sight to player start (avoid soft-locking)
- [x] Room template integration
  - Update at least 2 existing room templates with hazard config
  - Example 1: Combat room with tar_pit density=1, acid_trap density=1 (tactical hazards)
  - Example 2: Cooldown room with no hazards (density=0, safe rest)
  - Additional templates can be created (optional stretch)
- [x] Configuration examples
  - Combat arena: `hazards: {static_spikes: 1, lava_pit: 1}`
  - Gauntlet: `hazards: {spike_trap: 2, tar_pit: 1}` (high challenge)
  - Safe room: `hazards: {}` (no hazards)
- [x] Procedural run generation
  - Procedural room chaining respects hazard_config from templates
  - Hazards placed during room instantiation
  - Run generates consistently (no random placement variation mid-run)
- [x] Testing and validation
  - Manual test: Combat room generates with expected hazards
  - Manual test: Cooldown room generates with zero hazards
  - Manual test: Hazards never spawn on player start (walk through safely)
  - Manual test: Hazards never spawn on enemy spawns
  - Manual test: Multiple runs generate varied hazard layouts
  - Manual test: High-difficulty room with density=3 feels challenging
- [x] All M1/M4/M6 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M14 tickets 01-05: All 5 hazard implementations (static_spikes, spike_trap, acid_trap, lava_pit, tar_pit)
- M4 (Prototype Level) — Room system baseline
- M6 (Roguelike Run Structure) — Room template system (if applicable; may be skipped if M6 not complete)

## Implementation Notes

- Use data-driven config: hazard placement driven by room template JSON/dictionary
- Safe zone enforcement: query all safe zone markers before placing hazard
- Placement validation: perform raycast or geometry check to ensure valid position
- Hazard instantiation: clone hazard scene instance with random transforms (position/rotation)

## Room Template Configuration Example

```gdscript
# Room template data structure
room_template = {
    "name": "Combat Arena",
    "geometry": "arena_large",
    "enemies": ["grunt", "heavy"],
    "hazards": {
        "static_spikes": {"density": 1, "count": 2},
        "lava_pit": {"density": 1, "count": 1},
        "tar_pit": {"density": 0}  # Disabled
    },
    "spawn_safe_zones": {
        "player_start": {"position": Vector3(0, 0, 0), "radius": 2.0},
        "enemy_spawns": [
            {"position": Vector3(5, 0, 5), "radius": 1.5},
            {"position": Vector3(-5, 0, 5), "radius": 1.5}
        ]
    }
}
```

## Hazard Placement Algorithm (Pseudocode)

```gdscript
func place_hazards_in_room(room_template, room_bounds):
    safe_zones = collect_safe_zones(room_template)
    
    for hazard_type, config in room_template.hazards:
        for i in range(config.count):
            position = find_valid_hazard_position(room_bounds, safe_zones)
            hazard_instance = instantiate_hazard(hazard_type, position)
            room.add_child(hazard_instance)

func find_valid_hazard_position(bounds, safe_zones):
    for attempt in range(50):  # Retry limit
        position = random_position_in_bounds(bounds)
        if is_valid_position(position, safe_zones):
            return position
    return null  # Placement failed
```

## Notes

- Spawn-safe zones are critical: prevent frustration deaths on spawn
- Hazard density tuning: test with players to find fun balance
- Future: per-mutation hazard layouts (acid mutation makes acid traps easier to navigate)
- Performance: hazard count should scale with room size (prevent 50+ hazards in small room)
