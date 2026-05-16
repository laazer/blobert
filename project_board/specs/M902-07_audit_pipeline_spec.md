# M902-07 Governance Audit Pipeline and Baseline Specification

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/07_governance_audit_pipeline_and_baseline.md`

**Status:** SPECIFICATION

**Revision:** 1

**Date:** 2026-05-16

**Prepared by:** Spec Agent

---

## Executive Summary

This specification defines a complete governance audit pipeline that integrates the existing static analysis gate (M902-02 COMPLETE) with a baseline grandfathering mechanism. The pipeline:

1. Invokes the static analysis gate to scan the repo and collect violations.
2. Clusters violations by (rule_id, path_prefix) to reduce noise and produce ticket-sized remediation bundles.
3. Maintains a `.governance-baseline.json` file with expiration dates, ownership, rationale, and rule metadata.
4. Detects "new violations" (outside baseline) and generates both JSON audit reports and human-readable remediation markdown.
5. Integrates audit metadata into the gate framework (M902-04) for observability and escalation.
6. Documents the baseline update policy and operator workflows.

**Key objectives:**
- Provide repository-wide visibility into governance violations without overwhelming developers.
- Allow temporary tolerance of legacy violations via explicit baseline entries.
- Support expiration policies so old exemptions do not accumulate indefinitely.
- Enable M903 to enforce blocking mode and auto-remediation workflows.

**Target users:** Operators, developers, and M903 enforcement agents.

---

## Functional Requirements

### Requirement FR1: Audit Command Architecture

#### 1. Spec Summary

**Description:** Design and implement a unified audit command (`ci/scripts/audit.py`) that orchestrates the complete audit pipeline: invoke the static analysis gate, parse violations, load and validate the baseline, cluster violations, detect baseline diffs, and generate reports.

**Constraints:**
- Must invoke the existing `static_analysis_check` gate (M902-02) via `gate_runner.py` (M902-01).
- Baseline file is `.governance-baseline.json` at repo root (configurable via CLI flag).
- Must produce three outputs: (1) JSON audit report, (2) Markdown remediation snippets, (3) Structured metadata for gate framework.
- Exit codes: 0 (PASS or shadow mode), 1 (FAIL with new violations in blocking mode), 2 (config/usage error).
- CLI flags: `--mode shadow|blocking`, `--baseline-path <path>`, `--output-dir <dir>`, `--upstream-agent <name>`, `--downstream-agent <name>`, `--ticket-id <id>`.
- Must handle missing baseline gracefully (create empty baseline, no violations match).
- Must handle missing or unavailable gate runner (fail with clear diagnostic).
- All file paths must respect CLAUDE.md conventions and be git-aware (no accidental file creation in repo root unless .gitignore approved).

**Assumptions:**
- Static analysis gate output is deterministic and parseable (M902-02 guarantees JSON format).
- Gate runner is available at `ci/scripts/gate_runner.py` and functional (M902-01 COMPLETE).
- Repo root is determinable via `.git/` or PWD-based heuristics.
- Python 3.11+ with json, pathlib, datetime, subprocess, logging modules available.
- Baseline schema is validatable via jsonschema library (standard, installed in pyproject.toml dev deps).

**Scope:** Single audit command that is the entry point for all audit operations; invoked by gate runner wrapper, Taskfile task, or direct CLI.

#### 2. Acceptance Criteria

- **AC1.1** Audit command exists at `ci/scripts/audit.py` and is executable as `python ci/scripts/audit.py --mode shadow ...`.
- **AC1.2** Command accepts all required flags (mode, baseline-path, output-dir, upstream-agent, downstream-agent, ticket-id) and shows help via `--help`.
- **AC1.3** Command invokes gate runner with correct arguments; gate_runner.py output is captured and parsed without errors.
- **AC1.4** Command loads `.governance-baseline.json` (or alternative path); if file does not exist, creates empty baseline with no violations match.
- **AC1.5** Command produces JSON audit report at `<output-dir>/audit-report-<timestamp>.json` with schema matching spec (FR6).
- **AC1.6** Command produces Markdown report at `<output-dir>/audit-report-<timestamp>.md` with remediation snippets (FR7).
- **AC1.7** Exit code is 0 on PASS or shadow mode; 1 on FAIL (new violations in blocking mode); 2 on usage/config error.
- **AC1.8** Error handling covers missing gate runner, invalid baseline JSON, unparseable gate output, and permission errors (all logged with actionable messages).
- **AC1.9** Command is deterministic: same inputs produce identical outputs (same JSON, same markdown, same clusters).
- **AC1.10** Execution time is documented; target is <30 seconds for clean repo (gate runtime dominates).

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Gate runner binary/module may not be on PATH or importable; audit command must fail fast with clear diagnostic (not cryptic ImportError).
- Baseline file may be corrupted (invalid JSON, missing schema); audit should reject and fail rather than silently skipping validation.
- Gate output format may be unstable across gate runner versions; audit must validate schema and report parsing errors (not assume field presence).
- Timestamp generation in JSON/Markdown must be deterministic (not affected by system clock jitter); use fixed timestamps for testing.

**Ambiguities:**
- None identified. Architecture and entry point are well-specified by gate framework.

#### 4. Clarifying Questions

None. Requirement is fully specified.

---

### Requirement FR2: Baseline Schema and Validation

#### 1. Spec Summary

**Description:** Define a JSON Schema for `.governance-baseline.json` that enforces structure, required fields, and data types. The schema must support immutability, expiration dates, ownership, and rationale fields. Implement validation logic in `ci/scripts/baseline.py` (or imported module).

**Constraints:**
- Schema format: JSON Schema (draft 7 or later, compatible with jsonschema library).
- Root structure: `{ "metadata": {...}, "entries": [...] }`.
- Metadata fields: `version` (string, e.g., "1.0"), `last_updated` (ISO 8601), `audit_host` (string), `audit_commit_sha` (string, optional), `description` (string, optional).
- Entry fields (required): `rule_id` (string, e.g., "ruff:F401"), `path_prefix` (string, regex pattern for path matching).
- Entry fields (optional): `expires_at` (ISO 8601 date or null), `owner` (string, free-text email/team name), `rationale` (string, human-readable reason for exemption), `created_at` (ISO 8601), `created_by` (string), `suppression_justification` (string).
- Constraints: `rule_id` must match pattern `^[a-z0-9-]+:[A-Za-z0-9-]+$` (tool:rule format). `path_prefix` must be valid regex or literal path. Dates must be ISO 8601. `owner` and `rationale` must not contain secrets (documented policy, not enforced in validation).
- Immutability: Baseline entries are append-only; no modification or deletion of existing entries. Updating an entry means adding a new entry with modified `path_prefix` or `rule_id`.
- Validation on load: audit command validates baseline against schema; invalid entries cause audit to fail with diagnostics.
- Validation on save: audit command appends new entries to baseline; must validate new entries before append.

**Assumptions:**
- jsonschema library is available (Python 3.11+, installed via pyproject.toml dev deps).
- ISO 8601 date format is enforced (UTC with Z suffix recommended, but parser accepts other ISO formats).
- Path prefixes use forward slashes (Unix convention, enforced across platforms via pathlib normalization).
- Secrets are not intentionally stored; policy is documented as a code review responsibility (not automated in M902-07).

**Scope:** Applies to `.governance-baseline.json` at repo root; schema definition at `project_board/schemas/governance-baseline-schema.json`; validation logic in `ci/scripts/baseline.py`.

#### 2. Acceptance Criteria

- **AC2.1** JSON Schema exists at `project_board/schemas/governance-baseline-schema.json` and is valid JSON Schema (schema-of-schema validates).
- **AC2.2** Schema defines: metadata fields (version, last_updated, audit_host, audit_commit_sha, description) and entry fields (rule_id, path_prefix, expires_at, owner, rationale, created_at, created_by, suppression_justification).
- **AC2.3** Schema enforces: rule_id format (tool:rule), path_prefix as valid regex or literal path, ISO 8601 dates, optional fields (expires_at, owner, rationale, created_at, created_by, suppression_justification).
- **AC2.4** Baseline validation module `ci/scripts/baseline.py` implements: load_baseline(path) → dict, validate_baseline(data) → bool/exceptions, is_entry_expired(entry, now) → bool, match_violation(violation, entry) → bool.
- **AC2.5** Validation rejects invalid baselines with clear error messages (e.g., "entry lacks required field: rule_id").
- **AC2.6** Validation accepts example baselines from Task 3 (5 entries covering Python, TypeScript, Godot, jscpd).
- **AC2.7** Immutability is documented: entries are append-only, no merge/update of existing entries.
- **AC2.8** Examples document how to add new entries (JSON format, required/optional fields, no secrets).

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Regex patterns in path_prefix may be error-prone (user mistyping patterns, leading to incorrect matching). Mitigation: validate path_prefix as regex on baseline load; reject invalid patterns.
- Expiration dates may be in the past (already expired when added to baseline); audit should handle gracefully (treat as expired, not as error).
- ISO 8601 parsing may vary across libraries; audit must normalize to UTC before comparing with "now".

**Ambiguities:**
- None identified. Schema is fully specified.

#### 4. Clarifying Questions

None. Requirement is fully specified.

---

### Requirement FR3: Violation Clustering Algorithm

#### 1. Spec Summary

**Description:** Design and implement an algorithm that groups violations by (rule_id, path_prefix_cluster) where path_prefix_cluster is derived by stripping file-specific path components and grouping at a configured directory depth. Clustering reduces noise by grouping related violations into ticket-sized bundles (5–15 violations per cluster).

**Constraints:**
- Grouping key: (rule_id, path_cluster) where path_cluster is determined by taking the first N parent directory components of the violation's file path.
- Depth tuning per language/scope:
  - Python (asset_generation/python/src/*): cluster depth = 2 (e.g., `asset_generation/python/src/module` groups all violations in that module).
  - Web backend (asset_generation/web/backend/*): cluster depth = 2.
  - TypeScript/React frontend (asset_generation/web/frontend/src/*): cluster depth = 2.
  - Godot (scripts/*, scenes/*, tests/*): cluster depth = 1 (e.g., `scripts/` groups all script violations together; scenes/ groups scene violations).
  - jscpd duplication (repo-wide): cluster depth = 1 (all duplication violations grouped by rule_id only).
- Algorithm: For each violation, extract the file path, apply language-specific depth rule, construct cluster key, and append violation to cluster[key]. Violations with no file path (or root-level paths) are grouped under a default cluster.
- Determinism: Clustering must be reproducible; same violations always produce same clusters. Use stable sorting (sorted by file path within each cluster).
- Edge cases: Generated files (*.glb, *_export.png) are excluded by gate, so clustering does not see them. Symlinks are resolved to canonical paths. Relative vs absolute paths are normalized to relative-to-repo.

**Assumptions:**
- All violations have a `file` field (gate schema guarantees this). If file is null/empty, treat as root-level violation and group under a sentinel cluster.
- Path separators are forward slashes (gate normalizes to Unix paths; implementation uses pathlib for cross-platform consistency).
- Language context is implicit in the file path (e.g., paths under `asset_generation/python/` are Python; under `asset_generation/web/frontend/` are TypeScript).

**Scope:** Clustering is applied during audit pipeline after violations are parsed from gate output; clusters are returned as part of audit report (FR6).

#### 2. Acceptance Criteria

- **AC3.1** Clustering module exists in `ci/scripts/audit.py` (or imported function from `ci/scripts/cluster.py`) with function `cluster_violations(violations: list[dict]) → dict[str, list[dict]]`.
- **AC3.2** Clustering groups violations by (rule_id, path_cluster) where path_cluster is derived per language spec (depth 2 for Python/TS backend, depth 2 for React frontend, depth 1 for Godot/jscpd).
- **AC3.3** Clusters are deterministic and reproducible (same input produces same output; violations within clusters are sorted by file path).
- **AC3.4** Cluster keys are human-readable (e.g., `ruff:F401:asset_generation/python/src/models`, `eslint:no-unused-vars:asset_generation/web/frontend/src/components`).
- **AC3.5** Clustering handles edge cases: violations with no file path, deeply nested files, root-level files. Violations are not lost or duplicated.
- **AC3.6** Each cluster contains 5–20 violations on average (for typical repos); no cluster has >50 violations (if so, depth may need tuning for M903).
- **AC3.7** Clustering is included in audit report as `clusters[]` with cluster_key, rule_id, path_cluster, violation_count, and violations[].

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Depth tuning (2 vs 1 vs 3) is heuristic and may not fit all repos. Mitigation: Spec documents tuning rationale; M903 can make depth configurable.
- Some repos may have deeply nested paths (e.g., `asset_generation/python/src/module/submodule/component.py`); depth=2 may produce very large clusters. Mitigation: Tests will reveal if clusters are too large; M903 can adjust.
- Symlinks in repo structure may cause path normalization issues. Mitigation: Implementation uses pathlib.resolve() to canonicalize paths.

**Ambiguities:**
- None identified. Algorithm is deterministic and fully specified.

#### 4. Clarifying Questions

None. Requirement is fully specified.

---

### Requirement FR4: Baseline Diff Detection

#### 1. Spec Summary

**Description:** Implement logic to detect "new violations" (not covered by baseline), "expired violations" (baseline entry has passed expiration date), and "remediated violations" (were in baseline, no longer in latest scan). Generate audit status (PASS, WARN, FAIL) based on violation categories and mode (shadow vs blocking).

**Constraints:**
- Violation matching: A violation matches a baseline entry if rule_id and path_prefix both match. Rule_id must match exactly. Path_prefix is a regex pattern; violation file path must match the pattern (using Python re.match() or re.search()).
- New violations: violation not in baseline OR rule_id not in baseline at all → NEW. New violations trigger FAIL status in blocking mode; logged as warnings in shadow mode.
- Expired violations: baseline entry has expires_at field and current time > expires_at → EXPIRED. Expired entries are ignored (treated as if they do not exist in baseline). Expired violations are logged as WARN status (advisory, not enforcing in M902-07).
- Remediated violations: violation was in baseline (last scan) but not in current scan → REMEDIATED. Remediated violations are logged for informational purposes (positive signal of progress).
- Audit status mapping:
  - PASS: No new violations and no rule_id mismatches.
  - WARN: Expired violations present (baseline entries no longer valid; renewal needed).
  - FAIL: New violations present (only in blocking mode; in shadow mode, status is still PASS but new violations are reported).
- Unknown rules: If a violation has a rule_id not in baseline and mode is blocking, audit fails (unknown rules are not tolerated). In shadow mode, unknown rules are logged as WARN.
- Output: Structured report with new[], expired[], remediated[], audit_status, summary message.

**Assumptions:**
- Baseline entries are never modified; updates mean adding new entries. Path matching is via regex.
- Expiration is checked against current UTC time (datetime.now(timezone.utc)).
- Violations from the gate are already clustered (FR3); diff detection operates on clusters or raw violations (spec allows both).

**Scope:** Applies during audit pipeline after violations are loaded and baseline is validated; diff result is included in audit report (FR6).

#### 2. Acceptance Criteria

- **AC4.1** Baseline diff module exists in `ci/scripts/audit.py` (or imported) with function `detect_baseline_diff(violations: list[dict], clusters: dict, baseline: dict, now: datetime, mode: str) → dict`.
- **AC4.2** Function returns structured dict with: new[], expired[], remediated[], audit_status (PASS/WARN/FAIL), summary.
- **AC4.3** Violation matching correctly identifies matches (rule_id + path_prefix regex) and non-matches (NEW violations).
- **AC4.4** Expiration logic correctly identifies expired entries (expires_at < now) and treats them as invalid.
- **AC4.5** Remediated violations are identified and included in output (informational).
- **AC4.6** Unknown rule IDs are handled: blocking mode fails, shadow mode warns.
- **AC4.7** Audit status is correctly set: PASS (no new), WARN (expired only), FAIL (new violations in blocking mode).
- **AC4.8** Diff detection is deterministic and reproducible.
- **AC4.9** Edge cases handled: empty baseline, empty scan, empty clusters, path normalization across platforms.

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Regex matching may be slow on large baseline or if path_prefix patterns are overly complex. Mitigation: Profile implementation; optimize if necessary (M903).
- Timezone handling (expiration date may be in different timezone if baseline was edited manually). Mitigation: Spec enforces UTC (Z suffix); validation rejects non-UTC dates.
- Path normalization may differ (Windows vs Linux slashes); pathlib.PurePosixPath normalizes to Unix paths.

**Ambiguities:**
- None identified. Logic is fully specified.

#### 4. Clarifying Questions

None. Requirement is fully specified.

---

### Requirement FR5: Audit Report Generation (JSON)

#### 1. Spec Summary

**Description:** Generate a structured JSON audit report containing: audit metadata, violations (categorized by NEW/EXPIRED/REMEDIATED/BASELINE), clusters, baseline diff summary, and remediation hints. Report is written to `<output-dir>/audit-report-<timestamp>.json`.

**Constraints:**
- Report schema (JSON structure):
  ```json
  {
    "version": "1.0",
    "audit_timestamp": "<ISO 8601>",
    "audit_id": "<uuid>",
    "mode": "shadow|blocking",
    "audit_status": "PASS|WARN|FAIL",
    "gate_status": "PASS|FAIL",
    "repo_commit": "<commit SHA or 'unknown'>",
    "repo_branch": "<branch name or 'unknown'>",
    "baseline_path": "<path to baseline file>",
    "baseline_valid": true|false,
    "violations": {
      "total": <int>,
      "new": <int>,
      "expired": <int>,
      "remediated": <int>,
      "baseline_matched": <int>
    },
    "violation_list": [
      {
        "category": "NEW|EXPIRED|REMEDIATED|BASELINE",
        "rule_id": "<rule>",
        "file": "<path>",
        "line": <int or null>,
        "severity": "CRITICAL|ERROR|WARN|INFO",
        "message": "<details>",
        "cluster_key": "<rule:path_cluster>",
        "baseline_entry": {<entry>} or null
      }
    ],
    "clusters": [
      {
        "cluster_key": "<rule:path_cluster>",
        "rule_id": "<rule>",
        "path_cluster": "<path>",
        "violation_count": <int>,
        "new_count": <int>,
        "expired_count": <int>,
        "remediated_count": <int>,
        "baseline_matched_count": <int>
      }
    ],
    "baseline_diff": {
      "new_violations": [<violation>],
      "expired_violations": [<violation>],
      "remediated_violations": [<violation>],
      "unknown_rules": [<rule_id>]
    },
    "summary": {
      "message": "<human-readable summary>",
      "recommendation": "<action to take>",
      "next_steps": [<step1>, <step2>, ...]
    }
  }
  ```
- All paths in the report are relative to repo root.
- Violations are sorted by severity (CRITICAL > ERROR > WARN > INFO) and then by rule_id and file.
- Clusters are sorted by violation_count (descending) and then by cluster_key.
- Summary message and recommendation are human-readable; next_steps are actionable (e.g., "Review cluster ruff:F401:asset_generation/python/src/models for import cleanup", "Renew or delete expired baseline entries").
- Report is indented JSON (2-space indentation for readability).

**Assumptions:**
- git CLI is available for commit SHA and branch detection (if not, use "unknown" as fallback).
- Report is written atomically (write to temp file, rename).
- Report file is named `audit-report-<YYYYMMDDTHHMMSSZ>.json`.

**Scope:** JSON report is one output of the audit command; consumed by operators, dashboards, and M903 enforcement agents.

#### 2. Acceptance Criteria

- **AC5.1** Audit report exists at `<output-dir>/audit-report-<timestamp>.json` after audit command completes.
- **AC5.2** Report JSON validates against the schema defined in this requirement.
- **AC5.3** All violations from gate output are included in report (categorized by NEW/EXPIRED/REMEDIATED/BASELINE).
- **AC5.4** Clusters are correctly populated from clustering algorithm (FR3).
- **AC5.5** Baseline diff is correctly populated from diff detection logic (FR4).
- **AC5.6** Summary message, recommendation, and next_steps are clear and actionable.
- **AC5.7** Report is sorted (violations by severity, clusters by count).
- **AC5.8** Paths are relative to repo root (no absolute paths in report).
- **AC5.9** Report includes metadata (audit_timestamp, audit_id, mode, status, repo info).
- **AC5.10** Report is deterministic: same inputs produce identical output (including timestamps if fixed for testing).

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Report file may grow large if there are many violations (1000+). Mitigation: Spec allows pagination in M903; report is comprehensive in M902.
- git commands may not be available in all CI environments. Mitigation: Graceful fallback to "unknown" for commit SHA and branch.
- Summary recommendations may be generic; specific actionable steps will be improved in M903.

**Ambiguities:**
- None identified. Report structure is fully specified.

#### 4. Clarifying Questions

None. Requirement is fully specified.

---

### Requirement FR6: Remediation Report Generation (Markdown)

#### 1. Spec Summary

**Description:** Generate a human-readable Markdown report with remediation guidance and ticket snippets suitable for creating backlog items. Report is written to `<output-dir>/audit-report-<timestamp>.md`.

**Constraints:**
- Markdown format with sections:
  1. Audit Summary (status, timestamp, repo info, baseline path).
  2. Violations Overview (total counts, categorization).
  3. Violation Clusters (one section per cluster, sorted by violation count).
     - For each cluster: cluster key, rule_id, path_cluster, violation count, severity distribution, sample violations (top 5).
     - Suggested remediation ticket heading and body (markdown template).
  4. Baseline Renewal (if expired violations present): list expired entries with renewal recommendations.
  5. Next Steps (actionable recommendations).
  6. Appendix: Tool Documentation Links.
- Markdown headings use standard markdown syntax (# for H1, ## for H2, etc.).
- Remediation ticket templates are formatted as backlog item snippets:
  ```markdown
  ### Title
  
  **Cluster:** ruff:F401:asset_generation/python/src/models
  **Violations:** 8 (ruff:F401 unused import)
  **Severity:** INFO
  
  #### Description
  
  Remove unused imports in asset_generation/python/src/models module.
  
  #### Sample Violations
  
  - `asset_generation/python/src/models/__init__.py:5` — unused import: `os`
  - `asset_generation/python/src/models/entity.py:12` — unused import: `typing.Optional`
  ...
  
  #### Effort Estimate
  
  ~30 minutes (straightforward cleanup)
  ```
- No secrets must appear in markdown (policy is documented; not enforced).
- Links to external documentation (tool docs, rule explanations) are included where applicable (deferred to M903 for comprehensive link database).

**Assumptions:**
- Markdown is human-readable without special rendering (readable in plain text).
- Remediation ticket templates are suggestions; humans will refine before creating backlog items.
- Effort estimates are rough (INFO severity ~ 30 min, ERROR severity ~ 2 hours, CRITICAL ~ 4+ hours as placeholders).

**Scope:** Markdown report is the user-facing output of the audit command; consumed by operators to understand violations and create remediation tasks.

#### 2. Acceptance Criteria

- **AC6.1** Markdown report exists at `<output-dir>/audit-report-<timestamp>.md` after audit command completes.
- **AC6.2** Report includes all sections: Summary, Violations Overview, Violation Clusters, Baseline Renewal, Next Steps, Appendix.
- **AC6.3** Each cluster has a remediation ticket template (markdown snippet) with title, description, sample violations, and effort estimate.
- **AC6.4** Violations are presented clearly (rule_id, file, line, severity, message).
- **AC6.5** Expired baseline entries are listed with renewal recommendations.
- **AC6.6** Next Steps are actionable and prioritized (e.g., "Fix critical violations", "Renew expired baseline entries", "Review cluster X for remediation").
- **AC6.7** Markdown is human-readable in plain text (no complex rendering required).
- **AC6.8** External documentation links are included where applicable (tool docs, rule explanations).
- **AC6.9** Markdown does not contain secrets or sensitive information.
- **AC6.10** Report is deterministic (same inputs produce identical output).

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Markdown report may be verbose (many clusters → long document). Mitigation: Operator can focus on high-severity clusters; summary provides executive overview.
- Effort estimates are rough; humans will refine based on code context and team velocity.
- Links to external docs may change or become stale (M903 can maintain link database).

**Ambiguities:**
- None identified. Report structure is fully specified.

#### 4. Clarifying Questions

None. Requirement is fully specified.

---

### Requirement FR7: Metadata Integration with Gate Framework

#### 1. Spec Summary

**Description:** Wire audit metadata fields into the gate framework (M902-01 gate schema v0.2.0 from M902-04) so that audit events are logged in the event log (`ci/artifacts/audit-logs/`) and audit results can be consumed by downstream enforcement agents.

**Constraints:**
- Audit gate output (JSON from audit command) must match gate schema from M902-01/04 or be compatible with a documented extension.
- New metadata fields for audit events (to be included in gate-result JSON or separate audit-specific metadata):
  - `audit_timestamp`: ISO 8601 timestamp when audit completed.
  - `audit_violations_count`: Total violation count from gate.
  - `audit_clusters_count`: Number of violation clusters generated.
  - `audit_status`: "PASS" | "WARN" | "FAIL" (from baseline diff).
  - `baseline_entries_expired_count`: Number of expired baseline entries.
  - `baseline_entries_new_count`: Number of new violations not in baseline.
  - `audit_report_path`: Relative path to JSON audit report (for linking).
  - `audit_markdown_path`: Relative path to Markdown remediation report.
- Event logging: Audit command emits events to `ci/scripts/audit_log.py` (from M902-04) with event types: `audit_started`, `audit_completed`, `baseline_validation`, `clustering_completed`, `diff_detected`.
- Event schema: Each event includes: timestamp, run_id, gate_name, ticket_id, event_type, event_data (with metadata fields above).
- Shadow mode: Metadata is still emitted in shadow mode (audit_status may be PASS even with new violations).
- Integration point: When audit gate is invoked via gate_runner.py, metadata fields are passed back in the gate-result JSON for handoff to M902-04 event logging.

**Assumptions:**
- M902-04 audit_log module is available and functional (import from `ci/scripts/audit_log.py`).
- Gate runner can handle extended metadata fields without breaking.
- Event logging is append-only and non-blocking (errors in logging do not fail audit).

**Scope:** Metadata wiring is internal to audit pipeline; consumed by gate framework and M903 enforcement.

#### 2. Acceptance Criteria

- **AC7.1** Audit command emits all metadata fields (audit_timestamp, audit_violations_count, audit_clusters_count, audit_status, baseline_entries_expired_count, baseline_entries_new_count, audit_report_path, audit_markdown_path).
- **AC7.2** Metadata fields are included in gate-result JSON output (compatible with M902-01 schema or documented as extension).
- **AC7.3** Audit events are logged to `ci/artifacts/audit-logs/` via `audit_log.py` functions (emit_audit_started, emit_audit_completed, etc.).
- **AC7.4** Event logging does not block or crash audit execution (non-blocking logging).
- **AC7.5** Metadata is emitted in both shadow and blocking modes.
- **AC7.6** Integration with M902-04 event log is tested (events are written correctly).
- **AC7.7** Metadata fields are documented in operator guide (FR8) and visible in audit reports (FR5, FR6).

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Extended metadata fields may conflict with future M902-04 schema changes. Mitigation: Coordinate with M902-04 owner; document fields as "audit extension" with version tag.
- Event logging may fail due to permission errors or disk full. Mitigation: Log errors to stderr but do not block audit (per M902-04 design).

**Ambiguities:**
- Exact schema version (v0.2.0 extension or v0.3.0)—decision is made during implementation (Task 7 in execution plan).

#### 4. Clarifying Questions

None. Requirement is fully specified.

---

### Requirement FR8: Operator Guide and Baseline Update Policy

#### 1. Spec Summary

**Description:** Document complete operator workflows: how to run the audit locally, interpret audit reports, add baseline entries, monitor expiration, troubleshoot, and make remediation decisions. Include decision trees and examples. Document the baseline update policy (manual JSON editing, two-reviewer gate deferred to M903).

**Constraints:**
- Guide must cover: quick-start command (`task audit` or `python ci/scripts/audit.py`), understanding audit report sections, reading remediation clusters, adding baseline entries (manual JSON), renewing expired entries, remediation prioritization, troubleshooting common issues.
- Guide must include 3–5 real or realistic audit scenario examples showing: (1) all PASS, (2) some new violations, (3) expired entries, (4) blocking mode with new violations, (5) mixed status.
- Decision tree for remediation prioritization: start with CRITICAL/ERROR severity clusters, estimate effort per cluster, prioritize by impact and effort.
- Baseline entry addition process: (1) User edits `.governance-baseline.json` (or uses helper command to add entry), (2) Entry format includes rule_id, path_prefix, expires_at (optional), owner (email/team), rationale. (3) Two-reviewer policy deferred to M903 (document as TODO). (4) Commit baseline changes via git.
- Expiration monitoring: run audit periodically (e.g., weekly) to detect expired entries; renew if baseline entry should remain (add new entry with extended expires_at date) or delete if violation should be fixed.
- Troubleshooting section: missing gate runner, invalid baseline JSON, path matching issues, performance issues (large repos), permission errors.
- Links to tool documentation (ruff docs, mypy docs, eslint docs, jscpd docs) for rule explanations.
- Policy on secrets: baseline rationale must not contain secrets; document as code review responsibility.

**Assumptions:**
- Operators have Python 3.11+, bash, git, and basic command-line familiarity.
- Repository lockfiles (uv.lock, package-lock.json) are stable.
- M903 will add advanced features (second-reviewer gate, blocking enforcement, UI); guide documents M902-07 manual process.

**Scope:** Guide is documentation (Markdown file); consumed by operators and developers.

#### 2. Acceptance Criteria

- **AC8.1** Operator guide exists at `project_board/specs/M902-07_operator_guide.md` with all sections described above.
- **AC8.2** Quick-start instructions are copy-paste ready (e.g., `cd /path/to/blobert && task audit`).
- **AC8.3** Audit report interpretation guide explains all sections (violations overview, clusters, baseline diff, next steps).
- **AC8.4** Remediation cluster examples show realistic violations and suggested ticket templates.
- **AC8.5** Baseline entry addition process is documented with JSON format examples.
- **AC8.6** Expiration monitoring and renewal are documented (how to check expires_at, how to update).
- **AC8.7** Decision tree for prioritization is clear (severity → effort → impact).
- **AC8.8** Troubleshooting section covers at least 80% of common issues (missing tools, invalid JSON, path matching, permissions).
- **AC8.9** External documentation links are provided (tool docs, rule explanations).
- **AC8.10** Secrets policy is documented (no secrets in baseline, code review responsibility).
- **AC8.11** Policy deferral to M903 (second-reviewer gate, blocking enforcement) is explicitly noted.
- **AC8.12** Guide is readable in plain text and formatted as markdown (no special rendering required).

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Guide may become stale if audit command changes. Mitigation: Keep guide and audit command in sync; update guide during M903 implementation.
- Operators may not understand regex patterns in path_prefix. Mitigation: Guide includes examples with common patterns; recommend testing with regex tools.

**Ambiguities:**
- None identified. Guide is fully specified.

#### 4. Clarifying Questions

None. Requirement is fully specified.

---

### Requirement FR9: Example Baseline Fragment

#### 1. Spec Summary

**Description:** Provide example `.governance-baseline.json` file with 5–8 realistic baseline entries covering Python (ruff, mypy), TypeScript (eslint), and cross-repo (jscpd duplication). Examples demonstrate rule_id, path_prefix, expires_at, owner, rationale, and suppression_justification fields.

**Constraints:**
- Entries must be realistic and match actual violations that can occur in the blobert codebase.
- Examples cover: (1) Python ruff violation (e.g., F401 unused import), (2) Python mypy violation (e.g., type mismatch), (3) TypeScript eslint violation (e.g., no-unused-vars), (4) jscpd duplication, (5) one expired entry (for demonstration).
- Each entry includes: rule_id (exact format), path_prefix (regex or literal), expires_at (optional, ISO 8601), owner (email or team name), rationale (clear explanation), created_at (ISO 8601), created_by (who added entry).
- Example entries must pass schema validation (FR2).
- Metadata section includes: version, last_updated, audit_host, audit_commit_sha (can be placeholder), description.
- File is stored at `project_board/specs/M902-07_example_baseline.json` (not committed as `.governance-baseline.json` in repo root unless M903 policy decision made).

**Assumptions:**
- Examples can be hand-crafted to demonstrate schema (no need to scan actual repo for examples).
- Examples match realistic violations from M902-02 static analysis gate implementation.

**Scope:** Example file is documentation (for operator guide and specification reference).

#### 2. Acceptance Criteria

- **AC9.1** Example baseline exists at `project_board/specs/M902-07_example_baseline.json`.
- **AC9.2** File contains 5–8 entries covering Python (ruff, mypy), TypeScript (eslint), and jscpd.
- **AC9.3** All entries are valid per baseline schema (FR2); file passes schema validation.
- **AC9.4** Each entry includes: rule_id, path_prefix, owner, rationale, created_at, created_by.
- **AC9.5** At least one entry has expires_at field (demonstrating expiration).
- **AC9.6** At least one entry is expired (demonstration of expired baseline entry handling).
- **AC9.7** Rule IDs and path prefixes are realistic and match actual violations from static analysis tools.
- **AC9.8** Rationale text is clear and non-technical (explains why violation is exempted).
- **AC9.9** Example is referenced in operator guide (FR8) and milestone README (update).
- **AC9.10** Example does not contain secrets or sensitive information.

#### 3. Risk & Ambiguity Analysis

**Risks:**
- Examples may not match actual violations in the blobert repo (M902-07 is early in workflow). Mitigation: Examples can be synthetic and representative; implementation (M902-07 Task 11) will generate real baseline from actual violations if needed.

**Ambiguities:**
- None identified. Examples are documentation.

#### 4. Clarifying Questions

None. Requirement is fully specified.

---

## Non-Functional Requirements

### NFR1: Determinism and Reproducibility

**Description:** Audit pipeline must produce identical outputs given identical inputs (same violations from gate, same baseline file, same configuration).

**Acceptance Criteria:**
- Audit command run twice with same inputs produces identical JSON report (same clusters, same violation categorization, same order).
- Clustering algorithm is deterministic (violations sorted by file path within clusters).
- Baseline diff logic is deterministic (same matching rules, same expiration logic).
- Timestamps in report are generated once at audit start; not updated per violation (for reproducibility).
- Random seed (if any) is fixed or seeded from input hash.

---

### NFR2: Performance

**Description:** Audit pipeline must complete within reasonable time bounds on typical repositories.

**Acceptance Criteria:**
- Full audit (gate invocation + baseline validation + clustering + diff detection + report generation) completes in <30 seconds on blobert repo (typical size, clean state).
- Gate invocation is the dominant cost (gate runtime is not optimized in M902-07).
- Clustering and diff detection are fast (<1 second each) on 100+ violations.
- Report generation is fast (<1 second) for JSON and Markdown.
- Timeouts are documented (gate runner timeout, no timeout for audit pipeline itself).

---

### NFR3: Graceful Error Handling

**Description:** Audit pipeline must handle errors gracefully (missing files, invalid JSON, permission errors) with clear diagnostics.

**Acceptance Criteria:**
- Missing baseline file: create empty baseline, continue with audit (no violations match).
- Invalid baseline JSON: fail with clear error message (line number, parse error).
- Missing gate runner: fail with clear diagnostic (gate runner not found at PATH).
- Unparseable gate output: fail with clear error (JSON parse error, unexpected schema).
- Permission errors (file write): fail with clear diagnostic (cannot write to output directory).
- All errors are logged to stderr; stdout contains structured output (JSON, Markdown, exit code).

---

## Risk Taxonomy

### High-Priority Risks

1. **Regex Matching in Path Prefixes**
   - Risk: Path prefix patterns may be invalid regex or match incorrectly.
   - Mitigation: Validate path_prefix as regex on baseline load; reject invalid patterns. Tests cover regex edge cases.
   - Owner: Implementation (Task 11), Test Designer (Task 9).

2. **Expiration Date Handling**
   - Risk: Off-by-one errors (expiration_date == now may be treated as expired or not expired).
   - Mitigation: Adversarial tests cover boundary cases (expiration_date == now, before/after). Spec uses strict inequality (expiration_date < now → expired).
   - Owner: Test Breaker (Task 10), Implementation (Task 11).

3. **Gate Output Format Instability**
   - Risk: M902-02 gate output format may change, breaking audit parsing.
   - Mitigation: M902-02 is COMPLETE and tested (83+ tests); gate schema is frozen. Low risk.
   - Owner: Spec Agent (Task 2 audit of gate schema).

4. **Baseline File Secrets Exposure**
   - Risk: Operator accidentally commits secrets in baseline rationale field.
   - Mitigation: Policy documented (no secrets in baseline); code review responsibility (not automated). Secret scanning tool can be added in M903.
   - Owner: Operator (policy), M903 (automation).

### Medium-Priority Risks

5. **Clustering Depth Tuning**
   - Risk: Depth tuning (2 for Python, 1 for Godot) may produce clusters that are too large or too small.
   - Mitigation: Algorithm is documented with rationale; tests validate cluster sizes. M903 can make depth configurable.
   - Owner: Spec Agent (Task 4), Implementation (Task 11), M903.

6. **Path Normalization Across Platforms**
   - Risk: Windows vs Linux path separators may cause normalization issues.
   - Mitigation: Spec uses forward slashes; implementation uses pathlib for cross-platform consistency.
   - Owner: Implementation (Task 11).

7. **Large Repository Performance**
   - Risk: Audit may timeout or use excessive memory on repos with 1000+ violations.
   - Mitigation: Performance tests with synthetic large repo; document scan scope (excludes .venv, node_modules, *.glb per CLAUDE.md).
   - Owner: Implementation (Task 11), Test Breaker (Task 10).

### Low-Priority Risks

8. **Event Logging Failures**
   - Risk: Audit log write failures (disk full, permission) may block audit.
   - Mitigation: Event logging is non-blocking; errors logged to stderr but do not fail audit (per M902-04 design).
   - Owner: Implementation (Task 11).

---

## Decisions Frozen (Checkpoint Summary)

1. **Audit Architecture:** Reuse existing static analysis gate (M902-02) via gate_runner.py (M902-01). No separate audit pipeline; audit wraps gate output.
2. **Baseline Granularity:** Rule + path prefix (e.g., `ruff:F401:asset_generation/python/src/`). Fine-grained fingerprints deferred to M903.
3. **Expiration Policy:** Absolute ISO 8601 dates per entry; optional field (no expiration = permanent). Enforcement in M903.
4. **Ownership Model:** Free-text string (email, team name). No validation in M902-07; enforcement/notification in M903.
5. **Baseline Schema:** JSON Schema with required fields (rule_id, path_prefix) and optional fields (expires_at, owner, rationale, created_at, created_by, suppression_justification).
6. **Remediation Generation:** Audit produces Markdown snippets; ticket creation deferred to M903 or manual process.
7. **Clustering Depth:** Python/React backend = 2, Godot = 1, jscpd = 1 (rule_id only). Tunable in M903.
8. **Mode Handling:** Shadow mode reports violations without enforcing; blocking mode fails on new violations (deferred enforcement, M903 enables).
9. **Immutability:** Baseline entries are append-only; updates mean adding new entries (no modification/deletion).
10. **Metadata Integration:** Audit extends gate schema (v0.2.0 or v0.3.0 decision deferred to Task 7); events logged to ci/artifacts/audit-logs/.

---

## Deferred Boundaries (M903 & Beyond)

The following are explicitly **out-of-scope** for M902-07; they belong to Milestone 903 or later:

1. **Enforcement blocking** — M903 enables exit 1 on new violations in blocking mode; M902-07 is shadow-only.
2. **Second-reviewer gate** — M903 implements policy that baseline updates require approval; M902-07 documents manual process.
3. **Auto-remediation tickets** — M903 automates creation of backlog items; M902-07 generates Markdown snippets.
4. **Expiration enforcement** — M903 enforces renewal or deletion of expired entries; M902-07 reports and warns.
5. **Advanced clustering** — M903 may add configurable depth, per-tool tuning, and ML-based grouping.
6. **Secret scanning** — M903 integrates secret detection in baseline validation; M902-07 documents policy.
7. **Dashboard/observability** — M903 may add dashboards to visualize audit trends; M902-07 provides JSON data.
8. **Parallel gate execution** — M903 may parallelize gate invocation; M902-07 uses sequential execution.

---

## References

- **Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/07_governance_audit_pipeline_and_baseline.md`
- **Execution Plan:** `project_board/execution_plans/M902-07_governance_audit_pipeline.md`
- **Planning Checkpoint:** `project_board/checkpoints/M902-07/2026-05-16T00-00-00Z-planning.md`
- **M902-01 Framework:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/01_validation_gate_framework.md` and specs
- **M902-02 Static Analysis:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/02_static_analysis_gate_tooling.md` and specs
- **M902-04 Metadata:** `project_board/specs/902_04_audit_log_spec.md`, `project_board/specs/902_04_handoff_metadata_spec.md`
- **Gate Runner:** `ci/scripts/gate_runner.py`
- **Audit Log Module:** `ci/scripts/audit_log.py`
- **CLAUDE.md:** Repository guardrails (exclusions, conventions)

---

## Spec Exit Gate Check

This spec is type **generic** (per `spec_completeness_check.py` --type generic).

**Spec completeness check command:**
```bash
python ci/scripts/spec_completeness_check.py /Users/jacobbrandt/workspace/blobert/project_board/specs/M902-07_audit_pipeline_spec.md --type generic
```

**Expected outcome:** PASS (generic specs have no required sections; this document covers all functional and non-functional requirements with acceptance criteria).

---

## Checkpoint Log Location

Spec Agent checkpoint decisions and ambiguity resolutions are logged at:
`/Users/jacobbrandt/workspace/blobert/project_board/checkpoints/M902-07/2026-05-16T<run-id>-spec.md`

---

**Document Status:** Complete and ready for TEST_DESIGN stage.

**Last Updated:** 2026-05-16 by Spec Agent

**Revision:** 1

**Next Responsible Agent:** Test Designer Agent

**Stage:** TEST_DESIGN
