# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**blobert** is a Godot 4+ game project. The primary scripting language is GDScript; C# (Mono) support is also configured via `.gitignore` patterns.

## Development target: 3D scenes

Development is for **3D scenes**: 2.5D with one 3D world and 2D-like gameplay.

- **Main scene:** `res://scenes/test_movement_3d.tscn` (set in `project.godot` as `run/main_scene`).
- **Player:** `PlayerController3D` in `scripts/player_controller_3d.gd`; scene `scenes/player_3d.tscn`. Use **CharacterBody3D**, **Camera3D**, **Area3D**, **Node3D**, etc. for new gameplay and levels.
- **Movement logic:** Shared pure simulation in `scripts/movement_simulation.gd` (no Node/Input); the 3D controller maps Vector2 → Vector3 and drives physics.
- **2D scenes:** `test_movement.tscn`, `player.tscn`, and related 2D assets are kept for existing headless tests; do not add new features to 2D as the primary target. New tests for playable content should use the 3D scene (see `tests/test_3d_scene.gd`).

## Common Commands

Godot projects are primarily developed through the Godot editor, but the engine can also be invoked via CLI:

```bash
# Validate GDScript syntax without running the project
godot --headless --check-only

# Run the project headlessly (useful for CI/testing)
godot --headless

# Run all tests headlessly (recommended for CI and automated testing)
./ci/scripts/run_tests.sh
# Or manually: timeout 300 godot --headless -s tests/run_tests.gd

# Export the project (requires export templates installed)
godot --headless --export-release "Linux/X11" ./build/blobert
```

> If `godot` is not on your PATH, it may be installed as `godot4` or require a full path.
> The test script includes a 5-minute timeout to prevent hanging tests from blocking CI.

## ⏱ Godot Execution Rule: Always Use Timeout

**Critical rule:** All Godot invocations must use the `timeout` command to prevent hanging indefinitely.

- Recommended timeouts:
  - `timeout 120` — Syntax checks, quick operations
  - `timeout 300` — Full test suite (5 minutes)
  - `timeout 600` — Complex builds or exports (10 minutes)
  
**Example:**
```bash
# Good: Protected by timeout
timeout 300 godot --headless -s tests/run_tests.gd

# Bad: No timeout, can hang forever
godot --headless -s tests/run_tests.gd
```

This protects CI/automated workflows from hanging and blocking other tasks.

## Godot Project Structure (expected as project grows)

- `project.godot` — Main project configuration file; defines project name, entry scene, renderer settings, etc.
- `scenes/` — Godot scene files (`.tscn`). Each scene is a reusable tree of nodes.
- `scripts/` — GDScript (`.gd`) or C# (`.cs`) files attached to nodes.
- `assets/` — Raw assets: sprites, audio, fonts, etc.
- `resources/` — Custom Godot resources (`.tres`, `.res`) such as stat configs, themes, and materials.
- `.godot/` — Auto-generated import cache; never committed (in `.gitignore`).

## File Editing & Moves

- Prefer `git mv` or `mv` for any file renames or moves so history is preserved.
- Avoid delete+recreate patterns for moves unless a tool only supports add/delete semantics.

## Key Godot 4 Patterns

- Scenes are composed of **Nodes** in a tree hierarchy. Scripts attach to nodes via `extends NodeType`.
- Signals are the primary event/communication system between nodes — prefer signals over direct node references where possible.
- `@export` annotates variables to be editable in the Godot inspector.
- Use `autoload` (Project Settings > Autoload) for singleton/global state managers.
- GDScript is statically typed when type hints are used — prefer typed GDScript for maintainability.
