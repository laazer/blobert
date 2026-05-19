# M902-11 Specification: Stage 3 — Architecture Enforcement Gate

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/11_stage_3_architecture_enforcement_gate.md`  
**Version:** 1.0  
**Status:** DRAFT  
**Date:** 2026-05-19  
**Spec Agent:** Autonomous Checkpoint Protocol

---

## Overview

This specification defines the Stage 3 Architecture Enforcement Gate (M902-11), the fourth stage in an 8-stage governance pipeline. The gate enforces structural architecture rules across Python, TypeScript, and Godot code by aggregating violations from multiple analysis tools. It detects SRP (Single Responsibility Principle) violations, dependency direction violations, duplication clusters, complexity spikes, async safety issues, observability gaps, and data ownership violations. The gate reports findings with severity levels (FAIL, WARN) and returns a structured dict matching the M902-01 gate schema. The gate is **blocking** (enforcement mode) for critical violations and **shadow** (reporting mode) for warnings.

---

## Requirement 01: Gate Module and Registry Entry

### 1. Spec Summary

**Description:** Implement `ci/scripts/gates/architecture_enforcement_check.py` as a Python module that:
- Accepts an `inputs` dict with optional metadata (ticket_id, upstream_agent, downstream_agent, mode)
- Orchestrates multiple static analysis tools (import-linter, eslint-plugin-boundaries, semgrep, jscpd, radon/lizard) to detect architecture violations
- Aggregates violations into a unified report with severity levels (CRITICAL, ERROR, WARN, INFO)
- Computes risk and architecture scores per M902-04 framework
- Returns a dict matching the gate success/failure schema from M902-01
- Exports a `run(inputs: dict) -> dict` function callable by `gate_runner.py`

**Constraints:**
- Must be importable as `ci.scripts.gates.architecture_enforcement_check` and callable by gate_runner
- Must validate output against M902-01 gate schema before returning (all required fields present, types correct)
- Must not swallow exceptions; all tool failures must be logged and transformed to violations or re-raised
- Exception handling follows code_governance.md rules (no bare except, no silent failures)
- Module must be registered in `ci/scripts/gate_registry.json` with entry mapping the gate to module path
- Tool availability handling: if a tool is not installed, skip with WARN-level message; only FAIL if a violation is detected
- Gate must operate in two modes: `shadow` (report only, exit 0) and `blocking` (fail on architecture violations, exit 1 based on severity)

**Assumptions:**
- Tools (import-linter, eslint-plugin-boundaries, semgrep, jscpd, radon, lizard) are available on PATH or can be skipped gracefully
- Tool configurations exist in the repo (.semgrep.yml, .eslintrc, import-linter config, jscpd config)
- Gate runs from blobert repository root directory
- Code to analyze is available and readable (no permission errors expected, but handled if they occur)
- Violations are deterministic across runs (same code yields same violations)

**Scope:**
- Gate module implementation and tool orchestration only; integration into CI/CD workflows is deferred to M903
- Tool configuration tuning (semgrep rule customization, eslint rule selection) is out of scope; assume defaults are correct
- Rule suppression system (blobert-ignore-next-line) is deferred to M903 override system

### 2. Acceptance Criteria

1. **Module exists at correct path:** `ci/scripts/gates/architecture_enforcement_check.py` is present, syntactically valid Python, importable without errors
2. **run() function signature:** Exports `run(inputs: dict) -> dict` where:
   - `inputs` may contain: `ticket_id`, `upstream_agent`, `downstream_agent`, `mode` (shadow|blocking)
   - Returns a dict with fields: `status`, `gate`, `timestamp`, `ticket_id`, `message`, `violations`, `artifacts`, `duration_ms`, `risk_score`, `architecture_score` (see Requirement 02)
   - Function matches M902-01 gate framework contract
3. **Registry entry:** Gate is registered in `ci/scripts/gate_registry.json`:
   ```json
   {
     "name": "architecture_enforcement_check",
     "module": "ci.scripts.gates.architecture_enforcement_check",
     "run_function": "run",
     "required_inputs": [],
     "optional_inputs": ["mode", "ticket_id", "upstream_agent", "downstream_agent"],
     "default_mode": "shadow",
     "description": "Enforces SRP, dependency direction, duplication, and complexity rules via import-linter, eslint-plugin-boundaries, semgrep, jscpd, radon/lizard"
   }
   ```
4. **Exit codes:** Shadow mode always exits 0; blocking mode exits 0 on PASS, 1 on FAIL/ESCALATE
5. **Exception handling:** No bare `except:` or silent swallowing; all exceptions logged with context and either re-raised or transformed to violations
6. **Tool availability:** Graceful degradation when tools are unavailable (skip + WARN), not FAIL

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Tool not installed:** If import-linter, semgrep, jscpd, or radon is not on PATH, gate should skip that tool and record a WARN violation. Mitigation: Wrap tool invocation in try/except; continue with next tool; record skip in violations array.
- **Tool output format changes:** If a tool's JSON output format changes between versions, parser may fail. Mitigation: Defensive parsing with fallback (treat unparseable output as "tool error, not violation"); log tool version.
- **Multiple tools report same violation:** If semgrep and eslint both detect a circular import, gate should deduplicate violations. Mitigation: Use violation fingerprint (file + line + rule_id) to deduplicate.
- **Tool execution hangs:** If a tool hangs (infinite loop), subprocess will block indefinitely. Mitigation: Wrap each tool in `subprocess.run(..., timeout=<tool_timeout>)`.
- **Output message unclear:** If gate returns a message that doesn't match expected templates, user is confused about severity. Mitigation: Freeze message templates in Requirement 02; tests verify exact message.
- **Risk/architecture score computation wrong:** If score thresholds are misaligned, gate may escalate/fail incorrectly. Mitigation: Freeze computation rules in Requirement 02; tests verify score calculation.

**Ambiguities resolved by checkpoint protocol:**
- Q1: Shadow vs blocking mode semantics (shadow is non-blocking, for M903 orchestrator to decide routing; blocking fails on violations)
- Q2: Tool invocation order (tooling order is atomic; deduplication happens after aggregation)
- Q3: Severity mapping (CRITICAL/ERROR = SRP/dependency, WARN = complexity/duplication, INFO = minor issues)
- Q4: Risk score computation (weighted average of violation severities per M902-04)
- Q5: Architecture score computation (100 - (AR violations * 10), clamped [0, 100])

### 4. Clarifying Questions

None. Scope and constraints are frozen.

---

## Requirement 02: Output Contract and Schema

### 1. Spec Summary

**Description:** The gate returns a structured dict conforming to the M902-04 gate result schema. Output includes violations, risk/architecture scores, and severity classifications.

**On Success (status = "PASS"):**
- `status` = "PASS" (no violations, or only INFO/WARN violations in shadow mode)
- `gate` = "architecture_enforcement_check"
- `timestamp` = ISO 8601 UTC timestamp (e.g., "2026-05-19T00-00-00Z")
- `ticket_id` = provided in inputs or "M902-11" if omitted
- `message` = plain-text summary (e.g., "Architecture rules enforced: 0 violations detected")
- `violations` = array of violation objects (may be empty if PASS; may contain WARN violations in shadow mode)
- `risk_score` = integer [0–100], weighted average of violation severities
- `architecture_score` = integer [0–100], computed as 100 - (AR_violations * 10)
- `artifacts` = empty list (no re-staged files)
- `duration_ms` = elapsed time in milliseconds

**On Failure (status = "FAIL"):**
- `status` = "FAIL" (critical violations detected, or blocking mode with any violations)
- `gate` = "architecture_enforcement_check"
- `timestamp` = ISO 8601 UTC timestamp
- `ticket_id` = provided in inputs or "M902-11" if omitted
- `message` = plain-text summary of failure reason (e.g., "Architecture violations detected: 3 SRP violations in controllers")
- `violations` = array of violation objects (one per detected violation, sorted by severity)
- `risk_score` = integer [0–100]
- `architecture_score` = integer [0–100]
- `artifacts` = empty list
- `duration_ms` = elapsed time

**On Escalation (status = "ESCALATE"):**
- `status` = "ESCALATE" (high-risk violations, e.g., circular imports, async safety violations)
- Same fields as FAIL, but message indicates escalation reason

**Violation object structure (required fields):**
```python
{
  "tool": "import-linter",  # Tool name (import-linter, semgrep, eslint-plugin-boundaries, jscpd, radon, lizard)
  "severity": "ERROR",      # CRITICAL | ERROR | WARN | INFO
  "file": "asset_generation/python/src/model_registry/registry.py",  # File path relative to repo root
  "line": 42,               # Line number (1-based)
  "column": 0,              # Column number (0 if not applicable)
  "rule_id": "AR-01",       # Rule code (e.g., AR-01, EX-01, DUP-01, CX-01)
  "message": "Domain module 'model_registry' imports from 'routers' (forbidden cross-layer import)"
}
```

**Status determination logic:**
```
if architecture_score <= 30 or any(violation.severity == CRITICAL):
    status = "ESCALATE"
elif risk_score > 90 or any(violation.severity == ERROR):
    status = "FAIL"
elif risk_score > 50 or any(violation.severity == WARN):
    status = "WARN"
else:
    status = "PASS"

# Override: shadow mode always returns PASS even if violations present (non-blocking)
if mode == "shadow":
    status = "PASS"
```

**Severity mapping:**
- **CRITICAL:** Blocked execution required (e.g., circular imports, async safety violations, reflection abuse)
- **ERROR:** Architecture violation (e.g., SRP, dependency direction, forbidden cross-layer import)
- **WARN:** Complexity/quality warning (e.g., function size spike, duplication, missing observability)
- **INFO:** Minor issue or metric (e.g., duplication below threshold)

**Constraints:**
- All field names match schema exactly (case-sensitive)
- All values are JSON-serializable
- Message field is single-line, <300 chars
- Timestamp is ISO 8601 UTC with Z suffix
- status must be one of: "PASS", "FAIL", "WARN", "ESCALATE"
- violations array is sorted by severity (CRITICAL first, then ERROR, WARN, INFO)
- Violation rule_id must start with a category prefix: AR- (architecture), EX- (exception), RF- (reflection), AS- (async), OB- (observability), DUP- (duplication), CX- (complexity)

**Assumptions:**
- Gate runner will validate output schema after gate returns
- Downstream orchestrator will interpret status and severity to decide routing
- Tests will verify schema compliance via JSON schema validation

**Scope:** Output schema and message semantics only; downstream routing is out of scope.

### 2. Acceptance Criteria

1. **Schema compliance:** Returned dict matches M902-04 gate-result schema (success and failure variants)
2. **Message clarity:** Message field is human-readable and accurately describes the outcome
3. **Violation structure:** Each violation has required fields (tool, severity, file, line, column, rule_id, message)
4. **Severity mapping:** Violations are classified with correct severity (CRITICAL, ERROR, WARN, INFO)
5. **Risk score:** Computed as weighted average of violation severities (CRITICAL=100, ERROR=80, WARN=50, INFO=10)
6. **Architecture score:** Computed as 100 - (AR_violations * 10), clamped [0, 100]
7. **Status determination:** status is correctly set based on scores and mode (shadow always PASS)
8. **Sorting:** violations array is sorted by severity (descending)
9. **JSON serializability:** Returned dict can be serialized via json.dumps() without errors
10. **Timestamp format:** Timestamp is ISO 8601 UTC with Z suffix

### 3. Risk & Ambiguity Analysis

**Ambiguities resolved:**
- **Should shadow mode return PASS even with violations?** Yes. Shadow mode is reporting-only; violations are recorded but status is PASS (non-blocking).
- **What if multiple tools report the same violation?** Deduplicate by fingerprint (file + line + rule_id); keep one entry with merged context.
- **How are violations sorted in output?** By severity (CRITICAL/ERROR/WARN/INFO descending), then by file path (ascending).

### 4. Clarifying Questions

None. Output contract is frozen.

---

## Requirement 03: Tool Orchestration and Integration

### 1. Spec Summary

**Description:** The gate orchestrates five primary tools and coordinates their invocations:

**Tools and responsibilities:**

1. **import-linter (Python dependency graph):** Detects forbidden import patterns, circular imports, layer boundary violations
   - Config: `asset_generation/python/.import-linter` (assumed present)
   - Scope: `asset_generation/python/src`
   - Violations: AR-02 (reverse imports), AR-04 (circular imports), AR-05 (cross-layer imports)

2. **eslint-plugin-boundaries (TypeScript architecture):** Enforces feature boundaries, import restrictions
   - Config: `asset_generation/web/frontend/.eslintrc` (assumed present with boundaries plugin)
   - Scope: `asset_generation/web/frontend/src`
   - Violations: AR-03 (cross-feature coupling), AR-06 (boundary violation)

3. **semgrep (custom architecture rules):** Detects SRP violations, reflection abuse, forbidden patterns
   - Config: `asset_generation/python/.semgrep.yml` or `project_board/semgrep/architecture.yml` (custom rules)
   - Scope: `asset_generation/python/src`, `asset_generation/web/backend`
   - Violations: AR-01 (domain HTTP import), AR-07 (forbidden reflection), AR-08 (service logic leakage)

4. **jscpd (cross-file duplication):** Detects code duplication clusters (8+ lines)
   - Config: `jscpd.json` (assumed present)
   - Scope: all source files
   - Violations: DUP-01 (duplication cluster detected)

5. **radon/lizard (complexity metrics):** Detects function size spikes, nesting depth, cognitive complexity
   - Scope: Python code (`asset_generation/python/src`)
   - Violations: CX-01 (function too long), CX-02 (nesting depth exceeded), CX-03 (high cognitive complexity)

**Tool invocation sequence (atomic, no parallelization):**

1. Run import-linter on Python code → collect violations
2. Run eslint-plugin-boundaries on TypeScript code → collect violations
3. Run semgrep on Python + backend → collect violations
4. Run jscpd on all source code → collect violations
5. Run radon on Python code → collect violations
6. Aggregate all violations, deduplicate, sort by severity
7. Compute risk and architecture scores
8. Determine status and return result dict

**Tool execution strategy:**

- **Tool unavailable:** If a tool is not installed or config file missing, log WARN, record skip, continue to next tool. Do not FAIL.
- **Tool failure:** If a tool exits with non-zero code or raises exception, log ERROR, record violation with `rule_id: "TOOL_ERROR"`, continue to next tool.
- **Tool timeout:** If tool exceeds timeout (tool-specific, see timeouts below), log ERROR, record violation, continue to next tool.
- **Output parsing error:** If tool output cannot be parsed (invalid JSON, unparseable format), log WARNING, skip violations from that tool, continue.

**Tool timeout constraints:**
- import-linter: 60 seconds
- eslint-plugin-boundaries: 60 seconds
- semgrep: 120 seconds
- jscpd: 120 seconds
- radon: 60 seconds
- lizard: 60 seconds

**Tool availability checks:**
- import-linter: Try `lint-imports --version`
- eslint: Try `npx eslint --version` (npm required)
- semgrep: Try `semgrep --version`
- jscpd: Try `npx jscpd --version` (npm required)
- radon: Try `radon --version`
- lizard: Try `lizard --version`

**Deduplication strategy:**

After aggregating violations from all tools, deduplicate by fingerprint: `(file, line, rule_id)`. If multiple tools report violations with the same fingerprint, keep the most severe violation and merge messages (e.g., "import-linter + semgrep: circular import detected in model_registry").

**Constraints:**
- Tools must be invoked in the order specified (atomic sequence, no parallelization)
- Each tool invocation must have a timeout and be caught
- Tool output must be parsed defensively (invalid JSON returns empty violations list, not error)
- All tool invocations must be logged (DEBUG level for tool runs, ERROR for failures)

**Assumptions:**
- Tool configs exist in repo and are correct (not overridden or customized by gate)
- Tools are deterministic (same code yields same violations)
- Tool invocations do not modify filesystem (read-only operations)

**Scope:**
- Tool orchestration and invocation only; tool configuration customization is out of scope
- Rule creation/customization is out of scope (tool defaults are used)

### 2. Acceptance Criteria

1. **Tool invocation:** All five tools are invoked in specified order (import-linter → eslint → semgrep → jscpd → radon)
2. **Tool configs:** Gate uses tool configs from repo (no CLI overrides)
3. **Timeout handling:** Each tool has timeout; `subprocess.TimeoutExpired` is caught and logged
4. **Unavailable tool:** If tool not installed, gate logs WARN and continues (does not FAIL)
5. **Tool error:** If tool exits non-zero, gate logs ERROR, records violation, continues
6. **Output parsing:** Tool JSON output is parsed defensively; invalid output yields empty violations list
7. **Violation aggregation:** All violations from all tools are collected in single array
8. **Deduplication:** Violations with identical (file, line, rule_id) are deduplicated
9. **Sorting:** Violations are sorted by severity (CRITICAL/ERROR/WARN/INFO descending)
10. **Logging:** All tool invocations are logged at DEBUG level; failures at ERROR level

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Tool version mismatch:** Different versions of tools may report different violations. Mitigation: Spec assumes current versions are correct; version management is deferred to upstream package managers.
- **Tool config incorrect:** If tool configs (.semgrep.yml, .eslintrc, etc.) have wrong rules, gate will report false positives. Mitigation: Assume configs are correct per project standards; tests use known-good configs.
- **Parallel tool execution:** If tools modify shared state, parallelization will cause race conditions. Mitigation: Tools are sequential (atomic); parallelization is deferred to M903 (out of scope here).
- **Very large codebase:** jscpd and semgrep may timeout on large repos. Mitigation: Define reasonable timeouts (120s) and accept that very large analysis may need optimization in M903.

**Ambiguities resolved:**
- **Tool execution order matters?** No hard requirement; order is arbitrary. Current order (import-linter → eslint → semgrep → jscpd → radon) is chosen for pedagogical clarity.
- **If import-linter unavailable, skip only import-linter violations?** Yes. Semgrep can also detect circular imports; both tools run independently and deduplicate results.

### 4. Clarifying Questions

None. Tool orchestration is frozen.

---

## Requirement 04: SRP Violation Detection

### 1. Spec Summary

**Description:** The gate detects Single Responsibility Principle violations by enforcing strict layer boundaries and purpose constraints. SRP violations are classified as **ERROR** severity.

**SRP rules (frozen from code_governance.md Stage 3):**

**AR-01: Domain must not import HTTP libraries**
- Scope: `asset_generation/python/src/model_registry`, `asset_generation/python/src/enemies`, `asset_generation/python/src/player`, `asset_generation/python/src/materials`
- Pattern: Import of `fastapi`, `flask`, `requests`, `urllib`, `http`, `aiohttp`
- Detection: Semgrep rule or import-linter contract
- Severity: ERROR
- Message: "Domain module '<module>' imports from '<http_library>' (forbidden; domain is business logic only)"

**AR-02: Services must not construct HTTP responses**
- Scope: `asset_generation/web/backend/services`
- Pattern: Use of `JSONResponse`, `fastapi.Response`, `flask.make_response`
- Detection: Semgrep rule
- Severity: ERROR
- Message: "Service '<service>' constructs HTTP response (forbidden; services are orchestration only, responses belong in routers)"

**AR-03: Routers/Controllers must not contain business logic**
- Scope: `asset_generation/web/backend/routers`, `scripts/` (Godot controllers)
- Pattern: Function length >10 LOC without service delegation, or direct domain logic
- Detection: Semgrep rule, eslint-plugin-boundaries
- Severity: ERROR
- Message: "Router '<router>' contains business logic (>10 LOC without service delegation)"

**AR-04: Services/Adapters must not import from routers**
- Scope: `asset_generation/web/backend/services`, `asset_generation/web/backend/core`
- Pattern: Import from `..routers` or `routers` module
- Detection: import-linter contract or semgrep rule
- Severity: ERROR
- Message: "Module '<service>' imports from 'routers' (forbidden; breaks layering)"

**AR-05: Infrastructure must not leak to business logic**
- Scope: `asset_generation/python/src` (all business logic modules)
- Pattern: Direct use of database clients, HTTP clients, file I/O beyond persistence layer
- Detection: Semgrep rule
- Severity: ERROR
- Message: "Module '<module>' uses infrastructure service '<service>' directly (forbidden; must use repository pattern)"

**AR-06: Repository pattern enforced**
- Scope: `asset_generation/web/backend/services`, `asset_generation/python/src`
- Pattern: Persistence writes (db.insert, db.update, db.delete) must be in repository layer only
- Detection: Semgrep rule
- Severity: ERROR
- Message: "Module '<module>' contains persistence write (forbidden; only repositories write data)"

**Detection methods:**
- **import-linter:** Define contracts in `.import-linter` config (Python dependency graph)
- **semgrep:** Custom rules in `.semgrep.yml` for forbidden imports and patterns
- **eslint-plugin-boundaries:** Feature boundary rules for TypeScript (cross-feature imports)

**Constraints:**
- SRP violations are **never warnings**; they are always ERROR or CRITICAL
- Each SRP violation must include the module name, the forbidden action, and the rule
- SRP violations should block commits in blocking mode (FAIL status)

**Assumptions:**
- Tool configs (import-linter contracts, semgrep rules, eslint-plugin-boundaries) are present and correct
- Code changes to business logic layers are tested independently to verify SRP is maintained

**Scope:**
- SRP detection rules only; rule customization is deferred to M903

### 2. Acceptance Criteria

1. **AR-01 (domain HTTP import):** Detected via semgrep or import-linter; severity ERROR
2. **AR-02 (service HTTP response):** Detected via semgrep; severity ERROR
3. **AR-03 (router business logic):** Detected via semgrep or eslint-plugin-boundaries; severity ERROR
4. **AR-04 (service router import):** Detected via import-linter contract or semgrep; severity ERROR
5. **AR-05 (infrastructure leak):** Detected via semgrep; severity ERROR
6. **AR-06 (persistence write outside repo):** Detected via semgrep; severity ERROR
7. **Messaging:** Each violation includes module name and forbidden action
8. **Sorting:** SRP violations appear before other violations (ERROR severity)

### 3. Risk & Ambiguity Analysis

**Risks:**
- **False positives:** If tool configs are too strict, legitimate code may be flagged (e.g., test infrastructure in domain code). Mitigation: Tool configs are reviewed and frozen; tests verify no false positives on known-good code.
- **Tool coverage gaps:** If one tool detects SRP violations but another doesn't, coverage is inconsistent. Mitigation: Semgrep and import-linter both run; redundancy increases detection confidence.

**Ambiguities resolved:**
- **Should SRP violations always block?** Yes (ERROR severity). SRP is non-negotiable.
- **How strict should AR-03 (router logic detection) be?** Function length >10 LOC is a heuristic; exact implementation is tool-dependent.

### 4. Clarifying Questions

None. SRP rules are frozen.

---

## Requirement 05: Dependency Direction and Circular Import Detection

### 1. Spec Summary

**Description:** The gate detects violations of dependency direction rules (no reverse edges) and circular imports, which are **CRITICAL** severity violations.

**Rules:**

**AR-07: No reverse dependency edges**
- Trigger: If module A depends on module B, B must not depend on A
- Examples: Controllers must not import from services; services must not import from routers
- Detection: import-linter (Python), eslint-plugin-boundaries (TypeScript)
- Severity: CRITICAL
- Message: "Circular dependency: '<module_a>' ↔ '<module_b>' (blocks compilation/runtime)"

**AR-08: No circular imports**
- Trigger: If A imports B, B imports C, C imports A (cycle)
- Detection: import-linter (Python), semgrep (TypeScript)
- Severity: CRITICAL
- Message: "Circular import detected: '<module_a>' → '<module_b>' → ... → '<module_a>'"

**Detection methods:**
- **import-linter:** Python dependency graph analysis; detects cycles and reverse edges
- **eslint-plugin-boundaries:** TypeScript architecture analysis; detects feature boundary cycles
- **semgrep:** Cross-module import chain analysis (Python + TypeScript)

**Constraints:**
- Circular imports must **always block** (FAIL status in blocking mode, ESCALATE in high-risk score scenarios)
- Messages must include the import chain (A → B → C → A) for debugging
- Violations are deduplicated by cycle (if A → B → A and A → B → C → A, keep only the longer cycle)

**Assumptions:**
- All modules are syntactically correct (no parse errors)
- Code compiles without import resolution errors (circular imports are only detected in static analysis)

**Scope:**
- Cycle detection only; cyclic refactoring strategies are out of scope

### 2. Acceptance Criteria

1. **Reverse edge detection:** If A depends on B, B ↔ A import is flagged as CRITICAL
2. **Cycle detection:** A → B → C → A is flagged as CRITICAL
3. **Message clarity:** Message includes full import chain for debugging
4. **Deduplication:** Duplicate cycles are merged into one violation
5. **Blocking:** Circular imports always result in FAIL or ESCALATE (not WARN/INFO)

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Tool coverage gaps:** If import-linter misses a cycle, code will compile but fail at runtime. Mitigation: Tests include cycle detection test cases; manual code review catches missed cycles.
- **False positives:** Conditional imports or dynamic imports may not be detected correctly. Mitigation: Tool configs exclude test-only imports; spec assumes static analysis is conservative.

**Ambiguities resolved:**
- **Should cycles always escalate?** Yes (CRITICAL severity). Cycles are runtime hazards.

### 4. Clarifying Questions

None. Dependency direction rules are frozen.

---

## Requirement 06: Duplication Detection

### 1. Spec Summary

**Description:** The gate detects code duplication clusters (8+ lines of repeated code across files) using jscpd. Duplication is classified as **WARN** severity (not blocking, but flags code entropy).

**Rules:**

**DUP-01: Cross-file duplication clusters (8+ lines)**
- Trigger: Two or more files contain identical code blocks of 8+ contiguous lines
- Detection: jscpd with threshold 8 lines, min tokens configurable
- Severity: WARN
- Message: "Duplication cluster: '<file_a>' lines 42–49 duplicates '<file_b>' lines 100–107 (8 lines, <token_count> tokens)"

**DUP-02: High duplication ratio (>5% of codebase)**
- Trigger: Codebase duplication ratio exceeds 5%
- Detection: jscpd summary report
- Severity: WARN (informational, not blocking)
- Message: "Code duplication ratio: 7% of codebase is duplicated (consider refactoring hotspots)"

**Constraints:**
- Duplication violations are **never ERROR**; they are WARN or INFO
- Duplication does not block commits (non-blocking severity)
- Deduplication strategy: If same duplication cluster is reported by multiple files, keep one violation with all affected files listed
- Ignore test code duplication (test files excluded from analysis, or flagged separately)

**Assumptions:**
- jscpd is configured with correct file patterns and token threshold
- Duplication detection ignores whitespace-only changes (configured in jscpd)

**Scope:**
- Duplication detection and reporting only; refactoring strategies are out of scope

### 2. Acceptance Criteria

1. **Duplication detection:** 8+ line clusters are detected and reported
2. **Message clarity:** Message includes file pairs and line ranges
3. **Non-blocking:** Duplication violations are WARN, not ERROR
4. **Ratio reporting:** Overall duplication ratio is computed and reported

### 3. Risk & Ambiguity Analysis

**Risks:**
- **False positives from boilerplate:** Generated code, boilerplate imports, or template code may be flagged as duplication. Mitigation: jscpd config can exclude patterns; test results validate no false positives on known-good code.
- **High duplication baseline:** If project already has 10% duplication, WARN threshold may not be meaningful. Mitigation: Threshold is configurable; can be adjusted per project baseline.

**Ambiguities resolved:**
- **Should duplication always warn?** Yes. Duplication is a symptom of entropy; even if not blocking, it should be visible.

### 4. Clarifying Questions

None. Duplication rules are frozen.

---

## Requirement 07: Complexity Detection

### 1. Spec Summary

**Description:** The gate detects complexity spikes (function size, nesting depth, cognitive complexity) using radon and lizard. Complexity violations are classified as **WARN** severity (not blocking, but flags maintenance risk).

**Rules:**

**CX-01: Function size exceeded (>50 LOC)**
- Trigger: Function/method body exceeds 50 lines
- Detection: radon (via `radon cc`) or lizard
- Severity: WARN
- Message: "Function '<module>.<function>' exceeds size limit: 87 LOC (threshold: 50)"

**CX-02: Nesting depth exceeded (>4 levels)**
- Trigger: Code nesting (if/for/while/try chains) exceeds 4 levels
- Detection: radon (via `radon metrics`) or lizard
- Severity: WARN
- Message: "Nesting depth in '<module>.<function>' exceeds limit: 5 levels (threshold: 4)"

**CX-03: Cognitive complexity high (>10)**
- Trigger: Cyclomatic complexity or cognitive complexity exceeds 10
- Detection: radon (via `radon cc`) or semgrep (cognitive complexity rules)
- Severity: WARN
- Message: "Cognitive complexity in '<module>.<function>' is high: 14 (threshold: 10)"

**CX-04: Class size exceeded (>200 LOC)**
- Trigger: Class body exceeds 200 lines
- Detection: radon or lizard
- Severity: WARN
- Message: "Class '<module>.<class>' exceeds size limit: 320 LOC (threshold: 200)"

**Constraints:**
- Complexity violations are **never ERROR**; they are WARN or INFO
- Complexity does not block commits (non-blocking severity)
- Thresholds are frozen in this spec; customization deferred to M903
- Violations are aggregated by module; message includes specific function/class names

**Assumptions:**
- radon and lizard configs are present and correct (or use defaults)
- Complexity metrics are deterministic across runs

**Scope:**
- Complexity detection and reporting only; refactoring strategies are out of scope
- Performance complexity (runtime analysis, query optimization) is out of scope

### 2. Acceptance Criteria

1. **Function size detection:** Functions >50 LOC are flagged as WARN
2. **Nesting depth detection:** Nesting >4 levels is flagged as WARN
3. **Cognitive complexity detection:** Complexity >10 is flagged as WARN
4. **Class size detection:** Classes >200 LOC are flagged as WARN
5. **Message clarity:** Messages include actual vs threshold values
6. **Non-blocking:** Complexity violations are WARN, not ERROR

### 3. Risk & Ambiguity Analysis

**Risks:**
- **False positives from boilerplate:** Generated code or auto-formatted large data structures may be flagged. Mitigation: jscpd and semgrep can exclude generated files; config handles this.
- **Threshold misalignment:** If thresholds are too strict or too loose, warnings are not actionable. Mitigation: Thresholds are community standards (radon defaults); can be tuned in M903.

**Ambiguities resolved:**
- **Should complex code block commits?** No. Complexity is a maintenance signal, not a blocking rule (WARN severity).

### 4. Clarifying Questions

None. Complexity rules are frozen.

---

## Requirement 08: Async Safety Violations

### 1. Spec Summary

**Description:** The gate detects async safety violations (blocking I/O in async context, unbounded task spawning) using semgrep rules. Async violations are classified as **CRITICAL** severity (must not block async execution).

**Rules:**

**AS-01: No blocking I/O in async functions**
- Trigger: Async function contains blocking I/O (e.g., `requests.get()`, `open()`, `time.sleep()`)
- Detection: Semgrep rule pattern matching
- Severity: CRITICAL (blocks event loop)
- Message: "Blocking call '<function>' in async function '<module>.<async_func>' (will block event loop)"

**AS-02: No unbounded task spawning**
- Trigger: Async context creates unbounded number of tasks (e.g., `for item in items: asyncio.create_task(...)`)
- Detection: Semgrep rule pattern matching
- Severity: CRITICAL (resource exhaustion risk)
- Message: "Unbounded task spawning detected in '<module>.<function>' (no limit on concurrent tasks)"

**AS-03: Missing timeout on async operations**
- Trigger: `asyncio.wait()`, `asyncio.gather()` called without timeout parameter
- Detection: Semgrep rule
- Severity: WARN (potential deadlock risk)
- Message: "Async operation '<function>' in '<module>' missing timeout (risk of permanent blocking)"

**AS-04: No missing await on coroutine**
- Trigger: Coroutine created but not awaited (e.g., `func()` instead of `await func()`)
- Detection: Semgrep rule or mypy
- Severity: ERROR (silent failure risk)
- Message: "Coroutine '<module>.<function>' not awaited (will silently fail)"

**Constraints:**
- Async violations with CRITICAL severity must block (FAIL/ESCALATE status)
- Violations must include the blocking call and the async function name
- Async rules are Python-specific (async/await syntax)

**Assumptions:**
- Semgrep rules for async safety are configured in `.semgrep.yml` or external rule pack
- Async code is written using `asyncio` library (FastAPI async route handlers)

**Scope:**
- Async safety detection only; async design patterns are out of scope

### 2. Acceptance Criteria

1. **Blocking I/O detection:** Blocking calls in async functions are flagged as CRITICAL
2. **Task spawning detection:** Unbounded task creation is flagged as CRITICAL
3. **Timeout detection:** Missing timeouts on async ops are flagged as WARN
4. **Await detection:** Missing awaits are flagged as ERROR
5. **Message clarity:** Messages include blocking call and function names

### 3. Risk & Ambiguity Analysis

**Risks:**
- **False positives from thread pools:** If blocking calls are delegated to thread pools (e.g., `loop.run_in_executor()`), they are safe. Mitigation: Semgrep rules exclude executor patterns; tests validate no false positives.
- **Missing semgrep rules:** If async rules are not configured, no violations will be detected. Mitigation: Spec assumes rules are configured; implementation includes rule config files.

**Ambiguities resolved:**
- **Should async violations always block?** Yes (CRITICAL severity). Async blocking is a runtime hazard.

### 4. Clarifying Questions

None. Async safety rules are frozen.

---

## Requirement 09: Observability Rule Enforcement

### 1. Spec Summary

**Description:** The gate detects observability gaps (missing structured logging, missing correlation IDs, missing audit events) using semgrep rules. Observability violations are classified as **WARN** severity (not blocking, but flags ops risk).

**Rules:**

**OB-01: Structured logging required**
- Trigger: Function uses raw `logger.info()` or `print()` instead of structured logging (e.g., `logger.info(..., extra={...})`)
- Detection: Semgrep rule pattern matching
- Severity: WARN
- Message: "Function '<module>.<function>' uses unstructured logging (should use structured logging with context dict)"

**OB-02: Missing correlation/request ID**
- Trigger: API handler or critical path does not propagate correlation ID
- Detection: Semgrep rule pattern matching
- Severity: WARN
- Message: "Critical path '<module>.<function>' missing correlation ID (trace propagation impossible)"

**OB-03: Missing audit event on critical operations**
- Trigger: Database write, permission check, or security-sensitive operation lacks audit logging
- Detection: Semgrep rule pattern matching
- Severity: WARN
- Message: "Critical operation '<module>.<function>' missing audit event (no compliance trace)"

**Constraints:**
- Observability violations are **never ERROR**; they are WARN or INFO
- Violations do not block commits (non-blocking severity)
- Rules are heuristic-based (not exhaustive); gaps may exist

**Assumptions:**
- Structured logging library is available (e.g., `structlog`, `pythonjsonlogger`)
- Audit event framework is defined (deferred to observability layer)

**Scope:**
- Observability detection and reporting only; logging implementation is out of scope

### 2. Acceptance Criteria

1. **Logging structure detection:** Unstructured logging is flagged as WARN
2. **Correlation ID detection:** Missing correlation IDs in critical paths are flagged
3. **Audit event detection:** Missing audit events on security operations are flagged
4. **Non-blocking:** Observability violations are WARN, not ERROR

### 3. Risk & Ambiguity Analysis

**Risks:**
- **False positives from intentional unstructured logging:** Some logging may be intentionally simple (e.g., debug output). Mitigation: Rules can be tuned to exclude debug-level logs or specific contexts.
- **Hard to define "critical path":** Which functions require correlation IDs? Mitigation: Spec is conservative; annotations or explicit function names can define critical paths (deferred to M903).

**Ambiguities resolved:**
- **Should observability violations block?** No. Observability gaps are risks, not blockers (WARN severity).

### 4. Clarifying Questions

None. Observability rules are frozen.

---

## Requirement 10: Data Ownership and Mutation Boundary Violations

### 1. Spec Summary

**Description:** The gate detects data ownership violations (cross-layer state mutation, persistence writes outside repository layer) using semgrep rules. Mutation violations are classified as **ERROR** severity (architecture violation).

**Rules:**

**MUT-01: No cross-layer state mutation**
- Trigger: Service layer directly mutates domain object (e.g., `model.field = value` instead of `repo.update(model)`)
- Detection: Semgrep rule pattern matching
- Severity: ERROR
- Message: "Service '<module>.<function>' directly mutates domain object (must use repository pattern)"

**MUT-02: Persistence writes outside repository layer**
- Trigger: Non-repository code calls `db.insert()`, `db.update()`, `db.delete()` or ORM methods
- Detection: Semgrep rule pattern matching
- Severity: ERROR
- Message: "Module '<module>.<function>' contains persistence write (forbidden; only repositories write data)"

**MUT-03: DTO ownership violation**
- Trigger: DTO is instantiated or mutated outside designated owner layer
- Detection: Semgrep rule (requires custom rule per DTO)
- Severity: WARN (soft rule; may be acceptable in some contexts)
- Message: "DTO '<dto_class>' instantiated in '<module>' (owner is '<owner_layer>')"

**Constraints:**
- Mutation violations are **ERROR** (blocking in architecture)
- Violations must identify the object/DTO and the violating function
- Repository pattern is the only allowed way to write data (no direct database access elsewhere)

**Assumptions:**
- Repository layer is clearly delineated (e.g., `asset_generation/web/backend/repositories`)
- DTO ownership is documented via comments or type hints

**Scope:**
- Mutation boundary detection only; data design patterns are out of scope

### 2. Acceptance Criteria

1. **Cross-layer mutation detection:** Direct domain object mutation in services is flagged as ERROR
2. **Persistence write detection:** Database calls outside repository are flagged as ERROR
3. **DTO ownership detection:** DTO instantiation in non-owner layers is flagged as WARN
4. **Message clarity:** Messages identify the object and violating function

### 3. Risk & Ambiguity Analysis

**Risks:**
- **False positives from intentional mutations:** Some layers may intentionally mutate domain objects (e.g., DTOs for serialization). Mitigation: Rules can be tuned to allow intentional patterns; annotations (type hints, comments) guide rule behavior.
- **Hard to define ownership:** Which layer owns a DTO? Mitigation: Ownership is declared via naming convention or explicit comments (deferred to M903).

**Ambiguities resolved:**
- **Should mutation violations always block?** Yes (ERROR severity). Mutation boundaries are architectural.

### 4. Clarifying Questions

None. Mutation rules are frozen.

---

## Requirement 11: Error Handling and Tool Resilience

### 1. Spec Summary

**Description:** The gate handles tool unavailability, tool failures, and parsing errors gracefully. No errors are silently swallowed.

**Error handling rules:**

**Tool unavailable (graceful skip):**
- Trigger: Tool binary not on PATH or tool config file missing
- Action: Log WARN, record skip in violations, continue to next tool
- Return status: PASS (non-blocking; skip is graceful degradation)

**Tool failure (hard error):**
- Trigger: Tool exits non-zero or raises exception
- Action: Log ERROR, record violation with `rule_id: TOOL_ERROR`, attempt to parse partial output, continue to next tool
- Return status: FAIL (tool error is blocking; gate did not complete successfully)

**Tool timeout (hard error):**
- Trigger: Tool exceeds timeout
- Action: Log ERROR, record violation with `rule_id: TOOL_TIMEOUT`, continue to next tool
- Return status: FAIL

**Output parsing error (graceful skip):**
- Trigger: Tool output cannot be parsed (invalid JSON, unexpected format)
- Action: Log WARN, skip violations from that tool, continue to next tool
- Return status: PASS (parsing error is not a gate failure; skip that tool's output)

**Git/filesystem error (hard error):**
- Trigger: Cannot read source files or analyze codebase
- Action: Log ERROR, record violation with `rule_id: FS_ERROR`, return FAIL
- Return status: FAIL

**Exception handling patterns (per code_governance.md):**

```python
# ALLOWED: Explicit recovery with clear semantics
try:
    subprocess.run(['import-linter', '--version'], check=True, timeout=5)
except (OSError, FileNotFoundError):
    logger.warning("import-linter not installed; skipping")
    violations.append({'rule_id': 'TOOL_UNAVAILABLE', 'tool': 'import-linter', ...})
    continue

# ALLOWED: Log + re-raise or return FAIL
try:
    result = subprocess.run(['semgrep', ...], timeout=120, check=True, ...)
except subprocess.TimeoutExpired as e:
    logger.error(f"semgrep timed out: {e}")
    violations.append({'rule_id': 'TOOL_TIMEOUT', 'tool': 'semgrep', ...})
    return {"status": "FAIL", ...}

# FORBIDDEN: Silent swallowing
try:
    subprocess.run(['semgrep', ...], timeout=120)
except Exception:
    pass  # FORBIDDEN
```

**Constraints:**
- All errors must be logged (at minimum, ERROR level for failures, WARN for skips)
- All tool failures must result in violations being recorded
- Graceful skips (tool unavailable, parsing error) do not result in FAIL status
- Hard failures (tool error, timeout, filesystem error) result in FAIL status

**Assumptions:**
- Logging module is configured (gate uses stdlib `logging`)
- Violations array includes error violations mixed with detection violations

**Scope:**
- Error handling at gate module level only; higher-level error recovery is out of scope

### 2. Acceptance Criteria

1. **No silent errors:** All exceptions are logged or recorded in violations (no bare except / except Exception: pass)
2. **Tool unavailable:** Gate gracefully skips with WARN violation, returns PASS
3. **Tool failure:** Gate returns FAIL with violation describing the error
4. **Tool timeout:** Gate catches `subprocess.TimeoutExpired`, records violation, returns FAIL
5. **Parsing error:** Gate logs WARN, skips that tool's output, returns PASS
6. **Filesystem error:** Gate returns FAIL with violation
7. **Violation structure:** All error violations have required fields (tool, severity, rule_id, message)
8. **Exception propagation:** If error recovery is not defined in spec, exception is logged and handled as FAIL

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Over-permissive error handling:** If gate silently skips all tools, user is unaware of analysis failure. Mitigation: Violations array records all skips and errors; message includes summary of tools run vs skipped.
- **Ambiguous error messages:** If violation message doesn't explain what went wrong, user cannot debug. Mitigation: Include tool name, command, stderr, and exit code in violation message.

**Ambiguities resolved:**
- **Should tool unavailability FAIL the gate?** No. Tool availability is graceful degradation. Only tool execution failures (non-zero exit) or timeouts result in FAIL.

### 4. Clarifying Questions

None. Error handling rules are frozen.

---

## Requirement 12: Non-Functional Requirements (NFR)

### 1. Spec Summary

**Description:** The gate has performance, reliability, and testability targets.

**Performance targets:**
- Gate runtime: <30 seconds for typical codebase (10k LOC across Python, TypeScript, GDScript)
- Per-tool timeout: tool-specific (see Requirement 03)
- Violation reporting latency: <5 seconds (deduplication, sorting, score computation)

**Reliability targets:**
- Gate must exit cleanly even if tool unavailable (graceful skip, not crash)
- Gate must handle missing tool configs gracefully (skip that tool)
- Gate must be idempotent: calling gate twice on same codebase yields same violations

**Memory targets:**
- Gate must not consume >500 MB memory during execution
- Temp files must be cleaned up after use (no temp file leaks)

**Testability targets:**
- Gate must be testable without external service calls
- All paths (pass, fail, tool unavailable, timeout, parsing error) must be covered
- Violations must be reproducible with deterministic test fixtures

**Logging targets:**
- All tool invocations logged at DEBUG level
- All tool failures logged at ERROR level
- All graceful skips logged at WARN level
- All violations recorded in output dict (redundant with logging for traceability)

**Constraints:**
- Gate is not required to optimize for very large codebases (>100k LOC); timeout may exceed 30s
- Gate is not required to cache results across runs (deferred to M903)
- Gate is not required to run tools in parallel (sequential is safe default)
- Tool output parsing must be defensive (invalid JSON yields empty violations list, not error)

**Assumptions:**
- Typical codebase size is 10k LOC
- Tool execution is reasonably fast (no exotic slowdowns)
- Filesystem is responsive (no NFS latency issues)

**Scope:**
- Performance targets for this gate only; system-wide optimization is out of scope
- Parallelization is out of scope (M903)
- Caching strategies are out of scope (M903)

### 2. Acceptance Criteria

1. **Performance test:** Gate completes in <30s on 10k LOC mixed codebase (3k Python, 4k TS, 3k GDScript)
2. **Timeout handling:** Gate catches subprocess timeouts and returns FAIL within timeout+1s
3. **Idempotency:** Running gate twice on same codebase returns identical violations (deterministic)
4. **Memory safety:** Gate uses <500 MB memory (no memory leaks detected by simple profiling)
5. **Graceful degradation:** If all tools unavailable, gate returns PASS with WARN violations (does not crash)
6. **Logging:** Gate logs at appropriate levels (DEBUG, WARN, ERROR) via stdlib logging
7. **Testability:** All code paths are testable without external services or network

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Performance varies by system:** Tool execution time varies by hardware and system load. Mitigation: Define as "reasonable systems"; tests use relaxed timeouts (allow up to 60s).
- **Memory profiling difficult:** Python memory usage is hard to measure. Mitigation: Sanity check for obvious leaks (unbounded data structures); do not over-speculate.
- **Tool timeouts vary:** Some tools may need longer timeouts on large codebases. Mitigation: Timeouts are per-tool and configurable (adjust in implementation if needed).

**Ambiguities resolved:**
- **Should NFR targets be hard requirements or soft targets?** Soft targets (SLA-like). Tests use relaxed thresholds; implementation should aim to meet targets but not at cost of correctness.

### 4. Clarifying Questions

None. NFR targets are frozen.

---

## Requirement 13: Deferred Scope and Future Work (M903+)

### 1. Spec Summary

**Description:** The following features are explicitly OUT OF SCOPE for this ticket and deferred to M903 and beyond:

**Out of scope (M903 orchestration):**
1. CI/CD hook integration (GitHub Actions, GitLab CI)
2. Lefthook integration (pre-commit, pre-push hooks)
3. Orchestration logic to route stage 3 output to agent review or semantic extraction
4. User-facing UI or PR comments
5. Parallel tool execution (sequential is safe default)
6. Rule suppression system (`blobert-ignore-next-line` comments)

**Out of scope (tool customization):**
1. Custom semgrep rule creation (assume baseline rules exist)
2. Tool config overrides (gate uses repo configs as-is)
3. Tool version pinning (upstream package managers handle versions)
4. Custom severity thresholds per rule (thresholds are frozen in this spec)

**Out of scope (gate improvements):**
1. Caching gate results across runs
2. Incremental analysis (only analyze changed files)
3. Machine learning-based risk scoring (M904+)
4. Integration with external security scanners
5. Cross-repository analysis

**Out of scope (testing):**
1. Integration tests with real Godot scenes or Blender projects
2. Performance profiling against 1M+ LOC codebases
3. Cross-platform testing (assume Unix-like systems)

**Out of scope (documentation):**
1. User-facing troubleshooting guides
2. Tool setup/installation instructions
3. Rule explanation guides

**Constraints:**
- Nothing in deferred scope should be implemented in this ticket
- Implementation must not create scaffolding for deferred features (avoid over-engineering)
- Tests must not assume deferred features exist

**Assumptions:**
- M903 orchestration layer will handle CI/CD integration and routing
- M903 may require enhancements to this gate (e.g., new hooks), which will be version-bumped
- Future tickets will add features without breaking this gate's contract

**Scope:** Boundary statement only; not an AC item.

### 2. Acceptance Criteria

N/A (This is a scope boundary statement.)

### 3. Risk & Ambiguity Analysis

**Risks:**
- **Over-engineering:** If implementation includes deferred features, module becomes complex and hard to test. Mitigation: Spec explicitly forbids deferred features; code review will catch violations.
- **Scope creep:** If tests expect rule suppression or parallel execution, tests fail and ticket is delayed. Mitigation: Spec and execution plan clearly state "defer to M903".

**Ambiguities resolved:**
- **Is M903 orchestrator blocking?** No. M902-11 is standalone gate; M903 consumes its output independently.

### 4. Clarifying Questions

None. Deferred scope is frozen.

---

## Test Vectors (30+ Comprehensive Examples)

**Test vectors are organized by category and included here to freeze expected behavior for Test Designer and Test Breaker agents.**

### SRP Violation Tests (6 vectors)

| ID | Rule | Input | Expected Behavior | Expected Output |
|----|------|-------|---------|---------|
| TV-01 | AR-01 (domain HTTP import) | Domain module imports `fastapi` | Semgrep detects forbidden import | FAIL, violations=[{rule_id: AR-01, severity: ERROR}] |
| TV-02 | AR-02 (service HTTP response) | Service function returns `JSONResponse` | Semgrep detects response construction | FAIL, violations=[{rule_id: AR-02, severity: ERROR}] |
| TV-03 | AR-03 (router business logic) | Router function with 50 LOC domain logic | Semgrep detects large handler | FAIL, violations=[{rule_id: AR-03, severity: ERROR}] |
| TV-04 | AR-04 (service router import) | Service imports from `routers` module | import-linter detects forbidden edge | FAIL, violations=[{rule_id: AR-04, severity: ERROR}] |
| TV-05 | AR-05 (infrastructure leak) | Domain module directly calls `db.query()` | Semgrep detects direct DB access | FAIL, violations=[{rule_id: AR-05, severity: ERROR}] |
| TV-06 | AR-06 (persistence write) | Service performs `db.insert()` | Semgrep detects write outside repository | FAIL, violations=[{rule_id: AR-06, severity: ERROR}] |

### Circular Import Tests (3 vectors)

| ID | Scenario | Input | Expected Behavior | Expected Output |
|----|----------|-------|---------|---------|
| TV-07 | Two-way cycle | A imports B, B imports A | import-linter detects cycle | FAIL or ESCALATE, violations=[{rule_id: AR-07, severity: CRITICAL}] |
| TV-08 | Three-way cycle | A → B → C → A | import-linter detects cycle | FAIL or ESCALATE, violations=[{rule_id: AR-08, severity: CRITICAL}] |
| TV-09 | No cycle | Clean dependency dag | No violations from import-linter | PASS or low risk_score |

### Duplication Tests (4 vectors)

| ID | Scenario | Input | Expected Behavior | Expected Output |
|----|----------|-------|---------|---------|
| TV-10 | 8-line cluster | File A and B both contain 8 identical lines | jscpd detects cluster | PASS (WARN severity), violations=[{rule_id: DUP-01, severity: WARN}] |
| TV-11 | 15-line cluster | Multiple files with 15-line duplication | jscpd detects and aggregates | PASS, violations=[{rule_id: DUP-01, ...}] |
| TV-12 | <8 lines | 7 identical lines across files | jscpd ignores (below threshold) | PASS, no DUP violations |
| TV-13 | High duplication ratio | 8% of codebase is duplicated | jscpd reports high ratio | PASS, violations=[{rule_id: DUP-02, severity: WARN, message includes "8%"}] |

### Complexity Tests (4 vectors)

| ID | Rule | Input | Expected Behavior | Expected Output |
|----|------|-------|---------|---------|
| TV-14 | CX-01 (function size) | Function with 87 LOC | radon/lizard detects size | PASS, violations=[{rule_id: CX-01, severity: WARN}] |
| TV-15 | CX-02 (nesting depth) | 5 nested levels (if → for → while → try → if) | radon detects depth | PASS, violations=[{rule_id: CX-02, severity: WARN}] |
| TV-16 | CX-03 (cognitive complexity) | Function with complexity score 15 | radon/lizard detects complexity | PASS, violations=[{rule_id: CX-03, severity: WARN}] |
| TV-17 | CX-04 (class size) | Class with 320 LOC | radon detects class size | PASS, violations=[{rule_id: CX-04, severity: WARN}] |

### Async Safety Tests (3 vectors)

| ID | Rule | Input | Expected Behavior | Expected Output |
|----|------|-------|---------|---------|
| TV-18 | AS-01 (blocking I/O) | `async def foo(): requests.get(...)` | Semgrep detects blocking call | FAIL or ESCALATE, violations=[{rule_id: AS-01, severity: CRITICAL}] |
| TV-19 | AS-02 (unbounded spawning) | `for x in items: asyncio.create_task(...)` | Semgrep detects unbounded spawning | FAIL or ESCALATE, violations=[{rule_id: AS-02, severity: CRITICAL}] |
| TV-20 | AS-03 (missing timeout) | `asyncio.wait(tasks)` without timeout | Semgrep detects missing timeout | PASS, violations=[{rule_id: AS-03, severity: WARN}] |

### Observability Tests (2 vectors)

| ID | Rule | Input | Expected Behavior | Expected Output |
|----|------|-------|---------|---------|
| TV-21 | OB-01 (unstructured logging) | `logger.info("message")` without context dict | Semgrep detects unstructured | PASS, violations=[{rule_id: OB-01, severity: WARN}] |
| TV-22 | OB-02 (missing correlation ID) | Critical path without correlation ID propagation | Semgrep detects missing ID | PASS, violations=[{rule_id: OB-02, severity: WARN}] |

### Mutation/Data Ownership Tests (2 vectors)

| ID | Rule | Input | Expected Behavior | Expected Output |
|----|------|-------|---------|---------|
| TV-23 | MUT-01 (cross-layer mutation) | Service directly sets `model.field = value` | Semgrep detects direct mutation | FAIL, violations=[{rule_id: MUT-01, severity: ERROR}] |
| TV-24 | MUT-02 (persistence write) | Service calls `db.insert()` directly | Semgrep detects non-repo write | FAIL, violations=[{rule_id: MUT-02, severity: ERROR}] |

### Tool Availability Tests (4 vectors)

| ID | Scenario | Input | Expected Behavior | Expected Output |
|----|----------|-------|---------|---------|
| TV-25 | Tool unavailable | import-linter not installed | Skip import-linter, run others | PASS, violations=[{rule_id: TOOL_UNAVAILABLE, ...}] |
| TV-26 | Tool timeout | semgrep exceeds 120s timeout | Timeout caught, error recorded | FAIL, violations=[{rule_id: TOOL_TIMEOUT, ...}] |
| TV-27 | Tool error (non-zero exit) | jscpd exits with code 1 | Error logged, violation recorded | FAIL, violations=[{rule_id: TOOL_ERROR, ...}] |
| TV-28 | Parsing error | Tool outputs invalid JSON | Output skipped, WARN recorded | PASS, violations=[{rule_id: PARSE_ERROR, severity: WARN}] |

### Edge Cases (2 vectors)

| ID | Scenario | Input | Expected Behavior | Expected Output |
|----|----------|-------|---------|---------|
| TV-29 | Empty codebase | No source files to analyze | All tools run, no violations | PASS, risk_score=0, architecture_score=100 |
| TV-30 | All tools unavailable | No tools installed | All tools skip gracefully | PASS, violations=[{rule_id: TOOL_UNAVAILABLE, ...} for each tool] |

### NFR Tests (2+ vectors)

| ID | NFR | Scenario | Expected Behavior | Acceptance Threshold |
|----|-----|----------|---------|---------|
| TV-31 | Performance | Analyze 10k LOC mixed codebase | Gate completes | <30 seconds |
| TV-32 | Idempotency | Run gate twice on same code | Both runs return identical violations | Same violation set both runs |

---

## Acceptance Criteria Mapping

| Ticket AC | Requirement(s) | Test Vector(s) | Implementation Task |
|-----------|---|---|---|
| AC1: Gate runs import-linter, eslint-plugin-boundaries, semgrep, jscpd, radon/lizard | Req-03 | TV-01 to TV-32 | Tool orchestration logic |
| AC2: Detects SRP violations (controller→repo, domain→HTTP, etc.) | Req-04 | TV-01–TV-06 | SRP detection via semgrep/import-linter |
| AC3: Detects dependency direction violations (circular, reverse) | Req-05 | TV-07–TV-09 | Cycle detection via import-linter |
| AC4: Detects duplication clusters (8+ lines, cross-file) | Req-06 | TV-10–TV-13 | jscpd integration |
| AC5: Detects complexity spikes (function size, nesting, cognitive) | Req-07 | TV-14–TV-17 | radon/lizard integration |
| AC6: Flags async safety violations (blocking I/O, unbounded spawning) | Req-08 | TV-18–TV-20 | Semgrep async rules |
| AC7: Implemented as `ci/scripts/gates/architecture_enforcement_check.py` | Req-01 | All TV | Module at correct path |
| AC8: Tested with architecture violation vectors (SRP, circular, duplication, complexity) | Req-04–07 | TV-01–TV-32 | Test fixtures with violations |

---

## Risk Register (with Mitigations)

| Risk ID | Description | Severity | Likelihood | Impact | Mitigation | Task(s) |
|---------|-------------|----------|------------|--------|-----------|---------|
| R1 | Tool not installed in test env | Medium | High | Tests skip entire tool category | Mock subprocess in tests; implement skip+WARN in gate | Task 2, 4 |
| R2 | Tool output format changes between versions | Medium | Medium | Parsing fails, violations missed | Defensive JSON parsing; test with known-good tool versions | Task 1, 4 |
| R3 | Tool hangs on large codebase | Low | Medium | Gate blocks >timeout | Timeout logic; tool-specific timeouts defined | Task 1, 3 |
| R4 | Tool config missing/incorrect | Medium | Medium | False positives or no violations | Assume configs correct; tests use known-good configs | Task 4 |
| R5 | Multiple tools report same violation | Low | Low | Duplicate violations in output | Deduplication by fingerprint (file, line, rule_id) | Task 1, 2 |
| R6 | Circular imports not detected | Low | Low | Runtime failure | import-linter is standard tool for cycle detection | Task 1, 4 |
| R7 | Output schema non-compliance | Medium | Low | Gate runner rejects output | Validate output before returning; tests verify schema | Task 1, 4 |
| R8 | Severity mapping ambiguous | Low | Medium | User confused about priority | Freeze severity in spec; tests assert severity levels | Task 2, 4 |
| R9 | Performance exceeds 30s target | Low | Low | NFR not met | Optimize tool invocation; accept relaxed threshold (60s) | Task 1, 3, 4 |
| R10 | Gate not idempotent | Low | Low | Unexpected behavior | Ensure gate logic is pure; run idempotency test | Task 2, 3 |

---

## Dependencies & Blockers

**Hard dependencies (must be COMPLETE):**
- M902-01 (Validation Gate Framework) — **COMPLETE** ✓
  - Provides: gate_runner.py, gate schema, success/failure schemas
- M902-02 (Static Analysis tools baseline) — **COMPLETE** ✓
  - Provides: tool availability, tool configs, baseline violations
- Code Governance Stage 3 (bot_vault/architecture/code_governance.md) — **FROZEN** ✓
  - Provides: architecture rules, SRP definitions, layer boundaries

**Soft dependencies (informational):**
- M902-09 (Diff Classification) — **COMPLETE** ✓
  - Provides context: Stage 0 recommends "architecture_enforcement" route
- M902-10 (Formatting Gate) — **COMPLETE** ✓
  - Provides: gate module pattern, registry entry template

**Blocking issues:** None. All hard dependencies satisfied.

---

## Specification Completeness Checklist

- [x] 13 requirements defined (module, schema, tool orchestration, SRP, dependencies, duplication, complexity, async, observability, data ownership, error handling, NFR, deferred scope)
- [x] 30+ test vectors with expected behavior (6 SRP + 3 circular + 4 duplication + 4 complexity + 3 async + 2 observability + 2 mutation + 4 tool + 2 edge + 2 NFR)
- [x] Output contract frozen (success/failure schema, violation structure, severity mapping)
- [x] Acceptance criteria mapped to requirements and test vectors (8 ACs, all covered)
- [x] Risk register with mitigations (10 risks identified)
- [x] Clarifying questions resolved (none remaining)
- [x] Assumptions documented (8 assumptions)
- [x] No game/asset changes required
- [x] No destructive/randomness/load-open API concerns (generic ticket type)
- [x] Spec is unambiguous, implementable, and testable

**Status: READY FOR TEST_DESIGN**

---

## Signature & Versioning

**Spec Agent:** Autonomous (Checkpoint Protocol)  
**Date:** 2026-05-19  
**Version:** 1.0 (DRAFT)  
**Next Stage:** TEST_DESIGN (Test Designer Agent)  
**Next Responsible Agent:** Test Designer Agent  
**Input for Test Designer:** This spec (902_11_architecture_enforcement_gate_spec.md) + test vector checklist + code_governance.md Stage 3
