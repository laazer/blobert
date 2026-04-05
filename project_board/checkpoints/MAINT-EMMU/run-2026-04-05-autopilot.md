# MAINT-EMMU — enemy_mutation_map_unify

Run: 2026-04-05 autopilot (maintenance backlog queue, ticket 2)

### [MAINT-EMMU] PLANNING — Ticket scope and module shape
**Would have asked:** Is `enemy_mutation_map.gd` with a single `const MUTATION_BY_FAMILY` preloaded by both `generate_enemy_scenes.gd` and `load_assets.gd` the intended architecture, or should the map live on a named class with static access?
**Assumption made:** A dedicated script under `scripts/asset_generation/` exposing `const MUTATION_BY_FAMILY` (preload from both consumers) matches the ticket example and existing preload style (`enemy_name_utils.gd`).
**Confidence:** High

### [MAINT-EMMU] PLANNING — Historical spec doc conflict
**Would have asked:** Must `project_board/specs/first_4_families_in_level_spec.md` be amended in this workstream when AC only names code and tests?
**Assumption made:** Spec Agent updates or explicitly supersedes paragraphs that state the generator copies the dict verbatim from `load_assets.gd`, so planning/docs do not contradict the single-source implementation.
**Confidence:** Medium

### [MAINT-EMMU] PLANNING — Execution plan recorded
**Would have asked:** None; acceptance criteria and file paths are explicit in the ticket.
**Assumption made:** TDD order holds: Spec → Test Designer → Test Breaker → Implementation Generalist → `run_tests.sh` verification.
**Confidence:** High
