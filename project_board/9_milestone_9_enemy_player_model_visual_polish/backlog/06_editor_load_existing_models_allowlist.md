# TICKET: 06_editor_load_existing_models_allowlist

Title: Model editor — load existing exports from disk (draft + in-use only, canonical roots)

## Description

Add a **Load / Open existing** flow in the 3D model editor that **only** lists models under the project’s **canonical enemy/player export directories** (per spec), and **only** entries that are **draft** or **currently in-use** in the registry. Reject with a clear error any path outside the allowlist or ad-hoc “pick any file” dialogs for misc GLBs.

## Acceptance Criteria

- No UI path loads arbitrary `res://` or OS paths outside allowlisted roots.
- Draft and in-use models from registry appear in the picker; unrelated files in the same folder are hidden or disabled per spec.
- Automated test proves traversal / path injection cannot escape jail (mirror M21 assets-router patterns if applicable).
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

## Dependencies

- `01_spec_model_registry_draft_versions_and_editor_contract`
- M21
