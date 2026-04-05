# TICKET: base_models_split_by_archetype

Title: Optional — split `base_models.py` by body archetype (Python)

## Description

`asset_generation/python/src/enemies/base_models.py` combines `InsectoidModel`, `BlobModel`, `HumanoidModel`, and `ModelTypeFactory`. This splits **body archetypes**, not individual enemy slugs. Do this if debugging procedural mesh code for one archetype is hard with all three in one file.

## Acceptance Criteria

- One module per archetype (or factory separate from models); behavior unchanged for all callers of `ModelTypeFactory`.
- Generation smoke still succeeds for enemies using each archetype.

## Dependencies

- None

## Specification

Split `base_models` into a package with one module per archetype plus `base_model_type` and `model_type_factory`; preserve stable imports from `src.enemies.base_models` and exact `ModelTypeFactory` semantics (unknown key → insectoid, `get_available_types` order). Verification: pytest under `asset_generation/python/tests/` per `.lefthook/scripts/py-tests.sh`, ruff on touched files, docs updates per spec.

**Full spec:** [`project_board/specs/base_models_split_by_archetype_spec.md`](../../specs/base_models_split_by_archetype_spec.md)

## Execution Plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author functional spec: module map, public import path for `ModelTypeFactory` / `BaseModelType`, relative-import graph, default key behavior for unknown `model_type`, and verification commands (pytest + factory smoke). | Spec Agent | Ticket file; `asset_generation/python/src/enemies/base_models.py`; `workflow_enforcement_v1.md` | Ticket-sized spec section or linked spec artifact referenced from ticket; acceptance criteria traceability | None | Spec is unambiguous for Test Designer and Implementation; no unresolved blocking ambiguity | Layout choice (package vs flat) deferred to spec per checkpoint |
| 2 | Add behavioral tests: `ModelTypeFactory.create_model` for `insectoid`, `blob`, `humanoid` with fixed RNG under mocked `bpy` (reuse `tests/enemies` patterns); assert stable geometry/material wiring invariants. | Test Designer | Spec from task 1 | New/extended tests under `asset_generation/python/tests/` | 1 | Tests fail on current code only if they encode new required behavior; after implementation, tests pass | Factory currently uncalled in prod code; tests become the smoke contract per planning assumption |
| 3 | Adversarial review of tests (missing edges: unknown type → default class, `get_available_types` keys/order if specified). | Test Breaker | Tests from task 2 | Short review notes; optional test gaps filed or patched | 2 | No critical blind spot unaddressed | |
| 4 | Split implementation: move `BaseModelType` and each archetype to dedicated modules; place `ModelTypeFactory` in its own module or colocate per spec; preserve `MODEL_TYPES` and `create_model` / `get_available_types` semantics; update imports; keep documented public import stable; sync `PROJECT_STRUCTURE.md` and `docs/ARCHITECTURE_SUMMARY.md`; remove unused `ModelTypeFactory` import from `animated_enemies.py` if still unused. | Implementation Generalist | Spec; tests | Refactored Python tree; docs updated | 3 | `uv run pytest tests/ -q` (or project `.venv`) passes; no change to factory API for consumers | Circular imports between archetype modules and factory; mitigate via spec import order |
| 5 | Run static checks if present (e.g. ruff) on touched files; fix any new violations. | Static QA Agent | Repo lint config; changed files | Clean lint on touched paths | 4 | No new static violations in scope | |
| 6 | Confirm integration: full `asset_generation/python` pytest suite; note CI alignment with `.lefthook/scripts/py-tests.sh`. | Integration Agent | Green tests from task 4 | Validation status update recommendation or ticket note | 5 | Integration validation documented; regressions none | Blender-headless export not assumed unless spec demands it |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_GENERALIST

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: Passed (`cd asset_generation/python && uv run pytest tests/ -q` — 343 passed, 2026-04-05)
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
  "ticket_path": "project_board/maintenance/in_progress/base_models_split_by_archetype.md",
  "spec_path": "project_board/specs/base_models_split_by_archetype_spec.md",
  "tests_glob": "asset_generation/python/tests/enemies/test_base_models_factory.py"
}
```

## Status
Proceed

## Reason
Adversarial tests extended (unknown keys, case sensitivity, get_available_types immutability, import graph). Implementation Generalist executes package split per spec BMSBA-1–4; checkpoint `project_board/checkpoints/MAINT-BMSBA/run-2026-04-05-test-break.md`.
