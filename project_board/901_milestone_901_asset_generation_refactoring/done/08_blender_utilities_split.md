# Blender Utilities Split

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Split the jumbled `core/blender_utils.py` (628 LOC) into 3 focused modules organized by responsibility: primitives (sphere, cylinder, cone, box), creature parts (eye, mouth, tail), and mesh operations (smoothing, weight painting, normals). Improve code discoverability and clarity.

## Acceptance Criteria

- [ ] `primitives.py` (new): Primitive creators (create_sphere, create_cylinder, create_cone, create_box)
- [ ] `creature_parts.py` (new): Creature-specific builders (create_eye_mesh, create_mouth_mesh, create_tail_mesh, create_pupil_mesh)
- [ ] `mesh_ops.py` (new): Mesh transformations (apply_smooth_shading, set_vertex_weight_painted_group, detect_body_scale_from_mesh, etc.)
- [ ] `blender_utils.py` (refactored): Lightweight re-export module for backward compatibility
- [ ] All imports updated; no dangling references
- [ ] All tests pass with new structure
- [ ] Type hints improved: no Variant types, explicit return types

## Dependencies

- Import standardization (ticket #1): Ensures clean imports

## Execution Plan

# Project: Blender Utilities Split
**Description:** Split `asset_generation/python/src/core/blender_utils.py` into focused primitives, creature-parts, and mesh-operations modules while preserving runtime behavior and backward compatibility via re-exports.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Freeze scope and API inventory for split candidates | Spec Agent | Ticket AC, current `blender_utils.py` exports, existing consumers | Requirement-by-requirement specification mapping each existing public/helper function to `primitives.py`, `creature_parts.py`, `mesh_ops.py`, or retained compatibility export | None | Every moved symbol has a declared destination and ownership; no unclassified callable remains | Assumes current module boundaries are stable enough for one-pass split; risk of hidden side-effect helpers requiring co-location |
| 2 | Define compatibility and import contract | Spec Agent | Task 1 inventory, existing import graph | Explicit compatibility contract for `blender_utils.py` re-exports (what must remain importable, deprecation posture, and when direct-module imports are required) | 1 | Spec declares zero-breaking-change import behavior for existing call sites | Risk that wildcard imports or dynamic attribute access exist and are not obvious from static scans |
| 3 | Author behavioral contract tests for module split | Test Designer Agent | Tasks 1-2 specification, AC list | New/updated tests that assert callable availability, behavior parity of representative geometry/mesh ops, and import-path continuity | 1, 2 | Tests fail red against pre-implementation state when new module layout is missing or contract violated | Assumes Blender-context seams can be validated through existing test harness/mocks without nondeterministic failures |
| 4 | Add adversarial and regression-hardening tests | Test Breaker Agent | Task 3 tests and spec | Additional tests for dangling import regressions, mis-routed function allocation, and fail-closed behavior when consumer imports stale paths | 3 | Test suite catches likely false-green scenarios (re-export omissions, signature drift, implicit Any/type regressions) | Risk of overfitting tests to implementation details instead of observable behavior |
| 5 | Implement 3-module extraction and compatibility layer | Implementation Generalist Agent | Tasks 1-4 artifacts | New `primitives.py`, `creature_parts.py`, `mesh_ops.py`; refactored lightweight `blender_utils.py`; updated consumer imports and typing | 4 | All AC items implemented; no dangling references; explicit return types added on touched APIs; backward-compatible imports preserved | Risk of Blender API context assumptions breaking during function relocation; maintain import cycle safety |
| 6 | Run static/test validation and handoff evidence | Static QA Agent | Implementation diff, required test suites | Validation record with targeted pytest results, lint/type status for touched files, and any required diff-cover evidence for Python changes | 5 | Required suites pass and evidence is attached in ticket Validation Status | Assumes environment has required local tooling; if missing, must be documented with exact command/output |
| 7 | Gate acceptance criteria and close integration handoff | Acceptance Criteria Gatekeeper Agent | Ticket AC, validation evidence, implementation diff summary | AC-by-AC evidence map, remaining gaps (if any), and routing to next stage | 6 | Each AC is explicitly mapped to concrete evidence or escalated as blocker | Risk of ambiguous "no behavior change" claims without objective parity evidence |

## Notes
- Tasks are sequential and independently executable once dependencies are met.
- This is a refactor ticket (`generic` spec type); no destructive API or randomness selection policy freeze is required.
- Conservative assumption: dependency "Import standardization (ticket #1)" is satisfied because ticket `01_import_standardization` is completed under milestone `done/`.

---

## Specification (Frozen)

### Requirement R1: API Inventory Freeze and Module Ownership

#### 1. Spec Summary
- **Description:** Every callable currently defined in `asset_generation/python/src/core/blender_utils.py` is classified into one destination: `primitives.py`, `creature_parts.py`, `mesh_ops.py`, or retained in `blender_utils.py` as a compatibility re-export surface only.
- **Constraints:** No public callable is dropped, renamed, or behaviorally redefined in this ticket. Symbol ownership must be one-to-one (single canonical implementation file per callable).
- **Assumptions:** "Public callable" means any top-level function importable from `core.blender_utils`; private constants may move with their owning function group.
- **Scope:** `asset_generation/python/src/core/` module split and importers that reference `core.blender_utils`.

#### 2. Acceptance Criteria
- AC-R1.1: `primitives.py` owns primitive constructors: `create_sphere`, `create_cylinder`, `create_cone`, `create_box`.
- AC-R1.2: `creature_parts.py` owns creature-geometry builders: `create_eye_mesh`, `create_pupil_mesh`, `create_mouth_mesh`, `create_tail_mesh`, and shape constants used exclusively by these builders.
- AC-R1.3: `mesh_ops.py` owns mesh/scene operations and helpers: `clear_scene`, `detect_body_scale_from_mesh`, `apply_smooth_shading`, `join_objects`, `random_variance`, `bind_mesh_to_armature`, `bind_mesh_manually`, `ensure_mesh_integrity`, `fix_body_part_bindings`, `identify_vertex_body_part`.
- AC-R1.4: `blender_utils.py` remains importable and provides these callables via re-export, without becoming the canonical implementation location.
- AC-R1.5: No callable from the pre-split inventory is left unclassified or duplicated across canonical modules.

#### 3. Risk & Ambiguity Analysis
- Hidden coupling risk: creature-part builders call primitive builders; moving modules can introduce import cycles if ownership boundaries are unclear.
- Mixed-responsibility helper risk: `clear_scene` is scene-level, not mesh-level, but is grouped into `mesh_ops.py` as the least-privilege "operations" bucket.
- Inventory drift risk: if untracked helpers are added during implementation, they can bypass ownership rules unless inventory is revalidated.

#### 4. Clarifying Questions
- None. Conservative assumption applied: callable inventory is exactly the current top-level function set in `core.blender_utils`.

### Requirement R2: Compatibility Re-Export Contract

#### 1. Spec Summary
- **Description:** `blender_utils.py` becomes a lightweight compatibility layer that preserves existing import paths while forwarding symbols from split modules.
- **Constraints:** Existing call sites importing from `core.blender_utils` must remain functional without mandatory source migration in this ticket.
- **Assumptions:** This ticket is non-breaking and does not introduce deprecation warnings unless already established elsewhere.
- **Scope:** Import behavior for `core.blender_utils` and direct imports to new modules.

#### 2. Acceptance Criteria
- AC-R2.1: `from core.blender_utils import <existing_symbol>` succeeds for all inventory symbols listed in R1.
- AC-R2.2: Re-exported symbols preserve callable signatures and return semantics relative to pre-split behavior.
- AC-R2.3: `blender_utils.py` contains no duplicate business logic beyond import/re-export scaffolding and minimal compatibility metadata.
- AC-R2.4: Direct imports from new modules (`core.primitives`, `core.creature_parts`, `core.mesh_ops`) are valid and resolve canonical implementations.
- AC-R2.5: No wildcard-only contract is introduced; explicit symbol exports are deterministic (for example, via explicit imports and/or `__all__`).

#### 3. Risk & Ambiguity Analysis
- Dynamic import patterns (`getattr`, wildcard consumers) may depend on implicit names not intended as public API.
- Signature drift can occur silently if wrappers are added with mismatched defaults or keyword-only constraints.

#### 4. Clarifying Questions
- None. Conservative assumption applied: explicit import compatibility takes precedence over wildcard/reflective usage.

### Requirement R3: Behavioral Parity Boundaries

#### 1. Spec Summary
- **Description:** The split is structural; geometry generation, mesh transformations, and fallback behavior remain unchanged at observable runtime boundaries.
- **Constraints:** No intentional visual/functional tuning is permitted in this ticket. Existing shape fallbacks and default-return behavior stay stable.
- **Assumptions:** Blender operator side effects are part of observable behavior for this refactor.
- **Scope:** Runtime behavior of moved callables, including default branches and fallback paths.

#### 2. Acceptance Criteria
- AC-R3.1: Primitive constructors still return the active Blender object and preserve parameter semantics (`location`, `scale`, and shape-specific parameters).
- AC-R3.2: Creature-part shape dispatch preserves fallback behavior for unknown shapes (eye -> circle sphere, pupil -> dot sphere, mouth -> smile cylinder, tail -> curled sphere).
- AC-R3.3: `detect_body_scale_from_mesh` preserves fallback `1.0` for missing/empty mesh data and maintains lower-bound clamping behavior.
- AC-R3.4: Mesh-binding and integrity helpers preserve fail-safe flow: auto-bind attempt then manual fallback, followed by integrity correction behavior where invoked.
- AC-R3.5: Randomized helper behavior (`random_variance`) keeps the same value-distribution formula contract for identical `base_value`, `factor`, and `rng`.

#### 3. Risk & Ambiguity Analysis
- Blender context dependencies can make regressions appear as environment issues instead of behavior drift.
- Refactor-only tickets can still alter behavior accidentally through import-time ordering changes or constant movement.

#### 4. Clarifying Questions
- None.

### Requirement R4: Type-Hint and Interface Hardening

#### 1. Spec Summary
- **Description:** Split modules must improve explicit typing on touched interfaces and avoid ambiguous Variant-style or implicit dynamic typing where concrete types are practical.
- **Constraints:** Type hints must not require runtime behavior changes; annotations should remain compatible with Blender Python runtime realities.
- **Assumptions:** Project standard "no Variant types" means explicit Python type annotations are preferred over untyped/dynamic placeholders.
- **Scope:** New split modules and compatibility layer signatures touched by this ticket.

#### 2. Acceptance Criteria
- AC-R4.1: All moved top-level callables define explicit parameter and return annotations unless Blender runtime constraints make exact annotation impractical.
- AC-R4.2: Shape selector parameters are explicitly typed as `str`; coordinate/scale tuples are typed consistently at module boundaries.
- AC-R4.3: Functions with deterministic scalar returns (for example, `detect_body_scale_from_mesh`, `random_variance`) declare explicit `float` return types.
- AC-R4.4: No newly introduced `Any`/Variant-like placeholders are added in split modules without a documented constraint rationale.
- AC-R4.5: Compatibility re-exports do not erase or weaken canonical annotations.

#### 3. Risk & Ambiguity Analysis
- Overly strict Blender object typing may reduce portability between real Blender and test doubles.
- Annotation inconsistency across re-export/canonical definitions can create static-analysis confusion even when runtime behavior is correct.

#### 4. Clarifying Questions
- None. Conservative assumption applied: prefer precise annotations with tolerant object typing where Blender classes are environment-specific.

### Requirement R5: Import Graph Integrity and Non-Functional Constraints

#### 1. Spec Summary
- **Description:** The split must reduce discoverability debt without introducing dangling imports, circular dependencies, or module-load failures for existing consumers.
- **Constraints:** Refactor must be internal to module structure; no unrelated subsystem changes are in scope.
- **Assumptions:** Existing tests are the minimum regression net and will be expanded by downstream agents to cover split contracts.
- **Scope:** `asset_generation/python/src/core/` import graph and all direct consumers importing moved symbols.

#### 2. Acceptance Criteria
- AC-R5.1: All references to moved symbols resolve successfully after module split; no dangling imports remain.
- AC-R5.2: New module graph is acyclic for canonical split modules (`primitives`, `creature_parts`, `mesh_ops`) and compatibility layer.
- AC-R5.3: Importing `core.blender_utils` in a consumer path still succeeds and yields expected callables.
- AC-R5.4: Refactor does not introduce unrelated behavior changes outside blender utility organization and typing hardening.
- AC-R5.5: Test and static validation stages have sufficient contract surface to detect missing re-exports, mis-routed symbols, and signature regressions.

#### 3. Risk & Ambiguity Analysis
- Circular imports can emerge if `creature_parts.py` and `mesh_ops.py` depend on each other through compatibility paths.
- Missing one import-site update can fail only at runtime in rarely exercised generation branches.

#### 4. Clarifying Questions
- None.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

COMPLETE

## Revision

8

## Last Updated By

Autopilot Orchestrator

## Validation Status

- Tests (regression suites): `uv run pytest tests/enemies/test_eye_shape_pupil_geometry.py tests/enemies/test_eye_shape_pupil_geometry_adversarial.py tests/enemies/test_mouth_tail_geometry_adversarial_extended.py -q` => `110 passed in 0.59s` (executed from `asset_generation/python`).
- Tests (split contract): `uv run pytest tests/core/test_m901_08_blender_utilities_split_contract.py -q` => `50 passed in 0.05s`.
- Preflight: `bash ci/scripts/diff_cover_preflight.sh` (from repo root) => `PASS`, diff coverage `95%` (threshold `85%` vs `origin/main`).
- Compatibility evidence: `src/core/blender_utils.py` now exposes compatibility wrappers for creature-part builders and re-exports creature-part constants required by downstream tests/contracts.
- Static QA: `ReadLints` on touched files (`src/core/blender_utils.py`, `tests/core/test_m901_08_blender_utilities_split_contract.py`) => no linter errors found.
- AC coverage check (gatekeeper): split ownership modules exist (`src/core/primitives.py`, `src/core/creature_parts.py`, `src/core/mesh_ops.py`), compatibility re-export surface remains in `src/core/blender_utils.py`, and moved callables show explicit typed signatures with deterministic `__all__` exports.
- Remaining closure condition: ticket is not yet in milestone `done/` location required by workflow for `Stage: COMPLETE`.

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
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/done/08_blender_utilities_split.md",
  "focus": "Optional push/merge preparation.",
  "requirements": [
    "All AC evidence remains recorded in Validation Status.",
    "Optional: push branch after reviewing in-flight workspace changes."
  ]
}
```

## Status

Proceed

## Reason

All listed acceptance criteria have concrete implementation/test evidence and the ticket is now under milestone `done/`, satisfying completion policy.
