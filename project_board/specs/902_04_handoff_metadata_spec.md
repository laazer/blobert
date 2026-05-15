# Spec: Handoff Metadata Schema and Risk-Based Escalation

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/04_handoff_metadata_and_risk_escalation.md`

**Milestone:** 902 — Agent Predictability Improvements

**Agent:** Spec Agent

**Date:** 2026-05-15

**Status:** SPECIFICATION

**Revision:** 1

---

## Executive Summary

This specification defines the **handoff metadata schema (version 0.2.0)** and **risk-based escalation framework** for blobert's multi-agent validation gates. The framework enables:

1. **Structured gate outputs** with 10 required metadata fields: status, risk_score, architecture_score, test_confidence, duplication_delta, complexity_delta, violations, warnings, escalation_reasons, audit_events.
2. **Numeric risk scoring** (0-100 range) with configurable thresholds for WARN/FAIL/ESCALATE decision-making.
3. **Five escalation detectors** that identify governance violations, architecture drift, suppression abuse, and repeated failures.
4. **Append-only audit log** in JSON Lines format for forensic tracing and violation history.

The specification freezes all requirements for spec tasks (Tasks 1–9 of the 15-task execution plan). Implementation (Tasks 10–13) and testing (Tasks 14) depend on this frozen specification.

---

## Requirement 01: Versioned Handoff Metadata Schema (Version 0.2.0)

### 1. Spec Summary

**Description:** A JSON Schema (draft 2020-12 format) that defines the complete structure of gate output metadata. This schema extends the M902-01 success/failure records by adding risk scoring, architecture quality proxies, and escalation semantics. The schema is backward compatible via an explicit `version` field, permitting future upgrades to v0.3.0 or later without breaking consumers of v0.2.0.

**Constraints:**
- Must be valid JSON Schema format (draft 2020-12).
- Must define exactly 10 required top-level fields (no more, no fewer).
- Must include comprehensive examples (5+ valid output scenarios).
- Must support version mismatch handling by consumers (no breaking changes when version upgrades).
- Must not store secrets (API keys, tokens, passwords).

**Assumptions:**
- Numeric scores (0-100 range) are simpler than categorical only; tunable thresholds allow future ML/heuristics.
- escalation_reasons is a list of structured objects (detector, severity, details, confidence, recommendation).
- audit_events field contains references to audit log entry paths (strings), not full event bodies, to keep metadata payload bounded.
- Backward compatibility: v0.1.0 gates (M902-01) remain functional when v0.2.0 gates produce output.

**Scope:** All gates in the M902 pipeline (current + subsequent tickets).

### 2. Acceptance Criteria

- **AC-01.1:** Schema file exists at `project_board/specs/902_04_metadata_schema.json` and contains valid JSON.
- **AC-01.2:** Schema declares `"version": "0.2.0"` at the top level.
- **AC-01.3:** Schema defines exactly 10 required top-level properties: `status`, `risk_score`, `architecture_score`, `test_confidence`, `duplication_delta`, `complexity_delta`, `violations`, `warnings`, `escalation_reasons`, `audit_events`.
- **AC-01.4:** `status` field is an enum with exactly 4 values: `"PASS"`, `"WARN"`, `"FAIL"`, `"ESCALATE"`.
- **AC-01.5:** `risk_score`, `architecture_score`, `test_confidence` are numeric (0-100 integer OR null) OR the string `"UNKNOWN"`.
- **AC-01.6:** `duplication_delta`, `complexity_delta` are numeric (percentage, -100 to +500) OR null.
- **AC-01.7:** `violations` is an array of objects; each object has required fields: `rule_id` (string), `file` (string), `line` (integer or null), `severity` (enum: `"CRITICAL"`, `"ERROR"`, `"WARN"`, `"INFO"`), `message` (string), `remediation_hint` (string or null), `suppressible` (boolean).
- **AC-01.8:** `warnings` is an array with same structure as violations (same object schema).
- **AC-01.9:** `escalation_reasons` is an array of objects; each object has required fields: `detector` (string, e.g., `"governance_file_modifications"`), `severity` (enum: `"CRITICAL"`, `"HIGH"`, `"MEDIUM"`, `"LOW"`), `details` (string), `confidence` (enum: `"HIGH"`, `"MEDIUM"`, `"LOW"`), `recommendation` (string).
- **AC-01.10:** `audit_events` is an array of strings; each string is a reference path (e.g., `"ci/artifacts/audit-logs/static_analysis_check/2026-05-15/run-id-event.jsonl:line-5"`).
- **AC-01.11:** Example directory exists at `project_board/specs/902_04_metadata_examples/` with at least 5 example JSON files representing: (1) PASS status with no violations, (2) WARN status with low-risk violations, (3) FAIL status with high-risk violations, (4) ESCALATE status triggered, (5) multi-tool aggregated output.
- **AC-01.12:** Each example is valid against the schema (validated via jsonschema library).
- **AC-01.13:** Schema includes a `"_comment"` field documenting backward compatibility strategy: "This schema version (0.2.0) extends M902-01 v0.1.0 with risk scoring and escalation. Consumers must handle version mismatches gracefully by ignoring unknown fields."
- **AC-01.14:** A test exists that loads the schema, loads all examples, and validates each example against the schema using jsonschema library.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema drift between versions | Downstream consumers break | Require `version` field; enforce backward compatibility via tests; M903 defines upgrade policy |
| Numeric scores require calibration | Thresholds may be miscalibrated initially | Thresholds in Task 2 config are marked tunable; M903 refines based on real data |
| escalation_reasons duplication with violations | Confusion about what each field means | Violations are rule violations; escalation_reasons are detector-specific escalation triggers (different concern) |
| audit_events field bloats metadata | Payload size grows unbounded | References only (path strings), not full event bodies; keeps size bounded; 30-day log rotation (Task 9) limits history |
| Unknown future fields in v0.3.0 | v0.2.0 consumers don't recognize them | Schema allows additionalProperties: true; consumers must ignore unknown fields gracefully |

### 4. Clarifying Questions

- **Q1:** Should violations and warnings use the same severity enum? *Assumption: Yes, both use `["CRITICAL", "ERROR", "WARN", "INFO"]`. escalation_reasons uses a different enum: `["CRITICAL", "HIGH", "MEDIUM", "LOW"]` to distinguish detector severity from rule severity.*
- **Q2:** What is the format of audit_events references? *Assumption: `"ci/artifacts/audit-logs/<gate-name>/<date>/<timestamp>-<mode>.jsonl:line-N"` (file path + colon + 1-indexed line number). Consumers query via grep/jq.*
- **Q3:** Should the schema include tool metadata (which tool produced which violation)? *Assumption: No. Tool name can be inferred from rule_id prefix (ruff rules start with E/W, mypy with error codes, sempreg with rule-id, etc.). Detailed tool tracking deferred to M903.*

---

## Requirement 02: Score Calibration and Threshold Configuration

### 1. Spec Summary

**Description:** A YAML configuration file (`project_board/902_04_escalation_config.yml`) that documents score calculation formulas and defines WARN/FAIL/ESCALATE threshold mappings. All thresholds are configurable without code edits. Formulas are worked out with concrete examples.

**Constraints:**
- Must be valid YAML syntax.
- All thresholds must be configurable key-value pairs (no hardcoded constants in code).
- Formulas must be deterministic and implementable from gate output violations.
- All formulas must include worked examples with actual numeric data.

**Assumptions:**
- Numeric score formulas are simple weighted averages; complexity scoring in M903 can refine if needed.
- Baseline for architecture_score comes from M902-03 completion (zero AR violations baseline).
- duplication_delta and complexity_delta may be unavailable in MVP (marked "TODO"), with M903 deferral.
- test_confidence from gate metadata or "UNKNOWN" fallback.

**Scope:** All gates in M902+ pipeline; tunable in M903 per gate category.

### 2. Acceptance Criteria

- **AC-02.1:** Configuration file exists at `project_board/902_04_escalation_config.yml` and is valid YAML.
- **AC-02.2:** File contains a `scoring` section with:
  - `risk_score_formula`: Maps severity level to numeric weight (CRITICAL=100, ERROR=80, WARN=50, INFO=10) and calculation method (weighted average of violation severities).
  - `architecture_score_formula`: Subtracts AR violation count penalties (count * 10) and severity penalties from 100, clamped [0, 100].
  - `test_confidence_formula`: (tests_passed / tests_total) * 100 if test data available; "UNKNOWN" otherwise.
  - `duplication_delta_formula`: (current_tokens - baseline_tokens) / baseline_tokens * 100 (marked "TODO" if jscpd baseline unavailable).
  - `complexity_delta_formula`: Percentage delta (marked "TODO" if static analysis tool doesn't emit baseline).
- **AC-02.3:** File contains a `thresholds` section with mappings:
  - `risk_score`: WARN at >50, FAIL at >75, ESCALATE at >90 (each a configurable key-value pair).
  - `architecture_score`: WARN at <60, FAIL at <45, ESCALATE at <30 (inverted: lower scores are worse).
  - `test_confidence`: PASS at >70, WARN at 40-70, FAIL at <40 (advisory only, not a blocker in MVP).
  - `duplication_delta`: WARN at >10%, FAIL at >25% (delta from baseline; marked "TODO" if unavailable).
  - `complexity_delta`: WARN at >5%, FAIL at >15% (marked "TODO" if unavailable).
- **AC-02.4:** File includes 5+ worked examples showing:
  - Example 1 (Good case): 0 violations → risk_score=0, status=PASS.
  - Example 2 (Borderline): 2 ERROR + 1 WARN violations → risk_score=63.3, status=WARN.
  - Example 3 (Bad case): 2 CRITICAL violations → risk_score=100, status=FAIL.
  - Example 4 (Architecture drift): 3 AR violations → architecture_score=70, status=FAIL.
  - Example 5 (Multi-violation): Combined risk_score and architecture_score mapping to ESCALATE.
- **AC-02.5:** All thresholds have a comment indicating "Tunable in M903" and the current values are defaults.
- **AC-02.6:** A section documents baseline strategy: baseline file at `project_board/902_04_baseline_violations.json`, immutable snapshot, used for drift detection (Task 5).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Numeric thresholds miscalibrated initially | Too many false positives or false negatives | Thresholds in config file (no code edits); M903 refines after collecting real data from gates |
| Baseline snapshot drift | Gradual violations increase undetected | Baseline immutable; M903 implements time-window alerts or rolling baseline |
| Duplication/complexity deltas unavailable | Incomplete scoring | Marked "TODO" in config; acceptable for MVP; M903 implements when tools finalized |
| test_confidence unavailable for static analysis gate | Advisory-only, not escalation trigger | Acceptable; test_confidence = "UNKNOWN" for gates with no test data |

### 4. Clarifying Questions

- **Q1:** Should test_confidence ever trigger ESCALATE? *Assumption: No. test_confidence is advisory only in MVP; may be used in M903 for gates with available test data.*
- **Q2:** Are thresholds per-gate or global? *Assumption: Global defaults in config file; M903 adds per-gate overrides if needed.*

---

## Requirement 03: Escalation Detector Framework (Interface & Stubs)

### 1. Spec Summary

**Description:** A framework design document that freezes the detector interface, specifies input/output signatures, and documents 5 detector stubs (all signatures frozen, but MVP scope includes implementation of 3 with stubs for 2).

**Constraints:**
- Detector interface must be pure functions (no side effects except audit logging).
- All detectors must accept same input signature: `(gate_result: dict, baseline: dict | None, audit_log: list[dict]) -> list[EscalationReason]`.
- EscalationReason type: `{detector: str, severity: "CRITICAL"|"HIGH"|"MEDIUM"|"LOW", details: str, confidence: "HIGH"|"MEDIUM"|"LOW", recommendation: str}`.
- MVP scope: implement detectors 1–3 in Tasks 4–6; placeholder stubs for 4–5 with explicit M903 deferral.
- Detectors run sequentially post-aggregation.

**Assumptions:**
- Detectors are called from gate_runner post-aggregation (Task 11).
- Baseline is optional (may be None on first run).
- Detectors return empty list if no escalation triggered.

**Scope:** All gates in M902+ pipeline.

### 2. Acceptance Criteria

- **AC-03.1:** Specification document exists at `project_board/specs/902_04_escalation_detectors_spec.md`.
- **AC-03.2:** Document defines detector interface: `detect_X(gate_result: dict, baseline: dict | None, audit_log: list[dict]) -> list[EscalationReason]` where each `EscalationReason` is a dict with fields: `detector` (string), `severity` (enum), `details` (string), `confidence` (enum), `recommendation` (string).
- **AC-03.3:** All 5 detector signatures are documented: `detect_governance_file_modifications`, `detect_architecture_drift`, `detect_suppression_abuse`, `detect_security_sensitive_paths`, `detect_repeated_failures`.
- **AC-03.4:** Each detector has documented data source(s): violations list, audit log, baseline file, rule ids, etc.
- **AC-03.5:** Each detector specifies confidence level (HIGH/MEDIUM/LOW) and whether it requires audit log or baseline.
- **AC-03.6:** MVP scope is explicit: detectors 1–3 are fully specified for implementation; detectors 4–5 are marked "placeholder stub — M903" with no false escalations.
- **AC-03.7:** Document includes call order: sequential post-aggregation.
- **AC-03.8:** Detector stubs are documented with signatures: each stub returns empty list or placeholder `[EscalationReason(detector="...", severity="UNKNOWN", details="TODO M903", confidence="UNKNOWN", recommendation="M903 ticket TBD")]`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Detector scope too broad (many rules per detector) | Hard to maintain, low confidence | Each detector focuses on one escalation signal (governance, drift, suppression, etc.) |
| Placeholder stubs trigger false escalations | User confusion | Stubs explicitly log "TODO M903"; no escalation_reasons returned (empty list) |
| Baseline missing on first run | Drift detector fails | Graceful fallback: baseline = None; detector skips or returns empty list |

### 4. Clarifying Questions

- **Q1:** Should detectors be run in parallel or sequentially? *Assumption: Sequential (Task 11 serializes calls). M903 can add parallelization if performance requires.*

---

## Requirement 04: Governance File Modification Detector Specification

### 1. Spec Summary

**Description:** A specification for the governance file modification detector (`detect_governance_file_modifications`). This detector identifies when monitored governance files are modified and contain AR-* (architecture rule) violations, triggering ESCALATE with CRITICAL severity.

**Constraints:**
- Monitored files are a fixed set: {`CLAUDE.md`, `Taskfile.yml`, `lefthook.yml`, `project_board/CHECKPOINTS.md`, `.gitignore`}.
- Detection logic is boolean: IF (any violation with file in monitored_files AND rule_id in [AR-01, AR-02, AR-03, AR-04, AR-05, AR-06]) THEN escalate.
- Confidence is HIGH (violations are deterministic).
- Severity is CRITICAL (governance files are sensitivity-critical).

**Assumptions:**
- Only rule violations trigger escalation, not file modification alone.
- AR-01..06 are the only architecture-critical rules; other governance rules do not trigger this detector.

**Scope:** All gates; applies whenever violations include modified governance files.

### 2. Acceptance Criteria

- **AC-04.1:** Specification document exists at `project_board/specs/902_04_governance_detector_spec.md`.
- **AC-04.2:** Document lists monitored files: CLAUDE.md, Taskfile.yml, lefthook.yml, project_board/CHECKPOINTS.md, .gitignore.
- **AC-04.3:** Document specifies detection logic: for each violation in gate_result["violations"], if violation["file"] is in monitored_files AND violation["rule_id"] in ["AR-01", "AR-02", "AR-03", "AR-04", "AR-05", "AR-06"], then escalate.
- **AC-04.4:** EscalationReason structure is: `{detector: "governance_file_modifications", severity: "CRITICAL", details: f"Governance file {file} modified with architecture rule {rule_id}: {message}", confidence: "HIGH", recommendation: "Design review required before merge"}`.
- **AC-04.5:** Document includes 3 worked scenarios: (1) CLAUDE.md modified with AR-01 violation → escalate, (2) Taskfile.yml modified with no AR violations → no escalation, (3) Taskfile.yml modified with non-AR governance violations → no escalation.
- **AC-04.6:** Document marks monitored files list as "extensible via config in M903".

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Legitimate governance file changes trigger false escalations | User frustration | Confidence HIGH; review required; M903 can add context checks to reduce false positives |
| File path format differences | Detector misses some files | Normalize to relative paths; tests verify against real paths |

### 4. Clarifying Questions

- **Q1:** Should the detector trigger on .gitignore modifications? *Assumption: Yes, .gitignore is governance-critical; changes must not violate architecture rules.*

---

## Requirement 05: Architecture Drift Detector Specification

### 1. Spec Summary

**Description:** A specification for the architecture drift detector (`detect_architecture_drift`). This detector measures violation count increase from baseline, triggering ESCALATE if >20% increase or if new AR-* violations appear.

**Constraints:**
- Baseline source: `project_board/902_04_baseline_violations.json` (immutable snapshot from M902-03 completion).
- Drift threshold: 20% increase in violation count (tunable in M903).
- New AR violation detection: any AR-* rule appearing in current but not baseline triggers escalation.
- Confidence: MEDIUM (heuristic-based; threshold tunable).
- Severity: HIGH.

**Assumptions:**
- Baseline is immutable snapshot (no rolling baseline).
- 20% threshold is conservative; tunable in M903.
- Baseline file committed to repo (not gitignored).
- M902-02 gate outputs violations in structured format (rule_id, severity).

**Scope:** All gates; applies whenever violations are compared to baseline.

### 2. Acceptance Criteria

- **AC-05.1:** Specification document exists at `project_board/specs/902_04_drift_detector_spec.md`.
- **AC-05.2:** Document specifies baseline file format: JSON object with `{rule_id: count, rule_id: count, ...}` (e.g., `{"AR-01": 0, "E501": 5, ...}`).
- **AC-05.3:** Document specifies baseline location: `project_board/902_04_baseline_violations.json`.
- **AC-05.4:** Drift algorithm documented: `drift_pct = (current_count - baseline_count) / baseline_count * 100` if baseline_count > 0; else drift_pct = 0% (cannot drift if no baseline).
- **AC-05.5:** ESCALATE triggers: (1) drift_pct > 20% OR (2) any rule_id in [AR-01..06] appears in current but not baseline.
- **AC-05.6:** EscalationReason structure: `{detector: "architecture_drift", severity: "HIGH", details: f"Violation count increased {drift_pct}% from baseline ({baseline_count} → {current_count}) OR new AR violations detected: {new_ar_rules}", confidence: "MEDIUM", recommendation: "Review architecture changes; consider refactoring to reduce drift"}`.
- **AC-05.7:** Document includes 3 worked scenarios: (1) baseline 5 violations, current 6 violations (20% drift) → no escalation (at threshold), (2) baseline 5, current 7 (40% drift) → escalate, (3) baseline includes no AR violations, current includes AR-01 → escalate.
- **AC-05.8:** Document notes: "20% threshold is conservative and tunable in M903. Baseline file will be committed to repo for traceability."

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| 20% threshold too lenient | Gradual drift goes undetected | Conservative threshold; M903 refines based on real data; can lower threshold |
| 20% threshold too strict | Legitimate feature additions trigger false escalations | Suppressible via recommendation; M903 can add per-rule thresholds |
| Baseline missing (first run) | Detector cannot compare | Graceful fallback: if baseline file missing, detector returns empty list (no escalation) |
| New projects with different violation counts | Baseline outdated | Baseline is M902-03 snapshot; M903 implements rolling or time-window baselines |

### 4. Clarifying Questions

- **Q1:** Should the detector compare per-rule violation counts or just total count? *Assumption: Total count for MVP; M903 adds per-rule thresholds if needed.*
- **Q2:** What if baseline file is missing? *Assumption: Graceful fallback; detector returns empty list.*

---

## Requirement 06: Suppression Abuse Detector Specification

### 1. Spec Summary

**Description:** A specification for the suppression abuse detector (`detect_suppression_abuse`). This detector identifies GV-06 violations (suppression integrity) and flags recurring suppressions without valid issue links across multiple runs.

**Constraints:**
- GV-06 violations mark suppression integrity issues (from M902-03 governance_check.py output).
- Suppression abuse patterns: (a) `# noqa: <rule>` without preceding issue link, (b) `# pragma: no cover` without justification, (c) `# type: ignore` on non-type-error lines.
- Recurring abuse: query audit log for same (file, rule_id=GV-06) pair across 5+ runs.
- Confidence: HIGH for current violations, MEDIUM for recurring.
- Severity: HIGH (suppression abuse erodes governance).

**Assumptions:**
- M902-03 already emits GV-06 violations for suppression integrity (COMPLETE ticket confirms this).
- Audit log stores violation occurrence records queryable by (file, rule_id).
- Legitimate suppressions have issue links on prior line; format is `# issue: <id>`.

**Scope:** All gates that produce GV-06 violations.

### 2. Acceptance Criteria

- **AC-06.1:** Specification document exists at `project_board/specs/902_04_suppression_detector_spec.md`.
- **AC-06.2:** Document specifies GV-06 violation source: M902-03 governance_check.py output.
- **AC-06.3:** Document lists suppression abuse patterns: (1) `# noqa: <rule>` without `# issue: <id>` on prior line, (2) `# pragma: no cover` without justification, (3) `# type: ignore` on non-type-error lines.
- **AC-06.4:** Document specifies recurring abuse detection: query audit log for (file, rule_id=GV-06) pairs; if found in 5+ consecutive recent runs, flag as recurring abuse.
- **AC-06.5:** EscalationReason structure for current violations: `{detector: "suppression_abuse", severity: "HIGH", details: f"File {file} has GV-06 violation: {message}", confidence: "HIGH", recommendation: "Add issue link or remove suppression"}`.
- **AC-06.6:** EscalationReason structure for recurring: `{detector: "suppression_abuse", severity: "HIGH", details: f"File {file} has recurring GV-06 violation across 5+ runs", confidence: "MEDIUM", recommendation: "Investigate root cause; either fix underlying issue or create ticket for suppression justification"}`.
- **AC-06.7:** Document includes 3 scenarios: (1) GV-06 violation with issue link → no escalation, (2) GV-06 without link → escalate (HIGH confidence), (3) GV-06 recurring over 5 runs → escalate (MEDIUM confidence).
- **AC-06.8:** Document notes: "M903 will implement automated suppression link validator and stricter regex patterns."

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| GV-06 violations may not be available initially | Detector cannot run | Graceful fallback if GV-06 not in violations; detector returns empty list |
| Audit log query slow on large logs | Performance impact | Query recent logs only (last 5 runs); rotation (30-day retention) limits history |
| False positives on legitimate suppressions | User confusion | Confidence MEDIUM for recurring; recommendations provide context |

### 4. Clarifying Questions

- **Q1:** How many consecutive runs define "recurring"? *Assumption: 5 consecutive runs (tunable in M903).*

---

## Requirement 07: Repeated Failures Detector Specification

### 1. Spec Summary

**Description:** A specification for the repeated failures detector (`detect_repeated_failures`). This detector queries audit logs for violations that persist across multiple consecutive runs, flagging chronic issues requiring human review.

**Constraints:**
- Audit log query: filter events for "violation_added" with (rule_id, file) keys.
- Recurrence algorithm: count how many consecutive recent runs contain the same (rule_id, file) pair.
- ESCALATE trigger: if same (rule_id, file) appears in 5+ consecutive runs.
- Confidence: HIGH (deterministic audit log data).
- Severity: MEDIUM (chronic issues, not critical blocker).

**Assumptions:**
- Audit logs stored and accessible at `ci/artifacts/audit-logs/`.
- Audit events have (rule_id, file) metadata.
- "Consecutive" means last 5 runs regardless of time gap; acceptable for MVP.
- Deleted violations (no longer present) do not reset recurrence counter.
- Fallback if <5 prior runs exist: use available history.

**Scope:** All gates with audit log integration.

### 2. Acceptance Criteria

- **AC-07.1:** Specification document exists at `project_board/specs/902_04_repeated_failures_detector_spec.md`.
- **AC-07.2:** Document specifies audit log query: filter audit events with event_type="violation_added" from recent runs.
- **AC-07.3:** Document specifies grouping: group by (rule_id, file) tuple.
- **AC-07.4:** Recurrence algorithm: for each (rule_id, file) in current run, query audit logs for last N recent runs (N=5); count how many contain this pair.
- **AC-07.5:** ESCALATE trigger: if (rule_id, file) appears in 5+ consecutive most-recent runs.
- **AC-07.6:** Fallback logic: if <5 prior runs available, use available history (e.g., 3 consecutive runs if only 3 prior exist); escalate if recurrence threshold met.
- **AC-07.7:** EscalationReason structure: `{detector: "repeated_failures", severity: "MEDIUM", details: f"Violation {rule_id} in {file} has persisted across {N} consecutive runs", confidence: "HIGH", recommendation: "This is a chronic issue. Either fix the underlying problem or create a ticket to formally suppress with issue link"}`.
- **AC-07.8:** Document includes 3 scenarios: (1) first-time violation → no escalation, (2) violation present in 3 recent runs → no escalation (below threshold), (3) violation present in 5+ recent runs → escalate.
- **AC-07.9:** Document notes: "M903 will implement auto-remediation suggestions per rule and rule-specific recurrence thresholds."

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Audit logs may be incomplete initially | Detector cannot run early | Graceful fallback: if audit logs missing, detector returns empty list |
| Query performance on large audit logs | Slow escalation detection | Only query recent runs (last 5-10); 30-day rotation limits history size |
| Recurrence counter reset on deletion and re-introduction | False negatives | Conservative: deleted violations do not reset counter (acceptable; M903 can refine) |

### 4. Clarifying Questions

- **Q1:** Should recurrence threshold be rule-specific? *Assumption: Global threshold (5 runs) for MVP; M903 adds per-rule thresholds.*
- **Q2:** What defines "consecutive"? *Assumption: Last N runs in order (by timestamp), regardless of time gap; acceptable for MVP.*

---

## Requirement 08: Security-Sensitive Paths Detector Placeholder Specification

### 1. Spec Summary

**Description:** A specification for the placeholder security-sensitive paths detector (`detect_security_sensitive_paths`). This detector is stubbed in MVP and deferred to M903 because security-specific rules are not yet finalized.

**Constraints:**
- Placeholder detector must not trigger false escalations.
- Placeholder must log "TODO M903" message.
- Placeholder signature matches other detectors.

**Assumptions:**
- Security rule set (semgrep custom rules, bandit extended patterns) is deferred to M903.
- MVP is acceptable without this detector; governance/drift/suppression detectors cover primary cases.

**Scope:** All gates; deferred to M903 implementation.

### 2. Acceptance Criteria

- **AC-08.1:** Specification document exists at `project_board/specs/902_04_security_detector_placeholder_spec.md`.
- **AC-08.2:** Placeholder detector function signature: `detect_security_sensitive_paths(gate_result: dict, baseline: dict | None, audit_log: list[dict]) -> list[EscalationReason]`.
- **AC-08.3:** Placeholder implementation returns empty list (no escalation) OR single EscalationReason with: `{detector: "security_sensitive_paths", severity: "UNKNOWN", details: "TODO: implement in M903 after security rule set finalized", confidence: "UNKNOWN", recommendation: "M903 ticket TBD"}`.
- **AC-08.4:** Document clearly marks deferral: "Security rule set is not yet available; MVP will skip this detector. M903 will implement when security rules (semgrep custom patterns, bandit extensions) are finalized."
- **AC-08.5:** Document includes placeholder implementation (stub returning empty list or TODO message).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Stub left in production | False negatives in security scanning | Explicit "TODO M903" message; ticket ID tracked; M903 implements replacement |
| Feature creep into MVP scope | Timeline slips | Security detector explicitly out of scope; placeholder stub prevents confusion |

### 4. Clarifying Questions

- **Q1:** Should the stub return empty list or a TODO EscalationReason? *Assumption: Empty list (no false escalations). If logging is added (M903 audit trail), then log "TODO" and return empty list.*

---

## Requirement 09: Audit Log Schema and Persistence Strategy

### 1. Spec Summary

**Description:** A specification for the audit log storage format, location, event schema, retention policy, and security constraints. Logs are JSON Lines format, stored in `ci/artifacts/audit-logs/`, with 30-day retention.

**Constraints:**
- Format: JSON Lines (one JSON object per line, newline-delimited).
- Location: `ci/artifacts/audit-logs/<gate-name>/<YYYY-MM-DD>/<timestamp>-<mode>.jsonl`.
- Event schema: `{timestamp, run_id, gate_name, ticket_id, event_type, event_data}`.
- Event types: gate_started, tool_invoked, tool_finished, violation_added, escalation_triggered, audit_error.
- No secrets stored (API keys, tokens, passwords).
- Gitignored: yes, add `ci/artifacts/audit-logs/` to `.gitignore`.
- Retention: 30 days (rotation deferred M903).

**Assumptions:**
- JSON Lines format is acceptable (queryable via grep/jq); binary logging deferred to M903.
- 30-day retention is sufficient (M903 can extend or export).
- Concurrent writes to same file are rare (acceptable risk; M903 adds file locking if needed).

**Scope:** All gates that emit audit events.

### 2. Acceptance Criteria

- **AC-09.1:** Specification document exists at `project_board/specs/902_04_audit_log_spec.md`.
- **AC-09.2:** Document specifies location pattern: `ci/artifacts/audit-logs/<gate-name>/<YYYY-MM-DD>/<timestamp>-<mode>.jsonl`.
- **AC-09.3:** Document specifies format: JSON Lines (RFC 7464), one event per line.
- **AC-09.4:** Document specifies event schema: `{timestamp: ISO 8601, run_id: UUID string, gate_name: string, ticket_id: string or null, event_type: enum, event_data: dict}`.
- **AC-09.5:** Event types enumeration: `["gate_started", "tool_invoked", "tool_finished", "violation_added", "escalation_triggered", "audit_error"]`.
- **AC-09.6:** Event_data schema per event_type:
  - `gate_started`: `{mode: "shadow"|"blocking", upstream_agent: string, downstream_agent: string, ticket_id: string or null}`.
  - `tool_invoked`: `{tool_name: string, timeout_s: integer or null}`.
  - `tool_finished`: `{tool_name: string, exit_code: integer, duration_ms: integer}`.
  - `violation_added`: `{rule_id: string, file: string, line: integer or null, severity: enum, message: string}`.
  - `escalation_triggered`: `{detector: string, severity: enum, confidence: enum, details: string}`.
  - `audit_error`: `{error_type: string, details: string}`.
- **AC-09.7:** Document includes 3+ complete event sequences: (1) successful gate run (gate_started → tool_invoked → tool_finished → gate_completed), (2) run with violations (gate_started → violation_added → violation_added → escalation_triggered), (3) run with escalation (escalation_triggered event).
- **AC-09.8:** Document specifies retention: 30 days; rotation deferred M903.
- **AC-09.9:** Document specifies gitignore: `ci/artifacts/audit-logs/` added to `.gitignore`.
- **AC-09.10:** Document specifies security: no file contents, no secrets in event_data, keys/tokens/passwords redacted from tool outputs.
- **AC-09.11:** Sample audit log files provided at `project_board/specs/902_04_audit_log_examples/` with valid JSON Lines content.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Audit logs accumulate unbounded | Disk space, query performance | 30-day retention policy; M903 implements rotation script |
| Secrets leaked in logs | Security breach | Content filter: redact API keys, tokens, passwords; validate via content scanning (M903) |
| JSON Lines query complexity | Hard to extract data | Standard format; queryable via grep/jq; M903 adds query API if needed |
| Concurrent writes to same file | Race conditions | Acceptable risk for MVP; M903 adds file locking or per-process logs |

### 4. Clarifying Questions

- **Q1:** Should each tool invocation have a separate log file? *Assumption: No, all events for a gate run in one file per day per mode. Allows easy per-gate queries.*
- **Q2:** How are gate_completed events recorded? *Assumption: No explicit gate_completed event; completion inferred from last event timestamp. M903 can add explicit gate_completed if needed.*

---

## Non-Functional Requirements

### NFR-01: Backward Compatibility
- Version field in schema permits future upgrades without breaking consumers.
- v0.1.0 gates (M902-01) remain functional when v0.2.0 gates produce output.
- Consumers must handle version mismatches gracefully by ignoring unknown fields.

### NFR-02: Determinism
- Metadata output identical on repeated runs with same codebase state.
- No timestamps in metadata JSON except audit_events (references only).
- Score calculations deterministic (same inputs → same outputs).

### NFR-03: Bounded Payload
- audit_events field references log paths (strings), not full event bodies.
- Keeps metadata compact and queryable.
- Full events stored in audit logs (Task 10).

### NFR-04: No Secrets
- Audit logs never contain API keys, tokens, passwords.
- Validated via content filter (redaction of known patterns).
- File paths and rule IDs are safe; tool output redacted.

### NFR-05: Performance
- Escalation detector execution <100ms per detector (5 detectors ~500ms total acceptable).
- Audit logging <10ms per event (overhead low).
- Acceptable overhead on gate execution (<5% of total gate time).

### NFR-06: Configurability
- Thresholds in YAML config (no code edits).
- Detector list extensible (M903 adds security detector).
- Monitored files list in config (extensible).

### NFR-07: Auditability
- All violations and escalations logged with confidence/detector/details.
- Traceable to audit log entries (path + line number).
- Audit events append-only (no modification).

---

## Risk Register

| Risk ID | Description | Severity | Probability | Mitigation |
|---------|-------------|----------|-------------|------------|
| R1 | Architecture drift heuristic (20% threshold) misses semantic drift | MEDIUM | MEDIUM | Percentage-based conservative; M903 adds coverage-based detection |
| R2 | Repeated failures detector requires audit log infra not yet built | MEDIUM | HIGH | Placeholder stub in MVP; full impl deferred to Task 7 (Implementation phase) |
| R3 | Score calibration requires tuning after data collection | HIGH | MEDIUM | Thresholds in config file (no code edits); M903 refines based on real data |
| R4 | test_confidence unavailable for static analysis gate | LOW | MEDIUM | Fallback to "UNKNOWN"; acceptable, only advisory in metadata |
| R5 | duplication_delta unavailable if jscpd baseline missing | LOW | LOW | Marked "TODO" in spec; M903 implements when baseline strategy finalized |
| R6 | False positive escalations (governance + AR violations coincidence) | MEDIUM | LOW | Confidence levels document uncertainty; M903 adds context checks |
| R7 | Audit logs become security/privacy liability | MEDIUM | MEDIUM | No secrets stored; content filter validates; encryption (M903) optional |
| R8 | Threshold tuning creates alert fatigue | MEDIUM | MEDIUM | Conservative defaults (high thresholds); M903 tunes per team feedback |

---

## Assumptions Frozen (with Confidence Levels)

| # | Assumption | Confidence | Tunable in M903 |
|---|-----------|-----------|-----------------|
| A1 | Numeric scores (0–100 range) simpler than categorical | HIGH | Thresholds only; range fixed |
| A2 | Baseline immutable snapshot from M902-03 completion | MEDIUM | Yes; can implement rolling baseline |
| A3 | Governance file monitoring fixed set: {CLAUDE.md, Taskfile.yml, lefthook.yml, CHECKPOINTS.md, .gitignore} | MEDIUM | Yes; add more files via config |
| A4 | Drift threshold 20% conservative | MEDIUM | Yes; can lower threshold per rule |
| A5 | Repeated failures: 5 consecutive runs threshold | MEDIUM | Yes; can add time-window constraints |
| A6 | Suppression validation via GV-06 violations (M902-03) | HIGH | No; GV-06 is dependency |
| A7 | Audit log JSON Lines format queryable | HIGH | Format fixed; query API (M903) |
| A8 | ESCALATE advisory in shadow mode, blocking in blocking mode (deferred M903) | HIGH | Blocking enforcement deferred |

---

## Dependencies (Verified)

| Dependency | Ticket | Status | Impact |
|-----------|--------|--------|--------|
| Validation gate framework (gate runner, schemas) | M902-01 | COMPLETE ✓ | Provides gate_result dict format, runner CLI |
| Static analysis gate tooling (violations, aggregation) | M902-02 | COMPLETE ✓ | Provides violations format, multi-tool output |
| Governance rule enforcement (GV-06, AR-* rules) | M902-03 | COMPLETE ✓ | Provides governance violations for detectors |

---

## Specification Completeness Checklist

- [x] Requirement 01: Versioned metadata schema (10 fields, 5+ examples, backward compatibility)
- [x] Requirement 02: Score calibration formulas and YAML config (worked examples, tunable thresholds)
- [x] Requirement 03: Escalation detector framework (interface, 5 detector stubs, MVP scope)
- [x] Requirement 04: Governance file modification detector (monitored files, detection logic, 3 scenarios)
- [x] Requirement 05: Architecture drift detector (baseline, 20% threshold, 3 scenarios)
- [x] Requirement 06: Suppression abuse detector (GV-06 violations, recurring detection, 3 scenarios)
- [x] Requirement 07: Repeated failures detector (audit log query, 5-run threshold, 3 scenarios)
- [x] Requirement 08: Security detector placeholder (deferred to M903, no false escalations)
- [x] Requirement 09: Audit log schema (JSON Lines, events, retention, security, 3+ examples)
- [x] All non-functional requirements documented (backward compatibility, determinism, performance, security)
- [x] Risk register complete with mitigations
- [x] All assumptions frozen with confidence levels
- [x] All dependencies verified
- [x] All clarifying questions resolved
- [x] Spec is deterministic and actionable for implementation (Tasks 10–13)

---

**End of Specification Document**
