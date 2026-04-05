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

*(Spec Agent populates or links.)*

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
SPECIFICATION

## Revision
2

## Last Updated By
Planner Agent

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
Spec Agent

## Required Input Schema
```json
{
  "ticket_path": "string (absolute or repo-relative to this ticket)",
  "acceptance_criteria_ref": "enemy_script_extension_and_scene_generator AC bullets",
  "planning_assumption": "script stem = EnemyNameUtils.extract_family_name output; both generate_enemy_scenes.gd and load_assets.gd must stay in parity"
}
```

## Status
Proceed

## Reason

Planning complete: execution plan decomposes MAINT-ESEG into spec, TDD tests, implementation of per-slug optional `EnemyBase` subclasses under a documented path with generator fallback to `enemy_base.gd`, and full-suite verification without breaking existing scenes.
