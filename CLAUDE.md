# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**blobert** is a Godot 4+ game project. The primary scripting language is GDScript; C# (Mono) support is also configured via `.gitignore` patterns.

## Common Commands

Godot projects are primarily developed through the Godot editor, but the engine can also be invoked via CLI:

```bash
# Validate GDScript syntax without running the project
godot --headless --check-only

# Run the project headlessly (useful for CI/testing)
godot --headless

# Export the project (requires export templates installed)
godot --headless --export-release "Linux/X11" ./build/blobert
```

> If `godot` is not on your PATH, it may be installed as `godot4` or require a full path.

## Godot Project Structure (expected as project grows)

- `project.godot` — Main project configuration file; defines project name, entry scene, renderer settings, etc.
- `scenes/` — Godot scene files (`.tscn`). Each scene is a reusable tree of nodes.
- `scripts/` — GDScript (`.gd`) or C# (`.cs`) files attached to nodes.
- `assets/` — Raw assets: sprites, audio, fonts, etc.
- `resources/` — Custom Godot resources (`.tres`, `.res`) such as stat configs, themes, and materials.
- `.godot/` — Auto-generated import cache; never committed (in `.gitignore`).

## Key Godot 4 Patterns

- Scenes are composed of **Nodes** in a tree hierarchy. Scripts attach to nodes via `extends NodeType`.
- Signals are the primary event/communication system between nodes — prefer signals over direct node references where possible.
- `@export` annotates variables to be editable in the Godot inspector.
- Use `autoload` (Project Settings > Autoload) for singleton/global state managers.
- GDScript is statically typed when type hints are used — prefer typed GDScript for maintainability.
