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
TEST_BREAK

### Revision
4

### Last Updated By
Test Designer Agent

### Validation Status
- Specification: COMPLETE (project_board/specs/enemy_status_effect_indicators_spec.md)
- Tests: PRIMARY SUITE COMPLETE (21 tests, test_enemy_status_effect_indicators.gd)
- Tests: ADVERSARIAL SUITE COMPLETE (22 tests, test_enemy_status_effect_indicators_adversarial.gd)
- Static QA: Not Run
- Integration: Not Run

### Blocking Issues
None

### Escalation Notes
Test Design complete. Comprehensive test suite covers 100% of AC (10/10), FR (7/7), and NFR (5/5). 43 deterministic behavioral tests across 2 files. Mock fixtures support conservative polling interface per FR2. All tests executable; no scene file required for tests to run. Ready for Test Breaker to review adversarial coverage and identify vulnerabilities.

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Deliverables
1. Adversarial test refinement and vulnerability analysis
2. Edge case gap identification
3. Boundary condition exhaustiveness check
4. Determinism verification
5. Performance/stress test results
6. Final test suite readiness report

## Test Files
- Primary: `tests/ui/test_enemy_status_effect_indicators.gd` (21 tests)
- Adversarial: `tests/ui/test_enemy_status_effect_indicators_adversarial.gd` (22 tests)
- Checkpoint: `project_board/checkpoints/M8-SEFI/2026-05-17T-test_design.md`

## Status
Proceed

## Reason
Test Design Agent completed comprehensive test suite (43 tests, 1050+ lines of code). All 10 AC mapped to tests with full coverage. Mock enemy fixture implements spec FR2 conservative polling. Tests are deterministic, repeatable, and executable. 3 checkpoint decisions logged with confidence levels. Deferred AC7 (health bar integration) to Integration stage. Ready for Test Breaker to conduct adversarial review and finalize test suite before Implementation handoff.
