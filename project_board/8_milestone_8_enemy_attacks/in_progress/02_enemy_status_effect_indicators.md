Title:
Enemy Floating Status Effect Indicators

Description:
Extend the floating enemy UI with compact status effect indicators shown above the health bar (or merged into the same widget). Indicators communicate active combat states such as poison, slow, stun, weaken, and infection progress so players can make tactical decisions at a glance.

Acceptance Criteria:
- Active status effects render as icons/badges above each enemy health bar
- Multiple simultaneous effects are supported and displayed in deterministic order
- Expired effects are removed immediately from the indicator list
- Indicator stack has a max visible count; overflow is represented with a `+N` badge
- Indicator visuals update in real time when effects are added, refreshed, or removed
- Unknown/unmapped effect IDs render a safe fallback icon (no missing-resource errors)

Scope Notes:
- No tooltip or hover description text in this ticket
- No per-effect duration countdown text in this ticket
- Status effect gameplay logic is out of scope; this is display-layer integration only
- Precise icon art polish can iterate later; placeholders are acceptable initially

## Implementation Notes

**Godot Runtime (`scripts/`, `scenes/`)**
- Add status icon container to the world-space enemy UI scene from ticket 01
- Subscribe UI to enemy status-effect state updates (add/remove/refresh events)
- Add stable sort policy for icon ordering (for example: stun > weaken > poison > slow > infection)
- Add fallback resource path for unknown status IDs

**Tests**
- Add tests for multi-effect render order and overflow behavior
- Add tests ensuring removal on expiration and fallback icon behavior
- Add regression test proving status-only updates do not break health bar updates

## WORKFLOW STATE

### Stage
INTEGRATION

### Revision
8

### Last Updated By
Acceptance Criteria Gatekeeper Agent

### Validation Status
- Specification: COMPLETE (project_board/specs/enemy_status_effect_indicators_spec.md)
- Tests: PRIMARY SUITE COMPLETE (21 tests, test_enemy_status_effect_indicators.gd)
- Tests: ADVERSARIAL SUITE COMPLETE (22 tests, test_enemy_status_effect_indicators_adversarial.gd)
- Tests: ADVERSARIAL PART 2 COMPLETE (7 tests, test_enemy_status_effect_indicators_adversarial_part2.gd)
- Tests: MUTATION SUITE COMPLETE (22 tests, test_enemy_status_effect_indicators_mutation.gd)
- Tests: CONCURRENCY SUITE COMPLETE (20 tests, test_enemy_status_effect_indicators_concurrency.gd)
- Static QA: COMPLETE (GDScript linter passed, all review findings addressed)
  - Commit: 2678947 — Fixed magic numbers, validated resource paths, removed redundant _arrays_equal(), cleaned up scene orphans
- Integration: IN PROGRESS
  - Implementation files exist and are complete:
    - `scripts/ui/enemy_status_effect_indicators.gd` (274 lines, all required methods present)
    - `scenes/ui/enemy_status_effect_indicators.tscn` (scene structure complete with script and config)
  - All 85 tests created and structured for execution
  - Manual verification pending: test suite execution via ci/scripts/run_tests.sh to confirm all tests pass

### Blocking Issues
None

### Escalation Notes
Test Breaker complete. Extended test suite to 85 deterministic tests across 5 files (original 43 + new 42 mutation/concurrency tests). Implementation is code-complete with all required methods (effect reading, sorting, rendering, fallback handling, overflow badge). Stage corrected from invalid `IMPLEMENTATION_ENGINE_INTEGRATION_COMPLETE` to `INTEGRATION`. Awaiting test verification and human acceptance review.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Deliverables
1. Test execution verification: Run `timeout 300 ci/scripts/run_tests.sh` and confirm all 85 tests pass
2. Visual integration verification: Launch Godot, load a test scene with enemies, verify status effect indicators render above health bars
3. Code review: Inspect `scripts/ui/enemy_status_effect_indicators.gd` for correctness against Acceptance Criteria
4. Acceptance sign-off: Confirm that all 6 Acceptance Criteria are satisfied by implementation

## Test Files
- Primary: `tests/ui/test_enemy_status_effect_indicators.gd` (21 tests)
- Adversarial: `tests/ui/test_enemy_status_effect_indicators_adversarial.gd` (22 tests)
- Adversarial Part 2: `tests/ui/test_enemy_status_effect_indicators_adversarial_part2.gd` (7 tests)
- Mutation: `tests/ui/test_enemy_status_effect_indicators_mutation.gd` (22 tests)
- Concurrency: `tests/ui/test_enemy_status_effect_indicators_concurrency.gd` (20 tests)
- Implementation: `scripts/ui/enemy_status_effect_indicators.gd` (274 lines)
- Scene: `scenes/ui/enemy_status_effect_indicators.tscn`
- Checkpoint: `project_board/checkpoints/M8-SEFI/2026-05-17T-test_break.md`

## Status
Blocked — Awaiting Integration Verification

## Reason
Implementation code is complete and all test suites are structured. However, Acceptance Criteria Gatekeeper cannot verify test execution results in this autonomous run (test execution requires test runner subprocess with Godot binary). All 6 Acceptance Criteria require objective evidence from test execution:
1. AC1 (active effects render): Covered by tests, implementation present
2. AC2 (multiple effects in order): Covered by tests (_sort_effects method present)
3. AC3 (expired effects removed): Covered by tests, _process_update detects changes
4. AC4 (overflow badge): Covered by tests, _update_overflow_badge method present
5. AC5 (real-time updates): Covered by tests, _process method present
6. AC6 (fallback icon): Covered by tests, _get_fallback_icon method present

Before Stage can advance to COMPLETE, Human must execute test suite and confirm all 85 tests pass. If any tests fail, route to implementation agent to fix. If all tests pass and visual verification succeeds, move ticket to `project_board/8_milestone_8_enemy_attacks/done/` and set Stage to COMPLETE.
