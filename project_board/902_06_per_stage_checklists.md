# Per-Stage Validation Gate Checklists — M902-06

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/06_per_stage_gate_improvements.md`

**Stage:** SPECIFICATION (Task 1 deliverable)

**Date:** 2026-05-16

---

## Overview

This document defines what each validation gate checks for at six key workflow stages. Each stage has a checklist of automated and manual validation points, with references to gate module names and existing frameworks.

All gates are deterministic, run with only artifacts (markdown specs, test files, coverage data, git diffs), and produce JSON output matching the M902-01 gate schema.

---

## Stage 1: PLANNER

**Purpose:** Validate ticket structure, dependencies, and scope before hand-off to Spec Agent.

**Automated Checks:**

- [ ] **Planner Gate: Dependency Graph Validation** (`planner_check`)
  - Parses `EXECUTION PLAN` or `Dependencies` field from ticket markdown
  - Detects cyclic dependency edges via DFS algorithm
  - Output: PASS if acyclic; WARN if cycle detected (non-blocking)
  - Input: ticket file path from `project_board/` folder
  - Example: Detects M902-01 → M902-02 → M902-03 → M902-02 cycle (graph structure in YAML `dependencies` field)

- [ ] **Planner Gate: Ticket Umbrella Completeness**
  - Validates that all child tickets referenced in execution plan exist in filesystem
  - Checks folder state (backlog/, in_progress/, done/) for each child
  - Output: FAIL if gating child is not in done/ (blocking); WARN if backlog (non-blocking)
  - Integration: Part of planner_check module; wired into Planner Agent autopilot

- [ ] **Manual Review: Scope Sizing**
  - Verify that ticket AC (Acceptance Criteria) are feasible for single milestone
  - Check that design does not leak across multiple milestones without explicit DEFERRAL boundary
  - Evidence: Handoff metadata in ticket (Story Points estimate if applicable)

**Config:** None (built-in to planner_check module)

**Outputs:** JSON log at `gate-results/planner_check_<timestamp>.json` with status (PASS/WARN/FAIL), violations list, remediation hints

---

## Stage 2: SPECIFICATION

**Purpose:** Validate that Spec Agent produces complete, unambiguous spec before Test Designer begins.

**Automated Checks:**

- [ ] **Spec Gate: Section Completeness** (`spec_completeness`)
  - Runs `ci/scripts/spec_completeness_check.py <spec_file> --type <ticket_type>`
  - Validates required sections per ticket type (api, destructive, randomness, load-open, generic)
  - Output: PASS if all required sections present; FAIL if missing (blocking, prevents TEST_DESIGN advance)
  - Required sections frozen in spec_completeness.py (_SECTION_DEFS dictionary)
  - Example missing sections: Missing "Endpoint Freeze" in api spec → FAIL with remediation hint

- [ ] **Spec Gate: Example Coverage**
  - Validator checks that at least one concrete example (with inputs, expected behavior, success/failure case) exists per requirement
  - Scans for "Example:", "## Example", code blocks marked with language tags
  - Output: WARN if example count < requirement count (advisory, not blocking)
  - Integration: Optional in M902-06; placeholder for M903 enhancement

- [ ] **Spec Gate: Assumption Documentation**
  - Validator checks that spec includes "Assumptions:" section or "Risk & Ambiguity Analysis:"
  - Output: WARN if section missing (advisory)
  - Integration: Optional in M902-06; enforced in M903 via custom gate module

- [ ] **Manual Review: Traceability Matrix**
  - Verify that each acceptance criterion (AC) is independently testable
  - Verify that each AC can be verified via runtime behavior (code paths, APIs, schema validation), not just prose assertions
  - Evidence: AC section in spec

**Config:** None (spec_completeness.py is authoritative)

**Outputs:** JSON log at `gate-results/spec_completeness_check_<timestamp>.json`

---

## Stage 3: TEST_DESIGN

**Purpose:** Validate that Test Designer produces sufficient behavioral test coverage before Test Breaker writes adversarial tests.

**Automated Checks:**

- [ ] **Test Gate: Assertion Density** (`test_check`)
  - Scans all test files (tests/*.py) matching ticket scope
  - Counts regex matches of `assert ` per test function
  - Computes metric: assertions_per_function = total_assertions / test_function_count
  - Threshold: >= 2 assertions per function → PASS; < 2 → WARN
  - Output: WARN report with density histogram (e.g., "Function test_foo has 1 assertion, recommendation 2+")
  - Config: `project_board/902_06_test_gate_config.yml` with threshold tunable
  - Example: test_registry_mutation has 8 assertions across 3 functions → 2.67 per function → PASS

- [ ] **Test Gate: Async Test Markers** (`test_check`)
  - Counts test functions with `@pytest.mark.asyncio` decorator
  - Counts `async def test_*` functions
  - Output: INFO report with ratio (e.g., "5 async tests out of 32 total = 15.6%")
  - Integration: For informational purposes; no threshold (deferred to M903)
  - Example: test file with 2 async test functions → INFO "2 async markers detected"

- [ ] **Test Gate: Spec Traceability** (manual)
  - Verify that test docstrings or comments reference spec requirement IDs
  - Evidence: spec requirement cross-references in test file or test class docstring
  - Output: WARN if < 80% of tests have traceability comments (optional in M902-06)

- [ ] **Manual Review: Test Independence**
  - Verify that tests use mocks/fixtures (not real I/O, network, external services)
  - Verify that test order does not matter (no dependency chains)
  - Evidence: Test class docstring, fixture strategy

**Config:** `project_board/902_06_test_gate_config.yml` (YAML):
```yaml
test_assertion_density:
  min_assertions_per_function: 2
  severity: WARN  # not FAIL
async_markers:
  report_only: true
spec_traceability:
  enabled: false  # optional in M902-06
  min_coverage: 0.8
```

**Outputs:** JSON log at `gate-results/test_check_<timestamp>.json` with status, assertion density histogram, async marker counts, traceability coverage

---

## Stage 4: TEST_BREAK

**Purpose:** Validate that Test Breaker has written adversarial tests covering edge cases, failures, and mutations.

**Automated Checks:**

- [ ] **Test Gate: Adversarial Test Count** (manual)
  - Count tests in adversarial suite (typically `test_*_adversarial.py`)
  - Minimum: >= behavioral test count (1:1 ratio acceptable, goal 1:2 ratio)
  - Output: WARN if adversarial tests < behavioral tests
  - Example: 80 behavioral tests, 130 adversarial tests → PASS "adversarial coverage 162.5%"

- [ ] **Test Gate: Exception/Error Path Coverage** (manual)
  - Verify that adversarial suite tests error handling, malformed inputs, timeouts, permission errors
  - Evidence: Test function names and docstrings reference error categories
  - Output: WARN if coverage < 10 error categories

- [ ] **Manual Review: Mutation Targets**
  - For implementation modules (implementation stage spec), verify test suite identifies 5+ mutation targets
  - Evidence: test docstring comments referencing code lines/functions that tests would catch mutations
  - Deferred: Actual mutation testing tool integration deferred to M903

**Config:** None (test count heuristic built-in)

**Outputs:** Manual checklist in ticket (no JSON gate output)

---

## Stage 5: IMPLEMENTATION_{BACKEND,FRONTEND,GENERALIST}

**Purpose:** Validate that implementation code meets quality gates before hand-off.

**Automated Checks:**

- [ ] **Static Analysis Gate: Ruff + Mypy + Import-Linter** (existing M902-02 gate)
  - Linting, type checking, import correctness
  - Output: FAIL if violations present (blocking in M903, shadow in M902-06)

- [ ] **Governance Gate: Rule Enforcement** (existing M902-03 gate)
  - 30+ rules: exception safety, architecture boundaries, async safety, observability
  - Output: FAIL if ERROR-severity violations found (blocking in M903)

- [ ] **Code Coverage: Diff-Cover Threshold** (existing blobert workflow)
  - Runs `diff-cover` on Python implementation; threshold >= 85% for new lines
  - Output: FAIL if coverage below threshold (blocking before STATIC_QA)

- [ ] **Reviewer Gate: TODO/FIXME Scanning** (`reviewer_check`)
  - Scans git diff (staged files) for new `TODO`, `FIXME`, `HACK` comments
  - Output: WARN per new TODO (non-blocking; helps identify tech debt introduced in this PR)
  - Config: Tunable list of keywords in `project_board/902_06_reviewer_gate_policy.yml`
  - Example: PR adds `# TODO: improve error handling` → WARN "1 new TODO found on line 42"

- [ ] **Reviewer Gate: Suppression Audit** (`reviewer_check`)
  - Scans new `# noqa`, `# nosemgrep`, `# eslint-disable` comments
  - Verifies that suppressions cite issue/ticket (e.g., `# noqa M902-03` or `# nosemgrep AR-01 https://...`)
  - Output: WARN if suppression lacks issue link (non-blocking; governance hint)
  - Example: New `# noqa` without issue link → WARN "suppression on line 15 missing issue citation"

**Config:** 
- `project_board/902_06_reviewer_gate_policy.yml` for TODO/FIXME keywords
- built-in governance rules from M902-03 catalog

**Outputs:** JSON logs at `gate-results/reviewer_check_<timestamp>.json`

---

## Stage 6: STATIC_QA

**Purpose:** Validate implementation quality before INTEGRATION.

**Automated Checks:**

- [ ] **Learning Gate: Forbidden Phrases** (`learning_check`)
  - Scans checkpoint learning outputs (markdown files under project_board/checkpoints/)
  - Detects forbidden phrases per policy (e.g., "hack", "temporary", "XXX", "KLUDGE")
  - Output: FAIL if forbidden phrase found (blocking); cites line number and context
  - Config: `project_board/902_06_learning_gate_policy.yml` with phrase list
  - Example: Learning output includes "This is a temporary workaround" → FAIL "forbidden phrase 'temporary' on line 5"

- [ ] **Learning Gate: Remediation Guidance**
  - If forbidden phrase found, suggests refactoring guidance or ticket reference
  - Example: "temporary" phrase → remediation "Create M903-XX ticket for permanent solution and reference in code"

- [ ] **Manual Review: Architecture Review**
  - Verify that implementation respects layer boundaries and design assumptions from spec
  - Evidence: Code review checklist items checked off in PR/ticket

- [ ] **Manual Review: Observability**
  - For critical paths, verify logging is present (structured logging with context)
  - Evidence: Code inspection, log output samples

**Config:** `project_board/902_06_learning_gate_policy.yml` (YAML):
```yaml
forbidden_phrases:
  - phrase: "hack"
    severity: ERROR
    remediation: "Refactor to proper pattern or create follow-up ticket"
  - phrase: "temporary"
    severity: ERROR
    remediation: "Create permanent implementation or reference M903-XX ticket"
  - phrase: "XXX"
    severity: ERROR
  - phrase: "KLUDGE"
    severity: ERROR
  - phrase: "TODO"
    severity: WARN
    note: "Use spec's risk section, not TODO comments"
```

**Outputs:** JSON log at `gate-results/learning_check_<timestamp>.json`

---

## Stage 7: INTEGRATION

**Purpose:** Validate that cross-module integration works correctly.

**Manual Checks:**

- [ ] Verify that all dependent modules are wired correctly
- [ ] Run integration tests (if applicable to ticket scope)
- [ ] Evidence: Integration test output, manual testing notes

---

## Stage 8: DEPLOYMENT

**Purpose:** Validate production readiness (if applicable).

**Manual Checks:**

- [ ] Verify that all config/secret management is correct
- [ ] Verify that database migrations (if applicable) are tested
- [ ] Verify that rollback procedure is documented

---

## Gate Module Summary Table

| Stage | Gate Name | Module | Automated | Config File | Blocking? |
|-------|-----------|--------|-----------|-------------|-----------|
| PLANNER | Dependency Validation | `planner_check` | Yes | None | WARN only |
| SPECIFICATION | Section Completeness | `spec_completeness` | Yes | None | FAIL (blocks TEST_DESIGN) |
| TEST_DESIGN | Assertion Density | `test_check` | Yes | `902_06_test_gate_config.yml` | WARN only |
| TEST_DESIGN | Async Markers | `test_check` | Yes | `902_06_test_gate_config.yml` | INFO only |
| IMPLEMENTATION | TODO/FIXME Scanning | `reviewer_check` | Yes | `902_06_reviewer_gate_policy.yml` | WARN only |
| IMPLEMENTATION | Suppression Audit | `reviewer_check` | Yes | `902_06_reviewer_gate_policy.yml` | WARN only |
| STATIC_QA | Forbidden Phrases | `learning_check` | Yes | `902_06_learning_gate_policy.yml` | FAIL (blocks INTEGRATION) |
| STATIC_QA | Static Analysis (M902-02) | `static_analysis_check` | Yes | `.semgrep.yml` etc | WARN in M902, FAIL in M903+ |
| STATIC_QA | Governance (M902-03) | `governance_check` | Yes | None | WARN in M902, FAIL in M903+ |

---

## Integration with Gate Runner

All automated gates are invoked via `gate_runner.py`:

```bash
# Planner gate
python ci/scripts/gate_runner.py planner_check \
  --upstream-agent "Planner Agent" \
  --downstream-agent "Spec Agent" \
  --ticket-id M902-06 \
  --input '{"ticket_file": "project_board/902_06_per_stage_gate_improvements.md"}'

# Spec completeness gate
python ci/scripts/gate_runner.py spec_completeness_check \
  --upstream-agent "Spec Agent" \
  --downstream-agent "Test Designer Agent" \
  --ticket-id M902-06 \
  --input '{"spec_file": "project_board/specs/902_06_planner_gate_spec.md", "ticket_type": "generic"}'

# Test assertion density gate
python ci/scripts/gate_runner.py test_check \
  --upstream-agent "Test Designer Agent" \
  --downstream-agent "Test Breaker Agent" \
  --ticket-id M902-06 \
  --input '{"test_files": ["tests/ci/test_planner_gate.py"], "config": "project_board/902_06_test_gate_config.yml"}'

# Reviewer gate
python ci/scripts/gate_runner.py reviewer_check \
  --upstream-agent "Implementation Agent" \
  --downstream-agent "Spec Agent" \
  --ticket-id M902-06 \
  --input '{"policy_file": "project_board/902_06_reviewer_gate_policy.yml"}'

# Learning gate
python ci/scripts/gate_runner.py learning_check \
  --upstream-agent "Learning Agent" \
  --downstream-agent "Spec Agent" \
  --ticket-id M902-06 \
  --input '{"checkpoint_dir": "project_board/checkpoints/", "policy_file": "project_board/902_06_learning_gate_policy.yml"}'
```

---

## Remediation Decision Tree

When a gate fails:

1. **Planner Gate WARN:** Review ticket dependencies; refactor to break cycles if necessary.
2. **Spec Completeness FAIL:** Add missing section(s) per gate output; re-run gate.
3. **Test Assertion Density WARN:** Add assertions to test functions; consider splitting tests if complexity warrants separate tests.
4. **TODO/FIXME WARN:** Document reason for TODO in PR comment; or complete the work; or create follow-up ticket.
5. **Suppression Audit WARN:** Add issue/ticket reference to suppression comment.
6. **Learning Gate FAIL:** Refactor code to remove forbidden phrase; or create follow-up ticket with explicit reference in code.

---

## Handoff Sequence (Workflow Enforcement)

1. **Planner Agent** runs planner_check; if WARN, escalates to human for decision.
2. **Spec Agent** spec and runs spec_completeness_check via orchestrator before advancing to TEST_DESIGN.
3. **Test Designer** produces behavioral tests; test_check runs to validate assertion density.
4. **Test Breaker** produces adversarial tests; manual review of test count and error coverage.
5. **Implementation Agent** implements code; reviewer_check runs on `git diff --cached` before each commit.
6. **Learning Agent** produces checkpoint outputs; learning_check scans for forbidden phrases.
7. **Acceptance Criteria Gatekeeper** verifies all gates have been run and passed/warned appropriately.

---

## M903 Enhancements (Out of Scope for M902-06)

- Mutation testing gate (mutation score per module)
- Performance regression detection (execution time, memory usage)
- Example extraction + validation gate (parse and execute examples from specs)
- Enforcement mode: convert WARN → FAIL for governance + learning gates
- Diff-cover enforcement: currently exists in blobert CI; M903 integrates with gate framework
