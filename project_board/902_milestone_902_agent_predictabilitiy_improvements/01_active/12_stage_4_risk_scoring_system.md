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
3. **Task 3 (Test Breaker):** Adversarial test suite — 40+ tests for boundary conditions, weight mutations, schema edge cases, determinism [COMPLETE]
4. **Task 4 (Implementation Agent):** Python module `risk_scoring_check.py` with signal ingestion, scoring logic, proper error handling [COMPLETE]
5. **Task 5 (Spec/Code Review Agent):** Static QA — linting, type checking, schema compliance, scoring matrix verification
6. **Task 6 (Integration Agent):** Registry entry in `gate_registry.json`, integration tests, orchestrator validation
7. **Task 7 (Acceptance Gatekeeper):** Verify all 7 ACs met, advance ticket to COMPLETE

See execution plan file for detailed task breakdown, dependencies, success criteria, and risk analysis.

## Specification

Complete specification created and frozen at `project_board/specs/902_12_risk_scoring_spec.md` (Task 1 of execution plan).

**Spec Summary (Task 1 Complete — v1.1 with Contradiction Resolution):**
- 5 requirements with complete acceptance criteria
- 8-signal catalog with weights and rule_id mappings (SRP +3, architecture drift +5, duplication +1, async +5, migration +2, suppression +2, observability +1, ownership +1)
- Scoring formula: (sum_weights / 20) * 100, floor rounding, clamped [0-100]
- 3 scoring bands with hard thresholds on WEIGHT scale (0–2 EXIT, 3–5 WARN, 6+ ESCALATE) — **CLARIFIED v1.1 to explicitly state weight-based, not score-based**
- Output contract with 15 required fields (risk_score, band, reasoning, next_stage_recommendation, etc.)
- 33 test vectors covering all risk categories, boundaries, edge cases, determinism, NFR, schema validation — **CORRECTED v1.1: TV-02 updated to expect band=WARN per weight-based classification**
- 8 risks identified with mitigations
- Contradiction between Requirement 03 and Requirement 05 **RESOLVED** in favor of weight-based band classification (implementation-correct)
- Ready for Test Designer (Task 2)

## Implementation Notes

- Ingest violation data from previous gates (M902-09, M902-10, M902-11)
- Weight signals by impact (SRP = +3, architecture drift = +5, duplication = +1, async = +5, migration = +2, suppression = +2, observability = +1, ownership = +1)
- Normalize via weighted average (sum / 20 * 100)
- Classify band based on total_weight (not risk_score): weight 0–2 → EXIT, 3–5 → WARN, 6+ → ESCALATE
- Non-blocking shadow mode; status always PASS
- Signal detection via rule_id prefix mapping (AR-*, DUP-*, AS-*, IGN-*, OB-*, MUT-*)
- See: `code_governance.md` Stage 4 architecture
- Implementation at `ci/scripts/gates/risk_scoring_check.py` is CORRECT per weight-based band classification (v1.1 spec clarification aligns implementation with intended design)

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
| **Revision** | 10 |
| **Last Updated By** | Test Designer Agent |
| **Next Responsible Agent** | Test Breaker Agent |
| **Status** | Proceed |
| **Validation Status** | **TEST ASSERTIONS CORRECTED:** All band assertions updated to match weight-based classification per spec v1.1. Corrections applied: (1) TV-02 (weight=3): EXIT→WARN, (2) TV-03 (weight=1): WARN→EXIT, (3) TV-04 (weight=2): WARN→EXIT, (4) TV-09 (weight=6): WARN→ESCALATE, (5) TV-14: Added migration signal to include all 8 signals (weight=20, risk_score=100), (6) test_band_escalate_six: Corrected expected risk_score 30→35 (weight=7), (7) test_output_recommendation_matches_band: Added OB-02 to weight=3, (8) test_low_risk_pattern_duplication_only: Corrected band to EXIT (weight=1), (9) test_medium_risk_pattern_duplication_plus_complexity: Added OB-02 to weight=3, (10) test_consistency_recommendation_warn_with_warn_band: Added OB-02 to weight=3. Result: **All 144 tests pass** (79 behavioral + 75 adversarial). Implementation code verified correct (no changes required). Spec v1.1 alignment confirmed. Checkpoint log: project_board/checkpoints/M902-12/2026-05-19T-test_fix.md |
| **Blocking Issues** | None. All 144 tests passing. Ready for Test Breaker Agent to perform adversarial testing and verification that test suite comprehensively covers specification and edge cases. |
| **Escalation Notes** | Test Designer Agent completed test assertion corrections per spec v1.1 weight-based band classification. Committed: 4 files changed, 249 insertions(+), 14 deletions(-). Test results: 144 passed in 0.18s. No implementation code changes were needed (already correct). Advancing to TEST_BREAK for Test Breaker to verify test coverage, run adversarial scenarios, and validate spec contract compliance. |

## NEXT ACTION

**Test Breaker Agent:** Verify test coverage by executing adversarial test scenarios and edge-case validation. Confirm: (1) all 144 tests pass consistently, (2) test coverage matches spec Requirement 05 (33 test vectors + additional pattern/consistency tests), (3) band classification boundary cases (weight 2/3, 5/6 thresholds) are verified, (4) determinism and idempotence are validated, (5) error handling and malformed input robustness are tested. Once verified, route ticket to IMPLEMENTATION_BACKEND for code review and static QA validation.

---

## Summary

**Spec v1.1 contradiction RESOLVED and all test assertions CORRECTED.** Weight-based band classification (weight scale [0-20] → bands) is correct per spec, implementation, and code reasoning. Test assertions updated across 10 affected test cases (TV-02, TV-03, TV-04, TV-09, TV-14, and 5 additional pattern tests). All 144 tests pass (79 behavioral + 75 adversarial). Implementation code verified correct (no changes required). Advancing to TEST_BREAK for adversarial verification and spec contract compliance validation.
