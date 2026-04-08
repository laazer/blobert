# Spec: Model registry, draft versions, editor contract, and spawn integration

**Ticket:** `project_board/9_milestone_9_enemy_player_model_visual_polish/backlog/01_spec_model_registry_draft_versions_and_editor_contract.md`  
**Spec path (stable):** `project_board/specs/model_registry_draft_versions_spec.md`  
**Spec ID prefix:** MRVC  
**Date:** 2026-04-08  
**Last Updated By:** Spec Agent (autopilot)

---

## Overview

This document is the **authoritative data and UX contract** for:

- A **versioned visual registry** for enemies (many GLBs per gameplay type) and a **single active** player visual.
- **Draft** vs **in-use** (spawn pool / game-active) semantics, **promotion** and **demotion**.
- **Canonical filesystem roots** and an explicit **denylist** for editor and automation surfaces.
- **Deletion** rules (draft vs in-use, sole-version guard).
- **Spawn integration** — interface only; concrete wiring is owned by milestone work (including `08_runtime_spawn_random_enemy_visual_variant.md` and procedural milestone hooks).

**Downstream implementation tickets (must not need to reopen this contract):**

| Ticket | Scope |
|--------|--------|
| `04_editor_ui_draft_status_for_exports.md` | UI for marking/clearing draft on exports |
| `05_editor_ui_game_model_selection.md` | Player active path + enemy pool slots |
| `06_editor_load_existing_models_allowlist.md` | Browse/load only under allowlist |
| `07_editor_delete_draft_and_in_use_models.md` | Delete flows per matrix below |
| `08_runtime_spawn_random_enemy_visual_variant.md` | Runtime selection among in-use versions |
| `09_automated_tests_registry_allowlist_delete.md` | Automated tests for allowlist + deletion |

**Related specs:** `project_board/specs/assets_router_and_glb_viewer_spec.md` (ARGLB) defines backend list/serve roots; this spec **narrows** what the **registry** and **game/editor** may treat as first-class model paths.

---

## Traceability (ticket acceptance criteria)

| Ticket AC | Spec coverage |
|-----------|----------------|
| Spec file under `project_board/specs/` with stable filename | This document path |
| UI surfaces, persistence, migration from single GLB | MRVC-5, MRVC-6, MRVC-7, MRVC-10 |
| ADRs for ambiguous choices | **Architecture Decision Records** |
| Downstream `04`–`09` implementable without contract churn | Overview table + MRVC-1–MRVC-12 |

---

## Architecture Decision Records

### ADR-001 — Single manifest file vs sidecar JSON per GLB

- **Decision:** Persist the registry as **one** JSON document: `asset_generation/python/model_registry.json` (same parent directory as canonical export folders `animated_exports/`, `exports/`, `player_exports/`, `level_exports/`).
- **Rationale:** One diff-friendly source for version lists and flags; editor backend can read/write atomically; avoids orphan sidecars when GLBs are renamed.
- **Rejected alternative:** Per-GLB `*.meta.json` next to each file — higher filesystem churn and harder to query “all in-use versions for family X”.

### ADR-002 — Path encoding inside the manifest

- **Decision:** All file references in the manifest are **POSIX paths relative to `asset_generation/python/`** (the same `python_root` as `asset_generation/web/backend/core/config.py` and ARGLB). They use only forward slashes, have no `..` segments, and **must** start with one of the **allowlisted root prefixes** (MRVC-3).
- **Rationale:** Matches ARGLB list/serve `path` values (`animated_exports/foo.glb`). Godot consumers map to `res://asset_generation/python/<path>` by prepending a fixed prefix.
- **Rejected alternative:** Absolute filesystem paths — breaks clones and CI.

### ADR-003 — Player “exactly one active” semantics

- **Decision:** The manifest holds **at most one** `player_active_visual` record (nullable). Setting a new active path **replaces** the previous active path for game load purposes; the prior path remains on disk unless explicitly deleted per MRVC-9.
- **Rationale:** Matches umbrella ticket “full replacement” semantics.

---

## Requirement MRVC-1 — Schema: top-level shape

### 1. Spec summary

- **Description:** `model_registry.json` is a JSON object with **exactly** these top-level keys:
  - `"schema_version"` — integer, currently `1`.
  - `"enemies"` — object map: keys are **enemy family slugs** (non-empty strings, stable identifiers aligned with Python `EnemyTypes` / generated scene families, e.g. `acid_spitter`, `tar_slug`).
  - `"player_active_visual"` — either `null` or an object (MRVC-2).
- **Constraints:** No additional top-level keys in v1. Extensibility requires bumping `schema_version` and a spec revision.
- **Scope:** Serialization only; UI copy is MRVC-5–MRVC-7.

### 2. Acceptance criteria

- **MRVC-1.1:** A conforming file parses as JSON and contains keys `schema_version`, `enemies`, `player_active_visual` only at the top level.
- **MRVC-1.2:** `schema_version` equals `1` for all implementations until a deliberate migration.

---

## Requirement MRVC-2 — Enemy version entry and player active object

### 1. Spec summary

- **Enemy version entry** (elements of per-family arrays under `enemies[<slug>].versions`):

| Field | Type | Meaning |
|-------|------|--------|
| `id` | string | Stable unique id **within** the family (e.g. `v0`, `v1`, UUID, or filename stem). Used for UI and deletion targeting. |
| `path` | string | Repo-relative path; must satisfy MRVC-3. |
| `draft` | boolean | If `true`, entry **must not** appear in default spawn pools or default player selection. |
| `in_use` | boolean | If `true`, entry is eligible for **game spawn pool** (enemies) or is a candidate set for validation; for enemies, only non-draft `in_use` entries are spawn-eligible (MRVC-4). |

- **Player active object** (`player_active_visual` when not null):

| Field | Type | Meaning |
|-------|------|--------|
| `path` | string | Repo-relative path under allowlist; the **single** active player visual. |
| `draft` | boolean | If `true`, game **must not** load this path as the default player visual until promoted (`draft: false`). |

- **Constraints:** `draft: true` implies **not** spawn-eligible and **not** default player visual even if `in_use` is true; implementations **must** treat `draft && in_use` as **invalid** for enemies and **normalize or reject** on load (ticket `09` tests). For player, `draft` on the sole active record means “no default in-game visual until promoted.”

### 2. Acceptance criteria

- **MRVC-2.1:** Enemy entries carry `id`, `path`, `draft`, `in_use` as specified.
- **MRVC-2.2:** Invalid combinations are rejected or repaired per validation rules in MRVC-8.

---

## Requirement MRVC-3 — Canonical allowlist roots and denylist

### 1. Spec summary

- **Allowlist (prefixes for `path`, relative to `python_root`):** Paths **must** begin with one of:
  - `animated_exports/`
  - `exports/`
  - `player_exports/`
  - `level_exports/`

- **Denylist — editor and registry writers must never offer or persist:**
  - Paths that escape `python_root` (e.g. `..` segments), absolute paths, or prefixes outside the four roots above (e.g. `concept_art/`, `reference_projects/`, `.git/`).
  - File types other than `.glb` for **visual** slots (companion `.attacks.json` is not a visual slot; do not register as player/enemy visual `path`).
  - Bare filenames with no allowlisted prefix.

- **Editor behavior:** File pickers and “load existing” flows (ticket `06`) list only assets that resolve under allowlist **and** appear in registry or on-disk scan **limited to** those directories—**no** free-form path text entry that bypasses validation.

### 2. Acceptance criteria

- **MRVC-3.1:** Any persisted `path` fails validation if it does not start with an allowlisted prefix.
- **MRVC-3.2:** Traversal (`..`) and absolute paths are rejected.

---

## Requirement MRVC-4 — Promotion, demotion, and spawn eligibility

### 1. Spec summary

- **Promotion (draft → in-use for enemies):** Set `draft` to `false`. Optionally set `in_use` to `true` in the same operation when adding to spawn pool.
- **Demotion (in-use → draft):** Set `draft` to `true` and `in_use` to `false` for enemies so the version leaves the spawn pool but remains on disk and in the registry for editing.
- **Spawn eligibility:** For family `F`, the default uniform random pool is the set of versions where `draft == false` **and** `in_use == true` **and** `path` validates (MRVC-3). If the set is empty, spawn code **must** fall back per MRVC-11.

### 2. Acceptance criteria

- **MRVC-4.1:** Promoted entries become spawn-eligible; demoted entries are excluded from the default pool.
- **MRVC-4.2:** Draft entries never appear in the default pool.

---

## Requirement MRVC-5 — UI surfaces (editor and game-facing toggles)

### 1. Spec summary

- **Editor (M21):** Surfaces for draft flag, promotion/demotion, player active selection, and deletion (tickets `04`, `05`, `07`) **read and write** `model_registry.json` through validated APIs (no raw JSON in casual UI).
- **Game-facing toggles (if in scope of M9):** Any in-game “which model” UI **must** reflect the same manifest fields; no second source of truth. If in-game UI is deferred, ticket `05` still owns editor-side persistence so runtime can read one file later.

### 2. Acceptance criteria

- **MRVC-5.1:** Editor actions that change draft/in-use/player active persist to `model_registry.json` and pass MRVC-8 validation.

---

## Requirement MRVC-6 — Backend persistence location

### 1. Spec summary

- **Canonical file:** `asset_generation/python/model_registry.json`.
- **Atomicity:** Writers **should** use write-temp-then-rename to avoid torn reads during editor saves (implementation detail for `04`/`05`/`07`).

### 2. Acceptance criteria

- **MRVC-6.1:** Documentation and tests refer to this path unless ADR-001 is superseded by a numbered spec revision.

---

## Requirement MRVC-7 — Migration from single GLB per family

### 1. Spec summary

- **Today:** One primary animated GLB per family (e.g. `.../animated_exports/acid_spitter_animated_00.glb`).
- **Migration:** On first introduction of the registry, each known family receives `versions` with **one** entry: `id` derived from filename stem, `path` such as `animated_exports/<stem>.glb`, `draft: false`, `in_use: true`. `player_active_visual` is set to the current default player export path (e.g. under `player_exports/`) or `null` until player pipeline defines one.
- **Backward compatibility:** If the manifest file is **missing**, implementations **must** behave as today (implicit single path per family from code defaults) until the file is created—**without** treating missing file as error in production editor first run.

### 2. Acceptance criteria

- **MRVC-7.1:** Migration rules produce a valid MRVC-1 document.
- **MRVC-7.2:** Missing manifest is defined and non-fatal for initial bootstrap.

---

## Requirement MRVC-8 — Validation on read/write

### 1. Spec summary

- On **write** and **read** (eager or lazy), implementations validate:
  - JSON schema shape per MRVC-1 / MRVC-2.
  - All `path` values pass MRVC-3.
  - No duplicate `id` within a family.
  - Enemy: disallow `draft == true && in_use == true` (reject or auto-clear `in_use`).
  - Optional: `path` exists on disk for strict mode; **warn** in editor if missing, **error** on “promote to game” if strict.

### 2. Acceptance criteria

- **MRVC-8.1:** Invalid manifests are rejected with actionable errors in editor/automation contexts.

---

## Requirement MRVC-9 — Deletion matrix

### 1. Spec summary

| Case | Action | File on disk | Registry | Notes |
|------|--------|--------------|----------|--------|
| **D1 — Delete draft enemy version** | User confirms delete draft | **Delete** GLB (and optional companion JSON if orphaned) when implementation chooses “full delete”; otherwise registry-only remove | Remove version entry | Safe default: remove registry row **and** delete files under allowlist only |
| **D2 — Delete draft player candidate** | Not the active slot | Delete optional | Remove entry if stored in a draft list; player object may only hold one active — drafts for player may live as `draft: true` rows in a future `player_candidates` array **out of v1**; v1 **does not** require multiple player drafts—editor may use separate staging until spec revision | If v1 has only `player_active_visual`, “delete draft player” means clear or replace active if marked draft |
| **D3 — Delete in-use enemy version (non-sole)** | User confirms | Delete files per D1 | Remove entry; spawn pool updates immediately | No pool reassignment needed |
| **D4 — Delete in-use enemy version (sole)** | **Block** by default | No delete | No change | UI message: add another version and mark in-use, or demote gameplay to explicit fallback (out of scope for v1) — **block** is required |
| **D5 — Delete active player visual** | **Block** if it is the only resolved active path | No | No | Require assign new active first |

- **Confirmation:** D3 **must** use explicit confirmation naming the family and `id`. D1 **must** use confirmation if files are deleted.

### 2. Acceptance criteria

- **MRVC-9.1:** Sole in-use enemy version cannot be deleted without violating D4 (test in `09`).
- **MRVC-9.2:** Draft deletion removes registry row and may remove files per D1.

---

## Requirement MRVC-10 — Spawn integration hook (interface only)

### 1. Spec summary

- **Contract:** Runtime code that instantiates enemies **queries** “active visual paths for family `slug`” via a single choke point (name illustrative):  
  `resolve_enemy_visual_paths(slug: String) -> Array[String]`  
  returning `python_root`-relative paths **or** `res://` paths via a **single** documented mapper (`res://asset_generation/python/` + path), **only** from MRVC-4 eligible set.
- **Randomness:** Uniform among eligible entries unless a later spec adds weights (`schema_version` > 1).
- **Stub:** Until ticket `08` lands, sandbox may keep a single hardcoded path; behavior **must** document that it will switch to the resolver without changing MRVC-1–MRVC-9.

### 2. Acceptance criteria

- **MRVC-10.1:** Ticket `08` implements resolver behavior consistent with MRVC-4 and MRVC-11.

---

## Requirement MRVC-11 — Empty pool fallback

### 1. Spec summary

- If no spawn-eligible versions exist for a family, the resolver **must** fall back to the **legacy implicit default** path used by the project today for that family (same string as pre-registry code defaults), and **must** log or surface a **warning** once per session or per spawn wave (implementation choice).

### 2. Acceptance criteria

- **MRVC-11.1:** Empty registry / empty pool does not crash spawn; fallback is deterministic.

---

## Requirement MRVC-12 — Consistency with assets router

### 1. Spec summary

- Paths exposed to the web editor’s asset list (ARGLB) use the **same** `python_root`-relative strings as registry `path` entries for GLBs under the four export directories; registry `path` entries **must** correspond to files that could be listed under ARGLB rules for that root.

### 2. Acceptance criteria

- **MRVC-12.1:** Integration tests in `09` may cross-check a sample registry path against allowlist rules without requiring a running server.

---

## Risk and ambiguity

- **Cross-prefix:** Godot uses `res://asset_generation/python/` + manifest `path`; a **single mapping function** must be documented in ticket `08`—not duplicated ad hoc.
- **Weights / rarity:** Out of scope for v1; uniform random only.

## Clarifying questions

None for v1; supersede via ADR and `schema_version` bump.
