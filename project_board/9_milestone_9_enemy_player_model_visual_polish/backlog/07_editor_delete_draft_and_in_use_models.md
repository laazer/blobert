# TICKET: 07_editor_delete_draft_and_in_use_models

Title: Editor — delete draft exports and delete in-use models (safety rules)

## Description

Implement **delete draft** (remove registry entry + files or orphan handling per spec) and **delete in-use** with mandatory safeguards: e.g. block delete when sole version for a type, require confirmation, or auto-reassign pool — exactly as specified in `01_spec_model_registry_draft_versions_and_editor_contract`.

## Acceptance Criteria

- Both flows implemented with UX confirmation where spec requires it.
- Violations (delete last in-use version without replacement) are prevented or explicitly escalated per spec — no undefined game state.
- Automated tests cover allowlist/registry consistency after delete and at least one deletion path (draft or in-use).
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

## Dependencies

- `01_spec_model_registry_draft_versions_and_editor_contract`
- `05_editor_ui_game_model_selection` (soft)
- `06_editor_load_existing_models_allowlist` (soft)
- M21
