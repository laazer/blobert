# TICKET: 04_editor_ui_draft_status_for_exports

Title: 3D model editor UI — mark exports as draft and promote to in-use

## Description

Extend the **M21** asset web editor (or agreed UI surface) so operators can set a model export to **draft** or **promote** it to **in-use** per `01_spec_model_registry_draft_versions_and_editor_contract`. Draft assets must be **excluded** from default game load paths and spawn pools until promoted (enforced in registry consumer code, not UI-only).

## Acceptance Criteria

- UI can toggle or set **draft** status on an export that the registry knows about; persisted per spec.
- Promoted models appear in the **in-use** set; demotion path documented if supported.
- Backend API validated with tests; no silent filesystem writes outside canonical export roots.
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

## Dependencies

- `01_spec_model_registry_draft_versions_and_editor_contract`
- M21 — editor stack (FastAPI + React)
