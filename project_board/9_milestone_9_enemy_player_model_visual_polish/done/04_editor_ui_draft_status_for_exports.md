# TICKET: 04_editor_ui_draft_status_for_exports

Title: 3D model editor UI — mark exports as draft and promote to in-use

## Description

Extend the **M21** asset web editor (or agreed UI surface) so operators can set a model export to **draft** or **promote** it to **in-use** per `01_spec_model_registry_draft_versions_and_editor_contract`. Draft assets must be **excluded** from default game load paths and spawn pools until promoted (enforced in registry consumer code, not UI-only).

## Specification

- **Contract:** `project_board/specs/model_registry_draft_versions_spec.md` (MRVC-2, MRVC-4, MRVC-5, MRVC-6, MRVC-8).
- **Persistence:** `asset_generation/python/model_registry.json` (atomic write).
- **Backend:** FastAPI `GET /api/registry/model`, `PATCH .../enemies/{family}/versions/{version_id}`, `GET /api/registry/model/spawn_eligible/{family}` (consumer choke point for MRVC-4).
- **Frontend:** Center column **Registry** tab — per-family version table with Draft / In pool checkboxes; demotion documented inline (draft removes from pool).

## Execution Plan

| # | Stage | Deliverable |
|---|--------|-------------|
| 1 | Planner | Scope: service + API + UI + spawn_eligible consumer |
| 2 | Spec | MRVC cross-reference + endpoint list (above) |
| 3 | Test design | `tests/model_registry/test_service.py`, `tests/web/test_registry_api.py` |
| 4 | Test break | Invalid path / unknown version / empty PATCH body |
| 5 | Implementation | `src/model_registry/`, `routers/registry.py`, React `ModelRegistryPane` |
| 6 | AC Gatekeeper | `run_tests.sh` + evidence matrix |

## Acceptance Criteria

- UI can toggle or set **draft** status on an export that the registry knows about; persisted per spec.
- Promoted models appear in the **in-use** set; demotion path documented if supported.
- Backend API validated with tests; no silent filesystem writes outside canonical export roots.
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

## Dependencies

- `01_spec_model_registry_draft_versions_and_editor_contract`
- M21 — editor stack (FastAPI + React)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

COMPLETE

## Revision

7

## Last Updated By

Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: `uv run pytest tests/model_registry/ tests/web/test_registry_api.py` — registry service + HTTP contract (13 tests); full `pytest tests/` 588 passed with `uv run --extra dev` (includes new cases).
- Static QA: Ruff clean on `src/`, `tests/`, `main.py`.
- Integration: FastAPI router uses canonical `asset_generation/python` on `sys.path` for imports; manifest reads/writes use `settings.python_root` (tmp-isolated in ASGI tests). Only `model_registry.json` is written under that root.

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent

Human

## Required Input Schema

```json
{}
```

## Status

Proceed

## Reason

Registry service, `/api/registry/*` endpoints, Registry UI tab, and `spawn_eligible_paths` consumer landed; demotion described in UI copy (MRVC-4).
