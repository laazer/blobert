# FEAT-20260522 — Registry build-options snapshot (Functional & Non-Functional Specification)

**Ticket:** `project_board/inbox/00_backlog/FEAT-20260522-registry-build-options-snapshot.md`  
**Spec exit gate types:** `api`, `load-open`  
**Cross-reference (must not regress):** `project_board/bugfix/in_progress/model-load-ui-settings.md` REQ-1 (preview-only) / REQ-2 (explicit import)  
**Surfaces:** `asset_generation/python/src/model_registry/`, `asset_generation/python/src/enemies/base_enemy.py`, `asset_generation/python/src/player/player_builder.py`, `asset_generation/web/backend/routers/registry.py`, `asset_generation/web/backend/models/responses/registry.py`, `asset_generation/web/frontend/src/store/useAppStore.ts`, OpenAPI → `api.types.ts`

---

## Schema version decision (authoritative)

| Decision | Value | Rationale |
|----------|--------|-----------|
| Manifest `schema_version` | **Remain `1`** (`SCHEMA_VERSION` in `migrations.py` unchanged) | Additive optional field on version rows; no breaking top-level shape change |
| New registry field | **`versions[].build_options`** | Same key for **enemy and player** version rows (API/UI symmetry) |
| Player animation metadata | **Unchanged** — `{stem}.player.json` | Not used for procedural build UI hydration; remains animation/bone metadata only |
| Player build sidecar (export artifact) | **`{stem}.build_options.json`** (new write on player export) | Parity with enemy portability, backfill source, and `fetchBuildOptionsSidecarForGlbPath` fallback |

---

## HTTP API Contract — Endpoint Freeze

Existing routes are **extended** (optional JSON fields only). No route renames or method changes.

| Method | URI | Change |
|--------|-----|--------|
| GET | `/api/registry/model` | Each `enemies[{family}].versions[]` and `player.versions[]` row may include optional `build_options` object (validated manifest shape). |
| POST | `/api/registry/model/load_existing/open` | Success body adds optional `build_options` when the resolved registry version row carries a snapshot. |
| GET | `/api/registry/model/load_existing/candidates` | **Unchanged** shape (no `build_options` in list; clients use GET `/model` or open response). |
| POST | `/api/registry/model/enemies/{family}/sync_animated_exports` | Behavior: discovery + **idempotent backfill** of `build_options` from on-disk `*.build_options.json` (see R4). |
| POST | `/api/registry/model/player/sync_player_exports` | Same backfill for player rows from `*.build_options.json`. |
| PATCH | `/api/registry/model/enemies/{family}/versions/{version_id}` | **Does not accept** `build_options` in request body (preserve-on-patch only). |
| PATCH | `/api/registry/model/player/versions/{version_id}` | Same (if exposed; service `patch_player_version` today — no client patch of snapshot). |
| POST | `/api/run/stream` (and sync run completion) | No HTTP shape change; post-run registry write is server-side after `output_file` (see R5). |

**Deferred boundary:** No new dedicated `POST .../backfill_build_options` endpoint; backfill runs inside `sync_discovered_*` and export/post-run paths. Godot runtime does not read registry snapshots. Sidecar files are **not** removed.

---

## Validation Precedence

Checks apply in order; **first failure wins** (observable status/detail must be stable for contract tests).

### A. Manifest persistence (`validate_manifest` / `save_manifest_atomic`)

1. Top-level MRVC keys and `schema_version === 1`.
2. Per-version row required keys (`id`, `path`, `draft`, `in_use`, optional `name`, `tags`).
3. If `build_options` **key is absent** → row normalizes without it (optional field).
4. If `build_options` **present**:
   - Must be a JSON object (`dict`); non-object → `ValueError` (fail save / fail load normalization).
   - **Enemy row** (`enemies[{family}]`): validate with `coerce_validate_enemy_build_options(family, raw)` from `src.utils.build_options.validate`.
   - **Player row** (`player.versions[]`): validate with `coerce_validate_enemy_build_options("player_slime", raw)` (same coercion pipeline as `options_for_enemy("player_slime", …)` / `player_generator.py`).
   - Serialized UTF-8 JSON size of canonical snapshot ≤ **`262144` bytes** (256 KiB) → else `ValueError` with message containing `build_options too large`.
5. After coercion, if the dict is **empty** → **omit** `build_options` key from normalized row (do not persist `{}`).
6. Existing `draft` / `in_use` / slot normalization runs unchanged after row fields are validated.

### B. HTTP `POST .../load_existing/open`

1. Malformed body / mixed identity (existing router rules) → **400**.
2. Unknown kind → **400**.
3. Identity resolution → canonical allowlisted path.
4. File missing under `python_root` → **404** `registry target file not found`.
5. Attach `build_options` from **registry row** matching `version_id` (enemy/player) or path kind `path` → lookup row by normalized path in manifest; if no row or no snapshot → field **omitted** (not `null` in JSON when using `exclude_none`).

### C. Frontend explicit import (`importBuildOptions: true`)

1. Inline `build_options` from registry/open response if provided to hydrator.
2. Else `GET /api/assets/{path}` for `*.build_options.json` (404 → null).
3. If no snapshot or empty object → **no store mutation** (preview URL may still update).
4. **Never** read `*.player.json` for build UI hydration.

### D. Preview-only (`selectAssetByPath` without `importBuildOptions`)

No hydration (REQ-1 bugfix) — **no precedence table**; sidecar/registry ignored.

---

## Selector Mode Contract (load-existing)

| `kind` | Required body fields | Forbidden | Open success body |
|--------|----------------------|-----------|-------------------|
| `enemy` | `family`, `version_id` | `path` | `kind`, `family`, `version_id`, `path`, optional `build_options` |
| `player` | `version_id` | `family`, `path` | `kind`, `version_id`, `path`, optional `build_options` |
| `path` | `path` only | `family`, `version_id` | `kind`, `path`, optional `build_options` if a registry row matches that path |

**Mixed-selector rejection (unchanged):** `path` together with `family` or `version_id` → **400** `malformed target payload: mixed-identity-and-path`.

**Import coupling:** `ModelRegistryPane.openExistingSelection` continues to call `selectAssetByPath(payload.path, { importBuildOptions: true })` and must pass registry `build_options` into the hydrator when present so **sidecar fetch is skipped** (AC: hydrate without sidecar round-trip).

---

## Failure Taxonomy

| Condition | Layer | HTTP / behavior |
|-----------|--------|-----------------|
| Invalid `build_options` type or coercion failure | `validate_manifest` | **500** on GET `/model` if on-disk manifest invalid; **400** on mutating routes that persist |
| `build_options` over size cap | `validate_manifest` | Same as above |
| Unknown family / version on patch/delete | service | **404** |
| Load-open missing file | router | **404** |
| Load-open malformed payload | router | **400** (existing detail strings preserved) |
| Sidecar fetch 404 on explicit import | frontend | No-op hydration; preview still works |
| Post-run registry attach failure | `run.py` | **Non-fatal** (log warning; run still completes) — same as today’s `_sync_registry_for_family` |

---

## Requirement R1 — Registry schema: optional `versions[].build_options`

### 1. Spec Summary

- **Description:** Each version row under `enemies[{family}].versions` and `player.versions` may include an optional **`build_options`** object: the **validated procedural build snapshot** used when that GLB was produced (or backfilled from sidecar). The manifest remains `schema_version: 1`.
- **Constraints:** `validate_manifest` allowlist for version row keys becomes `{id, path, draft, in_use, name, tags, build_options}`. Validation uses **`coerce_validate_enemy_build_options`** with family slug or `"player_slime"`. No bare unvalidated dicts persisted.
- **Assumptions:** Snapshot content matches what export writes to `*.build_options.json` for enemies; player export gains the same sidecar write (R6).
- **Scope:** `schema.py`, `migrations.py` (constant only), `service.py` helpers, backend `VersionRowResponse`, frontend `RegistryEnemyVersion` / generated OpenAPI types.

### 2. Acceptance Criteria

1. Manifest with valid `build_options` on a spider row round-trips through `load_effective_manifest` with semantically equal snapshot (coerced keys stable).
2. Manifest with invalid `build_options` (e.g. wrong types for required controls) fails `validate_manifest` with `ValueError`.
3. Row without `build_options` key validates identically to pre-feature manifests.
4. `GET /api/registry/model` returns `build_options` on rows that have it (`exclude_none` omits absent rows’ field).

### 3. Risk & Ambiguity Analysis

- **Risk:** Large snapshots bloat `model_registry.json` — mitigated by 256 KiB cap (R7).
- **Edge:** Legacy rows with sidecar but no registry field — addressed by R4 backfill.

### 4. Clarifying Questions

- None (schema_version and field name decided above).

---

## Requirement R2 — Canonical read order (registry → sidecar → no import)

### 1. Spec Summary

- **Description:** For **explicit import** flows only, hydration uses **registry snapshot first**, then on-disk **`{glb_stem}.build_options.json`**, then stops without mutating build/color/command state. **Preview-only** path selection does not import (BUG REQ-1).
- **Constraints:** Do not load build state from `*.player.json`. `fetchBuildOptionsSidecarForGlbPath` remains the sidecar fetch implementation.
- **Assumptions:** `hydrateBuildOptionsFromPreviewGlbPath` (or successor) accepts optional inline snapshot; callers pass registry data when known.
- **Scope:** `useAppStore.ts`, `ModelRegistryPane.tsx`, `api/client.ts` types, unit tests including `useAppStore.selectAssetByPath.previewOnly.test.ts`.

### 2. Acceptance Criteria

1. When registry row has `build_options` and explicit import runs, **`fetchBuildOptionsSidecarForGlbPath` is not called** (mock assertion).
2. When registry lacks `build_options` but sidecar exists, import uses sidecar (existing behavior).
3. When neither exists, import no-ops; `animatedBuildOptionValues` unchanged.
4. Preview-only `selectAssetByPath(path)` without flag does not call hydrator (regression test stays green).
5. `openExistingSelection` with registry snapshot hydrates store without sidecar fetch.

### 3. Risk & Ambiguity Analysis

- **Risk:** Stale registry snapshot vs newer sidecar — **registry wins** when present (canonical for API/UI); re-export or backfill updates registry.
- **Edge:** `animatedBuildControls[slug]` empty — preserve today’s early-return guard.

### 4. Clarifying Questions

- None.

---

## Requirement R3 — Write path: animated enemy export

### 1. Spec Summary

- **Description:** On successful animated export, persist the same **`build_options_snapshot`** written to `{filename}.build_options.json` onto the registry version row whose **`path`** matches the exported GLB (after normalization). Sidecar write in `base_enemy._export_build_options_json` **remains**.
- **Constraints:** Snapshot input is the validated dict passed to `export_enemy(..., build_options_snapshot=opts)` (today `_build_options_for_current_enemy` / `options_for_enemy` + coerce path). Attach occurs in the same persistence transaction as registry row create/update for that export (not a separate manual step).
- **Assumptions:** Version `id` is the GLB stem; path is allowlisted under `animated_exports/`.
- **Scope:** `generator.py` / export pipeline hook, `model_registry/service.py`, optional thin helper `attach_build_options_to_version_row(manifest, family, version_id, snapshot)`.

### 2. Acceptance Criteria

1. After export of `animated_exports/spider_animated_09.glb`, `GET /api/registry/model` shows `build_options` on that row matching the sidecar JSON (semantic equality post-coercion).
2. Sidecar file still exists on disk next to GLB.
3. Re-export same path **may overwrite** registry snapshot and sidecar with new build (last export wins).

### 3. Risk & Ambiguity Analysis

- **Edge:** Row not yet in manifest — post-export `sync_discovered_*` or attach-on-export must ensure row exists before snapshot write.

### 4. Clarifying Questions

- None.

---

## Requirement R4 — Write path: `sync_discovered_*` backfill (idempotent)

### 1. Spec Summary

- **Description:** When `sync_discovered_animated_glb_versions` or `sync_discovered_player_glb_versions` runs, **backfill** `build_options` from on-disk `{stem}.build_options.json` for any version row (new or existing) that **does not already** have a non-empty registry snapshot.
- **Constraints:** **Idempotent:** if row already has `build_options` after validation, **do not overwrite** from sidecar. Parse sidecar with `parse_build_options_json` (file contents as string) then coerce per R1. Missing/unreadable sidecar → leave row unchanged. New discovered rows still default `draft: true`, `in_use: false` (unchanged).
- **Assumptions:** Sidecar absent for legacy player exports until re-export or manual backfill run after R6 ships.
- **Scope:** `service.py` `_discovered_*` / `sync_discovered_*`; HTTP sync endpoints delegate to same functions.

### 2. Acceptance Criteria

1. Row with sidecar on disk, no registry `build_options` → after sync, row has validated snapshot.
2. Row with registry snapshot A; sidecar B → after sync, snapshot remains A.
3. Two consecutive syncs → identical manifest (idempotent).
4. Sidecar malformed → treat as empty parse (`parse_build_options_json` rules); row stays without snapshot (no crash).

### 3. Risk & Ambiguity Analysis

- **Risk:** Partial read race during export — acceptable; next sync repairs.

### 4. Clarifying Questions

- None.

---

## Requirement R5 — Write path: post-run registry sync

### 1. Spec Summary

- **Description:** After successful `cmd=animated` run (`run.py` `_sync_registry_for_family`), attach build snapshot to the version row for **`output_file`**: use the run’s resolved build options JSON (query `build_options` / env `BLOBERT_BUILD_OPTIONS_JSON` merged the same way as `generator._build_options_for_current_enemy`) **or**, if that resolution is unavailable, read the freshly written sidecar for the output stem.
- **Constraints:** Failure to attach is **non-fatal** (log warning). Discovery sync still runs first so new GLB row exists.
- **Assumptions:** `refreshAssetsAndAutoSelect` on frontend continues `importBuildOptions: true`; user sees new export settings in UI.
- **Scope:** `run.py`, `service.py`, frontend `refreshAssetsAndAutoSelect` (import path only; may read snapshot from refreshed registry GET if implemented).

### 2. Acceptance Criteria

1. Simulated post-run with known `build_options` query and new `output_file` → registry row contains matching snapshot.
2. Frontend post-run auto-select hydrates editor (explicit import) without requiring sidecar fetch when registry already populated.

### 3. Risk & Ambiguity Analysis

- **Edge:** `enemy=all` — no family sync today; unchanged (no snapshot attach for all-slug runs).

### 4. Clarifying Questions

- None.

---

## Requirement R6 — Write path: player export sidecar + registry snapshot

### 1. Spec Summary

- **Description:** Player export writes **`{filename}.build_options.json`** alongside GLB (validated `player_slime` snapshot) in addition to existing `{filename}.player.json`. Registry row for that export receives the same snapshot in **`build_options`**.
- **Constraints:** Update `path_layout._sidecar_names` for `player_exports` to include `{stem}.build_options.json` so draft/live relocate moves both `player.json` and `build_options.json`.
- **Assumptions:** Player procedural controls use slug `player` / `player_slime` in store hydration (existing `PLAYER_PROCEDURAL_BUILD_SLUG` behavior).
- **Scope:** `player_builder.py` / `export_player_slime`, `player_generator.py`, `path_layout.py`, registry attach.

### 2. Acceptance Criteria

1. After player export, both `.player.json` and `.build_options.json` exist.
2. Registry player version row includes `build_options` matching `.build_options.json`.
3. Relocate draft ↔ live moves both sidecars.

### 3. Risk & Ambiguity Analysis

- **Legacy:** Old player GLBs without `build_options.json` rely on R4 after re-export or manual sync only.

### 4. Clarifying Questions

- None.

---

## Requirement R7 — Size, omit, and patch preservation

### 1. Spec Summary

- **Description:** Snapshots store the **coerced** build-options dict (same keys as sidecar export). **Omit** key when empty after coercion. Enforce max **262144** UTF-8 bytes per row. PATCH endpoints for draft/in_use/name/tags **must not clear** existing `build_options` on the row.
- **Constraints:** Do not persist derived/ephemeral keys not produced by `coerce_validate_enemy_build_options` (no extra stripping layer beyond coercion). `relocate_registry_row_assets` updates `path` only; snapshot unchanged on same row id.
- **Assumptions:** Coercion output is the intended portable snapshot (includes `mesh`, `features`, `zone_geometry_extras`, control keys as today).
- **Scope:** `schema.py`, `patch_enemy_version`, `patch_player_version`, delete flows (snapshot deleted with row).

### 2. Acceptance Criteria

1. Snapshot at cap−1 bytes persists; cap+1 fails validation.
2. `patch_enemy_version(..., {"draft": true})` leaves `build_options` unchanged when present.
3. Delete version removes row and snapshot together (existing delete behavior).

### 3. Risk & Ambiguity Analysis

- **Risk:** Manifest file size growth — acceptable within cap per row.

### 4. Clarifying Questions

- None.

---

## Requirement R8 — `load_existing/open` includes snapshot

### 1. Spec Summary

- **Description:** `POST /api/registry/model/load_existing/open` success responses include optional **`build_options`** copied from the matched registry version row (enemy identity, player identity, or path lookup).
- **Constraints:** Field omitted when absent. OpenAPI / `LoadExistingOpenResponse` (or inline schema) updated; run `sync-api-types.sh` in implementation.
- **Assumptions:** Candidates endpoint unchanged; pane may cache `GET /model` for snapshots before open.
- **Scope:** `registry.py`, `registry_query.py` (lookup helper), response models, frontend `openExistingRegistryModel` consumer.

### 2. Acceptance Criteria

1. Open enemy row with snapshot → response includes `build_options` deep-equal to manifest row.
2. Open row without snapshot → response has no `build_options` key (or omitted with `exclude_none`).
3. Contract tests in `asset_generation/python/tests/api/` and backend registry tests assert shape.

### 3. Risk & Ambiguity Analysis

- **Edge:** `kind=path` without registry row → no `build_options` in response; client falls back to sidecar on import.

### 4. Clarifying Questions

- None.

---

## Requirement R9 — Preview-only import unchanged (BUG-model-load-ui-settings)

### 1. Spec Summary

- **Description:** Registry version **preview** clicks and BuildControls preview sync call `selectAssetByPath` **without** `importBuildOptions`. Explicit import list remains: `refreshAssetsAndAutoSelect`, `openExistingSelection` (and any other call sites already passing `{ importBuildOptions: true }`).
- **Constraints:** REQ-3 CommandPanel / REQ-4 ColorsPane from bugfix ticket are **out of scope** for this feature unless regression fails; this ticket only guards REQ-1/REQ-2 interaction with registry-first hydration.
- **Assumptions:** Bugfix implementation is in working tree or merged before integration.
- **Scope:** Frontend store + registry pane tests.

### 2. Acceptance Criteria

1. `useAppStore.selectAssetByPath.previewOnly.test.ts` passes.
2. Explicit import with registry snapshot does not call sidecar fetch (R2 AC).

### 3. Risk & Ambiguity Analysis

- **Product:** “Preview shows export settings” deferred; explicit import only.

### 4. Clarifying Questions

- None.

---

## Test plan (for Test Designer / Test Breaker)

| REQ | Python (`tests/model_registry/`) | Backend (`tests/test_registry_*`, `tests/api/`) | Frontend (`src/store/*.test.ts`) |
|-----|----------------------------------|--------------------------------------------------|-------------------------------------|
| R1 | allowlist, invalid type, size cap, player_slime coercion | `GET /model` includes field | types compile after OpenAPI sync |
| R2 | — | — | registry-first, sidecar fallback, preview-only |
| R3 | attach on export hook | contract row + sidecar | — |
| R4 | sync idempotent backfill | sync endpoint manifest | — |
| R5 | post-run attach helper | run router integration (mock) | refreshAssetsAndAutoSelect import |
| R6 | player sidecar + path_layout | — | — |
| R7 | patch preserves snapshot | patch contract | — |
| R8 | — | load_existing/open body | openExisting + hydrate |
| R9 | — | — | previewOnly regression |

**Guardrail:** No tests that assert markdown/ticket prose only; assert manifest JSON, HTTP bodies, or store state.

---

## Traceability to ticket acceptance criteria

| Ticket AC | Requirements |
|-----------|----------------|
| GET `/api/registry/model` includes `build_options` after export | R1, R3, R6 |
| `open_existing` hydrates from registry without sidecar when present | R2, R8 |
| Preview-only does not change session build state | R9, R2 |
| Backfill idempotent from sidecars | R4 |
| Python + backend + frontend tests | Test plan |
| CI green | Implementation / Integration stage |

---

## Deferred boundary statement

- Removing `*.build_options.json` sidecars or stopping sidecar export.
- Godot gameplay consumption of registry snapshots.
- PATCH API for clients to mutate `build_options` directly.
- CommandPanel / ColorsPane store-sync bugfix scope beyond regression gates (see bugfix ticket).
