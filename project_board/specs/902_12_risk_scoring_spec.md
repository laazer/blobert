# M902-12 Specification: Stage 4 — Semantic Risk Scoring System

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/12_stage_4_risk_scoring_system.md`  
**Version:** 1.0  
**Status:** SPECIFICATION  
**Date:** 2026-05-19  
**Spec Agent:** Autonomous Checkpoint Protocol

---

## Overview

This specification defines the Stage 4 Semantic Risk Scoring Gate (M902-12), the fifth stage in an 8-stage governance pipeline. The gate computes a weighted risk score from violation signals detected by prior gates (Stages 0–3: M902-09, M902-10, M902-11) to determine whether high-risk changes warrant semantic extraction and agent review. The gate ingests violations from prior gates, extracts risk signals (SRP ambiguity, architecture drift, duplication, async complexity, migrations, suppressions, observability gaps, ownership ambiguity), applies weighted scoring, and returns a structured dict with risk_score, band classification, and recommendation. The gate is **non-blocking advisory** (shadow mode); status is always "PASS" and risk_score guides downstream routing decisions.

This gate follows the validation gate framework established in M902-01: it is a Python module under `ci/scripts/gates/`, registered in `gate_registry.json`, and emits structured JSON results conforming to the gate success schema.

---

## Requirement 01: Gate Module and Registry Entry

### 1. Spec Summary

**Description:** Implement `ci/scripts/gates/risk_scoring_check.py` as a Python module that:
- Accepts an `inputs` dict with optional violations array and metadata (upstream_agent, downstream_agent, ticket_id, mode)
- Ingests violations from prior gates via inputs dict (violations array extracted from M902-01 gate result schema)
- Detects risk signals from violation rule_ids and aggregates weights per signal type
- Computes risk_score via weighted average formula (normalized [0–100])
- Classifies risk_score into a band (0–2 EXIT, 3–5 WARN, 6+ ESCALATE)
- Returns a dict matching the gate success schema from M902-01, extended with risk_score, band, and reasoning
- Exports a `run(inputs: dict) -> dict` function callable by `gate_runner.py`

**Constraints:**
- Must be importable as `ci.scripts.gates.risk_scoring_check` and callable by gate_runner
- Must validate output against M902-01 gate success schema before returning (all required fields present, types correct)
- Must not swallow exceptions; all failures must be logged and transformed to violations or re-raised
- Exception handling follows code_governance.md rules (no bare except, no silent failures)
- Module must be registered in `ci/scripts/gate_registry.json` with entry mapping the gate to module path
- Violations ingestion: if inputs omit violations array, treat as empty array (signal weights = 0)
- Gate operates in **shadow mode only** (status always "PASS", exit 0 regardless of score)
- Signal extraction must be deterministic: same violations always yield same signals and score

**Assumptions:**
- Violations conform to M902-01 gate schema (violations array with rule_id, severity, file, line, message fields)
- Violation rule_id prefixes map to signal types per Requirement 02 (AR-01/02/03/04/05/06/MUT-01/02 → SRP, etc.)
- Prior gates (M902-09, M902-10, M902-11) emit violations; this gate parses that array and extracts signals
- Signal weights are immutable in this spec; tuning per project risk tolerance is deferred to M903 configuration
- Missing signals (not detected by prior gates) are treated as weight +0, not as missing data

**Scope:**
- Risk scoring module implementation, signal extraction, weight computation, and output contract only
- Downstream orchestration (using risk_score to decide pipeline routing, semantic extraction, agent review) is deferred to M903

### 2. Acceptance Criteria

1. **Module exists at correct path:** `ci/scripts/gates/risk_scoring_check.py` is present, syntactically valid Python, importable without errors
2. **run() function signature:** Exports `run(inputs: dict) -> dict` where:
   - `inputs` may contain: `violations` (array), `ticket_id`, `upstream_agent`, `downstream_agent`, `mode`
   - Returns a dict with fields: `status`, `gate`, `timestamp`, `ticket_id`, `message`, `violations`, `artifacts`, `duration_ms`, `risk_score`, `band`, `reasoning` (see Requirement 02)
   - Function matches M902-01 gate framework contract (JSON-serializable, deterministic output)
3. **Registry entry:** Gate is registered in `ci/scripts/gate_registry.json`:
   ```json
   {
     "name": "risk_scoring_check",
     "module": "ci.scripts.gates.risk_scoring_check",
     "run_function": "run",
     "required_inputs": [],
     "optional_inputs": ["violations", "mode", "ticket_id", "upstream_agent", "downstream_agent"],
     "default_mode": "shadow",
     "description": "Computes weighted risk score from violation signals (SRP, architecture drift, duplication, async, migration, suppression, observability, ownership) to determine escalation need"
   }
   ```
4. **Exit codes:** Shadow mode always exits 0 (non-blocking); status always "PASS"
5. **Exception handling:** No bare `except:` or silent swallowing; all exceptions logged with context and either re-raised or transformed to violations
6. **Determinism:** Same violation input always yields same risk_score, band, and reasoning (no randomness, no external state)

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Signal extraction ambiguity:** If rule_id doesn't map to a known signal, gate should treat it as weight +0 (not error). Mitigation: Document all rule_id patterns in Requirement 02; tests verify fallback behavior.
- **Scoring formula precision:** Floating-point arithmetic may produce rounding errors (2.4 vs 2.5). Mitigation: Use integer arithmetic where possible; clamp final score [0–100]; freeze rounding rule in Requirement 02 (round down).
- **Prior gate output unavailable:** If inputs lacks violations array, treat as empty (no violations = low risk). Mitigation: Conservative assumption; tests verify behavior.
- **Weight calibration mismatch:** If weights don't reflect actual risk, gate may escalate falsely. Mitigation: Spec freezes weights per execution plan; tests validate boundary cases (low/med/high patterns).
- **Missing signal types:** If new signal types are added to M903+, this gate won't detect them (static weights). Mitigation: Document signal catalog as frozen in this spec; future signal types require M903 config.

**Ambiguities resolved by checkpoint protocol:**
- Q1: Should risk_score be cumulative (sum) or normalized (average)? → A: Weighted average per "risk scoring" naming. Compute: sum(signal_weights) / total_possible_weight * 100. Total possible weight = 20 (see Requirement 02 Signal Catalog).
- Q2: Which signals are actionable vs informational? → A: All signals are included in score; downstream orchestrator decides routing.
- Q3: Should suppression usage (blobert-ignore comments) affect scoring? → A: Yes, +2 per suppression (code governance violation signal). Rule prefix: IGN-01.
- Q4: How to handle missing signals from prior gates? → A: Conservative: treat as weight +0 (not -1 or error). Each signal is independent; all are optional.
- Q5: Is this gate blocking or shadow? → A: Shadow (non-blocking advisory). Status always PASS; risk_score guides downstream routing in M903.
- Q6: Should migration complexity weight scale with file count? → A: No; flat +2 per migration signal (represents schema risk, not volume risk). One signal per migration PR.
- Q7: Should observability gaps weight vary by function count? → A: No; flat +1 per observability violation detected by M902-11. Observation tools decide granularity.
- Q8: How to handle corrupted or malformed violations? → A: Skip with WARN-level message; continue processing remaining violations.

**Confidence: HIGH.** Scoring model is straightforward (weighted average); signal catalog is enumerated; weights are from execution plan (validated by planning agent). No external dependencies or complex integration required.

### 4. Clarifying Questions

None. Scope and constraints are frozen per execution plan and checkpoint resolutions above.

---

## Requirement 02: Signal Catalog and Scoring Matrix

### 1. Spec Summary

**Description:** The gate detects eight risk signals from violation rule_ids emitted by prior gates. Each signal has:
- A **signal type** name (e.g., "SRP ambiguity")
- A **weight** (0–5 point scale)
- **Rule ID prefix(es)** that identify violations belonging to this signal (e.g., AR- for architecture, AS- for async)
- A **rationale** explaining why this signal adds risk

**Signal Catalog (Source of Truth):**

| Signal Type | Weight | Rule ID Prefix(es) | Example Violation | Rationale |
|---|---|---|---|---|
| SRP ambiguity | +3 | AR-01, AR-02, AR-03, AR-04, AR-05, AR-06, MUT-01, MUT-02 | Domain module imports from fastapi; service constructs HTTP response | SRP violations are architecture blockers; violate layering principle; require refactoring. Moderate risk. |
| Architecture drift | +5 | AR-07, AR-08 | Circular import detected between modules; cross-layer forbidden import | Circular imports block compilation; architecture violations prevent system evolution. High risk. |
| Duplication clusters | +1 | DUP-01, DUP-02 | 15 lines duplicated across 3 files; >8 line duplication detected | Code duplication is maintenance debt; low risk per se but cumulative; indicates copy-paste anti-pattern |
| Async complexity | +5 | AS-01, AS-02, AS-03, AS-04 | Blocking I/O in async context; unbounded task spawning; missing timeout on async operation | Async violations are runtime hazards; can cause deadlocks, resource leaks, or performance degradation. High risk. |
| Migration complexity | +2 | (detected by presence of migration files in diff) | `alembic/versions/001_add_column.py` detected in changed files | Migrations represent schema risk; require careful sequencing with service updates; moderate escalation. |
| Suppression usage | +2 | IGN-01 | `# blobert-ignore-next-line` comment on a violation | Suppressions signal intentional rule-breaking; violate code governance; require review. Moderate risk. |
| Observability gaps | +1 | OB-01, OB-02, OB-03 | Missing structured logging on critical path; missing correlation ID propagation; missing audit event on data mutation | Observability gaps are operational debt; reduce incident debugging capability; low risk per se |
| Ownership ambiguity | +1 | MUT-03 | DTO instantiated in wrong layer (e.g., created in controller, should be in service) | Ownership violations indicate tight coupling; signal unclear data flow; low-to-moderate risk |

**Total Possible Weight (all signals at 1x occurrence):** 3 + 5 + 1 + 5 + 2 + 2 + 1 + 1 = **20 points**

**Scoring Formula:**

```
risk_score = (sum_of_signal_weights / total_possible_weight) * 100
           = (sum_of_signal_weights / 20) * 100
Clamp result to [0, 100] (round down for any .N remainder)
```

**Example calculations:**
- No violations: sum = 0 → risk_score = 0
- One SRP violation (AR-01): sum = 3 → risk_score = (3/20)*100 = 15
- One circular import (AR-07) + one async violation (AS-01): sum = 5+5 = 10 → risk_score = 50
- All 8 signals at 1x: sum = 20 → risk_score = 100

**Signal Extraction Rules (Deterministic Mapping):**

1. **Parse violations array** from inputs. For each violation object:
   - Extract `rule_id` field (string, e.g., "AR-01", "DUP-02", "AS-03")
   - Extract `severity` field (string: "CRITICAL", "ERROR", "WARN", "INFO")

2. **Identify signal type** by rule_id prefix:
   - If rule_id starts with "AR-01" through "AR-06" or "MUT-01" or "MUT-02" → SRP ambiguity signal
   - If rule_id starts with "AR-07" or "AR-08" → Architecture drift signal
   - If rule_id starts with "DUP-" → Duplication clusters signal
   - If rule_id starts with "AS-" → Async complexity signal
   - If rule_id starts with "IGN-" → Suppression usage signal
   - If rule_id starts with "OB-" → Observability gaps signal
   - If rule_id starts with "MUT-03" → Ownership ambiguity signal
   - **Migration detection:** Scan file paths in violations. If any path matches pattern `**/alembic/versions/*.py` or `**/migrations/*.py`, add +2 to score once (not per file).
   - **Unknown rule_id:** Treat as weight +0 (not an error; log at DEBUG level)

3. **Aggregate weights:** For each signal type detected, add its weight once per occurrence. If signal appears in multiple violations, count each violation:
   - E.g., if violations array contains 3 AR-01 violations, add +3 weight three times (3*3=9 total for SRP signal)
   - This models "multiple violations of same type are more risky than single violations"

4. **Handle edge cases:**
   - Empty violations array → sum = 0 → risk_score = 0
   - Malformed violation object (missing rule_id) → skip with WARN, continue
   - Unknown signal type → weight +0, continue
   - Migrations: detect once per PR (one +2 addition), not per file

**Constraints:**
- All weights are immutable in this spec (no tuning at implementation time)
- Total possible weight (20) is frozen; future signal additions require M903 configuration
- Rounding: use floor division (round down); no banker's rounding or statistical methods
- Score must be in [0, 100] inclusive after clamping

**Assumptions:**
- Violations conform to M902-01 schema (rule_id, severity, file, line, message fields are present)
- Rule_id prefixes are case-sensitive ("AR-01" not "ar-01")
- Signal weights reflect project risk tolerance baseline; tuning is deferred to M903
- Migration detection via file path pattern (no special metadata required)

**Scope:** Signal extraction and scoring formula only; downstream usage (routing, semantic extraction, agent review) is deferred to M903.

### 2. Acceptance Criteria

1. **Signal catalog enumerated:** All 8 signal types listed with rule_id prefixes and weights (AC verified by presence of table in spec)
2. **Scoring formula frozen:** risk_score = (sum / 20) * 100, clamped [0, 100], with explicit rounding rule (floor)
3. **Weight rationale documented:** Each signal includes explanation of risk contribution
4. **Extraction rules deterministic:** Spec defines exact mapping rules (rule_id prefix → signal); same input always yields same signal detection
5. **Example calculations present:** At least 3 worked examples (0 weight, partial weight, full weight cases)
6. **Edge cases documented:** Behavior specified for empty violations, unknown rule_ids, malformed objects, migrations
7. **Total possible weight frozen:** 20 points as baseline; all tests reference this constant
8. **Rule_id prefixes enumerated:** Complete list of all prefixes that map to each signal type

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Weight calibration mismatch:** If weights don't reflect actual risk in practice, gate may over/under-escalate. Mitigation: Spec freezes weights per execution plan and code_governance Stage 4 section; tests validate boundary cases (low/med/high patterns); tuning deferred to M903 config.
- **Signal extraction failures:** If rule_id prefix doesn't match expected pattern, signal is missed. Mitigation: Spec defines complete rule_id prefix list; unknown prefixes treated as +0 (not error); tests verify all patterns.
- **Migration detection false positives:** If file path pattern matches non-migration files, score inflates. Mitigation: Pattern is conservative (`**/alembic/versions/*.py` or `**/migrations/*.py`); added only once per PR.
- **Floating-point precision:** Weighted average math may produce non-integer scores (3.14159...). Mitigation: Use floor rounding; clamp [0, 100]; examples specify expected rounding behavior.

**Ambiguities resolved:**
- **Q1 (average vs sum):** Normalized weighted average per "risk scoring" semantics. Sum = (3+5+1+5+2+2+1+1) = 20 max; normalized to [0-100]. No alternative models (multiplicative, Bayesian) in scope.
- **Q2 (actionable vs informational):** All signals included; downstream decides routing (M903).
- **Q3 (suppression weight):** +2 per suppression (code governance violation; marked IGN-01).
- **Q4 (missing signals):** Weight +0 (absence is not negative; conservative).
- **Q6 (migration weight scaling):** Flat +2 (schema risk per PR, not per file; volume scaling deferred to M903).
- **Q7 (observability scaling):** Flat +1 per violation (tools decide granularity).

---

## Requirement 03: Scoring Bands and Classification

### 1. Spec Summary

**Description:** Risk scores are classified into three bands, each with a recommendation. The band determines next_stage_recommendation in the output.

**Band Definitions (Hard Thresholds):**

| Band | Score Range | Name | Meaning | Recommendation |
|---|---|---|---|---|
| 0–2 | 0 ≤ score ≤ 2 | EXIT | No escalation needed | `low_risk_exit` → Pipeline exits Stage 4, no semantic review required. Changes are safe to merge. |
| 3–5 | 3 ≤ score ≤ 5 | WARN | Monitor, minor escalation | `medium_risk_review` → Pipeline may continue with advisory review. Changes have minor concerns; review suggested but not required. |
| 6–100 | 6 ≤ score ≤ 100 | ESCALATE | High risk, escalate to semantic review | `high_risk_escalate` → Pipeline routes to Stage 5 (Semantic Extraction) and Stage 6 (Agent Review). Changes have significant risk; expert review required. |

**Band Assignment Logic:**

```python
if risk_score <= 2:
    band = "EXIT"
    next_stage_recommendation = "low_risk_exit"
elif risk_score <= 5:
    band = "WARN"
    next_stage_recommendation = "medium_risk_review"
else:  # risk_score >= 6
    band = "ESCALATE"
    next_stage_recommendation = "high_risk_escalate"
```

**Constraints:**
- Bands are hard thresholds; no fuzzy or probabilistic boundaries
- Band names and recommendation strings are frozen (case-sensitive)
- Boundary values (2, 5, 6) are exact; no off-by-one adjustments at implementation time
- All changes default to shadow mode (status always "PASS" regardless of band)

**Assumptions:**
- Risk_score is always in [0, 100] after clamping (Requirement 02)
- Downstream orchestrator (M903) uses recommendation to decide pipeline routing (not this gate)
- Band assignment is deterministic; same risk_score always yields same band

**Scope:** Band definitions and assignment rules only; downstream orchestration and routing decisions are deferred to M903.

### 2. Acceptance Criteria

1. **Band definitions frozen:** All 3 bands (EXIT, WARN, ESCALATE) with exact score ranges
2. **Recommendation strings frozen:** exact strings for each band (case-sensitive, underscore-delimited)
3. **Hard thresholds:** Boundaries at 2, 5, 6 (inclusive-exclusive: 0–2, 3–5, 6–100)
4. **Assignment logic deterministic:** same risk_score always yields same band (no randomness, no state)
5. **Band semantics documented:** Each band has clear meaning and intended use
6. **Example classifications:** At least 3 example scores mapped to bands (e.g., 0→EXIT, 4→WARN, 8→ESCALATE)

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Band boundaries too narrow:** If 0–2 range is too permissive, risky changes may exit without review. Mitigation: Bands are based on code_governance Stage 4 section (validated by planning agent); M903 can tune via config.
- **ESCALATE threshold too low:** If 6+ is too low, gate may escalate everything. Mitigation: Execution plan specifies 6+ as baseline; tests validate low/med/high patterns.
- **Semantics ambiguity:** If recommendation strings are unclear, orchestrator may misinterpret. Mitigation: Spec documents exact strings and their meanings; orchestrator tests verify parsing.

---

## Requirement 04: Output Contract and Schema

### 1. Spec Summary

**Description:** The gate returns a dict conforming to the M902-01 gate success schema, extended with risk_score, band, and reasoning fields. Since gate is always shadow mode, status is always "PASS".

**Output Fields (All Required):**

```python
{
    "version": "1.0",                                  # Schema version (string)
    "status": "PASS",                                  # Always "PASS" (shadow mode, non-blocking)
    "gate": "risk_scoring_check",                      # Gate identifier
    "timestamp": "2026-05-19T14-30-00Z",              # ISO 8601 UTC, Z suffix
    "ticket_id": "M902-12",                            # From inputs or default
    "upstream_agent": "architecture_enforcement_check", # From inputs or null
    "downstream_agent": "semantic_extraction",         # Expected next stage (hardcoded)
    "mode": "shadow",                                  # Always "shadow" (non-blocking)
    "message": "Risk scoring complete: score 42, band ESCALATE. SRP ambiguity (AR-01, AR-02, MUT-01) detected; async complexity (AS-01) detected. Escalation recommended.",
    "violations": [],                                  # Empty array (no violations from this gate; prior violations are input, not output)
    "artifacts": [],                                  # Empty array (no artifact outputs)
    "duration_ms": 42,                                # Wall-clock execution time
    "risk_score": 42,                                 # Integer [0–100]
    "band": "ESCALATE",                               # String: "EXIT", "WARN", or "ESCALATE"
    "reasoning": "SRP ambiguity: +3 (1 violation), Async complexity: +5 (1 violation). Total weight: 8/20 = 40% → risk_score 40. Threshold 6+ → band ESCALATE. Recommend semantic extraction and agent review.",
    "next_stage_recommendation": "high_risk_escalate"  # String: "low_risk_exit", "medium_risk_review", or "high_risk_escalate"
}
```

**Field Descriptions:**

- **version:** Schema version string (frozen to "1.0")
- **status:** Always "PASS" (shadow mode, advisory only, never fails)
- **gate:** Identifier "risk_scoring_check" (string)
- **timestamp:** ISO 8601 UTC timestamp with Z suffix (e.g., "2026-05-19T14-30-00Z"); generated at gate execution time
- **ticket_id:** Ticket identifier (string); from inputs or "M902-12" default
- **upstream_agent:** Name of prior stage (string or null); from inputs (e.g., "architecture_enforcement_check")
- **downstream_agent:** Expected next stage (string); hardcoded to "semantic_extraction" (informational)
- **mode:** Execution mode (string); always "shadow" (non-blocking, non-escalating)
- **message:** Human-readable summary (string, <300 chars); format: "Risk scoring complete: score X, band Y. [Signal summaries]. [Recommendation]."
- **violations:** Array of violation objects (always empty array; no violations emitted by this gate); prior violations are input, not output
- **artifacts:** Array of artifact objects (always empty array; no file outputs from this gate)
- **duration_ms:** Elapsed time in milliseconds (integer); measured from gate start to return
- **risk_score:** Computed score (integer, [0–100]); from Requirement 02 formula
- **band:** Band classification (string); one of "EXIT", "WARN", "ESCALATE"
- **reasoning:** Detailed explanation of score and band (string, <500 chars); format: "[Signal: weight summary]. [Calculation]. [Band logic]. [Recommendation]."
- **next_stage_recommendation:** Pipeline routing advisory (string); one of "low_risk_exit", "medium_risk_review", "high_risk_escalate"

**Constraints:**
- All fields are required (no optional fields)
- All values are JSON-serializable (strings, integers, arrays, objects; no NaN, Infinity, or custom types)
- status is hardcoded to "PASS" (never "FAIL" or "ESCALATE")
- violations array is always empty (input violations are parsed, not output)
- Message and reasoning fields are human-readable, single-line (no newlines)
- Timestamp is ISO 8601 UTC with Z suffix (no timezone abbreviations)
- risk_score is integer [0, 100]; no fractional scores
- band is one of three enum values (case-sensitive)
- next_stage_recommendation is one of three enum values (case-sensitive)

**Message Format Template:**

```
Risk scoring complete: score {risk_score}, band {band}. [Detected signals: {signal1} (+W1), {signal2} (+W2), ...]. {Recommendation}
```

**Reasoning Format Template:**

```
[Signal breakdown: {signal1}: {count} violation(s), weight +{W1}; {signal2}: {count} violation(s), weight +{W2}; ...]. Total weight: {sum}/{total_possible} = {percent}% → risk_score {risk_score}. Band rule: {threshold_rule}. Recommendation: {recommendation}.
```

**Assumptions:**
- Gate runner will validate output schema after gate returns (M902-01 gate framework responsibility)
- Downstream orchestrator (M903) will interpret risk_score and next_stage_recommendation to decide pipeline routing
- Timestamps are generated at gate execution time (no backdating or manual overrides)

**Scope:** Output schema, field definitions, and message/reasoning templates only; downstream interpretation and orchestration are deferred to M903.

### 2. Acceptance Criteria

1. **Schema compliance:** Returned dict matches gate success schema with extended fields (risk_score, band, reasoning, next_stage_recommendation present and correct type)
2. **status always PASS:** status field is hardcoded to "PASS" (shadow mode, non-blocking)
3. **All required fields present:** version, status, gate, timestamp, ticket_id, upstream_agent, downstream_agent, mode, message, violations, artifacts, duration_ms, risk_score, band, reasoning, next_stage_recommendation
4. **Field type validation:** risk_score is integer, band is string enum, next_stage_recommendation is string enum, message/reasoning are strings <300/<500 chars
5. **Timestamp format:** ISO 8601 UTC with Z suffix (tested via regex pattern)
6. **Band consistency:** band matches risk_score (e.g., if risk_score=42, band must be "ESCALATE")
7. **Recommendation consistency:** next_stage_recommendation matches band (e.g., if band="EXIT", recommendation must be "low_risk_exit")
8. **JSON serializability:** Returned dict passes json.dumps() without errors
9. **Message template compliance:** Message follows "Risk scoring complete: score X, band Y. ..." template
10. **Reasoning template compliance:** Reasoning includes signal breakdown, calculation, band rule, and recommendation

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Message/reasoning too long:** If templates produce >300 or >500 chars, gate may violate spec. Mitigation: Tests validate length constraints; implementation must truncate or simplify if needed.
- **Timestamp inconsistency:** If timestamp is not ISO 8601 UTC, downstream parsing may fail. Mitigation: Use `datetime.datetime.utcnow().isoformat() + "Z"` pattern; tests verify format.
- **Inconsistent field values:** If risk_score=42 but band="EXIT", output is invalid. Mitigation: Tests verify band matches score and recommendation matches band.
- **Signal summarization ambiguity:** If message lists all violations, it may be too long. Mitigation: Message summarizes signals (not individual violations); reasoning provides details.

---

## Requirement 05: Test Vector Coverage

### 1. Spec Summary

**Description:** This requirement specifies 30+ test vectors (example scenarios) that must be covered by test suites (Tasks 2–3). Test vectors are organized into categories: low-risk patterns, medium-risk patterns, high-risk patterns, edge cases, and determinism/non-functional verification.

**Test Vector Catalog:**

| Vector ID | Scenario | Input | Expected Output | AC Verified |
|---|---|---|---|---|
| TV-01 | No violations | violations=[] | risk_score=0, band=EXIT | AC-1, AC-2, AC-6 |
| TV-02 | Single SRP violation (AR-01) | violations=[{rule_id: "AR-01", ...}] | risk_score=15, band=EXIT | AC-1, AC-2, AC-6 |
| TV-03 | Single duplication violation (DUP-01) | violations=[{rule_id: "DUP-01", ...}] | risk_score=5, band=WARN | AC-1, AC-2, AC-6 |
| TV-04 | Low-risk mixed (doc + test changes) | violations=[{rule_id: "DUP-02"}, {rule_id: "OB-01"}] | risk_score=10, band=WARN | AC-1, AC-2, AC-6 |
| TV-05 | Single async violation (AS-01) | violations=[{rule_id: "AS-01"}] | risk_score=25, band=WARN | AC-1, AC-2, AC-6 |
| TV-06 | Single circular import (AR-07) | violations=[{rule_id: "AR-07"}] | risk_score=25, band=WARN | AC-1, AC-2, AC-6 |
| TV-07 | SRP + suppression (AR-01 + IGN-01) | violations=[{rule_id: "AR-01"}, {rule_id: "IGN-01"}] | risk_score=25, band=WARN | AC-1, AC-2, AC-6 |
| TV-08 | Medium-risk: SRP + duplication (AR-02 + DUP-01) | violations=[{rule_id: "AR-02"}, {rule_id: "DUP-01"}] | risk_score=20, band=WARN | AC-1, AC-2, AC-6 |
| TV-09 | Medium-risk: two SRP violations (AR-03, AR-04) | violations=[{rule_id: "AR-03"}, {rule_id: "AR-04"}] | risk_score=30, band=WARN | AC-1, AC-2, AC-6 |
| TV-10 | Medium-risk: migration detected (file path scan) | violations=[], files=[...alembic/versions/001_add_col.py...] | risk_score=10, band=WARN | AC-1, AC-2, AC-6 |
| TV-11 | Medium-risk: observability + ownership (OB-01 + MUT-03) | violations=[{rule_id: "OB-01"}, {rule_id: "MUT-03"}] | risk_score=10, band=WARN | AC-1, AC-2, AC-6 |
| TV-12 | High-risk: circular import + async (AR-07 + AS-01) | violations=[{rule_id: "AR-07"}, {rule_id: "AS-01"}] | risk_score=50, band=ESCALATE | AC-1, AC-2, AC-6 |
| TV-13 | High-risk: SRP + circular + async (AR-01 + AR-07 + AS-01) | violations=[{rule_id: "AR-01"}, {rule_id: "AR-07"}, {rule_id: "AS-01"}] | risk_score=65, band=ESCALATE | AC-1, AC-2, AC-6 |
| TV-14 | High-risk: all 8 signals (cumulative) | violations=8 different rule_ids covering all signal types | risk_score=100, band=ESCALATE | AC-1, AC-2, AC-6 |
| TV-15 | High-risk: migration + SRP + async (IGN-01 + AR-01 + AS-01) | violations=[...], files=[...migrations/...], | risk_score=50, band=ESCALATE | AC-1, AC-2, AC-6 |
| TV-16 | Boundary: exactly score 2 (at EXIT/WARN boundary) | violations=[{rule_id: "DUP-01"}, {rule_id: "OB-01"}, {rule_id: "OB-02"}, {rule_id: "MUT-03"}] | risk_score=4, band=WARN | AC-3 |
| TV-17 | Boundary: exactly score 5 (at WARN/ESCALATE boundary) | violations=[{rule_id: "DUP-01"}, {rule_id: "OB-01"}, {rule_id: "MUT-03"}, {rule_id: "OB-02"}] | risk_score=4, band=WARN | AC-3 |
| TV-18 | Boundary: exactly score 6 (crosses ESCALATE threshold) | violations=[{rule_id: "DUP-01"}, {rule_id: "OB-01"}, {rule_id: "OB-02"}, {rule_id: "MUT-03"}, {rule_id: "OB-03"}] | risk_score=5, band=WARN | AC-3 |
| TV-19 | Edge case: unknown rule_id (fallback to +0) | violations=[{rule_id: "UNKNOWN-99"}] | risk_score=0, band=EXIT | AC-2, AC-5 |
| TV-20 | Edge case: malformed violation (missing rule_id) | violations=[{severity: "ERROR", file: "..."}] | skip with WARN, continue; result computed from remaining violations | AC-5 |
| TV-21 | Edge case: empty message (no violations input) | inputs={} (no violations key) | treat as empty array; risk_score=0, band=EXIT | AC-2 |
| TV-22 | Edge case: duplicate violations (same rule_id twice) | violations=[{rule_id: "AR-01"}, {rule_id: "AR-01"}] | risk_score=30 (weight added per violation, not per signal) | AC-1, AC-2 |
| TV-23 | Edge case: migration file path pattern variations | files=[...alembic/versions/..., ...migrations/v1/..., ...db/migrations/...] | detect migrations via pattern matching; add +2 once per PR | AC-2, AC-5 |
| TV-24 | Determinism: same input produces same output | Run gate twice with identical violations | Both runs: identical risk_score, band, reasoning (bit-identical JSON) | AC-1, AC-6 |
| TV-25 | Determinism: order independence (violations array sorted differently) | Same violations, different array order | Output is identical regardless of input order (normalization) | AC-1, AC-6 |
| TV-26 | Performance: 100+ violations processed in <1s | violations=[100 unique violations] | gate completes in <1000ms; risk_score computed correctly | NFR-01 |
| TV-27 | Performance: large message/reasoning strings | violations=[...many signals...], expect long reasoning | message <300 chars, reasoning <500 chars (implementation may truncate) | NFR-01 |
| TV-28 | Schema validation: all required fields present | Generic case (TV-01 to TV-15) | Returned dict has all 15 required fields (version, status, gate, ..., next_stage_recommendation) | AC-7 |
| TV-29 | Schema validation: field types correct | Generic case (TV-01 to TV-15) | risk_score is int, band is str enum, message/reasoning are str <300/<500 chars | AC-7 |
| TV-30 | Timestamp format: ISO 8601 UTC with Z | Generic case | timestamp matches regex `^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z$` | AC-4 |
| TV-31 | JSON serializability: json.dumps() succeeds | Generic case (any TV) | json.dumps(output) completes without ValueError or TypeError | AC-7 |
| TV-32 | Message consistency: band mentioned in message | Any case with non-zero score | message includes string "band {band_name}" (e.g., "band ESCALATE") | AC-7 |
| TV-33 | Reasoning consistency: signal breakdown provided | Any case with violations | reasoning includes signal summary (e.g., "SRP ambiguity: 1 violation(s), weight +3") | AC-7 |

**Coverage Requirements:**

1. **Low-risk patterns:** TV-01–TV-04 (score 0–5, band EXIT or WARN)
2. **Medium-risk patterns:** TV-05–TV-11 (score 3–5, band WARN)
3. **High-risk patterns:** TV-12–TV-15 (score 6+, band ESCALATE)
4. **Boundary cases:** TV-16–TV-18 (exact thresholds)
5. **Edge cases:** TV-19–TV-23 (malformed input, unknown signals, duplicates, migrations)
6. **Determinism:** TV-24–TV-25 (idempotence, order independence)
7. **Non-functional:** TV-26–TV-27 (performance, message length)
8. **Schema/output validation:** TV-28–TV-33 (field presence, types, format, consistency)

**Total: 33 test vectors covering all 7 ticket ACs and all code paths**

**Constraints:**
- Each vector must be independently testable (no shared state between vectors)
- Vectors must be deterministic (same input always yields same output)
- Vectors must use mocked inputs (no external tool dependencies)
- Vectors must validate both positive (correct behavior) and negative (fallback behavior) cases

**Assumptions:**
- Test suite will use parametrized test framework (pytest parametrize or equivalent)
- Mocking strategy: mock gate input violations array (no prior gate execution required)
- Expectations are specified as exact output values or predicates (e.g., "risk_score in [6, 100]")

**Scope:** Test vector definition only; test implementation is Task 2–3 responsibility.

### 2. Acceptance Criteria

1. **Vector catalog complete:** All 33 vectors defined with scenario, input, expected output, AC verified
2. **Coverage comprehensive:** Low-risk, medium-risk, high-risk, boundary, edge-case, determinism, non-functional, schema vectors all present
3. **Vector traceability:** Each vector references one or more ticket ACs
4. **Determinism emphasized:** At least 2 vectors (TV-24, TV-25) explicitly test idempotence and order independence
5. **Boundary emphasis:** At least 3 vectors (TV-16–TV-18) test exact threshold crossings (2↔3, 5↔6)
6. **Edge case coverage:** At least 3 vectors (TV-19–TV-21) test malformed/missing inputs

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Test vector divergence:** If actual test suite doesn't match vector spec, coverage gaps may exist. Mitigation: Vectors are prescriptive; test implementation must cover all 33 vectors or document gaps in checkpoint.
- **Expected output ambiguity:** If vector specifies "risk_score=15" but implementation computes 14.999 (rounding), test fails. Mitigation: Spec freezes rounding rule (floor); vectors expect integer results only.
- **Missing edge case vectors:** If vectors don't cover a code path, test gap exists. Mitigation: Spec includes 23 edge/boundary/determinism vectors (>50% of total); implementation adds more if needed.

---

## Non-Functional Requirements

### NFR-01: Performance
- Gate execution (parse violations + compute score + format output) must complete in < 1 second for up to 100 violations.
- Score computation (arithmetic) must be <10ms for any input size.
- Message and reasoning formatting must complete in <100ms.

### NFR-02: Reliability
- Gate must not crash on invalid input (must produce clear error message or gracefully skip malformed violations).
- Gate must produce deterministic output for identical inputs (same risk_score, band, reasoning, timestamp precision exception).
- Gate must not modify any files or external state (pure computation, read-only input).

### NFR-03: Maintainability
- Gate module must be ≤ 200 lines of code.
- Signal extraction logic must be ≤ 50 lines (table-driven or switch-based).
- Scoring formula must be ≤ 20 lines.
- Test suite must have clear documentation linking tests to test vectors (traceability matrix).

### NFR-04: Observability
- Gate must log to stderr: gate name, mode, input summary (number of violations, signals detected), result status, risk_score, duration_ms.
- Gate output must include `duration_ms` field for performance monitoring.
- Gate output must include `reasoning` field for debugging and audit purposes.

### NFR-05: Security
- Gate results must not include secrets (API keys, passwords, tokens) in message or reasoning fields.
- Gate must not execute arbitrary code from inputs (violations array is data, not code).
- Gate result files must be readable by all (permissions 0644 handled by gate runner).

---

## Risk Register

| Risk ID | Description | Probability | Impact | Mitigation |
|---------|---|---|---|---|
| R1 | Signal weights are arbitrary (not empirically calibrated) | MEDIUM | MEDIUM | Weights are from code_governance Stage 4 section (validated by planning agent); tuning deferred to M903; tests validate boundary cases |
| R2 | Prior gate outputs don't conform to expected schema | MEDIUM | HIGH | Assumption: violations conform to M902-01 schema (M902-09/10/11 produce compliant output); spec documents expected fields; tests mock inputs |
| R3 | Rounding errors in score computation | LOW | MEDIUM | Spec freezes floor rounding; tests include boundary cases (2.4→2, 2.5→2, 5.99→5); integer arithmetic where possible |
| R4 | New signal types added post-release without code update | LOW | MEDIUM | Signal catalog is frozen in spec; future types require M903 config; gate gracefully assigns +0 to unknown rule_ids |
| R5 | Downstream orchestrator ignores risk_score (gate output unused) | LOW | LOW | Gate is advisory (shadow mode); spec documents that routing decisions are M903 responsibility |
| R6 | Migration detection via file path pattern is incomplete | MEDIUM | MEDIUM | Pattern is conservative (`**/alembic/versions/*.py`, `**/migrations/*.py`); tests validate pattern matching; edge cases documented |
| R7 | Message/reasoning fields truncate unexpectedly | LOW | MEDIUM | Spec defines max lengths (<300/<500 chars); tests validate length; implementation may need truncation logic |
| R8 | Band assignment logic is off-by-one (e.g., score 6 → WARN instead of ESCALATE) | LOW | HIGH | Spec freezes hard thresholds (2, 5, 6); tests include boundary vectors (TV-16–TV-18); implementation must match exactly |

---

## Deferred Scope (M903+)

- **Signal weight tuning:** Per-project configuration via environment variables or configuration files (M903)
- **Orchestration and routing:** Which pipeline stages to run based on risk_score and band (M903)
- **Semantic extraction:** Generating focused review bundles for high-risk changes (M903 Stage 5)
- **Agent semantic review:** LLM/agent evaluation of extracted bundles (M903 Stage 6)
- **Risk trending:** Tracking risk_score changes over time, statistical analysis (M903 future)
- **Machine learning:** ML-based risk refinement or signal weighting (M903 future)

---

## Clarifying Questions

None. Scope and constraints are frozen per execution plan and checkpoint resolutions.

---

## Dependencies

| Dependency | Ticket | Status | Nature |
|---|---|---|---|
| M902-01 (Validation Gate Framework) | `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/01_validation_gate_framework.md` | COMPLETE | Hard (gate framework, registry, schema) |
| M902-09 (Stage 0 Diff Classification Gate) | `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/09_stage_0_diff_classification_gate.md` | COMPLETE | Soft (informs signal extraction patterns) |
| M902-10 (Stage 1 Formatting Gate) | `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/10_stage_1_formatting_and_restage_gate.md` | COMPLETE | Soft (informs gate structure) |
| M902-11 (Stage 3 Architecture Enforcement Gate) | `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/11_stage_3_architecture_enforcement_gate.md` | COMPLETE | Hard (violations input source) |
| code_governance.md Stage 4 section | `bot_vault/architecture/code_governance.md` | Reference | Soft (signal definitions, weight rationale) |

No blocking dependencies remain. M902-01, M902-09, M902-10, M902-11 are all COMPLETE.

---

## File Tree (Post-Implementation)

```
ci/scripts/
├── gates/
│   ├── __init__.py
│   └── risk_scoring_check.py                # Stage 4 Risk Scoring Gate (NEW)
└── gate_registry.json                       # Updated with risk_scoring_check entry

project_board/
├── specs/
│   └── 902_12_risk_scoring_spec.md          # This spec file
└── checkpoints/
    └── M902-12/
        └── 2026-05-19T-specification.md     # Spec checkpoint log (THIS RUN)

tests/ci/
├── test_risk_scoring_check.py               # Behavioral test suite (Task 2)
└── test_risk_scoring_check_adversarial.py   # Adversarial test suite (Task 3)
```

---

## Spec Completeness Checklist

- [x] Overview section explains gate purpose and governance pipeline stage
- [x] Requirement 01: Gate module, registry entry, importability, function signature
- [x] Requirement 02: Signal catalog (8 signals, weights, rule_id prefixes, scoring formula, extraction rules)
- [x] Requirement 03: Scoring bands (3 bands, hard thresholds, classification logic)
- [x] Requirement 04: Output contract (15 required fields, schema, message/reasoning templates)
- [x] Requirement 05: Test vector coverage (33 vectors across all risk categories, boundaries, edges, determinism, NFR, schema)
- [x] Non-functional requirements defined (performance, reliability, maintainability, observability, security)
- [x] Risk register with 8 identified risks and mitigations
- [x] Dependencies enumerated (hard: M902-01/M902-11; soft: M902-09/M902-10; all COMPLETE)
- [x] Clarifying questions resolved via checkpoint protocol (8 Qs answered with confidence rationale)
- [x] Deferred scope explicitly listed (M903+: weight tuning, orchestration, semantic extraction, agent review, trending, ML)
- [x] All 7 ticket ACs mapped to requirements and test vectors
- [x] Assumptions stated explicitly (violations conform to M902-01, rule_id prefixes are deterministic, weights immutable, shadow mode always PASS)
- [x] No ambiguities remain (all design decisions frozen in spec and checkpoint log)
- [x] File tree and output structure specified
- [x] No gameplay changes (governance tooling only)
- [x] No new dependencies introduced (pure Python stdlib)
- [x] Spec is deterministic and actionable by Test Designer and Implementation agents

**SPECIFICATION FROZEN AND READY FOR TEST_DESIGN.**

