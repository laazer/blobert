# M9-RSEVV — Scoped Checkpoint Log

Ticket: `project_board/9_milestone_9_enemy_player_model_visual_polish/in_progress/08_runtime_spawn_random_enemy_visual_variant.md`
Run: `run-2026-04-09-autopilot`

### [M9-RSEVV] PLANNING — bootstrap malformed backlog ticket
**Would have asked:** Should this ticket be converted to full workflow template before Planner runs, or should planner infer sections from the minimal stub?
**Assumption made:** Convert immediately to workflow-tracked ticket with Stage `PLANNING`, Revision `1`, and Planner handoff fields to preserve strict workflow enforcement.
**Confidence:** High

### [M9-RSEVV] PLANNING — random policy ambiguity
**Would have asked:** Should enemy visual selection be strictly uniform random across in-use versions, or support weighted random now?
**Assumption made:** Specify uniform random as the required default contract for this ticket, and defer weighted controls to a future ticket unless existing registry metadata already exposes stable weights.
**Confidence:** Medium

### [M9-RSEVV] PLANNING — spawn choke point ownership
**Would have asked:** Should this ticket modify current sandbox/procedural spawn paths directly now, or define a single helper contract to be consumed by M10 wiring work?
**Assumption made:** Plan targets a single reusable spawn-resolution helper contract first, then integrates it at the runtime spawn choke point used by both sandbox and procedural flows once M10 wiring is available.
**Confidence:** Medium

### [M9-RSEVV] SPECIFICATION — deterministic randomness seam
**Would have asked:** Which RNG source should runtime variant selection use so tests can be deterministic without mutating global engine randomness state?
**Assumption made:** The selector contract must accept an injectable RNG seam (or equivalent deterministic hook) while preserving current runtime randomness behavior when no deterministic hook is provided.
**Confidence:** Medium

### [M9-RSEVV] TEST_DESIGN — selector API + choke-point seam naming
**Would have asked:** What exact selector file/function names should tests target for runtime integration across sandbox and procedural spawn flows?
**Assumption made:** Primary tests target a single shared selector module at `res://scripts/system/enemy_visual_variant_selector.gd` exposing `resolve_spawn_visual_variant(family, manifest, rng)` and require procedural choke-point wiring in `run_scene_assembler.gd`; sandbox wiring assertions are deferred to Test Breaker for current branch seam discovery while enforcing selector behavior strictly now.
**Confidence:** Medium

### [M9-RSEVV] TEST_BREAK — malformed status-field semantics
**Would have asked:** If version metadata has missing/non-boolean `draft` or `in_use` fields, should runtime coerce values or reject them?
**Assumption made:** Fail closed and reject malformed entries entirely (no coercion), so any family with only malformed candidates returns an explicit non-success selector result.
**Confidence:** High

### [M9-RSEVV] INTEGRATION — AC evidence refresh for gatekeeper closure
- Updated ticket `WORKFLOW STATE`/`NEXT ACTION` only (Stage kept `INTEGRATION`, Revision `8`, Last Updated By `Engine Integration Agent`).
- Validation Status now explicitly maps AC1 to `tests/scripts/system/test_runtime_enemy_visual_variant_selector.gd` concrete selector diversity test and AC2 to primary + adversarial selector suites.
- Re-ran `timeout 300 ci/scripts/run_tests.sh` on 2026-04-09; exit code `0`; routed next action to `Acceptance Criteria Gatekeeper Agent` with `Status: Proceed` for final closure review.
