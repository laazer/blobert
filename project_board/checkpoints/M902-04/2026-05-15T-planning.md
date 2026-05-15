# Checkpoint Log: M902-04 Planning Run

**Date:** 2026-05-15  
**Stage:** PLANNING → SPECIFICATION  
**Ticket:** project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/04_handoff_metadata_and_risk_escalation.md  
**Ticket ID:** M902-04

---

## Executive Summary

Decomposed M902-04 (Handoff metadata schema and risk-based escalation) into a 15-task execution plan. All critical ambiguities resolved via checkpoint protocol. Execution ready for Spec Agent.

---

## Requirement Analysis

From ticket acceptance criteria:
1. Versioned JSON schema for gate outputs with 10 fields (status, risk_score, architecture_score, test_confidence, duplication_delta, complexity_delta, violations, warnings, escalation_reasons, audit_events)
2. Aggregation rules for multi-tool gate runs (ordering, deduplication, max severity)
3. ESCALATE triggers with concrete detectors (governance files, architecture drift, suppression abuse, security paths, repeated failures)
4. Append-only audit log (gitignored ci/artifacts/ or project_board/audit-logs/)
5. At least one gate (static analysis M902-02) produces compliant metadata end-to-end
6. ESCALATE blocks autonomous progression OR is explicitly wired to "human required"
7. WARN vs FAIL thresholds documented and configurable without code edits

---

## Key Ambiguities Resolved (Checkpoint Decisions)

### Ambiguity 1: What is "architecture drift" measurable from current gate outputs?

**Would have asked:** How do we quantify architecture drift from the existing static analysis gate? Is it violations count, rate of new violations, comparison to baseline, or depth of drift?

**Assumption made:** Architecture drift = relative increase in violations count from baseline, measurable via:
- Baseline snapshot (violations count per rule category) taken at M902 completion
- Current snapshot (latest static analysis run)
- Drift = (current_count - baseline_count) / baseline_count as percentage
- ESCALATE threshold: >20% increase in violations or any new violations in architecture-critical rules (AR-* from M902-03)

**Confidence:** MEDIUM
- Rationale: Assumes M902-03 governance rules are stable (COMPLETE, no changes expected). Percentage-based drift is conservative and implementable without coverage integration.
- Risk: May not catch semantic drift (violations change category but count stays same); acceptable for MVP, addressable in M903.

---

### Ambiguity 2: Should numeric scores (0-100) be used or categorical (LOW/MEDIUM/HIGH/CRITICAL)?

**Would have asked:** Are risk_score, architecture_score, test_confidence numeric or categorical? Numeric is more precise but harder to calibrate; categorical is opaque but easier to reason about.

**Assumption made:** Use NUMERIC scores (0-100 range) with documented calibration:
- risk_score: aggregate of severity distributions in violations (CRITICAL→100, ERROR→80, WARN→50, INFO→10); score = weighted average
- architecture_score: inverse of AR-* violation count and severity (perfect=100, decreases per AR violation)
- test_confidence: proxy from gate metadata (no coverage available), calculated as: (tests_run - tests_failed) / tests_run * 100, OR fallback to CATEGORICAL (PASS/FAIL) if test metadata unavailable
- Thresholds (configurable, documented): WARN >50, FAIL >75, ESCALATE >90

**Confidence:** MEDIUM-HIGH
- Rationale: Numeric allows precise escalation triggering and aggregation. Calibration frozen in Task 2 (schema design). Configurable thresholds avoid hardcoding.
- Risk: Numeric scoring is new to this codebase; may require tuning in M903. Fallback to categorical documented.

---

### Ambiguity 3: What signals exist for "test_confidence" without coverage integration?

**Would have asked:** How do we measure test confidence without code coverage? What metadata is available from gates that run tests?

**Assumption made:** test_confidence populated from available signals:
- If gate runs tests: (passed_tests / total_tests) * 100
- If gate does static analysis: inherited from prior gate that ran tests (spec_completeness_check can track test pass count)
- If no test signal available: default to "UNKNOWN" (categorical) or -1 (numeric), marked as "untested path" in audit log
- Documentation: test_confidence is advisory; escalation does NOT depend on it in MVP (M903 will wire test_confidence gates)

**Confidence:** MEDIUM
- Rationale: Signals are sparse; relying on gate metadata (not raw test output). Safe because test_confidence not a mandatory escalation trigger.
- Risk: If metadata sparse, test_confidence will be unavailable for many gates; acceptable, documented as limitation.

---

### Ambiguity 4: Where should audit logs live if they are noisy?

**Would have asked:** Should audit logs be under project_board/ (traceable, gittracked) or ci/artifacts/ (noisy, gitignored)? How many events per run?

**Assumption made:** Audit logs under `ci/artifacts/audit-logs/` (gitignored, noisy):
- Path: ci/artifacts/audit-logs/<ticket-id>/<gate-name>/<YYYY-MM-DD>/<timestamp>-<mode>.jsonl
- Format: JSON Lines (one audit event per line, append-only, rotated daily)
- Gitignored: yes (added to .gitignore if not present)
- Retention: 30 days (ci/scripts/audit_log_rotate.py, optional M903 task)
- Events logged per gate run: gate_started, tool_invoked, tool_finished, violation_added, escalation_triggered, audit_error
- Expected volume: ~10-50 events per run per gate; ~10MB/month across all gates; acceptable in CI artifacts

**Confidence:** HIGH
- Rationale: Matches blobert's CI conventions (artifacts, gitignored). ci/artifacts/ already used by other tools. Noisy but traceable.
- Risk: None identified; M903 can add rotation/cleanup if needed.

---

### Ambiguity 5: How is "repeated failures" tracked across runs?

**Would have asked:** Is "repeated failures" measured per-rule, per-file, per-category, or per-gate? Across how many runs?

**Assumption made:** Repeated failures tracked per RULE per FILE across last 5 runs:
- Data source: audit log events (violation_added entries)
- Algorithm: For each (rule, file) pair in current run, count occurrences in prior 4 runs
- ESCALATE trigger: If (rule, file) fails in 5+ consecutive runs, mark as "repeated failure" and ESCALATE
- Scope: Per gate (each gate tracks its own rules independently)
- Fallback: If <5 prior runs exist (fresh repo), use available history

**Confidence:** MEDIUM
- Rationale: Conservative (5 consecutive runs), per-rule-per-file is precise and actionable. Implementable via audit log query.
- Risk: Requires audit log persistence and query logic; acceptable complexity for MVP.

---

### Ambiguity 6: What concrete detectors for ESCALATE triggers are measurable from current gates?

**Would have asked:** From the 5 listed triggers (governance file modifications, architecture drift, suppression abuse, security-sensitive paths, repeated failures), which can be implemented with M902-01 and M902-02 gate outputs?

**Assumption made:** Implement 3 of 5 detectors in MVP (M902-04):
1. **Governance file modifications** (IMPLEMENTED via M902-03 gate): AR-* violations in CLAUDE.md, project_board/CHECKPOINTS.md, Taskfile.yml, lefthook.yml are ESCALATE-grade
2. **Architecture drift** (IMPLEMENTED via M902-02 gate): >20% increase in violations count from baseline, any new AR-* violations
3. **Suppression abuse** (IMPLEMENTED via M902-03 gate): marked as "GV-06" (suppression integrity); recurring suppressions without issue links ESCALATE
4. **Security-sensitive paths** (DEFERRED to M903): Requires security rules (semgrep, bandit); current rules don't distinguish; placeholder detector logs "TODO"
5. **Repeated failures** (IMPLEMENTED via M902-04 audit log): 5+ consecutive runs same (rule, file) pair

Detector implementation: Each detector is a Python function in ci/scripts/gates/escalation_detector.py, callable by gate runner post-aggregation.

**Confidence:** MEDIUM
- Rationale: 3/5 are implementable with existing gates. Security-sensitive paths deferred responsibly. Architecture drift tied to M902-03 governance rules (stable).
- Risk: Detectors are heuristic (especially drift %; may trigger false positives); acceptable for MVP, tunable in M903.

---

### Ambiguity 7: Is ESCALATE blocking or advisory?

**Would have asked:** Does ESCALATE block autonomous progression (autopilot loops, lefthook, CI), or is it advisory with human review required?

**Assumption made:** ESCALATE is BLOCKING in blocking mode gates (enforced at M903+), and ADVISORY in shadow mode (current):
- In shadow mode (default M902-04): gate returns status=ESCALATE, does NOT exit 1, does NOT block. Logged in audit.
- In blocking mode (M903+): gate returns status=ESCALATE, exits 1, blocks CI/autopilot. Requires human review.
- Wiring: gate_runner.py mode flag controls behavior; spec documents both paths.
- For M902-04: Static analysis gate runs shadow (deferred enforcement per M902-02), so ESCALATE is advisory.

**Confidence:** HIGH
- Rationale: Matches M902-01/02 shadow mode strategy. Mode toggle explicit and testable. Enforces human review without premature automation.

---

### Ambiguity 8: How should escalation_reasons be structured in the JSON schema?

**Would have asked:** Should escalation_reasons be a list of strings, or structured objects with detector name + confidence?

**Assumption made:** escalation_reasons is a list of STRUCTURED OBJECTS:
```json
"escalation_reasons": [
  {
    "detector": "governance_file_modification",
    "severity": "CRITICAL",
    "details": "CLAUDE.md modified; 2 AR violations introduced",
    "confidence": "HIGH",
    "recommendation": "Manual review required; check architecture compliance"
  }
]
```
- Allows downstream automation to reason about escalation drivers
- Confidence field permits gradual escalation tuning in M903
- Matches gate schema pattern (violations have severity; escalation reasons mirror it)

**Confidence:** HIGH
- Rationale: Structured format is parseable and actionable; unstructured strings are not. Supports future automation.

---

## Task Decomposition

Execution plan: 15 sequential tasks, each task ~1 agent run.

| # | Task | Agent | Key Outputs | Dependencies |
|---|------|-------|------------|--------------|
| 1 | Define handoff metadata schema (versioned, 10 fields, examples) | Spec | schema.json, examples.json, spec doc | M902-01/02 complete |
| 2 | Document score calibration and threshold configuration | Spec | config.md with risk_score/architecture_score/test_confidence formulas | Task 1 |
| 3 | Implement escalation detector framework | Implementation | escalation_detector.py with 5 detector stubs | Task 1, Task 2 |
| 4 | Implement governance file detector | Implementation | detector: GV file mods → ESCALATE | Task 3, M902-03 complete |
| 5 | Implement architecture drift detector | Implementation | detector: AR violations >20% increase | Task 3, M902-02 gate outputs |
| 6 | Implement suppression abuse detector | Implementation | detector: GV-06 recurring suppression → ESCALATE | Task 3, M902-03 complete |
| 7 | Implement repeated failures detector | Implementation | detector: audit log query, 5+ consecutive runs | Task 3, audit log infra |
| 8 | Implement security-sensitive paths detector (placeholder) | Implementation | detector stub: logs "TODO", logs path to M903 ticket | Task 3 |
| 9 | Design audit log schema and persistence | Spec | audit-logs spec, ci/artifacts/ setup, rotation policy | Task 1, Task 2 |
| 10 | Implement audit event logging | Implementation | audit_log.py with event emit functions | Task 9 |
| 11 | Wire escalation detector into gate runner post-processing | Implementation | gate_runner.py updated to call detectors, populate escalation_reasons | Task 3–8, M902-01 |
| 12 | Implement aggregation rules (multi-tool, ordering, dedupe, max severity) | Implementation | aggregator.py or gate_runner.py extension | Task 1, Task 11 |
| 13 | Integrate metadata schema validation into static analysis gate (M902-02) | Implementation | static_analysis_check.py updated to emit compliant metadata | Task 1, M902-02 gate |
| 14 | Create test suite (behavioral + adversarial) | Test Designer/Breaker | tests/ci/test_handoff_metadata.py, 80+ tests | Task 1–13 |
| 15 | Update Milestone 902 README with schema, thresholds, audit log policy | Spec/Documentation | README.md section on metadata, escalation, audit logs | Task 1–14 |

---

## Dependency Chain

```
M902-01 (gate framework) — COMPLETE ✓
         ↓
M902-02 (static analysis) — COMPLETE ✓
         ↓
M902-03 (governance rules) — COMPLETE ✓
         ↓
M902-04 (metadata + escalation) — PLANNING
```

All dependencies satisfied. No blockers identified.

---

## Assumptions Checkpoint Summary

| # | Assumption | Confidence | Notes |
|---|-----------|-----------|-------|
| 1 | Architecture drift = >20% violations increase from baseline | MEDIUM | Heuristic, tunable in M903 |
| 2 | Use numeric scores (0-100) with calibrated thresholds | MEDIUM-HIGH | Frozen in Task 2, configurable |
| 3 | test_confidence from gate metadata (pass/fail signals) | MEDIUM | Fallback to "UNKNOWN" if unavailable |
| 4 | Audit logs in ci/artifacts/ (gitignored, noisy) | HIGH | Matches blobert conventions |
| 5 | Repeated failures = per-rule-per-file across 5 runs | MEDIUM | Conservative, implementable |
| 6 | Implement 3/5 detectors in MVP, defer security paths | MEDIUM | Reasonable scope for M902-04 |
| 7 | ESCALATE is advisory in shadow mode, blocking in M903+ | HIGH | Matches M902-01/02 strategy |
| 8 | escalation_reasons = structured objects (detector, severity, confidence) | HIGH | Parseable and actionable |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Score calibration tuning delays | MEDIUM | HIGH | Thresholds configurable; M903 can retune |
| Audit log query performance (many events) | LOW | MEDIUM | Rotate daily; query recent logs only |
| False positive escalations (drift heuristic) | MEDIUM | MEDIUM | Document confidence per detector; M903 refines |
| Security detector deferred (placeholder) | HIGH | LOW | Acceptable for MVP; explicit M903 task |
| test_confidence unavailable (sparse metadata) | MEDIUM | LOW | Fallback to "UNKNOWN"; not in MVP escalation triggers |

---

## Ready for Next Stage

**Stage Transition:** PLANNING → SPECIFICATION

All ambiguities resolved and checkpointed. Task decomposition complete. Dependencies verified. Assumptions documented with confidence levels. No blockers identified.

**Next Responsible Agent:** Spec Agent

**Handoff Input Schema:**
```json
{
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/04_handoff_metadata_and_risk_escalation.md",
  "checkpoint_log": "project_board/checkpoints/M902-04/2026-05-15T-planning.md",
  "task_decomposition": "15 tasks, sequential, dependencies verified"
}
```

---

## Notes for Spec Agent

1. **Task 1 (schema design):** Extend M902-01 gate schema (version 0.1.0) to version 0.2.0 with 10 required fields. Keep backward compatible via version field.

2. **Task 2 (score calibration):** Freeze numeric formulas (risk_score, architecture_score, test_confidence) with worked examples. Document threshold mappings (WARN/FAIL/ESCALATE).

3. **Tasks 3–8 (detectors):** Each detector is ~50 lines Python, callable via `detect_X(gate_result, baseline, audit_log) -> list[escalation_reason]`. Stub out all 5; implement 3 in M902-04, placeholder 2 for M903.

4. **Task 9 (audit log):** Design append-only JSON Lines format. Path structure: ci/artifacts/audit-logs/<ticket-id>/<gate-name>/<date>/<timestamp>-<mode>.jsonl. Implement basic emit functions.

5. **Task 13 (integration):** Update static_analysis_check.py (M902-02 gate) to produce compliant 0.2.0 metadata. Validate schema in gate_runner.py or separate validator.

6. **Test Strategy:** Behavioral tests validate schema, score formulas, detector outputs. Adversarial tests corrupt scores, detectors, audit logs; expect graceful fallback.

---

**Checkpoint Logged:** 2026-05-15  
**Index Entry:** Added to project_board/CHECKPOINTS.md
