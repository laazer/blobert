# Import Standardization

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Standardize import patterns across the asset generation Python codebase. Remove `sys.path.insert()` hacks from entry points and consolidate on absolute imports (`from src.enemies.animated import ...`). This unblocks IDE autocomplete, simplifies test setup, and aligns with standard Python packaging.

## Acceptance Criteria

- [ ] All entry points (generator.py, player_generator.py, level_generator.py) use absolute imports with no `sys.path.insert()` calls
- [ ] All internal modules use absolute imports (`from src.enemies.animated import ...`) consistently
- [ ] No `try/except ImportError` fallback patterns exist
- [ ] `__init__.py` files expose public APIs via re-exports (schema, service, material_system, etc.)
- [ ] All tests pass with new import structure
- [ ] IDE autocomplete works correctly for all modules

## Dependencies

- None (foundational change that unblocks all Phase 2 work)

## Execution Plan

# Project: Import Standardization
**Description:** Standardize Python import structure in asset generation by removing path hacks, enforcing absolute imports, and exposing stable package APIs to improve reliability and tooling support.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Freeze import contract and migration spec for entrypoints, internal modules, and package exports | Spec Agent | This ticket's Description and Acceptance Criteria; current Python package layout under `asset_generation/python/src`; backend router usage under `asset_generation/web/backend/routers` | Complete spec with canonical import rules, affected module inventory, and explicit no-fallback policy (`no sys.path.insert`, `no try/except ImportError`) | None | Spec defines exact allowed import patterns and package boundary rules with no ambiguity for test writing | Risk: hidden dynamic imports may not be obvious in static scan; assumption: current runtime relies on import paths that can be represented with package exports |
| 2 | Design behavior-first regression tests for import contract and runtime loading | Test Designer Agent | Approved spec from Task 1; existing pytest structure under `asset_generation/python/tests`; entrypoint scripts and backend integration points | Deterministic tests that fail on path hacks/fallback imports and validate importability/runtime execution without custom path mutation | 1 | Tests fail on old patterns and pass only when absolute-import contract is met | Risk: overfitting tests to file text; assumption: tests verify executable import behavior (module loading / script invocation), not prose |
| 3 | Adversarially strengthen coverage for edge cases and migration regressions | Test Breaker Agent | Tests from Task 2; spec import contract | Additional negative/edge tests for package export gaps, transitive import failures, and mixed-style import regressions | 2 | Suite catches malformed package `__init__.py` exports, partial migration states, and fallback-pattern reintroduction | Risk: brittle test harness around import-time side effects; assumption: test breaker can isolate environment state to avoid false positives |
| 4 | Implement import standardization and package API re-export alignment | Implementation Generalist Agent | Approved spec and tests; target files in `asset_generation/python/src/**`, entrypoints, and backend router integration code | Mechanical code changes replacing path hacks and relative/fallback imports with canonical absolute imports; updated `__init__.py` exports | 3 | All acceptance criteria are satisfied, tests pass, and import structure is consistent across entrypoints/modules | Risk: circular imports introduced by new absolute import graph; assumption: `__init__.py` re-exports are limited to stable public APIs to avoid cycles |
| 5 | Validate static quality and integration readiness before closure | Static QA Agent then Integration Agent | Implementation diff and full test results | QA verdict with lint/static checks and integration confirmation that generators/backend wiring operate with new imports | 4 | No new lint/type/import errors; integration workflows execute without custom `PYTHONPATH` hacks | Risk: environment-dependent IDE autocomplete validation is partially manual; assumption: runtime and test evidence is authoritative, with IDE behavior validated via package structure correctness |

## Notes
- Tasks are sequential, independently executable once dependencies are met, and sized for single-agent runs.
- Ticket is not destructive API and does not include randomness-selection behavior; no specialized destructive/randomness freeze tasks required.
- Key ambiguity handled via checkpoint: revision baseline was missing, so this update initializes workflow-state revisioning at `1`.

## Specification

### Requirement R1 — Entry Point Import Contract

#### 1. Spec Summary
- **Description:** Each Python entry point in scope (`generator.py`, `player_generator.py`, `level_generator.py`) shall import project modules using canonical absolute imports rooted at `src` and shall not mutate `sys.path` at runtime for module resolution.
- **Constraints:**
  - `sys.path.insert`, `sys.path.append`, and equivalent path-mutation patterns for import resolution are prohibited in scoped entry points.
  - `try/except ImportError` or `try/except ModuleNotFoundError` fallback imports are prohibited in scoped entry points.
  - Absolute imports must resolve from package root using `from src...` or `import src...`.
- **Assumptions:** Entry points are executed from contexts where package resolution of `src` is expected to be valid under the repository’s supported run/test workflows.
- **Scope:** `asset_generation/python/` entry points named in ticket acceptance criteria.

#### 2. Acceptance Criteria
- AC-R1.1: The three scoped entry points contain no `sys.path` mutation statements used for import resolution.
- AC-R1.2: The three scoped entry points contain no fallback import blocks guarded by `ImportError` or `ModuleNotFoundError`.
- AC-R1.3: All project-internal imports in the three scoped entry points are absolute imports rooted at `src`.
- AC-R1.4: Importing each entry point module in a clean Python process succeeds without requiring entry-point-local path mutation logic.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Hidden side effects during module import could make importability checks flaky if entry points execute runtime logic at import time.
- **Risk:** Existing ad hoc local execution workflows may have relied on path hacks and can fail after migration if environment bootstrapping is inconsistent.
- **Edge Case:** Mixed import style where one entry point is migrated but transitive imports still rely on fallback patterns.
- **Impact:** Test design must isolate importability behavior from runtime side effects and verify no reintroduction of path mutation patterns.

#### 4. Clarifying Questions
- None. Conservative assumption logged via checkpoint protocol; proceed without human interaction.

### Requirement R2 — Internal Module Import Standardization

#### 1. Spec Summary
- **Description:** Internal modules under `asset_generation/python/src` shall use consistent absolute imports for project-internal dependencies and shall not use relative imports that traverse package boundaries as a compatibility mechanism.
- **Constraints:**
  - Canonical project-internal form: `from src.<package>.<module> import <symbol>` or `import src.<package>.<module>`.
  - Relative imports that represent internal package traversal (`from ..`, `from .`) are out of contract for migrated modules in scope.
  - Fallback dual-style import logic is prohibited.
- **Assumptions:** `asset_generation/python/src` is the authoritative source root for internal package imports.
- **Scope:** Python modules under `asset_generation/python/src/**` touched by the migration and any transitive import chain required for scoped entry points/backend integrations.

#### 2. Acceptance Criteria
- AC-R2.1: No migrated internal module in scope uses fallback imports (`try/except ImportError` or `ModuleNotFoundError`) for internal dependencies.
- AC-R2.2: Migrated internal modules in scope use only canonical absolute internal imports rooted at `src`.
- AC-R2.3: Import dependency graph for scoped modules is internally consistent (no mixed old/new import contracts within the same chain).
- AC-R2.4: A full test run in the existing Python test harness succeeds with standardized import paths.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Circular dependencies can be exposed when moving to absolute imports if previous relative/fallback patterns masked ordering issues.
- **Risk:** Broad mechanical replacement may miss dynamically imported modules, leaving latent regressions.
- **Edge Case:** Modules intended for dual execution contexts (script vs package) may previously have used fallback imports as a workaround.
- **Impact:** Tests must validate runtime import behavior across representative module-loading paths, not only static text patterns.

#### 4. Clarifying Questions
- None. Conservative assumption logged via checkpoint protocol; proceed without human interaction.

### Requirement R3 — Package API Re-Export Contract

#### 1. Spec Summary
- **Description:** Package `__init__.py` files in scope shall expose stable public APIs through explicit re-exports so callers can import sanctioned interfaces without depending on deep internal module paths.
- **Constraints:**
  - Re-exports must be explicit and deterministic; implicit wildcard export behavior is out of contract.
  - Public API boundaries must include interfaces called out in ticket acceptance criteria (`schema`, `service`, `material_system`, and similar package-facing surfaces in scope).
  - Re-export structure must avoid introducing import cycles.
- **Assumptions:** Existing consumers (including backend router integration points) expect stable package-level import surfaces for key components.
- **Scope:** `__init__.py` files under `asset_generation/python/src/**` that define or should define package public API surfaces used by scoped entry points/tests/backend integration points.

#### 2. Acceptance Criteria
- AC-R3.1: Scoped package `__init__.py` files explicitly re-export defined public symbols/interfaces required by consumers.
- AC-R3.2: Consumers in scope can import required APIs via package-level imports without deep-module fallback paths.
- AC-R3.3: Re-export changes do not introduce import-time circular dependency failures in scoped runtime/test flows.
- AC-R3.4: Public API exposure is consistent across packages in scope (no partial re-export states for required interfaces).

#### 3. Risk & Ambiguity Analysis
- **Risk:** Over-reexporting can create brittle coupling and hidden cycles.
- **Risk:** Under-reexporting can break existing callers expecting package-level imports.
- **Edge Case:** Symbol naming collisions across re-exported modules.
- **Impact:** Test coverage should include positive package-level importability and negative regressions for missing/partial exports.

#### 4. Clarifying Questions
- None. Conservative assumption logged via checkpoint protocol; proceed without human interaction.

### Requirement R4 — Backend Router and Integration Import Compatibility

#### 1. Spec Summary
- **Description:** Backend integration points under `asset_generation/web/backend/routers` that interact with asset-generation Python modules shall remain operational under standardized absolute imports and package re-export contracts.
- **Constraints:**
  - Backend integration code in scope shall not depend on entry-point-local path hacks for successful module loading.
  - Integration behavior must be compatible with canonical `src`-rooted imports and package-level exports defined in R3.
- **Assumptions:** Backend router workflows in scope are part of supported integration paths for this milestone.
- **Scope:** Router and adapter usage paths referenced by this ticket’s execution plan, plus direct import touchpoints into asset-generation modules.

#### 2. Acceptance Criteria
- AC-R4.1: Integration paths from scoped backend routers to Python asset-generation modules resolve imports successfully without runtime path mutation hacks.
- AC-R4.2: Existing backend-triggered generator workflows in scope execute without `ImportError`/`ModuleNotFoundError` caused by migration.
- AC-R4.3: No backend integration file in scope introduces fallback import patterns to compensate for migration.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Router-side execution environment may differ from test harness, revealing path-resolution regressions only in integration runs.
- **Edge Case:** Partial migration where backend imports package-level API that has not yet been re-exported.
- **Impact:** Integration-stage verification must exercise real backend invocation paths, not only module-level static checks.

#### 4. Clarifying Questions
- None. Conservative assumption logged via checkpoint protocol; proceed without human interaction.

### Requirement R5 — Quality, Tooling, and IDE Support Outcomes

#### 1. Spec Summary
- **Description:** Import standardization shall improve maintainability and tooling behavior by making package boundaries explicit and removing non-standard import workarounds.
- **Constraints:**
  - Runtime correctness and test pass criteria are authoritative gates.
  - IDE autocomplete criterion is satisfied by deterministic package structure and import graph consistency, not by editor-specific manual UI validation within this ticket.
- **Assumptions:** If import graph is canonical and package exports are stable, modern Python language servers can provide autocomplete behavior.
- **Scope:** Cross-cutting non-functional outcomes for scoped Python modules and package surfaces.

#### 2. Acceptance Criteria
- AC-R5.1: All tests in the relevant Python test suite pass after migration.
- AC-R5.2: No prohibited import anti-patterns remain in scope (`sys.path` mutation, fallback import blocks).
- AC-R5.3: Package structure and exports in scope are sufficient for static symbol discovery by standard Python IDE tooling.
- AC-R5.4: Documentation-independent evidence (runtime/test/static import checks) supports migration success.

#### 3. Risk & Ambiguity Analysis
- **Risk:** IDE autocomplete can vary across environments and cannot be perfectly proven in CI-only execution.
- **Edge Case:** Dynamic attribute exposure (`__getattr__`) may impact symbol discoverability even with standardized imports.
- **Impact:** Test Designer should encode behavior-first checks for importability/export surfaces and avoid prose-only assertions.

#### 4. Clarifying Questions
- None. Conservative assumption logged via checkpoint protocol; proceed without human interaction.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_GENERALIST

## Revision
4

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: Failing until import standardization implementation; adversarial suite in `asset_generation/python/tests/ci/test_import_standardization_behavior.py` (AST contract for entrypoints + `routers/`, subprocess isolation with `ensure_blender_stubs`, backend registry import seam, concurrency/reload stress, package `__all__` / no-star-export, CHECKPOINT re-exports)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Implementation Generalist Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/ready/01_import_standardization.md",
  "target_stage": "IMPLEMENTATION_GENERALIST",
  "scope": {
    "entrypoints": ["asset_generation/python/src/generator.py", "asset_generation/python/src/player_generator.py", "asset_generation/python/src/level_generator.py"],
    "python_src": "asset_generation/python/src",
    "backend_routers": "asset_generation/web/backend/routers"
  }
}
```

## Status
Proceed

## Reason
Test Breaker extended the import-contract suite (adversarial + checkpoint resolutions); Stage advances to implementation so code can satisfy R1–R5 and turn the suite green.
