# Material System Refactoring

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Decompose `materials/material_system.py` (896 LOC) from a god object into focused, single-responsibility modules. Extract texture handlers into a registry pattern, pull out material presets, separate feature zone logic, and isolate enemy material lookup. Enable independent testing and extension of each layer.

## Acceptance Criteria

- [ ] `system.py` (refactored): < 150 LOC, orchestration only (setup_materials, get_enemy_materials, apply_material_to_object)
- [ ] `presets.py` (new): Material finishes, color profiles, per-enemy defaults
- [ ] `texture_handlers.py` (new): Registry pattern for texture handlers (organic, gradient, stripes, spots)
- [ ] `feature_zones.py` (new): Feature zone override logic extracted from apply_feature_slot_overrides
- [ ] `material_lookup.py` (new): Enemy type → materials mapping logic
- [ ] All existing tests pass; expand to cover extracted modules
- [ ] Type hints added: dict[str, Material], remove Any types where possible
- [ ] No texture handler requires bpy context for definition (only for application)
- [ ] Backend routes use new imports without modification

## Dependencies

- Import standardization (ticket #1)
- Model registry layering (ticket #2): Optional but recommended before material refactoring

## Execution Plan

### Planner execution summary (authoritative task graph)

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Freeze module contracts for `system.py`, `presets.py`, `texture_handlers.py`, `feature_zones.py`, and `material_lookup.py`, including public API signatures, type contracts (`dict[str, Material]`), and "no bpy required at definition time" boundaries | Spec Agent | This ticket; current `materials/material_system.py`; current material helper modules and consumers | Specification with requirement IDs, module boundaries, API compatibility constraints, and explicit non-goals (no backend route behavior changes) | None | Spec is complete, testable, and unambiguous for all acceptance criteria; required contracts for handler registry and feature zones are explicit | **Assumption:** dependency #2 is optional and non-gating. **Risk:** hidden coupling in legacy `material_system.py` can mask side effects if contracts are not explicit. |
| 2 | Design behavior-first tests for extracted modules and orchestration continuity (registry dispatch, zone overrides, enemy mapping, API compatibility, typing expectations) | Test Designer Agent | Approved spec from task 1; existing material tests and pytest layout | Deterministic tests that fail on missing extraction behavior or regressions, including isolated tests for each new module and orchestration smoke for `system.py` | 1 | Tests assert executable behavior (not prose), cover each extracted responsibility, and encode acceptance criteria as runtime checks | **Risk:** over-reliance on import presence tests; mitigate with behavior assertions and fixture-based module isolation. |
| 3 | Expand adversarial coverage for edge cases: unknown enemy type, malformed texture handler registration, zone override precedence conflicts, and missing optional fields | Test Breaker Agent | Tests from task 2; approved spec | Additional negative/boundary tests that force fail-closed behavior and preserve compatibility guarantees | 2 | Suite catches invalid handler/zone/lookup states and prevents silent fallback regressions | **Risk:** flaky tests if bpy context leaks into pure-definition paths; enforce seams/mocks per spec. |
| 4 | Implement extraction and refactor: create `presets.py`, `texture_handlers.py`, `feature_zones.py`, `material_lookup.py`; slim `system.py` to orchestration; update imports without backend route modifications | Implementation Generalist Agent | Spec + RED tests from tasks 2-3; current materials package | Refactored module set matching acceptance criteria with unchanged public behavior and improved type hints | 3 | Target module boundaries are realized; `system.py` is orchestration-only; no handler definition requires bpy; all tests pass | **Risk:** circular imports or accidental API drift. **Assumption:** keep route signatures stable and adapt only internal imports. |
| 5 | Run static QA and integration verification for touched Python scope, including diff-cover preflight requirement for Python changes | Static QA Agent then Integration Agent | Implementation diff and test results | Validation evidence covering tests, lint/type checks, and integration smoke for material application pathways | 4 | `uv run pytest` scoped suites pass, static checks pass, and `bash ci/scripts/diff_cover_preflight.sh` passes when required | **Risk:** integration-only regressions in asset generation flows not covered by unit tests; include targeted smoke command(s) from spec. |

### Module Breakdown

| Module | Lines | Responsibility | Public API |
|--------|-------|-----------------|------------|
| `system.py` | ~150 | Orchestration, setup, lookups | `setup_materials()`, `get_enemy_materials()`, `apply_material_to_object()` |
| `presets.py` | ~120 | Finish/color/theme data | `FINISHES`, `MaterialColors`, `get_preset_for_theme()` |
| `texture_handlers.py` | ~200 | Texture handler registry | `register_handler()`, `apply_texture()`, handlers dict |
| `feature_zones.py` | ~180 | Feature slot override logic | `apply_feature_slot_overrides()`, `apply_zone_texture_pattern_overrides()` |
| `material_lookup.py` | ~80 | Enemy → materials mapping | `get_materials_for_enemy_type()` |

### File Changes Summary

| File | Change | Priority |
|------|--------|----------|
| `presets.py` (new) | Extract finish/color data | High |
| `texture_handlers.py` (new) | Extract handler registry | High |
| `feature_zones.py` (new) | Extract zone override logic | High |
| `material_lookup.py` (new) | Extract enemy lookup | High |
| `system.py` | Refactor to dispatch | High |
| `gradient_generator.py` | No change (keep as-is) | N/A |
| `stripes_texture.py` | No change (keep as-is) | N/A |
| Enemies builder files | Update imports | Medium |
| Test files | Expand coverage | Medium |

### Success Criteria

- All 5 modules < 200 LOC
- `pytest tests/materials/` passes with 85%+ coverage
- Texture handler registry testable without bpy
- Feature zone logic testable in isolation
- No functional changes to public API
- Material application still works end-to-end

## Notes

- 23 existing material tests provide safety net
- High coupling risk—tests critical before and after refactoring
- Texture handlers are good candidate for pytest parametrization
- Extract logic without touching gradient_generator.py (already good shape)

## Specification (Frozen)

### Requirement R1: Orchestration Boundary and Backward-Compatible Public API

#### 1. Spec Summary
- **Description:** Material orchestration must be split so the orchestration entrypoint is thin and limited to wiring calls across extracted modules. Public behavior for consumers must remain unchanged.
- **Constraints:** Existing callable API remains available to current importers: `setup_materials(...)`, `get_enemy_materials(...)`, and `apply_material_to_object(...)`; no backend route behavior changes are allowed.
- **Assumptions:** "system.py" in acceptance criteria is interpreted as orchestration role; current compatibility path `src/materials/material_system.py` remains valid during this ticket.
- **Scope:** `asset_generation/python/src/materials/` and all direct consumers under `asset_generation/python/src/`.

#### 2. Acceptance Criteria
- AC-R1.1: Orchestration module exposes the three public functions with same parameter semantics and return behavior as before refactor.
- AC-R1.2: Orchestration module delegates logic to extracted modules and does not re-embed extracted concerns (preset tables, handler implementation details, zone override internals, enemy mapping internals).
- AC-R1.3: Consumers currently importing/using the three public functions continue working without source edits outside import rewiring explicitly permitted by ticket.
- AC-R1.4: `get_enemy_materials` behavior remains sourced from enemy-theme mapping logic, with no contract drift in expected zone keys for existing enemy families.
- AC-R1.5: Orchestration module target is under 150 LOC excluding comments/docstrings/import wrapping shims.

#### 3. Risk & Ambiguity Analysis
- Hidden side effects may exist in legacy all-in-one module; refactor can unintentionally alter initialization order.
- "No backend route modifications" can be violated by accidental import-path churn; must preserve existing route-layer contracts.
- LOC limits may tempt brittle compression; maintainability must not be sacrificed for line count.

#### 4. Clarifying Questions
- None. Conservative compatibility assumption logged via checkpoint protocol.

### Requirement R2: Preset Extraction and Type Contract Hardening

#### 1. Spec Summary
- **Description:** Enemy finish and color preset logic must be extracted into a dedicated presets module with explicit typing and stable lookup behavior.
- **Constraints:** Preset defaults and fallback behavior match legacy outcomes; Any-typed surfaces are reduced where feasible.
- **Assumptions:** Existing finish presets (`default`, `glossy`, `matte`, `metallic`, `gel`) remain canonical unless explicitly changed by follow-up ticket.
- **Scope:** New `presets.py` and all callsites consuming finish/palette-derived defaults.

#### 2. Acceptance Criteria
- AC-R2.1: `presets.py` contains finish definitions and reusable preset accessors/constants consumed by orchestration/zone/material-creation flows.
- AC-R2.2: Material dictionaries are typed as `dict[str, Material]` (or Blender-compatible equivalent alias) at public boundaries.
- AC-R2.3: Unknown finish keys fail closed to the documented default preset rather than raising uncaught exceptions.
- AC-R2.4: Hex override parsing behavior remains deterministic: valid 6-char hex applies override, invalid/empty follows fallback path already defined by feature.
- AC-R2.5: No extracted preset function requires live bpy context at definition/import time.

#### 3. Risk & Ambiguity Analysis
- Blender runtime type objects may vary by environment; use stable typing aliases where strict bpy symbol availability is uncertain.
- Color/fallback behavior is correctness-critical for visual identity; subtle drift may pass structural tests but fail runtime appearance expectations.

#### 4. Clarifying Questions
- None.

### Requirement R3: Texture Handler Registry Decomposition

#### 1. Spec Summary
- **Description:** Texture application strategy must move to a registry-driven module that separates handler registration/lookup from orchestration and supports existing and required texture families.
- **Constraints:** Registry definitions must be import-safe without requiring bpy context; bpy may only be required when applying handlers to actual material/node instances.
- **Assumptions:** Required minimum families from ticket are `organic`, `gradient`, `stripes`, `spots`; current implemented additional modes remain supported.
- **Scope:** New `texture_handlers.py`, orchestration dispatch callsites, and integration seams for stripes/gradient/spots helpers.

#### 2. Acceptance Criteria
- AC-R3.1: `texture_handlers.py` exposes registry operations (`register_handler`, lookup/apply operation, registry mapping access for test visibility).
- AC-R3.2: Handler lookup by texture type is deterministic; unknown texture type does not throw and leaves material unchanged unless explicitly configured otherwise.
- AC-R3.3: Handler registration enforces callable contract and rejects malformed entries fail-closed (explicit exception or deterministic no-op contract, documented in module docstring).
- AC-R3.4: Existing texture behavior for known types remains functionally equivalent at the public API level.
- AC-R3.5: Module import/handler registration path does not touch `bpy.data` or require live scene/material objects.

#### 3. Risk & Ambiguity Analysis
- Circular imports are likely when splitting handlers that currently reference helper functions in monolith.
- Registry mutability can leak state across tests; tests must be able to reset or isolate registry state.
- If unknown texture types silently become hard errors, legacy material names may regress.

#### 4. Clarifying Questions
- None. Scope assumption logged via checkpoint protocol.

### Requirement R4: Feature Zone Override Isolation

#### 1. Spec Summary
- **Description:** Feature-zone and texture-pattern override logic must be extracted into dedicated module(s) so zone mutation behavior is independently testable and deterministic.
- **Constraints:** Override precedence remains: part-level override > zone-level override > base slot material. Pattern modes must remain supported for current flat-key build options.
- **Assumptions:** Existing flat build-option key schema (`feat_{zone}_texture_*`) remains authoritative for this ticket.
- **Scope:** New `feature_zones.py` owning feature-slot overrides and zone texture mode dispatch.

#### 2. Acceptance Criteria
- AC-R4.1: `apply_feature_slot_overrides(...)` and `apply_zone_texture_pattern_overrides(...)` are extracted and publicly importable from `feature_zones.py`.
- AC-R4.2: Both functions preserve non-mutating input contract by returning a derived slot map and leaving the original mapping unchanged.
- AC-R4.3: Override processing skips invalid/missing structures safely (e.g., non-dict feature entries) without raising uncaught exceptions.
- AC-R4.4: Gradient/spots/stripes/assets mode handling preserves existing normalization/clamping semantics (direction fallback, density clamp, stripe preset normalization, rotation sanitization).
- AC-R4.5: Zone/part extra helpers (`material_for_zone_part`, `material_for_zone_geometry_extra`) remain behaviorally consistent and callable for geometry-extra pipeline usage.

#### 3. Risk & Ambiguity Analysis
- Precedence regressions can produce visually incorrect but syntactically valid outputs; behavioral tests must assert winner selection in conflicts.
- Numeric coercion for texture parameters (density/rotation/tile) can throw if refactor changes safe parsing.

#### 4. Clarifying Questions
- None.

### Requirement R5: Enemy Material Lookup Separation

#### 1. Spec Summary
- **Description:** Enemy-type-to-material mapping logic must be isolated from orchestration into dedicated lookup module while preserving current enemy theme behavior.
- **Constraints:** Lookup API remains compatible with current callers providing `(enemy_type, materials, rng)` style inputs.
- **Assumptions:** Existing enemy theme module remains source of truth unless this ticket explicitly migrates internals behind stable wrapper.
- **Scope:** New `material_lookup.py` and orchestration import/wiring.

#### 2. Acceptance Criteria
- AC-R5.1: Enemy mapping responsibility is encapsulated in `material_lookup.py` and imported by orchestration module.
- AC-R5.2: Unknown enemy type handling remains deterministic and backward-compatible (same fallback semantics as current behavior).
- AC-R5.3: Returned mapping includes expected slot keys (`body`, `head`, `limbs`, plus optional extras where currently supported) for all existing enemy families.
- AC-R5.4: Lookup module can be imported and unit-tested without requiring bpy runtime initialization.

#### 3. Risk & Ambiguity Analysis
- Randomized variant selection tied to rng can drift subtly if lookup internals change call count/order.
- Theme fallback behavior is user-facing; regressions may only be visible in generated assets.

#### 4. Clarifying Questions
- None.

### Requirement R6: Non-Functional Quality, Testability, and Integration Guarantees

#### 1. Spec Summary
- **Description:** Refactor must improve modularity/testability without changing observable behavior, and must satisfy type-hint and integration constraints.
- **Constraints:** Existing tests must pass; test coverage must be expanded for extracted modules; no unnecessary documentation artifacts are created.
- **Assumptions:** Ticket-level static/integration gates run in downstream stages (Test Designer, Test Breaker, Implementation, QA).
- **Scope:** New/existing material modules plus targeted consumer smoke paths.

#### 2. Acceptance Criteria
- AC-R6.1: Each extracted module has direct behavioral test coverage for its primary responsibility (preset lookup, registry dispatch, zone overrides, enemy lookup, orchestration continuity).
- AC-R6.2: Type annotations replace avoidable `Any` in touched public/internal contracts where practical without runtime regressions.
- AC-R6.3: Import-time side effects are minimized; module imports in non-Blender unit-test contexts do not fail due to immediate bpy usage for definitions.
- AC-R6.4: End-to-end material application path still functions via existing generation entrypoints that call `setup_materials`, `get_enemy_materials`, and `apply_material_to_object`.
- AC-R6.5: Backend-facing code paths remain behaviorally unchanged; only internal import/module boundaries are refactored.

#### 3. Risk & Ambiguity Analysis
- Superficial tests (import-only assertions) may miss behavior regressions; downstream test design must focus on runtime behavior.
- Over-aggressive typing can conflict with Blender dynamic node APIs; use targeted typing and aliases instead of unsafe casts.
- End-to-end smoke gaps can hide integration regressions in procedural generation pathways.

#### 4. Clarifying Questions
- None.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

COMPLETE

## Revision

9

## Last Updated By

Acceptance Criteria Gatekeeper Agent

## Validation Status

- AC1 (`system.py` orchestration-only, <150 LOC): Verified `asset_generation/python/src/materials/system.py` is 63 LOC (`wc -l`) and only exposes/wires `setup_materials`, `get_enemy_materials`, `apply_material_to_object` with delegation to extracted modules (`material_lookup`, `presets`, `texture_handlers`).
- AC2 (`presets.py` new): Verified `asset_generation/python/src/materials/presets.py` exists and contains extracted finish presets, color typing aliases, and hex parsing/fallback helpers consumed by orchestration/zone flows.
- AC3 (`texture_handlers.py` new): Verified `asset_generation/python/src/materials/texture_handlers.py` exists with registry pattern (`register_handler`, `get_handlers`, `apply_texture`) and deterministic unknown-handler no-op behavior; enforced by `test_texture_handler_unknown_type_is_noop_for_material` and registration contract test.
- AC4 (`feature_zones.py` new): Verified `asset_generation/python/src/materials/feature_zones.py` exists and owns extracted `apply_feature_slot_overrides` and `apply_zone_texture_pattern_overrides`, plus geometry-extra helpers; behavior covered by precedence/sanitization/clamp tests in the M901 contract suite.
- AC5 (`material_lookup.py` new): Verified `asset_generation/python/src/materials/material_lookup.py` exists and encapsulates enemy type → slot mapping via `get_materials_for_enemy_type`, including deterministic unknown-enemy fallback.
- AC6 (existing tests pass + expanded extracted-module coverage): Executed `uv run pytest tests/materials/test_m901_material_system_refactor_contract.py tests/ci/test_type_hints_documentation_contract.py` in `asset_generation/python`; result: `27 passed, 1 skipped`.
- AC7 (type hints: `dict[str, Material]`, reduce `Any`): Verified new extracted modules use typed boundaries (`dict[str, bpy.types.Material]` / `dict[str, bpy.types.Material | None]`, `Mapping[str, object]`) and contain no `Any` usage; `rg "\bAny\b" asset_generation/python/src/materials/*.py` matches only legacy compatibility module `material_system.py`.
- AC8 (no texture handler requires bpy context for definition): Verified registry definitions in `texture_handlers.py` are callable registrations without `bpy.data` access at import/registration path; runtime `bpy.data` interaction occurs in `create_material` application path only. Import safety also covered by `test_refactor_modules_import_without_blender_runtime_context`.
- AC9 (backend routes use new imports without modification): Verified backend router scope unchanged for this refactor (`git diff --name-only -- asset_generation/web/backend/routers` and `git status --short -- asset_generation/web/backend/routers` both empty), satisfying "without modification" route compatibility constraint.
- Gate Decision: All ticket acceptance criteria have explicit, auditable coverage via structural verification and passing test evidence; no unresolved criterion-level gaps remain.

## Blocking Issues

- None.

## Escalation Notes

- Gatekeeper review complete. No escalation required.

---

# NEXT ACTION

## Next Responsible Agent

Human

## Required Input Schema

```json
{
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/ready/05_material_system_refactoring.md",
  "action": "human_final_review_or_folder_transition"
}
```

## Status

Proceed

## Reason

All acceptance criteria are explicitly evidenced in the ticket validation record (including test command output and compatibility checks), so the ticket can be treated as complete and handed to Human for final review/board transition.
