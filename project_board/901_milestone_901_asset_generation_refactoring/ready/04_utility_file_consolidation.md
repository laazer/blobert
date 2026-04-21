# Utility File Consolidation

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Reorganize the `utils/` directory (20+ files with unclear boundaries) into a clear, navigable structure. Consolidate constants, configuration, export utilities, and shared helpers into focused modules. Reduce cognitive overhead of finding things.

## Acceptance Criteria

- [ ] `config.py` (new): All constants and configuration values (EnemyTypes, AnimatedBuildOptions enums, etc.)
- [ ] `build_options.py` (refactored): Animated build options schema and validation (from Phase 2 ticket)
- [ ] `export.py` (new): Unified export naming, GLB validation, file I/O utilities
- [ ] `validation.py` (new): Shared validation helpers (not specific to build options or materials)
- [ ] `simple_viewer.py` (keep): Visualization utility (no changes)
- [ ] Orphaned utility files consolidated or deleted
- [ ] All imports updated; no dangling references
- [ ] All tests pass with new structure
- [ ] Type hints improved: no bare `dict`, use dict[str, T] or TypedDict

## Dependencies

- Import standardization (`done/01_import_standardization.md`) — satisfied.
- Animated build options consolidation (`ready/06_animated_build_options_consolidation.md`): may proceed in parallel; spec must define API boundary and sequencing for `build_options.py` vs. ticket 06 deliverables.

## Execution Plan

### Planner execution summary (authoritative task graph)

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Freeze `asset_generation/python/src/utils` module layout, public APIs, file-to-symbol migration map, and coordination rules with `06_animated_build_options_consolidation` (facade vs. decomposition; LOC targets per module) | Spec Agent | This ticket; current `utils/` tree; consumer imports across `asset_generation/python` and backend | Written specification with requirement IDs, explicit exports per new module, forbidden imports/cycles, and TypedDict/dict[str, T] contracts | None | `python ci/scripts/spec_completeness_check.py <spec> --type generic` passes when applicable; no unresolved boundary between config vs. materials vs. build_options vs. validation vs. export | **Assumption:** Import standardization (M901-01) is complete. **Risk:** Overlap with ticket 06; spec must nail re-export/split strategy. **Risk:** “< 250 LOC per module” conflicts with large `build_options`; spec resolves exemption or submodule split. |
| 2 | Design behavior-first tests for consolidation invariants (importability, no dangling symbols, export/validation behaviors) | Test Designer Agent | Approved spec; pytest layout under `asset_generation/python/tests` | Tests that fail on broken re-exports, missing modules, or invalid GLB/path handling per spec — not markdown prose | 1 | Tests are deterministic and assert runtime behavior / schemas, not ticket wording | **Risk:** Tests grep-only; mitigated by spec-driven behavioral cases |
| 3 | Adversarial pass: edge cases, partial migration, circular import attempts, rename regressions | Test Breaker Agent | Tests from task 2; spec | Strengthened negative and boundary tests | 2 | Suite catches incomplete consolidation and import graph regressions | **Risk:** Flaky import-order tests; keep focused on public API |
| 4 | Implement file moves/merges: `config.py`, `export.py`, `validation.py`; integrate `build_options.py` per spec; keep `simple_viewer.py`; retain `materials.py` only if spec keeps materials constants separate; delete orphans; update all imports | Implementation Generalist Agent | Spec + tests; full Python tree under scope | Clean `utils/` layout matching acceptance criteria; no dangling references; improved typing per AC | 3 | Full pytest suite for asset generation passes; `bash ci/scripts/diff_cover_preflight.sh` passes when Python changed | **Risk:** Large mechanical diff; assumption: follow spec symbol map exactly |
| 5 | Static QA (lint/type) and integration smoke (generator/build paths touched by imports) | Static QA Agent then Integration Agent | Final diff; test results | Verdict and any follow-up fixes | 4 | No new static errors; integration workflows run without import errors | **Risk:** Environment-specific paths; rely on CI-equivalent commands |

### Legacy reference — Current Utils State & Consolidation Plan

| Current File(s) | New Location | LOC | Action |
|----------|---------------|-----|--------|
| constants.py | config.py | 150+ | Move, consolidate |
| enemy_slug_registry.py | config.py | 50+ | Merge |
| animated_build_options*.py | build_options.py | 1,669 | Phase 2 output |
| export_*.py (scattered) | export.py | 100+ | Consolidate |
| simple_viewer.py | simple_viewer.py | 150 | Keep as-is |
| materials.py (constants) | Keep separate | 187 | Keep (materials layer) |
| Other utility helpers | validation.py | TBD | Consolidate |

### Module Breakdown

| Module | Lines | Responsibility | Public API |
|--------|-------|-----------------|------------|
| `config.py` | ~200 | All project constants, enums, defaults | `EnemyTypes`, `ZoneTypes`, `MATERIAL_DEFAULTS`, etc. |
| `build_options.py` | ~900 | Build option schema and validation | From Phase 2 consolidation |
| `export.py` | ~150 | Export utilities, GLB naming, file I/O | `get_export_path()`, `validate_glb()`, `export_manifest_entry()` |
| `validation.py` | ~100 | Shared validation helpers | `validate_path()`, `validate_enum()`, etc. |

### File Changes Summary

| Action | Files | Priority |
|--------|-------|----------|
| Create | config.py, export.py, validation.py | High |
| Consolidate into | config.py (constants.py, enemy_slug_registry.py) | High |
| Move/Integrate | build_options.py from Phase 2 | High |
| Keep | simple_viewer.py, materials.py | N/A |
| Delete | Orphaned/empty files (post-audit) | High |
| Update imports | All builders, routers, pipeline code | High |

### Success Criteria

- `utils/` now has 6 focused modules instead of 20+ scattered files
- Each module < 250 LOC with clear responsibility
- All tests pass with new import structure
- IDE autocomplete works; imports discoverable
- No circular dependencies
- Type hints: dict → dict[str, T], enums used instead of string literals

## Notes

- Can run in parallel with Phase 2 refactorings
- High impact on code navigation and onboarding
- Enums reduce string literal bugs (type safety)
- Export consolidation unifies GLB naming conventions
- Planner checkpoint `project_board/checkpoints/M901-04-utility-file-consolidation/2026-04-21T21-18-00Z-planning.md` records assumptions for ticket 06 and LOC vs. `build_options` size.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

STATIC_QA

## Revision

6

## Last Updated By

Python Reviewer Agent (M901-04)

## Validation Status

- Tests: Pass — `uv run pytest asset_generation/python/tests/` (2159 passed, 8 skipped, 2026-04-21)
- Utils spot-check: Pass — `uv run pytest asset_generation/python/tests/utils/` (1047 passed, 33 subtests, 2026-04-21)
- Static QA: Pending (Acceptance Criteria Gatekeeper)
- Integration: Not Run
- Diff-cover: Pass — `bash ci/scripts/diff_cover_preflight.sh` (threshold 85%, 97% on diff)

## Blocking Issues

- None.

## Escalation Notes

- None.

---

# NEXT ACTION

## Next Responsible Agent

Acceptance Criteria Gatekeeper

## Required Input Schema

```json
{
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/ready/04_utility_file_consolidation.md",
  "spec_path": "project_board/specs/m901_04_utility_file_consolidation_spec.md",
  "implementation_evidence": {
    "pytest": "uv run pytest asset_generation/python/tests/ — 2159 passed, 8 skipped",
    "diff_cover_preflight": "bash ci/scripts/diff_cover_preflight.sh — PASS (97% on diff vs origin/main)",
    "checkpoint": "project_board/checkpoints/M901-04-utility-file-consolidation/2026-04-21T22-30-00Z-implementation.md"
  },
  "verify_ac_against": "project_board/901_milestone_901_asset_generation_refactoring/ready/04_utility_file_consolidation.md Acceptance Criteria + spec R1–R9"
}
```

## Status

Handoff

## Reason

M901-04 implementation complete: `config.py`, `export.py` (`validate_glb_path`), `validation.py` (`clamp01`), `utils/build_options/` package with `animated_build_options*.py` moved off utils root; removed `constants.py`, `enemy_slug_registry.py`, `export_naming.py`, `export_subdir.py`, `demo.py`; imports updated under `asset_generation/python` and `asset_generation/web`; `test_enemy_slug_registry_contract` updated for `config`. Do not move ticket to `done/` until gatekeeper approval.
