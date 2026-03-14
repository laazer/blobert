# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**blobert** is a Godot 4+ game project. The primary scripting language is GDScript.

## Development target: 3D scenes

Development is for **3D scenes**: 2.5D with one 3D world and 2D-like gameplay.

- **Main scene:** `res://scenes/levels/sandbox/test_movement_3d.tscn` (set in `project.godot` as `run/main_scene`).
- **Player:** `PlayerController3D` in `scripts/player/player_controller_3d.gd`; scene `scenes/player/player_3d.tscn`. Use **CharacterBody3D**, **Camera3D**, **Area3D**, **Node3D**, etc. for new gameplay and levels.
- **Movement logic:** Shared pure simulation in `scripts/movement/movement_simulation.gd` (no Node/Input); the 3D controller maps Vector2 → Vector3 and drives physics.
- **New tests** should use the 3D scene (see `tests/scenes/levels/test_3d_scene.gd`).

## Common Commands

`direnv` puts `bin/godot` (headless wrapper) and `ci/scripts/` on PATH automatically.

```bash
# Run all tests (also catches parse errors — preferred over --check-only)
run_tests.sh
# Or directly:
timeout 300 godot -s tests/run_tests.gd

# Force reimport (rebuilds class cache — run if tests fail to load scripts)
godot --import
```

## ⏱ Always Use Timeout

When invoking Godot outside of `run_tests.sh`, use a timeout to prevent hanging:
- `timeout 300 godot -s tests/run_tests.gd` — full test suite

## ⚠️ Do Not Use `--check-only`

`godot --check-only` hangs indefinitely in this project. In Godot 4.6.1 headless mode it initializes the main scene, which runs physics scripts without collision resolution — the enemy falls forever and the process never exits. The test runner catches parse errors directly (script load fails with an explicit error), so `--check-only` provides no additional safety.

## File Editing & Moves

Prefer `git mv` for renames/moves so history is preserved.
