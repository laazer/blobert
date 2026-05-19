# M902-16 Execution Plan: Stage 8 — Security Gate Integration

**Planner Agent Run:** 2026-05-19T-m902-16-planning  
**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/16_stage_8_security_gate_integration.md`  
**Status:** PLANNING (Revision 1)  
**Confidence:** HIGH

---

## Project Overview

**M902-16** implements Stage 8 of the 8-stage governance pipeline: the **Final Security Gate**. This stage is the last layer before commit approval and runs dedicated security scanning tools to detect:
- **Secrets** (gitleaks) — hard fail on detection
- **Python security vulnerabilities** (bandit + semgrep) — hard fail on critical patterns (unsafe deserialization, auth bypass)
- **Dependency vulnerabilities** (pip-audit, npm audit) — hard fail on CVSS ≥7.0
- **Aggregate findings** into deterministic FAIL/WARN/PASS decisions based on severity thresholds

The gate integrates into the M902-01 validation framework as the final gate before commit and returns JSON following the M902-01 success schema.

**Key Constraints:**
- Runs after Stage 7 (Override System) — only called if no overrides triggered
- Deterministic: same staged files → same findings (no randomness)
- Hard-fail on secrets, unsafe deserialization, auth bypass, critical CVEs (CVSS ≥7.0)
- Soft-fail (WARN status) on low/medium CVEs and security advisories
- Non-blocking by default in M902 (shadow mode); enforcement deferred to M903
- Test fixtures validate vulnerability detection without committing real secrets/exploits

---

## Task Breakdown

### Task 1: Freeze M902-16 Specification (Spec Agent)

**Objective:** Produce specification document with 8 frozen requirements, all 9 ACs mapped, tool configuration decisions frozen, threshold policies defined.

**Input:**
- Ticket M902-16 (acceptance criteria, dependencies)
- code_governance.md Stage 8 rules (secrets, unsafe deserialization, auth bypass, critical CVE patterns)
- M902-01 gate framework examples (registry entry, gate success schema v0.2.0)
- M902-02 spec examples (tool configuration strategy, shadow mode, baseline violations)
- Tool documentation: gitleaks, bandit, semgrep, pip-audit, npm audit
- Existing gate specs (M902-10, M902-02 for configuration patterns)

**Expected Output:**
- Specification file at `project_board/specs/902_16_security_gate_spec.md` (v1.0 FROZEN)
- 8 Requirements documented with acceptance criteria:
  1. **Gitleaks Secret Detection:** Gitleaks as subprocess, detects secrets in staged files, hard fail on any match, rule scope documented
  2. **Bandit Python Security:** Bandit run on `asset_generation/python/` and `asset_generation/web/backend/`, critical severity patterns (B201, B301-B303 unsafe deserialization, B105-B107 hardcoded secrets), hard fail on critical findings
  3. **Semgrep Security Rules:** Local `.semgrep.yml` rules for authentication bypass, critical security patterns; runs on Python + TypeScript; hard fail on high-severity matches
  4. **Dependency Audit (pip-audit + npm audit):** pip-audit on Python venv, npm audit on `asset_generation/web/frontend/`, CVSS threshold definitions, hard fail on CVSS ≥7.0, soft fail on <7.0
  5. **Severity Thresholds & Fail/Warn/Pass Logic:** Decision matrix (hard fail conditions, soft fail/warn conditions, pass conditions), threshold config frozen, deterministic routing
  6. **Gate Output Contract:** JSON schema matching M902-01 (status, gate, timestamp, violations[], remediation_hints[], artifacts[], duration_ms), tool-specific metadata (tool_statuses array with name/exit_code/findings_count)
  7. **Tool Configuration & Scope:** Tool invocation paths, exclusions (*.glb, generated paths, node_modules, .venv), timeout values, command-line flags, version constraints
  8. **Test Fixture Strategy:** Known vulnerability test fixtures (mock secrets, test packages with CVEs, test Python code with unsafe patterns), determinism validation (same fixtures → identical findings)
- All 9 ticket ACs mapped to requirements with traceability
- Checkpoint decisions logged:
  1. Hard-fail conditions: any secret detected, B301-B303 (unsafe deserialization), auth bypass patterns, CVSS ≥7.0 CVEs
  2. Soft-fail/WARN conditions: low/medium CVEs, security warnings, advisories
  3. Tool ordering: gitleaks first (fail-fast), then bandit, then semgrep, then dependency audits
  4. Fixture strategy: mock secrets (not real), test CVE fixtures via pip packages, Python code with deliberate unsafe patterns (flagged by bandit)
  5. Timeout strategy: per-tool timeouts (gitleaks 10s, bandit 30s, semgrep 60s, pip-audit 20s, npm audit 20s)
  6. Exclusion policy: generated artifacts, lockfiles, vendored code
  7. Determinism: no randomness, no network dependencies (offline mode), same input → identical findings
  8. Performance target: <120s total gate execution
- Tool version constraints and dependency compatibility documented
- No ambiguities remain; all clarifying questions resolved

**Dependencies:** None (M902-01, M902-02 already COMPLETE; code_governance.md available)

**Success Criteria:**
- Spec v1.0 file created at `project_board/specs/902_16_security_gate_spec.md`
- All 8 requirements ≥150 words each with clear acceptance criteria
- All 9 ticket ACs mapped to requirement(s) with explicit traceability (AC-1 → Req2, etc.)
- Checkpoint log at `project_board/checkpoints/M902-16/<timestamp>-specification.md` with decisions + confidence
- Severity thresholds frozen (CVSS ≥7.0 = hard fail, <7.0 = warn, no findings = pass)
- Tool configuration scope documented (which directories, which file types, exclusions)
- Fixture strategy documented: mock vulnerabilities, no real secrets in repo, test packages list
- File tree specified (gate module path, config paths, test fixture paths)
- Spec marked "FROZEN v1.0" and ready for spec exit gate
- No deferred scope or ambiguities (all tool choices, threshold values, failure modes explicit)

**Risks / Assumptions:**
- **Risk:** Tool output parsing fragile across versions → **Mitigation:** Spec freezes tool versions; test fixtures validate parsing per version
- **Risk:** Real secrets accidentally committed during testing → **Mitigation:** Spec mandates mock fixtures only; test harness prevents real secret storage
- **Risk:** Dependency audit tools require network (PyPI index, npm registry) → **Mitigation:** Spec defines offline mode if available; fallback is cached index
- **Risk:** Gitleaks pattern false positives in code/comments → **Mitigation:** Spec defines allowlist mechanism (.gitleaksignore) for known false positives
- **Assumption:** gitleaks, bandit, semgrep, pip-audit, npm audit all installable and available in CI → Evidence: (TBD Task 2) audit confirms availability
- **Assumption:** Existing tool configs (ruff, eslint) don't conflict with new tools → Evidence: (TBD Task 2) compatibility audit
- **Assumption:** code_governance.md Stage 8 rules are authoritative → Evidence: code_governance.md is architectural spec, frozen

---

### Task 2: Audit Tool Availability & Configuration (Spec Agent)

**Objective:** Verify all security tools are available, document their configurations, identify gaps or conflicts.

**Input:**
- Spec v1.0 from Task 1
- Current environment: Python venv at `asset_generation/python/`, npm packages in `asset_generation/web/frontend/`
- `pyproject.toml` and `package.json` (existing dependencies)
- Tool documentation (gitleaks, bandit, semgrep, pip-audit, npm audit)
- CLAUDE.md guardrails (exclusions, scope)

**Expected Output:**
- Tool availability audit document at `project_board/specs/902_16_tool_audit.md` with:
  - **Gitleaks:** Installation status (via Homebrew, binary, source), version pinned, CLI path documented, example invocation
  - **Bandit:** Version in pyproject.toml or available, rule scope (B101-B306+), command example, config file location
  - **Semgrep:** Version, installation method (Python package or binary), local rules file location, online mode vs offline
  - **pip-audit:** Version, installation method, CVSS threshold CLI flag, output format
  - **npm audit:** Availability check (npm built-in), version, output parsing
  - **Compatibility matrix:** Tool conflicts (e.g., bandit vs semgrep rule overlap), exclusions shared across tools
  - **Version constraints table:** gitleaks (latest stable), bandit (1.7.5+), semgrep (1.50+), pip-audit (2.6+), npm audit (npm v8+)
  - **Baseline findings:** Run each tool on current codebase in shadow mode, capture baseline violation counts
  - **Fixture availability:** Verify test package sources (e.g., packages with known CVEs for pip-audit testing)
  - **Timeout justification:** Per-tool timeout estimates based on codebase size
  - **Exclusion strategy:** Documented patterns (.gitleaksignore, bandit excludes, semgrep excludes, npm/pip audit ignores)
- Checkpoint decisions logged for:
  1. Tool installation approach (pyproject.toml vs external install)
  2. Version pinning strategy (exact vs range)
  3. Any tool unavailable or deferred to M903
  4. Baseline violation counts (for shadow mode documentation)
- Configuration conflicts resolved

**Dependencies:** Task 1 (Spec v1.0 COMPLETE)

**Success Criteria:**
- Audit document created at `project_board/specs/902_16_tool_audit.md`
- All 5 tools (gitleaks, bandit, semgrep, pip-audit, npm audit) either confirmed available or explicitly deferred with M903 ticket
- Installation paths and version constraints documented
- Baseline violation counts captured (may be non-zero for shadow mode)
- Tool invocation examples included
- Exclusion strategy documented and aligned with CLAUDE.md
- Checkpoint includes any risk flags or compatibility warnings
- No blocking issues identified for gate implementation

**Risks / Assumptions:**
- **Risk:** Some tools not available in current environment → **Mitigation:** Audit confirms or defers; spec defines fallback behavior
- **Risk:** Tool versions incompatible → **Mitigation:** Audit identifies conflicts; spec freezes working version matrix
- **Assumption:** Test packages with real CVEs can be sourced safely (vendored or accessed read-only) → Evidence: (TBD Task 6) fixture strategy
- **Assumption:** Codebase has no actual secrets currently → Evidence: (TBD) audit run

---

### Task 3: Create Gitleaks Configuration & Fixtures (Spec Agent)

**Objective:** Configure gitleaks for secret detection, create test fixtures with mock secrets.

**Input:**
- Spec v1.0 from Task 1
- Tool audit from Task 2
- Gitleaks documentation and rule library
- Existing `.gitleaksignore` if present

**Expected Output:**
- `.gitleaksignore` file (root of repo) documenting known false positives or allowlist patterns
- Gitleaks configuration file (if needed; gitleaks uses built-in rules by default)
- Test fixtures at `tests/ci/fixtures/mock_secrets/`:
  - `mock_aws_key.txt` — fake AWS key pattern
  - `mock_private_key.pem` — fake RSA private key
  - `mock_github_token.txt` — fake GitHub token pattern
  - `mock_stripe_api.txt` — fake Stripe API key
  - `README.md` — documents that all fixtures are **MOCK** (non-functional), explains how test harness uses them
- Documented invocation: `gitleaks detect --source . --baseline .gitleaks-baseline.json` (if needed)
- Command-line flags documented (--exit-code, --report-path, --baseline)
- Fixture mounting strategy: test harness creates temporary git repo with mock secrets staged, runs gitleaks, verifies detection
- Checkpoint decisions logged:
  1. Whether `.gitleaksignore` is needed for existing allowlist
  2. Gitleaks rule subset selection (all rules vs high-confidence only)
  3. Baseline JSON approach (track known false positives)
  4. Mock secret complexity (simple patterns vs realistic-looking)

**Dependencies:** Tasks 1–2 (Spec v1.0, audit COMPLETE)

**Success Criteria:**
- `.gitleaksignore` or config file created (if needed for allowlist)
- Test fixtures directory created at `tests/ci/fixtures/mock_secrets/` with ≥4 mock secret types
- Each fixture file contains MOCK (non-functional) secret pattern
- README in fixtures directory clearly states: "MOCK SECRETS — FOR TESTING ONLY — NOT FUNCTIONAL"
- Gitleaks invocation command documented
- Test fixture strategy documented: how test harness uses fixtures (temporary git staging, detection validation)
- Baseline handling documented (whether baseline.json needed)

**Risks / Assumptions:**
- **Risk:** Mock secrets too simple, don't trigger detection → **Mitigation:** Spec freezes realistic mock patterns based on gitleaks rule documentation
- **Risk:** Accidental real secrets in test fixtures → **Mitigation:** Code review and static check required before commit (use gitleaks pre-commit hook)
- **Risk:** Gitleaks false positives on legitimate code → **Mitigation:** `.gitleaksignore` for documented allowlist
- **Assumption:** Mock fixtures are never functional (cannot be used to access real services) → Evidence: (TBD) validation in test harness

---

### Task 4: Create Bandit Configuration & Fixtures (Spec Agent)

**Objective:** Configure bandit for Python security scanning, create test fixtures with unsafe patterns.

**Input:**
- Spec v1.0 from Task 1
- Tool audit from Task 2
- Bandit documentation (rule IDs: B101-B306+)
- Existing ruff/bandit configs in `asset_generation/python/pyproject.toml`

**Expected Output:**
- `.bandit` configuration file in `asset_generation/python/` (or `pyproject.toml` [tool.bandit] section) with:
  - Rule inclusions: B201 (flask debug), B301-B303 (pickle/marshal/yaml deserialization), B105-B107 (hardcoded secrets), B110-B112 (try/except too broad), B303 (arbitrary code execution)
  - Exclusions: test directories (partial), comments with `# noqa: B###` respected
  - Severity thresholds: HIGH → hard fail, MEDIUM → warn (soft fail), LOW → pass
- Test fixtures at `tests/ci/fixtures/bandit_unsafe_patterns/`:
  - `unsafe_pickle.py` — demonstrates `pickle.loads()` on untrusted data (B301)
  - `unsafe_yaml.py` — demonstrates `yaml.load()` without Loader (B506)
  - `unsafe_deserialization.py` — demonstrates `marshal.loads()` (B303)
  - `hardcoded_secret.py` — demonstrates hardcoded password/API key (B105-B107)
  - `unsafe_exec.py` — demonstrates `eval()` on user input (B102)
  - `README.md` — documents fixture purpose and which rules they trigger
- Bandit invocation command documented: `bandit -r asset_generation/python/ -f json`
- Command-line flags documented (--severity, --confidence, --skip-ids)
- Test fixture strategy: import test files, run bandit, verify findings match expected rule IDs
- Checkpoint decisions logged:
  1. Hard-fail rules (B201, B301-B303, B105-B107, unsafe deserialization patterns)
  2. Severity mapping (HIGH → hard fail, MEDIUM → warn)
  3. Scope (asset_generation/python/ + web backend if applicable)
  4. Exception handling: catch B110 (bare except) separately?

**Dependencies:** Tasks 1–2 (Spec v1.0, audit COMPLETE)

**Success Criteria:**
- `.bandit` or `pyproject.toml [tool.bandit]` configuration created with rule inclusions and severity thresholds
- Test fixtures directory created at `tests/ci/fixtures/bandit_unsafe_patterns/` with ≥5 Python files demonstrating unsafe patterns
- Each fixture file is valid Python (syntactically correct, can be imported)
- README in fixtures directory documents which rule ID each fixture triggers
- Bandit invocation command documented
- Test fixture strategy documented: how to run bandit on fixtures and validate detection
- Hard-fail rule list frozen in spec: B201, B301-B303, B105-B107, others

**Risks / Assumptions:**
- **Risk:** Fixtures may introduce actual security risks if run → **Mitigation:** Fixtures are analysis-only (not executed in test harness), and runtime guards prevent execution
- **Risk:** Bandit detection may miss some patterns or have false positives → **Mitigation:** Spec freezes baseline violations; tests validate known patterns are detected
- **Assumption:** Fixture files are safe to store in repo (analysis-only, not executed) → Evidence: (TBD) test harness review confirms analysis-only approach
- **Assumption:** Bandit rules remain stable across versions → Evidence: Bandit rule IDs are stable API; version pinning in pyproject.toml

---

### Task 5: Create Semgrep Configuration & Fixtures (Spec Agent)

**Objective:** Configure semgrep with local security rules for critical patterns (auth bypass, unsafe deserialization), create test fixtures.

**Input:**
- Spec v1.0 from Task 1
- Tool audit from Task 2
- Semgrep documentation and rule registry (p/security/*, p/owasp/*, custom rules)
- code_governance.md Stage 8 rules (auth bypass, unsafe deserialization)

**Expected Output:**
- `.semgrep.yml` file at repo root (or `asset_generation/python/.semgrep.yml` if language-scoped) with:
  - Rule set for critical security patterns (auth bypass, unsafe deserialization, SQL injection, hardcoded secrets)
  - Rule severity levels (CRITICAL → hard fail, HIGH → hard fail, MEDIUM → warn, LOW → pass)
  - Language scopes (Python, JavaScript/TypeScript)
  - Exclusions: test files, generated code, vendored dependencies
  - Example rules:
    - `auth_bypass_patterns`: detects Flask/Django auth decorator bypasses, token validation skips
    - `unsafe_deserialize`: detects pickle/yaml/marshal usage, missing Loader specification
    - `sql_injection`: detects unsanitized SQL queries or missing parameterization
    - `hardcoded_secrets`: detects API keys, tokens, passwords in code
  - Policy: rules from p/owasp-top-10 and p/security registries, plus custom local rules
- Test fixtures at `tests/ci/fixtures/semgrep_patterns/`:
  - `auth_bypass.py` — demonstrates auth check bypass (missing or conditional skip)
  - `unsafe_deserialize.js` — demonstrates JSON.parse or eval on untrusted input
  - `sql_injection.py` — demonstrates unsanitized SQL query construction
  - `hardcoded_api_key.js` — demonstrates hardcoded API key in source
  - `README.md` — documents which rule each fixture triggers
- Semgrep invocation command documented: `semgrep --config .semgrep.yml asset_generation/python asset_generation/web/frontend -f json`
- Command-line flags documented (--json, --strict, --skip-path)
- Test fixture strategy: semgrep analyzes test files, verifies expected findings
- Checkpoint decisions logged:
  1. Rule selection strategy (curated vs full registry)
  2. Severity mapping (CRITICAL/HIGH → hard fail, MEDIUM → warn, LOW → pass)
  3. Exclusion strategy (test files, generated code)
  4. Local rule creation vs registry selection
  5. Performance: semgrep can be slow; timeout strategy documented

**Dependencies:** Tasks 1–2 (Spec v1.0, audit COMPLETE)

**Success Criteria:**
- `.semgrep.yml` configuration file created with rule definitions and severity mappings
- Test fixtures directory created at `tests/ci/fixtures/semgrep_patterns/` with ≥4 code samples demonstrating security patterns
- Semgrep invocation command documented
- Rule severity mapping frozen: CRITICAL/HIGH → hard fail, MEDIUM → warn
- Fixture strategy documented: semgrep runs on fixtures, validates detection
- Exclusions documented (test files, generated paths, .gitleaksignore false positives)
- Scope covered: Python (asset_generation/python/, web backend) + JavaScript/TypeScript (asset_generation/web/frontend/)

**Risks / Assumptions:**
- **Risk:** Semgrep can be slow on large codebases → **Mitigation:** Spec defines timeout (60s), scope limiting to critical rules only
- **Risk:** Rule registry or custom rules may have false positives → **Mitigation:** Baseline violations captured; spec freezes known allowlist
- **Risk:** Semgrep requires internet for remote rule registry → **Mitigation:** Spec uses local `.semgrep.yml` only (no remote registry in M902)
- **Assumption:** Local rule syntax is stable → Evidence: Semgrep documentation is authoritative
- **Assumption:** Performance is acceptable (<60s for typical codebase) → Evidence: (TBD Task 6) benchmark baseline run

---

### Task 6: Create Dependency Audit Configuration & Fixtures (Spec Agent)

**Objective:** Configure pip-audit and npm audit for dependency vulnerability scanning, create test fixtures with known CVEs.

**Input:**
- Spec v1.0 from Task 1
- Tool audit from Task 2
- pip-audit and npm audit documentation
- Existing `asset_generation/python/pyproject.toml` and `asset_generation/web/frontend/package.json`
- CVSS v3.1 threshold documentation

**Expected Output:**
- `pip-audit` configuration:
  - Command with CVSS threshold: `pip-audit --desc --format json --skip-vulnerable --ignore-vulns <ignore-list>` (or similar flags)
  - CVSS threshold: ≥7.0 → hard fail, <7.0 → warn, none → pass
  - Ignore list for known false positives or accepted risks (if any)
  - Command example documented
- `npm audit` configuration:
  - Command: `npm audit --json --production` (or full) with CVSS threshold
  - Severity mapping: critical/high → hard fail, medium → warn, low → pass
  - Allowlist for known false positives or accepted risks (if any)
  - audit-level flag documented
  - Command example documented
- Test fixture approach at `tests/ci/fixtures/vulnerable_packages/`:
  - `pip_vulnerable_packages.txt` — list of PyPI packages with known CVEs (e.g., `insecure-package==1.0.0` if such a test package exists)
  - `npm_vulnerable_packages.json` — mock package.json with vulnerable dependencies (or pointer to test npm package with CVEs)
  - **Strategy:** Do NOT add actual vulnerable packages to main pyproject.toml or package.json. Instead, test harness creates isolated virtual environments/npm contexts with vulnerable package lists, runs audits, validates detection.
  - README documenting test strategy: "Vulnerable package fixtures are test-only; never added to main dependencies"
- Invocation commands documented:
  - Python: `pip-audit --format json` (from venv)
  - Node: `npm audit --json` (from `asset_generation/web/frontend/`)
- CVSS threshold mapping documented: 7.0+ = hard fail, <7.0 = warn
- Checkpoint decisions logged:
  1. CVSS threshold (7.0 is standard critical/high boundary)
  2. Test fixture approach (isolated test environments, not real vulnerable packages in repo)
  3. Allowlist strategy (if needed for accepted risks)
  4. Scope: Python venv (from pyproject.toml uv sync), npm (from package.json in asset_generation/web/frontend/)

**Dependencies:** Tasks 1–2 (Spec v1.0, audit COMPLETE)

**Success Criteria:**
- pip-audit invocation documented with CVSS threshold and output format flags
- npm audit invocation documented with severity mapping
- CVSS threshold mapping frozen: ≥7.0 hard fail, <7.0 warn, none pass
- Test fixture strategy documented: isolated test environments, not polluting main dependencies
- Fixture directory created at `tests/ci/fixtures/vulnerable_packages/` with test data and README
- Allowlist mechanism documented (if needed)
- Both tools integrated into gate logic

**Risks / Assumptions:**
- **Risk:** Dependency audits require network access (PyPI, npm registry) → **Mitigation:** Spec uses cached/offline mode if available; CI may have network isolation
- **Risk:** Test packages with known CVEs may be removed from registries → **Mitigation:** Spec documents fallback: mock vulnerability JSON responses if real packages unavailable
- **Risk:** Dependency audit findings are high-volume (many transitive CVEs) → **Mitigation:** CVSS threshold (7.0+) filters to critical issues; spec freezes grandfathering policy for M903
- **Assumption:** pip-audit and npm audit are reliable and deterministic → Evidence: (TBD) baseline run validates same findings on repeated runs

---

### Task 7: Design Behavioral Test Suite (Test Designer)

**Objective:** Create 40+ behavioral tests covering all gate scenarios (secrets, unsafe code, CVEs, decision matrix).

**Input:**
- Spec v1.0 from Task 1
- Tool configurations from Tasks 3–6
- Test fixtures created in Tasks 3–6
- M902-02 test design examples (parametrized tests, fixtures, assertions)

**Expected Output:**
- Test file `tests/ci/test_security_gate_check.py` with 40+ behavioral tests
- Test organization by tool/scenario:
  - **Gitleaks (8+ tests):** 
    - Secret detection: AWS keys, GitHub tokens, private keys, Stripe API keys
    - No false positives on legitimate code/comments
    - Baseline comparison (if using baseline.json)
    - .gitleaksignore allowlist handling
  - **Bandit (8+ tests):**
    - B301-B303 unsafe deserialization detection
    - B105-B107 hardcoded secrets
    - B201 Flask debug mode
    - Severity level mapping (HIGH → hard fail, MEDIUM → warn)
  - **Semgrep (8+ tests):**
    - Auth bypass pattern detection
    - SQL injection detection
    - Hardcoded API key detection
    - Severity mapping (CRITICAL/HIGH → hard fail, MEDIUM → warn)
  - **Dependency Audit (8+ tests):**
    - pip-audit CVSS ≥7.0 detection (hard fail)
    - pip-audit CVSS <7.0 detection (warn)
    - npm audit critical findings
    - No false positives on approved dependencies
  - **Decision Matrix (8+ tests):**
    - Multiple violations (secret + CVE) → hard fail (secrets take priority)
    - Only MEDIUM CVEs → warn
    - No violations → pass
    - Mixed findings → correct status routing
- Each test validates:
  1. Gate entry point invoked (run() function called with inputs)
  2. Tool subprocess spawned with correct flags
  3. Output parsed correctly
  4. JSON result matches gate schema (status, violations, artifacts, duration_ms)
  5. Decision matches expected outcome (FAIL/WARN/PASS)
- All tests deterministic (no randomness, mocked subprocess/file I/O where needed)
- Test names describe scenario clearly (e.g., `test_gitleaks_aws_key_detected_hard_fails`, `test_bandit_unsafe_pickle_warns`)

**Dependencies:** Tasks 1–6 (Spec v1.0, all configurations and fixtures COMPLETE)

**Success Criteria:**
- Test file `tests/ci/test_security_gate_check.py` exists with 40+ passing tests (before implementation, expected failures OK)
- All 5 tools covered with ≥8 tests each
- Each test validates gate invocation, subprocess call, output parsing, JSON schema compliance
- Test names self-documenting (describe tool + scenario)
- Docstrings reference AC numbers and threat type (secrets, unsafe code, CVE)
- Edge case coverage: no violations (clean codebase), mixed findings, timeout handling
- All tests deterministic (can run twice, produce same results)
- Mocked subprocess calls to tool CLIs (don't execute real gitleaks/bandit)
- Coverage aligns with gate ACs (gitleaks, bandit, semgrep, pip-audit, npm audit all covered)

**Risks / Assumptions:**
- **Risk:** Tool subprocess output format may vary across versions → **Mitigation:** Spec freezes tool versions in Task 2; tests mock subprocess with fixed output
- **Risk:** Tests don't validate real tool findings (mocked) → **Mitigation:** Intended; real tool integration tested in Task 8 (integration tests on actual fixtures)
- **Assumption:** Behavioral tests define expected gate behavior; implementation must satisfy all tests → Evidence: TDD approach

---

### Task 8: Develop Adversarial Test Suite (Test Breaker)

**Objective:** Create 30+ adversarial tests for edge cases, stress conditions, and determinism validation.

**Input:**
- Spec v1.0 from Task 1
- Behavioral tests from Task 7
- Tool fixtures from Tasks 3–6
- Checkpoint protocol (for decision logging)

**Expected Output:**
- Test file `tests/ci/test_security_gate_check_adversarial.py` with 30+ parametrized tests
- Test categories:
  - **Tool timeout handling (4 tests):** gitleaks timeout, bandit timeout, semgrep timeout, npm audit timeout → gate returns FAIL with timeout violation
  - **Tool subprocess failure (4 tests):** gitleaks exits non-zero, bandit missing/broken, semgrep invalid config, npm not installed → gate returns FAIL with tool error
  - **Malformed output (4 tests):** gitleaks returns invalid JSON, bandit returns empty output, semgrep parsing error, audit JSON malformed → gate gracefully handles or returns FAIL
  - **Boundary thresholds (6 tests):**
    - CVSS exactly 7.0 → hard fail
    - CVSS 6.9 → warn
    - Secret with confidence score edge cases
    - Bandit HIGH vs MEDIUM severity boundary
  - **Determinism (4 tests):** 
    - Same staged files (fixture set A) run twice → identical findings
    - Tool output order independence (violations in different order) → same decision
    - No timestamps or randomness in decision logic
  - **Mixed violation scenarios (4 tests):**
    - Secret + CVE → hard fail (secret priority)
    - Unsafe code + medium CVE → hard fail (unsafe code priority)
    - Multiple unsafe patterns → hard fail with all violations aggregated
  - **Empty/edge input (4 tests):**
    - No staged files → pass (early exit)
    - Empty fixture set → pass or warn (no findings)
    - Very large staged file count (100+ files) → gate completes within timeout
- Checkpoint decisions logged for:
  1. Tool timeout strategy (per-tool vs aggregate timeout)
  2. Failure mode handling (tool crashes → FAIL with remediation hint)
  3. Violation aggregation (multiple tools finding same issue → deduplicate or count separately?)
  4. Determinism priority (same input → identical JSON output, not just semantic equivalence)
  5. Decision priority cascade (secret > unsafe code > CVE > warning)
- All tests initially expected to fail (before Task 9 implementation)

**Dependencies:** Tasks 1–7 (Spec v1.0, all configurations, behavioral tests COMPLETE)

**Success Criteria:**
- Test file `tests/ci/test_security_gate_check_adversarial.py` exists with 30+ expected failures (pre-implementation)
- Timeout and subprocess failure scenarios covered
- Determinism and decision priority tests explicit
- Checkpoint log documents assumptions for failure modes and edge cases
- All tests parametrized for easy verification during implementation

**Risks / Assumptions:**
- **Risk:** Adversarial tests may be fragile (hard to predict exact failure modes) → **Mitigation:** Tests encode conservative assumptions; implementation can refine
- **Assumption:** Tool subprocess behavior is predictable (same CLI flags → same failures) → Evidence: (TBD) baseline audit from Task 2

---

### Task 9: Implement Security Gate Logic (Implementation Agent)

**Objective:** Implement `ci/scripts/gates/security_gate_check.py` orchestrating all tools, aggregating findings, returning M902-01 gate schema JSON.

**Input:**
- Spec v1.0 from Task 1
- All tool configurations from Tasks 3–6
- Behavioral + adversarial tests from Tasks 7–8
- M902-01 gate schema (status, violations[], remediation_hints[], duration_ms)
- M902-02 gate implementation examples (subprocess orchestration, JSON output)

**Expected Output:**
- Gate implementation at `ci/scripts/gates/security_gate_check.py` (250+ lines) with:
  - `run(inputs: dict) -> dict` function (gate entry point per M902-01)
  - Subprocess orchestration for all 5 tools (gitleaks, bandit, semgrep, pip-audit, npm audit)
  - Severity threshold logic (hard fail, soft fail/warn, pass)
  - JSON output parsing per tool
  - Violation aggregation and deduplication
  - Timeout and error handling (tool crashes → FAIL with remediation)
  - Deterministic output (no timestamps in decision logic, same input → same findings)
  - Comprehensive logging (tool invocations, findings summary, decision rationale)
  - Status: FAIL (hard-fail conditions), WARN (soft-fail conditions), PASS (no critical findings)
- Gate implementation passes all behavioral tests (Task 7)
- Gate implementation passes all adversarial tests (Task 8)
- Diff-cover > 85% on new code
- Code style: follows CLAUDE.md conventions (no bare except, structured logging, type hints)
- Detailed comments explaining threshold logic and decision matrix
- Handles missing tools gracefully (skip if unavailable, log warning, continue pipeline)

**Dependencies:** Tasks 1–8 (Spec v1.0, configurations, fixtures, tests all COMPLETE)

**Success Criteria:**
- Gate implementation at `ci/scripts/gates/security_gate_check.py` exists and is executable
- All behavioral tests (Task 7) pass: 40+ tests PASS
- All adversarial tests (Task 8) pass: 30+ tests PASS
- Gate can be invoked: `python ci/scripts/gate_runner.py security_gate_check --upstream-agent <name> --downstream-agent <name> --ticket-id <id> --mode shadow`
- JSON output matches M902-01 schema (status, violations[], remediation_hints[], duration_ms)
- Hard-fail conditions respected: secrets → FAIL, unsafe deserialization → FAIL, CVSS ≥7.0 → FAIL
- Soft-fail conditions respected: CVSS <7.0 → WARN, low-severity findings → WARN
- No critical findings → PASS
- Diff-cover ≥85% on new code
- Static QA passes (ruff, mypy, bandit on the gate code itself)

**Risks / Assumptions:**
- **Risk:** Tool subprocess behavior unpredictable → **Mitigation:** Comprehensive error handling, fallback behaviors, test fixtures validate
- **Risk:** Performance timeout insufficient → **Mitigation:** Spec defines per-tool timeouts; implementation respects aggregate timeout
- **Assumption:** Tests from Tasks 7–8 are comprehensive → Evidence: 70+ tests covering all scenarios

---

### Task 10: Register Gate & Integrate with M902-01 Framework (Implementation Agent)

**Objective:** Register security_gate_check in gate_registry.json, ensure runner can invoke it, document in Milestone README.

**Input:**
- Gate implementation from Task 9
- `ci/scripts/gate_registry.json` (existing entries, pattern)
- Milestone 902 README or project documentation

**Expected Output:**
- Updated `ci/scripts/gate_registry.json` with new entry:
  ```json
  {
    "name": "security_gate_check",
    "module": "security_gate_check",
    "required_inputs": [],
    "optional_inputs": ["mode", "ticket_id", "upstream_agent", "downstream_agent"],
    "default_mode": "shadow",
    "description": "Final security gate: runs gitleaks, bandit, semgrep, pip-audit, npm audit; hard-fails on secrets, unsafe code, critical CVEs (CVSS ≥7.0); warns on medium CVEs.",
    "category": "security"
  }
  ```
- Gate invocation command documented in Milestone 902 README or CLAUDE.md:
  ```bash
  python ci/scripts/gate_runner.py security_gate_check \
    --upstream-agent Override --downstream-agent Commit \
    --ticket-id <ticket_id> \
    --mode shadow|blocking
  ```
- Tool scope and decision logic documented in README
- Baseline violation counts from Task 2 documented for reference
- Mode toggle instructions (shadow → blocking transition deferred to M903)

**Dependencies:** Task 9 (Gate implementation COMPLETE)

**Success Criteria:**
- Gate registry entry added and gate runner recognizes it: `python ci/scripts/gate_runner.py security_gate_check --help` (or equivalent discovery)
- Gate invocation command documented and tested manually
- README updated with gate description, tools, thresholds, scope
- All 9 ticket ACs explicitly referenced in documentation or gate code with line numbers
- No missing links between gate code and spec (traceability)

**Risks / Assumptions:**
- **Risk:** Gate runner schema incompatible with new gate entry → **Mitigation:** Follow existing entry patterns from M902-02, M902-10
- **Assumption:** Gate runner from M902-01 is stable and unchanged → Evidence: M902-01 COMPLETE, 220 tests PASS

---

### Task 11: Create Integration Tests on Real Fixtures (Test Designer)

**Objective:** Create 15+ integration tests that run real tools against actual fixture files, validate findings.

**Input:**
- All tool fixtures from Tasks 3–6
- Gate implementation from Task 9
- Integration test patterns from M902-02

**Expected Output:**
- Integration test file `tests/ci/test_security_gate_check_integration.py` with 15+ tests:
  - **Real tool tests (3+ tests):** 
    - Gitleaks against real mock_secrets/ fixture directory
    - Bandit against real bandit_unsafe_patterns/ fixture files
    - Semgrep against real semgrep_patterns/ fixtures
  - **Full gate tests (5+ tests):**
    - Gate runs against fixture directory with mock secrets → returns FAIL with gitleaks findings
    - Gate runs against unsafe Python code → returns FAIL/WARN depending on severity
    - Gate runs against code with CVEs (if fixture available) → returns appropriate status
    - Gate runs against clean codebase (no unsafe code) → returns PASS
  - **Tool isolation (4+ tests):**
    - Each tool can be run independently (gitleaks-only, bandit-only, etc.)
    - Tool findings aggregated correctly by gate
  - **Output schema validation (3+ tests):**
    - Verify JSON output matches M902-01 schema for each scenario
- All tests use real tool binaries (not mocked subprocess)
- Tests isolated to fixture directories (don't scan production code during tests)
- Tests may be slow but validate real tool behavior

**Dependencies:** Tasks 3–6 (Fixtures), Task 9 (Gate implementation)

**Success Criteria:**
- Integration test file created with 15+ tests
- Real tools execute and findings validated
- Fixtures trigger expected findings (gitleaks finds secrets, bandit finds unsafe patterns, etc.)
- JSON output matches M902-01 schema
- All tests isolated to fixture directories (no production code scanned)
- Tests document expected findings per fixture (traceability: fixture → finding → rule ID)

**Risks / Assumptions:**
- **Risk:** Real tools may not be installed in test environment → **Mitigation:** Tests skip if tools unavailable (pytest skip markers)
- **Risk:** Tool output format may vary by version → **Mitigation:** Tests validated against pinned tool versions from Task 2
- **Assumption:** Fixtures are representative of real vulnerabilities → Evidence: Spec Task 1 requires realistic patterns

---

### Task 12: Perform Static QA on Gate Code (Static QA Agent)

**Objective:** Run ruff, mypy, bandit on gate code itself; resolve findings.

**Input:**
- Gate implementation from Task 9
- Static analysis configuration (ruff, mypy, bandit from M902-02)

**Expected Output:**
- Ruff linting report (no E9, F, I violations)
- Mypy type checking report (no untyped definitions)
- Bandit security scan of gate code itself (no unsafe patterns in gate)
- Checkpoint log documenting any false positives or suppression justifications
- Clean static QA: all tools PASS

**Dependencies:** Task 9 (Gate implementation COMPLETE)

**Success Criteria:**
- Ruff: 0 violations (E9, F, I rules)
- Mypy: full type coverage (no Any without justification)
- Bandit: 0 CRITICAL/HIGH findings (gate must not have unsafe patterns)
- All code follows CLAUDE.md style conventions
- Any suppressions documented with justification

**Risks / Assumptions:**
- **Risk:** Subprocess calls to tools may trigger bandit warnings → **Mitigation:** Suppressions documented with ticket reference
- **Assumption:** Static analysis is reliable → Evidence: M902-02 established tools and configs

---

### Task 13: Test Design Completeness Check (Spec Agent via Orchestrator)

**Objective:** Run `spec_completeness_check.py` on spec document before advancing to TEST_DESIGN.

**Input:**
- Spec v1.0 from Task 1 at `project_board/specs/902_16_security_gate_spec.md`
- Spec completeness checker from M902-01 (executable at `ci/scripts/spec_completeness_check.py`)

**Expected Output:**
- Completeness check result: PASS or FAIL
- If PASS: gate spec is complete per M902-01 framework (all required sections present)
- If FAIL: route back to Spec Agent with missing sections list

**Dependencies:** Task 1 (Spec v1.0)

**Success Criteria:**
- Spec passes completeness check: `python ci/scripts/spec_completeness_check.py project_board/specs/902_16_security_gate_spec.md --type generic`
- All required sections present and populated
- No FAIL status blocking advancement to TEST_DESIGN stage

**Risks / Assumptions:**
- **Risk:** Spec missing sections → **Mitigation:** Spec Agent updates and re-runs check
- **Assumption:** Spec completeness checker is reliable (M902-01) → Evidence: 220 tests PASS

---

### Task 14: AC Gatekeeper Validation (AC Gatekeeper Agent)

**Objective:** Validate all 9 acceptance criteria are satisfied by implementation and tests.

**Input:**
- Ticket M902-16 (9 ACs)
- Gate implementation from Task 9
- Test suites from Tasks 7–8, 11
- Spec from Task 1
- Integration status documentation

**Expected Output:**
- AC gatekeeper validation report at `project_board/checkpoints/M902-16/2026-05-19T-ac_gatekeeper_final.md` with:
  - AC-1 (Gitleaks detection): ✓ Verified by test suite (gitleaks tests in Task 7, integration tests Task 11)
  - AC-2 (Bandit Python security): ✓ Verified by test suite
  - AC-3 (pip-audit + npm audit dependencies): ✓ Verified by test suite
  - AC-4 (Hard-fail conditions): ✓ Verified by decision matrix tests and spec
  - AC-5 (Soft-fail/WARN conditions): ✓ Verified by test suite
  - AC-6 (Gate at ci/scripts/gates/security_gate_check.py): ✓ File exists, executable
  - AC-7 (M902-01 integration): ✓ Gate registered in gate_registry.json, returns correct schema
  - AC-8 (Test fixtures): ✓ All fixture types created (mock secrets, unsafe patterns, vulnerable packages)
  - AC-9 (Deterministic, false positive analysis): ✓ Determinism tests (Task 8), false positive documentation in spec
- All ACs satisfied: PASS

**Dependencies:** Tasks 1–12 (All implementation and testing COMPLETE)

**Success Criteria:**
- All 9 ACs verified with explicit evidence (test names, file paths, code citations)
- AC gatekeeper report filed at checkpoint location
- No blockers remaining
- Ticket ready for Learning Agent

**Risks / Assumptions:**
- **Risk:** Some ACs may not be fully satisfied → **Mitigation:** AC Gatekeeper escalates findings to Implementation Agent for remediation
- **Assumption:** Test evidence is sufficient (fixtures, integration tests validate ACs) → Evidence: (TBD) gatekeeper review

---

### Task 15: Learning & Documentation (Learning Agent)

**Objective:** Extract engineering insights and update project memory/learnings.

**Input:**
- Completed ticket M902-16
- Checkpoint logs from all prior tasks
- Implementation code and test suites
- Spec and tool configurations

**Expected Output:**
- Learning checkpoint at `project_board/checkpoints/M902-16/<timestamp>-learning.md` with:
  - **Key decisions:** Tool selection rationale (gitleaks, bandit, semgrep, pip-audit, npm audit), severity threshold choices (CVSS 7.0), mode strategy (shadow → blocking transition)
  - **Challenges:** Tool output parsing variability, fixture design (balance between realism and safety), timeout tuning
  - **Wins:** Deterministic security scanning, reusable gate pattern from M902-01 framework, comprehensive fixture coverage
  - **Deferred to M903:** Enforcement (exit 1 on failures), grandfathering policy (accepted risks), rule tuning
- Updated project memory entry: `project_memory/security_gate_learned_M902-16.md` with concise reusable facts

**Dependencies:** All prior tasks

**Success Criteria:**
- Learning checkpoint filed
- Project memory updated with reusable learnings
- No forbidden phrases (hack, temporary, XXX, KLUDGE) per M902-06 learning gate policy

---

## Summary Table

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria |
|---|----------------|----------------|-------|-----------------|--------------|------------------|
| 1 | Freeze M902-16 Specification | Spec Agent | Ticket, code_governance.md Stage 8, M902-01/02 examples | Spec v1.0 at `project_board/specs/902_16_security_gate_spec.md` with 8 requirements, all 9 ACs mapped, decisions frozen | None | Spec passes completeness check, all requirements ≥150 words, no ambiguities, frozen v1.0 |
| 2 | Audit Tool Availability | Spec Agent | Spec v1.0, environment, existing configs | Audit doc at `project_board/specs/902_16_tool_audit.md`, tool versions, baseline violations, compatibility matrix | Task 1 | All 5 tools either confirmed available or deferred, baseline captured, no conflicts |
| 3 | Gitleaks Config & Fixtures | Spec Agent | Spec v1.0, audit, gitleaks docs | `.gitleaksignore`, mock secret fixtures at `tests/ci/fixtures/mock_secrets/`, README | Tasks 1–2 | Fixtures are mock (non-functional), gitleaks invocation documented |
| 4 | Bandit Config & Fixtures | Spec Agent | Spec v1.0, audit, bandit docs | `.bandit` config, unsafe pattern fixtures at `tests/ci/fixtures/bandit_unsafe_patterns/`, README | Tasks 1–2 | Fixtures demonstrate B201, B301-B303, B105-B107, valid Python |
| 5 | Semgrep Config & Fixtures | Spec Agent | Spec v1.0, audit, semgrep docs | `.semgrep.yml`, pattern fixtures at `tests/ci/fixtures/semgrep_patterns/`, README | Tasks 1–2 | Rules for auth bypass, unsafe deserialization, SQL injection, hardcoded secrets |
| 6 | Dependency Audit Config & Fixtures | Spec Agent | Spec v1.0, audit, pip-audit/npm audit docs | pip-audit & npm audit commands documented, fixture strategy (isolated test envs), CVSS threshold frozen | Tasks 1–2 | CVSS ≥7.0 hard fail, <7.0 warn, test fixtures never in main dependencies |
| 7 | Design Behavioral Tests | Test Designer | Spec v1.0, configurations (Tasks 3–6), test examples | Test file `tests/ci/test_security_gate_check.py` with 40+ behavioral tests covering all tools/scenarios | Tasks 1–6 | 40+ tests, all tools covered, deterministic, mocked subprocess calls |
| 8 | Develop Adversarial Tests | Test Breaker | Spec v1.0, behavioral tests (Task 7) | Test file `tests/ci/test_security_gate_check_adversarial.py` with 30+ adversarial tests (timeouts, failures, edge cases) | Tasks 1–7 | 30+ tests, determinism + decision priority validated, expected failures pre-implementation |
| 9 | Implement Security Gate Logic | Implementation Agent | Spec v1.0, configurations, tests (Tasks 7–8) | Gate at `ci/scripts/gates/security_gate_check.py`, all tests pass, diff-cover ≥85%, logging/error handling complete | Tasks 1–8 | 70+ tests PASS (40 behavioral + 30 adversarial), gate callable via gate_runner |
| 10 | Register Gate & Integrate | Implementation Agent | Gate (Task 9), gate_registry.json | Updated gate_registry.json entry, invocation command documented in README | Task 9 | Gate discoverable by gate_runner, documentation complete |
| 11 | Create Integration Tests | Test Designer | Fixtures (Tasks 3–6), gate (Task 9) | Integration test file `tests/ci/test_security_gate_check_integration.py` with 15+ real tool tests | Tasks 3–6, 9 | 15+ tests, real tools execute, findings validated, output matches schema |
| 12 | Static QA on Gate | Static QA Agent | Gate code (Task 9) | Ruff/mypy/bandit reports: 0 violations, gate code itself is secure | Task 9 | Ruff E9/F/I: 0, mypy: full coverage, bandit: 0 CRITICAL/HIGH |
| 13 | Completeness Check | Spec Agent (via Orchestrator) | Spec v1.0 (Task 1) | Completeness check PASS result | Task 1 | Spec passes spec_completeness_check.py |
| 14 | AC Gatekeeper Validation | AC Gatekeeper Agent | Ticket, implementation, tests | AC validation report at checkpoint, all 9 ACs verified | Tasks 1–12 | All ACs satisfied with explicit evidence |
| 15 | Learning & Documentation | Learning Agent | All prior work | Learning checkpoint, project memory update | All prior tasks | Learning filed, memory updated, no forbidden phrases |

---

## Notes

### Scope & Constraints
1. **Tool Selection:** Gitleaks (secrets), Bandit (Python security), Semgrep (code patterns), pip-audit (Python deps), npm audit (Node deps) are frozen per code_governance.md Stage 8 and M902-16 ticket.
2. **Severity Thresholds:** Hard-fail = secrets, unsafe deserialization, auth bypass, CVSS ≥7.0; Soft-fail/WARN = CVSS <7.0, medium CVEs, advisories; PASS = no critical findings.
3. **Non-Blocking in M902:** Gate runs in shadow mode (exits 0 regardless of findings); enforcement (exit 1) deferred to M903 per code_governance.md.
4. **Determinism:** Same staged files → identical findings every time (no randomness, no network drift, no tool version sensitivity beyond pinned versions).
5. **Fixture Strategy:** Mock secrets (non-functional), test Python code with unsafe patterns, test dependency lists with known CVEs (isolated, not polluting main codebase).
6. **Test Evidence:** All test names self-documenting (scenario clarity); integration tests validate real tool behavior; behavioral + adversarial tests total 70+.

### Risks & Mitigations
| Risk | Mitigation |
|------|-----------|
| Tool subprocess output parsing fragile | Spec freezes tool versions; tests mock output; real integration tests validate parsing |
| Real secrets accidentally in fixtures | Code review required; gitleaks pre-commit hook to catch accidental leaks |
| Tool timeout insufficient | Spec defines per-tool timeouts (gitleaks 10s, bandit 30s, semgrep 60s, pip-audit 20s, npm 20s, total <120s); tuning in integration tests |
| Dependency audit requires network | Spec uses offline mode if available; CI may have cached registries; fallback: mock CVE responses |
| False positives high-volume | CVSS threshold (7.0+) filters critical; spec freezes baseline for M903 grandfathering |
| Test coverage incomplete | 70+ tests (40 behavioral + 30 adversarial + 15 integration); all 8 gate scenarios and decision matrix covered |

### Dependencies Chain
```
Task 1 (Spec v1.0)
  ├─ Task 2 (Audit)
  │   ├─ Task 3 (Gitleaks)
  │   ├─ Task 4 (Bandit)
  │   ├─ Task 5 (Semgrep)
  │   ├─ Task 6 (Dependency Audit)
  │   └─ Tasks 7–8 (Test Design)
  │       └─ Task 9 (Implementation)
  │           ├─ Task 10 (Registration)
  │           ├─ Task 11 (Integration Tests)
  │           ├─ Task 12 (Static QA)
  │           ├─ Task 13 (Completeness Check)
  │           ├─ Task 14 (AC Validation)
  │           └─ Task 15 (Learning)
```

### File Paths (Ready for Execution)
- Spec: `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_16_security_gate_spec.md`
- Audit: `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_16_tool_audit.md`
- Fixtures (secrets): `/Users/jacobbrandt/workspace/blobert/tests/ci/fixtures/mock_secrets/`
- Fixtures (bandit): `/Users/jacobbrandt/workspace/blobert/tests/ci/fixtures/bandit_unsafe_patterns/`
- Fixtures (semgrep): `/Users/jacobbrandt/workspace/blobert/tests/ci/fixtures/semgrep_patterns/`
- Fixtures (dependencies): `/Users/jacobbrandt/workspace/blobert/tests/ci/fixtures/vulnerable_packages/`
- Gate implementation: `/Users/jacobbrandt/workspace/blobert/ci/scripts/gates/security_gate_check.py`
- Gate registry: `/Users/jacobbrandt/workspace/blobert/ci/scripts/gate_registry.json`
- Tests (behavioral): `/Users/jacobbrandt/workspace/blobert/tests/ci/test_security_gate_check.py`
- Tests (adversarial): `/Users/jacobbrandt/workspace/blobert/tests/ci/test_security_gate_check_adversarial.py`
- Tests (integration): `/Users/jacobbrandt/workspace/blobert/tests/ci/test_security_gate_check_integration.py`
- Checkpoints: `/Users/jacobbrandt/workspace/blobert/project_board/checkpoints/M902-16/`

---

**Status:** EXECUTION PLAN COMPLETE — Ready for Spec Agent to advance to SPECIFICATION stage.
