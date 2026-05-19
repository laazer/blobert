# M902-11: Stage 3 — Architecture Enforcement Gate

**Created:** 2026-05-18  
**Target Completion:** 2026-06-22

---

## Description

Implement Stage 3 of the 8-stage governance pipeline: **Structural Architecture Enforcement**. Enforce SRP, layer boundaries, dependency direction, duplication, and complexity limits.

Gate must aggregate violations from multiple analysis tools and report findings with appropriate severity levels (FAIL for SRP violations, WARN for complexity warnings, PASS for clean code).

---

## Acceptance Criteria

- [ ] Gate runs: import-linter (Python), eslint-plugin-boundaries (TypeScript), semgrep (custom rules), jscpd (duplication), radon/lizard (complexity)
- [ ] Detects SRP violations: controller→repository, domain→infrastructure, service→HTTP logic
- [ ] Detects dependency direction violations (reverse edges, circular imports)
- [ ] Detects cross-layer state mutation and ownership boundary violations
- [ ] Detects duplication clusters (8+ lines, cross-file)
- [ ] Detects complexity spikes (function/class size, nesting depth)
- [ ] Flags async safety violations (blocking I/O in async, unbounded spawning)
- [ ] Implemented as `ci/scripts/gates/architecture_enforcement_check.py` with aggregated report
- [ ] Integrated into gate registry (`gate_registry.json`)
- [ ] Tested with architecture violation vectors (SRP, circular imports, duplication, complexity)

---

## Dependencies

- M902-01 (Validation Gate Framework) — COMPLETE
- M902-02 (Static Analysis tools baseline) — COMPLETE
- `code_governance.md` Stage 3 architecture patterns

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_BACKEND

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: Designed and broken (80 tests: 51 behavioral + 29 adversarial, all fail until implementation)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Implementation Generalist (Backend)

## Status
Proceed

## Reason
Adversarial test suite completed (29 new tests covering mutation testing, boundary conditions, combinatorial failures, type violations, order dependency, mock exposure, and spec gap detection). Total test count: 80 (51 behavioral + 29 adversarial, 1,980+ LOC). Test files: tests/ci/test_architecture_enforcement_gate.py (51 tests) + tests/ci/test_architecture_enforcement_gate_adversarial.py (29 tests). Checkpoint log: project_board/checkpoints/M902-11/2026-05-19T-test_break.md. All 80 tests fail as expected (gate module not yet implemented). Adversarial tests target: score computation (weighted average, clamping, AR-only counting), status determination (ERROR/CRITICAL checks, shadow override), deduplication (fingerprint, severity, cross-tool), boundaries (zero/max violations, duration), combinatorics (mixed failures), types (validation), determinism (sorting), mock exposure (validation, null handling), spec gaps (defaults, constraints, invalid modes). Tests are deterministic and reproducible. Key implementation requirements: (1) risk_score = weighted average (CRITICAL=100, ERROR=80, WARN=50, INFO=10), clamped [0,100]; (2) architecture_score = 100 - (AR_violations * 10), clamped [0,100]; (3) status = ESCALATE if CRITICAL or score<=30, FAIL if ERROR or score>90, PASS otherwise, shadow mode forces PASS override; (4) deduplication by (file, line, rule_id), keep most severe; (5) mode defaults to 'shadow', ticket_id defaults to 'M902-11'. Ready for Implementation Generalist to create ci/scripts/gates/architecture_enforcement_check.py with proper tool orchestration, score computation, and error handling.
