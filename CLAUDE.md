# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**blobert** is a Godot 4+ game project. The primary scripting language is GDScript.

## Development target: 3D scenes

Development is for **3D scenes**: 2.5D with one 3D world and 2D-like gameplay.

- **Main scene:** `res://scenes/levels/test_movement_3d.tscn` (set in `project.godot` as `run/main_scene`).
- **Player:** `PlayerController3D` in `scripts/player/player_controller_3d.gd`; scene `scenes/player/player_3d.tscn`. Use **CharacterBody3D**, **Camera3D**, **Area3D**, **Node3D**, etc. for new gameplay and levels.
- **Movement logic:** Shared pure simulation in `scripts/movement/movement_simulation.gd` (no Node/Input); the 3D controller maps Vector2 → Vector3 and drives physics.
- **2D scenes:** `test_movement.tscn`, `player.tscn`, and related 2D assets are kept for existing headless tests; do not add new features to 2D. New tests should use the 3D scene (see `tests/scenes/levels/test_3d_scene.gd`).

## Common Commands

```bash
# Validate GDScript syntax
timeout 120 godot --headless --check-only

# Run all tests
./ci/scripts/run_tests.sh
# Or: timeout 300 godot --headless -s tests/run_tests.gd
```

## ⏱ Always Use Timeout

All Godot invocations must use `timeout` to prevent hanging:
- `timeout 120` — syntax checks
- `timeout 300` — full test suite
- `timeout 600` — builds/exports

## File Editing & Moves

Prefer `git mv` for renames/moves so history is preserved.
