# M902-16 Test Designer Checkpoint

## Decisions Made

### Spec Gap: Fixture Pre-Existence
**Would have asked:** Should test fixtures (mock secrets, unsafe code patterns, vulnerable packages) be pre-created by Spec Agent, or should this test suite assume they exist?

**Assumption made:** Per the execution plan (Tasks 3-6), Spec Agent creates fixtures before Test Designer writes behavioral tests (Task 7). I will assume fixtures exist at:
- `tests/ci/fixtures/mock_secrets/` — gitleaks test data
- `tests/ci/fixtures/bandit_unsafe_patterns/` — bandit test data
- `tests/ci/fixtures/semgrep_patterns/` — semgrep test data  
- `tests/ci/fixtures/vulnerable_packages/` — dependency audit test data

Tests will validate gate behavior by mocking subprocess calls to tools (not executing real tools), so fixture existence is not a hard blocker for test writing. If fixtures don't exist, integration tests (Task 11) will validate real tool behavior.

**Confidence:** High — this aligns with TDD practice (write tests against spec, implement later).

### Gate Implementation Pre-Existence
**Would have asked:** Should tests assume `ci/scripts/gates/security_gate_check.py` already exists?

**Assumption made:** Per execution plan (Task 9 Implementation), the gate is implemented after tests are designed. Tests will mock/patch the gate entry point or test expected behavior through a fake/stub gate object. Tests should NOT assume the real gate exists; instead, they validate the **behavior contract** defined in the spec.

**Confidence:** High — this is standard TDD: tests define contract, implementation satisfies tests.

### Tool Subprocess Mocking
**Would have asked:** Should tests execute real gitleaks/bandit/semgrep/pip-audit/npm audit, or mock subprocess calls?

**Assumption made:** Per spec (Requirement 8), tests are deterministic and do not require network calls. Behavioral tests (Task 7) will mock all tool subprocess calls to fixture JSON output. This ensures:
1. Tests are fast and deterministic (no tool version drift)
2. Tests validate gate logic (parsing, decision matrix, aggregation)
3. Integration tests (Task 11) will run real tools on real fixtures

**Confidence:** High — mocking is standard practice for testing orchestration logic.

### Tool Status Array vs Individual Tool Wrapper Classes
**Would have asked:** Should tests validate each tool's status object in `tool_statuses[]` array, or should gate logic handle tool status internally?

**Assumption made:** Per spec Requirement 6 (Gate Output Contract), the JSON schema requires a `tool_statuses[]` array with entries for each tool (gitleaks, bandit, semgrep, pip-audit, npm-audit). Each entry must have: name, exit_code, findings_count, timeout, error. Tests will assert that this array is always present and complete, even if a tool was skipped or timed out.

**Confidence:** High — spec is explicit on schema.

### Determinism Test Strategy
**Would have asked:** How should determinism tests verify that repeated runs produce identical results?

**Assumption made:** Per spec Requirement 8 (Determinism Validation), determinism tests will run the gate twice on the same mock input and assert:
1. Same `violations[]` array (order and content)
2. Same `status` field (FAIL/WARN/PASS)
3. Same decision logic output (no randomness)
Determinism tests will NOT compare `timestamp` or `duration_ms` fields, since those are expected to vary between runs.

**Confidence:** High — spec is explicit that determinism excludes time-based fields.

### Severity Cascade Priority
**Would have asked:** When multiple violations of different severity are present (e.g., secret + medium CVE), which takes priority in decision logic?

**Assumption made:** Per spec Requirement 5 (Severity Thresholds), the priority cascade is:
1. Secrets (gitleaks) → always FAIL
2. Unsafe deserialization (bandit B301-B303, semgrep) → always FAIL
3. Auth bypass (semgrep) → always FAIL
4. CVSS ≥7.0 (pip-audit, npm audit) → always FAIL
5. CVSS 4.0-6.9 or medium severity (bandit, semgrep) → WARN (if no hard-fail above)
6. CVSS <4.0 or low severity → INFO
7. No violations → PASS

Tests will parametrize this decision matrix explicitly.

**Confidence:** High — spec Requirement 5 is explicit on cascade order.

---

## Test Design Summary

**Test File:** `tests/ci/test_security_gate_check.py`

**Coverage:**
- 40+ behavioral tests organized by tool and scenario
- All 5 tools covered: gitleaks, bandit, semgrep, pip-audit, npm audit
- All 5 gate outcomes: FAIL (secrets), FAIL (unsafe code), FAIL (critical CVEs), WARN (medium CVEs), PASS (no violations)
- Edge cases: empty violations, mixed findings, decision priority
- Determinism: repeated runs on same input → identical output
- Schema validation: JSON output matches M902-01 gate schema

**Test Names Convention:**
- `test_gitleaks_<scenario>` — gitleaks scenarios
- `test_bandit_<scenario>` — bandit scenarios
- `test_semgrep_<scenario>` — semgrep scenarios
- `test_pip_audit_<scenario>` — pip-audit scenarios
- `test_npm_audit_<scenario>` — npm audit scenarios
- `test_decision_matrix_<scenario>` — decision logic and priority
- `test_schema_compliance_<scenario>` — output schema validation
- `test_determinism_<scenario>` — idempotency and consistency

---

## Known Unknowns (Deferred to Implementation/Test Breaker)

1. **Tool output format variance:** If real tool JSON output differs from mocked format, integration tests (Task 11) will catch parsing errors.
2. **Timeout strategy:** Spec defines per-tool timeouts (gitleaks 10s, bandit 30s, semgrep 60s, pip-audit 20s, npm audit 20s). Adversarial tests (Task 8) will cover timeout failure modes.
3. **Remediation hint content:** Spec requires actionable hints but doesn't prescribe exact wording. Tests will validate presence and non-emptiness; content validation in implementation.
4. **Tool unavailability:** If a tool is not installed/available, spec says "checkpoint and skip". Tests will mock tool availability; real availability validation in CI environment setup.

---

## Next Steps

1. Write 40+ behavioral tests in `tests/ci/test_security_gate_check.py`
2. Commit test file
3. Hand off to Test Breaker Agent for adversarial tests (Task 8)
4. Hand off to Implementation Agent (Task 9) — tests define contract

**Status:** READY TO WRITE TESTS
