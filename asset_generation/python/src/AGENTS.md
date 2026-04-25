# PYTHON ASSET GENERATION - KNOWLEDGE BASE

**Generated:** 2026-04-23  
**Package:** blender-experiments (asset_generation/python)  
**Purpose:** Procedural enemy/level asset generation via Blender Python API

## OVERVIEW

Python package for procedural asset generation. Organized as deep module garden (~19 __init__.py files across 5-6 depth levels). Explicit packaging with module-level imports; Pydantic/TypedDict for FastAPI payloads.

## STRUCTURE (module garden, ~19 __init__.py)

- **core/**: utilities, rig models (`rig_models/`)
- **enemies/**: generation pipeline, animated builders, zone geometry extras
- **model_registry/**: service.py (manifest loading), schema.py (validation)
- **player/**, **animations/**, **body_families/**, **combat/**
- **utils/build_options/**: build configuration schema
- **blobert_asset_pipeline_mcp/**: MCP CLI component

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Enemy generation | `src/enemies/` | Procedural assembly from primitive parts library |
| Model registry service | `src/model_registry/service.py` | Manifest loading, path normalization, mutation/slot handling |
| Build schema | `src/utils/build_options/schema.py` | 1513 lines; zone features, mesh defaults, validation |
| Geometry attachments | `src/enemies/zone_geometry_extras/attachment.py` | Blender geometry construction (617 lines) |
| MCP CLI entry | `src/blobert_asset_pipeline_mcp/__main__.py` | Command-line interface for asset pipeline tasks |

## CODE MAP

| Symbol | Type | Location | Refs | Role |
|--------|------|----------|------|------|
| `model_registry` | module | `src/model_registry/` | Backend import | Registry service for enemy/player models |
| `schema.py` | module | `src/utils/build_options/schema.py` | 1513 lines | Build config validation, zone features |
| `service.py` | class | `src/model_registry/service.py` | 597 lines | Manifest loading/patching, path normalization |
| `attachment.py` | module | `src/enemies/zone_geometry_extras/attachment.py` | 617 lines | Blender geometry attachment logic |

## CONVENTIONS

- **Module-level imports**: Required; lazy imports need explicit justification
- **Typed dicts / Pydantic**: For FastAPI payloads; avoid bare `dict` in asset_generation/**
- **Explicit packaging**: Each domain has its own __init__.py with clear responsibilities
- **Blender API isolation**: Geometry logic separated from Blender calls via adapters

## ANTI-PATTERNS (THIS MODULE)

| Pattern | Why Forbidden | Evidence |
|---------|---------------|----------|
| Bare `dict` usage | Blocks type safety; use TypedDict/Pydantic instead | asset_generation/** policy; Pydantic for FastAPI payloads |
| Monolithic schema.py | 1513 lines; hard to test, risky changes | Refactor: split into core_schema.py, zone_schema.py, mesh_schema.py |
| Blender coupling in logic | Breaks testability; isolate pure math from bpy calls | attachment.py; refactor geometry_core + attachment_utils |

## COMPLEXITY HOTSPOTS (>500 lines)

| File | Lines | Refactor Plan |
|------|-------|---------------|
| `schema.py` | 1513 | Split into core/zone/mesh/texture/placement submodules; add TypedDict models |
| `service.py` | 597 | Extract manifest.py, patching.py, path_utils.py modules |
| `attachment.py` | 617 | Split geometry_core (pure math) + attachment_utils (Blender glue) |

## COMMANDS

```bash
# Run asset pipeline
cd asset_generation/python && uv run python main.py

# MCP CLI entry
uv run python -m blobert_asset_pipeline_mcp

# Python tests with coverage gate
bash .lefthook/scripts/py-tests.sh

# Lint staged files
task hooks:py-review -- {staged_files}
```

## NOTES

- **Package name**: `blender-experiments` (from pyproject.toml)
- **Python version**: 3.11+ (pyproject.toml target-version = "py311")
- **Linter rules**: Ruff select=["E9", "F", "I"]; per-file ignore __init__.py F401
- **Test isolation**: Use unittest.mock (patch, MagicMock) over pytest monkeypatch unless mocking poorly handles os.environ swaps
