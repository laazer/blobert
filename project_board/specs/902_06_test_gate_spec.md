# Specification: Test Gate — Assertion Density & Async Marker Detection

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/06_per_stage_gate_improvements.md`

**Milestone:** 902 — Agent Predictability Improvements

**Task:** 4 (Spec Agent responsibility)

**Date:** 2026-05-16

**Revision:** 1

---

## Executive Summary

The **test gate** computes simple metrics on test files to validate sufficient test coverage before Test Breaker begins work:
1. **Assertion density:** count `assert` statements per test function (WARN if < 2 per function; tunable via YAML config).
2. **Async marker detection:** identify pytest async tests (`@pytest.mark.asyncio` + `async def`); report ratio (INFO only, no thresholds).

The gate is deterministic, heuristic-based (not deep semantic analysis), and defers mutation coverage to M903. All metrics are informational for MVP; threshold enforcement deferred to M903+.

**Scope:** Python pytest test files only. All test functions with `def test_*` signature (async or sync).

---

## Functional Requirements

### Requirement 1: Parse Test Files and Extract Test Functions

**Description:** Gate must identify all test functions in Python test files.

**Input Format:**
- `test_files` (list of strings, required): Paths to Python test files to analyze
- `config` (string, optional): Path to YAML config file (see Config File Schema section)

**Test Function Identification:**
- Pattern: `def test_<name>` or `async def test_<name>` (case-sensitive `test_` prefix required)
- Scope: Top-level functions and methods within test classes
- Examples:
  - `def test_planner_cycle_detection():` → test function
  - `async def test_reviewer_todo_detection():` → async test function
  - `def setUp(self):` → not a test function (no `test_` prefix)
  - `def helper_function():` → not a test function

**Constraints:**
- File must be valid Python syntax (detect errors gracefully).
- Nested function definitions within tests are not counted separately.
- Skip commented-out functions.
- Skip functions in comments.

**Scope:** All test files matching `tests/**/*.py` or paths explicitly provided.

**Acceptance Criteria:**
- Gate correctly identifies 3 test functions in file with 8 total functions.
- Gate correctly skips `def _helper()` and test functions in comments.
- Gate handles syntax errors gracefully (WARN, continue).

---

### Requirement 2: Count Assertions per Test Function

**Description:** Gate must count `assert` statements per test function using regex.

**Assertion Detection:**
- Regex pattern: `assert ` (exact word boundary; case-sensitive)
- Matches all assertion styles: `assert x`, `assert x == y`, `assert func()`, `assert x or y`
- Does NOT match: `# assert` (commented), `assert_equals()` (helper function), `assertions` (substring)

**Metric Calculation:**
- For each test function: count = regex matches of `assert ` in function body
- Per-function metric: assertion_count / test_function_count
- Aggregate metric: total_assertions / total_test_functions

**Example:**
```python
def test_foo():
    assert x == 1
    assert y is not None
    assert z > 0
    return True

def test_bar():
    result = helper()
    assert result.status == "ok"

def test_baz():
    # No asserts; helper_test() checks everything
    helper_test()
```

- test_foo: 3 assertions
- test_bar: 1 assertion
- test_baz: 0 assertions
- Density: (3 + 1 + 0) / 3 = 1.33 assertions per function

**Constraints:**
- Heuristic matching (does not parse AST or understand Python semantics).
- Generator assertions, comprehension assertions, assertion helpers (custom assert_* functions) are not counted separately.
- Assertions in fixtures (setup/teardown) not counted (out of scope).

**Scope:** Function body only (not file-level assertions or module-level constants).

**Acceptance Criteria:**
- Gate correctly counts 3 assertions in simple test function.
- Gate correctly reports 0 assertions for test with no assert statements.
- Gate correctly handles assertion in if-else block (counts both).
- Gate handles multiline assertions (e.g., `assert\n    x == y`).

---

### Requirement 3: Report Assertion Density with Severity Levels

**Description:** Gate categorizes assertion density and reports with appropriate severity.

**Severity Logic:**

| Assertions Per Function | Severity | Remediation |
|------------------------|----------|-------------|
| >= 2 | PASS | None |
| < 2 | WARN | Add more assertions or split test |
| 0 | WARN | Lowest density (critical) |

**Output Format (per test file):**
```json
{
  "file": "tests/ci/test_planner_check.py",
  "total_test_functions": 12,
  "total_assertions": 18,
  "density_per_function": 1.5,
  "severity": "WARN",
  "density_histogram": [
    { "function": "test_acyclic_graph", "assertions": 3, "severity": "PASS" },
    { "function": "test_cyclic_graph", "assertions": 2, "severity": "PASS" },
    { "function": "test_orphaned_dep", "assertions": 1, "severity": "WARN" },
    { "function": "test_malformed_yaml", "assertions": 0, "severity": "WARN" }
  ]
}
```

**Thresholds:**
- Default: min_assertions_per_function = 2 (tunable in YAML config)
- Severity for < threshold: WARN (not FAIL; heuristic metric, not definitive)

**Scope:** Aggregate metric per file, with per-function breakdown for transparency.

**Acceptance Criteria:**
- File with all functions >= 2 assertions → PASS.
- File with one function < 2 assertions → WARN (file-level severity).
- Density histogram includes all test functions.
- Remediation hint is clear ("Add more assertions or split test").

---

### Requirement 4: Detect Async Test Markers

**Description:** Gate must identify async test functions and report ratio.

**Async Test Detection:**
- Marker pattern: `@pytest.mark.asyncio` decorator (optional; advisory detection)
- Function pattern: `async def test_<name>` (required; async keyword)

**Detection Logic:**
- Count functions with `async def test_*` signature
- Count functions with `@pytest.mark.asyncio` decorator immediately preceding `def test_*`
- Report both counts and ratio: async_tests / total_tests

**Example:**
```python
@pytest.mark.asyncio
async def test_async_registry_load():
    result = await registry.load()
    assert result is not None

async def test_async_without_marker():
    # pytest-asyncio auto-detects async functions
    result = await async_func()
    assert result

def test_sync():
    assert True
```

- Async with marker: 1
- Async without marker: 1
- Sync: 1
- Total: 3
- Async ratio: 66.7% (2/3 async)

**Constraints:**
- Marker detection is regex-based (heuristic; `@pytest.mark` followed by `asyncio`).
- Does not validate pytest-asyncio configuration or plugin presence.
- Reports only; no threshold or severity enforcement (INFO only).

**Scope:** All test functions (async and sync).

**Acceptance Criteria:**
- Gate correctly identifies 2 async tests in file with 5 total tests.
- Gate reports both @pytest.mark.asyncio and `async def` patterns.
- Gate handles marker on preceding line (not directly above function).

---

### Requirement 5: JSON Output Format (M902-01 Schema Compliance)

**Description:** Gate emits JSON output matching M902-01 gate schema.

**Output Structure:**
```json
{
  "version": "0.1.0",
  "status": "PASS|WARN",
  "gate": "test_check",
  "upstream_agent": "Test Designer Agent",
  "downstream_agent": "Test Breaker Agent",
  "timestamp": "2026-05-16T12:00:00",
  "ticket_id": "M902-06",
  "mode": "shadow",
  "message": "Test metrics report: 5 files analyzed, 47 tests, 1.9 assertions/function (1 WARN).",
  "violations": [
    {
      "file": "tests/ci/test_planner_check.py",
      "line": 0,
      "rule": "low_assertion_density",
      "message": "File has 1.5 assertions per function (threshold: 2.0)",
      "severity": "WARN"
    }
  ],
  "remediation_hints": [
    "tests/ci/test_planner_check.py: function test_orphaned_dep has 1 assertion; recommend adding 1+ more",
    "Consider: (1) add assertion verifying side effects, (2) split test into smaller units with independent assertions"
  ],
  "artifacts": [
    {
      "path": "gate-results/test_check_metrics_20260516T120000Z.json",
      "type": "metrics_report"
    }
  ],
  "duration_ms": 42
}
```

**Status Mapping:**
- **PASS:** All files have >= threshold assertions per function; no WARN violations.
- **WARN:** At least one file has < threshold; detailed violations list.

**Violations Array:**
- One entry per file with WARN-severity density issues.
- Rule: "low_assertion_density".
- Message includes file, actual density, threshold.
- Line 0 (not applicable; file-level metric).

**Remediation Hints:**
- Per file with WARN: function name(s) with low assertion count.
- Generic guidance: "Add more assertions" or "Split test into independent test functions".

**Artifacts:**
- Detailed metrics report as JSON file (optional; for deep analysis by Test Designer).
- Path: `gate-results/test_check_metrics_<timestamp>.json`.

**Scope:** All output fields must be present; violations array empty if all PASS.

**Acceptance Criteria:**
- PASS output has status=PASS, no violations.
- WARN output includes all low-density files in violations array.
- Remediation hints are actionable and specific to failing functions.

---

### Requirement 6: Config File Support (YAML)

**Description:** Gate accepts optional YAML config file to customize thresholds.

**Config File Schema:**
```yaml
test_assertion_density:
  # Minimum assertions per test function to trigger WARN
  min_assertions_per_function: 2
  
  # Severity level for violations (WARN or FAIL; only WARN in M902-06 MVP)
  severity: WARN
  
  # Whether to report per-function breakdown in violations
  detailed_report: true

async_markers:
  # Whether to scan for async markers (default: true)
  enabled: true
  
  # Report only (no thresholds in M902-06)
  report_only: true

# Fileset scope (optional; if omitted, uses inputs.test_files list)
test_file_patterns:
  - "tests/**/*.py"
  - "!tests/**/_*.py"  # exclude private files
```

**Defaults (if config file missing):**
```yaml
test_assertion_density:
  min_assertions_per_function: 2
  severity: WARN
  detailed_report: true

async_markers:
  enabled: true
  report_only: true
```

**Config File Location:**
- Specified in inputs["config"] as absolute path.
- If missing: use hardcoded defaults (no YAML required).
- If file not found: WARN and use defaults (not FAIL).

**Scope:** All config keys are optional; any omitted key uses default value.

**Acceptance Criteria:**
- Gate correctly reads config YAML and applies min_assertions_per_function threshold.
- Gate defaults to WARN severity, not FAIL (even if config says FAIL; M902-06 limitation).
- Gate gracefully handles missing config file (uses defaults, emits INFO).

---

### Requirement 7: Error Handling & Graceful Degradation

**Description:** Gate must handle missing/unreadable test files, invalid Python, and config errors gracefully.

**Error Cases:**
- **Test file not found:** WARN, skip file (continue with other files).
- **Python syntax error:** WARN, skip file (file is invalid; Test Designer must fix).
- **Unreadable file (permissions, encoding):** WARN, skip file.
- **Config file not found:** WARN, use defaults (not FAIL).
- **Invalid YAML config:** WARN, use defaults.
- **Empty test file list:** PASS (vacuously; no tests = 0 assertions, density undefined but not an error).

**Constraints:**
- All errors reported in violations array or message (no silent failures).
- Gate does not halt on first error; continues with other files.
- Fallback: If all test files are unreadable, emit WARN with message "unable to analyze test files; skipping assertion density check".

**Scope:** Applies to gate invocation with potentially invalid inputs.

**Acceptance Criteria:**
- Missing test file → WARN (not FAIL).
- Python syntax error in test file → WARN, skip file.
- Config file not found → INFO "using defaults", apply defaults.
- Invalid YAML → WARN, use defaults.

---

## Non-Functional Requirements

### NFR-1: Deterministic Execution

**Requirement:** Gate must produce identical output for identical test files (no randomness).

**Scope:** Regex matching, metric calculation, output serialization.

**Verification:**
- Same test files + config → same result every invocation.
- Test function ordering (stable sorted by name) is deterministic.

**Acceptance Criteria:**
- Gate run on same test files twice → identical JSON output (except duration_ms and timestamp).

---

### NFR-2: No External Service Dependencies

**Requirement:** Gate must not require network, database, or external services.

**Scope:** All I/O is local filesystem read only; no test execution.

**Verification:**
- No HTTP, SSH, git, or RPC calls.
- Gate does NOT run pytest (static analysis only).
- No database queries.

**Acceptance Criteria:**
- Gate runs in offline/sandboxed environment with only filesystem read access.

---

### NFR-3: Performance

**Requirement:** Gate must complete in < 5 seconds for typical test suite (50 test files, 500 functions).

**Metrics:**
- File enumeration: < 1 second.
- File read + regex matching: < 3 seconds (all files combined).
- Metric calculation + JSON serialization: < 1 second.

**Acceptance Criteria:**
- Gate completes in < 5 seconds for 50 test files with 500 test functions.

---

### NFR-4: Observability

**Requirement:** Gate must log structured messages for debugging.

**Logging:**
- INFO: gate start, test files enumerated, summary statistics (total tests, avg density).
- DEBUG: per-file metrics, per-function assertion counts.
- WARN: skipped files, missing config, unreadable files.
- ERROR: exception stack traces (if gate module itself fails).

**Scope:** All logs at module level.

**Acceptance Criteria:**
- Gate logs at least 2 INFO messages per invocation (start, summary).

---

## Integration Notes

### Gate Runner Wiring

**Registry Entry (gate_registry.json):**
```json
{
  "name": "test_check",
  "module": "test_check",
  "required_inputs": ["test_files"],
  "optional_inputs": ["config", "mode", "ticket_id", "upstream_agent", "downstream_agent"],
  "default_mode": "shadow",
  "description": "Computes assertion density and async marker metrics for test suite. Output: PASS if all functions >= 2 assertions, WARN otherwise. Async markers reported as INFO (no threshold).",
  "category": "analysis"
}
```

**Invocation (from Test Designer or Test Breaker):**
```bash
python ci/scripts/gate_runner.py test_check \
  --upstream-agent "Test Designer Agent" \
  --downstream-agent "Test Breaker Agent" \
  --ticket-id M902-06 \
  --input '{"test_files": ["tests/ci/test_planner_check.py", "tests/ci/test_reviewer_check.py"], "config": "project_board/902_06_test_gate_config.yml"}'
```

**Module Location:** `ci/scripts/gates/test_check.py`

**Entry Point Function:** `run(inputs: dict[str, Any]) -> dict[str, Any]`

**Input Contract:**
```python
inputs = {
  "test_files": list[str],  # list of test file paths (required)
  "config": str,  # path to YAML config file (optional)
  "mode": "shadow|blocking",  # default "shadow"
  "ticket_id": str,  # ticket identifier
  "upstream_agent": str,  # agent name
  "downstream_agent": str,  # agent name
}
```

**Output Contract:** Dict matching M902-01 schema v0.2.0 with fields: version, status, gate, upstream_agent, downstream_agent, timestamp, ticket_id, mode, message, violations[], remediation_hints[], artifacts[], duration_ms.

---

## Config File Schema

**File Location:** `project_board/902_06_test_gate_config.yml`

**Complete Schema (YAML):**
```yaml
# Test assertion density thresholds
test_assertion_density:
  # Minimum assertions per test function
  # Default: 2
  # Rationale: MVP heuristic; mutation coverage (M903) is ground truth
  min_assertions_per_function: 2
  
  # Severity for violations
  # Default: WARN (not FAIL in M902-06)
  # Valid: WARN
  severity: WARN
  
  # Include per-function breakdown in violations array
  # Default: true
  detailed_report: true

# Async marker detection
async_markers:
  # Enable/disable async detection (default: true)
  enabled: true
  
  # Report only (no thresholds in M902-06)
  # Default: true
  report_only: true

# (Optional) Test file patterns to analyze
# If omitted, uses test_files from gate inputs
test_file_patterns:
  - "tests/**/*.py"
  - "!tests/**/_*.py"
  - "!tests/**/conftest.py"
```

---

## Examples

### Example 1: Simple Test File with Adequate Assertions (PASS)

**Input:**
```python
# tests/ci/test_planner_check.py
def test_acyclic_graph():
    graph = build_graph({"M902-01": [], "M902-02": ["M902-01"]})
    cycles = detect_cycles(graph)
    assert cycles == []

def test_cyclic_graph():
    graph = build_graph({"M902-02": ["M902-03"], "M902-03": ["M902-02"]})
    cycles = detect_cycles(graph)
    assert len(cycles) == 1
    assert cycles[0] == ["M902-02", "M902-03", "M902-02"]
```

**Analysis:**
- Total test functions: 2
- Assertions: test_acyclic_graph (1), test_cyclic_graph (2)
- Density: (1 + 2) / 2 = 1.5 assertions per function

**Wait, 1.5 < 2, so this should be WARN, not PASS.**

Let me adjust the example:

```python
def test_acyclic_graph():
    graph = build_graph({"M902-01": [], "M902-02": ["M902-01"]})
    cycles = detect_cycles(graph)
    assert cycles == []
    assert isinstance(cycles, list)

def test_cyclic_graph():
    graph = build_graph({"M902-02": ["M902-03"], "M902-03": ["M902-02"]})
    cycles = detect_cycles(graph)
    assert len(cycles) == 1
    assert cycles[0] == ["M902-02", "M902-03", "M902-02"]
```

**Analysis (revised):**
- Assertions: test_acyclic_graph (2), test_cyclic_graph (2)
- Density: (2 + 2) / 2 = 2.0 assertions per function
- Severity: PASS (>= 2 threshold)

**Output:**
```json
{
  "version": "0.1.0",
  "status": "PASS",
  "gate": "test_check",
  "message": "Test metrics: 1 file, 2 tests, 2.0 assertions/function (all PASS).",
  "violations": [],
  "remediation_hints": [],
  "artifacts": [
    {
      "path": "gate-results/test_check_metrics_20260516T120000Z.json",
      "type": "metrics_report"
    }
  ],
  "duration_ms": 12
}
```

---

### Example 2: File with Low Assertion Density (WARN)

**Input:**
```python
# tests/ci/test_reviewer_check.py
def test_no_todos():
    diff = git_diff("--cached")
    todos = scan_todos(diff)
    assert todos == []

def test_single_todo():
    diff = "# TODO: fix error handling"
    todos = scan_todos(diff)
    assert len(todos) == 1

def test_multiple_todos_no_assertions():
    diff = "# TODO: fix\n# TODO: improve"
    todos = scan_todos(diff)
    # No assertions; test is incomplete
```

**Analysis:**
- Total functions: 3
- Assertions: test_no_todos (1), test_single_todo (1), test_multiple_todos_no_assertions (0)
- Density: (1 + 1 + 0) / 3 = 0.67 assertions per function
- Severity: WARN

**Output:**
```json
{
  "version": "0.1.0",
  "status": "WARN",
  "gate": "test_check",
  "message": "Test metrics: 1 file, 3 tests, 0.67 assertions/function (1 WARN).",
  "violations": [
    {
      "file": "tests/ci/test_reviewer_check.py",
      "line": 0,
      "rule": "low_assertion_density",
      "message": "File has 0.67 assertions per function (threshold: 2.0)",
      "severity": "WARN"
    }
  ],
  "remediation_hints": [
    "tests/ci/test_reviewer_check.py: function test_no_todos has 1 assertion (recommend 2)",
    "tests/ci/test_reviewer_check.py: function test_single_todo has 1 assertion (recommend 2)",
    "tests/ci/test_reviewer_check.py: function test_multiple_todos_no_assertions has 0 assertions (critical)",
    "Add assertions verifying: TODO count, TODO content, TODO line numbers"
  ],
  "duration_ms": 9
}
```

---

### Example 3: Async Test Markers (INFO)

**Input:**
```python
@pytest.mark.asyncio
async def test_async_load():
    data = await load_data()
    assert data is not None

async def test_async_parse():
    result = await parse_input()
    assert result.is_valid

def test_sync():
    assert True
```

**Analysis:**
- Async with @pytest.mark.asyncio: 1
- Async without marker: 1
- Sync: 1
- Total: 3
- Async ratio: 66.7%

**Output (excerpt):**
```json
{
  "message": "Test metrics: ...; async markers: 2/3 tests (66.7%)",
  "async_markers": {
    "with_marker": 1,
    "without_marker_async": 1,
    "total_async": 2,
    "total_tests": 3,
    "async_ratio": 0.667
  }
}
```

---

### Example 4: Missing Config File (Uses Defaults)

**Input:**
```
config: "project_board/nonexistent_config.yml"
```

**Processing:**
- Attempt to read config file: FileNotFoundError
- Log INFO "Config file not found; using defaults"
- Continue with hardcoded defaults (min_assertions=2, severity=WARN)

**Output:**
```json
{
  "message": "Config file not found (project_board/nonexistent_config.yml); using defaults.",
  "violations": []
}
```

---

### Example 5: Invalid Python Syntax (Skipped File)

**Input Test File:**
```python
def test_valid():
    assert True

def test_invalid_syntax(
    # Missing closing paren
```

**Processing:**
- Parse test_valid: found 1 test function, 1 assertion
- Parse test_invalid_syntax: SyntaxError
- Log WARN "Syntax error in file; skipping"
- Result: Report only valid test (test_valid)

**Output (excerpt):**
```json
{
  "violations": [
    {
      "file": "tests/ci/test_invalid_syntax.py",
      "line": 0,
      "rule": "syntax_error",
      "message": "Python syntax error; skipping file",
      "severity": "WARN"
    }
  ]
}
```

---

## Risk & Ambiguity Analysis

### Risk 1: Assertion Heuristic Produces False Negatives
**Risk:** Tests with complex logic hidden in fixtures or helpers have low assertion counts per function.
**Mitigation:** WARN only (not FAIL). Test Designer can explain assertion strategy in comments. Mutation coverage (M903) is ground truth.
**Impact:** Low (acceptable for MVP; advisory metric).

### Risk 2: Regex Matching Counts Non-Test Assertions
**Risk:** Helper functions or callbacks with `assert` statements may be counted in test function body.
**Mitigation:** Count only `assert ` at statement level (heuristic); manual review catches false positives.
**Impact:** Low (minor overcounting; WARN only).

### Risk 3: Async Marker Detection Misses Other Patterns
**Risk:** Alternative async test frameworks (not pytest-asyncio) use different markers.
**Mitigation:** Scope frozen to pytest patterns (standard in blobert). Other frameworks not supported in MVP.
**Impact:** Low (blobert uses pytest; other frameworks out of scope).

---

## Clarifying Questions (Resolved via Checkpoint Protocol)

1. **Should gate run actual pytest to gather coverage?**
   - Answer: No (static analysis only). Test execution deferred to implementation/CI stages.

2. **What is acceptable assertion density?**
   - Answer: >= 2 per function = PASS. < 2 = WARN (heuristic). Mutation coverage (M903) is ground truth.

3. **Should async marker count affect test status?**
   - Answer: No (INFO only, no thresholds in M902-06). Async correctness verified by test execution.

---

## Acceptance Criteria Mapping

- **AC3 (Test gate computes assertion density & async markers):** Req1-7 + Examples satisfy this.
- **AC1 (Per-stage checks + checklists):** Documented in 902_06_per_stage_checklists.md.

---

## Sign-Off

Specification is complete, unambiguous, and actionable by Implementation Agent.
All 7 requirements + 4 NFRs + examples + config schema + error handling frozen.
Ready for gate module implementation (ci/scripts/gates/test_check.py, ~300 lines).
