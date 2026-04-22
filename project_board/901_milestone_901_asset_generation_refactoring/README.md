# Epic: Milestone 901 — Asset Generation Refactoring

**Milestone catalog number:** `901`  
**Folder:** `project_board/901_milestone_901_asset_generation_refactoring/`

This number distinguishes this track from the parallel Milestone 9 work in `9_milestone_9_enemy_player_model_visual_polish` (both historically sat under a `9_milestone_9_*` path).

**Goal:** Consolidate asset-generation Python logic and API transport into one cohesive package architecture (`blobert_asset_gen`) with explicit domain/service/api boundaries, while preserving existing endpoint contracts.

## Context

The asset generation codebase (`asset_generation/python/`) was originally written as a command-line tool but has grown significantly. It now has monolithic modules, scattered imports, mixed responsibilities, and code duplication that blocks new feature development. The local editor backend (`asset_generation/web/backend`) also carries duplicated bootstrap, policy, and orchestration logic.

This milestone now targets a single Python package layout where:
- domain logic remains framework-agnostic,
- service layer owns orchestration/security policy,
- API layer (FastAPI routers) stays thin and transport-only.

## Execution order (`ready/`)

Tickets are prefixed `NN_` in recommended dependency order:

| # | Ticket file |
|---|-------------|
| 01 | `01_import_standardization.md` |
| 02 | `02_model_registry_layering.md` |
| 03 | `03_type_hints_and_documentation.md` |
| 04 | `04_utility_file_consolidation.md` |
| 05 | `05_material_system_refactoring.md` |
| 06 | `06_animated_build_options_consolidation.md` |
| 07 | `07_enemy_builder_template.md` |
| 08 | `08_blender_utilities_split.md` |
| 09 | `09_zone_geometry_extras_decomposition.md` |
| 10 | `10_backend_python_import_adapter.md` |
| 11 | `11_registry_path_policy_unification.md` |
| 12 | `12_registry_mutation_service_boundary.md` |
| 13 | `13_backend_registry_service_extraction_and_router_thinning.md` |
| 14 | `14_backend_error_mapping_unification.md` |
| 15 | `15_run_contract_unification.md` |
| 16 | `16_metadata_catalog_single_source.md` |
| 17 | `17_export_directory_contract_consolidation.md` |
| 18 | `18_shared_manifest_schema_contract.md` |
| 19 | `19_material_system_dry_oop_decomposition.md` |
| 20 | `20_enemy_builder_composition_template_extraction.md` |
| 21 | `21_animated_build_options_modularization.md` |

## Scope (by phase)

### Phase 1: High-ROI, Low-Risk Cleanup (tickets 01–02)
- Import standardization (`sys.path` hacks → absolute imports)
- Model registry layering (schema → store → migrations → service)

### Phase 1b: Quality baseline (tickets 03–04)
- Type hints and documentation
- Utility file reorganization

### Phase 2: Core monolith decomposition (tickets 05–06)
- Material system refactoring (split large orchestrator into focused modules)
- Animated build options consolidation

### Phase 3: Architectural cleanup (tickets 07–09)
- Enemy builder template extraction
- Blender utilities split
- Zone geometry extras decomposition

### Package convergence (Python + backend) (tickets 10–18)
- Introduce import adapter and service boundaries as an incremental bridge.
- Move router-local orchestration/security helpers into package service modules.
- Keep endpoint contracts stable while backend code converges into unified package structure.

### DRY and OOP hardening (tickets 19–21)
- Material system DRY/OOP follow-on
- Enemy builder composition template extraction
- Animated build options modularization

## Target Architecture (End State)

- Canonical package root is `asset_generation/python/blobert_asset_gen` (or equivalent package name finalized in-ticket).
- Internal layering is explicit:
  - `blobert_asset_gen.domain` for pure asset logic and schemas.
  - `blobert_asset_gen.services` for orchestration, policy, and use-case flows.
  - `blobert_asset_gen.api` for FastAPI transport concerns only.
- `asset_generation/web/backend` remains only as compatibility shell or entrypoint glue until fully retired (no duplicated domain/security logic).
- No route handler performs direct `sys.path` mutation or Blender bootstrap.

## Exit Criteria

- All Python files pass type checking (`dict` → `dict[str, T]`, Pydantic models for API payloads where appropriate)
- No monolithic modules > 200 LOC with mixed responsibilities (per milestone intent; confirm against ticket acceptance criteria)
- Import patterns standardized (no ad-hoc `sys.path` hacks, no try/except imports except where justified)
- Shared service/policy modules are the single source for registry/run behavior used by both CLI and API paths
- API layer stays thin: request/response validation, error mapping, status codes
- Code duplication in enemy builders reduced materially
- All existing tests pass; test coverage ≥ 85% on refactored modules where applicable

## Status folders

- `ready/` – Clearly defined ticket with acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest/integration validation
- `done/` – Merged, verified
