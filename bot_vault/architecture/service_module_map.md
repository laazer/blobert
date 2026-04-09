# Service and Module Map

Evidence-backed map of active subsystems in this repository.

## Top-level runtime surfaces

| Surface | Role | Key paths |
| --- | --- | --- |
| Godot runtime | Gameplay scenes/scripts and headless tests | `project.godot`, `scripts/`, `scenes/`, `tests/` |
| Python asset pipeline | Procedural generation/model registry/services | `asset_generation/python/src/`, `asset_generation/python/tests/` |
| Web asset editor | Local editor frontend + FastAPI backend | `asset_generation/web/frontend/`, `asset_generation/web/backend/` |

## Naming resolution table

| Directory | Package/module name | Container/image | Deployed service | Port | Evidence |
| --- | --- | --- | --- | --- | --- |
| `asset_generation/python` | `blender-experiments` | N/A | N/A | N/A | `asset_generation/python/pyproject.toml` |
| `asset_generation/web/backend` | FastAPI app `Blobert Asset Editor API` | N/A | N/A | `8000` | `asset_generation/web/backend/main.py`, `asset_generation/web/backend/core/config.py`, `asset_generation/web/start.sh` |
| `asset_generation/web/frontend` | N/A | N/A | N/A | `5173` (dev) | `asset_generation/web/start.sh`, backend CORS defaults |
| `asset_generation/python/src/model_registry` | module `model_registry` | N/A | N/A | N/A | Imported by backend registry router |
| `project.godot` (root app) | Godot project `blobert` | N/A | N/A | N/A | `project.godot` |

## Backend API module layout

`asset_generation/web/backend/main.py` registers these routers:

- `files`
- `run`
- `assets`
- `meta`
- `registry`

These route groups are API modules within the same backend runtime, not separate deployed services.
