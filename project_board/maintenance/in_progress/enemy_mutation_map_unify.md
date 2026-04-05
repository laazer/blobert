# TICKET: enemy_mutation_map_unify

Title: Single source of truth for enemy family → mutation drop (Godot)

## Description

`MUTATION_BY_FAMILY` is duplicated in `scripts/asset_generation/generate_enemy_scenes.gd` and `scripts/asset_generation/load_assets.gd`. Drift between copies causes subtle bugs; adversarial tests already reference this risk (`tests/scenes/enemies/test_enemy_scene_generation_adversarial.gd`).

Extract the map to one module (e.g. `scripts/asset_generation/enemy_mutation_map.gd`) and have both scripts load it. Update any tests that assert on the dict location if needed.

## Acceptance Criteria

- Exactly one definition of the family → mutation mapping exists under `scripts/asset_generation/`.
- `generate_enemy_scenes.gd` and `load_assets.gd` both use that module; no duplicate const dicts.
- `run_tests.sh` exits 0.

## Dependencies

- None

---

## Execution Plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Define shared `enemy_mutation_map` module contract and documentation alignment | Spec Agent | Ticket AC; `generate_enemy_scenes.gd` / `load_assets.gd` current dicts; `test_enemy_scene_generation_adversarial.gd` comments; `project_board/specs/first_4_families_in_level_spec.md` (AC-GEN / copy-paste narrative) | Specification in ticket **Specification** section (or linked spec path): single file path under `scripts/asset_generation/`, exported symbol(s), preload pattern for both `SceneTree` CLI and `@tool` `EditorScript`, behavior for unknown family (`"unknown"`), whether any call sites beyond the two named files must switch | None | Spec states one canonical map location; contradicts “copied verbatim” story where obsolete; lists blast-radius symbols before implementation | **Assumption:** One `const` dictionary preloadable from both contexts is valid in Godot 4 for this repo. **Risk:** Spec doc is large; only update paragraphs that assert duplicate maps. |
| 2 | Author / adjust behavioral tests for single source of truth | Test Designer | Task 1 spec | Failing tests (where TDD applies) or new tests proving one definition drives both pipelines; update adversarial tests if they hard-code “two copies” or file paths for the dict | 1 | Tests encode AC (no duplicate dict definitions); `timeout 300 godot -s tests/run_tests.gd` shows new failures only where expected pre-implementation | **Risk:** Over-testing file layout vs behavior; prefer assertions on shared preload or exported map identity. |
| 3 | Stress-test the test suite | Test Breaker | Task 2 tests | Review notes / test hardening only in `tests/**` per agent charter | 2 | Gaps documented or tests strengthened without implementation | Low risk. |
| 4 | Implement shared module and remove duplicates | Implementation Generalist | Spec + tests | New `scripts/asset_generation/enemy_mutation_map.gd` (or spec-chosen name); `generate_enemy_scenes.gd` and `load_assets.gd` import single map; no remaining `const MUTATION_BY_FAMILY` in those two files | 2, 3 (tests ready); implementation typically follows failing tests | `rg MUTATION_BY_FAMILY` shows exactly one definition under `scripts/asset_generation/` (the new module); both consumers reference it | **Assumption:** `get_blast_radius` / call-site search run before edit per workflow. **Risk:** Typo in map during move; tests must catch. |
| 5 | Verify full suite and handoff | Implementation Generalist (or Integration) | Task 4 diff | Clean `run_tests.sh` (exit 0); ticket Validation Status updated on handoff | 4 | `run_tests.sh` exits 0; matches ticket AC | None if suite green. |

---

## Specification

### Requirement EMU-MOD-1 — Canonical module and symbol

#### 1. Spec Summary
- **Description:** Introduce a single Godot script at `res://scripts/asset_generation/enemy_mutation_map.gd` that holds the family → mutation string map as one **named constant** `MUTATION_BY_FAMILY` (type: dictionary with string keys and string values). The dictionary’s **entries must match exactly** the current `const MUTATION_BY_FAMILY` blocks in `generate_enemy_scenes.gd` and `load_assets.gd` as of this spec (same keys, same values, same key order as today — no reordering or “cleanup” so diffs stay mechanical).
- **Constraints:** No second `const MUTATION_BY_FAMILY := { ... }` literal anywhere under `scripts/asset_generation/`. The module must be loadable via `preload` in both a `SceneTree` entry script and an `@tool` `EditorScript` without editor-only APIs.
- **Assumptions:** Godot 4.x preloaded script resources expose top-level `const` to callers as `PreloadedScript.MUTATION_BY_FAMILY`. The script may `extends RefCounted` (or equivalent lightweight base) for consistency with `enemy_name_utils.gd`; `class_name` is optional and not required if preload-only access is used.
- **Scope:** `scripts/asset_generation/enemy_mutation_map.gd` (new); `scripts/asset_generation/generate_enemy_scenes.gd`; `scripts/asset_generation/load_assets.gd`.

#### 2. Acceptance Criteria
- File exists at `scripts/asset_generation/enemy_mutation_map.gd` and defines exactly one map constant named `MUTATION_BY_FAMILY`.
- Byte-level identity of the map payload: for every key in the current duplicate dicts, the value in the unified module equals that value (including `"mutation_clown": "random"`).
- `generate_enemy_scenes.gd` and `load_assets.gd` contain **no** `const MUTATION_BY_FAMILY := {` block; both obtain the map only through the preload pattern below.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Reformatting or reordering keys makes review harder and can hide accidental edits; preserve formatting style of the existing dict when moving.
- **Edge case:** Future families must be added only in this module.

#### 4. Clarifying Questions
- None (ticket and code sources are explicit).

---

### Requirement EMU-CON-1 — Consumer preload and access

#### 1. Spec Summary
- **Description:** Both consumers add a preload alias immediately after (or alongside) their existing `EnemyNameUtils` preload, using the same identifier naming style as the project uses for utilities.
- **Constraints:** Use `res://` paths only. Do not `load()` the map at runtime from disk in a way that bypasses static preload for this constant (keep a single const preload binding at script top).
- **Assumptions:** Preload identifier `EnemyMutationMap` is acceptable (mirrors `EnemyNameUtils`); if Implementation prefers another alias, it must be one const preload per file and documented in the implementation handoff notes — default specified here is `EnemyMutationMap`.
- **Scope:** The two consumer scripts only.

#### 2. Acceptance Criteria
- **Pattern (mandatory shape):**  
  `const EnemyMutationMap = preload("res://scripts/asset_generation/enemy_mutation_map.gd")`  
  Access: `EnemyMutationMap.MUTATION_BY_FAMILY` everywhere the map was previously referenced.
- `generate_enemy_scenes.gd` (extends `SceneTree`): uses `EnemyMutationMap.MUTATION_BY_FAMILY` for scene generation mutation resolution.
- `load_assets.gd` (`@tool` / `EditorScript`): uses `EnemyMutationMap.MUTATION_BY_FAMILY` for the same purpose.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Typo in `res://` path breaks both pipelines; tests and/or a quick headless/editor run must catch it.
- **Edge case:** None beyond standard parse/load failures.

#### 4. Clarifying Questions
- None.

---

### Requirement EMU-SEM-1 — Unknown family semantics

#### 1. Spec Summary
- **Description:** For a family name **not** present as a key in `MUTATION_BY_FAMILY`, consumers must behave as today: treat the mutation drop as the literal string `"unknown"`.
- **Constraints:** Do not introduce a new sentinel or change default string.
- **Assumptions:** `generate_enemy_scenes.gd` may continue to wrap resolution in `str(...)` if required to satisfy strict typing / Variant warnings; `load_assets.gd` must resolve to a `String` with default `"unknown"` (explicit typing as needed to match project strict mode).
- **Scope:** Call sites that currently call `.get(family_name, "unknown")` on the map.

#### 2. Acceptance Criteria
- **Example:** `family_name == "totally_fake_family"` → mutation drop / mutation string used in output is `"unknown"`.
- Existing spec **AC-GEN-3.4** behavior (unrecognized family → `"unknown"`) remains satisfied.

#### 3. Risk & Ambiguity Analysis
- **Edge case:** Empty or malformed `family_name` from `EnemyNameUtils` — no change from current behavior (still a miss in the map → `"unknown"` unless already special-cased elsewhere; do not add new branches unless a test demands it).

#### 4. Clarifying Questions
- None.

---

### Requirement EMU-QA-1 — `rg MUTATION_BY_FAMILY` hygiene

#### 1. Spec Summary
- **Description:** After implementation, there must be **exactly one** definition site of the symbol `MUTATION_BY_FAMILY` as a **map literal** under `scripts/asset_generation/`, namely inside `enemy_mutation_map.gd`. Other occurrences in that tree are **references** only (e.g. `EnemyMutationMap.MUTATION_BY_FAMILY` or comments if any).
- **Constraints:** Verification command: `rg MUTATION_BY_FAMILY` from repository root (or `rg MUTATION_BY_FAMILY scripts/asset_generation` for a narrower check).
- **Assumptions:** Matches in `tests/**`, `project_board/**`, `agent_context/**`, historical checkpoints, and other docs are **allowed** and do not violate this requirement — they are **documented exceptions** to the “single definition” rule. The **hard** gate is: no `const MUTATION_BY_FAMILY :=` (or equivalent second full dict definition) outside `enemy_mutation_map.gd` under `scripts/asset_generation/`.
- **Scope:** Entire repo for search; enforcement target is `scripts/asset_generation/`.

#### 2. Acceptance Criteria
- Under `scripts/asset_generation/`, `rg` shows the dict literal only in `enemy_mutation_map.gd`.
- `generate_enemy_scenes.gd` and `load_assets.gd` do not contain `MUTATION_BY_FAMILY` as a local const initializer to a new dictionary literal.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Comment or string in another file contains the substring; acceptable. **Risk:** Test code duplicates the dict for assertions — if introduced, it violates the spirit of single source of truth; Test Designer should prefer preloading `enemy_mutation_map.gd` or asserting against the same preload in tests.

#### 4. Clarifying Questions
- None.

---

### Requirement EMU-NFR-1 — Non-functional constraints

#### 1. Spec Summary
- **Description:** The new module must add negligible overhead: static const only, no per-frame logic, no filesystem reads beyond script parse. Both consumers must remain valid in their respective execution contexts (headless `godot -s .../generate_enemy_scenes.gd` and editor **Run** of `load_assets.gd`).
- **Constraints:** Do not add autoload entries or cyclic dependencies between `enemy_mutation_map.gd` and consumers.
- **Assumptions:** None.
- **Scope:** Module + both consumers.

#### 2. Acceptance Criteria
- `run_tests.sh` exits 0 after full implementation (per ticket AC).
- No new autoload registration required for this feature.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Circular preload if the map module preloads consumers — forbidden; map module must depend on nothing in those two files.

#### 4. Clarifying Questions
- None.

---

### Requirement EMU-DOC-1 — Blast radius and spec doc alignment

#### 1. Spec Summary
- **Description:** **Blast radius (symbols / files):** `MUTATION_BY_FAMILY` definitions and uses in `generate_enemy_scenes.gd` (~lines 16–82, ~147) and `load_assets.gd` (~22–87, ~121); comments in `tests/scenes/enemies/test_enemy_scene_generation_adversarial.gd` referencing duplicate-map risk; prose in `project_board/specs/first_4_families_in_level_spec.md` that states the generator copies the dict verbatim from `load_assets.gd` or that the two files are intentionally kept separate for the map.
- **Constraints:** Update `first_4_families_in_level_spec.md` in the same change set as implementation so narrative matches EMU-MOD-1 (single module, preloaded by both). Replace “copied verbatim / not imported / manually sync” language with “defined in `enemy_mutation_map.gd`, preloaded by generator and editor script.”
- **Assumptions:** Planner/ticket allowed doc updates outside `scripts/` as part of this maintenance item.
- **Scope:** Spec markdown file; test comments optional cleanup if they assert “two copies” literally.

#### 2. Acceptance Criteria
- `first_4_families_in_level_spec.md` no longer instructs maintainers to duplicate or manually sync two `MUTATION_BY_FAMILY` dicts between generator and `load_assets.gd`.
- Adversarial test comments remain accurate (they may still warn about map correctness; they must not claim two authoritative code definitions if only one exists).

#### 3. Risk & Ambiguity Analysis
- **Risk:** Stale line references in old checkpoints — no requirement to edit frozen checkpoints.

#### 4. Clarifying Questions
- None.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_BREAK

## Revision
4

## Last Updated By
Test Designer Agent

## Validation Status

- Tests: `timeout 300 godot -s tests/run_tests.gd` — **fails** (expected): `test_enemy_mutation_map_unify.gd` reports 10 failures until `enemy_mutation_map.gd` + consumer preload refactor land.
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Status
Proceed

## Reason

Primary behavioral suite added under `tests/scripts/asset_generation/test_enemy_mutation_map_unify.gd` (EMU-MOD-1, EMU-CON-1, EMU-SEM-1, EMU-QA-1, shared `is_same` dict reference). Suite fails until `enemy_mutation_map.gd` exists and both consumers use `EnemyMutationMap` preload only. Ready for test-breaker pass.
