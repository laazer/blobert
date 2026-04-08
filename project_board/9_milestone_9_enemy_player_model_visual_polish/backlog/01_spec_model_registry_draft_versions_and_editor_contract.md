# TICKET: 01_spec_model_registry_draft_versions_and_editor_contract

Title: Specification — model registry, draft flag, player active path, enemy version slots, allowlist roots, deletion rules

## Description

Author `project_board/specs/model_registry_draft_versions_spec.md` (name final in spec PR) that defines the **data contract** called out in `blocked/enemy_model_versions_draft_editor_and_spawn.md`:

- **Registry / manifest** format: per-enemy-type **version list** (paths or IDs), **draft** vs **in-use** flags, **single player active** visual path (replacement semantics).
- **Canonical filesystem roots** for enemy exports and player/Blobert exports; explicit **denylist** of “misc” paths the editor must never offer.
- **Promotion** draft → in-use; **demotion** if needed.
- **Deletion:** draft delete (files + registry); in-use delete (sole-version guard, confirmation, pool reassignment, or block — pick one table per case).
- **Spawn integration hook:** how runtime reads “active versions” for random selection (interface only; implementation may land in M10 + ticket `08`).

## Acceptance Criteria

- Spec file exists under `project_board/specs/` with stable filename referenced from downstream tickets.
- Covers UI surfaces (editor + any game-facing toggles if in scope), backend persistence location, and migration from “single GLB per family” today.
- ADRs for ambiguous choices (e.g. JSON next to GLB vs single `models.json` in repo root).
- Downstream tickets `04`–`09` can be implemented without reopening the contract.

## Dependencies

- M5 / M21 — current export layout and editor app structure (read-only discovery)
