# CLAUDE.md

This file is the repository-level operating manual for Claude Code and other coding agents.

## Project Overview

**blobert** is a Godot 4+ game project with a non-traditional setup:

- **Game runtime:** Godot scenes/scripts (primary language: GDScript)
- **Asset pipeline:** Python/Blender-oriented tooling under `asset_generation/python`
- **Local asset editor stack:** FastAPI backend + frontend dev server under `asset_generation/web`

## Technology Stack

- Godot 4.x (`project.godot`, GDScript gameplay/runtime)
- Python 3.11+ project at `asset_generation/python` (`pyproject.toml`)
- FastAPI backend at `asset_generation/web/backend`
- Frontend dev server under `asset_generation/web/frontend` (npm scripts)
- Lefthook + Taskfile orchestration (`lefthook.yml`, `Taskfile.yml`)

## Architecture Summary

### Runtime and toolchain topology

1. Godot drives gameplay and tests.
2. Python pipeline code drives procedural asset generation and model registry logic.
3. Asset editor frontend talks to backend API; backend imports model-registry services from Python project code.

### Current structural patterns in this repository

- **Godot gameplay code:** `scripts/`, `scenes/`, `tests/`
- **Python project:** `asset_generation/python/src/...` + `tests/...`
- **Web backend:** route-first FastAPI layout (`main.py`, `routers/`, `core/`, `services/`)
- **Web frontend:** npm app under `asset_generation/web/frontend`

This repo does **not** currently implement a uniform layered pattern like `api -> application -> domain -> infrastructure` across every subsystem. Agents should follow local conventions per subsystem and avoid inventing new global abstractions.

## Naming Convention Resolution Table (Source Of Truth)

Use this table when translating names across directories, packages/modules, runtime services, and ports.

| Directory | Package / Module Name | Container / Image Name | Deployed Service Name | Port | Evidence |
| --- | --- | --- | --- | --- | --- |
| `asset_generation/python` | `blender-experiments` | N/A | N/A | N/A | `asset_generation/python/pyproject.toml` (`[project].name`) |
| `asset_generation/web/backend` | FastAPI app `Blobert Asset Editor API` | N/A | N/A | `8000` | `asset_generation/web/backend/main.py`, `asset_generation/web/backend/core/config.py`, `asset_generation/web/start.sh` |
| `asset_generation/web/frontend` | N/A (no in-repo package metadata found) | N/A | N/A | `5173` (dev) | `asset_generation/web/start.sh`, backend CORS in `asset_generation/web/backend/core/config.py` |
| `asset_generation/web/backend/routers/registry.py` | Router module `registry` (prefix `/api/registry`) | N/A | N/A | N/A | `asset_generation/web/backend/routers/registry.py` |
| `asset_generation/python/src/model_registry` | Python module `model_registry` | N/A | N/A | N/A | Imported by backend router (`asset_generation/web/backend/routers/registry.py`) |
| repo root (`project.godot`) | Godot project `blobert` | N/A | N/A | N/A | `project.godot` (`config/name`) |

When a layer is not present in code/config (Docker image, deployed service), keep it as `N/A` rather than guessing.

## Development Target: 3D Scenes

Development is for **3D scenes**: 2.5D with one 3D world and 2D-like gameplay.

- **Main scene:** `res://scenes/levels/sandbox/test_movement_3d.tscn` (`run/main_scene` in `project.godot`)
- **Player:** `PlayerController3D` in `scripts/player/player_controller_3d.gd`; scene `scenes/player/player_3d.tscn`
- **Movement logic:** `scripts/movement/movement_simulation.gd` is pure simulation (no Node/Input)
- **Tests:** New tests should target the 3D setup (`tests/scenes/levels/test_3d_scene.gd`)

## Non-Traditional Repo Guardrails

### 1) Choose the target runtime first

Before changing code, classify the work surface:

- Godot gameplay/runtime (`scripts/`, `scenes/`, `tests/`)
- Python asset pipeline (`asset_generation/python`)
- Web editor backend/frontend (`asset_generation/web`)

Do not apply conventions from one runtime onto another by default.

### 2) Command source-of-truth order

When commands disagree, resolve in this order:

1. `Taskfile.yml` task entry
2. Hook/CI scripts (`.lefthook/scripts/*`, `ci/scripts/*`)
3. `CLAUDE.md`
4. `README.md` (advisory only if stale)

### 3) Generated/binary artifacts are special

Treat generated or binary files (`*.glb`, generated `*.attacks.json`, generated images/exports) as read-only unless the task explicitly targets regeneration or asset updates. Avoid incidental rewrites.

### 4) Evidence-first documentation updates

Architecture and naming docs must cite concrete files. Missing deploy/container layers stay `N/A`.

### 5) Reference projects are read-only

`reference_projects/` is implementation reference material only. Do not add blobert runtime code there.

## Agent Checkpoints (Autopilot / Autonomous Agents)

- Full checkpoint entries (`Would have asked` / `Assumption made` / `Confidence`) belong only in `project_board/checkpoints/<ticket-id>/<run-id>.md`.
- `project_board/CHECKPOINTS.md` is index-only: headers, pointers, one-line outcomes, and `Log:` paths.

## Common Workflows (Exact Commands)

`direnv` (see `.envrc`) places `bin/godot` and `ci/scripts/` on PATH, sets `UV_PROJECT=asset_generation/python`, and prepends that `.venv/bin` when present (after `cd asset_generation/python && uv sync --extra dev`).

### Run

```bash
# Start local asset editor stack (backend + frontend)
task editor
# equivalent
bash asset_generation/web/start.sh

# Open Godot project
godot project.godot
```

### Asset Pipeline MCP (Cursor / Claude Code)

Coding agents can use a **local stdio MCP** (FastMCP) that proxies the asset editor HTTP API on **:8000**. Setup, `mcp.json` fragments, troubleshooting, and security notes: **`asset_generation/mcp/README.md`**. Normative tool names and routes: **`project_board/specs/asset_pipeline_mcp_spec.md`** (APMCP). Procedural skill (install via symlink): **`asset_generation/resources/agent_skills/blobert-asset-pipeline-mcp/SKILL.md`**.

### Tests

```bash
# Canonical full suite
timeout 300 ci/scripts/run_tests.sh

# Godot-only tests
timeout 300 godot --headless -s tests/run_tests.gd

# Godot import refresh
timeout 120 godot --headless --import

# Python tests + diff-cover gate
bash .lefthook/scripts/py-tests.sh

# Frontend tests
cd asset_generation/web/frontend && npm test
```

### Lint / Review

```bash
# Python staged-file checks (Ruff rules from asset_generation/python/pyproject.toml)
task hooks:py-review -- {staged_files}

# Python org checks
task hooks:py-organization -- {staged_files}

# Godot reviewer/org checks
task hooks:gd-review -- {staged_files}
task hooks:gd-organization -- {staged_files}
```

### Hooks / Pre-Push Equivalents

```bash
task hooks:godot
task hooks:python
```

### Build / Deploy

No explicit build/deploy command is currently defined in `Taskfile.yml` or CI scripts. Treat both as **N/A** until added.

## Critical Execution Constraints

### Always use timeout for Godot CLI

- `timeout 300 godot -s tests/run_tests.gd`
- `timeout 120 godot --headless --import`
- Keep import steps bounded and fail-fast: do not swallow `godot --import` errors with `|| true` or stderr redirection.

### Do not use `godot --check-only`

`godot --check-only` hangs indefinitely in this project and is not an approved workflow here.

## Code Style and Testing Requirements

### File moves

Prefer `git mv` for renames/moves to preserve history.

### Colocate configuration with what it configures

- Keep tuning/default constants near the class/module they configure.
- Create shared constants modules only when values are truly cross-cutting.

### Reviewer policy (new/changed lines)

#### GDScript

- Treat unexplained tuning literals as findings.
- Exempt obvious identity/index literals (`0`, `1`, `-1`, etc.) and named constants/enums/exports.

#### Python

- Prefer module-level imports; lazy imports require explicit justification.
- Treat unexplained tuning/threshold literals as findings.
- In `asset_generation/**`, avoid bare `dict` and untyped dicts: use `dict[str, T]`, `Mapping[str, T]` for read-only arguments, `TypedDict` for fixed key sets, and Pydantic models for FastAPI payloads. Reserve `dict[str, Any]` for validated JSON boundaries (e.g. registry/manifest parse → validate → serialize), not as a routine internal type.

### Test files (all languages)

- **File names** describe *behavior and location*, not backlog tickets. Use stable names like `test_registry_path_policy.py`, `test_python_import_bridge.py`, or `test_<package>_<concern>.py`. Do **not** embed milestone ids, ticket numbers, or `M901-*`-style slugs in filenames. Traceability (ticket path, spec section, or requirement id) belongs in a short module docstring or a comment on the test class, not the filename.
- **Isolation:** Prefer `unittest.mock` (`patch`, `MagicMock`, `AsyncMock`, `PropertyMock` where needed) to replace callables, types, and imported collaborators so expectations stay explicit. Reserve `pytest`’s `monkeypatch` for cases that mocks handle poorly: `os.environ` / `sys.modules` hygiene, restoring singleton settings, or one-off attribute swaps where `patch` would be noisier than the test target. If you use `monkeypatch` for a replaceable dependency, add a one-line note explaining why a mock was not used.

### Pre-commit enforcement

- GDScript checks: `task hooks:gd-review`
- Python Ruff checks: `task hooks:py-review` (`E9`, `F`, `I`)

## Conventional Commits (Going Forward)

Use Conventional Commits format for new commits:

- `feat(scope): ...`
- `fix(scope): ...`
- `refactor(scope): ...`
- `test(scope): ...`
- `docs(scope): ...`
- `chore(scope): ...`

Examples:

- `fix(web-backend): handle missing registry key in asset lookup`
- `test(godot): cover 3d movement recoil edge case`
