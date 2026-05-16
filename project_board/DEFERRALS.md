# Deferrals Index

Tracks out-of-scope features and decisions deferred to future milestones.

---

## Milestone 902 Deferrals (Deferred to M903+)

| Ticket | Feature | Target Milestone | Rationale | Status |
|--------|---------|------------------|-----------|--------|
| M902-01 | Spec template UI visualization | M903 | Gate framework focuses on CLI/validation; visualization is presentation-only | DEFERRED |
| M902-02 | Mutation testing metrics | M903 | Mutation tooling not yet installed; placeholder WARN logic implements gate pattern | DEFERRED |
| M902-03 | Governance rule enforcement (blocking) | M903 | M902 implements rule catalog; enforcement (hard blocks) deferred for M903 hardening | DEFERRED |
| M902-04 | Metadata schema v1.0 → v1.1 upgrade | M903 | v0.2.0 handles current gate metadata; v1.1 will add audit/workflow fields | DEFERRED |
| M902-05 | Hook self-bypass enforcement | M903 | PreToolUse hooks implemented; BLOBERT_SKIP_HOOKS escape hatch allows M903 policy tightening | DEFERRED |
| M902-06 | Automated TODO/FIXME remediation | M903 | Gate detects violations; auto-fix logic deferred to M903 (risk: over-aggressive cleanup) | DEFERRED |
| M902-07 | Automated remediation ticket generation | M903 | Audit emits markdown snippets; backlog ticket creation (file I/O, templating) deferred | DEFERRED |
| M902-07 | Baseline policy enforcement (expiry, notification) | M903 | Baseline tolerates grandfathered violations; M903 adds owner notification, auto-delete | DEFERRED |
| M902-07 | Performance tuning (parallel linting, caching) | M903 | Audit runs <30s on typical repos; incremental scanning deferred | DEFERRED |

---

## Non-Deferrals (M902 Scope)

| Ticket | Feature | Reason |
|--------|---------|--------|
| M902-01 | Gate framework CLI + registry | CORE INFRASTRUCTURE — required by M902-02 through M902-07 |
| M902-02 | Static analysis linting (ruff, mypy, eslint, semgrep, etc.) | CORE INFRASTRUCTURE — blocks gate development |
| M902-03 | Governance rule catalog (30+ rules) | CORE REQUIREMENT — defines policy enforceability |
| M902-04 | Handoff metadata schema v0.2.0 | CORE REQUIREMENT — gates use metadata to escalate |
| M902-05 | PreToolUse command inspection hooks | CORE REQUIREMENT — governance bypass prevention |
| M902-06 | Per-stage gate checklists (6 gates) | CORE REQUIREMENT — ensures consistency across agent handoffs |
| M902-07 | Audit + baseline mechanism | CORE REQUIREMENT — grandfathers existing violations while catching new ones |

---

## Decision Log

### M902-01: Why defer gate visualization?
- **Decision:** CLI-only for MVP; no UI for viewing gate results
- **Rationale:** Gate framework focuses on validation contracts (JSON/YAML); visualization is presentation-layer (M903)
- **Impact:** Operators read gate output from terminal/CI logs; dashboard deferred
- **Confidence:** HIGH — aligns with Milestone 902 scope (validation gates, not dashboarding)

### M902-02: Why defer mutation testing?
- **Decision:** Implement WARN placeholder for mutation score; no actual mutation tooling
- **Rationale:** Mutation testing tools (mutmut, cosmic-ray) not installed; adding new dependency deferred to M903
- **Impact:** Gate template shows "Mutation score: [WARN] metric not available" (advisory only)
- **Confidence:** HIGH — ticket explicitly permits WARN placeholders

### M902-07: Why defer automated ticket generation?
- **Decision:** Audit emits markdown snippets suitable for manual backlog entry; auto-creation deferred
- **Rationale:** Automated file creation + templating is a separate subsystem (risk of creating malformed tickets)
- **Impact:** Operator manually creates backlog tickets from audit markdown snippets
- **Confidence:** MEDIUM — M903 must coordinate with backlog structure to avoid errors

---

## Milestone 903 Pre-Planning

### Suggested M903 Roadmap (from M902 deferrals)
1. **Gate Visualization Dashboard:** web UI for browsing gate results, trends, remediation status
2. **Mutation Testing Integration:** install mutmut/cosmic-ray, integrate into test gate
3. **Governance Enforcement Hardening:** convert advisory WARN gates to blocking (policy enforcement)
4. **Baseline Policy Engine:** owner notification, auto-expiry, second-reviewer approval
5. **Remediation Ticket Automation:** auto-generate backlog tickets from audit/gate violations
6. **Performance Optimization:** parallel linting, incremental scanning, caching

---

## Notes

- Deferrals are deliberate scope boundaries, not "nice-to-haves"
- Each deferral explicitly states Target Milestone (M903, M904, etc.) and Rationale
- Confluence point: M903 planning should reference this index to identify handoff artifacts from M902
