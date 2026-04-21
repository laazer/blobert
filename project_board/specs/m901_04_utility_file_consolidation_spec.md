# M901-04 — Utility File Consolidation (Functional & Non-Functional Specification)

**Ticket:** `project_board/901_milestone_901_asset_generation_refactoring/ready/04_utility_file_consolidation.md`  
**Spec exit gate type:** `generic`  
**Gating dependencies:** M901-01 Import standardization — satisfied. M901-06 Animated build options consolidation — **not** a hard gate; this spec defines the API boundary and sequencing rules.

---

## Deferred Boundary Statement

- **In scope for M901-04:** Restructuring `asset_generation/python/src/utils/` so that **constants/configuration**, **export naming and paths**, **shared non-domain validation helpers**, and the **animated build options public surface** have clear module boundaries, with imports updated project-wide under `asset_generation/python` and `asset_generation/web` where they reference `src.utils.*`.
- **Shared with M901-06:** The **internal** decomposition of animated build options into `schema.py` / `validate.py` (per ticket 06) is **owned by M901-06**. M901-04 establishes the **`src.utils.build_options` package** as the **only** stable consumer import path and permits either (a) moving existing `animated_build_options*.py` sources under `utils/build_options/` unchanged until 06 refactors them, or (b) landing 06 first and having M901-04 wire `__init__.py` re-exports — **provided** the public API and behavior in §R5 remain unchanged.
- **Out of scope:** Changing procedural mesh/material algorithms, HTTP response shapes, registry semantics, or Godot/web filename parsing rules beyond preserving existing Python-side stems and directory names.

---

## Requirement R1 — Module layout, layering, and line-count policy

### 1. Spec Summary

- **Description:** After this work, the `utils/` area must present a **small set of top-level modules** with explicit responsibilities. New or merged modules **`config.py`**, **`export.py`**, and **`validation.py`** are introduced. **`materials.py`** and **`simple_viewer.py`** remain as today (viewer unchanged per ticket). **`src.utils.build_options`** is delivered as a **package** (`utils/build_options/` with `__init__.py`), not a parallel duplicate `build_options.py` file at `utils/` root (avoids ambiguous `build_options` resolution).
- **Constraints:**
  - **Directed acyclic imports (authoritative):**
    - `config` → may import stdlib, third-party, and `body_families` (same as current `constants.py`) — **must not** import `build_options`, `export`, `materials`, `validation`, or `simple_viewer`.
    - `export` → may import `config` (for `ExportConfig`, `LevelExportConfig`, `PlayerExportConfig` and related path constants), `validation` (for shared path checks), stdlib — **must not** import `build_options` or `materials`.
    - `validation` → stdlib + typing only — **must not** import `config`, `build_options`, `export`, or `materials`.
    - `materials` → **must not** import `build_options` or `export` (preserve current isolation).
    - `build_options` (package) → may import `config`, `blender_stubs`, `body_type_presets`, `placement_clustering`, and internal submodules — **must not** import `export` or `materials`.
  - **LOC guideline:** `config.py`, `export.py`, `validation.py`, `materials.py`, `simple_viewer.py`, and any **new** single-purpose helper module created under `utils/` (except the `build_options/` tree) SHOULD each stay **≤ 250 non-blank, non-pure-comment lines** as counted by `wc -l` on the file after stripping empty lines (implementation may use a slightly different local metric; CI may add a check later).
  - **`build_options/` exemption:** The **entire** `utils/build_options/` directory is **exempt** from the per-file 250 LOC cap until M901-06 completes its split; aggregate size may remain similar to today’s `animated_build_options*` total. After M901-06, individual `schema.py` / `validate.py` files SHOULD target ≤ 250 LOC per ticket 06.
- **Assumptions:** Python 3.10+ typing (`dict[str, T]`, `X | Y`). Import style follows M901-01 (`src.*` where established).
- **Scope:** `asset_generation/python/src/utils/**` and **all** Python import sites that reference migrated symbols under `asset_generation/python/**` and `asset_generation/web/**/*.py`.

### 2. Acceptance Criteria

- [ ] No import cycle: a static check (e.g. `python -c` import ordering smoke for the listed modules) passes for `config`, `export`, `validation`, `materials`, `build_options` in any order that respects the DAG above.
- [ ] No new `sys.path` hacks in `utils/` beyond what already exists project-wide (align with M901-01).

### 3. Risk & Ambiguity Analysis

- **Risk:** M901-04 and M901-06 touching the same files — **mitigation:** `build_options/__init__.py` is the **only** outward-facing contract; internal filenames may change in 06 without breaking consumers if `__all__` / documented public symbols stay stable.
- **Edge case:** `enemy_slug_registry` today **must not** import `constants` to avoid cycles — merging into `config.py` must preserve ordering so slug tuples and `ANIMATED_ENEMY_LABELS` consistency check execute **before** `EnemyTypes` methods that reference them.

### 4. Clarifying Questions

- None — preempted by checkpoint assumptions in `project_board/checkpoints/M901-04-utility-file-consolidation/2026-04-21T21-18-00Z-planning.md` and §Deferred Boundary.

---

## Requirement R2 — `config.py` (constants, enums, slug registry)

### 1. Spec Summary

- **Description:** Replace `utils/constants.py` and `utils/enemy_slug_registry.py` with a single module **`utils/config.py`** that exposes **all** symbols those two files currently expose, with **identical runtime values and behavior** (including `ANIMATED_ENEMY_LABELS` keyset guard, `animated_enemies_for_api()` ordering, `EnemyTypes.get_*()` lists, animation/export name mappings, `ExportConfig` / `LevelExportConfig` / `PlayerExportConfig`, player/level animation helpers, etc.).
- **Constraints:** Delete **`constants.py`** and **`enemy_slug_registry.py`** after migration (no duplicate definitions). Update **every** import of `src.utils.constants` or `src.utils.enemy_slug_registry` to `src.utils.config` (including relative `..utils.constants` in package code).
- **Assumptions:** No intentional behavior changes — refactor-only for this requirement.
- **Scope:** All consumers (including `export_subdir.py` logic moved to `export.py`, `model_registry/migrations.py`, `meta.py`, tests).

### 2. Acceptance Criteria

- [ ] **Symbol map (authoritative migration):**
  - From **`enemy_slug_registry.py`** → `config.py`: `ANIMATED_SLUGS`, `STATIC_SLUGS`, `ANIMATED_ENEMY_LABELS`, `animated_enemies_for_api`.
  - From **`constants.py`** → `config.py`: `EnemyTypes`, `AnimationTypes`, `AnimationConfig`, `PlayerAnimationTypes`, `PlayerAnimationConfig`, `PlayerBoneNames`, `PlayerExportConfig`, `LevelObjectTypes`, `LevelExportConfig`, `ExportConfig`, and re-exports `BoneNames`, `EnemyBodyTypes` from `body_families` (same try/except import pattern as today).
- [ ] `utils/__init__.py` MUST be updated to import re-exports from `config` instead of `constants` (see R8).
- [ ] Contract test `tests/utils/test_enemy_slug_registry_contract.py` (or successor name) continues to validate slug/label invariants against **`config`** imports.

### 3. Risk & Ambiguity Analysis

- **Risk:** Typing drift — **mitigation:** replace `Dict`/`List` with `dict`/`list` builtins and `dict[str, T]` where values are homogeneous (R9).

### 4. Clarifying Questions

- None.

---

## Requirement R3 — `export.py` (naming, directories, GLB path validation, I/O helpers)

### 1. Spec Summary

- **Description:** Consolidate **`export_naming.py`** and **`export_subdir.py`** into **`utils/export.py`**. Centralize **animated stem naming**, **draft/start-index environment behavior**, and **shared GLB path checks** used by the export pipeline. Add **`validate_glb_path`** (name per ticket: “GLB validation”) as a **single** canonical helper for “is this a plausible readable `.glb` path for our pipeline” used by new call sites in this refactor (existing `model_registry` checks may remain until a future consolidation ticket unless a no-behavior-change extraction is trivial).
- **Constraints:**
  - **`animated_export_stem(enemy_type, variant_index, *, prefab_name=None)`** — preserve signature and string format exactly (including zero-padded variant).
  - **`variant_start_index`**, **`animated_export_directory`**, **`player_export_directory`**, **`level_export_directory`** — preserve environment variables `BLOBERT_EXPORT_USE_DRAFT_SUBDIR` and `BLOBERT_EXPORT_START_INDEX` semantics exactly.
  - **`validate_glb_path(path: str | os.PathLike[str])` → `Path` (or documented return type)** MUST: resolve to a `Path`; **raise `ValueError`** (or `FileNotFoundError` only when the spec’d contract chooses one — pick **`ValueError`** with a clear message for “not a file / wrong suffix / empty”) when the path is not a non-empty existing file whose suffix is `.glb` (case-insensitive). **Idempotent** for the same path.
  - **Delete** `export_naming.py` and `export_subdir.py` after migration.
- **Assumptions:** `export_manifest_entry()` is **not** present in the codebase today; **optional** helper with that name MAY be added only if it deduplicates real manifest row construction **without** changing registry JSON shapes — otherwise **omit** and treat the ticket table row as aspirational / deferred.
- **Scope:** Generator, player/level generators, tests `test_export_naming.py`, `test_export_subdir.py`, and any other `export_*` imports.

### 2. Acceptance Criteria

- [ ] All previous imports of `src.utils.export_naming` / `src.utils.export_subdir` point to `src.utils.export`.
- [ ] Comments in `ExportConfig` that reference `utils.export_naming` are updated to reference `utils.export`.
- [ ] At least one **behavior-first** test exercises `validate_glb_path` on: missing file, wrong suffix, and a minimal empty/temp `.glb` file that passes (create temp file in test).

### 3. Risk & Ambiguity Analysis

- **Edge case:** Draft subdir concatenation must remain identical on POSIX paths (use `os.path.join` as today).

### 4. Clarifying Questions

- None.

---

## Requirement R4 — `validation.py` (shared helpers)

### 1. Spec Summary

- **Description:** Introduce **`utils/validation.py`** containing **generic** validation/coercion helpers **not** tied exclusively to materials or animated build options. Initial contents MUST include **`clamp01`** moved from **`placement_clustering.py`** implementation (or duplicated then deleted — single canonical definition in `validation.py`). **`placement_clustering.py`** MUST import `clamp01` from `validation` and re-export if needed for backward compatibility during migration, then **all** imports SHOULD resolve to `validation.clamp01` for new code.
- **Constraints:** `validation.py` MUST NOT contain spider/eye/build-option rules, material finish lists, or mesh keys — those stay in `build_options` or `materials`.
- **Optional consolidation:** **`validate_enum_value(value, allowed: frozenset[str] | tuple[str, ...], *, label: str)`**-style helper MAY be added if it removes duplicate string checks — **not** required if no clear duplication is found.
- **Assumptions:** `body_type_presets.py` remains a **separate** module (domain-specific geometry presets); not forced into `validation.py` for M901-04.
- **Scope:** `placement_clustering.py`, any small numeric coercion duplicated elsewhere identified during implementation.

### 2. Acceptance Criteria

- [ ] `validation.py` exists and is imported by at least `placement_clustering` (for `clamp01`) and **does not** introduce cycles (R1).
- [ ] Existing tests for placement clustering still pass without behavior change to sampling distributions.

### 3. Risk & Ambiguity Analysis

- **Risk:** Moving `clamp01` changes import paths — **mitigation:** update tests only if they imported `clamp01` from `placement_clustering` explicitly (preserve re-export temporarily if needed).

### 4. Clarifying Questions

- None.

---

## Requirement R5 — `build_options` package (animated build options public API)

### 1. Spec Summary

- **Description:** Replace the **`animated_build_options*.py`** top-level cluster with a **`utils/build_options/`** package. The **only** supported import path for consumers is **`src.utils.build_options`** (and `from src.utils import build_options` if re-exported). The **runtime behavior** of `options_for_enemy`, `parse_build_options_json`, `animated_build_controls_for_api`, `OFFSET_XYZ_MIN` / `OFFSET_XYZ_MAX`, and any **module-level attributes** tests introspect via `import src.utils.animated_build_options as abo` / `hasattr(abo, "_tail_control_defs")` MUST remain **observably equivalent** after updating test import paths to `build_options` (same attribute names on the **`build_options` package object** / `__init__.py` surface).
- **Constraints:**
  - **Delete** (or relocate under `build_options/`) these files: `animated_build_options.py`, `animated_build_options_appendage_defs.py`, `animated_build_options_mesh_controls.py`, `animated_build_options_validate.py`, `animated_build_options_zone_texture.py`, `animated_build_options_spider_eye.py`, `animated_build_options_part_feature_defs.py` — **no** stray `animated_build_options*.py` remain at `utils/` root after completion.
  - **M901-06 alignment:** If M901-06 lands in the same timeframe, `utils/build_options/schema.py` and `utils/build_options/validate.py` **replace** ad-hoc filenames **inside** the package; `__init__.py` MUST re-export the public API. If M901-06 is not yet merged, implementation MAY keep internal module names temporarily **inside** `build_options/` with the same graph as today (no circular imports).
- **Assumptions:** Backend `meta.py` and all tests update imports from `src.utils.animated_build_options` to `src.utils.build_options`.
- **Scope:** All references in repo from grep `animated_build_options`.

### 2. Acceptance Criteria

- [ ] `from src.utils.build_options import options_for_enemy, parse_build_options_json, animated_build_controls_for_api, OFFSET_XYZ_MIN, OFFSET_XYZ_MAX` succeeds.
- [ ] Tests that previously imported `src.utils.animated_build_options` are updated and still validate the same behaviors (defaults, coercion, API payload shape for `animated_build_controls_for_api()`).
- [ ] No `from src.utils.animated_build_options` imports remain in `asset_generation/python` or `asset_generation/web`.

### 3. Risk & Ambiguity Analysis

- **Risk:** Internal import cycle (`animated_build_options_validate` vs main module) — **mitigation:** preserve lazy import pattern inside package with **behavior unchanged**.

### 4. Clarifying Questions

- None.

---

## Requirement R6 — Modules explicitly retained (non-goals for deletion)

### 1. Spec Summary

- **Description:** The following remain **separate files** with **no functional requirement to merge** them into `config` / `export` / `validation` for this ticket: **`simple_viewer.py`** (unchanged per ticket), **`materials.py`**, **`blender_stubs.py`**, **`body_type_presets.py`**, **`placement_clustering.py`** (minus moved `clamp01` per R4), **`texture_asset_loader.py`**.
- **Constraints:** `simple_viewer.py` content MUST NOT change except accidental whitespace from mass-edit — **prefer zero edits**.
- **Assumptions:** “Orphaned” means **no importers** — `demo.py` is treated as orphan (see R7).
- **Scope:** File retention only.

### 2. Acceptance Criteria

- [ ] `simple_viewer.py` is still runnable under Blender as documented in its docstring (manual smoke optional; automated guard = file unchanged or hash-equivalent per git for non-touched lines).

### 3. Risk & Ambiguity Analysis

- **Edge case:** If `demo.py` is found to be imported dynamically — implementation MUST grep before delete.

### 4. Clarifying Questions

- None.

---

## Requirement R7 — Orphan removal

### 1. Spec Summary

- **Description:** **`utils/demo.py`** MUST be **deleted** if **no** references exist in `asset_generation/python` tests or production code (current expectation: unused). If any reference appears, replace with a pointer to `config`/`materials` docs in code comments and then delete only after updating the caller.
- **Constraints:** No orphan `.py` files left under `utils/` that are unreferenced **except** intentional `__init__.py` and retained modules in R6/R5.

### 2. Acceptance Criteria

- [ ] Grep-based audit shows no import of `utils.demo` or `src.utils.demo`.

### 3. Risk & Ambiguity Analysis

- **Low risk:** Demo was example-only.

### 4. Clarifying Questions

- None.

---

## Requirement R8 — `utils/__init__.py` public surface

### 1. Spec Summary

- **Description:** Update **`utils/__init__.py`** to re-export the same **logical** public constants as today, but sourced from **`config`** instead of **`constants`**. If **`build_options`** is added to `__all__`, document explicitly; default is **do not** star-export build_options from `utils` package root unless already conventional (today it does not export animated build options — **preserve** that: consumers use `src.utils.build_options` directly).
- **Constraints:** `__all__` lists remain intentional; no wildcard imports of `build_options`.

### 2. Acceptance Criteria

- [ ] `from src.utils import EnemyTypes, AnimationTypes, EnemyBodyTypes, BoneNames, AnimationConfig, ExportConfig, MaterialColors, ...` continues to work with the same names as `__init__.py` currently exports.

### 3. Risk & Ambiguity Analysis

- **Risk:** Missing re-export — **mitigation:** compare `__all__` before/after.

### 4. Clarifying Questions

- None.

---

## Requirement R9 — Non-functional: typing, tests, coverage

### 1. Spec Summary

- **Description:** In **new or heavily edited** files under this ticket, avoid bare `dict` / `list` in annotations — use `dict[str, T]`, `list[T]`, or `TypedDict` where structure is stable. Replace legacy `Dict`/`List` from `typing` in touched lines when practical. **No** new `Any`-only public APIs without justification in code review.
- **Constraints:** Full **`pytest`** suite for `asset_generation/python` passes. After Python changes, run **`bash ci/scripts/diff_cover_preflight.sh`** when `.py` files under `asset_generation/python` change (per workflow).
- **Assumptions:** CI-equivalent commands run locally or in pipeline.

### 2. Acceptance Criteria

- [ ] No dangling imports: `python -m compileall` or project-standard import smoke passes for `asset_generation/python`.
- [ ] Test suite green; diff-cover preflight passes threshold when triggered for this change set.

### 3. Risk & Ambiguity Analysis

- **Risk:** Large mechanical diff — rely on tests + grep for `animated_build_options` / old module names.

### 4. Clarifying Questions

- None.

---

## Traceability — Ticket acceptance criteria mapping

| Ticket AC | Spec coverage |
|-----------|----------------|
| `config.py` — constants, enums, EnemyTypes, etc. | R2 |
| `build_options.py` / refactor — schema + validation surface | R5 (+ Deferred Boundary with M901-06) |
| `export.py` — naming, GLB validation, I/O | R3 |
| `validation.py` — shared helpers | R4 |
| `simple_viewer.py` keep | R6 |
| Orphans consolidated/deleted | R7, R5 (remove old animated_* files) |
| Imports updated | R2, R3, R5, R8 |
| Tests pass | R9 |
| Type hints improved | R9 |

---

## Explicit forbidden patterns

- Importing `build_options` from `config` or `validation`.
- Leaving `src.utils.constants` or `src.utils.enemy_slug_registry` import paths after completion.
- Leaving any `utils/animated_build_options*.py` file at `utils/` root after completion.
- Prose-only tests that assert ticket wording under `project_board/**` as the sole correctness signal (workflow guardrail).
