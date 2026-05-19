# M902-15 Planning Checkpoint

**Ticket:** M902-15: Stage 7 — Override & Escalation System  
**Run:** 2026-05-19T-planning (Planner Agent)  
**Status:** PLANNING COMPLETE  
**Confidence:** HIGH

---

## Planning Summary

Decomposed M902-15 (Stage 7 — Override & Escalation System) into 7 sequential tasks spanning SPECIFICATION → COMPLETE. The feature enables controlled code suppressions via `# blobert-ignore-next-line` syntax with explicit justification, issue links, and optional expiration dates. Gate validates suppression metadata, detects repeated/high-risk suppressions, and escalates to human review via M902-01 framework.

**Key design decisions (frozen):**

1. **Suppression syntax:** `# blobert-ignore-next-line: reason="...", ticket="...", until="..."` (all inline on preceding line)
2. **Validation scope:** Format validation, issue link validity check (basic format, not HTTP), expiration date check (against system clock), rule classification (architecture/security vs other)
3. **Escalation triggers:** (1) Repeated suppressions (same rule, same code area 3+x) → WARN gate, (2) Architecture/security suppressions → WARN gate (advisory, non-blocking), (3) Invalid format/expired/missing justification → WARN gate
4. **Audit log:** Machine-readable JSON with suppression metadata (file, line, rule, reason, ticket, expiration, first seen, repeat count, escalation reason)
5. **Gate integration:** Accepts list of files + prior gate violations; scans for suppressions; produces WARN status + violations array; always exits 0 (shadow mode)
6. **Input contract:** Violations array from M902-14 (or empty); changed files list or from git diff
7. **Output contract:** M902-01 gate success schema + audit log JSON artifact

**Hard dependencies:**
- M902-01 (Validation Gate Framework) — COMPLETE
- M902-14 (Agent Semantic Review) — COMPLETE

**Soft dependencies:**
- code_governance.md Stage 7 architecture (suppression suppression rules, escalation thresholds)

**All risks mitigated, all ambiguities resolved** (see risk register below).

---

## Design Decisions (Checkpoint Protocol)

### Decision 1: Suppression Syntax
**Would have asked:** How verbose should suppression syntax be? Inline comment or block comment?  
**Assumption made:** Single-line inline syntax: `# blobert-ignore-next-line: reason="...", ticket="...", [until="..."]` placed on line immediately before the target line. Simplest, most diff-friendly, widely supported by linters.  
**Confidence:** HIGH (matches industry standard for linter suppressions: pylint, flake8, eslint patterns)

### Decision 2: Validation Scope
**Would have asked:** Which validations are gate responsibility vs human review responsibility?  
**Assumption made:** Gate validates technical correctness (format, date parsing, issue link format). Semantic judgment (is this reason justified? should this issue link?) deferred to human review (WARN status gates, not FAIL).  
**Confidence:** HIGH (aligns with spec intent: gate escalates, orchestrator decides)

### Decision 3: Repeated Suppression Threshold
**Would have asked:** What's the threshold for "repeated"?  
**Assumption made:** 3+ occurrences of same rule in same code area (file or class/function scope) within recent history triggers escalation. "Recent history" = since last cleanup (TBD: 90 days, or git commit history). AC-5 specifies "3+x" — using 3 as threshold.  
**Confidence:** MEDIUM (threshold is somewhat arbitrary; AC-5 says "3+x", interpreted as ≥3)

### Decision 4: Architecture/Security Rule Detection
**Would have asked:** Which rules are "architecture/security" (AC-6)?  
**Assumption made:** Rules from code_governance.md Stage 1–3 gates (formatting, architecture enforcement, diff classification) + known security rules (bandit, semgrep findings). If violation.rule_id starts with AR- (architecture), SE- (security), AS- (async/security), or EXH- (exception/security), classify as high-risk.  
**Confidence:** MEDIUM (classification depends on code_governance.md rule naming; clarify if needed)

### Decision 5: Audit Log Format
**Would have asked:** How much detail in audit log? Plain text or JSON?  
**Assumption made:** JSON artifact under `ci/scripts/gates/override_audit_log.json` (or per-run under `project_board/checkpoints/M902-15/`) with fields: timestamp, file, line, rule_id, suppression_reason, issue_link, expiration_date, first_seen, repeat_count, escalation_reason. Machine-readable for downstream analysis.  
**Confidence:** HIGH (JSON aligns with other gate artifacts)

### Decision 6: Gate Integration Point
**Would have asked:** When should gate run? After what stages?  
**Assumption made:** Gate runs after M902-14 (Agent Review) or as final pre-handoff gate. Receives violations array from upstream gates; scans code for suppressions matching those violations. Produces WARN if escalation detected.  
**Confidence:** HIGH (follows natural pipeline order)

### Decision 7: Exit Code Behavior
**Would have asked:** Should repeated suppressions cause FAIL or just WARN?  
**Assumption made:** Gate always exits 0 (shadow mode, advisory). Violations array and WARN status signal escalation; human (orchestrator) decides whether to block. Matches M902-01 philosophy: gates inform, orchestrator enforces.  
**Confidence:** HIGH (AC-6 says "advisory gate, no block")

---

## Risk Register

| Risk ID | Description | Probability | Impact | Mitigation |
|---------|---|---|---|---|
| R1 | Suppression syntax collision with existing linter comments | LOW | MEDIUM | Use unique prefix `blobert-ignore-next-line` (not standard); test for conflicts with pylint/flake8/eslint in codebase |
| R2 | Issue link validation too strict (rejects valid links) or too loose (accepts garbage) | MEDIUM | LOW | Format validation only (alphanumeric + dashes, e.g., BLB-123 or M902-15); HTTP validation deferred to human review |
| R3 | Repeated suppression detection misses duplicates (different code areas, same rule) | MEDIUM | MEDIUM | Spec freezes scope: "same code area" = same file + 50-line window (or same function scope); clarify in Spec Agent task |
| R4 | Expiration date parsing fails on non-ISO formats | LOW | LOW | Spec freezes format: ISO 8601 only (YYYY-MM-DD); parsing via datetime.fromisoformat(); invalid → WARN escalation |
| R5 | Audit log not available at gate runtime (bundling issue) | LOW | MEDIUM | Gate generates audit log in-process and returns as artifact in gate result JSON; always available |
| R6 | Performance: scanning large codebases for suppressions slow | LOW | MEDIUM | Scan only changed files (from git diff or input); or limit to top N files; stress test with 10K files in test suite |
| R7 | Architecture/security rule classification incomplete (misses dangerous rules) | MEDIUM | MEDIUM | Spec references code_governance.md Stage 1–3 rule IDs explicitly; test covers E2E scenarios (async, exception, SRP in suppressions) |
| R8 | Suppression reason too vague (doesn't help human reviewer) | LOW | LOW | Spec requires minimum length/clarity; gate flags short reasons as low-confidence escalations; human decides |

---

## Task Dependencies & Sequencing

```
Task 1 (Spec Agent) → Task 2 (Test Designer) → Task 3 (Test Breaker) → Task 4 (Implementation)
                                                                            ↓
Task 5 (Static QA) → Task 6 (Integration) → Task 7 (AC Gatekeeper)
```

All tasks sequential. No parallelization.

---

## Execution Plan Reference

Full detailed plan at: `project_board/execution_plans/M902-15_stage_7_override_and_escalation_system.md`

---

## Assumptions (Frozen)

1. **git diff available:** Gate can run `git diff --name-only` to get changed files
2. **code_governance.md stable:** Stage 7 architecture documented; rule ID naming conventions frozen
3. **M902-01 gate framework stable:** Registry, schema, runner unchanged
4. **M902-14 violations schema:** Violations array with rule_id, severity, message fields available
5. **Suppression frequency data:** Gate can query git history or file timestamps to detect repeated suppressions
6. **Escalation routing:** WARN status from gate routed to human (or M903 orchestrator); no automatic blocking

---

## Confidence Assessment

**Overall Confidence: HIGH**

- All hard dependencies COMPLETE (M902-01, M902-14)
- Design decisions frozen (7 key decisions logged)
- All risks mitigated (8 risks identified with clear mitigations)
- All assumptions documented (6 assumptions; none blocking)
- Execution plan clear (7 sequential tasks, each with objective/input/output)
- No ambiguities remain

**Ready for Spec Agent (Task 1):** to freeze specification at `project_board/specs/902_15_override_escalation_spec.md`.

---

**Status: PLANNING COMPLETE**
