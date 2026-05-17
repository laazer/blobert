# TICKET: sandbox_enemy_spawn_stage

**Milestone:** M17 Sandbox Enemy Spawn  
**Status:** Backlog  
**Type:** Implementation (Development Tool)

## Title

Sandbox enemy spawn stage — runtime enemy spawning for tuning and QA

## Description

Create a dedicated sandbox scene for enemy spawning and combat tuning. Allows spawning any generated enemy family at runtime without procedural run assembly or manual scene edits. Primary use: balance testing, visual tuning, attack validation. Scene remains separate from main game scenes.

## Acceptance Criteria

- [x] Sandbox scene created: `scenes/sandbox/enemy_spawn_sandbox.tscn`
  - Player start position (safe from spawns)
  - Empty arena suitable for 1v1 or 1vMany combat
  - Clean, minimal environment (no hazards initially)
  - Lighting setup for clear visibility
- [x] Enemy spawn controls
  - UI panel or debug menu to select enemy family
  - Spawn button to instantiate enemy at arena position
  - Support spawning multiple instances (test group behavior)
  - Each spawn placed at safe distance from player
- [x] Enemy family selection
  - Dropdown or list shows all current enemy families
  - Each selectable enemy uses production scripts/scenes (no hacks)
  - Spawn configuration: count, spacing, health (configurable)
  - Easy switching between families mid-test
- [x] Game state compatibility
  - Player health and state match main game (configurable)
  - Mutation availability: can acquire mutations during test
  - Attack system fully functional
  - Damage/knockback physics identical to main game
- [x] Clear/reset functionality
  - "Clear" button removes all spawned enemies
  - "Reset" button resets player to start (health, mutations)
  - No orphaned nodes or memory leaks
  - Scene state clean after clear (ready for new spawns)
- [x] Documentation
  - `CLAUDE.md` updated with sandbox launch instructions
  - Instructions cover: how to run, how to spawn enemies, how to test
  - Example: "godot project.godot --main_scene=res://scenes/sandbox/enemy_spawn_sandbox.tscn"
- [x] Testing and validation
  - Manual test: Spawn single enemy, fight works
  - Manual test: Spawn multiple enemies, all behave correctly
  - Manual test: Switch enemy families, new family appears
  - Manual test: Acquire mutations, combat tuning works
  - Manual test: Reset clears all spawned enemies
  - No console errors during spawn/clear
- [x] All M1 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M8 (Enemy Attacks) — Enemy families must exist
- M18 (Enemy Navigation) — Enemy AI functional (or placeholder)

## Scene Structure

```
enemy_spawn_sandbox (Node3D)
├── Player (PlayerController3D / player_3d.tscn)
├── Arena (Node3D)
│   ├── FloorPlane (MeshInstance3D) [flat arena]
│   └── WallPlanes (optional, for boundaries)
├── SpawnUI (CanvasLayer)
│   ├── ControlPanel (Panel)
│   │   ├── EnemySelector (OptionButton/DropDown)
│   │   ├── SpawnCountInput (TextEdit) [optional]
│   │   ├── SpawnButton (Button) "Spawn"
│   │   ├── ClearButton (Button) "Clear All"
│   │   └── ResetButton (Button) "Reset Player"
│   └── InfoLabel (Label) [feedback text]
└── EnemySpawnPoint (Node3D) [reference position for spawns]
```

## Example Configuration

```gdscript
# Sandbox configuration (hardcoded or external)
var enemy_families = [
    {"name": "Grunt", "scene": "res://scenes/enemies/grunt.tscn"},
    {"name": "Heavy", "scene": "res://scenes/enemies/heavy.tscn"},
    {"name": "Boss", "scene": "res://scenes/enemies/boss.tscn"}
]

var spawn_config = {
    "count": 1,
    "spacing": 2.0,  # Distance between spawns
    "position_offset": Vector3(5, 0, 0)  # From player
}
```

## Implementation Notes

- Spawn position: offset from player center (avoid collision on spawn)
- Enemy instances: instantiate from production scene (no duplicates)
- Reset: restore player health/mutations via RunStateManager or equivalent
- Documentation: keep instructions up-to-date as enemy families expand

## Documentation Template

```
# Sandbox Enemy Spawn Stage

Launch sandbox for testing enemy behavior and combat tuning:

godot project.godot --main_scene=res://scenes/sandbox/enemy_spawn_sandbox.tscn

## Controls

1. Select enemy family from dropdown
2. Click "Spawn" to instantiate enemy
3. Fight and tune attacks/behavior
4. Click "Clear All" to remove enemies
5. Click "Reset Player" to restore health/mutations

## Testing Checklist

- [ ] All enemy families spawn correctly
- [ ] Spawned enemies use production scripts (same behavior as game)
- [ ] Player can acquire mutations and test combined combat
- [ ] Damage numbers and knockback match main game
- [ ] Multiple spawns work (test group AI)
```

## Notes

- Sandbox is development-only (do not ship in final build)
- Quick iteration tool: maintain as features change
- Extensible: easy to add new enemy families
