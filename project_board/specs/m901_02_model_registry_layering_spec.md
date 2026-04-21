# M901-02 — Model Registry Layering (Functional & Non-Functional Specification)

**Ticket:** `project_board/901_milestone_901_asset_generation_refactoring/ready/02_model_registry_layering.md`  
**Spec exit gate type:** `api` (registry exposes mutation HTTP endpoints; layering must preserve observable HTTP behavior).  
**Gating dependency:** M901-01 Import standardization — satisfied.

---

## HTTP API Contract — Endpoint Freeze

Registry HTTP surface is defined by `asset_generation/web/backend/routers/registry.py` and `asset_generation/web/backend/routers/run.py` (post-run sync only). This milestone **does not** add, remove, or rename routes or change status codes, response JSON shapes, or error `detail` strings for existing behaviors.

| Method | URI prefix | Purpose |
|--------|------------|---------|
| GET | `/api/registry/model` | Full effective manifest JSON |
| PATCH | `/api/registry/model/enemies/{family}/versions/{version_id}` | Patch enemy version flags / name |
| PATCH | `/api/registry/model/player_active_visual` | Set player primary path / draft |
| GET | `/api/registry/model/enemies/{family}/slots` | Enemy slot payload |
| PUT | `/api/registry/model/enemies/{family}/slots` | Replace enemy slot IDs |
| POST | `/api/registry/model/enemies/{family}/sync_animated_exports` | Sync discovered animated GLBs |
| GET | `/api/registry/model/player/slots` | Player slot payload |
| PUT | `/api/registry/model/player/slots` | Replace player slot IDs |
| POST | `/api/registry/model/player/sync_player_exports` | Sync discovered player GLBs |
| GET | `/api/registry/model/spawn_eligible/{family}` | MRVC-4 eligible paths |
| GET | `/api/registry/model/load_existing/candidates` | Load-existing candidates (reads unvalidated JSON + router logic) |
| POST | `/api/registry/model/load_existing/open` | Resolve identity/path |
| DELETE | `/api/registry/model/enemies/{family}/versions/{version_id}` | Delete enemy version (manifest + optional file) |
| DELETE | `/api/registry/model/player_active_visual` | Unslot active player visual |

**Deferred boundary:** `run.py` `_sync_registry_for_family` continues to call `reg.sync_discovered_animated_glb_versions(settings.python_root, family)` after import bootstrap; behavior (non-fatal warning on failure) unchanged.

---

## Validation Precedence

When a single request can fail multiple checks, **observable precedence must remain** as implemented today (refactor must not reorder checks in a way that changes which error wins).

**Router-level (unchanged):** Path normalization (`_normalize_registry_relative_glb_path`), mixed-identity validation for load-existing, confirmation text for deletes, sole in-use version guards.

**Service-backed persistence:** Operations that both mutate in-memory structures and persist must **validate after mutation** with `validate_manifest` before atomic save, matching current `patch_*` / `put_*` / `sync_*` flows. `load_effective_manifest` continues to return **validated** data (or default migrated manifest when file absent).

**Store vs schema:** Raw file read may produce invalid JSON (parse error) or non-object root — errors remain as today (`ValueError` messages from current `load_effective_manifest` / `save_manifest_atomic` semantics). **Store layer must not embed MRVC field validation**; normalization and MRVC rules stay in `schema` / `migrations` as specified below.

---

## Failure Taxonomy

| Layer | Typical exception | HTTP mapping (router) | Notes |
|-------|-------------------|-------------------------|-------|
| JSON parse / not object | `ValueError` | 500 on GET `/model` if invalid on disk; 400 where router catches | Preserve message substrings where tests assert them |
| Unknown family / version | `KeyError` | 404 | |
| Business rule / MRVC validation | `ValueError` | 400 | Includes patch key errors, empty slot lists, player draft rules |
| Import / stub setup | `ImportError` | 503 | Deferred import path in router |
| Delete: confirmation / sole version | `HTTPException` | 400 / 409 | Router-only; unchanged |

---

## Requirement R1 — Module layout and dependency graph

### 1. Spec Summary

- **Description:** Split `asset_generation/python/src/model_registry/service.py` into four modules: `schema.py`, `store.py`, `migrations.py`, and a thinner `service.py`. Each file has a single primary concern; imports form a **directed acyclic graph** with no cycles.
- **Constraints:**
  - **No new** `sys.path` manipulation in `model_registry` (align with M901-01).
  - **Four** implementation modules under `asset_generation/python/src/model_registry/` plus existing `__init__.py` (updated re-exports only as needed). No additional sibling modules unless Planner expands scope.
  - `ANIMATED_SLUGS` import (from `utils.enemy_slug_registry` / `src.utils.enemy_slug_registry` fallback) remains the single slug source for default manifest generation.
- **Assumptions:** Python 3.10+ typing (`dict[str, T]`, `X | Y`). HTTP routers stay in backend; `model_registry` stays importable from both `src.model_registry` (tests / FastAPI with `python/src` on path) and `model_registry` (backend package layout for `run.py`).
- **Scope:** `asset_generation/python/src/model_registry/**` and re-export updates in `__init__.py`. Router/run files **behavior-frozen**; **import-only** edits allowed to keep resolving `service` (same public callables).

### 2. Acceptance Criteria

- [ ] **Directed acyclic import graph (authoritative):**  
  - `service` → `schema`, `store`, `migrations`.  
  - `schema` → `migrations` (for legacy input normalization helpers used inside `validate_manifest`, and for `SCHEMA_VERSION` if that constant is owned by `migrations` — see below).  
  - `migrations` → **must not** import `schema` or `service` or `store` (prevents cycles: if `schema` imports `migrations`, then `migrations` cannot import `schema`).  
  - `store` → **no** imports from `schema`, `migrations`, or `service` (stdlib + `pathlib` only).  
  - **Single source for `SCHEMA_VERSION`:** Define it in **`migrations.py`**; **`schema.py` imports `SCHEMA_VERSION` from `migrations`** for validation checks. **`default_migrated_manifest`** remains in `migrations` and uses the same constant without cross-import to `schema`.
- [ ] A diagram or bullet list of allowed imports is documented in implementation notes (for reviewers).
- [ ] `python -c` import smoke: `from src.model_registry import service` and `from src.model_registry.service import validate_manifest, load_effective_manifest` succeed when `cwd`/PYTHONPATH match CI.

### 3. Risk & Ambiguity Analysis

- **Risk:** `validate_manifest` currently interleaves legacy player migration with validation; splitting may tempt circular imports. Mitigation: legacy **pure** transforms live in `migrations`; `schema.validate_manifest` imports them; `SCHEMA_VERSION` is owned by `migrations` so `migrations` never imports `schema`.
- **Edge case:** Dual import of `ANIMATED_SLUGS` stays in `migrations.default_migrated_manifest` (or `service` orchestration calling migrations).

### 4. Clarifying Questions

- None — resolved: **import-only** router/run edits are allowed; HTTP behavior unchanged.

---

## Requirement R2 — `schema.py` (validation and types)

### 1. Spec Summary

- **Description:** Owns MRVC validation constants (except `SCHEMA_VERSION` — see **migrations**), manifest shape typing, and **`validate_manifest(data: dict[str, Any]) -> dict[str, Any]`** with the same semantics as today (MRVC-1/2/3/8 family rules, allowlisted paths, duplicate ID/slot rules, player block normalization, derived `player_active_visual`). Houses **TypedDict** (or equivalent typing constructs) for the persisted manifest and nested row types where they improve clarity; public API remains `dict`-based at runtime for compatibility.
- **Constraints:** No filesystem I/O. Contains `_path_is_allowlisted` / family normalization helpers currently used only by validation (may remain private or be module-private with leading underscore). **No** business orchestration (patch/slot/sync) in `schema`. **May** import pure helpers from `migrations` for legacy top-level normalization **provided** `migrations` does not import `schema`.
- **Assumptions:** `ALLOWLIST_PREFIXES`, `REGISTRY_FILENAME`, and `_MAX_VERSION_NAME_LEN` (or exported constant with same value) live here; `SCHEMA_VERSION` is imported from `migrations` for equality checks; `registry_path` lives in `store` with `REGISTRY_FILENAME` from `schema` or duplicated string — document choice with no drift.
- **Scope:** Pure validation + normalization output structure.

### 2. Acceptance Criteria

- [ ] `validate_manifest` behavior is byte-for-byte equivalent for all existing tests in `asset_generation/python/tests/model_registry/` (same exceptions, same normalized output keys and coercion rules).
- [ ] TypedDict (or Protocol) definitions are added for at least: top-level manifest, enemy family block, version row (id, path, draft, in_use, optional name).
- [ ] Constants `ALLOWLIST_PREFIXES`, `REGISTRY_FILENAME` are defined once for validation; `SCHEMA_VERSION` is **not** redefined here — use `from migrations import SCHEMA_VERSION` (or equivalent) for version checks.

### 3. Risk & Ambiguity Analysis

- **Risk:** Subtle coercion of `draft`/`in_use` and slot auto-repair must not change. Regression covered by existing tests; new unit tests may target `schema` in isolation with **in-memory** dicts only.

### 4. Clarifying Questions

- None.

---

## Requirement R3 — `store.py` (persistence I/O)

### 1. Spec Summary

- **Description:** Responsible for deterministic path resolution to `model_registry.json` under `python_root`, **reading** raw file content (or signaling missing file), and **atomic write** of JSON text. May use `tempfile.mkstemp` + `os.replace` as today.
- **Constraints:** **No** MRVC validation, no migration from legacy schema — passes through **parsed** `dict` to caller or receives **pre-serialized** JSON string from caller. Caller (`service`) is responsible for calling `validate_manifest` before save.
- **Assumptions:** UTF-8 encoding; indented JSON for writes remains `json.dumps(..., indent=2, sort_keys=True) + "\n"` unless tests assert otherwise.
- **Scope:** Filesystem operations only.

### 2. Acceptance Criteria

- [ ] Missing registry file is distinguishable from empty/invalid file (same as current: missing → handled in `load_effective_manifest` orchestration).
- [ ] Atomic save: either full file replaced or previous file unchanged on failure (existing exception + temp cleanup behavior preserved).
- [ ] `registry_path(python_root: Path) -> Path` implemented here **or** in `service` as thin delegate to `store` — **one** canonical definition.

### 3. Risk & Ambiguity Analysis

- **Edge case:** Partial writes — temp file + replace pattern must remain. Adversarial tests already cover failure paths via existing suite.

### 4. Clarifying Questions

- None.

---

## Requirement R4 — `migrations.py` (version and legacy shape)

### 1. Spec Summary

- **Description:** Owns **`SCHEMA_VERSION`**, **`default_migrated_manifest()`**, legacy **`_legacy_pav_to_player_block`**, **`_derive_player_active_visual_from_block`**, and any **schema version migration** glue for future bumps. Today only version `1` is active; functions remain callable with identical outputs.
- **Constraints:** No direct file I/O. May import `ANIMATED_SLUGS`. **Must not** import `schema` (see R1 — `schema` imports from `migrations`).
- **Assumptions:** MRVC-7 default shape (enemy rows from animated slugs, empty player) unchanged.
- **Scope:** In-memory transforms only.

### 2. Acceptance Criteria

- [ ] `default_migrated_manifest()` output matches existing tests (families, paths, flags).
- [ ] Legacy PAV migration path used inside `validate_manifest` remains observably identical.

### 3. Risk & Ambiguity Analysis

- **Risk:** Duplicating slug list logic — keep single call to `ANIMATED_SLUGS` iterator.

### 4. Clarifying Questions

- None.

---

## Requirement R5 — `service.py` (orchestration and frozen surface)

### 1. Spec Summary

- **Description:** Public **business API** remains on `src.model_registry.service`: all call sites in `registry.py`, `run.py`, and tests must continue to work **without behavioral change**. Implements orchestration: load = store read → parse → `validate_manifest`; save = validate → serialize → store atomic write; patch/sync/slot/discovery functions unchanged in outcome.
- **Constraints:**  
  - **Frozen symbols** (must remain importable from `src.model_registry.service` with same signatures and semantics):  
    `registry_path`, `validate_manifest` (re-export or thin delegate to `schema` — **callers use `service.validate_manifest`** as today), `default_migrated_manifest`, `load_effective_manifest`, `save_manifest_atomic`, `patch_enemy_version`, `patch_player_active_visual`, `patch_player_version`, `get_enemy_slots`, `get_player_slots`, `put_enemy_slots`, `put_player_slots`, `sync_discovered_animated_glb_versions`, `sync_discovered_player_glb_versions`, `spawn_eligible_paths`, and test-imported **private** helpers: `_MAX_VERSION_NAME_LEN`, `_derive_player_active_visual_from_block`, `_legacy_pav_to_player_block`.  
  - `__init__.py` may continue to re-export the current subset; adding re-exports is allowed if it does not break star-import assumptions (prefer **no** removal of existing `__all__` names).
- **Assumptions:** Disk discovery (`animated_exports`, `player_exports` scans) stays in `service` (not `store`) because it is domain scanning, not single-file persistence.
- **Scope:** All procedural logic not moved to schema/store/migrations.

### 2. Acceptance Criteria

- [ ] Full pytest scope for `asset_generation/python/tests/model_registry/` passes.
- [ ] Backend tests under `asset_generation/web/backend/tests/` that touch registry pass (no 4xx/5xx regressions).
- [ ] `run.py` post-run sync still invokes `sync_discovered_animated_glb_versions` successfully when imports resolve.

### 3. Risk & Ambiguity Analysis

- **Risk:** Tests import private `_`-prefixed names — these are **compatibility requirements** for this refactor.

### 4. Clarifying Questions

- None.

---

## Requirement R6 — Typing and Pydantic policy

### 1. Spec Summary

- **Description:** Replace untyped `dict` parameters/returns with `dict[str, ...]` / TypedDict views where practical in `model_registry`. **Pydantic** models for HTTP request bodies stay in **`asset_generation/web/backend/routers/registry.py`** (existing `EnemyVersionPatch`, etc.); **do not** add a `pydantic` dependency to `asset_generation/python/src/model_registry/`. Optional shared backend schema modules are out of scope unless a follow-up ticket requests consolidation.
- **Constraints:** No behavioral change in FastAPI validation.
- **Assumptions:** Mypy/ruff may be incremental; typing improvements should not reduce runtime safety.

### 2. Acceptance Criteria

- [ ] New/edited `model_registry` modules use modern `dict[str, T]` annotations for public functions where values are homogeneous or use `Any` only at manifest boundaries.
- [ ] Router files unchanged in validation behavior; Pydantic models unchanged unless import paths require no logic edits.

### 3. Risk & Ambiguity Analysis

- **Low:** Over-strict typing on `Any`-heavy manifest could slow work — TypedDict for shapes is sufficient.

### 4. Clarifying Questions

- None.

---

## Requirement R7 — Non-functional constraints

### 1. Spec Summary

- **Description:** Each new module should target **under ~200 LOC** (soft cap per ticket planning), readable single responsibility, and test coverage **maintained or improved** (diff-cover preflight when Python under `asset_generation/python/` changes).
- **Constraints:** No circular imports; no duplicate `ALLOWLIST` definitions between backend router and `model_registry` beyond what exists today (future DRY is optional follow-up).
- **Assumptions:** CI scripts (`pytest`, `diff_cover_preflight.sh`) are authoritative.

### 2. Acceptance Criteria

- [ ] `bash ci/scripts/diff_cover_preflight.sh` passes when implementation touches `asset_generation/python/`.
- [ ] No performance regression requirement beyond current O(n) manifest sizes.

### 3. Risk & Ambiguity Analysis

- **Edge case:** Large manifests — same algorithms as today.

### 4. Clarifying Questions

- None.

---

## Consolidated traceability

| Ticket AC | Addressed by |
|-----------|----------------|
| `schema.py` new | R2 (imports `SCHEMA_VERSION` from `migrations`) |
| `store.py` new | R3 |
| `migrations.py` new | R4 |
| `service.py` refactored | R1, R5 |
| Tests pass / coverage | R5, R7 |
| Type hints | R6 |
| No circular deps | R1 |
| Routers work (import-only OK) | R1, Endpoint Freeze, R5 |
| `dict` → `dict[str, T]` / TypedDict | R2, R6 |

---

## Requirement R8 — Testing expectations (for Test Designer)

### 1. Spec Summary

- **Description:** New tests should assert **runtime behavior**: validation outcomes, atomic persistence properties, migration round-trips, and service orchestration. Avoid assertions on ticket prose or markdown. Prefer testing **public** `schema`/`store`/`migrations` surfaces **only where** they are stable contracts per this spec; otherwise test via `service` API.
- **Constraints:** Follow workflow test realism guardrails (`workflow_enforcement_v1.md`).
- **Assumptions:** Test Breaker may add adversarial cases with `# CHECKPOINT` per checkpoint protocol.

### 2. Acceptance Criteria

- [ ] Layer leakage tests (e.g. validation inside `store`) fail if boundaries violate this spec.
- [ ] No new tests that only match spec paragraph wording in `project_board/`.

### 3. Risk & Ambiguity Analysis

- **Risk:** Over-mocking filesystem — keep integration-style tests for atomic write where feasible.

### 4. Clarifying Questions

- None.

---

*End of specification — ready for `spec_completeness_check.py` and Test Design.*
