# M902-14 Specification: Stage 6 — Agent Semantic Review Layer

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/14_stage_6_agent_semantic_review_layer.md`  
**Version:** 1.0 FROZEN  
**Status:** SPECIFICATION  
**Date:** 2026-05-19  
**Spec Agent:** Autonomous (Checkpoint Protocol)

---

## Overview

This specification defines **Stage 6 of the 8-stage governance pipeline: Agent Semantic Review Layer**. The gate receives focused semantic bundles extracted by Stage 5 (M902-13) and evaluates them using deterministic rule-based agent logic to render APPROVE/WARN/REJECT decisions. The agent evaluates 8 key signals derived from code_governance.md Stage 6 (SRP correctness, abstraction justification, hierarchy correctness, ownership clarity, observability completeness, async safety, exception handling, suppression justification) and outputs structured JSON with decision, confidence score (0.0–1.0), reasoning, and violations. The gate integrates into the M902-01 validation framework as a callable gate and returns result JSON conforming to the gate success schema. The gate is **non-blocking shadow mode by default**; actual routing decisions (APPROVE → Stage 7, WARN → log + proceed, REJECT → escalate) are deferred to M903 orchestrator.

**Key Constraints:**
- Agent receives only JSON bundle (no repo, git, or filesystem context)
- Decision logic is deterministic: same bundle → same JSON output (byte-for-byte)
- Evaluation against code_governance.md Stage 6 rules (8 signals frozen)
- Input contract frozen to M902-13 bundle v1.0 schema (20+ fields)
- Non-blocking advisory gate (shadow mode); orchestration deferred to M903
- Performance target: <2 seconds per bundle; gate overhead <500ms

---

## Requirement 01: Agent Module & Gate Integration

### 1. Spec Summary

**Description:** Implement two Python modules:

**(a) Agent Module** at `ci/scripts/agents/semantic_reviewer.py` (~200 LOC):
- Exports function `evaluate_bundle(bundle: dict) -> dict`
- Accepts M902-13 bundle JSON (v1.0 schema, 20+ fields)
- Validates input schema; malformed bundles trigger graceful degradation (skip validation, log WARNING, continue with best-effort evaluation)
- Evaluates 8 signals from code_governance Stage 6 (see Requirement 02 for signal definitions)
- Scores confidence per signal and overall (heuristic weights, see Requirement 03)
- Determines decision (approve/warn/reject) via priority cascade (Requirement 03)
- Generates reasoning (1–3 sentences per signal, max 500 chars total)
- Compiles violations array (applicable for warn/reject decisions)
- Computes evaluated_signals array (metadata of which signals were evaluated)
- Returns JSON dict: `{decision, confidence, reasoning, violations, evaluated_signals}`
- Module implements SRP: 8 signal evaluation functions (one per signal) are modular, each with single responsibility
- Exception handling follows code_governance.md (no bare except, all logged with context, re-raised or transformed)
- Determinism enforced: same bundle input → identical JSON output; no timestamps in decision logic; JSON output sorted keys

**(b) Gate Wrapper** at `ci/scripts/gates/agent_review_check.py` (~100 LOC):
- Exports function `run(inputs: dict) -> dict`
- Reads bundle path from inputs (either explicit path or from `.semantic_reviews/<issue_id>.json` default)
- Loads bundle JSON; handles missing/unreadable files gracefully (log ERROR, set decision="error", exit gracefully)
- Calls `evaluate_bundle()` with loaded bundle
- Transforms agent output to gate success schema (M902-01: status, gate, timestamp, ticket_id, message, violations, artifacts, duration_ms)
- Adds agent-specific fields: `decision` (approve/warn/reject), `confidence` (0.0–1.0), `agent_decision_reasoning` (reasoning string)
- Returns result dict matching M902-01 gate schema extended with agent fields
- Registers gate in `ci/scripts/gate_registry.json` with entry:
  ```json
  {
    "name": "agent_review_check",
    "module": "ci.scripts.gates.agent_review_check",
    "run_function": "run",
    "required_inputs": [],
    "optional_inputs": ["bundle_path", "issue_id"],
    "default_mode": "shadow",
    "description": "Evaluates semantic bundles (code, imports, ownership, violations) using rule-based agent logic; renders approve/warn/reject decision with confidence score"
  }
  ```

**Constraints:**
- Both modules must be importable as `ci.scripts.agents.semantic_reviewer` and `ci.scripts.gates.agent_review_check` without errors
- Both modules must validate their outputs conform to schemas (Requirement 03 for agent output, M902-01 for gate output)
- No external dependencies beyond Python stdlib (json, logging, pathlib, typing)
- No bare `except:` blocks; all exceptions logged with context, re-raised or transformed
- Bundle validation errors → log WARNING, continue with evaluation (degrade gracefully, not fail)
- Determinism: same bundle input → identical JSON (no dict ordering issues, no randomness)
- Performance: agent <2 seconds per bundle; gate overhead <500ms

**Assumptions:**
- M902-13 bundle v1.0 schema is stable (no changes during M902-14 implementation)
- M902-01 gate success schema is authoritative (gate output must conform)
- code_governance.md Stage 6 rules are source of truth for signal definitions
- Agent SDK (or callable Python function pattern) supports importable function interface
- Violation input from prior gates (M902-11, M902-12) conforms to M902-01 violations array schema

**Scope:**
- Agent module implementation, gate wrapper, and gate registry entry only
- Downstream orchestration (routing based on decision, agent scheduling, feedback loops) deferred to M903
- Agent instruction sets in `agent_context/agents/` (if directory structure differs) clarified post-implementation

### 2. Acceptance Criteria

1. **Agent module exists at correct path:** `ci/scripts/agents/semantic_reviewer.py` is present, syntactically valid Python, importable without errors, no dependencies beyond stdlib
2. **Agent function signature:** Exports `evaluate_bundle(bundle: dict) -> dict` where bundle is M902-13 v1.0 schema JSON, returns dict with fields: `decision` (string: approve/warn/reject), `confidence` (float: [0.0–1.0]), `reasoning` (string: 1–3 sentences, ≤500 chars), `violations` (array), `evaluated_signals` (array of signal names evaluated)
3. **Gate wrapper exists at correct path:** `ci/scripts/gates/agent_review_check.py` is present, syntactically valid Python, importable without errors
4. **Gate function signature:** Exports `run(inputs: dict) -> dict` matching M902-01 gate framework contract; optional inputs bundle_path or issue_id; returns M902-01 gate success schema + agent fields (decision, confidence, agent_decision_reasoning)
5. **Gate registry entry:** Gate registered in `ci/scripts/gate_registry.json` with all required fields (name, module, run_function, required_inputs, optional_inputs, default_mode, description); no syntax errors in JSON
6. **Exit codes:** Gate always exits 0 (shadow mode, non-blocking); status always "PASS" regardless of decision outcome
7. **Exception handling:** No bare `except:` or silent swallowing; all exceptions logged with context (file, function, line, message) and either re-raised or transformed to violations; bundle validation errors → WARNING, continue (graceful degradation)
8. **Determinism:** Same bundle input → identical JSON output (byte-for-byte after json.dumps with sort_keys=True); no timestamps in decision logic; all arrays sorted deterministically
9. **SRP boundary clear:** 8 signal evaluation functions separated (one per signal) or clearly demarcated; no cross-domain logic bleed; naming matches signal types

### 3. Risk & Ambiguity Analysis

**Risks:**

- **Agent logic too complex (8 signals hard to weigh jointly):** Risk: Decision cascade may not capture all signal interactions. Mitigation: Spec freezes decision priority (reject if critical signal, else warn if ambiguous, else approve); signal evaluation is independent, not weighted combinatorially. Tests validate priority cascade with multi-signal bundles.

- **Bundle schema mismatch with M902-13:** Risk: Agent fails to parse bundles if schema changes. Mitigation: Spec references M902-13 bundle v1.0 schema explicitly; input contract frozen in Requirement 02; test fixtures use M902-13 schema; agent validates schema before evaluation.

- **Non-deterministic output (LLM-based sampling):** Risk: Same bundle produces different decisions/confidences. Mitigation: Spec requires rule-based logic, not LLM sampling; no randomness in signal evaluation; tests validate idempotence (run twice, same output).

- **Agent sees full repo context (violates AC-7):** Risk: Agent makes decisions based on context outside bundle. Mitigation: Input contract spec: bundle JSON only; agent has no file/git/repo access; integration test validates bundle-only input (mock bundles, no filesystem).

- **Performance degradation (agent >2s per bundle):** Risk: Gate becomes bottleneck in pipeline. Mitigation: Target <2s agent, <500ms gate overhead; stress test bundle (100+ violations) in adversarial suite; establish baseline in integration tests.

- **Bundle validation too strict (rejects valid bundles):** Risk: Agent fails on edge cases. Mitigation: Error handling degrades gracefully (skip validation, log WARNING, continue with best-effort evaluation).

**Ambiguities resolved (per checkpoint protocol):**

- **Q1: How to enforce determinism?** → A: Rule-based logic only, no randomness. Same bundle → same JSON (byte-for-byte). Tests validate idempotence.
- **Q2: How to resolve multi-signal conflicts?** → A: Decision priority cascade frozen in Requirement 03 (reject > warn > approve).
- **Q3: Agent SDK constraints?** → A: Spec requires importable Python function (`evaluate_bundle`); actual agent_context structure clarified post-implementation.
- **Q4: What to do with malformed bundles?** → A: Validate schema; if invalid, log WARNING, skip validation, continue with evaluation (graceful degradation).

### 4. Clarifying Questions

None. Scope and constraints frozen per execution plan and checkpoint protocol.

---

## Requirement 02: Bundle Evaluation Scope & Signal Definitions

### 1. Spec Summary

**Description:** The agent evaluates bundles on 8 independent signals derived from code_governance.md Stage 6 rules. Each signal is evaluated against bundle fields, producing a violation flag (present/absent) and contributing to decision logic (Requirement 03).

**8 Evaluation Signals (AUTHORITATIVE SOURCE: code_governance.md Stage 6, lines 308–323):**

| Signal ID | Signal Type | Bundle Source | Rule Definition | Evaluation Logic |
|---|---|---|---|---|
| S1 | SRP correctness | `code_hunks`, `violations_summary`, `import_graph.affected_modules` | Single-responsibility principle (SRP): each module has one reason to change; no multi-role classes; composition over inheritance | Scan violations_summary for violations with rule_ids matching SRP patterns (AR-01–AR-06, MUT-01/02); if present, flag violation. Acceptable: one clear responsibility per module. |
| S2 | Abstraction justification | `code_hunks`, `import_graph.affected_modules` | Abstraction must reduce complexity, not add it; no unnecessary inheritance depth; no empty wrapper classes; no fake abstraction layers | Scan code_hunks for abstract classes/interfaces with no concrete subclasses or with single subclass (unnecessary). Scan for inheritance depth >3 levels. Flag if found. |
| S3 | Hierarchy correctness | `import_graph` (cycles, depth) | No circular imports; proper layering; no cross-layer imports; dependency direction enforced | Scan import_graph.cycles_detected flag. Check import_graph for cross-layer patterns (e.g., domain → infrastructure). Flag if cycles present OR cross-layer imports detected. |
| S4 | Ownership clarity | `ownership.assignments`, `import_graph.affected_modules` | Data ownership explicit; mutation boundaries clear; DTOs have single owner; no implicit cross-layer state mutation | Scan ownership.assignments; if any file missing owner OR ownership conflicts (same file, multiple owners), flag. Check if ownership source is heuristic (less confident than CODEOWNERS). |
| S5 | Observability completeness | `violations_summary`, `code_hunks` | Structured logging required; correlation/request IDs required; no raw logger usage; audit events required for critical flows; trace propagation required | Scan violations_summary for violations with rule_ids matching observability patterns (OB-01–OB-03). If present and affecting code_hunks, flag violation. |
| S6 | Async safety | `violations_summary`, `code_hunks` | No blocking calls in async context; no unbounded task spawning; proper cancellation handling required | Scan violations_summary for violations with rule_ids matching async patterns (AS-01–AS-04). If present, **CRITICAL FLAG** (high-risk signal). Async violations are runtime hazards; escalate immediately. |
| S7 | Exception handling | `violations_summary`, `code_hunks` | No bare except blocks; no silent failures; all exceptions must propagate, transform, observe+propagate, or explicit recovery | Scan violations_summary for violations with rule_ids matching exception patterns (EXH-01–EXH-04, or patterns in code_governance). If present, flag. |
| S8 | Suppression justification | `code_hunks` | Suppressions (blobert-ignore comments) must include justification, issue reference, optional expiration date | Scan code_hunks for `blobert-ignore`, `blobert-ignore-next-line` comments. For each, check if followed by justification comment (reason + ticket reference). If suppression without justification, flag violation. |

**Input Contract (Bundle Schema v1.0 Fields Required):**

The agent receives M902-13 bundle JSON with at minimum these fields (full schema in M902-13 spec):
- `version` (string): "1.0"
- `issue_id` (string): PR or ticket ID
- `code_hunks` (array): Code changes with line ranges and language
- `import_graph` (object): Dependency graph with cycles_detected flag, affected_modules
- `ownership` (object): File-to-owner assignments
- `violations_summary` (object): Violations from prior gates (M902-11, M902-12)
- `metadata` (object): Git state, extraction time, bundle metadata

Missing fields → log WARNING, assume empty/absent (graceful degradation).

**Signal Evaluation Rules (Deterministic, Independent):**

Each signal is evaluated independently:

1. **Parse bundle fields** relevant to signal (code_hunks, violations_summary, ownership, import_graph)
2. **Apply signal-specific rules** (see Evaluation Logic column above)
3. **Determine violation presence:** Flag present (1) or absent (0)
4. **No signal weighting:** Each signal is binary (violated / not violated); decision priority (Requirement 03) combines signals

**Signal Type Classification (for decision logic):**

- **CRITICAL signals:** Async safety (S6), Hierarchy correctness if cycles (S3)
  - If critical signal violated: decision → REJECT
- **MODERATE signals:** SRP (S1), Abstraction (S2), Exception handling (S7), Suppression unjustified (S8)
  - If multiple moderate signals violated: decision → WARN
- **LOW signals:** Ownership (S4), Observability (S5)
  - If present alone: decision → WARN (advisory)

**Constraints:**
- All signals must be evaluated independently (no joint weighting, no Bayesian combination)
- Signal evaluation uses only bundle fields (no external API, no repo access)
- Malformed violations in violations_summary → skip with WARN, continue evaluation
- Code hunk analysis is pattern-based (regex for blobert-ignore, imports, inheritance keywords)
- No AST parsing required (already done by prior gates)

**Assumptions:**
- Violations in violations_summary conform to M902-01 schema (rule_id, severity, message, file, line)
- Rule ID prefixes map to signal types per execution plan (AR-01–06 → SRP, AS-01–04 → async, etc.)
- Code_hunks text is raw (not parsed AST); pattern matching sufficient for blobert-ignore, inheritance detection

**Scope:**
- Signal evaluation rules only; downstream routing logic deferred to M903

### 2. Acceptance Criteria

1. **8 signals enumerated:** All 8 signal types defined with bundle source fields, rule definitions, and evaluation logic
2. **Signal evaluation independent:** Each signal evaluated in isolation; no joint weighting or Bayesian combination
3. **Critical signals identified:** Async (S6) and circular imports (S3) marked as critical; evaluation logic specifies rejection threshold
4. **Evaluation logic deterministic:** Same bundle → same signal flags (0 or 1 per signal); no randomness, no state
5. **Graceful degradation:** Missing bundle fields → log WARNING, assume empty (don't fail evaluation)
6. **Malformed violations skipped:** Violations missing rule_id or severity → skip with WARN, continue
7. **Code hunk pattern matching:** blobert-ignore detection via regex; inheritance depth via regex/keyword search; no AST parsing required
8. **Input contract specified:** Bundle v1.0 schema fields documented; required vs optional fields enumerated

### 3. Risk & Ambiguity Analysis

**Risks:**

- **Signal evaluation incomplete:** If bundle fields are sparse or malformed, some signals may not evaluate correctly. Mitigation: Spec defines fallback behavior (assume empty field, flag as unknown, continue). Tests validate edge cases (missing fields, empty arrays).

- **Rule ID mapping ambiguity:** If prior gates use unexpected rule_id prefixes, signal mapping fails. Mitigation: Spec references execution plan rule_id catalog (AR-01–06, AS-01–04, OB-01–03, etc.); unknown prefixes treated as unknown signal (not error).

- **Inheritance depth heuristic unreliable:** Regex-based detection may miss deep chains or misidentify. Mitigation: Heuristic is best-effort (code_hunks contain relevant code for review); tests validate with realistic patterns.

- **Suppression detection false positives:** If blobert-ignore appears in strings or comments unrelated to code governance, misidentification occurs. Mitigation: Pattern match `blobert-ignore` in comments only (crude but conservative); tests verify pattern accuracy.

**Ambiguities resolved:**

- **Q1: What if bundle lacks violations_summary?** → A: Assume no violations (empty array). Signal evaluation proceeds with available fields.
- **Q2: How to handle unknown rule_id prefixes?** → A: Treat as unknown signal (flag at DEBUG level, don't fail).
- **Q3: Inheritance depth threshold (when is depth "too deep")?** → A: >3 levels is excessive (heuristic from code_governance); spec uses this baseline.

### 4. Clarifying Questions

None. Signal definitions frozen per code_governance Stage 6 and execution plan Requirement 02.

---

## Requirement 03: Agent Output Contract & Decision Logic

### 1. Spec Summary

**Description:** The agent returns a JSON dict with decision, confidence score, reasoning, violations, and evaluated_signals metadata.

**Agent Output JSON Schema (AUTHORITATIVE):**

```json
{
  "decision": "approve|warn|reject",
  "confidence": 0.0,
  "reasoning": "...",
  "violations": [],
  "evaluated_signals": []
}
```

**Field Definitions:**

| Field | Type | Constraints | Description |
|---|---|---|---|
| `decision` | string (enum) | One of: `"approve"`, `"warn"`, `"reject"` | Decision outcome determined by signal evaluation and priority cascade (see Decision Logic below) |
| `confidence` | float | [0.0, 1.0] (inclusive), rounded to 2 decimal places | Confidence score reflecting certainty in decision. Computed via heuristic weights per signal flags; clamped to [0.0, 1.0] |
| `reasoning` | string | ≤500 characters, non-empty | Human-readable explanation (1–3 sentences). Summarizes which signals triggered decision and reasoning per signal. |
| `violations` | array of objects | Non-empty for warn/reject; empty for approve | Violations relevant to decision (subset of violations_summary filtered by applicable signals). See Violation Object schema below. |
| `evaluated_signals` | array of objects | Non-empty; one entry per evaluated signal | Metadata: which signals were evaluated, presence flags, confidence per signal. See Evaluated Signal Object schema below. |

**Violation Object Schema (Subset of M902-01):**

```json
{
  "rule_id": "AS-01",
  "severity": "CRITICAL|ERROR|WARN|INFO",
  "message": "Blocking I/O in async context",
  "file": "model_registry/service.py",
  "line": 50,
  "signal": "async_safety"
}
```

| Field | Type | Description |
|---|---|---|
| `rule_id` | string | Rule identifier (e.g., "AS-01", "SRP-01") |
| `severity` | string | One of: `"CRITICAL"`, `"ERROR"`, `"WARN"`, `"INFO"` |
| `message` | string | Violation description (from violations_summary) |
| `file` | string | File path (optional from violations_summary) |
| `line` | integer | Line number (optional from violations_summary) |
| `signal` | string | Signal type this violation belongs to (S1–S8 names) |

**Evaluated Signal Object Schema:**

```json
{
  "signal_name": "async_safety",
  "signal_id": "S6",
  "violation_present": true,
  "confidence": 0.9,
  "reasoning": "Async context violations detected"
}
```

| Field | Type | Description |
|---|---|---|
| `signal_name` | string | Signal type name (e.g., "async_safety", "srp_correctness") |
| `signal_id` | string | Signal ID (S1–S8) |
| `violation_present` | boolean | True if signal evaluation found violations |
| `confidence` | float | [0.0, 1.0] Confidence in this signal's evaluation (e.g., 0.9 if clear, 0.6 if ambiguous) |
| `reasoning` | string | Brief explanation of signal evaluation result |

**Decision Logic (Deterministic Priority Cascade):**

```python
# Evaluate all 8 signals (S1–S8) independently
signal_flags = {
    "S1_srp": evaluate_signal_1(bundle),
    "S2_abstraction": evaluate_signal_2(bundle),
    "S3_hierarchy": evaluate_signal_3(bundle),
    "S4_ownership": evaluate_signal_4(bundle),
    "S5_observability": evaluate_signal_5(bundle),
    "S6_async": evaluate_signal_6(bundle),
    "S7_exception": evaluate_signal_7(bundle),
    "S8_suppression": evaluate_signal_8(bundle)
}

# REJECT if any CRITICAL signal violated
if signal_flags["S6_async"] or (signal_flags["S3_hierarchy"] and cycles_detected):
    decision = "reject"
    confidence = 0.95 - (0.15 * count_critical_violations)

# WARN if multiple MODERATE signals violated OR suppression unjustified
elif (signal_flags["S1_srp"] + signal_flags["S2_abstraction"] + 
      signal_flags["S7_exception"] + signal_flags["S8_suppression"]) >= 2:
    decision = "warn"
    confidence = 0.65 - (0.10 * count_moderate_violations)

# WARN if LOW signals present (observability, ownership ambiguity)
elif signal_flags["S4_ownership"] or signal_flags["S5_observability"]:
    decision = "warn"
    confidence = 0.75 - (0.05 * (signal_flags["S4_ownership"] + signal_flags["S5_observability"]))

# APPROVE if no critical signals and ≤1 moderate signal
else:
    decision = "approve"
    confidence = 0.85 + (0.05 * num_owned_modules)  # bonus for clear ownership
```

**Confidence Scoring (Heuristic Weights):**

- **Start:** 0.75 (baseline, moderate confidence)
- **Per critical signal violation:** -0.25 (high impact)
- **Per moderate signal violation:** -0.10 (medium impact)
- **Per low signal violation:** -0.05 (advisory impact)
- **Clear ownership assignment (all files owned):** +0.05
- **Clamp:** Result to [0.0, 1.0]; round to 2 decimal places

**Example Confidence Calculations:**

| Scenario | Signals | Calculation | Confidence |
|---|---|---|---|
| Clean bundle (no violations) | None | 0.75 + 0.05 (ownership) = 0.80 | 0.80 |
| One SRP violation (S1) | S1 | 0.75 - 0.10 (S1) = 0.65 | 0.65 |
| Async + SRP violations (S6, S1) | S6 + S1 | 0.75 - 0.25 (S6 critical) - 0.10 (S1) = 0.40 | 0.40 |
| Circular import (S3 critical) | S3 | 0.75 - 0.25 (S3 critical) = 0.50 | 0.50 |

**Reasoning Composition:**

Reasoning string must be 1–3 sentences summarizing decision and key signals:

- **APPROVE:** "Bundle passes semantic review. No critical signals detected; ownership is clear and observability requirements met."
- **WARN:** "Bundle has moderate concerns. Multiple SRP violations and missing audit logging detected. Review recommended before merge."
- **REJECT:** "Bundle requires redesign. Async safety violations detected in critical path. Blocking I/O must be refactored to async before proceeding."

**Constraints:**
- All fields must be JSON-serializable (no custom types, no NaN/Infinity)
- `decision` must be exactly one of the three enum values (case-sensitive lowercase)
- `confidence` must be finite float in [0.0, 1.0]; rounded to 2 decimal places
- `violations` array must be sorted by severity (CRITICAL > ERROR > WARN > INFO)
- `evaluated_signals` array must be sorted by signal_id (S1 → S8)
- Output must be deterministic: same bundle → identical JSON (byte-for-byte after json.dumps with sort_keys=True)

**Assumptions:**
- All 8 signals are evaluated (even if violations_summary is sparse, evaluation proceeds with absent flags)
- Confidence is heuristic (project-specific tuning deferred to M903)
- Decision priority is frozen (reject > warn > approve); no alternative models in scope

**Scope:**
- Output contract and decision logic only; downstream routing (M903 orchestrator) is deferred

### 2. Acceptance Criteria

1. **Output schema complete:** All 5 top-level fields (decision, confidence, reasoning, violations, evaluated_signals) with correct types and constraints
2. **Decision enum frozen:** Exactly 3 values (approve, warn, reject); case-sensitive lowercase
3. **Confidence bounds enforced:** [0.0, 1.0] inclusive; rounded to 2 decimal places; no NaN/Infinity
4. **Reasoning non-empty:** 1–3 sentences; ≤500 characters; describes decision rationale
5. **Violations array structured:** Violation objects with required fields (rule_id, severity, message, signal); sorted by severity
6. **Evaluated signals metadata:** One object per signal (S1–S8) with violation_present flag, confidence, reasoning
7. **Decision logic deterministic:** Frozen priority cascade (reject > warn > approve); same bundle → same decision
8. **Confidence scoring heuristic frozen:** Starting baseline 0.75, signal weights frozen (-0.25 critical, -0.10 moderate, -0.05 low, +0.05 ownership); examples demonstrate calculation
9. **JSON serialization deterministic:** sorted keys, no timestamps, same output byte-for-byte on repeated runs
10. **All example decisions documented:** At least 3 worked examples (approve, warn, reject) with confidence calculations

### 3. Risk & Ambiguity Analysis

**Risks:**

- **Confidence score too high/low:** Heuristic weights may not reflect actual decision quality. Mitigation: Spec freezes weights per execution plan; M903 can tune via configuration; tests validate confidence bounds with edge cases.

- **Decision priority conflicts:** If multiple critical signals present, priority cascade unclear. Mitigation: Spec specifies explicit cascade (if any critical → reject; if multiple moderate → warn; if low → warn; else → approve). Tests validate with multi-violation bundles.

- **Reasoning string vague or uninformative:** If reasoning doesn't explain decision clearly, downstream use impaired. Mitigation: Spec prescribes reasoning structure (1–3 sentences, which signals triggered, why). Tests validate reasoning non-empty and informative.

- **Violated signals not included in violations array:** If violations array misses applicable violations, decision transparency degraded. Mitigation: Implementation must filter violations_summary to include only violations affecting decision signals.

**Ambiguities resolved:**

- **Q1: What if multiple signals conflict?** → A: Priority cascade frozen; reject if critical, else warn if moderate, else approve. Deterministic.
- **Q2: How to compute confidence with no violations?** → A: Baseline 0.75–0.85 (high confidence in clean code). No violations → no penalties. Bonus for clear ownership.
- **Q3: How detailed should reasoning be?** → A: 1–3 sentences max 500 chars. Describe decision and key signals; avoid vagueness.

### 4. Clarifying Questions

None. Output contract and decision logic frozen per execution plan and checkpoint protocol.

---

## Requirement 04: Gate Integration with M902-01 Framework

### 1. Spec Summary

**Description:** The agent module outputs a dict. The gate wrapper (`agent_review_check.py`) transforms agent output to conform to the M902-01 gate success schema and registers the gate in `gate_registry.json`.

**M902-01 Gate Success Schema Extension (with Agent Fields):**

```json
{
  "version": "1.0",
  "status": "PASS",
  "gate": "agent_review_check",
  "timestamp": "2026-05-19T10:30:00Z",
  "ticket_id": "M902-14",
  "upstream_agent": "semantic_extraction_check",
  "downstream_agent": "orchestrator",
  "message": "Agent semantic review complete. Decision: approve. Confidence: 0.85.",
  "violations": [],
  "artifacts": [{"path": "some-artifact-path", "sha256": "..."}],
  "duration_ms": 1250,
  "mode": "shadow",
  "decision": "approve",
  "confidence": 0.85,
  "agent_decision_reasoning": "Bundle passes semantic review. No critical signals detected."
}
```

**Field Mapping:**

| Field | Source | Mapping |
|---|---|---|
| `version` | M902-01 schema | "1.0" (frozen) |
| `status` | M902-01 schema | Always "PASS" (shadow mode) |
| `gate` | M902-01 schema | "agent_review_check" (gate name) |
| `timestamp` | M902-01 schema | ISO 8601 UTC (generated by gate runner) |
| `ticket_id` | inputs dict | From inputs or environment |
| `upstream_agent` | inputs dict | From inputs (e.g., "semantic_extraction_check") |
| `downstream_agent` | inputs dict | From inputs (e.g., "orchestrator", "M903-override-system") |
| `message` | agent output | Synthesized from decision + confidence + reasoning (max 500 chars) |
| `violations` | agent output | From agent output violations array (filtered by applicable signals) |
| `artifacts` | optional | Bundle path if stored; include bundle JSON path if available |
| `duration_ms` | gate wrapper | Elapsed time from bundle load to decision return (agent + overhead) |
| `mode` | M902-01 schema | "shadow" (default_mode in registry) |
| `decision` | agent output | From agent output decision (approve/warn/reject) |
| `confidence` | agent output | From agent output confidence (0.0–1.0) |
| `agent_decision_reasoning` | agent output | From agent output reasoning (full text, ≤500 chars) |

**Gate Success Schema (M902-01 Reference):**

The gate output must conform to the M902-01 gate success schema (ticket `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/01_validation_gate_framework.md`, Requirement 02). The schema includes:
- `version` (string): "1.0"
- `status` (string): "PASS"
- `gate` (string): Gate name
- `timestamp` (string): ISO 8601 UTC
- `ticket_id` (string): Ticket identifier
- `upstream_agent` (string): Prior agent (M902-13)
- `downstream_agent` (string): Next agent (M903 orchestrator)
- `message` (string): Human-readable summary
- `violations` (array): Any violations (structured per M902-01 schema)
- `artifacts` (array): Output artifacts (file paths with SHA-256)
- `duration_ms` (integer): Elapsed time milliseconds
- `mode` (string): "shadow" or "blocking" (shadow default)

**Gate Registry Entry (M902-01 Reference):**

The gate must be registered in `ci/scripts/gate_registry.json`:

```json
{
  "name": "agent_review_check",
  "module": "ci.scripts.gates.agent_review_check",
  "run_function": "run",
  "required_inputs": [],
  "optional_inputs": ["bundle_path", "issue_id", "upstream_agent", "downstream_agent", "mode"],
  "default_mode": "shadow",
  "category": "governance",
  "description": "Evaluates semantic bundles (code, imports, ownership, violations) using rule-based agent logic; renders approve/warn/reject decision with confidence score"
}
```

**Gate Input Contract:**

The gate receives `inputs` dict with optional fields:
- `bundle_path` (string): Explicit path to bundle JSON; if omitted, defaults to `.semantic_reviews/<issue_id>.json`
- `issue_id` (string): Issue/PR identifier; used to construct default bundle path if bundle_path not provided
- `upstream_agent` (string): Prior agent name (e.g., "semantic_extraction_check")
- `downstream_agent` (string): Next agent name (e.g., "orchestrator")
- `mode` (string): "shadow" or "blocking" (from gate runner `--mode` flag)
- Other M902-01 handoff fields (ticket_id, etc.)

**Gate Output Contract:**

The gate returns a dict with all M902-01 gate success schema fields plus agent-specific fields:
- All M902-01 success schema fields (version, status, gate, timestamp, ticket_id, upstream_agent, downstream_agent, message, violations, artifacts, duration_ms, mode)
- Agent-specific fields: `decision`, `confidence`, `agent_decision_reasoning`

**Constraints:**
- Gate must validate output conforms to M902-01 schema before returning
- All timestamps must be ISO 8601 UTC format
- `duration_ms` must include bundle load, agent evaluation, and gate transform time
- `violations` array must match M902-01 violation object schema (rule_id, severity, message, file, line optional)
- `artifacts` array should include bundle path and any diagnostic outputs
- Exit code: always 0 (shadow mode, non-blocking per M902-01 Requirement 05)

**Assumptions:**
- M902-01 gate success schema is authoritative (gate output must conform exactly)
- M902-01 gate runner is responsible for calling gate and handling exit codes (gate module returns dict only)
- Downstream orchestrator (M903) will parse agent output fields and use decision/confidence for routing
- Bundle path defaults to `.semantic_reviews/<issue_id>.json` if not specified

**Scope:**
- Gate integration with M902-01 framework only; actual routing decisions deferred to M903

### 2. Acceptance Criteria

1. **Gate returns M902-01 schema:** Output dict includes all required fields (version, status, gate, timestamp, ticket_id, upstream_agent, downstream_agent, message, violations, artifacts, duration_ms, mode)
2. **Agent-specific fields added:** `decision`, `confidence`, `agent_decision_reasoning` fields present in output
3. **Status always PASS:** status field always "PASS" (shadow mode, non-blocking)
4. **Duration measured:** `duration_ms` field includes total elapsed time (load + evaluate + transform) in milliseconds
5. **Violations transformed:** Agent violations array transformed to M902-01 violation object format (rule_id, severity, message, file, line, signal)
6. **Artifacts recorded:** Bundle path and any diagnostics included in artifacts array with SHA-256 hashes
7. **Registry entry present:** Gate registered in `ci/scripts/gate_registry.json` with all required fields; JSON valid
8. **Integration test validates schema:** Test loads gate output, validates all required fields present, types correct, enums valid (decision, severity, etc.)

### 3. Risk & Ambiguity Analysis

**Risks:**

- **Schema version mismatch:** If M902-01 schema changes, gate output may become incompatible. Mitigation: Version field is frozen ("1.0"); future schema changes require version bump; spec requires exact conformance to M902-01 v1.0.

- **Gate registry becomes stale:** If module path changes post-implementation, registry entry becomes invalid. Mitigation: Integration test validates registry entry resolves to actual module file; test runs at CI time.

- **Orchestrator expects different field names:** If downstream expects decision_outcome instead of decision, routing fails. Mitigation: Spec freezes field names per execution plan; integration test validates gate output can be consumed by mock orchestrator.

**Ambiguities resolved:**

- **Q1: Should gate validate bundle schema?** → A: Agent module validates; gate wrapper loads and transforms. Validation errors handled by agent module (log WARNING, continue).
- **Q2: Where does bundle path come from?** → A: Explicit inputs.bundle_path or default `.semantic_reviews/<issue_id>.json`.

### 4. Clarifying Questions

None. Integration contract with M902-01 frozen per framework spec and execution plan.

---

## Requirement 05: Test Vector Coverage & Determinism Validation

### 1. Spec Summary

**Description:** The agent implementation must pass 90+ test vectors covering all 8 signals, decision outcomes, confidence bounds, edge cases, and determinism validation.

**Test Vector Categories (35+ total, per execution plan):**

| Category | Count | Coverage | Examples |
|---|---|---|---|
| **Signal Evaluation (8×5)** | 40 | All 8 signals individually + combinations | test_srp_single_responsibility_approved, test_async_blocking_call_rejected, test_abstraction_unnecessary_warned |
| **Decision Outcomes** | 6 | approve, warn, reject with high/low confidence | test_clean_bundle_approve_high_confidence, test_multiple_violations_warn, test_critical_async_reject |
| **Confidence Bounds** | 4 | Thresholds [0.0, 0.5, 1.0] | test_confidence_zero_critical_violation, test_confidence_1_0_clean_bundle |
| **Bundle Variations** | 8 | Clean, with violations, edge cases | test_empty_violations_summary, test_malformed_bundle_graceful_degradation |
| **Determinism** | 4 | Same bundle twice, order independence | test_idempotence_same_bundle_twice, test_violations_order_independence |
| **Suppression Edge Cases** | 4 | Justified, unjustified, expired dates | test_suppression_justified_allowed, test_suppression_no_justification_flagged |
| **Performance** | 3 | Baseline, stress (100+ violations), large code hunks | test_performance_baseline_under_2s, test_stress_large_bundle |
| **Error Handling** | 6 | Missing fields, malformed violations, decode errors | test_malformed_violation_rule_id_skip, test_missing_code_hunks_log_warning |
| **Schema Compliance** | 3 | Output valid JSON, all fields present, types correct | test_output_schema_valid_json, test_confidence_never_negative |
| **Cross-Signal** | 6 | Multiple violations, decision priority, confidence interactions | test_async_and_srp_reject_priority, test_multiple_moderate_warn_combined |

**Total: 90+ test vectors (50 behavioral + 40 adversarial per execution plan)**

**Test File Organization:**

- **Behavioral Tests:** `tests/ci/test_semantic_reviewer_agent.py` (50+ tests)
  - Organized by signal type (8 groups, 5+ tests each)
  - Each test validates: decision, confidence, reasoning, violations structure
  - Test names self-documenting (e.g., `test_srp_single_responsibility_approved`)
  - Docstrings reference AC numbers and code_governance rule IDs

- **Adversarial Tests:** `tests/ci/test_semantic_reviewer_agent_adversarial.py` (40+ tests)
  - Parametrized tests for edge cases
  - Boundary conditions, malformed input, determinism emphasis
  - Checkpoint decisions logged for (1) determinism priority, (2) decision priority cascade, (3) confidence bounds, (4) suppression handling, (5) empty bundle behavior

- **Integration Tests:** `tests/ci/test_agent_review_integration.py` (3–5 tests)
  - E2E tests: bundle loading, gate wrapper invocation, schema compliance
  - Determinism validation (run twice, compare outputs)
  - Performance baseline
  - Gate registry validation

**Determinism Validation Strategy:**

All tests must validate that **same bundle input → identical JSON output**:

```python
# Test pseudo-code
bundle = load_test_bundle("clean_bundle.json")
result1 = evaluate_bundle(bundle)
result2 = evaluate_bundle(bundle)

assert json.dumps(result1, sort_keys=True) == json.dumps(result2, sort_keys=True)
```

**Test Fixtures:**

- M902-13 bundle v1.0 examples (JSON files under `tests/ci/fixtures/bundles/`)
- Mock bundles for edge cases (missing fields, malformed violations, empty arrays)
- Expected output fixtures (approved, warned, rejected bundles)

**Constraints:**
- All tests deterministic (no randomness, no mocking of agent internals, only bundle fixtures)
- Tests run in isolation (no cross-test state sharing)
- Performance assertions: agent <2s per bundle, gate overhead <500ms
- Coverage: all 8 signals, all 3 decision outcomes, confidence [0.0–1.0] range, edge cases

**Assumptions:**
- M902-13 bundle examples available (in checkpoints or can be mocked)
- Bundle schema v1.0 is stable (no changes during test design)
- pytest parametrize and fixtures are available (standard Python testing)

**Scope:**
- Test vector specification only; actual test implementation (Task 2) and breaking (Task 3) are separate tasks

### 2. Acceptance Criteria

1. **50+ behavioral tests present:** Test file `tests/ci/test_semantic_reviewer_agent.py` with 50+ passing tests (before implementation, expected failures OK)
2. **8 signal types covered:** Each signal type (S1–S8) has ≥5 dedicated tests validating signal evaluation
3. **Decision outcomes tested:** Tests validate all 3 decision types (approve, warn, reject) with varying violation patterns
4. **Confidence bounds tested:** Tests validate confidence [0.0, 1.0] with explicit boundary cases (0.0, 0.5, 1.0)
5. **Determinism validated:** Tests call agent twice with same bundle, compare JSON byte-for-byte (assert json.dumps equality)
6. **Edge cases covered:** Empty violations, malformed input, missing fields, large bundles, deep imports
7. **Test names self-documenting:** Test function names describe signal + scenario (e.g., `test_async_blocking_call_rejected`)
8. **Docstrings reference specs:** Each test docstring cites AC number and rule ID from code_governance.md or execution plan
9. **Fixtures organized:** Bundle fixtures under `tests/ci/fixtures/bundles/` with clear naming
10. **Coverage aligns with spec:** 35+ test vector categories mapped to 90+ test implementations

### 3. Risk & Ambiguity Analysis

**Risks:**

- **Test vectors too rigid (implementation can't satisfy):** Risk: Tests fail due to overly strict expectations. Mitigation: Spec freezes test vector categories and counts; tests define behavior, not implementation detail.

- **Determinism tests unreliable:** Risk: Floating-point rounding or dict ordering causes false failures. Mitigation: Tests use json.dumps with sort_keys=True; confidence rounded to 2 decimals; no timestamp logic.

- **Bundle fixtures incompatible with M902-13 schema:** Risk: Tests use stale schema. Mitigation: Spec references M902-13 v1.0 explicitly; fixtures validated against schema.

**Ambiguities resolved:**

- **Q1: What precision for confidence in tests?** → A: 2 decimal places (0.00–1.00); rounded, not raw floats.
- **Q2: How strict is determinism validation?** → A: Byte-for-byte JSON comparison after sort_keys=True serialization.

### 4. Clarifying Questions

None. Test coverage specification frozen per execution plan Task 2 and checkpoint protocol.

---

## Requirement 06: Edge Cases & Error Handling

### 1. Spec Summary

**Description:** The agent gracefully handles edge cases and errors per code_governance.md exception handling rules.

**Edge Cases (with Handling Strategy):**

| Edge Case | Scenario | Agent Behavior | Output Impact |
|---|---|---|---|
| **Empty bundle** | All sections empty (no violations, no code hunks, no imports) | Evaluate all 8 signals as "no violation" flags; high confidence in clean code | decision: "approve", confidence: 0.80–0.85 |
| **Minimal bundle** | Only required fields, all others empty/null | Gracefully degrade: skip validation on missing fields, evaluate available signals | decision: varies (depends on available data), confidence: lower (0.60–0.70 uncertainty) |
| **Malformed violations_summary** | Violations array with missing rule_id, invalid severity | Skip malformed violation with WARN log message; continue evaluation with remaining violations | No error; continue evaluation; log "Skipped malformed violation at index 3" |
| **Unknown rule_id prefix** | Violations with rule_id not in known prefixes (AR-01, AS-01, etc.) | Treat as unknown signal (not error); log at DEBUG level; don't add signal flag | Continue evaluation; unknown violations ignored in signal scoring |
| **Missing code_hunks** | code_hunks array empty or absent | Assume no code changes to analyze; skip code-based signal evaluation (abstraction, suppression checks) | Confidence lower for relevant signals; other signals still evaluated |
| **Circular import cycles** | import_graph.cycles_detected = true | Flag S3 (hierarchy) as CRITICAL violation; trigger REJECT decision | decision: "reject", confidence: 0.50–0.60 (moderate certainty in cycle risk) |
| **Ownership conflicts** | Same file appears in ownership.assignments twice with different owners | Flag S4 (ownership) as violation; consider ownership ambiguous | decision: may shift to "warn" if single conflict, "reject" if multiple |
| **Very large bundle** | Bundle >100KB (from M902-13 truncation) | Evaluate normally (no size constraints on agent); metadata indicates truncation | decision unaffected; confidence may be slightly lower due to missing context |
| **Suppression without justification** | blobert-ignore comment present but no reason/ticket reference | Flag S8 (suppression) violation; add to violations array | decision shifts to "warn" if sole violation, contributes to "reject" if combined with critical |
| **Code hunk with invalid UTF-8** | Binary data or decode errors in code_hunks text | Skip problematic hunk with WARN log; continue evaluation with other hunks | No error; continue; log "Skipped code hunk at file X due to decode error" |
| **Missing ownership assignments** | ownership.assignments is empty (no CODEOWNERS, fallback failed) | Evaluate S4 normally but flag as "unable_to_verify"; confidence lower for ownership signal | decision may shift to "warn" (ownership ambiguous) |
| **Null/None values in bundle fields** | Bundle contains `null` for expected object/array fields | Treat null as empty (empty array, empty object); continue evaluation | No error; graceful degradation |
| **Malformed JSON in nested structures** | Violation object missing required fields (e.g., no message) | Skip with WARN; include in evaluation if some fields recoverable | Continue; log "Malformed violation missing field 'message'" |

**Exception Handling Rules (per code_governance.md):**

All exceptions in agent evaluation must follow one of these patterns:

1. **Propagate:** Re-raise original exception (fail fast)
2. **Transform:** Convert to domain-specific exception (e.g., `BundleValidationError`)
3. **Observe + propagate:** Log with context (file, function, line, message) + re-raise
4. **Explicit recovery:** Documented fallback with clear semantics (e.g., skip malformed violation, log WARNING, continue)

**Forbidden patterns:**
- `except:` (bare except)
- `except Exception: pass` (silent swallowing)
- Silent failures (return None, return False without explanation)
- Logging-only exception handling (log without propagation/transformation)

**Implementation constraints:**
- No bare `except:` blocks
- All exceptions logged with structured context (file, function, line, exception type, message)
- Malformed bundle fields → log WARNING, continue with available data (explicit recovery)
- Network/IO errors (bundle load failure) → log ERROR, transform to BundleLoadError, propagate (fail gate, but cleanly)
- Agent evaluation errors (signal evaluation exception) → log ERROR with full traceback, transform to EvaluationError, propagate

**Graceful Degradation Strategy:**

When bundle fields are missing, sparse, or malformed:

1. **Log severity:** Use appropriate log level (DEBUG for expected edge cases, INFO for warnings, ERROR for exceptions)
2. **Continue evaluation:** Don't fail entire evaluation due to one missing field
3. **Confidence adjustment:** Reduce confidence score proportionally to uncertainty (fewer signals evaluated → lower confidence)
4. **Document in violations:** If field absence affects decision, add a note to violations array explaining uncertainty

**Performance Constraints:**

- Agent must complete evaluation in <2 seconds per bundle, even with:
  - 100+ violations in violations_summary
  - 50+ modules in import_graph
  - 1000+ lines of code in code_hunks (truncated per M902-13)
- Stress test scenario: large bundle (100+ violations) → target <2s completion
- Gate wrapper overhead (load, transform, return) <500ms

**Constraints:**
- All edge cases must be handled without raising unhandled exceptions (fail gracefully)
- Error logs must be structured and queryable (include timestamp, severity, context, message)
- Evaluation must complete even with partial data (no cascading failures)

**Assumptions:**
- Bundle validation errors are expected (bundles may be sparse); not critical failures
- Bundle load errors (missing file) are critical and should propagate
- Signal evaluation never raises exceptions (all logic is pattern-based, not AST parsing)

**Scope:**
- Edge case handling and error strategies only; actual implementation logging patterns deferred to implementation task

### 2. Acceptance Criteria

1. **Edge cases enumerated:** All 13 edge cases documented with agent behavior and output impact
2. **No bare except blocks:** Code review confirms no `except:` or `except Exception: pass` patterns
3. **All exceptions logged:** Exception handling includes structured context (file, function, line, exception type)
4. **Graceful degradation:** Missing/malformed fields → log WARNING, continue evaluation; confidence adjusted accordingly
5. **Bundle validation errors don't cascade:** Single malformed field doesn't fail entire evaluation
6. **Confidence reflection:** Output confidence reflects data completeness (lower confidence if fewer signals evaluated)
7. **Performance acceptable:** Agent <2s per bundle; stress test (100+ violations) passes <2s SLA
8. **Edge case tests present:** Adversarial test suite (Task 3) includes ≥1 test per edge case category
9. **Error messages informative:** Logs include file, function, line, exception type, context (not generic "error occurred")

### 3. Risk & Ambiguity Analysis

**Risks:**

- **Graceful degradation too permissive:** If agent evaluates with too many missing fields, decision may be unreliable. Mitigation: Spec defines minimum required fields (code_hunks, violations_summary); if missing, agent should note in reasoning that evaluation was partial. Tests validate confidence reflects uncertainty.

- **Performance degradation with large bundles:** Stress test may timeout. Mitigation: Avoid O(n²) algorithms in signal evaluation (e.g., don't compare every violation against every module). Use set lookups for known rule_ids. Lazy evaluation (skip signals with missing fields early). Baseline established in integration tests.

- **Suppression heuristic unreliable:** Regex pattern for blobert-ignore may have false positives/negatives. Mitigation: Heuristic is best-effort; code_hunks already extracted by M902-13 so raw text is available; tests validate pattern accuracy with known examples.

**Ambiguities resolved:**

- **Q1: What's the minimum viable bundle?** → A: At minimum: `code_hunks` (non-empty array), `violations_summary` (may be empty). If both missing, agent should note "insufficient data for evaluation" in reasoning.
- **Q2: Should agent retry on transient errors (bundle load)?** → A: No. Retry logic is gate runner responsibility (M903 orchestration). Agent fails loudly if bundle can't be loaded.

### 4. Clarifying Questions

None. Edge case handling strategy frozen per code_governance.md and execution plan.

---

## File Tree & Paths (Post-Implementation)

```
ci/scripts/
├── agents/
│   └── semantic_reviewer.py                       # Agent module (Req 01)
├── gates/
│   ├── __init__.py
│   └── agent_review_check.py                      # Gate wrapper (Req 01)
└── gate_registry.json                             # Updated with agent_review_check entry (Req 01)

tests/ci/
├── test_semantic_reviewer_agent.py               # Behavioral tests (50+, Req 05)
├── test_semantic_reviewer_agent_adversarial.py   # Adversarial tests (40+, Req 05)
└── test_agent_review_integration.py              # Integration tests (3–5, Req 04)

tests/ci/fixtures/
└── bundles/                                       # M902-13 bundle fixtures (v1.0 schema)
    ├── clean_bundle.json
    ├── violations_bundle.json
    ├── edge_case_empty.json
    └── ...

project_board/specs/
└── 902_14_agent_review_layer_spec.md            # This spec (v1.0 FROZEN)

project_board/checkpoints/M902-14/
└── 2026-05-19T-m902-14-specification.md         # Spec checkpoint log

.semantic_reviews/                                # Input bundle directory (runtime artifacts, NOT committed)
└── <issue_id>.json                               # Example: PR-42.json (from M902-13 semantic extraction)
```

---

## Deferred Scope (M903+)

- **Orchestration & routing:** Which changes trigger bundling, bundle archival, per-PR vs per-commit routing (M903 responsibility)
- **Agent scheduling:** When/how agent review runs, feedback loops, re-evaluation after fixes (M903+)
- **Decision enforcement:** Actual routing (APPROVE → Stage 7, WARN → log + proceed, REJECT → FAIL) handled by orchestrator (M903)
- **Confidence-based weighting:** Using confidence score to influence downstream decisions (M903 policy)
- **Multi-language support:** Python-centric in M902-14; JavaScript, GDScript extension (M904+)
- **Agent configuration:** Per-project tuning of confidence weights, decision thresholds (M903 configuration)
- **Interactive agent feedback:** Bundle clarifications, agent follow-up questions (M906+)
- **Machine learning refinement:** ML-based signal weighting, neural feature extraction (M905+)
- **Semantic code analysis beyond bundles:** AST-level analysis, complexity scoring (M904+)

**M902-14 scope:** Stage 6 agent semantic review layer (deterministic evaluation, decision output, JSON output contract) only.

---

## Summary

**Specification v1.0 is FROZEN.** All 6 requirements documented with acceptance criteria, risk analysis, and edge case handling. All 7 ticket ACs mapped. Design decisions frozen in checkpoint log. Ready for spec exit gate and Test Designer handoff.

**Next Steps:**
1. Run `python ci/scripts/spec_completeness_check.py project_board/specs/902_14_agent_review_layer_spec.md --type generic` to validate completeness
2. If spec exit gate passes: advance ticket Stage → TEST_DESIGN, Revision → 3, Next Responsible Agent → Test Designer Agent
3. Test Designer: read spec v1.0 and execute plan Task 2 (design 50+ behavioral tests covering all signals and decision outcomes)
