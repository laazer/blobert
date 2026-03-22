# Blender Enemy Generator

A procedural 3D enemy generation pipeline for game developers. Generates GLB files with full animation sets, procedural materials, and companion combat data — ready to drop into Godot, Unity, or Unreal.

## Features

- **13 animations per enemy** — idle, move, attack, special_attack, damage variants, stunned, celebrate, taunt, death
- **3 body type systems** — blob, quadruped, humanoid; each with distinct movement and attack patterns
- **Combat data export** — companion `.attacks.json` alongside every GLB with hit frames, range, cooldown, AoE
- **22+ procedural materials** — no external textures; biological, elemental, metallic, stone
- **AI-assisted generation** — generate enemies from plain text descriptions
- **External model integration** — import FBX/GLB/OBJ and enhance with auto-generated animations and materials

## Requirements

- **Blender 3.6+** — auto-detected; override with `BLENDER_PATH` env var if needed
- **Python 3.11+** — for the CLI and test suite

## Installation

```bash
git clone <repository-url>
cd blender-experiments

# Install dev dependencies (pytest only)
uv sync --extra dev   # or: pip install -e ".[dev]"

# Verify Blender is found
python3 bin/find_blender.py

# Quick test
./enemy.sh test
```

## Commands

All commands are available via `./enemy.sh` (shell wrapper) or `python main.py` directly.

### Generate animated enemies

```bash
python main.py animated adhesion_bug          # 3 variants (default)
python main.py animated adhesion_bug 1        # 1 variant
python main.py animated all                   # all 3 animated enemy types
python main.py test                           # quick test: 1 adhesion_bug
```

Outputs to `animated_exports/`:
- `{enemy}_animated_{nn}.glb` — mesh + armature + all 13 animations
- `{enemy}_animated_{nn}.attacks.json` — combat stats (hit frames, damage type, range, cooldown)

### AI-assisted generation

```bash
python main.py smart --description "large fire spider with powerful attacks"
python main.py smart --description "small ice blob that is very fast" --difficulty hard
python main.py smart --description "boss metal warrior" --export-stats godot
```

### Stats export

```bash
python main.py stats adhesion_bug --export-stats godot
python main.py stats tar_slug --export-stats json --difficulty nightmare
```

### View in Blender

```bash
python main.py view adhesion_bug_animated_00 --anim move
python main.py view tar_slug_animated_00 --anim attack
```

### Import external models

```bash
python main.py import --model-path dragon.fbx --body-type quadruped
python main.py import --model-path warrior.glb --body-type humanoid --animation-set core
```

Supported formats: `.fbx`, `.obj`, `.dae`, `.gltf`, `.glb`, `.blend`

### List enemies and animations

```bash
python main.py list
```

## Animated Enemy Types

| Enemy | Body Type | Movement | Attack |
|-------|-----------|----------|--------|
| `adhesion_bug` | Quadruped | 6-legged tripod gait | Pounce with all legs coiling/springing |
| `tar_slug` | Blob | Squash/stretch | Expansion slam (AoE) |
| `ember_imp` | Humanoid | Bipedal walk with arm swing | Fire punch with body lean + guard arm |

## Animation System

### Core (all enemies, always generated)

| Animation | Duration | Description |
|-----------|----------|-------------|
| `idle` | 2.0s | Breathing and subtle movement |
| `move` | 1.0s | Locomotion loop |
| `attack` | 1.5s | Windup → strike → recovery |
| `damage` | 0.5s | Knockback reaction |
| `death` | 3.0s | Dramatic collapse |

### Extended (all enemies, generated with `animation_set=all`)

| Animation | Duration | Description |
|-----------|----------|-------------|
| `spawn` | 2.0s | Emerge from ground |
| `special_attack` | 2.5s | Signature power move |
| `damage_heavy` | 1.0s | Major knockback |
| `damage_fire` | 0.75s | Fire damage + burning shake |
| `damage_ice` | 1.25s | Ice damage + freezing |
| `stunned` | 2.5s | Dazed swaying |
| `celebrate` | 1.5s | Victory bounce |
| `taunt` | 1.0s | Provocative gesture |

All animations are self-contained — each starts and ends at rest pose so they loop cleanly in any order.

## Combat Data (`.attacks.json`)

Every generated GLB gets a companion JSON:

```json
{
  "filename": "adhesion_bug_animated_00",
  "attacks": [
    {
      "name": "pounce",
      "animation_name": "attack",
      "attack_type": "physical",
      "range": 3.0,
      "hit_frame": 18,
      "cooldown_seconds": 2.0,
      "knockback_force": 5.0,
      "is_area_of_effect": false
    }
  ]
}
```

`hit_frame` is the exact frame within the animation when damage registers — use it in Godot to trigger hitbox activation at the right moment rather than hardcoding a timer.

## Project Structure

```
├── main.py                  # CLI entry point
├── enemy.sh                 # Shell wrapper for main.py
├── bin/
│   └── find_blender.py      # Cross-platform Blender resolver
├── src/
│   ├── core/                # Blender scene utilities
│   ├── materials/           # Procedural material system
│   ├── animations/          # Keyframe, armature, body-type systems
│   ├── enemies/             # Enemy class definitions + export
│   ├── combat/              # Attack data structures and per-enemy profiles
│   ├── smart/               # AI-assisted generation
│   └── integration/         # External model import pipeline
├── tests/
│   ├── combat/              # Tests for attack data and profiles
│   └── animations/          # Tests for animation frame timing
├── animated_exports/        # Generated GLB + JSON output
├── pyproject.toml           # Project metadata and dependencies
└── uv.lock                  # Locked dependency versions
```

## Blender Path Resolution

Blender is located automatically in this order:

1. `BLENDER_PATH` environment variable
2. Platform-specific default install paths (macOS, Linux, Windows)
3. `blender` on `$PATH`

Override for a non-standard install:
```bash
export BLENDER_PATH=/path/to/blender
```

## Running Tests

```bash
uv run pytest tests/        # via uv
python -m pytest tests/     # directly
```

## Godot Integration

See [GODOT_INTEGRATION.md](GODOT_INTEGRATION.md) for a complete guide including GDScript examples that use the companion `.attacks.json` for hit-frame-accurate damage.
