# FEAT-20260522-registry-build-options-snapshot — feature run

Started: 2026-05-22  
Planner handoff: 2026-05-23

Ticket: `project_board/inbox/00_backlog/FEAT-20260522-registry-build-options-snapshot.md`

---

## Checkpoint — Planner (2026-05-23)

### Would have asked
Should player version rows use the same `build_options` key and `*.build_options.json` validation as enemies, or a separate key sourced from `*.player.json`?

### Assumption made
Spec Agent will define a player snapshot field (default assumption: same `build_options` object shape where applicable, validated against player export JSON schema; enemy rows use `parse_build_options_json` / sanitize path). Sidecars remain on disk for both; registry is canonical for API/UI reads.

### Confidence
Medium

---

### Would have asked
Should `schema_version` increment when adding `versions[].build_options`, or is an optional key on `schema_version: 1` sufficient?

### Assumption made
Keep `SCHEMA_VERSION = 1` with optional `build_options` on version rows unless spec documents a migration bump; backfill is idempotent merge from on-disk sidecars, not a destructive manifest rewrite.

### Confidence
High

---

### Would have asked
Where should post-run persistence attach the snapshot — inside `sync_discovered_animated_glb_versions`, a new service helper called from `run.py`, or a dedicated `POST` backfill endpoint only?

### Assumption made
Primary write on successful animated run: extend post-run sync path (`_sync_registry_for_family` + service) to attach snapshot from the run’s resolved `build_options` JSON or freshly written sidecar for the new `output_file` stem. Backfill for legacy rows runs in discover-sync or a spec-defined one-shot helper (idempotent).

### Confidence
Medium

---

### Dependency note (non-blocking)
`project_board/bugfix/in_progress/model-load-ui-settings.md` is **in_progress**, not `done/`. Not an umbrella child ticket. Execution plan requires preserving preview-only semantics from working-tree fix; Spec must cross-reference REQ-1/REQ-2 in that bug doc.

---

## Checkpoint — Spec Agent (2026-05-23)

### Would have asked
Should PATCH endpoints accept client-supplied `build_options` for manual correction?

### Assumption made
**No.** PATCH bodies remain `draft` / `in_use` / `name` / `tags` only; snapshots are written by export, post-run attach, and idempotent `sync_discovered_*` backfill. PATCH must preserve existing snapshots.

### Confidence
High

---

### Would have asked
For legacy player exports with only `*.player.json`, should backfill synthesize a minimal snapshot from filename color?

### Assumption made
**No synthesis.** Player backfill reads `*.build_options.json` only (new sidecar after R6). Legacy rows stay without registry snapshot until re-export or sidecar appears.

### Confidence
High

---

### Would have asked
When registry snapshot and sidecar disagree, which wins on explicit import?

### Assumption made
**Registry canonical** when `build_options` present on row; sidecar used only when registry field absent (R2).

### Confidence
High

---

### Spec output
`project_board/specs/FEAT-20260522_registry_build_options_snapshot_spec.md` — `schema_version` stays **1**; player field name **`build_options`**; player validation via **`coerce_validate_enemy_build_options("player_slime", …)`**; new player **`*.build_options.json`** export sidecar for backfill/portability.

---

## Checkpoint — Test Designer (2026-05-23)

### Deliverables
- Python RED: `test_version_row_build_options_schema.py`, `test_sync_discovered_build_options_backfill.py`, `test_attach_build_options_to_version.py`
- Backend RED: `test_registry_build_options_exposure.py`
- API RED: `test_registry_build_options_contract.py`
- Frontend RED: `useAppStore.buildOptionsHydration.test.ts`; preview-only regression `useAppStore.selectAssetByPath.previewOnly.test.ts` **green**

### Targeted run summary (RED expected)

**Python** (`uv run pytest` model_registry + attach): **11 failed, 4 passed**

```
ValueError: enemies['spider'].versions[0] unexpected keys: ['build_options']
ImportError: cannot import name 'attach_build_options_to_version_by_path' from 'src.model_registry.service'
KeyError: 'build_options'  # sync backfill not implemented
pytest.fail: attach_build_options_to_version_by_path is not implemented on model_registry.service
```

**Backend** (`uv run pytest tests/test_registry_build_options_exposure.py`): **2 failed, 1 passed**

```
assert 500 == 200
WARNING registry get: validation error — enemies['imp'].versions[0] unexpected keys: ['build_options']
KeyError: 'build_options'  # load_existing/open
```

**API contract** (`tests/api/test_registry_build_options_contract.py`): **2 failed**

```
AssertionError: expected status 200, got 500: {"detail":"enemies['imp'].versions[0] unexpected keys: ['build_options']"}
KeyError: 'build_options'
```

**Frontend** (`npm test` hydration + previewOnly): **2 failed, 2 passed**

```
AssertionError: expected 3 to be 99  # registry-first not implemented; sidecar wins
useAppStore.selectAssetByPath.previewOnly.test.ts: 1 passed (REQ-1 regression green)
```

### Handoff
`handoff-latest.yaml` test_designer → test_breaker; ticket Stage **TEST_BREAK**, Revision **3**.

---

## Checkpoint — Test Breaker (2026-05-23)

### New adversarial test files (no ticket id in filenames)

| File | Matrix coverage |
|------|-----------------|
| `asset_generation/python/tests/model_registry/test_version_row_build_options_adversarial.py` | Null/empty/type, player_slime coercion, UTF-8 cap boundary, PATCH key rejection (service) |
| `asset_generation/python/tests/model_registry/test_sync_discovered_build_options_adversarial.py` | Dual-miss (no registry + no sidecar), corrupt sidecar, invalid coercion, player parity |
| `asset_generation/python/tests/api/test_registry_build_options_contract_adversarial.py` | Oversized on-disk manifest → GET 500, player `load_existing/open` |
| `asset_generation/web/backend/tests/test_registry_build_options_patch_adversarial.py` | PATCH must not accept client `build_options` (HTTP preserve canonical) |
| `asset_generation/web/backend/tests/test_registry_build_options_exposure_adversarial.py` | Player GET row, path-kind open without registry row |
| `asset_generation/web/frontend/src/store/useAppStore.buildOptionsHydration.adversarial.test.ts` | Player registry-first, dual-miss no-op, registry beats sidecar |

### Targeted run summary (RED expected pre-implementation)

**Python adversarial** (`uv run pytest` new model_registry + api adversarial modules): **14 passed, 6 failed**

```
ValueError: enemies['spider'].versions[0] unexpected keys: ['build_options']
KeyError: 'build_options'  # player sync backfill + player open contract
```

**GREEN (service layer today):** `test_patch_enemy_version_rejects_client_build_options_key`, `test_patch_player_version_rejects_client_build_options_key`

**Backend adversarial** (`uv run pytest` patch + exposure adversarial): **1 passed, 3 failed**

```
AssertionError: assert None == 7  # PATCH with build_options on disk row — manifest load rejects key before preserve assertion
assert 400 == 200  # mixed draft + build_options PATCH while manifest invalid
assert 500 == 200  # GET player row with build_options
```

**Frontend adversarial** (`npm test` adversarial hydration): **1 passed, 3 failed**

```
Expected eye_count 5 / 6 / 9 — received 1 / 1 (registry-first not implemented; sidecar mock null)
```

### Handoff
`handoff-latest.yaml` test_breaker → implementation (Generalist phase 1, Frontend phase 2). Ticket Stage **IMPLEMENTATION_BACKEND**, Revision **4**.
