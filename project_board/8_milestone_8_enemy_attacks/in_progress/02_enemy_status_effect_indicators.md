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
IMPLEMENTATION_ENGINE_INTEGRATION

### Revision
6

### Last Updated By
Engine Integration Agent

### Validation Status
- Specification: COMPLETE (project_board/specs/enemy_status_effect_indicators_spec.md)
- Tests: PRIMARY SUITE COMPLETE (21 tests, test_enemy_status_effect_indicators.gd)
- Tests: ADVERSARIAL SUITE COMPLETE (22 tests, test_enemy_status_effect_indicators_adversarial.gd)
- Tests: MUTATION SUITE COMPLETE (22 tests, test_enemy_status_effect_indicators_mutation.gd)
- Tests: CONCURRENCY SUITE COMPLETE (20 tests, test_enemy_status_effect_indicators_concurrency.gd)
- Static QA: Not Run
- Integration: Not Run

### Blocking Issues
None

### Escalation Notes
Test Breaker complete. Extended test suite to 85 deterministic tests across 4 files (original 43 + new 42). New mutation tests expose type confusion, interface conflicts, cache invalidation, config edge cases. New concurrency tests expose enemy lifecycle, state machine, and concurrent update vulnerabilities. All tests executable without scene files. Comprehensive coverage of adversarial scenarios, stress testing, and edge cases. Ready for Backend Implementation.

---

# NEXT ACTION

## Next Responsible Agent
Backend Implementation Agent (GDScript)

## Required Deliverables
1. GDScript implementation: `scripts/ui/enemy_status_effect_indicators.gd`
2. Scene file: `scenes/ui/enemy_status_effect_indicators.tscn`
3. All 85 tests passing (existing + mutation + concurrency suites)
4. Type safety: All effect IDs converted to strings
5. Cache correctness: Array duplication for change detection
6. Interface priority: Strict order (getter > meta > property > enum)
7. Export property live-update: Re-render on @export value change

## Test Files
- Primary: `tests/ui/test_enemy_status_effect_indicators.gd` (21 tests)
- Adversarial: `tests/ui/test_enemy_status_effect_indicators_adversarial.gd` (22 tests)
- Adversarial Part 2: `tests/ui/test_enemy_status_effect_indicators_adversarial_part2.gd` (7 tests)
- Mutation: `tests/ui/test_enemy_status_effect_indicators_mutation.gd` (22 tests)
- Concurrency: `tests/ui/test_enemy_status_effect_indicators_concurrency.gd` (20 tests)
- Checkpoint: `project_board/checkpoints/M8-SEFI/2026-05-17T-test_break.md`

## Status
Proceed

## Reason
Test Breaker Agent extended test suite from 43 to 85 deterministic tests. Added mutation tests targeting type confusion, interface conflicts, cache invalidation, extreme configurations. Added concurrency tests targeting enemy lifecycle, state machines, concurrent indicators, disabled behavior. Comprehensive vulnerability coverage with checkpoint decisions logged. All tests executable without scene files. Ready for Backend Implementation to write GDScript and scene files while passing all 85 tests.
