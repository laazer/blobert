# M902-16: Stage 8 — Security Gate Integration

**Status:** PENDING  
**Target:** 2026-07-27

## Overview

Implement Stage 8 of the 8-stage governance pipeline: **Final Security Gate**. Run security scanning tools (gitleaks, bandit, dependency audit) and hard-fail on critical violations.

## Acceptance Criteria

- [ ] Gate runs: gitleaks (secrets detection), bandit (Python security), semgrep security rules, npm audit / pip-audit (dependency vulnerabilities)
- [ ] Hard-fail conditions: secrets detected, unsafe deserialization, auth bypass patterns, critical CVEs (CVSS 7.0+)
- [ ] Soft-fail conditions: low/medium CVEs, security warnings
- [ ] Implemented as `ci/scripts/gates/security_gate_check.py`
- [ ] Integrated into gate registry as final gate before commit
- [ ] Tested with known vulnerability patterns (does NOT commit them)
- [ ] False positive analysis documented

## Implementation Notes

- Invoke gitleaks: `gitleaks detect --source . -v`
- Invoke bandit: bandit with semgrep security rules
- Invoke dependency audit: `pip-audit` for Python, `npm audit` for JS
- Aggregate all findings; any secret = immediate hard fail
- Return FAIL with full violation list + remediation links

## Spec Reference

See: `project_board/specs/902_16_security_gate_spec.md`

## Dependencies

- M902-01 (Validation Gate Framework)
- M902-02 (Static Analysis tools)
- `code_governance.md` Stage 8 architecture
