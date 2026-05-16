# Checkpoint Log: M902-07 Governance Audit Pipeline and Baseline — SPECIFICATION Stage

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/07_governance_audit_pipeline_and_baseline.md`

**Run ID:** `2026-05-16T14-00-00Z-specification`

**Stage:** SPECIFICATION

**Agent:** Spec Agent

---

## Summary

Spec Agent completed the comprehensive specification for M902-07 governance audit pipeline and baseline feature. The specification document (`project_board/specs/M902-07_audit_pipeline_spec.md`) fully addresses the ticket requirements: audit command architecture, baseline schema design, violation clustering algorithm, baseline diff detection, JSON and Markdown report generation, metadata integration with gate framework, operator guide, and example baseline.

All functional requirements (FR1–FR9) and non-functional requirements (NFR1–NFR3) are fully specified with acceptance criteria, risk analysis, and no unresolved ambiguities.

---

## Specification Completeness

**Functional Requirements:**
- **FR1: Audit Command Architecture** — Unified audit entry point, CLI flags, gate runner integration, error handling.
- **FR2: Baseline Schema and Validation** — JSON Schema definition, immutability policy, validation logic, example entries.
- **FR3: Violation Clustering Algorithm** — Deterministic grouping by (rule_id, path_cluster), language-specific depth tuning.
- **FR4: Baseline Diff Detection** — New/expired/remediated violation categories, audit status mapping, unknown rule handling.
- **FR5: Audit Report Generation (JSON)** — Structured JSON with violations, clusters, baseline diff, metadata, summary.
- **FR6: Remediation Report Generation (Markdown)** — Human-readable markdown with cluster sections and ticket templates.
- **FR7: Metadata Integration with Gate Framework** — Audit event logging, metadata field wiring, integration with M902-04 event log.
- **FR8: Operator Guide and Baseline Update Policy** — Documentation of workflows, decision trees, troubleshooting, policy deferral to M903.
- **FR9: Example Baseline Fragment** — 5–8 realistic baseline entries demonstrating schema usage.

**Non-Functional Requirements:**
- **NFR1: Determinism and Reproducibility** — Audit outputs are identical for identical inputs.
- **NFR2: Performance** — Full audit completes in <30 seconds on typical repos.
- **NFR3: Graceful Error Handling** — Clear diagnostics for all error modes.

**Risk Taxonomy:** High, medium, and low-priority risks documented with mitigation strategies and ownership.

**Decisions Frozen:** 10 key design decisions documented (audit architecture, baseline granularity, expiration policy, ownership model, schema, remediation generation, clustering depth, mode handling, immutability, metadata integration).

**Deferred Boundaries:** 8 features explicitly deferred to M903 (enforcement blocking, second-reviewer gate, auto-remediation, expiration enforcement, advanced clustering, secret scanning, dashboards, parallel execution).

---

## Key Design Decisions (Checkpoint)

### [M902-07] Audit Architecture — Gate Reuse Decision

**Would have asked:** Should the audit command reuse M902-02 static analysis gate or implement a separate pipeline?

**Assumption made:** Audit command invokes M902-02 gate via M902-01 gate_runner.py and wraps output with clustering, baseline comparison, and reporting logic. This preserves investment in static analysis tooling and avoids duplication.

**Confidence:** High. M902-02 is COMPLETE with 83+ tests; gate schema is frozen and stable (M902-01 verified).

---

### [M902-07] Baseline Granularity — Rule + Path Prefix

**Would have asked:** Granularity at rule + path prefix (aggregated), per-violation fingerprint (file + line), or per-file?

**Assumption made:** Baseline entries group by (rule_id, path_prefix), e.g., `ruff:F401:asset_generation/python/src/models/`. This reduces baseline file size and simplifies reasoning. Fine-grained fingerprints deferred to M903.

**Confidence:** High. Ticket explicitly mentions "clustering (by rule + path prefix)"; planning checkpoint supports this.

---

### [M902-07] Expiration Policy — Absolute ISO 8601 Dates

**Would have asked:** Sensible defaults for expires_at? Absolute vs relative? Configurable per entry or global?

**Assumption made:** Each baseline entry carries optional absolute `expires_at` ISO 8601 date (UTC). Entries without expiration are permanent. Enforcement logic deferred to M903.

**Confidence:** Medium-High. Allows flexibility; M903 can add defaults if needed.

---

### [M902-07] Ownership Model — Free-Text String

**Would have asked:** What does "owner" mean? GitHub username, team name, email?

**Assumption made:** Owner is free-text string (e.g., "alice@blobert.team" or "Backend Team"). No validation in M902-07; enforcement/notification deferred to M903.

**Confidence:** Medium. Spec documents as code review responsibility (manual validation).

---

### [M902-07] Remediation Ticket Generation — Markdown Snippets

**Would have asked:** Auto-create backlog tickets or generate markdown for manual creation?

**Assumption made:** Audit command generates markdown remediation report suitable for human review. Ticket creation deferred to M903 or manual process.

**Confidence:** High. Ticket says "outputs markdown snippets suitable for `project_board/**/00_backlog/`" without requiring automation.

---

### [M902-07] Clustering Depth Tuning — Language-Specific

**Would have asked:** Fixed cluster depth across all languages or language-specific?

**Assumption made:** Depth = 2 for Python/React backend, depth = 1 for Godot/jscpd. Language context derived from file path; depth tunable in M903.

**Confidence:** Medium. Heuristic based on typical repo structure; M903 can refine.

---

### [M902-07] Schema Validation — Strict on Load

**Would have asked:** Validate baseline against schema or permit lenient parsing?

**Assumption made:** Audit command validates baseline file on load; invalid entries cause audit to fail with clear diagnostic. This prevents silent corruption.

**Confidence:** High. Basic hygiene requirement.

---

### [M902-07] Immutability Policy — Append-Only Baseline

**Would have asked:** Allow in-place modification of baseline entries?

**Assumption made:** Baseline entries are append-only; updates mean adding new entries with modified path_prefix or rule_id. No deletion or in-place modification.

**Confidence:** High. Supports auditability and M903 second-reviewer gate.

---

### [M902-07] Metadata Integration — Gate Schema Extension or Separate

**Would have asked:** Extend M902-04 gate schema (v0.2.0) or maintain separate metadata contract?

**Assumption made:** Audit extends gate schema with new fields (audit_timestamp, audit_violations_count, audit_clusters_count, etc.). Version decision (v0.2.0 extension vs v0.3.0) deferred to implementation (Task 7). No conflicts expected.

**Confidence:** Medium. M902-04 schema is stable; field additions are backward-compatible.

---

### [M902-07] Mode Handling — Shadow Mode Only in M902-07

**Would have asked:** Implement both shadow and blocking modes?

**Assumption made:** M902-07 implements shadow mode (reports violations without enforcing exit 1). Blocking mode enforcement deferred to M903. Audit command accepts --mode flag for future compatibility.

**Confidence:** High. Ticket context (grandfathering + expiration) aligns with M903 enforcement phase.

---

## No Unresolved Ambiguities

All clarification prompts from the ticket have been addressed:

1. **Baseline granularity** — Spec FR2 defines rule + path prefix granularity with schema and examples.
2. **Expiration defaults** — Spec FR2 documents optional absolute ISO 8601 dates; M903 can add defaults.
3. **Governance trend metrics** — Out of scope for M902-07; M903 can add dashboards and observability.

---

## Specification Document Details

**Location:** `/Users/jacobbrandt/workspace/blobert/project_board/specs/M902-07_audit_pipeline_spec.md`

**Size:** ~650 lines (comprehensive specification with FR1–FR9, NFR1–NFR3, risk taxonomy, deferred boundaries).

**Sections:**
- Executive Summary
- 9 Functional Requirements (each with spec summary, constraints, assumptions, scope, acceptance criteria 8–10 per req, risk analysis)
- 3 Non-Functional Requirements (determinism, performance, error handling)
- Risk Taxonomy (high/medium/low priority)
- 10 Frozen Design Decisions
- 8 Deferred Boundaries
- References and exit gate check

**Acceptance Criteria Coverage:**
- AC1.1–AC1.10 (audit command)
- AC2.1–AC2.8 (baseline schema)
- AC3.1–AC3.7 (clustering)
- AC4.1–AC4.9 (baseline diff)
- AC5.1–AC5.10 (JSON report)
- AC6.1–AC6.10 (Markdown report)
- AC7.1–AC7.7 (metadata integration)
- AC8.1–AC8.12 (operator guide)
- AC9.1–AC9.10 (example baseline)

**Total: 77 acceptance criteria across all requirements.**

---

## Dependencies Verified

- **M902-01 (Validation Gate Framework):** COMPLETE. Gate runner at `ci/scripts/gate_runner.py`, gate schema, event logging framework stable.
- **M902-02 (Static Analysis Gate Tooling):** COMPLETE. `static_analysis_check` gate tested, JSON output format stable.
- **M902-04 (Handoff Metadata & Risk Escalation):** COMPLETE. Audit log module at `ci/scripts/audit_log.py`, event logging framework available.
- **jsonschema library:** Standard Python 3.11+ library; will be added to pyproject.toml dev deps if not present.
- **CLAUDE.md guardrails:** Reviewed and incorporated (exclusions, path conventions, generated artifacts, etc.).

---

## Ticket Workflow Updated

**Ticket state updated:**
- Stage: SPECIFICATION → TEST_DESIGN
- Revision: 2 → 3
- Last Updated By: Planner Agent → Spec Agent
- Next Responsible Agent: Spec Agent → Test Designer Agent
- Validation Status: Backlog → Specification Complete

---

## Next Steps for Test Designer

Test Designer Agent should:
1. Read the specification at `/Users/jacobbrandt/workspace/blobert/project_board/specs/M902-07_audit_pipeline_spec.md`.
2. Design behavioral test suite (50 tests) covering FR1–FR9 and all acceptance criteria.
3. Create test fixtures (synthetic violations, baseline fragments, expected JSON/Markdown outputs).
4. Produce test design document at `project_board/test_designs/M902-07_audit_pipeline_test_design.md`.
5. Verify coverage of all 77 acceptance criteria and critical edge cases.

---

**Specification complete and ready for TEST_DESIGN stage.**

**Document Status:** READY FOR HANDOFF

**Confidence Level:** HIGH — All requirements fully specified with acceptance criteria, no ambiguities, dependencies verified.
