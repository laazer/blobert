# SCENES MODULE - GODOT SCENE KNOWLEDGE BASE

**Generated:** 2026-04-23  
**Purpose:** Godot scene organization, procedural assembly patterns

## OVERVIEW

Godot scenes (.tscn) for blobert's gameplay. Main run scene (`procedural_run.tscn`) assembled at runtime via `RunSceneAssembler` from hand-crafted room templates; non-deterministic layout per run.

## STRUCTURE

```
scenes/
├── levels/
│   ├── procedural_run.tscn             # Main entry; RunSceneAssembler assembles runs
│   └── (room template directories)      # Intro, combat, mutation tease, fusion, cooldown, boss rooms
├── player/
│   └── player_3d.tscn                   # 3D player scene (CharacterBody3D)
├── enemies/
│   ├── enemy_base.tscn                 # Base enemy template
│   └── generated/                      # Auto-generated enemy scenes from .glb models
├── test_movement_3d.tscn               # Development target; 2.5D gameplay
└── (other runtime scenes)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Main run entry | `scenes/levels/procedural_run.tscn` | RunSceneAssembler assembles from room templates at runtime |
| Room templates | `scenes/levels/[category]/` | Intro, combat, mutation tease, fusion opportunity, cooldown, boss |
| Player scene | `scenes/player/player_3d.tscn` | CharacterBody3D with PlayerController3D script attached |
| Enemy scenes | `scenes/enemies/generated/` | Auto-generated from .glb models via load_assets.gd |
| Dev target | `scenes/test_movement_3d.tscn` | 2.5D gameplay; side-view camera, plane-constrained physics |

## CONVENTIONS

- **Procedural assembly**: Main scene not static; RunSceneAssembler chains room templates per run progression rules
- **Hand-crafted rooms**: Individual rooms designed by hand; layout non-deterministic
- **Template categories**: Intro → movement introduction → mutation tease → fusion opportunity → skill check → cooldown → exit
- **Generated enemies**: .glb models exported from Blender pipeline; load_assets.gd creates wrapper scenes with collision, hurtbox, markers

## ANTI-PATTERNS (THIS MODULE)

| Pattern | Why Forbidden | Evidence |
|---------|---------------|----------|
| Static main scene | Breaks procedural run design; RunSceneAssembler expected | Avoid hardcoding single static level; use procedural assembly |
| Manual enemy scene creation | load_assets.gd handles generation; manual creates drift | Use asset pipeline for all enemy scenes |

## UNIQUE STYLES

- **RunSceneAssembler**: Runtime node that assembles runs from room templates; maintains run state, progress tracking
- **Room chaining**: Templates connected via procedural rules (intro → development → climax → cooldown)
- **2.5D camera**: Side-view Camera3D with plane-constrained movement despite 3D world

## COMMANDS

```bash
# Import scene changes
timeout 120 godot --headless --import

# Headless test run main scene
timeout 300 godot --headless -s tests/run_tests.gd
```

## NOTES

- **Entry point**: `project.godot` → `run/main_scene = res://scenes/levels/procedural_run.tscn`
- **Dev target**: `test_movement_3d.tscn` for new feature development; 2.5D gameplay setup
- **Generated scenes**: Enemy .tscn files auto-generated from .glb models; treat as read-only unless regenerating assets
