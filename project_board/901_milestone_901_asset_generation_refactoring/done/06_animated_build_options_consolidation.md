# Animated Build Options Consolidation

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Consolidate 7 scattered `animated_build_options*.py` files (1,669 LOC total) into 2 cohesive, focused modules. Clarify the separation between schema definitions, validation rules, and parsing logic. This is CRITICAL for adding new enemies without sprawl.

## Acceptance Criteria

- [ ] `schema.py` (new): All control definitions, zones, feature defs consolidated (TypedDict-based)
- [ ] `validate.py` (new): All validation rules and normalization logic
- [ ] Original 7 files deleted (including satellite `_appendage_defs`, `_mesh_controls`, etc.)
- [ ] Public API preserved: `options_for_enemy()`, `get_control_definitions()`, validation functions
- [ ] All existing tests pass; test coverage maintained
- [ ] Adding a new enemy now requires < 150 LOC changes (down from 250+)
- [ ] No circular imports between schema and validate modules
- [ ] Type hints added: dict[str, Any] → dict[str, ControlValue], TypedDict for specific structures

## Dependencies

- Import standardization (ticket #1)
- Model registry layering (ticket #2): Optional

## Execution Plan

### Planner execution summary (authoritative task graph)

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Freeze consolidated build-options contract for `schema.py`, `validate.py`, and package-level API compatibility (`options_for_enemy`, `get_control_definitions`, validation entrypoints), including type aliases (`ControlValue`) and no-circular-import boundaries | Spec Agent | This ticket; current files under `asset_generation/python/src/utils/build_options/`; current consumers under builders/tests | Frozen, requirement-indexed specification with explicit module ownership, API signatures, type contracts, and non-goals (no behavioral drift) | None | Spec is complete, testable, and unambiguous for every acceptance criterion; contract documents deletion/migration mapping for all 7 source files | **Risk:** hidden coupling across scattered option modules can create accidental behavior drift if contracts are underspecified. |
| 2 | Design behavior-first regression tests covering schema composition, normalization/validation behavior, API compatibility, and enemy option generation continuity after consolidation | Test Designer Agent | Approved spec from task 1; existing tests under `asset_generation/python/tests/` that exercise animated build options | Deterministic RED/GREEN behavioral tests encoding acceptance criteria as runtime contracts | 1 | Tests fail on missing consolidation behavior or API drift and pass only when equivalent runtime behavior is preserved | **Risk:** import-only assertions masquerading as coverage; require behavior checks with concrete option dictionaries and enemy presets. |
| 3 | Add adversarial tests for malformed controls, unknown enemy keys, invalid range values, and malformed feature metadata to enforce fail-closed behavior | Test Breaker Agent | Spec from task 1; test suite from task 2 | Additional negative/edge-case tests that detect silent fallback regressions and unsafe normalization | 2 | Suite captures malformed-input paths and enforces deterministic fallback/validation behavior | **Assumption:** malformed eligibility/feature metadata must fail closed per conservative parsing policy. |
| 4 | Implement consolidation by creating `schema.py` and `validate.py`, migrating definitions/validators, preserving package API via `__init__.py`, updating imports, and deleting the 7 legacy `animated_build_options*` modules | Implementation Generalist Agent | Frozen spec + RED tests (tasks 2-3); current `utils/build_options` package | Refactored module layout with preserved public API, removed legacy files, updated callsites, and improved typing (`dict[str, ControlValue]` where applicable) | 3 | All acceptance criteria satisfied; no circular imports; `options_for_enemy`/`get_control_definitions` behavior preserved | **Risk:** migration can break transitive imports in builders/backends; require compatibility re-exports and scoped smoke checks. |
| 5 | Run static/integration validation including required Python diff-cover preflight and targeted animated-build-options test suites | Static QA Agent then Integration Agent | Implementation diff and test results | Verification evidence: passing pytest scope, static checks, and `bash ci/scripts/diff_cover_preflight.sh` when `.py` changes exist | 4 | Required quality gates pass with auditable command evidence and no unresolved regressions | **Risk:** integration regressions may appear only in end-to-end asset generation flows; include at least one enemy generation smoke path from spec. |

### Module Breakdown

| Module | Lines | Responsibility | Public API |
|--------|-------|-----------------|------------|
| `schema.py` | ~700 | Control defs, zone textures, feature defs, presets | `get_control_definitions()`, `CONTROL_SCHEMA`, `ZONE_TEXTURE_PATTERNS`, enemy presets |
| `validate.py` | ~200 | Validation rules, normalization, range checks | `validate_build_options()`, `normalize_controls()` |
| `__init__.py` | ~20 | Re-exports, public API | `options_for_enemy()`, `validate_build_options()` |

### Files to Consolidate

| File | LOC | Consolidate Into |
|------|-----|------------------|
| `animated_build_options.py` | 912 | schema.py + validate.py |
| `animated_build_options_appendage_defs.py` | 288 | schema.py |
| `animated_build_options_mesh_controls.py` | 145 | schema.py |
| `animated_build_options_validate.py` | 113 | validate.py |
| `animated_build_options_zone_texture.py` | 32 | schema.py |
| `animated_build_options_spider_eye.py` | 69 | schema.py (per-enemy specifics) |
| `animated_build_options_part_feature_defs.py` | 110 | schema.py |

### File Changes Summary

| File | Change | Priority |
|------|--------|----------|
| `schema.py` (new) | Consolidate all defs | High |
| `validate.py` (new) | Consolidate validation | High |
| `__init__.py` (new) | Public API re-exports | High |
| 7 old files | Delete | High |
| All builder files | Update imports from `utils.animated_build_options*` → `utils.build_options` | High |
| Test files | Update imports | Medium |

### Success Criteria

- 2 modules with clear responsibility
- Adding new enemy: copy control preset, add to schema, no scattered file changes
- `pytest tests/utils/test_animated_build_options*.py` all pass
- All enemies continue to work (no functional changes)
- Type hints: dict[str, ControlValue] used throughout
- Git diff shows only consolidation, no logic changes

## Notes

- CRITICAL blocker for new enemies; address early
- High test coverage (12 dedicated tests) provides safety
- Untangle spider-eye-specific logic (move to spider builder, not build options)
- Clear ownership per control type prevents future sprawl

## Specification (Frozen)

### Requirement R1: Consolidated Module Ownership and Package Boundary

#### 1. Spec Summary
- **Description:** Animated build-options logic must be consolidated into exactly two implementation modules under `asset_generation/python/src/utils/build_options/`: `schema.py` for definitions/composition and `validate.py` for validation/normalization.
- **Constraints:** Ownership split is strict: `schema.py` contains control definitions, feature definitions, zone texture schemas, and enemy presets; `validate.py` contains validation rules, normalization, coercion, and range checks; no circular imports between these two modules.
- **Assumptions:** Legacy behavior remains authoritative; this ticket does not redesign build-option semantics.
- **Scope:** `asset_generation/python/src/utils/build_options/` and immediate imports from builders/tests that currently consume `animated_build_options*`.

#### 2. Acceptance Criteria
- AC-R1.1: Exactly two consolidation targets (`schema.py`, `validate.py`) hold the migrated logic from the seven legacy `animated_build_options*.py` files.
- AC-R1.2: `schema.py` imports may reference typing/constants/helpers but must not import `validate.py`.
- AC-R1.3: `validate.py` may consume schema-owned definitions through explicit imports, but the resulting import graph remains acyclic.
- AC-R1.4: Package-level API surface in `utils.build_options` remains the single consumer-facing boundary for downstream imports.
- AC-R1.5: No migrated definition/validator remains duplicated across both modules after consolidation.

#### 3. Risk & Ambiguity Analysis
- Hidden coupling across split legacy files can trigger behavior drift if ownership boundaries are not explicit.
- Circular imports are likely when validators need schema metadata; directional dependency must be enforced.
- Strict two-module targeting can regress readability if helper placement is not disciplined.

#### 4. Clarifying Questions
- None. Conservative assumptions logged via checkpoint protocol.

### Requirement R2: Legacy File Retirement and Migration Mapping

#### 1. Spec Summary
- **Description:** All seven listed legacy `animated_build_options*.py` modules are retired, with their responsibilities migrated into `schema.py` and/or `validate.py`.
- **Constraints:** The following files are deleted: `animated_build_options.py`, `animated_build_options_appendage_defs.py`, `animated_build_options_mesh_controls.py`, `animated_build_options_validate.py`, `animated_build_options_zone_texture.py`, `animated_build_options_spider_eye.py`, `animated_build_options_part_feature_defs.py`.
- **Assumptions:** Compatibility is preserved through package API (`utils.build_options`) and import rewiring; retaining any of the seven legacy files as shims violates this ticket.
- **Scope:** File-system changes under `asset_generation/python/src/utils/` and dependent import callsites.

#### 2. Acceptance Criteria
- AC-R2.1: Each of the seven legacy files is absent after implementation.
- AC-R2.2: Every legacy file has an explicit destination mapping in implementation notes or commit diff (`schema.py` and/or `validate.py`).
- AC-R2.3: No runtime import in active code/tests references any deleted legacy module path.
- AC-R2.4: Import rewiring targets `utils.build_options` package API rather than new deep internal paths where a package export exists.

#### 3. Risk & Ambiguity Analysis
- Transitive imports from builders/backends can fail if migration misses deep references.
- Keeping partial shim files could hide incomplete migration and violate AC intent.
- Broad import rewiring can accidentally change load order.

#### 4. Clarifying Questions
- None. Conservative deletion policy logged via checkpoint protocol.

### Requirement R3: Backward-Compatible Public API Contract

#### 1. Spec Summary
- **Description:** Public API behavior remains stable after consolidation so current consumers keep equivalent runtime outcomes.
- **Constraints:** Required callable API remains available: `options_for_enemy()`, `get_control_definitions()`, and validation entrypoints currently exposed to consumers.
- **Assumptions:** API compatibility is behavioral, not just symbol presence; return-shape semantics and fallback behavior must remain consistent for existing enemy/control inputs.
- **Scope:** Package exports in `asset_generation/python/src/utils/build_options/__init__.py` and all callsites in asset-generation code/tests.

#### 2. Acceptance Criteria
- AC-R3.1: Existing consumers can import the required API from the supported package boundary without changing invocation shape.
- AC-R3.2: For currently supported enemy types and option dictionaries, `options_for_enemy()` returns behaviorally equivalent output (same key-space and fallback behavior).
- AC-R3.3: `get_control_definitions()` returns the consolidated control schema with equivalent control availability for existing enemies.
- AC-R3.4: Validation entrypoints preserve pass/fail and normalization outcomes for equivalent valid and invalid inputs.
- AC-R3.5: No public API symbol required by existing tests is removed or renamed in this ticket.

#### 3. Risk & Ambiguity Analysis
- Signature compatibility can pass while subtle output-shape drift breaks downstream builders.
- Consolidation can change defaulting order, especially when schema and validation responsibilities move.
- Exporting internals directly can couple tests to unstable paths.

#### 4. Clarifying Questions
- None.

### Requirement R4: Type System and Data Contract Tightening

#### 1. Spec Summary
- **Description:** Consolidated build-options contracts must replace broad dictionary typing with explicit value/type aliases and TypedDict structures where specified.
- **Constraints:** Replace `dict[str, Any]` at touched boundaries with `dict[str, ControlValue]` (or equivalent alias contract), and use TypedDict for specific schema structures.
- **Assumptions:** Typing improvements are constrained to this consolidation scope and must not force runtime behavior changes.
- **Scope:** `schema.py`, `validate.py`, package exports, and touched callsites/tests that consume typed contracts.

#### 2. Acceptance Criteria
- AC-R4.1: `ControlValue` (or an equivalent explicit type alias) is defined and used for control option mappings in consolidated modules.
- AC-R4.2: Core schema structures (control definitions, feature definitions, or zone definitions) are represented with TypedDict contracts rather than untyped dicts.
- AC-R4.3: Newly introduced public/internal functions in consolidation scope carry explicit type hints for parameters and return values.
- AC-R4.4: Typing changes do not reduce accepted valid runtime inputs compared to legacy behavior.

#### 3. Risk & Ambiguity Analysis
- Over-constrained typing can reject legitimate dynamic option values.
- Partial typing adoption can produce misleading static guarantees.
- TypedDict drift from runtime shape can break tests and future extension work.

#### 4. Clarifying Questions
- None.

### Requirement R5: Validation and Normalization Behavioral Continuity

#### 1. Spec Summary
- **Description:** Validation and normalization logic is centralized in `validate.py` and must preserve existing fail-closed and normalization behavior.
- **Constraints:** Validation must continue to handle malformed or out-of-range control values deterministically; unknown/invalid values must not silently expand capability.
- **Assumptions:** "Fail closed" means invalid values are rejected or normalized to safe defaults according to current behavior, not accepted as-is.
- **Scope:** `validate.py` and all callsites using validation functions from build-options API.

#### 2. Acceptance Criteria
- AC-R5.1: All validation functions from legacy modules are represented in `validate.py` (directly or via equivalent consolidated entrypoints).
- AC-R5.2: Numeric range enforcement and normalization (clamping/coercion/defaulting) remains behaviorally equivalent for existing option inputs.
- AC-R5.3: Malformed feature/control metadata is handled deterministically with no uncaught exceptions on expected invalid-input paths.
- AC-R5.4: Validation behavior remains deterministic across repeated calls with identical input.

#### 3. Risk & Ambiguity Analysis
- Consolidating normalization can accidentally alter precedence of defaults versus user-provided values.
- Error-path regressions are often untested and can surface only in edge enemy configurations.
- Determinism can break if mutable shared defaults are introduced during refactor.

#### 4. Clarifying Questions
- None.

### Requirement R6: Enemy-Addition Scalability and Maintainability Targets

#### 1. Spec Summary
- **Description:** Consolidation must reduce change-surface for adding a new enemy to fewer than 150 LOC by centralizing schema and validation touchpoints.
- **Constraints:** New enemy onboarding should no longer require edits scattered across multiple legacy animated-build-options files.
- **Assumptions:** LOC target is measured as net changed lines needed for a representative new-enemy addition after this refactor, excluding generated artifacts.
- **Scope:** Consolidated build-options modules and package API documentation/comments needed to keep extension path clear.

#### 2. Acceptance Criteria
- AC-R6.1: Representative new-enemy workflow requires edits in consolidated module set only (plus intentional consumer wiring), not in deleted legacy files.
- AC-R6.2: Documented extension path identifies where to add control schema entries and where validation behavior must be updated.
- AC-R6.3: Estimated new-enemy implementation delta is demonstrably under 150 LOC in consolidated design.

#### 3. Risk & Ambiguity Analysis
- LOC target can be gamed by moving complexity into opaque helpers.
- Without explicit extension path, future contributors may recreate sprawl in adjacent modules.
- Enemy-specific edge behavior (for example spider-eye logic) can reintroduce scattered ownership if not contained.

#### 4. Clarifying Questions
- None. Spider-eye ownership note treated as advisory, not in-scope migration in this ticket.

### Requirement R7: Non-Functional Constraints, Quality Gates, and Non-Goals

#### 1. Spec Summary
- **Description:** Refactor must preserve behavior and quality while satisfying integration constraints and avoiding unrelated functional drift.
- **Constraints:** All existing relevant tests must continue to pass; coverage for animated build-options behavior is maintained; no backend-route behavioral changes; no generated-artifact dependency in tests; no unnecessary documentation files.
- **Assumptions:** Runtime-equivalence is validated in downstream test/implementation stages through behavior assertions rather than prose checks.
- **Scope:** Consolidation-related source files, import callsites, and test suites under `asset_generation/python/tests/`.

#### 2. Acceptance Criteria
- AC-R7.1: Post-consolidation test suite for animated build options passes with maintained behavioral coverage.
- AC-R7.2: Consolidation introduces no circular import regressions and no import-time failures in non-Blender unit-test contexts beyond existing constraints.
- AC-R7.3: Refactor diff is limited to consolidation goals (module split/migration/typing/import updates) with no unrelated feature additions.
- AC-R7.4: No new markdown documentation artifact is created solely for this refactor ticket.

#### 3. Risk & Ambiguity Analysis
- Import-cycle issues may pass static inspection but fail at runtime for specific entrypoints.
- Coverage metrics can remain stable while edge-case behavior regresses.
- Scope creep during refactor can add hidden behavior changes.

#### 4. Clarifying Questions
- None.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

COMPLETE

## Revision

10

## Last Updated By

Autopilot Orchestrator

## Validation Status

- Tests (full-scope): `uv run pytest tests -q` executed from `asset_generation/python` => `2256 passed, 8 skipped, 149 subtests passed in 48.78s`. This is explicit broad-suite evidence for "all existing tests pass" in the Python asset-generation scope touched by this ticket.
- Circular-import/import-time proof (objective):  
  - `uv run python -X importtime -c "import src.utils.build_options.schema as s; import src.utils.build_options.validate as v; import src.utils.build_options as bo; print('IMPORT_OK', callable(bo.options_for_enemy), callable(bo.validate_build_options), len(s._ANIMATED_BUILD_CONTROLS))"` => `IMPORT_OK True True 2` with successful import-time trace (no ImportError/cycle failure).  
  - `uv run python -c "import importlib; import src.utils.build_options.validate as v; import src.utils.build_options.schema as s; bo=importlib.import_module('src.utils.build_options'); print('IMPORT_ORDER_OK', callable(bo.options_for_enemy), hasattr(v, 'coerce_validate_enemy_build_options'), hasattr(s, 'options_for_enemy'))"` => `IMPORT_ORDER_OK True True True`.  
  These two commands prove both import directions and package boundary load successfully.
- Maintainability / `<150 LOC` proof (objective, scripted): `uv run python -c "...print('REPRESENTATIVE_NEW_ENEMY_LOC', add_lines)..."` => `REPRESENTATIVE_NEW_ENEMY_LOC 12`, with `SCHEMA_TOUCHPOINTS _FEATURE_ZONES_BY_SLUG _ANIMATED_BUILD_CONTROLS` and `VALIDATE_TOUCHPOINTS none_required_for_standard_controls`. Representative standard new-enemy onboarding remains well under the `<150 LOC` criterion.
- Extension-path proof (schema vs validate separation):  
  - Schema update points for new enemy definitions are explicitly in `src/utils/build_options/schema.py`: add slug ownership in `_FEATURE_ZONES_BY_SLUG` and optional enemy-specific controls in `_ANIMATED_BUILD_CONTROLS` (both confirmed by scripted touchpoint output above).  
  - Validation update points are in `src/utils/build_options/validate.py` only when introducing new control *types* or normalization rules (entrypoint `coerce_validate_enemy_build_options`), not for standard select/int/float/bool controls already covered by current coercion paths.  
  - This documents a concrete split between schema composition and validation logic for extension work.
- Acceptance criteria gate result: All listed acceptance criteria are now backed by explicit automated evidence or direct structural verification in this ticket record; no uncovered AC remains.

## Blocking Issues

- None.

## Escalation Notes

- None.

---

# NEXT ACTION

## Next Responsible Agent

Human

## Required Input Schema

```json
{
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/done/06_animated_build_options_consolidation.md",
  "action": "optional_push_after_review",
  "required_evidence": [
    "All AC evidence remains recorded in Validation Status.",
    "Ticket is already under milestone `done/` with Stage COMPLETE."
  ]
}
```

## Status

Proceed

## Reason

All acceptance criteria are evidenced with objective test/import/maintainability proof, and the ticket now resides under milestone `done/`, satisfying completion policy.
