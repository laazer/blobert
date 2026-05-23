# TICKET: FEAT-20260522-registry-build-options-snapshot
Title: Store build configs on model registry version rows
Project: blobert
Created By: Human
Created On: 2026-05-22

---

## Description

The asset editor treats `model_registry.json` as a file index (`id`, `path`, `draft`, `in_use`, `tags`). Procedural build options, colors, and command export fields live only in colocated sidecars (`*.build_options.json` next to GLBs) and are loaded via a separate asset fetch (`fetchBuildOptionsSidecarForGlbPath`). That forces implicit derive-on-load behavior, extra round-trips, and drift risk when registry rows exist without sidecars (e.g. after `sync_discovered_*` only scans GLBs).

We recently fixed preview-only loads so `selectAssetByPath` does not hydrate from sidecars unless `{ importBuildOptions: true }` (explicit import on post-run auto-select and registry load-existing open). This feature makes registry the durable record of how each version was built.

**Goal:** Each registry version row stores the full validated build snapshot used to create that model. The editor and API read config from the registry first; sidecars remain as export artifacts and legacy fallback until backfill completes.

**Design (default — spec may refine):**
- Canonical for API/UI: `versions[].build_options` on registry rows (enemy animated exports).
- Still write sidecar on export (`base_enemy._export_build_options_json`) for file portability and `path_layout.relocate_registry_row_assets`.
- Read order: registry `build_options` → sidecar file → no import (preview-only unchanged).
- Player: equivalent snapshot on player version rows (spec defines field name and validation).

**Scope:** Python `model_registry`, web backend registry router/OpenAPI, frontend store hydration and types.

**Non-goals:** Removing sidecars entirely; registry-only with no sidecar on export; Godot runtime consumption.

**Key references:** `schema.py`, `service.py`, `base_enemy.py`, `registry.py`, `useAppStore.ts`, `project_board/bugfix/in_progress/model-load-ui-settings.md`, `project_board/specs/registry-fix-versions-slots-load.md`.

---

## Acceptance Criteria

- After generating/exporting an animated enemy variant, `GET /api/registry/model` includes `build_options` on that version row matching the export snapshot.
- `open_existing` / explicit import hydrates the editor from registry `build_options` without sidecar fetch when the field is present.
- Preview-only registry version click does not change in-session build/color/command state (regression `BUG-model-load-ui-settings-preview-select-does-not-import-sidecar` stays green).
- Backfill: migration or discover-sync populates `build_options` for existing rows that have on-disk sidecars (idempotent).
- Python model_registry tests, backend registry contract tests, and frontend unit tests cover read/write/fallback paths.
- `timeout 300 ci/scripts/run_tests.sh` green for touched areas (or documented scope-limited evidence per gatekeeper policy).

---

## Dependencies

- BUG model-load-ui-settings preview vs explicit import semantics (implemented in working tree; must not regress).

---

## Execution Plan

**Domain:** Python asset pipeline + web backend + web frontend (no Godot).

**Estimated Effort:** M (6–8 agent runs: Spec 1 → Test design/break 2 → Implementation 2–3 Python then API+frontend → Static QA → Integration).

**Primary file surfaces**

| Layer | Paths |
|-------|--------|
| Registry schema/validation | `asset_generation/python/src/model_registry/schema.py`, `migrations.py` |
| Registry persistence/backfill/sync | `asset_generation/python/src/model_registry/service.py`, `path_layout.py` |
| Export sidecar (unchanged write, coordinated read) | `asset_generation/python/src/enemies/base_enemy.py`, `asset_generation/python/src/player/player_builder.py` |
| Post-run registry sync hook | `asset_generation/web/backend/routers/run.py` (`_sync_registry_for_family`) |
| HTTP registry + load-open | `asset_generation/web/backend/routers/registry.py`, `models/responses/registry.py`, `services/registry_query.py` |
| OpenAPI → TS | `asset_generation/web/frontend/scripts/sync-api-types.sh`, `src/api.types.ts` |
| Editor hydration | `asset_generation/web/frontend/src/store/useAppStore.ts`, `src/api/client.ts`, `ModelRegistryPane.tsx` |
| Tests | `asset_generation/python/tests/model_registry/`, `asset_generation/web/backend/tests/test_registry_*`, `asset_generation/python/tests/api/`, `asset_generation/web/frontend/src/store/*.test.ts` |

**Spec exit gate:** `spec_completeness_check.py` with `--type api,load-open` (registry mutation + `load_existing/open` hydration).

### Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author feature spec: `versions[].build_options` contract, validation (`parse_build_options_json` / sanitize), player snapshot field, read order, backfill idempotency, post-run write path, size/omit rules | Spec Agent | Ticket AC + file surfaces above | `project_board/specs/FEAT-20260522_registry_build_options_snapshot_spec.md` | — | Spec passes `spec_completeness_check.py --type api,load-open`; REQ traceability to AC | Player uses `.player.json` not `.build_options.json` — spec must define equivalent; assume `schema_version` stays `1` with optional key unless spec documents bump |
| 2 | Failing Python tests: schema allowlist, normalize/validate, persist on sync/export hook, backfill from sidecar, idempotent rediscovery | Test Designer Agent | Spec § test plan | Tests under `asset_generation/python/tests/model_registry/` (new or extended) | 1 | `uv run pytest` on new tests **fail** for missing impl | Large snapshots may bloat `model_registry.json` — spec should cap or strip derived keys |
| 3 | Failing backend contract tests: `GET /api/registry/model` exposes `build_options`; `POST .../load_existing/open` returns snapshot when present; post-run row populated | Test Designer Agent | Spec API tables | Tests in `asset_generation/web/backend/tests/` + `asset_generation/python/tests/api/` as applicable | 1 | Contract tests fail pre-impl | OpenAPI sync is follow-up in impl — tests may use response shapes from spec until types land |
| 4 | Failing frontend tests: registry-first hydrate; sidecar fallback; preview-only regression (`importBuildOptions` false) | Test Designer Agent | Spec REQ preview/import | `useAppStore` tests + extend `useAppStore.selectAssetByPath.previewOnly.test.ts` | 1 | `npm test` targeted files fail pre-impl | Assumes `hydrateBuildOptionsFromPreviewGlbPath` refactored to accept inline snapshot |
| 5 | Adversarial test pass: malformed `build_options`, missing sidecar+registry, oversized JSON, player/enemy parity | Test Breaker Agent | Tasks 2–4 | Additional failing tests or gap doc in checkpoint | 2, 3, 4 | New edge cases documented; no prose-only tests | Route to **generalPurpose** or frontend-capable agent — **not** Godot agents |
| 6 | Python implementation: schema + service persist/backfill; enrich `sync_discovered_*`; attach snapshot on post-run (run router passes resolved JSON or reads fresh sidecar) | Implementation Agent (Generalist) | Spec + failing Python tests | Green Python tests; `model_registry.json` rows carry snapshots after export/sync | 5 | `bash .lefthook/scripts/py-tests.sh` passes for touched modules; `diff_cover_preflight.sh` if required | `sync_discovered_*` today only adds `{id,path,draft,in_use}` — must extend without breaking R1 multi-version spec |
| 7 | Web backend implementation: `VersionRowResponse.build_options`, manifest mapping, `load_existing/open` payload includes snapshot; optional backfill/sync endpoint if spec defines | Implementation Agent (Generalist) | Spec + failing backend tests | Green backend + api contract tests; OpenAPI updated | 6 | `uv run pytest` backend registry tests pass | Run `sync-api-types.sh` before frontend impl |
| 8 | Frontend implementation: registry-first in `hydrateBuildOptionsFromPreviewGlbPath` (or successor); pass registry snapshot from `openExisting` / `GET` cache; keep sidecar fallback | Implementation Frontend Agent | Spec + failing frontend tests + synced `api.types.ts` | Green frontend unit tests; explicit import uses registry when present | 7 | `npm test` store/registry tests pass; preview regression green | `CommandPanel` local state races — spec should reference REQ-2 from bugfix doc |
| 9 | Static QA | Static QA | Changed py/ts files | Clean `task hooks:py-review`, `npx tsc --noEmit`, staged hooks | 6, 7, 8 | No new linter violations | api-contract-check if backend OpenAPI changed |
| 10 | Integration + AC gate | Acceptance Criteria Gatekeeper Agent | Full AC list | `timeout 300 ci/scripts/run_tests.sh` evidence in checkpoint; ticket COMPLETE in `done/` | 9 | All AC met; git clean/pushed per workflow | Scope-limited CI only if gatekeeper documents |

**Implementation sequencing:** 6 → 7 → 8 (Python manifest truth before API/TS). Sidecar export in `base_enemy` remains; registry write is additive.

**Test-breaker routing:** `asset_generation/web/frontend/**` and store hydration → Test Breaker with frontend/generalPurpose; `asset_generation/python/**` → test-breaker default; **no** `gameplay-systems` / `engine-integration` / Godot.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_DESIGN

## Revision
2

## Last Updated By
Spec Agent

## Validation Status
- Tests: Not Run
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Test Designer Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/inbox/00_backlog/FEAT-20260522-registry-build-options-snapshot.md",
  "spec_path": "project_board/specs/FEAT-20260522_registry_build_options_snapshot_spec.md",
  "spec_completeness_types": "api,load-open",
  "checkpoint_log": "project_board/checkpoints/FEAT-20260522-registry-build-options-snapshot/2026-05-22T-feature-run.md"
}
```

## Status
Proceed

## Reason
Spec complete (R1–R9, api/load-open gates). Orchestrator must run spec_completeness_check.py before test authoring proceeds.
