# M902-12 AC Gatekeeper Checkpoint

**Date:** 2026-05-19  
**Stage:** INTEGRATION → AC VALIDATION  
**Status:** Blocked — Spec Contradiction Identified

## Summary

**Acceptance Criteria Analysis:**
- AC-1 through AC-7 all have implementation and test evidence
- Implementation correctly implements band classification per spec Requirement 03
- 10 test failures caused by contradiction between Requirement 03 and Requirement 05
- Spec issue, not implementation gap

## AC Evidence Matrix

| AC | Status | Evidence |
|---|---|---|
| AC-1 | EVIDENCED | Signal extraction function at lines 147-189; test vectors TV-01-15 validate; all tests pass |
| AC-2 | EVIDENCED | Signal catalog lines 31-64 with 8 signals; rule_id prefix mappings per spec; test coverage complete |
| AC-3 | UNRESOLVED | Band classification logic correct per Requirement 03; 10 tests fail due to Requirement 05 contradiction |
| AC-4 | EVIDENCED | Scoring matrix documented in spec Requirement 02 with weights and rationale |
| AC-5 | EVIDENCED | Module exists at correct path; exports run() function; registered in gate_registry.json; 7/7 contract tests pass |
| AC-6 | EVIDENCED | Output includes all 15 required fields; 16 contract tests pass; JSON serializability confirmed |
| AC-7 | PARTIALLY EVIDENCED | 154 test vectors defined; 134/144 pass; failures due to spec contradiction, not coverage gap |

## Spec Contradiction Analysis

### Issue: Requirement 03 vs Requirement 05

**Requirement 03 (Band Definitions):** Defines band thresholds on **weight scale**
- 0-2 → EXIT
- 3-5 → WARN
- 6+ → ESCALATE

**Requirement 05 (Test Vectors):** Expects band assignments that contradict Requirement 03

**Example Conflict:**
- Test vector TV-02: Single SRP violation (rule_id: AR-01)
  - Weight contribution: +3 (SRP ambiguity signal)
  - Risk score: (3/20)*100 = 15
  - TV-02 expectation: band=EXIT
  - Requirement 03 classification: weight 3 → WARN (3 ≤ weight ≤ 5)
  - Contradiction confirmed

**Root Cause:** Requirement 05 test vectors were likely written with a different interpretation of band thresholds (possibly score-based: 0-2→EXIT, 3-5→WARN instead of weight-based). When Implementation Agent built the gate, they correctly followed Requirement 03 (authoritative spec), causing test vector assertions to fail.

### Implementation Decision

Implementation Agent documented this in checkpoint (2026-05-19T-implementation.md):
- Recognized contradiction
- Chose to follow Requirement 03 (band definitions are authoritative spec language)
- Implemented weight-based band classification
- Documented decision with confidence level HIGH
- Noted that all core functionality (signal extraction, scoring, schema compliance) is correct

### Test Failure Breakdown

**Failing tests (10 total):** All failures are band classification assertions that conflict with Requirement 03

Examples:
- `test_tv_02_single_srp_violation`: expects weight=3 → band=EXIT (contradicts Requirement 03)
- `test_band_exit_two`: edge case with conflicting assertion
- Several `test_tv_*` vectors with weight-to-band mismatches

**Passing tests (134 total):**
- Module contract tests: 7/7 pass
- Signal extraction tests: all pass
- Output contract tests: 16/16 pass
- Adversarial tests: 75/75 pass
- Spec-aligned band tests: 5/6 pass (one has assertion bug, not a real failure)
- Determinism tests: all pass

## Core Functionality Assessment

**Signal Extraction:** ✓ Correct
- 8 signals properly detected from rule_id prefixes
- Weights correctly aggregated per violation count
- Migration detection via file path pattern works

**Scoring Formula:** ✓ Correct
- Implements (sum/20)*100 with floor rounding
- Clamped to [0, 100]
- Example: weight=10 → risk_score=50 ✓

**Band Classification:** ✓ Correct per Requirement 03
- Implements weight-based thresholds per spec
- If requirement intended score-based thresholds, spec should have been explicit

**Output Contract:** ✓ Complete
- All 15 required fields present
- Types and formats correct
- JSON serializable

**Code Quality:** ✓ Production-ready
- No bare except clauses
- Type hints present
- Exception handling explicit
- Performance <100ms for 100+ violations
- Deterministic output (TV-24, TV-25 pass)

## Decision Point

**Cannot gate Stage to COMPLETE** with 10 failing tests, per workflow_enforcement_v1.md § Tool, script, and test failures (lines 55-59):
> A non-zero exit code, thrown exception, missing executable, or unreadable required input is a **failure**, not product ambiguity. Do **not** use the checkpoint protocol to "assume away" a failed command or a red test suite.

However, **failures are due to spec contradiction**, not implementation gap.

**Resolution:** Route to Spec Agent to reconcile Requirement 03 and Requirement 05. Implementation is correct and should not be reworked; spec needs clarification.

## Checkpoint Protocol Resolution

### Would have asked
"Should AC-3 and AC-7 be gated as COMPLETE given that 10 tests fail due to a spec contradiction (Requirement 03 vs 05), but the implementation correctly implements the spec as written?"

### Assumption made
Implementation correctly follows Requirement 03 (authoritative band definitions). The 10 test failures are due to Requirement 05 having contradictory expectations. Per workflow enforcement, failing tests block COMPLETE, even if failures are due to spec issues. Route to Spec Agent to resolve contradiction. Do not override workflow enforcement just because the gap is spec-level rather than code-level.

### Confidence
HIGH. The contradiction is clearly documented in the implementation checkpoint. The implementation's choice to follow Requirement 03 is justified (spec text is authoritative). The failing tests are mathematically demonstrable contradictions, not ambiguous edge cases.

## Recommendations

1. **Spec Agent:** Authoritative decision required. Requirement 03 defines band thresholds explicitly; Requirement 05 test vectors don't match. Either:
   - *Option A (likely):* Accept weight-based band classification per Requirement 03, update test vectors to match.
   - *Option B (unlikely):* Change band definitions to score-based thresholds (would require spec and code changes).

2. **If Option A:** Test Designer/Test Breaker updates test vector assertions (TV-02, etc.) to match weight-based classification.

3. **If Option B:** Implementation Agent adjusts `_classify_band()` to use risk_score instead of total_weight.

4. **Implementation is solid:** No code rework needed if Option A is chosen; only test assertions need updating.

## Validation

- [x] All implementation paths code-reviewed (type hints, exception handling, logic)
- [x] No bare except clauses or silent failures
- [x] Signal extraction logic correct
- [x] Scoring formula correct (per spec)
- [x] Band classification correct per Requirement 03
- [x] Output contract complete and JSON-serializable
- [x] Performance acceptable
- [x] Determinism verified
- [x] Module registered and importable
- [ ] All tests passing (10 failures due to spec contradiction, not implementation)

