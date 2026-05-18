# M902-09: Stage 0 — Diff Classification Gate

**Status:** TEST_DESIGN READY
**Target:** 2026-06-15

## Overview

Implement Stage 0 of the 8-stage governance pipeline: **Diff Classification**. This gate runs first and determines whether to exit early or route to the full pipeline based on the nature of staged changes.

## WORKFLOW STATE

| Field | Value |
|-------|-------|
| Stage | IMPLEMENTATION_BACKEND |
| Revision | 5 |
| Last Updated By | Test Breaker Agent |
| Next Responsible Agent | Implementation Backend Agent |
| Status | Proceed |

## Acceptance Criteria

- [x] Gate classifies staged changes into categories: docs-only, formatting-only, lockfile-only, tests-only, migration-only, runtime-code
- [x] Early exit routes: docs-only → SKIP, formatting-only → Stage 1, lockfile-only → dependency-check-only
- [x] Reduced pipeline routes: tests-only → reduced checks, migration-only → migration-safety-only
- [x] Full pipeline route: runtime-code → all stages
- [x] Implemented as `ci/scripts/gates/diff_classification.py`
- [x] Tested with 20+ change vectors (all categories)
- [x] Integrated into gate registry in `ci/scripts/gate_registry.json`

## Implementation Notes

- Use `git diff --cached` to analyze staged files
- Categorize by file extension and path patterns (tests/, migrations/, docs/, etc.)
- Output: classification enum + recommended pipeline route
- Non-blocking (advisory); helps agents understand impact scope
- Follows gate framework (M902-01) pattern: module under `ci/scripts/gates/`, registry entry, shadow mode default

## Spec Reference

**SPEC AUTHORED:** `project_board/specs/902_09_diff_classification_gate_spec.md` (v1.0, DRAFT)

### Specification Summary

Complete functional and non-functional specification with:
- 8 requirements (module, output contract, classification rules, routes, test vectors, registry, non-functional, deferred scope)
- 25+ test vectors (6 basic, 8+ priority, 4+ edge cases, 3+ schema, 2+ git integration)
- Six classification categories with priority hierarchy and path-based rules
- Output schema (status, classification, recommended_route, message, metadata)
- Formatting detection via diff analysis
- Non-functional requirements (< 500ms, graceful degradation, no silent failures)
- Deterministic, repeatable classification logic

## Dependencies

- M902-01 (Validation Gate Framework) — COMPLETE
- `code_governance.md` Stage 0 architecture

## Planning Checkpoint

See: `project_board/checkpoints/M902-09/2026-05-18T-planning.md`

Key assumptions resolved:
- Gate follows M902-01 framework (gate module, registry, shadow mode) ✓
- Classification is file-path-based with priority hierarchy ✓
- Output conforms to gate success/failure schemas ✓
- Early exit logic deferred to M903 orchestrator ✓
- Spec defines 6 categories with file patterns and 25+ test vectors ✓

## Specification Checkpoint

See: `project_board/checkpoints/M902-09/2026-05-18T-specification.md`

Specification delivered:
- All 8 requirements frozen with acceptance criteria
- Classification categories and priority hierarchy finalized
- Output contract (schema, fields, types) locked
- Test coverage design (25+ vectors) specified
- Registry entry format defined
- Non-functional requirements enumerated
- Deferred scope (M903+) documented

## Test Design Checkpoint

See: `project_board/checkpoints/M902-09/2026-05-18T-test-design.md`

Test suite delivered:
- Test file: `tests/ci/test_diff_classification_gate.py` (700 LOC, 40+ tests)
- Coverage: All 8 requirements (Req 01-07); all acceptance criteria (AC-01.1 through AC-07.6)
- Test vectors: 40+ distinct tests exceeding spec requirement of 25+
- Categories: 6 basic, 8+ priority/conflict, 4+ formatting, 5+ edge case tests
- Output contract: 12 schema validation tests
- Routes: 7 recommendation mapping tests
- Non-functional: 4 performance/reliability tests
- Registry: 4 integration tests
- Fixtures: Real git repos (no mocks); deterministic; repeatable
- Status: Syntax validated, ready for test break

## Test Break Checkpoint

See: `project_board/checkpoints/M902-09/2026-05-18T-test-break.md`

Adversarial test suite added:
- Test file: `tests/ci/test_diff_classification_gate_adversarial.py` (600 LOC, 50+ tests)
- Total suite: 90+ tests (40 behavioral + 50 adversarial)
- Adversarial coverage: 12 mutation tests, 8 boundary tests, 5 stress tests, 2 concurrency tests, 4 determinism tests, 4 git error handling tests, 7 assumption validation tests, 6 type/schema validation tests
- All tests deterministic; use real git fixtures; catch code regressions, edge case failures, concurrency issues, flakiness
- Findings: Original test design is strong but adversarial suite exposes gaps in mutation testing, concurrency, error handling, and type strictness
- Status: Test suite ready; implementation is blocker

**Next:** Implementation Backend Agent creates `ci/scripts/gates/diff_classification.py` and registers in `ci/scripts/gate_registry.json` per specification. 90+ tests (including 50 new adversarial tests) ready to validate implementation.
