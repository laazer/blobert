# SCRIPTS MODULE - GODOT RUNTIME KNOWLEDGE BASE

**Generated:** 2026-04-23  
**Purpose:** GDScript runtime patterns, player/enemy systems, movement simulation

## OVERVIEW

GDScript runtime for blobert's Godot gameplay. Organized around **base/derive separation**: `base_*.gd` files define core physics/entities; `*_controller.gd` files handle behavior orchestration; `*_hitbox.gd` isolates combat mechanics. Uses `class_name` for globally accessible scripts.

## STRUCTURE

```
scripts/
├── movement/           # Pure physics simulation (movement_simulation.gd)
│   └── movement_simulation.gd  # 687 lines; core 2D math → 3D mapping
├── player/             # Player behavior & physics
│   ├── base_physics_entity_3d.gd    # Base physics entity class
│   └── player_controller_3d.gd      # Player behavior controller (3D)
├── enemies/            # Enemy systems
│   ├── enemy_base.gd                   # Shared enemy state/behavior
│   ├── enemy_animation_controller.gd   # Animation logic (separate from state)
│   └── enemy_attack_hitbox.gd          # Combat hitbox/attack logic
├── system/             # Global systems
│   └── logging.gd                    # Project-wide logging utility
├── project_controller_3d.gd      # Root node for Godot project
└── (other runtime scripts)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Movement physics | `scripts/movement/movement_simulation.gd` | Pure simulation class; no Node/Input coupling |
| Player behavior | `scripts/player/player_controller_3d.gd` | Maps movement output to 3D; handles input, jump, wall cling |
| Enemy state machine | `scripts/enemies/enemy_base.gd` | Normal/Weakened/Infected states; infection logic |
| Enemy attacks | `scripts/enemies/enemy_attack_hitbox.gd` | Hitbox activation, damage calculation |
| Project root | `scripts/project_controller_3d.gd` | Manages scene transitions, run state |

## CODE MAP

| Symbol | Type | Location | Refs | Role |
|--------|------|----------|------|------|
| `MovementSimulation` | class | `scripts/movement/movement_simulation.gd` | 8+ | Pure physics simulation (2D math → 3D mapping) |
| `PlayerController3D` | class | `scripts/player/player_controller_3d.gd` | ~10 | Player behavior controller (3D) |
| `EnemyBase` | class | `scripts/enemies/enemy_base.gd` | ~15 | Base enemy state/behavior |
| `ProjectController3D` | class | `scripts/project_controller_3d.gd` | 5+ | Root node for Godot project |

## CONVENTIONS

- **Naming**: `base_*.gd` (core physics), `*_controller.gd` (behavior orchestration), `*_hitbox.gd` (combat mechanics)
- **class_name**: Used for globally accessible scripts; enables scene composition via resources
- **Separation of concerns**: Animation separate from state; hitboxes isolated from movement
- **Pure simulation**: Movement logic is a class with no Node/Input coupling; testable in isolation

## ANTI-PATTERNS (THIS MODULE)

| Pattern | Why Forbidden | Evidence |
|---------|---------------|----------|
| Monolithic simulate() | 687 lines; hard to test, edge cases missed | `movement_simulation.gd`; refactor candidates: extract MovementState + MovementEngine |
| Godot coupling in simulation | Breaks testability; pure math should be isolated | movement_simulation.gd has per-frame logic with many branches |
| Missing class_name on shared classes | Prevents resource-based composition | Some enemy/player scripts lack global accessibility |

## UNIQUE STYLES

- **Base-then-derive**: `base_physics_entity_3d.gd` provides foundation; controllers add behavior layers
- **State machine pattern**: Enemies have explicit Normal/Weakened/Infected states with clear transitions
- **2.5D mapping**: Pure 2D physics simulation (`movement_simulation.gd`) mapped to 3D world via `PlayerController3D`

## COMMANDS

```bash
# Syntax check for GDScript (use run_tests.sh instead - godot --check-only hangs)
timeout 120 godot --headless --import

# Run Godot tests only
timeout 300 godot --headless -s tests/run_tests.gd
```

## NOTES

- **Complexity hotspot**: `movement_simulation.gd` (687 lines); refactor candidates: extract MovementState into separate module, split simulate() into smaller helpers
- **Testability**: MovementSimulation class is designed for unit testing; test pure math paths independently of Godot API
- **Scene wiring**: Main scene (`procedural_run.tscn`) uses RunSceneAssembler to procedurally assemble runs from room templates
