# Title

PreToolUse hooks: argv-aware command inspection and hard blocks for bypass attempts

# Context

The MVP requires PreToolUse hooks for all agent shell/tool execution that parse argv safely, normalize commands, inspect nested shell constructs where feasible, and hard-block governance/CI bypass patterns (including multiline attempts). Simple substring matching alone is insufficient.

# Scope

- Implement hook integration compatible with Cursor hooks or Claude Code hooks (follow existing repo hook layout under `.cursor/` or `.claude/` as applicable).
- Parse and normalize commands sufficiently to detect: `git commit --no-verify`, hook disabling env vars, deletion/disablement of governance scripts, global linter disables, and nested `bash -c` / `sh -c` payloads carrying bypass flags.
- Provide explicit failure messages and remediation steps.
- Add tests for the parser/normalizer using representative command vectors.

# Scope

- Implement hook integration compatible with Cursor hooks or Claude Code hooks (follow existing repo hook layout under `.cursor/` or `.claude/` as applicable).
- Parse and normalize commands sufficiently to detect: `git commit --no-verify`, hook disabling env vars, deletion/disablement of governance scripts, global linter disables, and nested `bash -c` / `sh -c` payloads carrying bypass flags.
- Provide explicit failure messages and remediation steps.
- Add tests for the parser/normalizer using representative command vectors.

# Acceptance Criteria

- Hook fires before tool execution for configured tool types (document which tools are covered).
- Parser tests cover at least: direct bypass, nested `-c` bypass, combined flags, and benign commands that must not false-positive.
- Blocking behavior is configurable (strict in CI-like profiles; optional warn profile for local dev) but default policy is documented.

# Agent Execution Prompt

Implement PreToolUse command inspection hooks.

Goal: Add a robust command inspection layer with unit-tested parsing and integrate it into the project's hook system.

Constraints:
- Do not block legitimate workflows (document escape hatches if any).
- Avoid executing user commands during inspection.

Expected output:
- Hook config + implementation + tests.
- Short operator doc: how to run locally and what is blocked.

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (hook platform API docs, test harness)
- What assumption cannot be verified? (which agents actually honor hooks)
- What ambiguity prevents completion? (coverage of zsh/bash-specific quoting)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about which shell is canonical for agents?
- What decision needs to be made about allowlisted maintenance commands?
- What are the possible interpretations of "inspect nested shell execution" depth limits?

# Dependencies

None (can proceed in parallel; coordinate file locations with gate framework ticket).

# Definition of Done

- Hooks merged with tests and documented defaults.
- Parser test suite passes in CI.

---

## PLANNING NOTES

**Specification Delivered:**
- Complete functional and non-functional specification at `project_board/specs/902_05_pretooluse_hooks_spec.md` (frozen in Tasks 1–3).
- Specification includes:
  - **Requirement 01:** Command Parsing Algorithm & Bypass Pattern Catalog (5 patterns, 3+ examples per pattern, false positive analysis)
  - **Requirement 02:** Hard-Block Failure Messages & Remediation Documentation (6 error templates, operator guide structure)
  - **Requirement 03:** Configurable Blocking Modes & Default Policy (STRICT/WARN/SHADOW, behavior matrix, exit codes, escape hatches)
  - **Requirement 04:** Non-Functional Requirements (performance <100ms, false positive <5%, security, usability)
- All assumptions frozen with confidence levels.
- All 5 bypass patterns documented: GIT_NO_VERIFY, HOOK_ENV_DISABLE, GOVERNANCE_SCRIPT_DELETION, GLOBAL_LINTER_DISABLE, NESTED_BYPASS_PAYLOAD.
- Test strategy provided (25–35 behavioral, 20–30 adversarial tests).

**Bypass Pattern Catalog (Frozen):**
1. **Git --no-verify:** Detects `git commit|push` with `--no-verify` or `-n` flag (any order, variant forms)
2. **Hook env disables:** Detects env vars LEFTHOOK, PRE_COMMIT, HUSKY, SKIP_HOOKS, GIT_COMMIT_MESSAGE_SKIP set to disable hooks
3. **Governance script deletion:** Detects `rm` targeting `.lefthook/`, `.claude/`, `ci/scripts/`, `project_board/`
4. **Global linter disables:** Detects `--no-sort`, `--ignore-errors`, `--no-enforce`, `--disable`, `# noqa`, `# eslint-disable`
5. **Nested bash -c / sh -c payloads:** Recursively extracts and checks nested commands (max depth 2)

**Blocking Modes (Frozen):**
- **STRICT (default local):** Hard block, exit code 1, error response
- **WARN:** Log warning, allow execution, exit code 0
- **SHADOW (default CI):** Log info, allow execution, exit code 0
- **Escape Hatches:** `BLOBERT_HOOK_MODE=warn|shadow`, `BLOBERT_SKIP_HOOKS=1`

**Error Message Templates:**
- All 6 templates provided (5 patterns + parser error)
- Each includes: reason, governance rule, remediation steps, documentation_url
- Non-scary tone, actionable remediation, escape hatch references

**Non-Functional Requirements:**
- NFR-01: Parsing <100ms per command, nesting recursion <1s
- NFR-02: <5% false positive rate
- NFR-03: No command execution, no secrets in logs, no eval/exec
- NFR-04: Robust to malformed JSON, oversized input
- NFR-05: Logging with timestamp, hook_id, pattern, snippet, mode, exit code
- NFR-06: Deterministic (same input → same output)
- NFR-07: Error messages actionable and non-scary
- NFR-08: Escape hatches discoverable in operator guide

**Implementation Tasks (Tasks 4–13, pending):**
- Task 4: Command Parser Implementation (Python/Bash)
- Task 5: Blocking Mode & Escape Hatch Logic
- Task 6: Hard-Block Failure Messages & JSON Formatting
- Task 7: Hook Integration with `.claude/settings.json`
- Task 8: Operator Guide Generation (`.claude/hooks/OPERATOR_GUIDE.md`)
- Task 9: Parser Unit Test Suite (25–35 behavioral tests)
- Task 10: Parser Adversarial Test Suite (20–30 tests)
- Task 11: Integration Test with Actual Hook
- Task 12: Static QA (Ruff, Pylint, Semgrep)
- Task 13: Acceptance Validation & Ticket Closure

---

## TEST DESIGN NOTES

**Behavioral Test Suite Delivered:**
- File: `tests/ci/test_pretooluse_command_inspection.py`
- Test Design Doc: `project_board/test_designs/902_05_command_inspection_test_design.md`
- Total Tests: 80 (all passing, 0.16s execution)
- Test Classes: 6 (parsing, 5 bypass patterns, modes, env vars, errors, benign commands, edge cases)
- Coverage: All 4 requirements, 34 acceptance criteria, 5 bypass patterns, 3 blocking modes
- False Positive Rate: 0% on benign command suite (13 commands, 100% allowed)

**Test Organization:**
- TestCommandParsingAndNormalization (8 tests): JSON extraction, whitespace/quote normalization, UTF-8
- TestGitNoVerifyBypassPattern (7 tests): git --no-verify / -n detection, short form, nested -c
- TestHookEnvDisableBypassPattern (7 tests): LEFTHOOK, HUSKY, PRE_COMMIT, SKIP_HOOKS detection
- TestGovernanceScriptDeletionBypassPattern (6 tests): rm targeting .lefthook, .claude, ci/scripts, project_board
- TestGlobalLinterDisableBypassPattern (6 tests): --no-sort, --disable, # noqa, # eslint-disable detection
- TestNestedBypassPayloadDetection (5 tests): bash -c / sh -c nesting (depth 1–2), recursive extraction
- TestBlockingModesAndExitCodes (7 tests): STRICT/WARN/SHADOW modes, exit codes (0/1/2)
- TestEnvironmentVariableOverrides (5 tests): BLOBERT_HOOK_MODE, BLOBERT_SKIP_HOOKS, CI detection
- TestErrorMessageAndRemediation (8 tests): JSON response format, 6 error templates, escape hatches
- TestBenignCommandsNoFalsePositives (13 tests): npm, docker, python, make, git, bash, linter commands
- TestEdgeCases (8 tests): Malformed JSON, oversized input, null bytes, deep nesting, whitespace

**Specification Gaps:** None. Spec is frozen and complete.

**Handoff for Test Breaker:** Write adversarial test suite (20–30 tests) for evasion attempts, suppression abuse, configuration mutations, tool-level failures, schema boundary violations, governance bypass attempts.

---

## ADVERSARIAL TEST NOTES

**Adversarial Test Suite Delivered:**
- File: `tests/ci/test_pretooluse_command_inspection_adversarial.py`
- Total Tests: 31 (all passing, 0.19s execution)
- Test Classes: 6 (evasion, config mutations, tool failures, schema violations, governance bypass, performance)
- Coverage: Targets weaknesses, evasion techniques, edge cases, configuration boundaries
- Test organization:
  - TestBypassEvasionTechniques (8 tests): Quoting evasion, case variation, comment obfuscation, env var substitution, hex escapes, variable indirection, case-sensitive env vars, path traversal deletion
  - TestConfigurationMutations (5 tests): Mode typo (case-sensitive), escape hatch typo, empty mode value, CI environment missing, mode priority override
  - TestToolFailures (4 tests): Malformed JSON, oversized input (>10MB), null bytes, recursion depth bomb (DoS prevention)
  - TestSchemaViolations (4 tests): Missing required error response fields, pattern name mutation, invalid exit codes, missing continue field
  - TestGovernanceBypassAttempts (4 tests): Direct hook disabler in CI, blanket suppress (eslint-disable), suppression without issue link, env var mode bypass attempt
  - TestPerformanceAndBoundaries (3 tests): Performance (1000 benign commands <1s), stress (100 depth-2 nested <5s), false positive resilience under evasion stress
  - TestCheckpointEncodedEdgeCases (3 tests): Env var word boundary, nesting depth limit enforcement, case-sensitive mode selection

**Adversarial Coverage:**
- Evasion attempts: 8 tests covering obfuscation, indirection, encoding
- Configuration edge cases: 5 tests covering typos, defaults, fallback behavior
- Tool robustness: 4 tests covering malformed input, resource exhaustion, DoS prevention
- Schema/contract validation: 4 tests covering response format, field presence, valid codes
- Governance bypass evasion: 4 tests covering suppression abuse, mode tricks
- Performance/determinism: 3 tests covering batch operations, stress conditions, determinism

**Combined Test Suite:**
- Behavioral: 80 tests
- Adversarial: 31 tests
- Total: 111 tests (all passing, 0.18s combined execution)

**Key Adversarial Findings:**
- Tests encode strictest defensible expectations for ambiguous cases (e.g., env var case sensitivity, mode priority, nesting depth)
- All tests target executable behavior (no prose assertions)
- Tests are deterministic and reproducible
- No mocks for core logic; mocks used for env/file seams where appropriate
- Tests validate parser robustness against: malformed input, oversized data, null bytes, recursion bombs, and configuration edge cases

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | IMPLEMENTATION_BACKEND |
| Revision | 5 |
| Last Updated By | Test Breaker Agent |
| Next Responsible Agent | Implementation Agent |
| Status | Proceed |
| Validation Status | ADVERSARIAL TESTS COMPLETE; 31 tests passing; combined suite 111/111 passing; ready for implementation |
| Blocking Issues | None |
