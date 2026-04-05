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

## Status
Proceed

## Reason

Planning complete. Specification must lock the shared module API, preload usage from CLI generator and editor script, and reconcile `first_4_families_in_level_spec.md` where it still describes duplicated maps.
