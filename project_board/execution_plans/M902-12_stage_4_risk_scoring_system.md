# M902-12 Execution Plan: Stage 4 — Semantic Risk Scoring System

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/12_stage_4_risk_scoring_system.md`  
**Plan Version:** 1.0  
**Created:** 2026-05-19  
**Status:** READY FOR EXECUTION

---

## Overview

This execution plan decomposes M902-12 into 7 sequential, testable tasks. The feature implements Stage 4 of the 8-stage governance pipeline: **Semantic Risk Scoring**. The gate computes a weighted risk score from violation signals detected by Stages 0–3 gates (diff classification, formatting, architecture enforcement) and determines whether high-risk changes warrant semantic extraction and agent review.

The gate must:
1. Ingest violation data and signals from prior gates (M902-09, M902-10, M902-11)
2. Define weighted signal catalog: SRP ambiguity, architecture drift, duplication clusters, async complexity, migration complexity, suppression usage, observability gaps, ownership ambiguity
3. Compute risk_score (0–100) from signal weights
4. Classify scoring bands: 0–2 EXIT, 3–5 WARN, 6+ ESCALATE
5. Return structured JSON with risk_score, reasoning, next_stage_recommendation
6. Register as `risk_scoring_check.py` in gate registry
7. Be tested with high/medium/low risk change patterns

**Dependencies:**
- M902-01 (Validation Gate Framework) — COMPLETE
- M902-09 (Stage 0 Diff Classification Gate) — COMPLETE
- M902-10 (Stage 1 Formatting Gate) — COMPLETE
- M902-11 (Stage 3 Architecture Enforcement Gate) — COMPLETE
- `code_governance.md` Stage 4 section — READ

**No gating blockers identified.**

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Specification freeze: Risk scoring matrix, signal catalog, output schema, classification bands | Spec Agent | Ticket M902-12, M902-01 gate schema, M902-09/10/11 specs for signal definitions, `code_governance.md` Stage 4 section | Spec file `project_board/specs/902_12_risk_scoring_spec.md` (requirements 01–07, acceptance criteria, test vectors, scoring matrix, signal weights) | M902-01, M902-09/10/11, code_governance.md | Spec completeness check passes; all 7 ticket ACs mapped to requirements; signal catalog enumerated with weights (SRP=+3, duplication=+1, async=+5, etc.); scoring bands frozen (0–2 EXIT, 3–5 WARN, 6+ ESCALATE); output schema validated against M902-01; at least 30 test vectors provided (high/medium/low risk patterns) | Q1: Should risk_score be cumulative (sum of weights) or normalized (average)? A: Weighted average per stage name ("risk scoring"), clamped [0–100]. Q2: Which signals are actionable vs informational? A: All signals included; downstream (M903) decides routing. Q3: Should suppression usage (blobert-ignore) affect scoring? A: Yes, +2 penalty per suppression (code governance violation signal). Q4: How to handle missing signals from prior gates? A: Conservative: treat as unknown (+0), not as missing (-1). Each stage output includes signal metadata. Q5: Is this gate blocking or shadow? A: Shadow (non-blocking advisory). Status is always PASS; risk_score guides downstream routing. Q6: Should migrations have special weight? A: Yes, +2 per migration file (represents schema risk). Q7: Should observability gaps weight scale with function count? A: No; flat +1 per observability violation detected by prior gates. Confidence: HIGH (scoring model well-defined in ticket description). |
| 2 | Test Design: Behavioral test suite for risk scoring gate | Test Designer Agent | Spec file from Task 1 | Test file `tests/ci/test_risk_scoring_check.py` with 50+ behavioral tests covering: (a) module signature & output schema, (b) low-risk patterns (formatting-only, docs-only, simple tests), (c) medium-risk patterns (minor SRP, some duplication), (d) high-risk patterns (circular imports, async violations, migration+SRP combo), (e) signal aggregation (multiple violations from same change), (f) band classification (0–2 EXIT, 3–5 WARN, 6+ ESCALATE), (g) registry integration, (h) error handling | Task 1 (Spec) | Tests cover all 7 ticket ACs; test vectors from spec (30+ minimum); deterministic (mocked prior gate outputs); syntax valid; all tests passing locally before handoff | Will mock M902-09/10/11 gate outputs to simulate various change scenarios. Will use parametrized tests for risk band boundaries. Reference M902-11 test suite for structure and patterns. Confidence: MEDIUM (risk scoring logic new; signal aggregation strategy must be validated). |
| 3 | Test Break: Adversarial & mutation test suite for risk scoring | Test Breaker Agent | Behavioral test suite from Task 2 | Additional test file `tests/ci/test_risk_scoring_check_adversarial.py` with 40+ adversarial tests covering: (a) signal weight mutation (incorrect weights, sum overflow), (b) boundary cases (risk_score=2.5 rounding, risk_score=5.99 vs 6), (c) empty signal set, (d) conflicting signals (high SRP + low complexity), (e) signal from non-existent violations, (f) schema validation edge cases (huge reasoning strings, null fields), (g) determinism (same input always yields same score), (h) assumption validation (prior gate outputs well-formed) | Task 2 (Behavioral tests) | 40+ adversarial tests; all tests passing; designed to catch rounding errors, weight edge cases, schema violations; deterministic; no external dependencies | Will focus on numerical precision and boundary rounding. Will encode conservative assumptions as checkpoint markers. Reference M902-11 adversarial suite for strategy. Confidence: MEDIUM. |
| 4 | Implementation: Python module `risk_scoring_check.py` with signal aggregation & scoring logic | Implementation Agent | Spec from Task 1, tests from Tasks 2–3 | Module `ci/scripts/gates/risk_scoring_check.py` with: (a) `run(inputs: dict) -> dict` function matching M902-01 gate schema, (b) signal ingestion from prior gates (via inputs dict or artifact references), (c) scoring matrix application (weight per signal, normalize to [0–100]), (d) band classification (return status consistent with score), (e) reasoning generation (explain which signals contributed to score), (f) output dict with risk_score, reasoning, next_stage_recommendation, (g) proper exception handling (no bare except), (h) logging per code_governance.md rules | Tasks 2–3 (tests define contract) | Module created; all tests pass (100% pass rate); code review passes (no bare except, no logging-only error handlers); scoring logic correct per spec matrix; output schema matches M902-01 | Will structure signal aggregation as separate functions (extract_signals, compute_score, classify_band) for testability. Prior gates (M902-09/10/11) output violations; this gate parses violations array to extract signals. Conservative: if a signal cannot be inferred from violations, assign weight 0 (not a failure). Confidence: MEDIUM (upstream signal availability must be documented). |
| 5 | Static QA: Code review, linting, type checking | Spec/Code Review Agent | Implementation from Task 4 | Code review report; module passes all linters (ruff, mypy, wemake rules); no bare except; proper logging; gate schema compliance validated; scoring logic verified against spec matrix | Task 4 (Implementation) | No ruff/mypy/wemake violations; no bare except; proper exception propagation; code follows M902-11/M902-10/M902-09 patterns; gate schema matches M902-01 | Reference M902-11 static QA for code review checklist. Use same logging, exception handling patterns. Verify scoring matrix against spec (spot-check 5+ signal weights). Confidence: HIGH (pattern well-established). |
| 6 | Integration: Register gate in `gate_registry.json`, verify orchestration path | Integration Agent | Module from Task 4 + Static QA from Task 5 | Updated `ci/scripts/gate_registry.json` with entry for `risk_scoring_check` gate (stage: 4, blocking: false, shadow: true); gate is callable by orchestrator; integration tests pass | Tasks 4–5 (implementation & review) | Registry entry created with correct metadata; gate is importable; orchestrator can call `run({})` with M902-11 output and receive valid JSON; integration tests pass (<5s execution time per test) | Will follow gate_registry.json schema from M902-09/11 (stage, blocking, shadow, description fields). risk_scoring_check is non-blocking (shadow=true); status always PASS per spec. Confidence: HIGH. |
| 7 | Acceptance Gatekeeper: Verify all 7 ticket ACs met, advance to COMPLETE | Spec Agent / Planner Agent | All deliverables from Tasks 1–6 | Gatekeeper report; ticket Stage advanced to COMPLETE; Revision incremented; Last Updated By set; all 7 ACs verified: (AC1) risk scoring function computes weighted inputs, (AC2) signals supported [list 8], (AC3) bands classify correctly, (AC4) matrix documented with rationale, (AC5) gate module at correct path, (AC6) returns JSON with risk_score/reasoning/recommendation, (AC7) tested with high/med/low risk patterns | Tasks 1–6 (all prior work) | All 7 ACs from ticket verified; implementation COMPLETE; tests passing (100%); code review clean; registry integrated; ticket Stage=COMPLETE | Gatekeeper must validate each AC: (1) spec has matrix with weights, (2) spec enumerates 8 signal types, (3) test suite has band boundary tests, (4) spec includes rationale for each weight, (5) module path correct, (6) output schema check, (7) test vectors cover patterns. Use M902-11 gatekeeper log as pattern. Confidence: HIGH. |

---

## Notes

### Dependencies & Ordering

- **Strict sequential:** Tasks must complete in order (1 → 2 → 3 → 4 → 5 → 6 → 7)
- **Task 1 (Spec)** requires reading `code_governance.md` Stage 4 section and M902-01/M902-09/M902-10/M902-11 for signal context
- **Tasks 2–3 (Tests)** can be done in parallel after Task 1 completes (though sequenced 2 → 3 per standard workflow)
- **Task 4 (Implementation)** depends on Tasks 2–3 for test contracts
- **Task 5 (Static QA)** depends on Task 4
- **Task 6 (Integration)** depends on Tasks 4–5
- **Task 7 (Acceptance)** depends on all prior tasks

### Signal Catalog (From Ticket AC-2)

The gate must support signals for:
1. **SRP ambiguity:** Single responsibility principle violations (domain imports HTTP, service constructs response, etc.)
2. **Architecture drift:** Dependency direction violations, cross-layer imports
3. **Duplication clusters:** Code duplication (8+ lines, cross-file)
4. **Async complexity:** Blocking I/O in async context, unbounded task spawning, missing timeouts
5. **Migration complexity:** Database/schema migrations (special handling; schema risk)
6. **Suppression usage:** Code governance rule suppressions (`blobert-ignore` comments)
7. **Observability gaps:** Missing structured logging, correlation IDs, audit events
8. **Ownership ambiguity:** Data ownership violations, DTO mutation outside owner layer

These signals are detected by M902-09 (diff), M902-10 (formatting), M902-11 (architecture). This gate (M902-12) aggregates them into a risk score.

### Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Signal aggregation strategy unclear (which violations map to which signals?) | MEDIUM | HIGH | Spec Agent must enumerate mapping rules (e.g., "AR-01 violation → +SRP ambiguity +3"). Document in Requirement 02 of spec. |
| Scoring matrix not well-calibrated (weights arbitrary, don't reflect actual risk) | MEDIUM | MEDIUM | Use code_governance.md Stage 4 as baseline. Spec Agent documents weight rationale. Tests validate boundaries (low/med/high patterns). Accept that initial weights are heuristic; can be tuned in M903. |
| Prior gates don't emit signal-level metadata (only violations) | MEDIUM | MEDIUM | This gate must infer signals from violations. Spec Agent documents inference rules (e.g., "if violation.rule_id starts with AR- → SRP signal"). Assumption: M902-09/10/11 outputs conform to gate schema with violations array. |
| Downstream orchestrator doesn't consume risk_score (gate output ignored) | LOW | LOW | Gate is advisory (non-blocking shadow mode). Spec defines output; M903 decides usage. No blocker. |
| Risk_score computation precision (floating point, rounding errors) | LOW | MEDIUM | Use integer arithmetic where possible. Clamp final score [0–100]. Test boundary cases (2.5 → 2 or 3? 5.99 → 5 or 6?). Spec freezes rounding rule (e.g., "round down" or "banker's rounding"). |
| Performance (aggregating many violations, computing scores) | LOW | LOW | Expect <1s per run (simple arithmetic). Stress test with 100+ violations in Task 3. |

### Assumptions

1. **Prior gate outputs conform to M902-01 schema:** M902-09/10/11 return dicts with violations array. This gate parses that array.
2. **Violation rule_id identifies signal type:** Spec Agent maps rule_id prefixes to signals (e.g., AR- → architecture, AS- → async).
3. **Signal weights frozen in spec:** Once spec is approved, weights are immutable (changeable in M903 via configuration, not code).
4. **Scoring model is linear (additive):** Risk_score = sum(signal_weights) / total_possible_weight * 100. Alternatives (multiplicative, Bayesian) deferred.
5. **Bands are hard thresholds:** 0–2 EXIT (no escalation), 3–5 WARN (advisory), 6+ ESCALATE (high risk). No fuzzy boundaries.
6. **Gate is always non-blocking:** Status always "PASS" (shadow mode). Routing decisions deferred to M903 orchestrator.
7. **Missing signals treated as 0 weight, not unknown:** If a gate output doesn't include a signal, assume that signal is absent (weight +0), not missing data.
8. **Gate output schema from M902-01:** Output must conform to gate-result-success.json structure. risk_score, reasoning, next_stage_recommendation are additional fields beyond base schema.

### Deferred Scope (M903+)

- Orchestration and routing decisions based on risk_score (which pipeline stages to skip/escalate)
- Signal weight tuning/configuration per project risk tolerance
- Machine learning-based risk refinement
- Agent semantic review integration (Stage 6)
- Dynamic risk rule injection from agent layer
- Risk_score tracking and trending over time

---

## Signal-to-Violation Mapping (For Spec Agent)

The following mapping is a starting point. Spec Agent must validate and freeze this in Requirement 02.

| Signal Type | Rule ID Prefix(es) | Example Violation | Suggested Weight | Rationale |
|---|---|---|---|---|
| SRP ambiguity | AR-01, AR-02, AR-03, AR-04, AR-05, AR-06, MUT-01, MUT-02 | Domain imports fastapi | +3 | SRP violations are architecture blockers; moderate escalation |
| Architecture drift | AR-07, AR-08 | Circular import detected | +5 | Circular imports block compilation; high risk |
| Duplication clusters | DUP-01, DUP-02 | 15 lines duplicated across 3 files | +1 | Duplication is maintenance debt; low risk per se |
| Async complexity | AS-01, AS-02, AS-03, AS-04 | Blocking I/O in async context | +5 | Async violations are runtime hazards; high risk |
| Migration complexity | (migration files detected in diff) | `alembic/versions/001_add_column.py` | +2 | Migrations represent schema risk; moderate escalation |
| Suppression usage | (blobert-ignore comments in violations) | Code with governance suppressions | +2 | Suppressions signal intentional rule-breaking; moderate risk |
| Observability gaps | OB-01, OB-02, OB-03 | Missing audit event on critical op | +1 | Observability gaps are ops debt; low risk per se |
| Ownership ambiguity | MUT-03 | DTO instantiated in wrong layer | +1 | Ownership violations indicate coupling; low-to-moderate risk |

**Total possible weight (all 8 signals at 1x):** 3 + 5 + 1 + 5 + 2 + 2 + 1 + 1 = 20 (normalized to [0–100]: divide by 20, multiply by 100)

**Scoring bands:**
- 0–2: EXIT (no action needed)
- 3–5: WARN (monitor, minor escalation)
- 6+: ESCALATE (high risk, recommend review)

---

## File Paths (Source of Truth)

**Input files:**
- Ticket: `/Users/jacobbrandt/workspace/blobert/project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/12_stage_4_risk_scoring_system.md`
- Code governance: `/Users/jacobbrandt/workspace/blobert/bot_vault/architecture/code_governance.md` (Stage 4 section)
- Gate framework (M902-01): `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_01_gate_runner_spec.md`
- Stage 0 spec (M902-09): `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_09_diff_classification_gate_spec.md`
- Stage 1 spec (M902-10): `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_10_formatting_gate_spec.md`
- Stage 3 spec (M902-11): `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_11_architecture_enforcement_gate_spec.md`
- Reference implementation (M902-09): `/Users/jacobbrandt/workspace/blobert/ci/scripts/gates/diff_classification.py`
- Reference implementation (M902-10): `/Users/jacobbrandt/workspace/blobert/ci/scripts/gates/formatting_check.py`
- Reference implementation (M902-11): `/Users/jacobbrandt/workspace/blobert/ci/scripts/gates/architecture_enforcement_check.py`
- Reference tests (M902-11): `/Users/jacobbrandt/workspace/blobert/tests/ci/test_architecture_enforcement_check.py`, `test_architecture_enforcement_check_adversarial.py`

**Output files:**
- Spec: `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_12_risk_scoring_spec.md` (Task 1)
- Behavioral tests: `/Users/jacobbrandt/workspace/blobert/tests/ci/test_risk_scoring_check.py` (Task 2)
- Adversarial tests: `/Users/jacobbrandt/workspace/blobert/tests/ci/test_risk_scoring_check_adversarial.py` (Task 3)
- Implementation: `/Users/jacobbrandt/workspace/blobert/ci/scripts/gates/risk_scoring_check.py` (Task 4)
- Registry: `/Users/jacobbrandt/workspace/blobert/ci/scripts/gates/gate_registry.json` (Task 6, update only)
- Execution plan (this file): `/Users/jacobbrandt/workspace/blobert/project_board/execution_plans/M902-12_stage_4_risk_scoring_system.md`

---

## Execution Readiness Checklist

- [x] All tasks are small, single-objective, and self-contained
- [x] Dependencies are explicit and ordered correctly
- [x] Success criteria are measurable and testable
- [x] Risks and assumptions are documented with confidence levels
- [x] File paths are absolute and verified to exist (input files)
- [x] No blocking issues remain (all hard dependencies M902-01/09/10/11 COMPLETE)
- [x] Spec Agent has sufficient context (M902-01 schema, M902-09/10/11 prior gates, code_governance Stage 4)
- [x] Test Designers have reference implementations (M902-09, M902-10, M902-11 test suites)
- [x] Implementation Agent has test contracts to implement against
- [x] Integration Agent has clear registry schema and gate contract
- [x] Gatekeeper has AC mapping and acceptance criteria list (7 ACs all traceable)

**Plan is READY FOR HANDOFF to Spec Agent.**
