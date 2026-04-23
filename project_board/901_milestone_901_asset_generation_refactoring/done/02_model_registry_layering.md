# Model Registry Layering

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Ticket ID:** M901-02  
**Project:** blobert  
**Created By:** Human  
**Created On:** 2026-04-21

---

## Description

Decompose `model_registry/service.py` (684 LOC) from a god object into 4 focused, layered modules. Separate concerns: schema validation, file I/O, version migrations, and business logic. Enable each layer to be tested and modified independently.

---

## Acceptance Criteria

- [ ] `schema.py` (new): Contains all TypedDict definitions, validation constants, and `validate_manifest()` function
- [ ] `store.py` (new): Handles manifest file I/O (load, save); no validation logic
- [ ] `migrations.py` (new): Handles version migration logic and `normalize_*` functions
- [ ] `service.py` (refactored): Business logic layer using schema, store, and migrations; public API unchanged
- [ ] All existing tests pass; test coverage maintained or improved
- [ ] Type hints added: dict → dict[str, T], Pydantic models for API payloads
- [ ] No circular dependencies between modules
- [ ] Backend routes (`routers/registry.py`) work without modification

---

## Dependencies

- **M901-01 — Import standardization** (gating): Must standardize imports first. **Status:** satisfied — `project_board/901_milestone_901_asset_generation_refactoring/done/01_import_standardization.md`

---

# Project: Model Registry Layering

**Description:** Split `asset_generation/python/src/model_registry/service.py` into `schema.py`, `store.py`, `migrations.py`, and a thinner `service.py`, preserving the public Python API and HTTP behavior while improving testability and typing.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author module-boundary spec: TypedDict/schema ownership, store I/O contract, migration hooks, frozen public `service` API, Pydantic placement for FastAPI payloads, and acyclic import graph | Spec Agent | This ticket; `service.py` full contents; `model_registry/__init__.py` re-exports; `asset_generation/web/backend/routers/registry.py` and backend test imports; `agent_context/agents/common_assets/destructive_api_spec_template.md` only if delete/purge semantics need extension | Written spec with explicit layer responsibilities, symbol lists per file, and Pydantic model map for registry HTTP payloads | None | Spec exit gate passes with `--type api` (mutation/registry endpoints); no ambiguity on which module owns validation vs persistence | Risk: tension between “routers unchanged” and new imports — spec must state whether import-only router edits are allowed. Assumption (planning): HTTP behavior unchanged; import lines may adjust to stable package symbols |
| 2 | Design behavior-first tests for schema validation, atomic save/load, migration round-trips, and service orchestration (no prose/ticket assertions) | Test Designer Agent | Approved spec; existing `asset_generation/python/tests/model_registry/` and `asset_generation/python/tests/ci/test_import_standardization_behavior.py` export contract | New or updated tests that fail if layers leak concerns (e.g. validation inside store) or public API regresses | 1 | Tests assert runtime behavior and disk/API effects, per workflow realism guardrails | Risk: tests coupling to private helpers — prefer seams defined in spec |
| 3 | Adversarial test strengthening (partial writes, corrupt JSON, migration edge cases, import cycles) | Test Breaker Agent | Tests from Task 2; spec | Additional negative tests; `# CHECKPOINT` where conservative assumptions encoded | 2 | Suite catches boundary violations and regression of MRVC semantics | Risk: over-mocking filesystem — keep assertions grounded in observable outcomes |
| 4 | Implement extraction: `schema.py`, `store.py`, `migrations.py`, refactor `service.py`, update `__init__.py` re-exports, add Pydantic models per spec | Implementation Generalist Agent | Spec + tests; target under `asset_generation/python/src/model_registry/` and any router/schema files spec names | Layered modules each under 200 LOC (per ticket goal); public API preserved; routers behave per AC | 3 | `pytest` for scoped and full suites green; `bash ci/scripts/diff_cover_preflight.sh` passes when `.py` under `asset_generation/python/` changes | Risk: dual-import patterns (`utils` vs `src.utils`) — align with M901-01 conventions. Assumption: no new `sys.path` hacks |
| 5 | Static QA then Integration | Static QA Agent; Integration Agent | Implementation diff | Lint/type/import checks; backend registry tests and API integration pass | 4 | Validation Status updated; no regressions in `asset_generation/web/backend/tests/test_registry_*.py` | Risk: environment-specific FastAPI paths — integration evidence is authoritative |

## Notes

- Not an umbrella ticket; single refactor with one satisfied gating dependency (M901-01 in `done/`).
- Not a randomness-selection feature; no Selection Policy Freeze task.
- Destructive API: only if spec expands delete/purge contracts — otherwise Spec Agent uses `--type api` and destructive template only as needed for existing router semantics.
- `spec_completeness_check.py` must run before TEST_DESIGN per workflow enforcement.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

STATIC_QA

## Revision

11

## Last Updated By

Implementation Generalist Agent

## Validation Status

- Tests: Passed (`uv run pytest tests/model_registry -q` -> `124 passed`; `uv run pytest tests/ci/test_import_standardization_behavior.py -q` -> `37 passed`; `uv run pytest ../../asset_generation/web/backend/tests/test_registry_*.py -q` -> `73 passed`)
- Static QA: Diff-cover preflight passed (`bash ci/scripts/diff_cover_preflight.sh` -> `PASS`, diff coverage `100%`)
- Integration: Not Run

## Blocking Issues

- None.

## Escalation Notes

- None.

---

# NEXT ACTION

## Next Responsible Agent

Acceptance Criteria Gatekeeper Agent

## Required Input Schema

```json
{
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/done/02_model_registry_layering.md",
  "implementation_summary": [
    "Added model_registry/schema.py (validation constants, TypedDicts, validate_manifest)",
    "Added model_registry/store.py (registry_path, read_registry_object, write_registry_json_atomic)",
    "Added model_registry/migrations.py (SCHEMA_VERSION, default_migrated_manifest, legacy PAV helpers)",
    "Refactored model_registry/service.py to orchestrate schema/store/migrations while preserving public API"
  ],
  "validation_evidence": [
    "uv run pytest tests/model_registry -q",
    "uv run pytest tests/ci/test_import_standardization_behavior.py -q",
    "uv run pytest ../../asset_generation/web/backend/tests/test_registry_*.py -q",
    "bash ci/scripts/diff_cover_preflight.sh"
  ]
}
```

## Status

Proceed

## Reason

Implementation completed with layered extraction and passing scoped + gate checks; ready for Acceptance Criteria Gatekeeper verification before any completion closure.
