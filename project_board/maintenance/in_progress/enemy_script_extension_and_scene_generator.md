# TICKET: enemy_script_extension_and_scene_generator

Title: Per-enemy (or per-family) `EnemyBase` subclasses and scene generator wiring

## Description

Generated enemy roots currently attach `enemy_base.gd` for all GLBs. As M8/M9/M15 add divergent behavior, introduce a convention: `extends EnemyBase` in one script per slug or per family, selected when writing `.tscn` in `generate_enemy_scenes.gd` (fallback to `enemy_base.gd` when no override exists). Keeps shared nodes (`EnemyAnimationController`, infection wiring) unless a specific enemy needs overrides.

## Acceptance Criteria

- Documented pattern for where new enemy scripts live (e.g. `scripts/enemies/generated/adhesion_bug.gd`) and how the generator picks them.
- `generate_enemy_scenes.gd` sets `root.script` from family name with safe fallback.
- `run_tests.sh` exits 0; existing generated scenes still load (default script unchanged until overrides are added).

## Dependencies

- `enemy_mutation_map_unify` (recommended first — shared asset_generation touchpoints) — **done** (`project_board/maintenance/done/enemy_mutation_map_unify.md`).

---

## Execution Plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Lock resolver contract: path convention, lookup key, parity consumers, docs | Spec Agent | Ticket AC; `scripts/asset_generation/generate_enemy_scenes.gd` (`family_name`, `DEFAULT_ENEMY_SCRIPT`, `set_script`); `scripts/asset_generation/load_assets.gd` (same); `scripts/asset_generation/enemy_name_utils.gd` (`extract_family_name`); `scripts/enemies/enemy_base.gd` (`class_name EnemyBase`); `project_board/specs/first_4_families_in_level_spec.md` if it asserts a single fixed script path | **Specification** section (or linked spec path): canonical directory for optional subclasses (e.g. `res://scripts/enemies/generated/<stem>.gd`); exact stem = output of `EnemyNameUtils.extract_family_name` for the GLB basename; `ResourceLoader.exists` then `load`, else fallback `res://scripts/enemies/enemy_base.gd`; both `generate_enemy_scenes.gd` and `load_assets.gd` must use the same resolution (no editor/headless drift); whether resolver lives in a new `scripts/asset_generation/*.gd` module vs duplicated logic; blast-radius list of symbols/files; optional second-tier lookup (e.g. by mutation bucket) explicitly allowed or deferred | None | Spec is unambiguous for implementers; documents “extends `EnemyBase`” expectation for override scripts; calls out LEARNINGS parity requirement for the two generators | **Assumption:** “Family name” in AC means the existing `family_name` variable (`extract_family_name` result), not mutation bucket string. **Risk:** Ambiguity between per-slug scripts vs one script per mutation group — spec must pick one primary rule. |
| 2 | Author behavioral / static tests for resolver + generator wiring | Test Designer | Task 1 spec | New or extended tests under `tests/**` (e.g. asset_generation scene + adversarial suites) that fail until implementation: missing override → base path; present override → that path; both consumers reference shared resolver per spec; no regression on existing generated `.tscn` load | 1 | `timeout 300 godot -s tests/run_tests.gd` shows expected pre-implementation failures; tests trace to spec IDs | **Risk:** Tests that require a real `.gd` on disk — use minimal fixture under `scripts/enemies/generated/` only if spec requires, or source-level assertions like EMU suite. |
| 3 | Stress-test the test suite | Test Breaker | Task 2 tests | Hardened tests / notes in `tests/**` only | 2 | Edge cases covered (invalid stem characters if spec forbids, double preload, drift between generators) | Low risk if spec is clear. |
| 4 | Implement resolver module + wire both generators; add `scripts/enemies/generated/` placeholder if empty | Implementation Generalist | Spec + tests | Spec-chosen resolver API; `generate_enemy_scenes.gd` and `load_assets.gd` call it before `set_script`; optional `.gitkeep` or doc stub in `scripts/enemies/generated/` per spec; **no** mass change to committed `.tscn` when no override files exist | 2, 3 | `run_tests.sh` exit 0; `rg`/tests show single resolution path for both pipelines; regenerated scenes (if run) match “default `enemy_base`” for all current GLBs | **Assumption:** `get_blast_radius` / call-site search before edits per workflow. **Risk:** Forgetting `load_assets.gd` causes editor/CLI drift (LEARNINGS). |
| 5 | Full verification and handoff | Implementation Generalist (or Integration) | Task 4 | `run_tests.sh` exit 0; load smoke for representative `res://scenes/enemies/generated/*.tscn` if spec requires; ticket Validation Status + NEXT ACTION updated on handoff | 4 | AC satisfied: documented pattern, generator picks script with safe fallback, no broken existing scenes | None if suite green. |

---

## Specification

**Traceability:** Requirements `REQ-ESEG-1`–`REQ-ESEG-3` satisfy ticket AC and execution plan task 1. Lookup key is **`family_name`**: the string produced by `EnemyNameUtils.extract_family_name(glb_basename)` where `glb_basename` is `glb_path.get_file().get_basename()` (same as today in both generators). That utility lives at `scripts/asset_generation/enemy_name_utils.gd` (class `EnemyNameUtils`).

**Blast radius (implementation / tests):** `scripts/asset_generation/generate_enemy_scenes.gd`; `scripts/asset_generation/load_assets.gd`; new shared resolver module under `scripts/asset_generation/` (see REQ-ESEG-1); optional new or touched files under `scripts/enemies/generated/`; tests under `tests/**` per Test Designer.

---

### Requirement REQ-ESEG-1 — Shared enemy root script resolver

#### 1. Spec Summary
- **Description:** Introduce a **single** resolver module under `scripts/asset_generation/` (exact filename at implementer discretion; e.g. `enemy_root_script_resolver.gd`) that exposes the **only** authoritative logic for choosing which `res://` path to attach to the **root** node of a generated enemy scene. Given `family_name: String`, the resolver returns `res://scripts/enemies/generated/%s.gd % family_name` when `ResourceLoader.exists` is true for that path; otherwise returns `res://scripts/enemies/enemy_base.gd`. Both `generate_enemy_scenes.gd` and `load_assets.gd` must **call this resolver** (preload + invoke) immediately before `set_script` on the root — **no duplicated path rules** in either file.
- **Constraints:** Resolver must not depend on editor-only APIs so headless `generate_enemy_scenes.gd` and `@tool` `load_assets.gd` behave identically. Base path string must remain the current default: `res://scripts/enemies/enemy_base.gd`. Override directory is exactly `res://scripts/enemies/generated/`.
- **Assumptions:** No second-tier lookup (e.g. by mutation bucket) in this ticket; deferred unless a follow-up ticket adds it. `family_name` is already computed by existing generator code; resolver accepts it as input only.
- **Scope:** Root `CharacterBody3D` / `Node3D` gameplay script attachment only; does not change animation controller, ESM stub, or other child node scripts.

#### 2. Acceptance Criteria
- **AC-ESEG-1a:** One module under `scripts/asset_generation/` defines the override path pattern, the base path constant, and the exists-then-select logic in one place.
- **AC-ESEG-1b:** `generate_enemy_scenes.gd` uses only that module (plus existing `EnemyNameUtils` for `family_name`) to obtain the script path before `load` + `root.set_script`.
- **AC-ESEG-1c:** `load_assets.gd` uses the same module the same way (no copy-pasted conditional).
- **AC-ESEG-1d:** When no file exists at `res://scripts/enemies/generated/<family_name>.gd`, the chosen path equals `res://scripts/enemies/enemy_base.gd` (behavior unchanged from today for all current GLBs).
- **AC-ESEG-1e:** When such a file exists, the chosen path is that override path.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Drift if a future edit updates only one generator — mitigated by tests asserting a single implementation and by LEARNINGS parity expectations.
- **Edge case:** Multiple GLB basenames mapping to the same `family_name` (e.g. `acid_spitter_00` and `acid_spitter_animated_00`) intentionally share one override script; per-full-basename overrides are out of scope.

#### 4. Clarifying Questions
- None for this handoff; primary rule is per-`extract_family_name` stem, not per mutation bucket.

---

### Requirement REQ-ESEG-2 — Override script path and `EnemyBase` contract

#### 1. Spec Summary
- **Description:** Optional per-family scripts live at **`res://scripts/enemies/generated/{family_stem}.gd`** where **`family_stem`** is exactly the string returned by `EnemyNameUtils.extract_family_name` for the GLB basename (underscore-separated segments after stripping trailing numeric variant index and all `animated` segments — implementation in `scripts/asset_generation/enemy_name_utils.gd`). Each override file **must** be a GDScript that **`extends EnemyBase`** (`class_name EnemyBase` in `scripts/enemies/enemy_base.gd`) so exports and shared behavior remain compatible. Attachment pattern: `ResourceLoader.exists(override_path)` → `var script_res := load(resolved_path)` → if non-null, `root.set_script(script_res)`; if override path missing, resolved path is base script (same load + set pattern).
- **Constraints:** File name is `{family_stem}.gd` only (no subdirectory variants in this ticket). Do not require override scripts to exist for the pipeline to succeed.
- **Assumptions:** Repository may ship an empty `scripts/enemies/generated/` (e.g. `.gitkeep`) until first override is added.
- **Scope:** Gameplay root script only.

#### 2. Acceptance Criteria
- **AC-ESEG-2a:** For a given `family_name` value `F`, the resolver tests path `res://scripts/enemies/generated/F.gd` (single segment join: directory + `F` + `.gd`).
- **AC-ESEG-2b:** Documented expectation: new override scripts declare `extends EnemyBase` (or equivalent inheritance chain whose native class is `EnemyBase`).
- **AC-ESEG-2c:** Example: basename `adhesion_bug_00` → `family_name` `adhesion_bug` → optional override `res://scripts/enemies/generated/adhesion_bug.gd`.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Override script forgetting `extends EnemyBase` breaks exports — caught by review and optionally static/tests in follow-on work; spec states the contract explicitly.
- **Edge case:** Empty `family_name` after extraction is unspecified for real assets; if tests need it, treat as “no override file” / base only unless a test defines otherwise.

#### 4. Clarifying Questions
- None.

---

### Requirement REQ-ESEG-3 — ESEG-DOC: human-facing documentation pattern

#### 1. Spec Summary
- **Description:** Document for humans (in ticket **Description** or **Specification** pointer — this section satisfies **ESEG-DOC**): (1) Add optional enemy-specific behavior under `res://scripts/enemies/generated/`. (2) Name the file **`{family_stem}.gd`** where `family_stem` is the output of `EnemyNameUtils.extract_family_name` on the GLB basename (same string as scene `enemy_family` metadata / export). (3) Script must extend **`EnemyBase`**. (4) Regenerate scenes via headless `godot -s scripts/asset_generation/generate_enemy_scenes.gd` and/or editor **`load_assets.gd`** as today; both use the **same resolver**, so editor and CLI never disagree on which root script is written. (5) If the override file is absent, roots keep **`enemy_base.gd`** — no manual `.tscn` script path edits required for the default case.
- **Constraints:** Documentation must not claim per-mutation-bucket script selection unless a future ticket adds it.
- **Assumptions:** Readers know where GLBs live (`res://assets/enemies/generated_glb`) and output scenes (`res://scenes/enemies/generated`).
- **Scope:** Onboarding / maintenance docs only; no new standalone doc file required by this spec (ticket body carries ESEG-DOC).

#### 2. Acceptance Criteria
- **AC-ESEG-3a:** Ticket AC “Documented pattern for where new enemy scripts live and how the generator picks them” is satisfied by this **ESEG-DOC** section plus REQ-ESEG-1/2.
- **AC-ESEG-3b:** Parity rule is explicit: any change to resolution logic happens in the shared resolver, not in one generator alone.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Contributors add overrides with wrong stem — mitigated by naming examples and reference to `extract_family_name`.

#### 4. Clarifying Questions
- None.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_DESIGN

## Revision
3

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
  "ticket_path": "project_board/maintenance/in_progress/enemy_script_extension_and_scene_generator.md",
  "spec_requirements": ["REQ-ESEG-1", "REQ-ESEG-2", "REQ-ESEG-3"],
  "resolver_contract": "Single module under scripts/asset_generation/; family_name -> res://scripts/enemies/generated/{family_name}.gd if ResourceLoader.exists else res://scripts/enemies/enemy_base.gd",
  "parity_consumers": [
    "scripts/asset_generation/generate_enemy_scenes.gd",
    "scripts/asset_generation/load_assets.gd"
  ],
  "family_name_source": "EnemyNameUtils.extract_family_name(glb_path.get_file().get_basename()) in scripts/asset_generation/enemy_name_utils.gd"
}
```

## Status
Proceed

## Reason

Specification complete: REQ-ESEG-1 (shared resolver, single resolution path), REQ-ESEG-2 (override path `res://scripts/enemies/generated/{family_stem}.gd`, `extends EnemyBase`, exists/load/set_script pattern with base fallback), REQ-ESEG-3 (ESEG-DOC human pattern and parity rule). Test Designer should author failing tests for resolver + dual-consumer wiring per AC-ESEG-* before implementation.
