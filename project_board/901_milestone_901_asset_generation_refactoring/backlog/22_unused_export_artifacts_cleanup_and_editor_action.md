# TICKET: Unused export artifacts cleanup and asset editor action

**Epic:** Milestone 901 — Asset Generation Refactoring  
**Status:** Backlog

---

## Title

Clean up allowlisted export trees of orphaned files and add an asset editor control to delete unused models and derived images safely.

## Description

Export directories under `asset_generation/python/` (for example `animated_exports/`, `animated_exports/draft/`, `animated_exports/textures/`, `animated_exports/spots/`, `player_exports/`, `level_exports/` as defined by the canonical export-path contract and registry policy) accumulate **orphaned artifacts**: GLBs, PNG textures, spot maps, companion files such as `*.attacks.json`, and other generated outputs that are **no longer referenced** by `model_registry.json` (or other single-source manifests the pipeline treats as authoritative).

This ticket delivers:

1. **A defined notion of “unused”** for files under the allowlisted export roots (e.g. not referenced by any registry version path, active visual, or linked manifest entry — exact rules to be specified in implementation after auditing callers).
2. **Backend support**: endpoints or service operations to **list** candidate orphans (dry-run), optionally **preview** what would be removed, and **delete** a confirmed set — with validation that paths stay within allowlisted prefixes (reuse registry path policy / export directory contract).
3. **Asset editor UI**: a **button** (with confirmation and summary of affected paths) that triggers the cleanup flow so operators do not rely on manual `git` or filesystem deletes.
4. **One-time repo hygiene**: remove or document any known orphaned files already present after the feature exists (optional follow-up commit scoped to true orphans only).

Related areas to review during implementation: FastAPI routers under `asset_generation/web/backend/routers/` (assets/registry), `asset_generation/python/src/model_registry/`, frontend editor panes under `asset_generation/web/frontend/src/components/Editor/`, and any CLI that writes exports so new writes stay consistent with registry updates.

## Acceptance Criteria

- [ ] **Orphan detection** is implemented in shared Python service logic (not only in the router) and is covered by **unit tests** with temporary directories (no dependency on real `animated_exports/` blobs in assertions).
- [ ] **Path safety**: delete/list operations reject paths outside allowlisted export roots; behavior matches existing registry path validation patterns.
- [ ] **API**: documented routes (or extension of existing assets/maintenance routes) for at least: list unused candidates; execute delete for an explicit allowlist of relative paths or a server-side computed set after user confirmation token — design choice documented in ticket implementation notes.
- [ ] **UI**: asset editor exposes a **clear control** (e.g. “Remove unused export files…”) that shows a **preview count/list** (truncated + expandable if large) and requires **explicit confirmation** before deletion.
- [ ] **Regression**: existing backend and frontend tests pass; new tests cover happy path and at least one forbidden-path / out-of-root case.
- [ ] **Operational note** in code or ticket completion comment: what file categories are considered (GLB, PNG, JSON sidecars, etc.) and any intentional exclusions (e.g. never delete `draft/` without toggle).

## Dependencies

- Export directory contract and registry path policy modules (see `done/17_export_directory_contract_consolidation.md` and `done/11_registry_path_policy_unification.md`) — implementation must import **canonical** allowlists/constants rather than duplicating path tuples.

## Non-goals (initial scope)

- Deleting files referenced by the Godot project under `res://` that are not tracked by the model registry (requires a separate audit).
- Automatic deletion on every export run without user confirmation.

## Notes

- Prefer **dry-run default** in UI: load preview first, then confirm delete.
- Consider pairing deletes: e.g. GLB and sibling `*.attacks.json` when both are orphaned and detection rules say they belong together.
