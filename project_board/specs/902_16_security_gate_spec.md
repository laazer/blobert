# M902-16 Security Gate Specification

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/16_stage_8_security_gate_integration.md`  
**Milestone:** 902 — Agent Predictability Improvements  
**Spec Agent:** Spec Agent  
**Date:** 2026-05-19  
**Status:** SPECIFICATION (FROZEN v1.0)  
**Revision:** 1

---

## Executive Summary

This specification defines the **Stage 8 Final Security Gate** for blobert's multi-agent governance pipeline. The security gate runs five deterministic security scanning tools (gitleaks, bandit, semgrep, pip-audit, npm audit) and hard-fails on critical violations: secrets detected, unsafe deserialization, authentication bypass patterns, and critical-severity CVEs (CVSS ≥7.0).

The gate integrates into the M902-01 validation framework, runs in **shadow mode** in M902 (non-blocking; enforcement deferred to M903), and outputs structured JSON conforming to the gate schema. All findings must be deterministic: identical staged files produce identical results across runs, with no randomness or network drift.

**Key Constraints:**
- 5 tools mandatory per code_governance.md Stage 8
- Hard-fail conditions: secrets, unsafe deserialization, auth bypass, CVSS ≥7.0
- Soft-fail conditions: CVSS <7.0, medium-severity warnings
- No real secrets in test fixtures (mock only)
- Tool versions pinned in pyproject.toml and package.json
- Deterministic output: no timestamps in decision logic, no network calls
- Gate implementation at `ci/scripts/gates/security_gate_check.py`
- Total execution <120s per gate invocation

---

## Requirement 1: Gitleaks Secrets Detection

### 1. Spec Summary

**Description:** Configure and invoke gitleaks to detect secrets (API keys, tokens, private keys) in staged files. Any secret detected triggers a hard FAIL status. The gate invokes gitleaks as a subprocess, parses JSON output, and records all detected secrets as violations.

**Gitleaks** is a SAST tool that scans git repositories for secrets using pattern matching (built-in rule library). It supports JSON output with detailed match information (file, line, rule name, offending value patterns).

**Constraints:**
- Gitleaks invocation via subprocess: `gitleaks detect --source . --json --report-path <temp>.json --exit-code 1` (or equivalent flags per gitleaks version).
- Must exclude test fixtures, mock secrets, .gitleaksignore, and known false positives.
- Timeout: 10 seconds per invocation.
- Output parsing: JSON format, match array with file/line/rule/secret_type fields.
- Hard-fail rule: any match found → violation recorded, status → FAIL.
- Test fixtures: `.gitleaksignore` or baseline.json for allowlist (if needed).

**Assumptions:**
- Gitleaks is installed and available on PATH or via Homebrew/binary package.
- Built-in gitleaks rule library is current and stable across versions.
- JSON output format is consistent (may vary by gitleaks version; spec freezes version per M902-02 audit).
- Mock secrets in test fixtures are never functional (cannot authenticate to real services).

**Scope:** Applies to all staged files in the repository (git index). Scans Python, JavaScript, Godot, configuration files, and documentation. Excludes: `.git/`, `node_modules/`, `.venv/`, binary files (`.glb`, `.png`, `.jpg`, `.so`), and patterns in `.gitleaksignore`.

### 2. Acceptance Criteria

- **AC-1.1:** Gitleaks binary is discovered or installed; version is pinned (e.g., v8.18.0).
- **AC-1.2:** Gate invocation includes gitleaks subprocess call with JSON output flag and report path.
- **AC-1.3:** Any secret detected is recorded as a violation with fields: file, line, rule (gitleaks rule ID), message (human-readable secret type), severity (ERROR).
- **AC-1.4:** Hard-fail condition met: if violations.length > 0 → status = FAIL.
- **AC-1.5:** Gitleaks subprocess timeout respected: if execution exceeds 10s → gate returns FAIL with timeout violation.
- **AC-1.6:** JSON output parsed without errors; if parsing fails → gate returns FAIL with tool_error violation.
- **AC-1.7:** `.gitleaksignore` or baseline file exists (if needed) and is respected by gitleaks invocation.
- **AC-1.8:** Test fixtures at `tests/ci/fixtures/mock_secrets/` include mock patterns (non-functional) for validation.
- **AC-1.9:** Gate runs gitleaks twice on same staged files (determinism test) → identical violation list.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Real secret accidentally in test fixture | Accidental credential leak to repository | Code review required; gitleaks pre-commit hook validates before commit |
| Gitleaks rule false positives (common patterns in code/comments) | High noise, advisory reporting overhead | `.gitleaksignore` allowlist for documented false positives; M903 grandfathering policy |
| Gitleaks version incompatibility with output format | Output parsing breaks across versions | Spec freezes gitleaks version per M902-02 audit; test fixtures validate parsing |
| Sensitive data in logs (remediation hints expose secret patterns) | Credential leak in build logs | Remediation hints redact actual secret values; only rule names and files logged |

| Ambiguity | Resolution |
|-----------|-----------|
| Should mock secrets be "realistic" (look like real keys) or obviously fake? | Realistic enough to trigger gitleaks rules, but non-functional (cannot authenticate). Documented in fixture README. |
| What if gitleaks is not installed? | Task 2 audit confirms availability; if unavailable in specific environment, checkpoint decision and skip gitleaks (gate still runs other tools). |

### 4. Clarifying Questions

None; gitleaks integration is deterministic and well-documented.

---

## Requirement 2: Bandit Python Security Rules

### 1. Spec Summary

**Description:** Configure and invoke bandit to detect unsafe Python security patterns in Python code under `asset_generation/python/` and `asset_generation/web/backend/`. Bandit checks for unsafe deserialization (pickle, marshal, yaml without Loader), hardcoded secrets (B105-B107), and other CRITICAL/HIGH severity patterns. Hard-fail on critical findings; soft-fail (WARN) on medium/low.

**Bandit** is a static security analyzer for Python that detects common security issues via rule-based AST analysis. Rules are identified by ID (B201, B301-B303, etc.) and have severity levels (HIGH, MEDIUM, LOW).

**Constraints:**
- Bandit invocation: `bandit -r <target-dirs> -f json` (or equivalent flags per version).
- Target directories: `asset_generation/python/src/`, `asset_generation/web/backend/` (both code and test directories, unless excluding test fixtures separately).
- Hard-fail rules (critical): B201 (Flask debug mode), B301-B303 (pickle/marshal/yaml unsafe deserialization), B105-B107 (hardcoded secrets), B602 (paramiko shell injection), others per code_governance.md Stage 8.
- Soft-fail rules (medium/low): B110-B112 (try/except too broad), B404-B407 (import restrictions), others.
- Severity mapping: BANDIT HIGH → gate violation severity ERROR, BANDIT MEDIUM → WARN, BANDIT LOW → INFO.
- Timeout: 30 seconds per invocation.
- Output: JSON format with issue list containing issue_text, severity, test_id (rule ID), line_number, filename.
- Test fixtures: `tests/ci/fixtures/bandit_unsafe_patterns/` with Python files demonstrating unsafe patterns.

**Assumptions:**
- Bandit is installed as dev dependency in `asset_generation/python/pyproject.toml`.
- Bandit rule IDs are stable across versions (pinned version per M902-02 audit).
- JSON output format is deterministic (same code → same rule violations).
- Bandit does not flag test code differently unless explicitly configured (no separate test exclusion in M902).

**Scope:** Python code in `asset_generation/python/` (source and tests), `asset_generation/web/backend/` (FastAPI backend), and any Python scripts under `scripts/`, `ci/`, etc. Excludes: `.venv/`, `node_modules/`, `.glb`, generated exports.

### 2. Acceptance Criteria

- **AC-2.1:** Bandit is listed as dev dependency in `asset_generation/python/pyproject.toml` with pinned version (e.g., bandit>=1.7.5,<2.0).
- **AC-2.2:** Bandit configuration (`.bandit` or `pyproject.toml [tool.bandit]`) defines hard-fail rules (B201, B301-B303, B105-B107, etc.) and severity thresholds.
- **AC-2.3:** Gate invocation includes bandit subprocess call with JSON output flag, targeting `asset_generation/python/` and `asset_generation/web/backend/`.
- **AC-2.4:** Each bandit finding is recorded as a violation with fields: file, line, rule (test_id), message, severity (mapped from BANDIT severity).
- **AC-2.5:** Hard-fail condition: if any violation has severity ERROR (mapped from BANDIT HIGH on hard-fail rules) → status = FAIL.
- **AC-2.6:** Soft-fail condition: if all violations have severity WARN or INFO → status = WARN (does not trigger FAIL unless combined with other failures).
- **AC-2.7:** Bandit subprocess timeout respected: if execution exceeds 30s → gate returns FAIL with timeout violation.
- **AC-2.8:** JSON output parsed without errors; if parsing fails → gate returns FAIL with tool_error violation.
- **AC-2.9:** Test fixtures at `tests/ci/fixtures/bandit_unsafe_patterns/` include valid Python files demonstrating B201, B301-B303, B105-B107 patterns.
- **AC-2.10:** Determinism test: gate runs bandit twice on same files → identical violation list.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Bandit detects false positives (legitimate subprocess, intentional hardcoded test passwords) | High noise, advisory overhead | Spec freezes bandit version; test fixtures validate known patterns are detected; baseline violations documented for M903 grandfathering |
| Bandit rule severity misalignment (library marks B301 as MEDIUM but we want HARD FAIL) | Hard-fail rules may not actually cause FAIL | Spec freezes rule → severity mapping per bandit version; tests validate mapping |
| Fixture files contain real security risks if executed | Risk if someone runs fixtures as code | Fixtures are analysis-only (never executed); documented in README; runtime guards prevent execution |

| Ambiguity | Resolution |
|-----------|-----------|
| Should bandit scan test directories or exclude them? | Include test directories in M902 (shadow mode allows advisory); M903 can refine exclusions per policy. |
| What if bandit is not installed? | Task 2 audit confirms availability; if unavailable, checkpoint and skip bandit. |

### 4. Clarifying Questions

None; bandit integration follows established patterns from M902-02.

---

## Requirement 3: Semgrep Security Rules

### 1. Spec Summary

**Description:** Configure and invoke semgrep with local security rules (no remote registry) to detect critical patterns: authentication bypass (conditional auth checks, token validation skips), unsafe deserialization (pickle/yaml/JSON eval on untrusted input), SQL injection (unsanitized queries), and hardcoded secrets. Hard-fail on CRITICAL/HIGH severity; soft-fail on MEDIUM/LOW.

**Semgrep** is a fast static analysis tool supporting Python, JavaScript/TypeScript, and other languages via pattern-matching rules (YAML-defined or registry-based). M902-16 uses **local `.semgrep.yml`** only (no remote registry, no internet calls).

**Constraints:**
- Semgrep invocation: `semgrep --config .semgrep.yml <target-dirs> --json` (or equivalent flags per version).
- Configuration: `.semgrep.yml` at repo root defining local hardcoded rules with severity levels (CRITICAL, HIGH, MEDIUM, LOW).
- Rule categories required:
  1. **Auth bypass patterns:** Flask/Django decorator bypasses, conditional token validation skips, hardcoded permission checks.
  2. **Unsafe deserialization:** pickle.loads/dumps on untrusted data, yaml.load without Loader, json.loads with eval.
  3. **SQL injection:** Unsanitized string concatenation in queries, missing parameterization.
  4. **Hardcoded secrets:** API keys, tokens, passwords in source code.
- Severity mapping: SEMGREP CRITICAL/HIGH → gate violation severity ERROR, SEMGREP MEDIUM → WARN, SEMGREP LOW → INFO.
- Target languages: Python and JavaScript/TypeScript.
- Target directories: `asset_generation/python/`, `asset_generation/web/backend/`, `asset_generation/web/frontend/`, `scripts/`.
- Timeout: 60 seconds per invocation.
- Output: JSON format with results array containing rule, message, path, start/end lines.
- Test fixtures: `tests/ci/fixtures/semgrep_patterns/` with Python and JS files demonstrating each pattern category.

**Assumptions:**
- Semgrep is installed (Python package or standalone binary; version pinned per M902-02 audit).
- Local `.semgrep.yml` rules are hand-curated and conservative (avoid false positives).
- Semgrep rule syntax is stable across versions.
- No internet connectivity required; all rules are local.

**Scope:** Python code, JavaScript/TypeScript code, configuration files. Excludes: test fixtures in `.semgrep.yml` (can be overridden locally), `node_modules/`, `.venv/`, binary files, reference_projects.

### 2. Acceptance Criteria

- **AC-3.1:** Semgrep is installed (package or binary) with version pinned per M902-02 audit.
- **AC-3.2:** `.semgrep.yml` exists at repo root defining ≥4 local rule categories (auth bypass, unsafe deserialization, SQL injection, hardcoded secrets).
- **AC-3.3:** Each rule has explicit severity level (CRITICAL, HIGH, MEDIUM, LOW) and human-readable message.
- **AC-3.4:** Gate invocation includes semgrep subprocess call with `--config .semgrep.yml` flag, JSON output, targeting multi-language directories.
- **AC-3.5:** Each semgrep finding is recorded as a violation with fields: file, line, rule (rule ID from .semgrep.yml), message, severity (mapped from semgrep severity).
- **AC-3.6:** Hard-fail condition: if any violation has severity ERROR (CRITICAL/HIGH semgrep rules) → status = FAIL.
- **AC-3.7:** Soft-fail condition: if all violations have severity WARN or INFO → status = WARN.
- **AC-3.8:** Semgrep subprocess timeout respected: if execution exceeds 60s → gate returns FAIL with timeout violation.
- **AC-3.9:** JSON output parsed without errors; if parsing fails → gate returns FAIL with tool_error violation.
- **AC-3.10:** Test fixtures at `tests/ci/fixtures/semgrep_patterns/` include Python and JS files demonstrating each rule category.
- **AC-3.11:** Determinism test: gate runs semgrep twice on same files → identical violation list.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Semgrep rule false positives (overly strict patterns) | High noise, advisory overhead | Rules are hand-curated; test fixtures validate detection; baseline documented for M903 |
| Semgrep slow on large codebases (can exceed 60s timeout) | Gate timeout occurs frequently | Spec limits rule scope to critical patterns only; timeout at 60s; M903 can parallelize |
| Local rule maintenance burden (curating rules by hand) | Rules may drift out of sync with threats | Spec freezes rules; M903 establishes review process; consider registry migration later |

| Ambiguity | Resolution |
|-----------|-----------|
| Should `.semgrep.yml` be at repo root or under `asset_generation/`? | Repo root (applies globally across Python + JS; supports rule reuse). |
| What if semgrep is not installed? | Task 2 audit confirms availability; if unavailable, checkpoint and skip semgrep. |

### 4. Clarifying Questions

None; semgrep rule structure is well-documented; local YAML syntax is standard.

---

## Requirement 4: Dependency Vulnerability Audit (pip-audit + npm audit)

### 1. Spec Summary

**Description:** Run pip-audit on Python dependencies and npm audit on JavaScript dependencies to detect known CVEs. Hard-fail on critical CVSS scores (≥7.0); soft-fail on medium/low (CVSS <7.0). Both tools compare installed packages against CVE databases and report vulnerabilities.

**pip-audit** scans a Python environment (virtual or system) and reports CVEs in installed packages from PyPI advisory database. **npm audit** scans node_modules against npm public registry advisories.

**Constraints:**
- **pip-audit invocation:** `pip-audit --format json --desc --skip-vulnerable` (flags per version; --format json for deterministic output).
  - Target: Python virtual environment from `asset_generation/python/` (activated via `uv sync`).
  - Offline mode: use cached advisories if network unavailable; fallback to mock responses for testing.
  - Timeout: 20 seconds.
  - Output: JSON with vulnerabilities array containing CVE ID, advisory title, severity, CVSS score, affected package, fixed version.

- **npm audit invocation:** `npm audit --json --production` (flags per version; --production excludes dev dependencies in some cases; adjust per policy).
  - Target: `asset_generation/web/frontend/` (node_modules from package.json).
  - Offline mode: use cached registry if available; allow npm registry cache.
  - Timeout: 20 seconds.
  - Output: JSON with vulnerabilities object keyed by package name, containing CVSS score, severity, advisory.

- **CVSS Threshold Mapping:**
  - CVSS ≥7.0 (high/critical): hard-fail → status FAIL, severity ERROR.
  - CVSS 4.0–6.9 (medium): soft-fail → status WARN, severity WARN.
  - CVSS <4.0 (low): info only → severity INFO.

- **Test Fixtures:** `tests/ci/fixtures/vulnerable_packages/` with:
  - `pip_vulnerable_packages.txt`: list of PyPI packages with known CVEs (e.g., test packages if available; or mock CVE responses).
  - `npm_vulnerable_packages.json`: mock package.json with vulnerable dependencies for isolated npm audit runs.
  - Strategy: test harness creates isolated venv/npm contexts, runs audits, validates detection (never pollutes main dependencies).

**Assumptions:**
- pip-audit and npm audit are available in CI/local environment.
- CVSS v3.1 scoring is standard across CVE databases.
- Offline mode or cached advisories are acceptable (no live network calls required in M902).
- Test packages with known CVEs are available (either real packages or mock responses).

**Scope:** All Python packages in `asset_generation/python/pyproject.toml`, all npm packages in `asset_generation/web/frontend/package.json` (including transitive dependencies). Excludes: dev-only dependencies (depending on policy; spec includes both in M902).

### 2. Acceptance Criteria

- **AC-4.1:** pip-audit is available in Python environment (installed or as command-line tool); version documented per M902-02 audit.
- **AC-4.2:** npm audit is available (npm built-in); npm and node versions documented.
- **AC-4.3:** Gate invocation includes pip-audit subprocess call with `--format json`, targeting activated Python venv from `asset_generation/python/`.
- **AC-4.4:** Gate invocation includes npm audit subprocess call with `--json`, targeting `asset_generation/web/frontend/`.
- **AC-4.5:** Each CVE vulnerability is recorded as a violation with fields: file (package name), rule (CVE ID), message (advisory title + CVSS score), severity (mapped from CVSS score).
- **AC-4.6:** Hard-fail condition: if any violation has CVSS ≥7.0 → status = FAIL.
- **AC-4.7:** Soft-fail condition: if all violations have CVSS <7.0 → status = WARN.
- **AC-4.8:** pip-audit subprocess timeout respected: if execution exceeds 20s → gate returns FAIL with timeout violation.
- **AC-4.9:** npm audit subprocess timeout respected: if execution exceeds 20s → gate returns FAIL with timeout violation.
- **AC-4.10:** JSON output parsed without errors; if parsing fails → gate returns FAIL with tool_error violation.
- **AC-4.11:** CVSS score mapping is deterministic: same CVSS score → same severity every time.
- **AC-4.12:** Test fixtures at `tests/ci/fixtures/vulnerable_packages/` include test data for pip-audit and npm audit validation.
- **AC-4.13:** Determinism test: gate runs both audits twice on same files → identical violation list.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dependency audits require network (PyPI, npm registry) | CI may have network isolation; audit fails offline | Spec defines offline mode (cached advisories); M903 documents fallback strategy |
| Test packages with known CVEs may be delisted from registries | Fixtures cannot use real packages; test harness fails | Spec uses mock CVE responses for testing; real package scanning validated in integration tests |
| Transitive dependency explosion (many CVEs from deep dependency trees) | High volume of findings; many false positives (indirect, unpatched upstream) | CVSS ≥7.0 threshold filters critical only; M903 establishes grandfathering + ignore policies |
| CVSS score drift (CVE database updates scores retroactively) | Same package → different severity on different dates | Spec freezes baseline per M902-02 audit; M903 documents update cadence |

| Ambiguity | Resolution |
|-----------|-----------|
| Should dev dependencies be included in npm audit? | Include in M902 (shadow mode); M903 can refine to prod-only if needed. |
| How to handle unavailable packages in test fixtures? | Use mock CVE JSON responses; real integration tests validate against actual packages if available. |

### 4. Clarifying Questions

None; dependency audit tools are mature and well-documented.

---

## Requirement 5: Severity Thresholds and Fail/Warn/Pass Decision Matrix

### 1. Spec Summary

**Description:** Define the deterministic decision logic that routes violations into hard-fail (FAIL), soft-fail (WARN), and pass (PASS) status. The gate aggregates findings from all 5 tools and applies a severity cascade: secrets and unsafe patterns take priority over CVEs; hard-fail rules always trigger FAIL; soft-fail rules only trigger WARN if no hard-fail rules are present.

**Decision Logic (Deterministic Cascade):**

1. **Secrets detected (gitleaks):** Any secret → FAIL (highest priority).
2. **Unsafe deserialization (bandit B301-B303, semgrep rules):** Any finding → FAIL.
3. **Auth bypass patterns (semgrep):** Any finding → FAIL.
4. **CVSS ≥7.0 (pip-audit, npm audit):** Any finding → FAIL.
5. **CVSS 4.0–6.9 or medium-severity bandit/semgrep:** Any finding → WARN (if no hard-fail above).
6. **CVSS <4.0 or low-severity:** INFO only (does not affect status).
7. **No findings:** PASS.

**Severity Threshold Table:**

| Tool | Pattern/Finding | Severity | Status |
|------|-----------------|----------|--------|
| **gitleaks** | Secret detected | ERROR | FAIL |
| **bandit** | B201 (Flask debug), B301-B303 (unsafe deserialize), B105-B107 (hardcoded secret) | ERROR | FAIL |
| **bandit** | B110-B112 (except too broad), B404-B407 (imports) | WARN | WARN |
| **semgrep** | Auth bypass, unsafe deserialize (CRITICAL/HIGH) | ERROR | FAIL |
| **semgrep** | Medium patterns | WARN | WARN |
| **pip-audit / npm audit** | CVSS ≥7.0 | ERROR | FAIL |
| **pip-audit / npm audit** | CVSS 4.0–6.9 | WARN | WARN |
| **pip-audit / npm audit** | CVSS <4.0 | INFO | (no status change) |

**Constraints:**
- Status is deterministic: same violations always produce same status.
- No timestamps or randomness in decision logic.
- Status field: `"PASS"`, `"WARN"`, or `"FAIL"` (string enum).
- Violations array ordered by severity (ERROR first, then WARN, then INFO).
- Remediation hints provided per violation type (e.g., "run `git reset HEAD <file>` to unstage secrets", "remove hardcoded password from source").

**Assumptions:**
- Hard-fail conditions are non-negotiable (enforced per code_governance.md Stage 8).
- Soft-fail (WARN) allows advisory reporting without CI breakage (shadow mode in M902).
- Status cascade is stable across gate runs (no randomness).

**Scope:** Applies to all violations from all 5 tools; aggregated by gate orchestrator.

### 2. Acceptance Criteria

- **AC-5.1:** Decision matrix is documented in spec with tool → severity → status mapping.
- **AC-5.2:** Status is deterministic: running gate twice on same files → same status.
- **AC-5.3:** Violations array is sorted by severity (ERROR > WARN > INFO).
- **AC-5.4:** Any gitleaks secret match → FAIL (highest priority, rule out other tools).
- **AC-5.5:** Any bandit B301-B303 or semgrep auth bypass → FAIL.
- **AC-5.6:** Any CVSS ≥7.0 CVE → FAIL.
- **AC-5.7:** CVSS 4.0–6.9 or WARN-severity patterns (no hard-fail above) → WARN.
- **AC-5.8:** No violations → PASS.
- **AC-5.9:** Remediation hints are provided for each violation type (e.g., file path, rule ID, actionable fix).
- **AC-5.10:** Tests validate decision matrix: parametrized tests cover all combinations (secret + CVE, CVE only, no violations, etc.).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Decision matrix complexity (5 tools, cascading logic) | Hard to maintain; bugs in priority logic | Spec freezes matrix; tests parametrize all cases; implementation comments explain cascade |
| Status change when tools update (bandit rule severity changes) | Unexpected FAIL/WARN status shifts | Tool versions pinned; M903 establishes update cadence; changelog reviewed before version bump |

| Ambiguity | Resolution |
|-----------|-----------|
| If secret + CVE ≥7.0 detected, which takes priority? | Secret always triggers FAIL first (hard-fail cascade). |
| Should WARN status block commits in shadow mode? | No; shadow mode always exits 0 (non-blocking). Enforcement in M903. |

### 4. Clarifying Questions

None; decision matrix is straightforward and deterministic.

---

## Requirement 6: Gate Output Contract (M902-01 Schema Integration)

### 1. Spec Summary

**Description:** The security gate returns a JSON object conforming to the M902-01 gate success/failure schema. The schema includes standard fields (status, timestamp, artifacts, duration_ms) plus security-specific fields (violations[], remediation_hints[], tool_statuses[]).

**Output Structure:**

```json
{
  "version": "1.0",
  "status": "PASS|WARN|FAIL",
  "gate": "security_gate_check",
  "upstream_agent": "<agent-name>",
  "downstream_agent": "<agent-name>",
  "ticket_id": "<ticket-id>",
  "timestamp": "2026-05-19T10:30:00Z",
  "mode": "shadow|blocking",
  "_shadow_mode": true|false,
  "duration_ms": <integer>,
  "message": "<summary>",
  "artifacts": [
    { "path": "ci/scripts/gates/security_gate_check.py", "sha256": "<hash>" },
    { "path": ".semgrep.yml", "sha256": "<hash>" }
  ],
  "violations": [
    {
      "file": "<relative-path>",
      "line": <integer or null>,
      "rule": "<rule-id>",
      "message": "<human-readable>",
      "severity": "ERROR|WARN|INFO"
    }
  ],
  "remediation_hints": [
    "<actionable fix 1>",
    "<actionable fix 2>"
  ],
  "tool_statuses": [
    {
      "name": "gitleaks",
      "exit_code": 0|1|2,
      "findings_count": <integer>,
      "timeout": false|true,
      "error": null|"<error message>"
    },
    { "name": "bandit", "..." },
    { "name": "semgrep", "..." },
    { "name": "pip-audit", "..." },
    { "name": "npm-audit", "..." }
  ]
}
```

**Constraints:**
- JSON is valid and parseable by standard JSON parsers.
- `version` field is string "1.0" (matches M902-01 schema version).
- `status` must be one of: "PASS", "WARN", "FAIL" (enum).
- `timestamp` is ISO 8601 format (e.g., 2026-05-19T10:30:00Z).
- `duration_ms` is wall-clock time from gate start to end (integer milliseconds).
- `message` summarizes findings (e.g., "1 secret, 2 unsafe patterns detected" for FAIL).
- `violations` array ordered by severity (ERROR, WARN, INFO).
- `remediation_hints` are actionable strings (file paths, rule IDs, fix suggestions).
- `tool_statuses` array includes all 5 tools, even if some timed out or were skipped.
- `_shadow_mode` boolean mirrors `mode` field for debugging.
- `artifacts` array includes paths to gate configuration files (e.g., `.semgrep.yml`, `.bandit`, gate implementation).

**Assumptions:**
- Gate runner (M902-01) handles JSON serialization of results; gate module returns dict conforming to schema.
- Timestamps are UTC (no timezone conversion).
- SHA-256 hashing is done by gate runner or gate module (spec does not prescribe location).

**Scope:** All gate outputs must conform; no exceptions.

### 2. Acceptance Criteria

- **AC-6.1:** Gate returns JSON object with all required fields from M902-01 schema + security-specific extensions (violations, remediation_hints, tool_statuses).
- **AC-6.2:** JSON is valid (parseable by `json.loads()` or equivalent without errors).
- **AC-6.3:** `status` field is one of "PASS", "WARN", "FAIL".
- **AC-6.4:** `timestamp` is ISO 8601 format (regex: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`).
- **AC-6.5:** `violations` array has each element with required fields: file, line (or null), rule, message, severity.
- **AC-6.6:** `tool_statuses` array includes exactly 5 objects, one per tool (gitleaks, bandit, semgrep, pip-audit, npm-audit), with fields: name, exit_code, findings_count, timeout, error.
- **AC-6.7:** If a tool timed out, `tool_statuses[i].timeout = true` and error message is recorded.
- **AC-6.8:** If a tool crashed/errored, `tool_statuses[i].error` contains error message (no exception traceback, only human-readable summary).
- **AC-6.9:** `duration_ms` reflects total wall-clock time; timeouts are included in duration.
- **AC-6.10:** Tests validate schema compliance: example JSON conforming to M902-01 schema + security extensions is validated via schema validator or type checks.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| JSON schema version mismatch (future M902-01 updates) | Output may become incompatible with orchestrator | Spec freezes version; M903 establishes schema versioning + migration strategy |
| SHA-256 hashing of large files (artifacts array bloat) | Output size grows; slow hashing | Skip hashing files >10MB; record sha256: null with note |

| Ambiguity | Resolution |
|-----------|-----------|
| Should violations include detailed context (e.g., code snippet)? | No; file/line/message suffice. M903 can extend with context if needed. |
| Should error messages include stack traces? | No; only summary. Stack traces logged separately for debugging. |

### 4. Clarifying Questions

None; schema is inherited from M902-01 and well-defined.

---

## Requirement 7: Tool Configuration and Scope

### 1. Spec Summary

**Description:** Define tool invocation paths, command-line flags, target directories, exclusion patterns, and version constraints for all 5 tools. This requirement freezes the exact configuration used by the gate during M902-16 implementation.

**Tool Configurations:**

### 7.1 Gitleaks

**Installation:** Homebrew binary or standalone from https://github.com/gitleaks/gitleaks/releases (version pinned per M902-02 audit; e.g., v8.18.0).

**Command:**
```bash
gitleaks detect --source . --json --report-path <temp-report>.json --exit-code 1 2>/dev/null
```

**Flags:**
- `--source .`: scan current repo (or specific directory).
- `--json`: output JSON format.
- `--report-path`: write report to file (gate reads file after completion).
- `--exit-code 1`: exit with code 1 if leaks found (gate checks exit code).

**Scope:** All staged files in git index (repo root).

**Exclusions:** `.git/`, binary files (`.glb`, `.so`, `.o`), large generated files (`.png`, `.jpg` over 1MB), node_modules, .venv, reference_projects.

**Baseline:** `.gitleaksignore` file in repo root (optional; documents known false positives).

### 7.2 Bandit

**Installation:** Python package from PyPI; version constraint in `asset_generation/python/pyproject.toml` (e.g., bandit>=1.7.5,<2.0).

**Command:**
```bash
bandit -r asset_generation/python/ asset_generation/web/backend/ -f json --exit-code 1 2>/dev/null
```

**Flags:**
- `-r`: recursive (scan directories).
- `-f json`: JSON output format.
- `--exit-code 1`: exit with code 1 if issues found.

**Configuration File:** `.bandit` in `asset_generation/python/` or `[tool.bandit]` in `pyproject.toml` defining severity thresholds and hard-fail rules.

**Scope:** Python source files in `asset_generation/python/src/`, `asset_generation/web/backend/`, and other Python scripts.

**Exclusions:** `.venv/`, `__pycache__/`, test fixtures (optional; included in M902), `.glb`.

### 7.3 Semgrep

**Installation:** Python package or binary; version pinned per M902-02 audit (e.g., semgrep>=1.50,<2.0).

**Command:**
```bash
semgrep --config .semgrep.yml asset_generation/python/ asset_generation/web/backend/ asset_generation/web/frontend/ --json --strict 2>/dev/null
```

**Flags:**
- `--config .semgrep.yml`: use local rule file (no remote registry).
- `--json`: JSON output format.
- `--strict`: fail on parse errors (no silent skips).

**Configuration File:** `.semgrep.yml` at repo root defining local hardcoded rules with severities.

**Scope:** Python, JavaScript/TypeScript files in `asset_generation/`, `scripts/`, `ci/`.

**Exclusions:** `node_modules/`, `.venv/`, `.git/`, `reference_projects/`, test fixtures (optional).

### 7.4 pip-audit

**Installation:** Python package; version pinned in `asset_generation/python/pyproject.toml` (e.g., pip-audit>=2.6,<3.0).

**Command:**
```bash
cd asset_generation/python && pip-audit --format json --desc 2>/dev/null
```

**Flags:**
- `--format json`: JSON output.
- `--desc`: include advisory descriptions (human-readable).

**Invocation Context:** Requires activated Python venv from `asset_generation/python/` (gate activates via `source .venv/bin/activate` or equivalent).

**Scope:** All packages in Python venv (from pyproject.toml + uv.lock).

### 7.5 npm audit

**Installation:** npm built-in (npm 8+); no separate installation needed.

**Command:**
```bash
cd asset_generation/web/frontend && npm audit --json --production 2>/dev/null
```

**Flags:**
- `--json`: JSON output.
- `--production`: prod dependencies only (or all; spec allows both; M903 can refine).

**Invocation Context:** Requires node_modules from `package.json` + package-lock.json.

**Scope:** All packages in `asset_generation/web/frontend/node_modules/`.

### Tool Version Constraints (Frozen per M902-02 Audit)

| Tool | Version Constraint | Rationale |
|------|-------------------|-----------|
| **gitleaks** | v8.18.0 (or latest stable) | Latest production release; JSON format stable |
| **bandit** | >=1.7.5,<2.0 | Rule IDs stable in 1.x series |
| **semgrep** | >=1.50,<2.0 | Performance improvements in 1.50+ |
| **pip-audit** | >=2.6,<3.0 | JSON format stable in 2.x series |
| **npm audit** | npm >=8.0,<10.0 | Built-in; no separate install |

**Timeout Per Tool:**

| Tool | Timeout | Rationale |
|------|---------|-----------|
| gitleaks | 10s | Fast pattern matching |
| bandit | 30s | AST analysis on Python codebase |
| semgrep | 60s | Slow on large codebases |
| pip-audit | 20s | Quick DB lookup |
| npm audit | 20s | Quick registry check |
| **Total (aggregate)** | **120s** | Sum of all timeouts (parallel not assumed in M902) |

### Exclusion Pattern Reference (Per CLAUDE.md)

**Global exclusions applied to all tools:**
- `*.glb` (binary Blender models)
- `*.png`, `*.jpg` (generated image exports >1MB)
- `.venv/` (Python virtual environment)
- `node_modules/` (npm packages)
- `.git/` (git metadata)
- `reference_projects/` (read-only reference material)
- `asset_generation/python/animated_exports/` (generated model exports)
- Generated lockfiles (handled separately; pip-audit/npm audit manage them)

**Per-Tool Specifics:**
- **gitleaks:** respects `.gitleaksignore` (if present).
- **bandit:** respects `# noqa: B###` comments (inline suppression).
- **semgrep:** respects `# nosemgrep` comments; `.semgrep.yml` can define rule-specific exclusions.
- **npm audit:** respects `.npmignore` (standard npm behavior).

### 2. Acceptance Criteria

- **AC-7.1:** Gitleaks command documented with exact flags; version constraint specified and justified.
- **AC-7.2:** Bandit command documented; configuration file (`.bandit` or pyproject.toml) specified with hard-fail rule list.
- **AC-7.3:** Semgrep command documented; `.semgrep.yml` file location and local rule strategy specified.
- **AC-7.4:** pip-audit command documented; venv activation strategy specified.
- **AC-7.5:** npm audit command documented; invocation from `asset_generation/web/frontend/` specified.
- **AC-7.6:** All timeout values (per-tool and aggregate) documented and justified.
- **AC-7.7:** Exclusion patterns documented per tool and cross-referenced to CLAUDE.md.
- **AC-7.8:** Tool version constraints are frozen and pinned in dependency files (pyproject.toml, package.json, or external binary version).
- **AC-7.9:** All config files (`.bandit`, `.semgrep.yml`, jscpd.json if applicable) are valid and syntax-checked during implementation.
- **AC-7.10:** Commands are deterministic: same staged files → same tool output across multiple runs (no randomness, no network drift).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tool binary unavailable in CI environment | Gate fails to run | Task 2 audit confirms availability; M903 establishes fallback (skip tool, log warning) |
| Timeout values insufficient for large codebases | Gate timeouts in CI; tests don't catch performance regressions | Timeout values based on execution plan Task 1 estimates; integration tests (Task 11) validate timing; M903 can tune |
| Exclusion patterns incomplete (accidentally scans generated files) | Noisy findings; false positives | Spec defines comprehensive exclusion list per CLAUDE.md; test fixtures validate exclusions are respected |

| Ambiguity | Resolution |
|-----------|-----------|
| Should tools run in parallel or sequentially? | Sequential in M902 (simpler implementation); M903 can parallelize if timeout becomes issue. |
| What if a tool is not installed? | Checkpoint decision per Task 2; skip tool and log warning; gate continues with remaining tools. |

### 4. Clarifying Questions

None; tool configuration is deterministic and documented per vendor specifications.

---

## Requirement 8: Test Fixture Strategy and Determinism

### 1. Spec Summary

**Description:** Define the test fixtures used to validate that each security scanning tool detects intended vulnerabilities correctly. Fixtures are mock (non-functional) and used only for testing, never committed as production code. The fixture strategy ensures determinism: same fixtures run multiple times produce identical findings.

**Fixture Categories:**

### 8.1 Mock Secrets (Gitleaks Testing)

**Location:** `tests/ci/fixtures/mock_secrets/`

**Files:**
- `mock_aws_key.txt`: Fake AWS access key pattern (e.g., `AKIA...` format, non-functional).
- `mock_private_key.pem`: Fake RSA private key header + body (non-functional).
- `mock_github_token.txt`: Fake GitHub token pattern (e.g., `ghp_...` format, non-functional).
- `mock_stripe_api.txt`: Fake Stripe API key pattern (e.g., `sk_test_...`, non-functional).
- `README.md`: **CRITICAL:** Documents "MOCK SECRETS FOR TESTING ONLY — NOT FUNCTIONAL — CANNOT ACCESS REAL SERVICES".

**Fixture Validation:** Each mock secret matches a gitleaks rule but is non-functional (cannot authenticate to real service). Test harness: creates temporary git repo, stages mock secret files, runs gitleaks, validates detection.

**Determinism:** Same mock files → gitleaks always detects same rules (deterministic rule matching).

### 8.2 Unsafe Python Patterns (Bandit Testing)

**Location:** `tests/ci/fixtures/bandit_unsafe_patterns/`

**Files:**
- `unsafe_pickle.py`: Demonstrates `pickle.loads(untrusted_data)` (B301, unsafe deserialization).
- `unsafe_yaml.py`: Demonstrates `yaml.load(data)` without `Loader` (B506, unsafe YAML).
- `unsafe_deserialization.py`: Demonstrates `marshal.loads(data)` (B303).
- `hardcoded_secret.py`: Demonstrates `password = "admin123"` hardcoded (B105, hardcoded password).
- `unsafe_exec.py`: Demonstrates `eval(user_input)` (B102, arbitrary code execution).
- `README.md`: Documents which rule ID each file triggers.

**Fixture Validation:** Each file is syntactically valid Python (can be imported); when bandit analyzes file, expected rule ID is detected. Test harness: imports fixture, runs bandit on it, validates expected violation appears.

**Determinism:** Same Python files → bandit always detects same rule IDs (deterministic AST analysis).

### 8.3 Security Pattern Code (Semgrep Testing)

**Location:** `tests/ci/fixtures/semgrep_patterns/`

**Files:**
- `auth_bypass.py`: Demonstrates conditional auth check bypass (e.g., `if user.is_admin: return data` without further validation, semgrep rule detects).
- `unsafe_deserialize.js`: Demonstrates `eval(json_string)` or `JSON.parse` with unsafe usage (semgrep rule detects).
- `sql_injection.py`: Demonstrates unsanitized SQL: `query = f"SELECT * FROM users WHERE id={user_id}"` (semgrep rule detects).
- `hardcoded_api_key.js`: Demonstrates `const API_KEY = "sk_test_..."` hardcoded (semgrep rule detects).
- `README.md`: Documents which rule each file triggers.

**Fixture Validation:** Each file matches a `.semgrep.yml` rule. Test harness: runs semgrep on fixture, validates expected rule match appears.

**Determinism:** Same code files → semgrep always detects same rules (deterministic pattern matching).

### 8.4 Vulnerable Package Lists (Dependency Audit Testing)

**Location:** `tests/ci/fixtures/vulnerable_packages/`

**Files:**
- `pip_vulnerable_packages.txt`: List of PyPI packages with known CVEs (format: `package-name==version`, one per line). Example: `insecure-package==1.0.0` (if such a test package exists with published CVE). If real packages unavailable, use mock CVE JSON responses in test.
- `npm_vulnerable_packages.json`: Mock `package.json` with vulnerable dependencies (e.g., `"old-package": "1.0.0"` where 1.0.0 has published CVEs).
- `README.md`: Documents "TEST FIXTURES ONLY — Never added to main dependencies — Isolated test environments only".

**Fixture Validation:** Test harness creates isolated venv/npm context, installs packages from fixture list, runs pip-audit/npm audit, validates CVE detection.

**Determinism:** Same package lists → audit tools always report same CVEs (deterministic DB lookup; assumes stable advisory DB snapshot per version).

### 8.5 Determinism Validation Strategy

**Test Pattern (applies to all tools):**

```python
def test_determinism_gitleaks():
    # Run gitleaks on mock_secrets fixture twice
    result1 = run_gitleaks(fixture_dir="tests/ci/fixtures/mock_secrets/")
    result2 = run_gitleaks(fixture_dir="tests/ci/fixtures/mock_secrets/")
    
    # Assert same violations
    assert result1.violations == result2.violations
    assert result1.status == result2.status
```

**Determinism Constraints:**
- No timestamps in findings comparison (compare only rule/file/line/message).
- No network calls (offline advisory DB, cached registry).
- Tool versions pinned (same binary → same output).
- Same input files → identical violation list (order, count, rule IDs).

### 2. Acceptance Criteria

- **AC-8.1:** Mock secret fixtures created at `tests/ci/fixtures/mock_secrets/` with ≥4 types (AWS, GitHub, private key, Stripe); each documented as MOCK in README.
- **AC-8.2:** Unsafe Python pattern fixtures created at `tests/ci/fixtures/bandit_unsafe_patterns/` with ≥5 files demonstrating hard-fail rules (B301-B303, B105-B107, etc.).
- **AC-8.3:** Semgrep pattern fixtures created at `tests/ci/fixtures/semgrep_patterns/` with ≥4 code samples (auth bypass, unsafe deserialize, SQL injection, hardcoded secret).
- **AC-8.4:** Vulnerable package fixtures created at `tests/ci/fixtures/vulnerable_packages/` with pip and npm test lists or mock CVE responses.
- **AC-8.5:** All fixture READMEs explicitly state "TESTING ONLY — NOT FUNCTIONAL — NEVER IN PRODUCTION".
- **AC-8.6:** All fixture files are syntactically valid (Python fixtures parseable by Python AST; JSON fixtures valid JSON).
- **AC-8.7:** Determinism test exists for each tool: running gate twice on same fixture → identical violations (order, count, rule IDs match).
- **AC-8.8:** Test harness strategy documented: how mock secrets are staged (temp git repo), how fixtures are isolated (separate venv/npm context), how findings are validated.
- **AC-8.9:** No fixture contains real secrets or functional keys that could authenticate to real services.
- **AC-8.10:** Fixtures are checked into repo (not generated dynamically); SHA-256 hashes are stable across runs.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mock secrets accidentally look too much like real keys | Risk of accidental copy-paste to production | README explicitly marks as MOCK; test harness never executes code; code review required before commit |
| Fixture package versions become outdated (CVEs fixed) | Audit tests no longer detect expected CVEs | Spec documents baseline CVEs; M903 establishes update cadence; mock responses fallback if real packages updated |
| Determinism breaks if tool versions change | Same fixtures produce different output | Tool versions pinned in dependencies; M903 establishes version update policy |

| Ambiguity | Resolution |
|-----------|-----------|
| Should fixtures be extensive (many examples) or minimal (just enough to test)? | Minimal + comprehensive: ≥4-5 per tool covering key hard-fail rules. More extensive in M903 if needed. |
| How to handle Python fixtures that use unsafe patterns (never executed)? | Fixtures are analysis-only; never executed by test harness; documented clearly in README. |

### 4. Clarifying Questions

None; fixture strategy is well-defined and security-conscious.

---

## Appendix A: Requirement-to-AC Mapping

| Ticket AC | Requirement(s) | Description |
|-----------|----------------|-------------|
| AC-1 | Req 1 (Gitleaks) | Gate runs gitleaks for secrets detection; any secret triggers hard FAIL |
| AC-2 | Req 2 (Bandit) | Gate runs bandit + semgrep security rules for Python code |
| AC-3 | Req 4 (pip-audit + npm audit) | Gate runs pip-audit (Python) and npm audit (JavaScript) for dependency CVEs |
| AC-4 | Req 5 (Severity Thresholds) | Hard-fail conditions: secrets, unsafe deserialization, auth bypass, critical CVEs (CVSS ≥7.0) |
| AC-5 | Req 5 (Decision Matrix) | Soft-fail conditions: low/medium CVEs, security warnings return WARN status |
| AC-6 | Req 6 (Gate Output) | Implemented as `ci/scripts/gates/security_gate_check.py` integrated into M902-01 framework |
| AC-7 | Req 6 (M902-01 Integration) | Integrated into gate registry as final gate before commit; returns M902-01 success schema |
| AC-8 | Req 8 (Test Fixtures) | Tested with known vulnerability patterns; fixtures validate detection without committing real vulnerabilities |
| AC-9 | Req 8 (Determinism) | False positive analysis documented in spec; validation results deterministic |

---

## Appendix B: File Paths and Artifacts

**Specification and Documentation:**
- Spec: `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_16_security_gate_spec.md` (this file)
- Execution Plan: `/Users/jacobbrandt/workspace/blobert/project_board/execution_plans/M902-16_stage_8_security_gate_integration.md`
- Tool Audit (Task 2): `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_16_tool_audit.md` (TBD, created in Task 2)

**Gate Implementation:**
- Main gate: `/Users/jacobbrandt/workspace/blobert/ci/scripts/gates/security_gate_check.py` (TBD, created in Task 9)
- Gate registry: `/Users/jacobbrandt/workspace/blobert/ci/scripts/gate_registry.json` (updated in Task 10)

**Tool Configurations:**
- `.gitleaksignore`: `/Users/jacobbrandt/workspace/blobert/.gitleaksignore` (TBD, Task 3)
- `.bandit`: `/Users/jacobbrandt/workspace/blobert/asset_generation/python/.bandit` (TBD, Task 4)
- `.semgrep.yml`: `/Users/jacobbrandt/workspace/blobert/.semgrep.yml` (TBD, Task 5)
- pyproject.toml: `/Users/jacobbrandt/workspace/blobert/asset_generation/python/pyproject.toml` (updated with tool deps, Task 2)
- package.json: `/Users/jacobbrandt/workspace/blobert/asset_generation/web/frontend/package.json` (updated with npm audit, Task 2)

**Test Fixtures:**
- Mock secrets: `/Users/jacobbrandt/workspace/blobert/tests/ci/fixtures/mock_secrets/` (TBD, Task 3)
- Bandit patterns: `/Users/jacobbrandt/workspace/blobert/tests/ci/fixtures/bandit_unsafe_patterns/` (TBD, Task 4)
- Semgrep patterns: `/Users/jacobbrandt/workspace/blobert/tests/ci/fixtures/semgrep_patterns/` (TBD, Task 5)
- Vulnerable packages: `/Users/jacobbrandt/workspace/blobert/tests/ci/fixtures/vulnerable_packages/` (TBD, Task 6)

**Test Files:**
- Behavioral tests: `/Users/jacobbrandt/workspace/blobert/tests/ci/test_security_gate_check.py` (TBD, Task 7)
- Adversarial tests: `/Users/jacobbrandt/workspace/blobert/tests/ci/test_security_gate_check_adversarial.py` (TBD, Task 8)
- Integration tests: `/Users/jacobbrandt/workspace/blobert/tests/ci/test_security_gate_check_integration.py` (TBD, Task 11)

**Checkpoints:**
- Specification checkpoint: `/Users/jacobbrandt/workspace/blobert/project_board/checkpoints/M902-16/2026-05-19T-specification.md`
- Tool audit checkpoint (Task 2): TBD
- AC Gatekeeper final: `/Users/jacobbrandt/workspace/blobert/project_board/checkpoints/M902-16/2026-05-19T-ac_gatekeeper_final.md` (Task 14)

---

## Appendix C: Glossary and Definitions

- **Hard-fail:** Condition that triggers FAIL status (gate returns non-zero exit code in blocking mode; always exits 0 in shadow mode).
- **Soft-fail (WARN):** Condition that triggers WARN status (non-blocking; does not prevent commit in any mode).
- **Mock fixture:** Non-functional test data (e.g., fake secret pattern, fake API key) used only for testing; never committed as production code.
- **Deterministic:** Same input → identical output across multiple runs; no randomness, no network drift, no timestamp variance in decision logic.
- **Shadow mode:** Gate runs, produces findings, always exits 0 (non-blocking); used for rollout and monitoring.
- **Blocking mode:** Gate runs, produces findings, exits non-zero if FAIL status (blocks commit); enforcement deferred to M903.
- **CVSS score:** Common Vulnerability Scoring System v3.1; numeric score 0.0–10.0 indicating severity.
- **Tool status:** Exit code, findings count, timeout flag, and error message for each of the 5 tools (recorded in JSON output).
- **Remediation hint:** Actionable suggestion for fixing a violation (e.g., "run `git reset HEAD <file>` to unstage secret").

---

## Appendix D: References

1. **code_governance.md** (Stage 8 Security Gate): Architecture specification, hard-fail conditions, tool selection rationale.
2. **M902-01 Gate Runner Spec**: Gate schema, success/failure record formats, registry structure.
3. **M902-02 Static Analysis Gate Spec**: Tool orchestration patterns, configuration strategies, baseline reporting.
4. **CLAUDE.md** (Project conventions): Guardrails, exclusion patterns, scope discipline.
5. **Execution Plan** (M902-16): Task breakdown, dependencies, success criteria.

---

**Status:** SPECIFICATION COMPLETE (v1.0 FROZEN)  
**Ready for:** Task 2 (Tool Audit) and parallel spec exit gate validation.
