# TICKET: 13_registry_paths_align_with_draft_vs_in_use_directories

Title: Align model registry paths / export pipeline with directory layout (draft vs in-use / slotted)

## Description

Today **draft**, **in_use**, and **slot** membership are carried only in `model_registry.json` (and UI), while GLBs for all states typically live under the same roots (e.g. `asset_generation/python/animated_exports/*.glb`). That makes it hard to **commit only shipped assets** without manually cross-checking the registry or staging individual files.

This ticket **reconciles on-disk layout with lifecycle state** so directory trees reflect meaning:

- **Draft** exports live under an agreed **draft subtree** (per asset class: animated enemies, player, levels, etc.).
- **Non-draft, in-use** (spawn-pool eligible) models live under an agreed **canonical “live” subtree** (or remain at the current root if spec prefers draft-only nesting).
- **Optional:** “slotted but not in pool” vs “in pool” — only split directories if the spec finds a clean rule; otherwise keep **slots** as registry-only and use **draft vs live** folders as the primary VCS lever.

The outcome should support a simple git workflow (e.g. `.gitignore` for `**/…/draft/**` or documented `git add` patterns) **without** breaking allowlisted path validation (`ALLOWLIST_PREFIXES` in `asset_generation/python/src/model_registry/service.py`), asset serving (`/api/assets/...`), editor load allowlists, or Godot `res://` references.

## Acceptance Criteria

- Written spec (`project_board/specs/` or ticket appendix) names the **exact relative paths** under `asset_generation/python/` (and any mirror under `res://` if applicable) for: draft animated exports, live animated exports, player exports, and other allowlisted roots — including **migration** from today’s flat `animated_exports/` layout.
- **Export / save** paths (Blender pipeline, backend write endpoints, `SaveModelModal` / related flows) write new files to the directory that matches the version’s **draft** flag (and player **player_active_visual** draft if relevant).
- **Promote / demote draft** (and any “move into spawn pool” operation) updates **both** registry `path` fields **and** moves or re-exports files so disk and JSON stay consistent; failures are transactional or clearly recoverable per spec.
- **Validation:** `validate_manifest` / allowlist rules accept the new prefixes; traversal and path-normalization tests stay green.
- **Tests:** extend Python registry + backend tests (existing patterns in `asset_generation/web/backend/tests/test_registry_*.py` and `asset_generation/python/tests/`) for new paths; `timeout 300 ci/scripts/run_tests.sh` exits 0.
- **Docs:** short note for contributors (where to commit vs ignore draft exports) — only if an existing doc is updated; no new standalone doc file unless already standard for this milestone.

## Dependencies

- Cross-check with `done/` tickets for registry UI and delete flows so **move** semantics don’t fight **delete draft / delete in-use** rules.
- Coordinate any **Godot** resource paths that embed `animated_exports/` literally.

## Execution plan

1. Spec: final directory tree, migration steps, gitignore policy, edge cases (rename id, duplicate stem, missing file).
2. Python: `ALLOWLIST_PREFIXES`, path helpers, manifest validate + patch paths; optional one-shot migration script or documented manual move list.
3. Backend + frontend: save/promote/demote/delete flows use shared path resolution.
4. CI: full test run + spot-check editor load and spawn-eligible path list for a fixture family.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
1

## Last Updated By
Autopilot / implementation handoff

## Validation Status

- Tests: `timeout 300 ci/scripts/run_tests.sh` exit 0; `asset_generation/python` pytest (707 passed); frontend `npm test` (162 passed).
- Spec: `project_board/specs/registry_draft_live_directory_layout_spec.md`
- Static QA: Ruff clean on touched Python; TypeScript tests green.

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

Draft/live layout, relocate on patch, sync scans `draft/`, run stream `output_draft`, asset list includes draft subtree, contributor note in milestone README.
