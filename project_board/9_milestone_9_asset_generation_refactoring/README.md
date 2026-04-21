# Epic: Milestone 9 – Asset Generation Refactoring

**Goal:** Clean up and refactor the Python asset generation codebase for maintainability and extensibility.

## Context

The asset generation codebase (asset_generation/python/) was originally written as a command-line tool but has grown significantly. It now has monolithic modules, scattered imports, mixed responsibilities, and code duplication that blocks new feature development. This milestone consolidates the codebase into layered, cohesive modules.

## Scope

### Phase 1: High-ROI, Low-Risk Cleanup (3–4 days)
- Import standardization (sys.path hacks → absolute imports)
- Model registry layering (schema → store → migrations → service)

### Phase 2: Core Monolith Decomposition (10–12 days)
- Material system refactoring (split 896 LOC god object into focused modules)
- Animated build options consolidation (merge 5 scattered files into 2 cohesive modules)
- Utility file reorganization (clear boundaries in utils/)

### Phase 3: Architectural Cleanup (5–7 days)
- Enemy builder template extraction (reduce duplication in 5 enemy classes)
- Blender utilities split (split 628 LOC jumble into 3 focused modules)
- Zone geometry extras decomposition (extract testable math/placement from untestable monolith)

## Exit Criteria

- All Python files pass type checking (dict → dict[str, T], add Pydantic models for API payloads)
- No monolithic modules > 200 LOC with mixed responsibilities
- Import patterns standardized (no sys.path hacks, no try/except imports)
- Code duplication in enemy builders reduced by 50%+
- All existing tests pass; test coverage ≥ 85% on refactored modules

## Status Folders

- `ready/` – Clearly defined ticket with acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest/integration validation
- `done/` – Merged, verified
