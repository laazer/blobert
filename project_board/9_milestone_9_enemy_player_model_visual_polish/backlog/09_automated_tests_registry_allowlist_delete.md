# TICKET: 09_automated_tests_registry_allowlist_delete

Title: Automated tests — registry API, allowlisted load, draft promotion, deletion invariants

## Description

Add **pytest** (backend) and/or **frontend** tests as appropriate to lock: registry read/write, draft vs in-use filtering, allowlisted path rejection, and post-delete invariants. Complements per-ticket tests in `04`–`07`; this ticket is the **cross-cutting** suite so refactors do not regress the contract.

## Acceptance Criteria

- New tests live next to existing M21 test layout (`asset_generation/web` / `tests/` per repo convention).
- Covers at minimum: reject path outside allowlist; draft not in default “game pool” reader; one delete scenario from `07_editor_delete_draft_and_in_use_models`.
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

## Dependencies

- `01_spec_model_registry_draft_versions_and_editor_contract`
- `04_editor_ui_draft_status_for_exports` through `07_editor_delete_draft_and_in_use_models` (soft — tests can grow incrementally)
