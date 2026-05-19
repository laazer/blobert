# M902-16 Specification Checkpoint

**Date:** 2026-05-19  
**Stage:** SPECIFICATION  
**Spec Agent:** Initial Analysis

## Analysis Summary

Read execution plan, workflow enforcement module, checkpoint protocol, M902-01/02 gate examples, and code_governance.md Stage 8 architecture.

## Key Decisions

### 1. Gate Framework Integration Pattern
**Would have asked:** How should security_gate_check.py integrate with the M902-01 gate runner framework?
**Assumption made:** Follow exact M902-01 and M902-02 patterns:
- Implement `run(inputs: dict) -> dict` function
- Return JSON matching gate schema: status, violations[], remediation_hints[], duration_ms, artifacts[], tool_statuses[]
- Register in gate_registry.json with category "security"
- Support --mode shadow|blocking via gate_runner
**Confidence:** HIGH (M902-01/02 are reference implementations, fully COMPLETE)

### 2. Tool Selection Authority
**Would have asked:** Are the 5 tools (gitleaks, bandit, semgrep, pip-audit, npm audit) flexible or frozen?
**Assumption made:** FROZEN per code_governance.md Stage 8 (lines 365-383). No tool substitutions or omissions allowed; all 5 are mandatory for M902-16.
**Confidence:** HIGH (explicit in code_governance.md and execution plan)

### 3. Severity Thresholds
**Would have asked:** What CVSS threshold is "critical" for CVEs?
**Assumption made:** CVSS ≥7.0 = hard fail, <7.0 = soft fail (WARN). Industry standard aligns with NIST definitions. Confirmed in execution plan Task 1.
**Confidence:** HIGH (standard security practice, documented in execution plan)

### 4. Mock Fixtures vs Real Secrets
**Would have asked:** Can test fixtures contain real secret patterns or fake-only patterns?
**Assumption made:** MOCK ONLY (non-functional). Prevents accidental committed real secrets. Gitleaks pre-commit hook validates. Documented in execution plan Task 3.
**Confidence:** HIGH (security best practice, enforced by code review)

### 5. Tool Timeout Strategy
**Would have asked:** Should timeouts be per-tool or aggregate?
**Assumption made:** PER-TOOL with aggregate limit:
- gitleaks: 10s
- bandit: 30s
- semgrep: 60s
- pip-audit: 20s
- npm audit: 20s
- Total gate: <120s
Documented in execution plan Task 1, confirmed via tuning in Task 11 integration tests.
**Confidence:** MEDIUM (requires baseline validation from Task 2 audit)

### 6. Exclusion Policy
**Would have asked:** Which artifacts should security scanning skip?
**Assumption made:** Per CLAUDE.md guardrails:
- *.glb (binary models)
- Generated asset exports
- node_modules/, .venv/
- reference_projects/
- Generated lockfiles
Documented explicitly in spec per CLAUDE.md section "Non-Traditional Repo Guardrails".
**Confidence:** HIGH (direct from CLAUDE.md)

### 7. Determinism Requirement
**Would have asked:** Can tool output vary across runs?
**Assumption made:** NO randomness permitted. Same staged files → identical findings every time. No network dependencies (offline mode if available). Tool versions pinned in pyproject.toml/package.json. Documented in execution plan.
**Confidence:** HIGH (explicit requirement in execution plan, Stage 8 architecture)

### 8. Shadow Mode vs Blocking
**Would have asked:** Should security violations hard-fail commits in M902?
**Assumption made:** SHADOW MODE ONLY in M902. Gate runs, produces findings, always exits 0 (shadow mode). Enforcement (exit 1) deferred to M903 per code_governance.md and execution plan. Documented as "non-blocking in M902".
**Confidence:** HIGH (explicit in code_governance.md Stage 8, confirmed in execution plan)

## No Ambiguities Remaining

All major design decisions are anchored to:
1. code_governance.md Stage 8 (authoritative architecture spec)
2. M902-01/02 specs (gate framework, tool orchestration patterns)
3. Execution plan (tool selections, thresholds, scope)
4. CLAUDE.md (guardrails, exclusions)

---

**Status:** Ready to write full spec document at `project_board/specs/902_16_security_gate_spec.md`

**Next:** Proceed to spec document generation with 8 frozen requirements per execution plan.
