# Specification: Stage 7 — Override & Escalation System

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/15_stage_7_override_and_escalation_system.md`  
**Milestone:** 902 — Agent Predictability Improvements  
**Agent:** Spec Agent  
**Date:** 2026-05-19  
**Status:** SPECIFICATION (Revision 1)  
**Version:** 1.0 FROZEN

---

## Overview

This specification defines Stage 7 of the 8-stage governance pipeline: the **Override & Escalation System**. This stage enables controlled code suppressions via the `# blobert-ignore-next-line` syntax, with explicit justification, issue links, and optional expiration dates. The gate validates suppression metadata (format, issue link validity, expiration status), detects repeated/high-risk suppressions, and escalates to human review via the M902-01 validation framework.

**Scope:** Governance layer for enforcement of code suppressions in Python, JavaScript, GDScript, and other supported languages under the blobert project.

**Core Constraints:**
- Suppression syntax is comment-based, appearing on the line immediately preceding the target line.
- Gate validates technical correctness (format, date parsing, issue link format); semantic judgment (is reason justified?) deferred to human review.
- Gate integrates into M902-01 validation gate framework (registry, schema, runner).
- Gate always exits 0 in shadow mode (advisory; orchestrator decides enforcement).

---

## Assumptions and Checkpoint Resolutions

The following assumptions are made per the checkpoint protocol. Each resolves an ambiguity that would otherwise require human input.

| # | Ambiguity | Assumption | Confidence |
|---|-----------|------------|------------|
| A1 | Suppression syntax: inline or block comment? | Single-line inline comment: `# blobert-ignore-next-line: reason="...", ticket="...", [until="..."]` placed on line immediately before target. Simplest, most diff-friendly. | High |
| A2 | Validation responsibility: gate vs human? | Gate validates technical correctness (format, date parsing, link format). Semantic judgment deferred to human (WARN status gates, not FAIL). | High |
| A3 | Repeated suppression threshold? | 3+ occurrences of same rule in same code area (file + 50-line window, or function scope) trigger escalation. | Medium |
| A4 | High-risk rule classification? | Rules from code_governance.md Stage 1–3 with rule_id prefixes AR- (architecture), SE- (security), AS- (async safety), EXH- (exception handling). | Medium |
| A5 | Audit log format and location? | JSON artifact in gate result (or under `project_board/checkpoints/M902-15/override_audit_log.json`) with timestamp, file, line, rule_id, reason, ticket, expiration, first_seen, repeat_count, escalation_reason. | High |
| A6 | Gate exit code behavior? | Always exits 0 (shadow mode, advisory). Violations array and WARN status signal escalation; orchestrator decides enforcement. Matches M902-01 philosophy. | High |
| A7 | Changed files source? | Gate receives file list from input (changed_files) or invokes `git diff --name-only` to discover changed files. Scanning limited to changed files for performance. | High |
| A8 | Expiration date format and timezone? | ISO 8601 format (YYYY-MM-DD) only; all date comparisons in UTC (system clock as reference). Invalid format → WARN escalation. | High |

---

## Requirement 01: Suppression Syntax and Metadata Schema

### 1. Spec Summary

**Description:** Defines the syntax and metadata fields for code suppressions that allow controlled bypasses of governance rules. Suppressions are represented as inline comment directives appearing on the line immediately preceding the target code.

The suppression syntax is:
```
# blobert-ignore-next-line: reason="...", ticket="...", [until="..."]
```

**Example:**
```python
# blobert-ignore-next-line: reason="Async context required for I/O operation per AC-6", ticket="M902-15", until="2026-08-31"
async def critical_io_operation():
    ...
```

**Constraints:**
- Syntax must be a single-line comment.
- Syntax must appear on the line immediately preceding the suppressed code (no blank lines or other comments in between).
- Required fields: `reason` (string, min 10 chars, max 200 chars), `ticket` (format: alphanumeric + dashes, length 3–20 chars).
- Optional fields: `until` (ISO 8601 date, YYYY-MM-DD).
- Field separator: `reason="...", ticket="..."` (comma + space).
- No nesting or recursion (one suppression per line; each suppresses only the next line).

**Assumptions:**
- Syntax is globally unique within blobert (unlikely to collide with other linter/formatter directives).
- Metadata is human-readable and machine-parseable (no binary encoding, no escaped quotes in values).

**Scope:** Applies to all code in blobert under governance (Python at `asset_generation/python/`, JavaScript at `asset_generation/web/`, GDScript at `scripts/`).

### 2. Acceptance Criteria

- **AC-01.1:** Suppression syntax matches the regex pattern: `^\s*#\s+blobert-ignore-next-line:\s*reason="[^"]{10,200}",\s*ticket="[A-Z0-9\-]{3,20}"(,\s*until="\d{4}-\d{2}-\d{2}")?$` (case-insensitive prefix check; case-sensitive field names).
- **AC-01.2:** Suppression with minimal metadata (reason + ticket) is valid; example: `# blobert-ignore-next-line: reason="Temporary coupling required", ticket="BLB-123"`.
- **AC-01.3:** Suppression with expiration is valid; example: `# blobert-ignore-next-line: reason="Migration in progress", ticket="M902-15", until="2026-08-31"`.
- **AC-01.4:** Suppression on line N suppresses the violation on line N+1 only (not N or N+2).
- **AC-01.5:** Multiple suppressions on consecutive lines are processed independently (each suppresses the next line).
- **AC-01.6:** Spec includes a complete BNF/regex definition of suppression syntax for implementation reference.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Syntax collision with existing linter comments (pylint, flake8, eslint) | Gate processes valid governance suppressions; external tools process their own | Unique prefix `blobert-ignore-next-line` distinguishes from `pylint:`, `noqa:`, `eslint-disable`. Test validates no conflicts in codebase. |
| Regex parsing too strict (misses valid formats) | Legitimate suppressions rejected | AC-01.1 defines regex explicitly; tests validate all variations (quoted fields, optional expiration, whitespace). |
| Reason field too vague (doesn't help reviewer) | Human reviewer lacks context | Spec requires min 10 chars; gate flags short reasons as low-confidence escalation; human decides weight. |
| Suppression on wrong line (suppresses unintended code) | Silent governance bypass | Gate validates line number + target line content (TBD in Requirement 02); test validates target matching. |

### 4. Clarifying Questions

- **Q1:** Should suppression support Unicode characters in reason field (e.g., emoji, non-ASCII)? *Assumption: Yes; spec requires reason be valid UTF-8 string. Test validates Unicode handling.*
- **Q2:** Should suppression allow escaped quotes in reason (e.g., `reason="Use \"exact\" syntax"`)?. *Assumption: No; spec prohibits quotes in reason field (simplest parsing). If needed, use alternative wording.*

---

## Requirement 02: Validation Rules and Metadata Processing

### 1. Spec Summary

**Description:** Defines how the gate validates suppression metadata (format, reason, ticket, expiration) and processes suppressions to check for technical correctness.

**Validation Layers:**

1. **Format Validation:** Suppression comment matches regex pattern from Requirement 01.
2. **Reason Validation:** Non-empty, min 10 chars, max 200 chars, contains only printable ASCII + common Unicode (no control codes).
3. **Ticket Validation:** Format check only (alphanumeric + dashes, 3–20 chars); HTTP/link validity deferred to human review.
4. **Expiration Validation:** If `until` field present, parse as ISO 8601 date (YYYY-MM-DD); compare against system clock (UTC); flag if expired.
5. **Rule Classification:** If suppression targets a rule_id (from prior violations), classify as high-risk (AR-, SE-, AS-, EXH- prefixes) or normal.

**Processing Flow:**
1. Scan changed files for suppression comments.
2. Extract metadata from each suppression.
3. Validate format, reason, ticket, expiration (step 2 above).
4. If valid, create suppression record: {file, line, rule_id (TBD), reason, ticket, expiration_date}.
5. If invalid, create escalation record: {file, line, validation_error, reason_provided}.

**Constraints:**
- Validation logic is deterministic (same input → same output).
- Invalid suppressions do not block gate (gate always exits 0); violations array tracks errors.
- Expiration validation uses system clock (UTC) as reference; no local timezone conversion.
- Reason validation is length-based (min/max bounds); content analysis deferred to human.

**Assumptions:**
- System clock is authoritative and in UTC.
- Ticket format is simple (alphanumeric + dashes); no HTTP resolution.
- Rule_id is provided by upstream gates (M902-14 violations array).

**Scope:** Applies to all suppressions detected by gate in changed files.

### 2. Acceptance Criteria

- **AC-02.1:** Gate validates suppression format against regex pattern from AC-01.1; stores validation result (pass/fail) with error message.
- **AC-02.2:** Gate validates reason field: min 10 chars, max 200 chars, non-empty, printable ASCII + common Unicode (no control codes); stores validation result (pass/fail) with error message.
- **AC-02.3:** Gate validates ticket field: format `[A-Z0-9\-]{3,20}` (alphanumeric + dashes, 3–20 chars); stores validation result (pass/fail); does not validate HTTP link existence.
- **AC-02.4:** Gate validates expiration (if present): parses as ISO 8601 date (YYYY-MM-DD); compares against system clock (UTC); flags if `until_date < today` as EXPIRED; stores validation result.
- **AC-02.5:** Gate classifies rule_id from violations array: if rule_id starts with AR-, SE-, AS-, or EXH-, classify as "high_risk"; otherwise "normal".
- **AC-02.6:** Spec includes validation algorithm pseudocode or flowchart for implementation reference.
- **AC-02.7:** A test vector file `project_board/specs/902_15_test_vectors.md` lists 30+ validation test cases (valid/invalid formats, expiration scenarios, edge cases).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Regex too strict (rejects valid Unicode in reason) | Legitimate suppressions fail validation | AC-02.2 specifies "printable ASCII + common Unicode"; tests validate Unicode ranges explicitly. |
| Expiration boundary ambiguity (today = expired or valid?) | Suppressions on expiration date handled inconsistently | Assumption frozen: `until_date < today` is EXPIRED; `until_date >= today` is valid. Test covers boundary cases. |
| Invalid date format (e.g., 2026/12/31 instead of 2026-12-31) | Suppressions with wrong date format silently ignored or error | Spec: Invalid format → WARN escalation + validation error. Test validates error case. |
| Ticket format too loose (accepts garbage like "XXX-YYY") | Invalid issue links passed through | Spec: Format validation only (alphanumeric + dashes). HTTP validation deferred to human review. Test validates format boundary cases. |
| Rule classification incomplete (misses high-risk rules) | Architecture/security suppressions not detected | Spec lists specific prefixes (AR-, SE-, AS-, EXH-) with references to code_governance.md Stage 1–3. Test covers E2E scenarios. |

### 4. Clarifying Questions

- **Q3:** Should gate reject suppressions with tickets that don't exist (e.g., typo in ticket ID)?. *Assumption: No; format validation only. HTTP resolution deferred to human review (M903+).*
- **Q4:** Should gate track "first seen" timestamp (when suppression first appeared) or only "repeat count"?. *Assumption: Track both; audit log includes `first_seen` (ISO 8601 UTC) + `repeat_count` for trend analysis.*

---

## Requirement 03: Escalation Detection and Categorization

### 1. Spec Summary

**Description:** Defines the logic to detect escalation triggers (repeated suppressions, high-risk rules, invalid metadata) and categorize them for human review.

**Escalation Triggers:**

1. **Repeated Suppressions:** Same rule_id in same code area (file + 50-line window, or same function scope) appears 3+ times → escalate with `escalation_reason="REPEATED_SUPPRESSION"` and `repeat_count` field.

2. **Architecture/Security Rules:** Suppression targets rule_id with high-risk prefix (AR-, SE-, AS-, EXH-) → escalate with `escalation_reason="HIGH_RISK_RULE"` (advisory gate, non-blocking).

3. **Invalid Metadata:** Suppression fails format, reason, ticket, or expiration validation → escalate with `escalation_reason="VALIDATION_ERROR"` and error details.

4. **Expired Suppression:** Suppression has `until_date < today` (UTC) → escalate with `escalation_reason="EXPIRED"`.

**Processing Flow:**
1. For each suppression, check if any of the above triggers apply.
2. If trigger applies, create escalation record: {file, line, rule_id, reason, ticket, expiration, escalation_reason, repeat_count (if repeated), validation_error (if invalid)}.
3. If no trigger, mark as "APPROVED" (no escalation).
4. Aggregate escalations for audit log output.

**Constraints:**
- Escalation detection is deterministic.
- Multiple triggers on same suppression: record all escalation reasons (not just first).
- Repeated suppression count is per-file (not global); scope boundary is 50-line window within same file (or function scope TBD in implementation).
- Escalation status does not affect gate exit code (always 0 in shadow mode).

**Assumptions:**
- Rule_id is provided by upstream gate (M902-14 violations array).
- Code area scope is file + 50-line window (or function scope; implementation clarifies).
- Suppression first seen timestamp can be derived from git history or file modification time.

**Scope:** Applies to all suppressions detected in changed files.

### 2. Acceptance Criteria

- **AC-03.1:** Gate detects repeated suppressions: if same rule_id appears 3+ times in same file (within 50-line window), create escalation record with `escalation_reason="REPEATED_SUPPRESSION"` and `repeat_count` field.
- **AC-03.2:** Gate detects high-risk rule suppressions: if rule_id starts with AR-, SE-, AS-, or EXH-, create escalation record with `escalation_reason="HIGH_RISK_RULE"` (advisory, non-blocking).
- **AC-03.3:** Gate detects invalid metadata: if format, reason, ticket, or expiration validation fails, create escalation record with `escalation_reason="VALIDATION_ERROR"` and error message.
- **AC-03.4:** Gate detects expired suppressions: if `until_date < today` (UTC), create escalation record with `escalation_reason="EXPIRED"`.
- **AC-03.5:** Multiple escalation triggers on same suppression are all recorded (not collapsed to one reason).
- **AC-03.6:** Repeated suppression scope definition is explicit: same file + 50-line window (TBD in implementation: confirm window size or function scope).
- **AC-03.7:** Spec includes escalation decision matrix (rule_id prefix → escalation reason) for implementation reference.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Repeated suppression scope unclear (50-line window vs function scope) | Duplicates missed or false positives | Spec freezes scope definition in AC-03.6; implementation clarifies in code comment; test covers both window and function boundaries. |
| Architecture/security rule classification incomplete (misses rules) | High-risk suppressions not detected | Spec lists specific prefixes (AR-, SE-, AS-, EXH-) with references to code_governance.md. Test covers E2E scenarios (async, exception, SRP in suppressions). |
| Multiple escalation reasons on same suppression confuse human reviewer | Escalation actionability unclear | Spec: record all escalation reasons; audit log includes all; human decides priority. Test validates multi-reason cases. |
| Repeated count not reset after suppression removed | Stale data in audit log | Spec: repeat_count is per-run (not persistent); removed suppressions don't accumulate. Test validates reset behavior. |

### 4. Clarifying Questions

- **Q5:** Should repeated count reset if same rule moves to different code area (file or function)? *Assumption: Yes; repeated count is per-file per-window (or per-function). Same rule in different file = new baseline.*
- **Q6:** Should expiration check consider time-of-day (not just date)? *Assumption: No; date only (YYYY-MM-DD). Time-of-day comparison deferred to M903+ if needed.*

---

## Requirement 04: Gate Module and M902-01 Integration

### 1. Spec Summary

**Description:** Specifies the gate module implementation and integration into the M902-01 validation gate framework.

**Gate Module:**
- **Path:** `ci/scripts/gates/override_and_escalation_check.py`
- **Function:** `run(inputs: dict) -> dict`
- **Purpose:** Validate suppressions, detect escalations, return M902-01 gate result schema + audit log artifact.

**Input Contract:**
```python
{
  "changed_files": ["file1.py", "file2.py"],  # List of paths relative to repo root (optional; if not provided, gate invokes git diff)
  "violations": [...],  # Violations array from M902-14 (optional; if not provided, gate processes all suppressions as potential)
  "issue_id": "M902-15",  # (optional) Upstream issue ID for audit log traceability
  "ticket_id": "M902-15",  # (optional) Ticket under which gate runs
  "upstream_agent": "Agent Review",  # (optional) Agent name for audit trail
  "downstream_agent": "Override Check",  # (optional) Agent name for audit trail
  "mode": "shadow"  # (optional; default "shadow") Shadow or blocking mode
}
```

**Output Contract (M902-01 success schema + audit log):**
```json
{
  "version": "1.0",
  "status": "PASS",
  "gate": "override_and_escalation_check",
  "upstream_agent": "Agent Review",
  "downstream_agent": "Override Check",
  "ticket_id": "M902-15",
  "timestamp": "2026-05-19T14-30-00Z",
  "duration_ms": 1234,
  "message": "Suppression validation complete. 0 escalations detected.",
  "artifacts": [
    {
      "path": "ci/scripts/gates/override_audit_log.json",
      "sha256": "abc123..."
    }
  ],
  "violations": [],  # Empty if no escalations; populated with escalation records if escalations detected
  "mode": "shadow"
}
```

**Audit Log Artifact Format (`override_audit_log.json`):**
```json
{
  "timestamp": "2026-05-19T14-30-00Z",
  "total_suppressions": 5,
  "total_escalations": 2,
  "suppressions": [
    {
      "file": "asset_generation/python/src/model.py",
      "line": 42,
      "rule_id": "AR-SRP-001",
      "reason": "Temporary coupling required for migration per M902-15",
      "ticket": "M902-15",
      "expiration_date": "2026-08-31",
      "first_seen": "2026-05-19T00-00-00Z",
      "repeat_count": 1,
      "escalation_reasons": ["HIGH_RISK_RULE"]
    },
    {
      "file": "asset_generation/python/src/model.py",
      "line": 60,
      "rule_id": "EXH-SILENT-FAIL",
      "reason": "Exception handling in progress",
      "ticket": "M902-15",
      "expiration_date": null,
      "first_seen": "2026-05-19T00-00-00Z",
      "repeat_count": 1,
      "escalation_reasons": ["HIGH_RISK_RULE", "VALIDATION_ERROR"]
    }
  ]
}
```

**Gate Registry Entry:**
```json
{
  "name": "override_and_escalation_check",
  "module": "ci.scripts.gates.override_and_escalation_check",
  "run_function": "run",
  "required_inputs": [],
  "optional_inputs": ["changed_files", "violations", "issue_id", "ticket_id", "upstream_agent", "downstream_agent", "mode"],
  "default_mode": "shadow",
  "description": "Validates code suppressions (# blobert-ignore-next-line) for proper justification, expiration, and escalates repeated/architecture/security bypasses for human review. Produces audit log and escalation violations."
}
```

**Constraints:**
- Module must be importable and callable via M902-01 gate runner.
- Must conform to M902-01 success schema (status, gate, timestamp, artifacts, duration_ms).
- Must not modify any files outside output directory.
- Must use only Python stdlib (no new third-party dependencies).
- Exception handling: no bare except; all exceptions logged with context, re-raised or transformed.

**Assumptions:**
- M902-01 gate framework stable (registry, runner, schema).
- Violations array from M902-14 has rule_id field.
- Changed files are relative paths from repo root.

**Scope:** Applies to M902-15 implementation only.

### 2. Acceptance Criteria

- **AC-04.1:** Gate module `ci/scripts/gates/override_and_escalation_check.py` exists and is importable.
- **AC-04.2:** Function `run(inputs: dict) -> dict` accepts input contract (AC-04 Input Contract) and returns output contract (AC-04 Output Contract).
- **AC-04.3:** Gate conforms to M902-01 success schema: `status`, `gate`, `timestamp` (ISO 8601), `artifacts` (array with path + sha256), `duration_ms`, `message`.
- **AC-04.4:** Gate produces audit log artifact as JSON: `suppressions` array with all required fields (file, line, rule_id, reason, ticket, expiration_date, first_seen, repeat_count, escalation_reasons).
- **AC-04.5:** Gate registered in `ci/scripts/gate_registry.json` with all required fields: `name`, `module`, `run_function`, `required_inputs`, `optional_inputs`, `default_mode`, `description`.
- **AC-04.6:** Gate is invocable via M902-01 gate runner: `python ci/scripts/gate_runner.py override_and_escalation_check --input '{"changed_files": [...], ...}'` produces valid result file.
- **AC-04.7:** Gate handles missing inputs gracefully: if `changed_files` not provided, invokes `git diff --name-only` (or logs WARNING and continues); if `violations` not provided, processes all suppressions as potential.
- **AC-04.8:** Exception handling per code_governance.md: no bare except; file not found → log WARNING, skip file; git diff unavailable → log WARNING, fallback to input files or skip.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gate module import fails (syntax error, missing dependency) | Gate runner crashes; no result file produced | Test gate import before handoff; validate syntax and dependencies. |
| Git diff unavailable (detached HEAD, no git repo) | Gate cannot discover changed files | Graceful fallback: if `changed_files` provided in input, use those; if not, log WARNING and process empty set. |
| Audit log artifact very large (1000+ suppressions) | Result file bloated; downstream processing slow | Audit log only includes suppressions, not full code context; should remain <1MB for typical changes. Stress test validates. |
| SHA-256 computation slow for large audit log | Gate performance degraded | Compute SHA-256 only for generated artifact (not for input files); should be <100ms. |

### 4. Clarifying Questions

- **Q7:** Should audit log be a separate file (written to disk) or returned inline in gate result JSON? *Assumption: Both; gate writes to disk (under `ci/scripts/gates/` or `project_board/checkpoints/M902-15/`) and references in `artifacts` array with path + sha256.*

---

## Requirement 05: Audit Logging and Machine-Readable Escalation Record

### 1. Spec Summary

**Description:** Specifies the audit log artifact that records all suppressions, escalations, and metadata for downstream analysis, trend tracking, and human review.

**Audit Log Schema:**
```json
{
  "version": "1.0",
  "timestamp": "2026-05-19T14-30-00Z",
  "total_suppressions": <count>,
  "total_escalations": <count>,
  "total_files_scanned": <count>,
  "suppressions": [
    {
      "file": "<relative_path_from_repo_root>",
      "line": <line_number>,
      "rule_id": "<rule_id_or_null>",
      "reason": "<justification_text>",
      "ticket": "<issue_or_ticket_id>",
      "expiration_date": "<YYYY-MM-DD_or_null>",
      "first_seen": "<ISO_8601_UTC_timestamp>",
      "repeat_count": <integer>,
      "escalation_reasons": [<list_of_escalation_reason_strings>],
      "validation_errors": [<list_of_error_messages_or_null>]
    },
    ...
  ]
}
```

**Field Definitions:**
- `file`: Relative path from repo root (e.g., `asset_generation/python/src/model.py`).
- `line`: Line number where suppression comment appears (line N suppresses line N+1).
- `rule_id`: Rule ID targeted by suppression (from violations array, or null if no violations provided).
- `reason`: Justification text extracted from suppression comment.
- `ticket`: Issue/ticket ID extracted from suppression comment.
- `expiration_date`: Expiration date from suppression comment (null if not provided).
- `first_seen`: ISO 8601 UTC timestamp (derived from git history or system time at gate run).
- `repeat_count`: Number of times same rule appears in same code area (1 if not repeated).
- `escalation_reasons`: Array of escalation trigger strings (e.g., `["HIGH_RISK_RULE", "EXPIRED"]`); empty if no escalations.
- `validation_errors`: Array of validation error messages (format error, invalid date, etc.); null if no errors.

**Output Location:**
- Primary: `ci/scripts/gates/override_audit_log.json` (or per-run under `project_board/checkpoints/M902-15/<timestamp>_override_audit_log.json`).
- Registered in gate result `artifacts` array with SHA-256 hash.

**Constraints:**
- All timestamps in ISO 8601 UTC (e.g., `2026-05-19T14-30-00Z`).
- Audit log always valid JSON (even if no suppressions found; `suppressions` array is empty).
- Audit log is machine-readable; no free-form text descriptions (use structured arrays and enums).
- Determinism: same input → identical audit log (sorted arrays, no timestamps in decision logic).

**Assumptions:**
- File paths are relative to repo root.
- Line numbers start at 1 (not 0).
- System clock is authoritative for `first_seen` timestamp (if git history unavailable).

**Scope:** Applies to all gate runs that detect suppressions.

### 2. Acceptance Criteria

- **AC-05.1:** Audit log is valid JSON with schema matching AC-05 Audit Log Schema.
- **AC-05.2:** Audit log includes `version`, `timestamp` (ISO 8601 UTC), `total_suppressions`, `total_escalations`, `total_files_scanned`.
- **AC-05.3:** Each suppression record includes all fields: `file`, `line`, `rule_id`, `reason`, `ticket`, `expiration_date`, `first_seen`, `repeat_count`, `escalation_reasons`, `validation_errors`.
- **AC-05.4:** Audit log is deterministic: same input → identical JSON (sorted suppressions array, no timestamps in decision logic).
- **AC-05.5:** Escalation reasons and validation errors are enums (not free-form text); valid values documented in spec.
- **AC-05.6:** Test validates audit log schema on every gate run (test loads JSON, validates field types, format).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Audit log not deterministic (timestamps vary per run) | Same input → different JSON; test failures | Gate uses system clock for `first_seen` only at suppression discovery time, not in decision logic; sorting ensures stable JSON. |
| Audit log grows unbounded (retention policy) | Disk space issues | Spec: gate produces artifact per run; retention policy deferred to M903+. |
| Escalation reason text unclear (human reviewer confused) | Escalation actionability reduced | Spec: escalation_reasons are enum strings (REPEATED_SUPPRESSION, HIGH_RISK_RULE, VALIDATION_ERROR, EXPIRED); documentation maps each to action. |
| Validation error messages not helpful (cryptic) | Human reviewer can't debug | Spec: validation_errors include specific error details (e.g., "Reason too short: 8 chars < 10 min"). Test validates error clarity. |

### 4. Clarifying Questions

- **Q8:** Should audit log include suppressed rule details (rule name, severity) from violations array? *Assumption: No; keep audit log minimal. Rule details deferred to human query of violations array.*

---

## Requirement 06: Test Vector Coverage and Edge Cases

### 1. Spec Summary

**Description:** Specifies comprehensive test coverage for all functionality: suppression formats, validation scenarios, escalation detection, and edge cases.

**Test Categories (50+ tests total):**

1. **Valid Suppression Formats (8 tests):**
   - Minimal valid syntax (reason + ticket).
   - With expiration date.
   - Unicode characters in reason.
   - Max length reason (200 chars).
   - Various ticket formats (M902-15, BLB-123, PR-42).
   - Extra whitespace in comment.

2. **Invalid Formats (8 tests):**
   - Missing reason field.
   - Missing ticket field.
   - Malformed syntax (typos, wrong separators).
   - Invalid characters in field values.
   - Duplicate field names (e.g., two `reason=` fields).
   - Extra unexpected fields.

3. **Reason Validation (5 tests):**
   - Minimum length (9 chars = FAIL, 10 chars = OK).
   - Maximum length (200 chars = OK, 201 chars = FAIL).
   - Empty reason.
   - Whitespace-only reason.
   - Special characters (quotes, newlines — should FAIL).

4. **Ticket Validation (5 tests):**
   - Valid format (M902-15, BLB-123, PR-42).
   - Invalid format (spaces, special chars, too short/long).
   - HTTP link format check (format only, no HTTP resolution).
   - Case sensitivity (uppercase only).

5. **Expiration Validation (8 tests):**
   - Future date (2026-12-31 = OK if today < date).
   - Past date (2020-01-01 = EXPIRED).
   - Expiration date = today (boundary: TBD; assume valid).
   - Invalid date format (2026/12/31 = FAIL).
   - Leap year dates (2024-02-29 = OK).
   - Invalid month (2026-13-01 = FAIL).
   - Out-of-range date (2026-01-32 = FAIL).
   - Missing `until=` field (optional, OK).

6. **Repeated Suppression Detection (8 tests):**
   - 1x same rule in file = NO escalation.
   - 2x same rule in file = NO escalation.
   - 3x same rule in file = ESCALATION.
   - 5x same rule in file = ESCALATION (with repeat_count=5).
   - 3x same rule in different files = NO escalation (per-file).
   - 3x different rules in same file = NO escalation (per-rule).
   - Repeated in same function vs different functions in same file (scope boundary).

7. **Architecture/Security Rule Detection (8 tests):**
   - Suppression for AR-* rule = ESCALATION (architecture).
   - Suppression for SE-* rule = ESCALATION (security).
   - Suppression for AS-* rule = ESCALATION (async safety).
   - Suppression for EXH-* rule = ESCALATION (exception handling).
   - Suppression for SRP-* rule = NO escalation (normal).
   - Suppression for unknown rule = NO escalation.
   - Mix of high-risk + low-risk rules = ESCALATION if any high-risk.
   - Rule_id prefix case sensitivity (only uppercase triggers escalation).

8. **Multi-File Changes (3 tests):**
   - Suppressions in multiple files → each processed independently.
   - Repeated rule across files → counted separately per file.
   - File set changes → recount.

9. **Audit Log Output (3 tests):**
   - Audit log JSON valid and parseable.
   - All required fields present (file, line, rule_id, reason, ticket, etc.).
   - Timestamps in ISO 8601 UTC format.
   - Arrays sorted deterministically (by file path, then line number).

10. **Determinism (2 tests):**
    - Same input → identical output JSON (byte-for-byte).
    - Same input (different order) → identical output (after sorting).

11. **Gate Integration (3 tests):**
    - Gate output conforms to M902-01 success schema.
    - Gate handles missing inputs (changed_files, violations).
    - Gate registration in gate_registry.json is valid.

12. **Edge Cases (5 tests):**
    - No changes (empty file list) → empty audit log.
    - No suppressions → empty escalations array.
    - Suppression on first line of file → applies to line 2.
    - Suppression on last line of file → applies beyond EOF (no effect).
    - Very large file (10K lines) with suppression near end.

13. **Performance & Stress (3 tests):**
    - Large file set (100 files) → gate completes <5 seconds.
    - Large violations array (500 entries) → audit log still complete.
    - Long reason text (500 chars, validation FAIL) → handled gracefully.

**Test Organization:**
- Parametrized tests using pytest.mark.parametrize.
- Fixtures for: file content mocking, violations array, expected audit log.
- Each test validates: (1) gate output status, (2) violations array (if escalations), (3) audit log structure.
- Test names describe scenario clearly (e.g., `test_repeated_suppression_3x_same_rule_escalates`).
- Docstrings reference AC numbers and spec requirements.

**Constraints:**
- All tests deterministic (no randomness, no mocking of gate internals).
- Tests are behavioral (validate gate output, not internal implementation).
- Performance tests include timing assertions (e.g., `assert duration_ms < 5000`).

**Assumptions:**
- File mocking available (pytest fixtures, pathlib.Path mocking).
- violations array from M902-14 has rule_id field.
- System clock available for timezone tests (or mocked).

**Scope:** Applies to all gate functionality.

### 2. Acceptance Criteria

- **AC-06.1:** Test file `tests/ci/test_override_and_escalation_check.py` exists with 50+ behavioral tests organized by category (at least 8 per category).
- **AC-06.2:** Test file `tests/ci/test_override_and_escalation_check_adversarial.py` exists with 40+ adversarial/edge case tests (stress, boundary conditions, determinism).
- **AC-06.3:** Each test validates gate output: status (PASS), violations array (if escalations), audit log structure (JSON schema).
- **AC-06.4:** Test names are self-documenting (e.g., `test_repeated_suppression_3x_same_rule_escalates`); docstrings reference AC numbers.
- **AC-06.5:** All tests are parametrized (use `pytest.mark.parametrize`); no hardcoded test data in function bodies.
- **AC-06.6:** All tests are deterministic: running twice → same results; no mocking of gate internals (only inputs).
- **AC-06.7:** Spec includes test vector file `project_board/specs/902_15_test_vectors.md` listing 30+ test cases with inputs/expected outputs.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Test coverage too strict (implementation can't satisfy) | High test failure rate before implementation starts | Test vectors are conservative (match spec requirements); implementation must satisfy all tests. |
| Test vectors conflict with code_governance.md rules | Tests fail despite correct implementation | Spec freezes rule priorities and escalation thresholds; test vectors validated against spec explicitly. |
| Mocking too complex (tests hard to maintain) | High maintenance burden | Use pytest fixtures for file/violations mocking; keep mocks simple and focused. |

### 4. Clarifying Questions

- **Q9:** Should tests validate suppression syntax against actual linter comment styles in codebase (e.g., existing pylint comments)?. *Assumption: No; tests validate blobert suppression syntax only. Linter compatibility checked separately.*

---

## Non-Functional Requirements

### NFR-01: Performance
- Gate execution (suppression scanning + validation + escalation detection) must complete in < 5 seconds for 100-file changes with up to 50 suppressions.
- SHA-256 computation for audit log artifact must complete in < 100ms.
- regex matching and date parsing must be constant-time (no ReDoS vulnerabilities).

### NFR-02: Reliability
- Gate must not crash on invalid input (must produce clear error message and exit 0 in shadow mode).
- Gate must not modify any files outside output directory (read-only except for audit log).
- Gate results must be deterministic for the same inputs (same audit log, same JSON structure).
- File not found or git diff unavailable must be handled gracefully (log WARNING, continue).

### NFR-03: Maintainability
- Gate module must be ≤ 700 lines of code (including comments and docstrings).
- Validation logic must be modular (separate functions for each validation type).
- Regex pattern must be documented (source of truth for syntax).
- Escalation decision logic must be clear (priority order, enum values documented).

### NFR-04: Observability
- Gate results must include `duration_ms` for performance monitoring.
- Gate results must include `timestamp` in ISO 8601 UTC format.
- Gate must log to stderr: gate name, mode, input summary, result status.
- Audit log must be machine-readable (JSON; no free-form text).

### NFR-05: Security
- Gate must not execute arbitrary code from suppression comments.
- Gate must not include secrets in audit log (validate no API keys/passwords in reason field).
- Regex pattern must be safe against ReDoS attacks (no nested quantifiers).
- File paths in audit log must be validated (no path traversal).

---

## Risk Register

| Risk ID | Description | Severity | Mitigation |
|---------|-------------|----------|------------|
| R1 | Suppression syntax collision with existing linter comments (pylint, flake8, eslint) | Medium | Use unique prefix `blobert-ignore-next-line`; test for conflicts in codebase |
| R2 | Issue link validation too strict (rejects valid) or too loose (accepts garbage) | Low | Format validation only; HTTP validity deferred to human review |
| R3 | Repeated suppression detection misses duplicates (different scopes, same rule) | Medium | Spec freezes scope definition (50-line window or function scope); test covers boundaries |
| R4 | Expiration date parsing fails on non-ISO formats | Low | Spec freezes ISO 8601; invalid → WARN escalation; test covers invalid formats |
| R5 | Audit log not available at gate runtime | Low | Gate generates in-process; returned in result JSON; always available |
| R6 | Performance: scanning large codebases slow (timeout) | Low | Scan only changed files; stress test validates <5s for 100-file set |
| R7 | Architecture/security rule classification incomplete (misses dangerous rules) | Medium | Spec references code_governance.md Stage 1–3 rule IDs; test covers E2E scenarios |
| R8 | Suppression reason too vague (doesn't help reviewer) | Low | Spec requires min 10 chars; gate flags short reasons as escalation; human decides |

---

## Dependencies

| Dependency | Ticket | Status | Impact |
|------------|--------|--------|--------|
| M902-01 (Validation Gate Framework) | COMPLETE | Gate registry, schema, runner available and stable |
| M902-14 (Agent Semantic Review) | COMPLETE | Violations array schema with rule_id field; examples available |
| code_governance.md Stage 7 | Reference | Suppression rules, escalation thresholds, rule ID naming conventions |

**No blocking dependencies.** All hard dependencies COMPLETE.

---

## File Tree (Post-Implementation)

```
project_board/
├── specs/
│   ├── 902_15_override_escalation_spec.md              # This spec (frozen v1.0)
│   └── 902_15_test_vectors.md                          # Test vectors (30+ cases)
├── checkpoints/
│   └── M902-15/
│       ├── 2026-05-19T-specification.md                # Spec Agent checkpoint
│       ├── 2026-05-19T-test_design.md                  # Test Designer checkpoint
│       ├── 2026-05-19T-test_break.md                   # Test Breaker checkpoint
│       ├── 2026-05-19T-implementation.md               # Implementation checkpoint
│       ├── 2026-05-19T-static_qa.md                    # Static QA checkpoint
│       ├── 2026-05-19T-integration.md                  # Integration checkpoint
│       └── 2026-05-19T-ac_gatekeeper_final.md          # AC Gatekeeper checkpoint
└── execution_plans/
    └── M902-15_stage_7_override_and_escalation_system.md

ci/scripts/
├── gates/
│   ├── __init__.py
│   └── override_and_escalation_check.py                # Gate module (NEW)
├── gate_registry.json                                  # Updated with override_and_escalation_check entry
└── gate_schemas/
    └── (inherited from M902-01)

tests/ci/
├── test_override_and_escalation_check.py               # Behavioral tests (50+ tests, NEW)
├── test_override_and_escalation_check_adversarial.py   # Adversarial tests (40+ tests, NEW)
└── test_override_escalation_integration.py             # Integration tests (5–8 tests, NEW)

.artifacts/
└── override_audit_log.json                             # Example audit log (OUTPUT, NOT COMMITTED)
```

---

## Spec Exit Gate Checklist

This spec is ready for the spec exit gate when:

- [x] All 6 requirements have Acceptance Criteria that are measurable, unambiguous, and independently verifiable.
- [x] All Acceptance Criteria reference concrete, testable behavior (not prose).
- [x] All assumptions are stated and confidence assessed (A1–A8 checkpoint resolution table).
- [x] Risks and edge cases are identified with mitigations (Risk Register section).
- [x] Clarifying questions are documented with assumptions (Q1–Q9 in requirements).
- [x] Non-functional requirements are defined (performance, reliability, maintainability, observability, security).
- [x] Dependencies are enumerated (M902-01, M902-14, code_governance.md).
- [x] File tree is specified (paths for gate module, tests, audit log, specs).
- [x] No gameplay changes are included (workflow governance only).
- [x] No new third-party dependencies required (stdlib only).
- [x] Schema files (audit log, gate result) are defined with examples.
- [x] Test coverage is explicit (50+ behavioral, 40+ adversarial, 5–8 integration).

---

## Spec Summary Table

| Aspect | Summary |
|--------|---------|
| **Core Feature** | Suppression syntax (`# blobert-ignore-next-line: reason="...", ticket="..."`) with metadata validation, repeated suppression detection, and escalation to human review. |
| **Gate Location** | `ci/scripts/gates/override_and_escalation_check.py` |
| **Input Contract** | Changed files list, violations array (optional), issue_id, ticket_id, mode |
| **Output Contract** | M902-01 gate success schema + audit log JSON artifact |
| **Escalation Triggers** | Repeated suppressions (3+x), high-risk rules (AR-, SE-, AS-, EXH- prefixes), invalid metadata, expired suppressions |
| **Audit Logging** | JSON artifact with suppression metadata, escalation reasons, validation errors; ISO 8601 UTC timestamps; deterministic |
| **Exit Behavior** | Always exits 0 (shadow mode, advisory); violations array signals escalations to orchestrator |
| **Test Coverage** | 50+ behavioral tests (formats, validation, escalation), 40+ adversarial tests (edge cases, stress, determinism), 5–8 integration tests |
| **Performance Target** | <5 seconds for 100-file changes with 50 suppressions |
| **Determinism** | Same input → identical audit log JSON (sorted arrays, no timestamps in decision logic) |

---

**Status: FROZEN v1.0 — Ready for Test Designer handoff**
