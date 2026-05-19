# M902-16: Stage 8 — Security Gate Integration

## Description

Implement Stage 8 of the 8-stage governance pipeline: **Final Security Gate**. Run security scanning tools (gitleaks, bandit, dependency audit) and hard-fail on critical violations. Aggregate findings from multiple tools (gitleaks for secrets, bandit + semgrep for Python security, pip-audit / npm audit for dependencies) and render deterministic FAIL/WARN/PASS decisions based on severity thresholds.

## Acceptance Criteria

- [ ] **AC-1:** Gate runs gitleaks for secrets detection; any secret triggers hard FAIL
- [ ] **AC-2:** Gate runs bandit + semgrep security rules for Python code
- [ ] **AC-3:** Gate runs pip-audit (Python) and npm audit (JavaScript) for dependency CVEs
- [ ] **AC-4:** Hard-fail conditions: secrets detected, unsafe deserialization, auth bypass patterns, critical CVEs (CVSS 7.0+)
- [ ] **AC-5:** Soft-fail conditions: low/medium CVEs, security warnings return WARN status
- [ ] **AC-6:** Implemented as `ci/scripts/gates/security_gate_check.py` integrated into M902-01 framework
- [ ] **AC-7:** Integrated into gate registry as final gate before commit; returns M902-01 success schema
- [ ] **AC-8:** Tested with known vulnerability patterns (test fixtures validate detection without committing real vulnerabilities)
- [ ] **AC-9:** False positive analysis documented in spec; validation results deterministic (same input → identical findings)

## Dependencies

- **M902-01** (Validation Gate Framework) — COMPLETE
- **M902-02** (Static Analysis tools) — TBD (verify availability in CI environment)
- `code_governance.md` Stage 8 architecture

## WORKFLOW STATE

| Field | Value |
|-------|-------|
| **Stage** | TEST_BREAK |
| **Revision** | 4 |
| **Last Updated By** | Test Designer Agent |
| **Next Responsible Agent** | Test Breaker Agent |
| **Status** | Proceed |

## NEXT ACTION

Test Breaker Agent: Develop adversarial test suite for M902-16 security gate. Create `tests/ci/test_security_gate_check_adversarial.py` with 30+ adversarial tests covering timeout scenarios, tool subprocess failures, malformed output, boundary thresholds (CVSS exactly 7.0 vs 6.9), determinism validation, and mixed violation scenarios. Behavioral tests completed: 59 tests at `tests/ci/test_security_gate_check.py` covering all 5 tools, decision matrix, schema compliance, and edge cases. See spec at `project_board/specs/902_16_security_gate_spec.md` for threat model and decision logic.
