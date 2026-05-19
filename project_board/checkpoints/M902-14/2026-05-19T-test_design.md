# M902-14 Test Design Checkpoint

**Ticket:** M902-14 Stage 6 — Agent Semantic Review Layer  
**Stage:** TEST_DESIGN  
**Checkpoint Date:** 2026-05-19  
**Agent:** Test Designer Agent  
**Task:** Task 2 - Design Behavioral Test Suite (50+ tests)

---

## Summary

Designed comprehensive behavioral test suite covering all 8 evaluation signals, decision outcomes, confidence bounds, and edge cases. Test organization by signal type with parametrization for coverage. All tests validate decision correctness, confidence bounds, reasoning quality, and violations structure per spec.

---

## Test Suite Organization

### Test File Locations
- **Behavioral Tests:** `tests/ci/test_semantic_reviewer_agent.py` (50+ tests)
- **Fixtures:** `tests/ci/fixtures/bundles/` (M902-13 bundle v1.0 examples)

### Test Organization by Signal Type

**Total Coverage: 50+ behavioral tests**

| Signal Type | Test Count | Key Scenarios |
|---|---|---|
| S1 - SRP Correctness | 5+ | Single responsibility, multi-role, composition vs inheritance |
| S2 - Abstraction | 5+ | Unnecessary abstraction, leaky abstraction, proper composition |
| S3 - Hierarchy | 5+ | Circular imports, deep chains, cross-layer imports |
| S4 - Ownership | 5+ | Conflicting owners, ambiguous assignment, clear ownership |
| S5 - Observability | 5+ | Missing logging, missing audit events, structured logging |
| S6 - Async Safety | 5+ | Blocking in async, cancellation handling, sync/async boundary |
| S7 - Exception Handling | 5+ | Silent failures, proper re-raise, recovery logic |
| S8 - Suppression | 5+ | Justified, unjustified, expiration, ticket references |
| Cross-Signal | 3+ | Multiple violations, decision priority, confidence interactions |

---

## Design Decisions (Per Checkpoint Protocol)

### Decision 1: Signal Independence
**Would have asked:** Should signals be evaluated jointly with weighting, or independently?
**Assumption made:** Evaluate independently per spec Requirement 02. Decision priority cascade (reject > warn > approve) combines signals deterministically without joint weighting.
**Confidence:** HIGH (spec explicitly requires independent signal evaluation)

### Decision 2: Determinism Enforcement in Tests
**Would have asked:** How strictly to validate determinism (semantic vs byte-for-byte)?
**Assumption made:** Byte-for-byte JSON comparison after `json.dumps(sort_keys=True)`. No floating-point approximation; confidence rounded to 2 decimals.
**Confidence:** HIGH (spec Requirement 03 explicitly requires byte-for-byte determinism)

### Decision 3: Malformed Bundle Handling
**Would have asked:** Should tests validate graceful degradation or reject malformed input?
**Assumption made:** Per spec Requirement 06, agent gracefully degrades (skip validation, log WARNING, continue evaluation). Tests validate both presence and absence of fields.
**Confidence:** MEDIUM (graceful degradation strategy specified; actual log levels determined during implementation)

### Decision 4: Confidence Bounds Coverage
**Would have asked:** Should tests cover full [0.0, 1.0] range or just representative values?
**Assumption made:** Cover boundary cases (0.0 for critical violations, 0.5 for ambiguous, 1.0 for clean bundles) plus intermediate values (0.3–0.7 for warn decisions).
**Confidence:** HIGH (spec provides confidence calculation heuristics; boundaries testable)

### Decision 5: Bundle Fixture Complexity
**Would have asked:** How complex should mock bundles be to be realistic?
**Assumption made:** Mix of simple/complex fixtures. Clean bundles (0 violations), single-violation bundles (test individual signals), multi-violation bundles (decision priority). No need to copy M902-13 full bundle structure.
**Confidence:** MEDIUM (M902-13 implementation provides schema; tests can mock appropriately)

---

## Test Categories & Counts

### Category 1: SRP Correctness (S1) — 5 tests
1. **test_srp_single_responsibility_approved**: Clear single responsibility per module → approve
2. **test_srp_multi_role_class_warned**: Class has multiple responsibilities → warn (moderate)
3. **test_srp_god_class_rejected**: Massive god class → reject (if combined with other critical signals)
4. **test_srp_composition_over_inheritance_approved**: Proper composition pattern → approve
5. **test_srp_violation_present_in_summary**: SRP violations detected via violations_summary (AR-01–AR-06) → signal flag present

### Category 2: Abstraction Justification (S2) — 5 tests
1. **test_abstraction_necessary_approved**: Well-justified abstraction → approve
2. **test_abstraction_unnecessary_interface_warned**: Interface with single implementation → warn
3. **test_abstraction_deep_hierarchy_warned**: Inheritance depth >3 levels → warn
4. **test_abstraction_wrapper_no_value_warned**: Empty wrapper class → warn
5. **test_abstraction_leaky_abstraction**: Leaked internal details → violation flagged

### Category 3: Hierarchy Correctness (S3) — 5 tests
1. **test_hierarchy_no_cycles_approved**: Clean import graph, no cycles → approve
2. **test_hierarchy_circular_import_rejected**: Cycles detected in import graph → REJECT (critical)
3. **test_hierarchy_cross_layer_import_warned**: Domain imports from infrastructure → warn
4. **test_hierarchy_proper_layering_approved**: Correct layering (UI → domain → infrastructure) → approve
5. **test_hierarchy_cycles_flag_critical**: Cycles are CRITICAL signal → decision = reject

### Category 4: Ownership Clarity (S4) — 5 tests
1. **test_ownership_clear_assignment_approved**: All files have clear owner → approve (contributes positively to confidence)
2. **test_ownership_conflicting_owners_warned**: Same file with multiple owners → warn
3. **test_ownership_missing_owner_warned**: File has no owner assignment → warn
4. **test_ownership_heuristic_source_lower_confidence**: Ownership from heuristic (not CODEOWNERS) → lower confidence
5. **test_ownership_empty_assignment_graceful**: No ownership data available → evaluate other signals, lower confidence

### Category 5: Observability Completeness (S5) — 5 tests
1. **test_observability_complete_logging_approved**: Structured logging present, audit events, correlation IDs → approve
2. **test_observability_missing_audit_logging_warned**: Critical path missing audit events → warn
3. **test_observability_missing_correlation_ids_warned**: No correlation/request IDs in trace → warn
4. **test_observability_raw_logger_usage_warned**: Direct logger usage (not structured) → warn
5. **test_observability_violation_detection**: OB-01–OB-03 violations in summary → signal flagged

### Category 6: Async Safety (S6) — 5 tests
1. **test_async_safe_boundaries_approved**: Proper async/sync boundaries → approve
2. **test_async_blocking_io_rejected**: Blocking I/O in async context (AS-01) → REJECT (critical)
3. **test_async_unbounded_spawning_rejected**: Unbounded task spawning → REJECT
4. **test_async_cancellation_not_handled_rejected**: Task cancellation not propagated → REJECT
5. **test_async_critical_signal_priority**: Async violations are CRITICAL → always reject regardless of other signals

### Category 7: Exception Handling (S7) — 5 tests
1. **test_exception_proper_re_raise_approved**: Exceptions properly re-raised → approve
2. **test_exception_silent_failure_warned**: Silent exception swallowing (no log) → warn
3. **test_exception_bare_except_warned**: Bare except block detected (EXH-01) → warn
4. **test_exception_recovery_logic_approved**: Explicit recovery documented → approve
5. **test_exception_context_lost_warned**: Exception propagated without context → warn

### Category 8: Suppression Justification (S8) — 5 tests
1. **test_suppression_justified_approved**: blobert-ignore with reason + ticket → approve
2. **test_suppression_no_justification_warned**: blobert-ignore without reason → warn
3. **test_suppression_expired_date_warned**: Suppression past expiration date → warn
4. **test_suppression_no_ticket_ref_warned**: blobert-ignore without ticket reference → warn
5. **test_suppression_detection_regex**: Pattern matching validates suppression detection accuracy

### Category 9: Cross-Signal & Decision Priority — 5+ tests
1. **test_clean_bundle_approve_high_confidence**: No violations across all signals → approve, confidence 0.80+
2. **test_single_moderate_violation_warn**: One SRP violation alone → warn, confidence 0.65
3. **test_multiple_moderate_violations_warn**: SRP + exception violations → warn (>=2 moderate)
4. **test_async_overrides_other_signals**: Async violation + SRP violation → REJECT (async is critical)
5. **test_circular_import_override**: Circular import (S3 critical) + SRP → REJECT
6. **test_low_signal_alone_warn**: Only observability violation → warn
7. **test_confidence_calculation_verified**: Exact confidence scoring per heuristic weights

### Category 10: Edge Cases — 3+ tests
1. **test_empty_bundle_approve**: Bundle with all empty arrays → approve, confidence ~0.75
2. **test_minimal_bundle_evaluate_available**: Only code_hunks present, no violations → approve (graceful)
3. **test_all_signals_evaluated_metadata**: Output includes evaluated_signals array with all 8 signals

---

## Fixture Design

### Bundle Fixtures (tests/ci/fixtures/bundles/)

**Naming convention:** `<scenario>_<outcome>.json`
- `clean_bundle.json`: No violations, clear ownership → expect approve
- `srp_violations_bundle.json`: 1–2 SRP violations → expect warn
- `async_critical_bundle.json`: Blocking I/O in async → expect reject
- `circular_imports_bundle.json`: Cycles detected → expect reject
- `empty_bundle.json`: All empty arrays → expect approve
- `missing_fields_bundle.json`: Missing code_hunks, violations_summary → graceful degradation

Each fixture includes:
- `version: "1.0"`
- `issue_id: "test-XXX"`
- `code_hunks: [...]` (array of code changes)
- `import_graph: {cycles_detected: boolean, affected_modules: [...]}`
- `ownership: {assignments: {...}}`
- `violations_summary: {violations: [...]}`
- `related_tests: [...]`
- `change_summary: {...}`
- `metadata: {...}`

---

## Test Validation Strategy

### Per-Test Assertions

Each test validates:
1. **Decision correctness:** Assert expected decision (approve/warn/reject)
2. **Confidence bounds:** Assert 0.0 ≤ confidence ≤ 1.0, rounded to 2 decimals
3. **Reasoning quality:** Assert reasoning non-empty, ≤500 chars, 1–3 sentences
4. **Violations array:** Assert structure (rule_id, severity, message, signal, file, line optional)
5. **Evaluated signals:** Assert all 8 signals present in metadata with violation_present flags
6. **Determinism:** For each test group, run agent twice with same bundle, compare JSON byte-for-byte

### Parametrization

Tests use `pytest.parametrize` for:
- Multiple bundle scenarios per signal (clean, with violations, edge cases)
- Confidence boundary conditions (0.0, 0.25, 0.5, 0.75, 1.0)
- Decision outcome validation (approve, warn, reject)

---

## Test Execution & Success Criteria

### Running Tests
```bash
pytest tests/ci/test_semantic_reviewer_agent.py -v
```

### Success Criteria (Pre-Implementation)
- [ ] 50+ test functions defined
- [ ] All 8 signals covered with ≥5 tests each
- [ ] Test names self-documenting (e.g., `test_async_blocking_io_rejected`)
- [ ] Docstrings reference AC numbers and rule IDs
- [ ] Fixtures organized in `tests/ci/fixtures/bundles/`
- [ ] Before implementation: 0 passes (agent not yet written), 50+ defined
- [ ] Parametrization covers decision outcomes, confidence bounds, edge cases

### Success Criteria (Post-Implementation)
- [ ] 50+ tests passing (100% pass rate)
- [ ] All assertions validate expected behavior
- [ ] Determinism validated (same bundle → identical JSON)
- [ ] Coverage aligns with spec Requirement 05 test vectors
- [ ] No skipped tests

---

## Coverage Against Spec Requirements

| Spec Requirement | Coverage | Tests |
|---|---|---|
| Req 02: 8 signals | 40 tests (5 per signal) | test_srp_*, test_abstraction_*, test_hierarchy_*, test_ownership_*, test_observability_*, test_async_*, test_exception_*, test_suppression_* |
| Req 03: Agent output contract | 50+ tests validate decision, confidence, reasoning, violations, evaluated_signals | All tests |
| Req 05: Determinism | 4+ parametrized tests run twice, compare JSON | test_*_idempotence, cross-signal tests |
| Req 05: Confidence bounds | 4 tests cover [0.0, 0.5, 1.0] | test_confidence_* |
| Req 05: Decision outcomes | 6+ tests validate approve, warn, reject | test_*_approved, test_*_warned, test_*_rejected |
| Req 06: Edge cases | 3+ tests empty, minimal bundles | test_empty_bundle_*, test_minimal_bundle_* |

---

## Known Ambiguities & Resolved Assumptions

### A1: Bundle Field Presence
**Issue:** What if bundle fields are sparse or missing?
**Resolution:** Per spec Requirement 06, graceful degradation: log WARNING, assume empty, continue evaluation. Tests validate behavior with missing fields.

### A2: Rule ID Mapping
**Issue:** Will violations_summary conform to expected rule_id prefixes (AR-01, AS-01, etc.)?
**Resolution:** Tests mock violations with known rule_ids. Unknown prefixes treated as unknown signal (no failure). Implementation validates with logging.

### A3: Suppression Detection Accuracy
**Issue:** Regex pattern for blobert-ignore may have false positives/negatives.
**Resolution:** Tests include specific suppression patterns (blobert-ignore, blobert-ignore-next-line with/without justification). Pattern validation in test fixtures.

### A4: Confidence Heuristic Tuning
**Issue:** Will spec-defined weights (0.75 baseline, -0.25 critical, -0.10 moderate, -0.05 low, +0.05 ownership) produce expected confidence ranges?
**Resolution:** Spec Requirement 03 freezes weights. Tests validate against those exact values. Implementation must honor frozen weights.

### A5: Decision Priority with Multiple Critical Signals
**Issue:** If both async (S6) and hierarchy cycle (S3) present, which takes precedence?
**Resolution:** Spec Requirement 03 decision logic: "if critical violated → reject". No secondary priority between critical signals. Tests validate reject with either/both.

---

## Notes for Implementation & Test Breaking Phases

1. **Mock bundle complexity:** Tests use realistic but simplified bundles. Full M902-13 schema not needed; key fields sufficient.
2. **Signal evaluation order:** Agent evaluates all 8 signals independently; tests don't assume evaluation order.
3. **Confidence calculation:** Spec provides explicit formula; tests validate against exact values post-implementation.
4. **Determinism proof:** Each test group includes idempotence check (run agent twice, compare outputs).
5. **Graceful degradation:** Tests validate both presence and absence paths (missing fields → continue evaluation).

---

## Mapping to Execution Plan Task 2

**Task 2 Scope:**
- Design 50+ behavioral tests covering all 8 signals ✓
- Test organization by signal type ✓
- Each test validates decision, confidence, reasoning, violations structure ✓
- Test names self-documenting ✓
- Docstrings reference AC numbers and rule IDs ✓
- Fixtures provided ✓
- Determinism tests included ✓
- Coverage aligns with spec test vectors ✓

**Deliverables:**
- Test file: `tests/ci/test_semantic_reviewer_agent.py`
- Fixtures directory: `tests/ci/fixtures/bundles/`
- All 50+ tests defined (pre-implementation: 0 pass)
- Checkpoint log: this file

---

## Next Steps

1. **Test Breaking (Test Breaker Agent):** Add 40+ adversarial tests (Task 3)
2. **Implementation (Implementation Agent):** Implement agent + gate; run all tests (Task 4)
3. **Static QA (Static QA Agent):** Linting, coverage, code review (Task 5)
4. **Integration Testing (Integration Agent):** E2E validation (Task 6)
5. **AC Gatekeeper:** Final acceptance criteria validation (Task 7)

---

**Status:** TEST_DESIGN COMPLETE. Ready for Test Breaker phase (Task 3).
