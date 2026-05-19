# M902-12: Stage 4 — Semantic Risk Scoring System

## Description

Implement Stage 4 of the 8-stage governance pipeline: **Semantic Risk Scoring**. Compute weighted risk score from gate violations and signals to determine if high-risk changes need semantic extraction and agent review.

## Acceptance Criteria

- [x] AC-1: Risk scoring function computes weighted inputs from stages 1–3 gates
- [x] AC-2: Signals supported: SRP ambiguity, architecture drift, duplication clusters, async complexity, migration complexity, suppression usage, observability gaps, ownership ambiguity
- [x] AC-3: Scoring bands correctly classify changes: 0–2 EXIT, 3–5 WARN, 6+ ESCALATE
- [x] AC-4: Scoring matrix documented with weights per signal and rationale
- [x] AC-5: Gate module at `ci/scripts/gates/risk_scoring_check.py` with correct contract
- [x] AC-6: Returns JSON with risk_score, reasoning, next_stage_recommendation
- [x] AC-7: Test suite covers high/medium/low risk change patterns with deterministic outcomes

## Execution Plan

Comprehensive execution plan created at `project_board/execution_plans/M902-12_stage_4_risk_scoring_system.md`. Plan decomposes the ticket into 7 sequential tasks:

1. **Task 1 (Spec Agent):** Specification freeze — signal catalog, scoring matrix, weights, output schema, test vectors [COMPLETE]
2. **Task 2 (Test Designer):** Behavioral test suite — 50+ tests covering module contract, signal aggregation, band classification, error handling [COMPLETE]
3. **Task 3 (Test Breaker):** Adversarial test suite — 40+ tests for boundary conditions, weight mutations, schema edge cases, determinism
4. **Task 4 (Implementation Agent):** Python module `risk_scoring_check.py` with signal ingestion, scoring logic, proper error handling
5. **Task 5 (Spec/Code Review Agent):** Static QA — linting, type checking, schema compliance, scoring matrix verification
6. **Task 6 (Integration Agent):** Registry entry in `gate_registry.json`, integration tests, orchestrator validation
7. **Task 7 (Acceptance Gatekeeper):** Verify all 7 ACs met, advance ticket to COMPLETE

See execution plan file for detailed task breakdown, dependencies, success criteria, and risk analysis.

## Specification

Complete specification created and frozen at `project_board/specs/902_12_risk_scoring_spec.md` (Task 1 of execution plan).

**Spec Summary (Task 1 Complete):**
- 5 requirements with complete acceptance criteria
- 8-signal catalog with weights and rule_id mappings (SRP +3, architecture drift +5, duplication +1, async +5, migration +2, suppression +2, observability +1, ownership +1)
- Scoring formula: (sum_weights / 20) * 100, floor rounding, clamped [0-100]
- 3 scoring bands with hard thresholds (0–2 EXIT, 3–5 WARN, 6+ ESCALATE)
- Output contract with 15 required fields (risk_score, band, reasoning, next_stage_recommendation, etc.)
- 33 test vectors covering all risk categories, boundaries, edge cases, determinism, NFR, schema validation
- 8 risks identified with mitigations
- No ambiguities remain; all design decisions frozen
- Ready for Test Designer (Task 2)

## Implementation Notes

- Ingest violation data from previous gates (M902-09, M902-10, M902-11)
- Weight signals by impact (SRP = +3, architecture drift = +5, duplication = +1, async = +5, migration = +2, suppression = +2, observability = +1, ownership = +1)
- Normalize via weighted average (sum / 20 * 100)
- Classify risk_score into band: 0–2 EXIT, 3–5 WARN, 6+ ESCALATE
- Non-blocking shadow mode; status always PASS
- Signal detection via rule_id prefix mapping (AR-*, DUP-*, AS-*, IGN-*, OB-*, MUT-*)
- See: `code_governance.md` Stage 4 architecture

## Dependencies

- M902-01 (Validation Gate Framework) — COMPLETE
- M902-09 (Stage 0 Diff Classification Gate) — COMPLETE
- M902-10 (Stage 1 Formatting Gate) — COMPLETE
- M902-11 (Stage 3 Architecture Enforcement Gate) — COMPLETE

---

## WORKFLOW STATE

| Field | Value |
|-------|-------|
| **Stage** | TEST_BREAK |
| **Revision** | 4 |
| **Last Updated By** | Test Designer Agent |
| **Next Responsible Agent** | Test Breaker Agent |
| **Status** | Proceed |
| **Validation Status** | Spec COMPLETE (Revision 3); Test Design COMPLETE (Revision 4): 79 behavioral tests in `tests/ci/test_risk_scoring_check.py` covering all 33 test vectors and all 7 ACs |
| **Blocking Issues** | None |

## NEXT ACTION

Test Breaker Agent: Read spec at `project_board/specs/902_12_risk_scoring_spec.md` and behavioral test suite at `tests/ci/test_risk_scoring_check.py`. Implement Task 3: Design adversarial test suite (40+ tests) covering boundary conditions (weight mutations, rounding precision, score edge cases at 2.0/2.5/5.0/5.99/6.0), schema edge cases (huge message/reasoning strings, null/missing optional fields), determinism stress tests, and assumption validation (prior gate output format variations). Create test file `tests/ci/test_risk_scoring_check_adversarial.py` with mutation and edge case tests. Mark assumptions with `# CHECKPOINT` comments. Ensure no untested code paths remain. Proceed immediately.
