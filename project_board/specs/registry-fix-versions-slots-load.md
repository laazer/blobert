# Spec: Registry — multiple versions, empty slots, load existing (`registry-fix-versions-slots-load`)

**Ticket:** `project_board/inbox/in_progress/registry-fix-versions-slots-load.md`  
**Surfaces:** `asset_generation/python/src/model_registry/service.py`, `asset_generation/web/backend/routers/registry.py`, `asset_generation/web/frontend` (`SaveModelModal.tsx`, `ModelRegistryPane.tsx`, `registrySlotOps.ts`, `registryLoadExisting.ts`, `RegistryPlayerSection.tsx`, `AddEnemySlotModal.tsx`).  
**Scope:** **Enemy and player** registry families share manifest schema and HTTP patterns; both are in scope unless a requirement explicitly names one.

---

## Requirement R1 — Multi-version persistence (enemy and player)

### 1. Spec Summary

- **Description:** The manifest must support **multiple distinct `versions` rows** per enemy family and for `player`, identified by unique `id`, without overwriting or dropping unrelated rows when the user exports additional GLBs, runs discovery/sync, patches one row, or assigns slots. A new on-disk variant (e.g. `{family}_animated_01.glb` vs `_00`) must be representable as an **additional** row after `sync_discovered_animated_glb_versions` (enemy) or `sync_discovered_player_glb_versions` (player), not as a replacement of the sole row unless the user explicitly deletes the old row.
- **Constraints:** `schema_version` remains `1`. `validate_manifest` rules for duplicate `versions[].id` within a family stay strict (reject duplicates). `save_manifest_atomic` / `validate_manifest` before write remain mandatory for persisted state. Spawn pool semantics (`spawn_eligible_paths`: non-draft + in-use) are unchanged unless this ticket’s later requirements explicitly adjust eligibility for slotting only.
- **Assumptions:** Export pipeline produces allowlisted relative paths under `animated_exports/` (enemy) or `player_exports/` (player). Version `id` for animated enemies follows existing stem convention (`{family}_animated_{NN}`).
- **Scope:** Python `service.py` (load/validate/save/sync/patch), FastAPI registry router read paths, frontend save/sync/slot flows that refresh registry state.

### 2. Acceptance Criteria

1. Given a family with `versions` containing row A, after discovering and syncing a new on-disk GLB for the same family that maps to a **new** `id` and path not already in `versions`, the persisted manifest contains **both** A and the new row (order not fixed except “append” is acceptable).
2. `patch_enemy_version` / `patch_player_version` updates **only** the targeted `version_id`; other rows in the same family are byte-for-byte unchanged except for manifest-wide normalization (`sort_keys` on save may reorder JSON keys; semantic equality of other rows preserved).
3. Automated tests prove that two distinct enemy version IDs under one family can coexist after sync + save; same idea for player when two distinct `player_exports` stems are registered.

### 3. Risk & Ambiguity Analysis

- **Risk:** UI or client might replace slot arrays or refresh state in a way that **appears** to lose versions (stale client); tests should distinguish API/manifest truth from UI cache.
- **Edge case:** Same path or same `id` twice → validation error; spec does not require deduplication beyond current rules.

### 4. Clarifying Questions

- None for this requirement (multi-version persistence is fully defined above).

---

## Requirement R2 — Slot arrays: empty placeholders and PUT contract

### 1. Spec Summary

- **Description:** Slot lists (`enemies[family].slots`, `player.slots`) are ordered lists of **string** entries. The empty string `""` is a valid **placeholder** for an unassigned slot position. `put_enemy_slots` / `put_player_slots` (and HTTP `PUT .../slots`) must accept payloads that include `""` interleaved with assigned version IDs, provided global validation passes. The service must reject **only** where this spec and existing invariants require (e.g. unknown non-empty id, draft/in-use rules for assigned ids, duplicate non-empty slot ids). `version_ids` **must not** be the empty list `[]` at the API boundary (current `ValueError` behavior is **retained**).
- **Constraints:** `validate_manifest` / `_normalize_registry_family_block` already permits `""` in `slots`; duplicate `""` placeholders must not be treated as duplicate “assigned” ids (only non-empty ids participate in duplicate-slot detection). Assigned slot entries must reference an existing `versions[].id`.
- **Assumptions:** No new top-level manifest keys.
- **Scope:** `put_enemy_slots`, `put_player_slots`, `validate_manifest`, router PUT handlers, frontend slot editor state and save.

### 2. Acceptance Criteria

1. `PUT /api/registry/model/enemies/{family}/slots` with body `{"version_ids": ["", "valid_id"]}` succeeds when `valid_id` refers to a non-draft, `in_use` row, and results in persisted slots matching that order (including leading/trailing `""` where sent).
2. After `add empty slot` in the UI, the user can choose a version for that index (or save placeholders and fill later) without a **spurious** 400 solely because placeholders exist, assuming assigned ids satisfy R3.
3. `{"version_ids": []}` continues to be rejected with a client-visible 400 and a clear detail message (behavior preserved).
4. Tests cover at least one payload with multiple `""` and mixed assigned ids for enemy; player PUT mirrors the same rules if the product exposes player slot PUT in the UI or API.

### 3. Risk & Ambiguity Analysis

- **Risk:** Frontend might send `[]` when all rows removed; spec preserves rejection—UI must either forbid that state or repopulate a minimal valid list per product rules (implementer chooses with tests).
- **Edge case:** All slots `""` only: non-empty list `[""]` or `["",""]` — valid structurally; implementer ensures no accidental “empty list” coercion.

### 4. Clarifying Questions

- None.

---

## Requirement R3 — Slot eligibility: `draft`, `in_use`, and UI/API alignment

### 1. Spec Summary

- **Description:** For any **non-empty** slot entry `version_id` (not `""`), the backing version row must satisfy **`draft === false` and `in_use === true`** before `put_enemy_slots` / `put_player_slots` persist successfully. This matches current Python enforcement. The **frontend must not** present a disabled “add slot” or “save in slot” path as available when the only outcomes would be a 400 from this rule **without** a documented recovery (auto-promote, explicit button, or error text that states the exact missing flags). Specifically, **`canAddEnemySlot` (and any analogous player helper)** must use the **same** eligibility predicate as code paths that eventually call PUT slots (i.e. treat “slottable” as non-draft **and** in-use **and** not already occupying a non-placeholder slot if the product defines that). **`nextEnemySlotsAfterAdd`** and **`canAddEnemySlot`** must not disagree on what counts as an eligible candidate. `SaveModelModal` must either auto-promote to `in_use: true` (and non-draft) in a defined order before PUT, or show a **single** clear error that matches server rules (no contradictory copy). `AddEnemySlotModal` / `confirmAddEnemySlot` already patch `in_use` when needed; the spec requires that flow to remain consistent with PUT validation after any refactor.
- **Constraints:** No change to `spawn_eligible_paths` MRVC-4 definition. Promoting `in_use` for slotting does not imply changing draft without user intent—default remains: user actions that “add to spawn slots” may set `in_use` true together with non-draft per existing `patch_enemy_version` coercion rules.
- **Assumptions:** Discovery continues to insert new rows as `draft: true`, `in_use: false`; user or automation promotes before slotting.
- **Scope:** `registrySlotOps.ts`, `ModelRegistryPane.tsx`, `SaveModelModal.tsx`, `AddEnemySlotModal.tsx`, Python `put_*_slots`, tests.

### 2. Acceptance Criteria

1. For a family where the only unsynced row is `draft: true`, the UI does not show “add slot” as enabled **unless** the flow includes promotion (sync modal + pick + patch) such that PUT will succeed; after promotion, PUT succeeds.
2. For any version that is non-draft but `in_use: false`, if the UI offers “save in new slot” / “add slot” for that version, the client **either** patches `in_use: true` before PUT **or** disables the control with copy explaining that the version must be in the spawn pool.
3. Unit tests on `canAddEnemySlot` / `nextEnemySlotsAfterAdd` encode the **same** eligibility rules (update existing tests in `registrySlotOps.test.ts` / `ModelRegistryPane.slot_contract.test.ts` accordingly).
4. Server-side tests remain for `put_enemy_slots` rejecting draft or non-in-use assigned ids with stable error messages.

### 3. Risk & Ambiguity Analysis

- **Risk:** Auto-promote might surprise users; mitigated by UI copy in `AddEnemySlotModal` style (“will enable when added”) and consistent Save modal behavior.
- **Edge case:** Duplicate assignment of same version in two non-placeholder slots — still rejected by validation; unchanged.

### 4. Clarifying Questions

- None.

---

## Requirement R4 — Load existing registry models (candidates + open)

### 1. Spec Summary

- **Description:** Users can load an existing registry-backed GLB into the editor preview through a **short, documented** flow in the Registry tab: (1) open Registry pane (data loads `GET /api/registry/model` and `GET .../load_existing/candidates`), (2) optionally filter by type/family, (3) select a candidate, (4) invoke open (`POST /api/registry/model/load_existing/open`) and show the model in preview via the same mechanism as today (`selectAssetByPath` with canonical path). **Candidates** include any version row where `draft is True` **or** `in_use is True` (per router filtering logic), with allowlisted normalized paths. **404** when the file is missing on disk must surface a readable error (existing `registry target file not found` or improved copy); **400** for malformed payloads must remain distinct.
- **Constraints:** Path allowlisting and traversal rules in `registry.py` unchanged. Candidate listing uses canonical checkout read rules consistent with tests.
- **Assumptions:** Asset URL / preview bridge accepts the relative paths returned by open.
- **Scope:** `registry.py` (`get_load_existing_candidates`, `open_load_existing`), `registryLoadExisting.ts`, `RegistryPlayerSection` / pane wiring.

### 2. Acceptance Criteria

1. With at least one valid enemy row in the registry and file on disk, the candidate appears in the dropdown (or list) after refresh; choosing it and confirming open loads without manual URL editing.
2. Player rows appear when `player.versions` is populated (or legacy `player_active_visual` only) per existing router helpers.
3. Empty candidate set shows existing empty-state copy (`LOAD_EXISTING_EMPTY_COPY` or successor); no uncaught exception.
4. Backend tests: candidates shape `{ kind, family?, version_id, path }` stable; open returns canonical path.
5. Frontend tests: filter + selection + open request shape (mocked fetch) match spec.

### 3. Risk & Ambiguity Analysis

- **Risk:** Unvalidated registry read for candidates vs validated `get_model_registry` could diverge; acceptable if documented—tests should use realistic JSON.
- **Edge case:** Legacy-only `player_active_visual` must still produce a player candidate.

### 4. Clarifying Questions

- None.

---

## Requirement R5 — Non-functional: atomicity, errors, testing

### 1. Spec Summary

- **Description:** All writes to `model_registry.json` go through **`save_manifest_atomic`** after **`validate_manifest`**. No partial-file observers should see corrupt JSON mid-write. HTTP status codes: **400** validation/client errors, **404** missing family/version/target file, **409** reserved for documented conflicts (e.g. delete sole in-use), **503** import/service failures. Pydantic request bodies remain strict per project Python guidelines. Automated tests must cover: `validate_manifest` slot arrays with `""`; `put_enemy_slots` / `put_player_slots` success and failure cases; `sync_discovered_*` append behavior; router endpoints above; frontend slot/load-existing behaviors per R3–R4. Full Godot suite stays green when Godot paths are untouched.
- **Constraints:** Do not weaken atomic write or allowlist rules. Do not add Godot coupling to Python tests.
- **Assumptions:** CI already runs Python, backend, and frontend tests in separate tasks; this ticket adds or extends tests only under existing layouts (`asset_generation/python/tests/`, `asset_generation/web/backend/tests/`, `asset_generation/web/frontend/**/*.test.ts*`).
- **Scope:** CI-relevant test locations only.

### 2. Acceptance Criteria

1. Every new behavioral rule in R1–R4 has at least one automated test (Python and/or TS as appropriate).
2. `bash .lefthook/scripts/py-tests.sh` (or project-canonical Python test entry) passes after implementation.
3. Frontend `npm test` passes for touched components/utilities.
4. No regression in delete/slot invariants explicitly called out in the ticket (sole in-use delete still 409).

### 3. Risk & Ambiguity Analysis

- **Risk:** Temp `python_root` in tests vs canonical import path—follow existing `settings.python_root` patterns in `registry.py` tests.

### 4. Clarifying Questions

- None.

---

## API contract summary (implementer checklist)

| Operation | Method / path | Body / params | Success | Failure |
|-----------|----------------|---------------|---------|---------|
| Full manifest | `GET /api/registry/model` | — | 200 JSON validated manifest | 500/503 |
| Enemy slots | `GET /api/registry/model/enemies/{family}/slots` | — | `{ family, version_ids, resolved_paths }` | 404 unknown family |
| Put enemy slots | `PUT /api/registry/model/enemies/{family}/slots` | `{ "version_ids": string[] }` non-empty | Same shape as GET | 400 invalid / draft-in-slot / duplicate assigned id; 404 unknown family or version id |
| Put player slots | Service `put_player_slots` exists; HTTP route may be absent today—add router + client only if UI gains player slot editing | non-empty `version_ids` | player slots payload | Same rules as enemy PUT |
| Sync enemy GLBs | `POST /api/registry/model/enemies/{family}/sync_animated_exports` | — | Updated manifest JSON | 404/400/503 |
| Candidates | `GET /api/registry/model/load_existing/candidates` | — | `{ candidates: [...] }` | 400/503 |
| Open existing | `POST /api/registry/model/load_existing/open` | `LoadExistingOpenRequest` | `{ kind, path, ... }` | 400/404/503 |

---

## Document history

| Revision | Author | Note |
|----------|--------|------|
| 1 | Spec Agent | Initial spec for `registry-fix-versions-slots-load`. |
