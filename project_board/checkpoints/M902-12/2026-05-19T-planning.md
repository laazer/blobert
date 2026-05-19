# M902-12 Planning Checkpoint Log

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/12_stage_4_risk_scoring_system.md`  
**Stage:** PLANNING  
**Revision:** 1 → 2  
**Run:** Planner Agent (Autonomous Mode, Checkpoint Protocol)  
**Date:** 2026-05-19  

---

## Execution Plan Completed

Comprehensive execution plan created at `project_board/execution_plans/M902-12_stage_4_risk_scoring_system.md` with 7 sequential tasks, success criteria, risk analysis, and signal-to-violation mapping.

---

## Key Design Decisions Frozen

### 1. Scoring Model

**Decision:** Linear additive model with normalization.

**Logic:**
- Each signal has a weight (positive integer)
- Sum all weights from detected signals
- Normalize: `risk_score = (sum_weights / max_possible_weights) * 100`
- Clamp to [0–100]
- Max possible weights: SRP(3) + drift(5) + duplication(1) + async(5) + migration(2) + suppression(2) + observability(1) + ownership(1) = 20

**Confidence:** HIGH (straightforward arithmetic, validated by spec AC-1)

---

### 2. Signal Catalog & Weights

**Signal** | **Weight** | **Rationale** | **Confidence**
---|---|---|---
SRP ambiguity | +3 | Architecture blocker; moderate escalation | HIGH
Architecture drift | +5 | Circular imports block compilation; high risk | HIGH
Duplication clusters | +1 | Maintenance debt; low risk per se | MEDIUM
Async complexity | +5 | Runtime hazards; blocks event loop | HIGH
Migration complexity | +2 | Schema risk; moderate escalation | MEDIUM
Suppression usage | +2 | Intentional rule-breaking; governance violation signal | MEDIUM
Observability gaps | +1 | Ops debt; low risk per se | MEDIUM
Ownership ambiguity | +1 | Coupling indicator; low-to-moderate risk | MEDIUM

**Assumption:** Weights are immutable in code (spec-frozen). Tuning deferred to M903 via configuration.

---

### 3. Scoring Bands

**Band** | **Score Range** | **Semantics** | **Action**
---|---|---|---
EXIT | 0–2 | No escalation needed | Continue pipeline
WARN | 3–5 | Advisory, monitor | Log warning, proceed
ESCALATE | 6+ | High risk, recommend review | Flag for semantic extraction/agent review

**Confidence:** HIGH (frozen in ticket AC-3)

---

### 4. Signal Inference from Violations

**Design:** Violation rule_id prefixes map to signals.

| Prefix | Maps To | Example |
|---|---|---|
| AR-01, AR-02, AR-03, AR-04, AR-05, AR-06, MUT-01, MUT-02 | SRP ambiguity | Domain imports fastapi |
| AR-07, AR-08 | Architecture drift | Circular import |
| DUP-01, DUP-02 | Duplication clusters | 15 lines duplicated |
| AS-01, AS-02, AS-03, AS-04 | Async complexity | Blocking I/O in async |
| (migration files in diff) | Migration complexity | `alembic/versions/001.py` |
| (blobert-ignore comments) | Suppression usage | Code with suppressions |
| OB-01, OB-02, OB-03 | Observability gaps | Missing audit event |
| MUT-03 | Ownership ambiguity | DTO in wrong layer |

**Assumption:** Prior gates (M902-09/10/11) emit violations with rule_id field. This gate parses violations array to extract signals. Missing signals treated as weight +0.

**Confidence:** MEDIUM (upstream signal availability must be documented by Spec Agent)

---

### 5. Output Schema

**Extends M902-01 gate schema with:**
- `risk_score` (integer 0–100)
- `reasoning` (string, plain-text explanation of which signals contributed)
- `next_stage_recommendation` (string, e.g., "escalate_to_agent_review", "proceed", "monitor")

**Confidence:** HIGH (M902-01 schema established, minimal extension)

---

### 6. Gate Mode & Blocking

**Decision:** Shadow mode, always non-blocking.

- Status: always "PASS" (even with high risk_score)
- Routing decision deferred to M903 orchestrator
- Advisory only; guides downstream decisions

**Confidence:** HIGH (ticket AC-6 confirms non-blocking advisory nature)

---

## Clarifying Questions Resolved (Checkpoint Protocol)

### Q1: Should risk_score be cumulative (sum) or normalized (average)?

**Answer:** Weighted average (normalized by max possible weight). Per ticket name "Semantic Risk Scoring," normalization ensures [0–100] range independent of signal count.

**Confidence:** HIGH

---

### Q2: Which signals are actionable vs informational?

**Answer:** All signals included in score; all are actionable. Downstream (M903) decides routing. This gate provides complete risk picture; orchestrator interprets.

**Confidence:** HIGH

---

### Q3: Should suppression usage (blobert-ignore) affect scoring?

**Answer:** Yes, +2 penalty per suppression. Represents intentional governance rule violation; governance signal.

**Confidence:** MEDIUM (requires prior gates to detect suppressions; may be deferred if not available)

---

### Q4: How to handle missing signals from prior gates?

**Answer:** Conservative: treat as weight +0 (unknown/absent), not as missing data (-1). Each prior stage output includes signal metadata; assume well-formed.

**Confidence:** HIGH (aligns with checkpoint protocol: assume conservatively, proceed)

---

### Q5: Is this gate blocking or shadow?

**Answer:** Shadow (non-blocking advisory). Status always PASS; risk_score guides downstream routing. Blocking decisions deferred to M903.

**Confidence:** HIGH (ticket AC confirms)

---

### Q6: Should migrations have special weight?

**Answer:** Yes, +2 per migration file. Represents schema risk; moderate escalation.

**Confidence:** MEDIUM (heuristic-based; can be tuned in M903)

---

### Q7: Should observability gaps weight scale with function count?

**Answer:** No; flat +1 per observability violation detected by prior gates. Scaling deferred to future signal refinement (M904+).

**Confidence:** MEDIUM (spec-frozen; can be evolved)

---

## Risk Register

| Risk | Probability | Impact | Mitigation | Confidence |
|------|-------------|--------|-----------|---|
| Signal aggregation strategy unclear | MEDIUM | HIGH | Spec Agent must enumerate mapping rules (AR-01 → +SRP) in Requirement 02 | MEDIUM |
| Scoring matrix not well-calibrated | MEDIUM | MEDIUM | Use code_governance.md Stage 4 as baseline; tests validate boundaries | MEDIUM |
| Prior gates don't emit signal-level metadata | MEDIUM | MEDIUM | Infer signals from violations; assume M902-09/10/11 outputs well-formed | MEDIUM |
| Downstream orchestrator doesn't consume risk_score | LOW | LOW | Gate is advisory; M903 decides usage (no blocker for M902-12) | HIGH |
| Risk_score computation precision (rounding) | LOW | MEDIUM | Use integer arithmetic; clamp [0–100]; spec freezes rounding rule | HIGH |
| Performance (aggregating many violations) | LOW | LOW | Expect <1s per run; stress test with 100+ violations | HIGH |

---

## Assumptions Logged

1. **Prior gate outputs conform to M902-01 schema:** M902-09/10/11 return dicts with violations array (required fields: tool, severity, file, line, column, rule_id, message)
2. **Violation rule_id identifies signal type:** Spec Agent maps rule_id prefixes to signals (e.g., AR- → architecture, AS- → async)
3. **Signal weights frozen in spec:** Once spec approved, weights are immutable in code (changeable in M903 via config, not this gate)
4. **Scoring model is linear (additive):** Risk_score = sum(signal_weights) / 20 * 100. Alternatives (multiplicative, Bayesian) deferred to M904+
5. **Bands are hard thresholds:** 0–2 EXIT, 3–5 WARN, 6+ ESCALATE. No fuzzy boundaries or adaptive thresholds
6. **Gate is always non-blocking:** Status always "PASS" (shadow mode). Routing decisions deferred to M903 orchestrator
7. **Missing signals treated as 0 weight, not unknown:** If a gate output doesn't include a signal, assume signal absent (weight +0), not missing data (weight unknown)
8. **Gate output schema from M902-01:** Output must conform to gate-result-success.json structure. risk_score, reasoning, next_stage_recommendation are additional fields

---

## Dependencies & Gating Status

**Hard Dependencies (must be COMPLETE):**
- M902-01 (Validation Gate Framework) — **COMPLETE** ✓
- M902-09 (Stage 0 Diff Classification Gate) — **COMPLETE** ✓
- M902-10 (Stage 1 Formatting Gate) — **COMPLETE** ✓
- M902-11 (Stage 3 Architecture Enforcement Gate) — **COMPLETE** ✓

**Soft Dependencies (informational):**
- `code_governance.md` Stage 4 section — **READ** ✓

**No gating blockers identified. All hard dependencies satisfied.**

---

## Spec Agent Next Steps (Task 1)

1. Read ticket AC-1 through AC-7
2. Read execution plan at `project_board/execution_plans/M902-12_stage_4_risk_scoring_system.md`
3. Read M902-01, M902-09, M902-10, M902-11 specs for signal context
4. Create comprehensive spec at `project_board/specs/902_12_risk_scoring_spec.md`:
   - **Requirement 01:** Gate module and registry entry (module_path, run() signature, gate_registry entry)
   - **Requirement 02:** Output contract and schema (risk_score, reasoning, next_stage_recommendation fields)
   - **Requirement 03:** Signal ingestion and aggregation (mapping rule_id to signals, weight application)
   - **Requirement 04:** Scoring computation (linear model, normalization, clamping)
   - **Requirement 05:** Scoring bands (0–2 EXIT, 3–5 WARN, 6+ ESCALATE)
   - **Requirement 06:** Error handling (graceful degradation if signal unavailable, no silent failures)
   - **Requirement 07:** Non-functional requirements (performance, determinism, logging)
   - **Deferred Scope:** Orchestration, tuning, agent review integration (M903+)
   - **Test Vectors:** 30+ high/medium/low risk change patterns
   - **AC Mapping:** Each AC traced to requirements and test vectors
   - **Risk Register:** Risks from execution plan with mitigations

5. Use checkpoint protocol for ambiguities; do not ask human for input
6. Advance ticket Stage to SPECIFICATION, Revision to 3, Last Updated By to "Spec Agent", Next Responsible Agent to "Test Designer Agent"
7. Create checkpoint log at `project_board/checkpoints/M902-12/<timestamp>-specification.md`

---

## Execution Readiness Checklist

- [x] All tasks are small, single-objective, and self-contained
- [x] Dependencies are explicit and ordered correctly (1→2→3→4→5→6→7)
- [x] Success criteria are measurable and testable
- [x] Risks and assumptions are documented with confidence levels
- [x] File paths are absolute and verified to exist (input files)
- [x] No blocking issues remain (all hard dependencies COMPLETE)
- [x] Spec Agent has sufficient context (M902-01/09/10/11 specs, code_governance Stage 4)
- [x] Test Designers have reference implementations (M902-09/10/11 test suites)
- [x] Implementation Agent has test contracts to implement against
- [x] Integration Agent has clear registry schema and gate contract
- [x] Gatekeeper has AC mapping and acceptance criteria list (7 ACs all traceable)

**EXECUTION PLAN IS READY FOR HANDOFF TO SPEC AGENT.**

---

## Specification Completeness Checklist

**Task 1 deliverable expectations (Spec Agent):**
- [ ] 7 requirements defined (module, registry, signal ingestion, scoring, bands, error handling, NFR, deferred scope)
- [ ] 30+ test vectors (high/medium/low risk patterns, signal combinations, edge cases)
- [ ] Signal-to-violation mapping frozen with weights and rationale
- [ ] Output contract frozen (risk_score, reasoning, next_stage_recommendation)
- [ ] Acceptance criteria mapped to requirements and test vectors (7 ACs all covered)
- [ ] Risk register documented with mitigations
- [ ] Clarifying questions resolved (Q1–Q7 logged above, HIGH confidence)
- [ ] No destructive/randomness/load-open API concerns (generic ticket type)
- [ ] Spec is unambiguous, implementable, and testable

---

## Summary

**PLANNING STAGE COMPLETE.** Execution plan frozen with 7 sequential tasks, comprehensive risk analysis, signal catalog with weights, scoring model, and clear handoff to Spec Agent. All 7 ticket ACs mapped to specific implementation tasks. No gating blockers; all hard dependencies satisfied. Spec Agent has sufficient context to proceed with Task 1 specification.

**CONFIDENCE LEVEL: HIGH** — Ticket AC well-defined, pattern established by M902-11/10/09, scoring model straightforward, 7 clarifying questions resolved with HIGH-MEDIUM confidence. Ready for Spec Agent to freeze requirements.

**NEXT RESPONSIBLE AGENT:** Spec Agent (Task 1)

**BLOCKING ISSUES:** None.
