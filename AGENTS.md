# PROJECT KNOWLEDGE BASE

**Generated:** 2026-04-23  
**Commit:** (git rev-parse --short HEAD)  
**Branch:** (git rev-parse --abbrev-ref HEAD)

## OVERVIEW

**blobert** is a Godot 4+ experimental platformer ("Lab Escape Slime") with procedural asset generation and a web-based editor. Three runtimes: **Godot gameplay**, **Python/Blender asset pipeline**, **FastAPI + Vite frontend**. Developed entirely via multi-agent TDD.

## STRUCTURE

```
blobert/
├── scripts/          # GDScript runtime (player, enemies, movement)
├── scenes/           # Godot scenes (.tscn), procedural assembly
├── tests/            # Headless test suite (GDScript + shell)
├── asset_generation/
│   ├── python/       # Blender pipeline (blender-experiments package)
│   └── web/          # Asset editor (FastAPI backend + Vite frontend)
├── project_board/    # Milestone specs, done docs, checkpoints
├── reference_projects/ # Read-only external Godot demos/kits
├── ci/scripts/       # Test runner, lint hooks
└── CLAUDE.md         # Operating manual for coding agents
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Player movement logic | `scripts/player/`, `scripts/movement/` | `movement_simulation.gd` is pure 2D math; `player_controller_3d.gd` maps to 3D |
| Enemy systems | `scripts/enemies/`, `asset_generation/python/src/enemies/` | Runtime: enemy_base, attack hitboxes. Pipeline: procedural generation |
| Asset pipeline | `asset_generation/python/src/` | Python package `blender-experiments`; uses explicit packaging (__init__.py) |
| Web editor backend | `asset_generation/web/backend/` | FastAPI app "Blobert Asset Editor API"; port 8000; route-first structure |
| Web editor frontend | `asset_generation/web/frontend/` | Vite + React + TypeScript; port 5173 dev server |
| Headless tests | `ci/scripts/run_tests.sh`, `tests/run_tests.gd` | Timeout 300s; exits 0=pass, 1=fail |
| Agent instructions | `CLAUDE.md`, `.claude/agents/` | Project operating manual + specialized subagent definitions |

## CODE MAP

| Symbol | Type | Location | Refs | Role |
|--------|------|----------|------|------|
| `ProjectController3D` | class | `scripts/project_controller_3d.gd` | 5+ | Root node for Godot project |
| `PlayerController3D` | class | `scripts/player/player_controller_3d.gd` | ~10 | Player behavior controller (3D) |
| `MovementSimulation` | class | `scripts/movement/movement_simulation.gd` | 8+ | Pure physics simulation (2D math → 3D mapping) |
| `EnemyBase` | class | `scripts/enemies/enemy_base.gd` | ~15 | Base enemy state/behavior |
| `RunSceneAssembler` | script | `scenes/levels/procedural_run.tscn` | N/A | Procedurally assembles run from room templates |
| `model_registry` | module | `asset_generation/python/src/model_registry/` | Backend import | Registry service for enemy/player models |

## CONVENTIONS

- **Godot**: base_*.gd (core physics), *_controller.gd (behavior), *_hitbox.gd (combat). class_name for globally accessible scripts.
- **Python**: Module-level imports required. Typed dicts / Pydantic for FastAPI payloads. Avoid bare `dict` in asset_generation/**.
- **Naming**: Stable filenames describing behavior/location (e.g., `test_registry_path_policy.py`). No ticket IDs in names.
- **Git**: Conventional Commits (`feat(scope):`, `fix(scope):`, etc.). Use `git mv` for renames.
- **Constants**: Colocate near configured class/module. Shared constants only when truly cross-cutting.

## ANTI-PATTERNS (THIS PROJECT)

| Pattern | Why Forbidden | Evidence |
|---------|---------------|----------|
| `godot --check-only` | Hangs indefinitely; headless initializes main scene, runs physics with no collision resolution, never exits | CLAUDE.md p.173-178; project_board/* |
| Shotgun debugging / random changes | Wastes tokens, breaks codebase, ignores root causes | CLAUDE.md p.202 |
| `as any`, `@ts-ignore` suppression | Type safety violation; blocks proper error detection | Behavior_Instructions |
| Empty catch blocks | Hides errors, makes debugging impossible | Code Quality |
| Generated/binary files in edits | *.glb, generated JSON/images are read-only unless explicitly targeted | CLAUDE.md p.85-89 |
| Reference project modification | reference_projects/ is read-only; never add blobert runtime code there | CLAUDE.md p.93-94 |

## UNIQUE STYLES

- **Procedural runs**: Main scene (`procedural_run.tscn`) assembled at runtime via `RunSceneAssembler` from room templates, not static scenes.
- **Physical mutation system**: Detach chunks → infect weakened enemies → absorb mutations; fusion creates hybrids occupying both slots.
- **Multi-agent development**: Entire codebase developed via AI agents (planner → spec → test-designer → test-breaker → implementation). Human input steers scope/review only.
- **2.5D gameplay**: Single 3D world with constrained movement (side-view camera, plane-constrained physics).

## COMMANDS

```bash
# Development
task editor                 # Start asset editor stack (backend + frontend)
godot project.godot         # Open Godot editor (bin/godot on PATH via direnv)

# Testing
timeout 300 ci/scripts/run_tests.sh     # Full suite (Godot + Python + Frontend)
timeout 300 godot --headless -s tests/run_tests.gd  # Godot-only
bash .lefthook/scripts/py-tests.sh      # Python + diff-cover gate

# Linting
task hooks:py-review {files}   # Ruff (E9, F, I) on staged files
task hooks:gd-review {files}   # GDScript reviewer on staged files

# Git
git mv old_path new_path       # Preserves history for renames
```

## NOTES

- **direnv setup**: `.envrc` places `bin/godot` and CI scripts on PATH; sets `UV_PROJECT=asset_generation/python`; prepends `.venv/bin` after `uv sync --extra dev`.
- **Test isolation**: Use `unittest.mock` (`patch`, `MagicMock`) over pytest's monkeypatch unless mocking poorly handles the case (e.g., os.environ swaps).
- **Complexity hotspots** (>500 lines): `movement_simulation.gd` (687), `schema.py` (1513), `service.py` (597), `attachment.py` (617) — refactoring candidates.
- **Non-standard patterns**: GDScript in `assets/Models/gobot/gobot_skin.gd`; external kit duplication in `reference_projects/`. Consider vendor strategy or Git subtree.
