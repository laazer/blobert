# M902-11 Planning Checkpoint: Stage 3 Architecture Enforcement Gate

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/11_stage_3_architecture_enforcement_gate.md`  
**Stage:** PLANNING  
**Revision:** 1 → 2 (after plan completion)  
**Date:** 2026-05-19  
**Run ID:** 2026-05-19T-planning  

---

## Planning Summary

Decomposed M902-11 (Stage 3 Architecture Enforcement Gate) into a 7-task sequential execution plan. The feature implements structural architecture enforcement using 5 analysis tools (import-linter, eslint-plugin-boundaries, semgrep, jscpd, radon/lizard) aggregated into a single gate module conforming to M902-01 gate schema.

**Plan Status:** FROZEN. Ready for handoff to Spec Agent (Task 1).

---

## Key Decisions & Assumptions

### Q1: Should complexity warnings block or warn-only?
**Would have asked:** How should complexity violations be treated? Block (FAIL) or warn only (WARN)?  
**Assumption made:** Complexity violations are WARN-level per code_governance.md Stage 3 exit rules ("complexity violations → WARN or FAIL configurable"). Spec Agent will document as WARN-default; implementation can make configurable.  
**Confidence:** HIGH (code_governance.md is explicit; Stage 2 micro-quality uses wemake for early detection; Stage 3 focuses on structural, not micro, complexity).

### Q2: How should tool unavailability be handled?
**Would have asked:** If import-linter or other tools are not installed, should gate FAIL or gracefully exit?  
**Assumption made:** Graceful skip via exit code 0 with PASS + message "Tool <X> not available" (pattern from M902-02 static_analysis_check.py, M902-09 diff_classification.py). Tools are best-effort; tests will mock all tools to avoid external dependencies.  
**Confidence:** HIGH (established pattern; M902-02 references this).

### Q3: What is the duplication detection threshold?
**Would have asked:** jscpd has configurable thresholds (lines, tokens). What should blobert use?  
**Assumption made:** Baseline 8+ lines, cross-file per code_governance.md Stage 3 description ("Detects duplication clusters (8+ lines, cross-file)"). Defer tuning to M903+; spec documents baseline.  
**Confidence:** MEDIUM (configurable in jscpd; baseline reasonable; exact tuning deferred).

### Q4: Should async safety violations block (FAIL)?
**Would have asked:** code_governance.md lists "async safety violations → hard fail" in Stage 2 exit rules. Does Stage 3 enforce the same?  
**Assumption made:** Yes, async safety violations are HARD FAIL per code_governance.md Stage 3 exit rules: "async & concurrency safety" with "no blocking calls in async context, no unbounded task spawning, proper cancellation handling." Semgrep rules will detect these; failures → FAIL status.  
**Confidence:** HIGH (code_governance.md explicit).

### Q5: How should observability violations be treated?
**Would have asked:** code_governance.md lists observability rules (structured logging, correlation IDs, etc.). Should violations block or warn?  
**Assumption made:** Observability violations are WARN-level per code_governance.md Stage 3 "Observability Enforcement (NEW)" section. Rules documented for reference; initial implementation focus on SRP/dependency/circular/async as FAIL; observability as secondary WARN. Agent semantic review (Stage 6) handles detailed observability validation.  
**Confidence:** MEDIUM (code_governance.md lists rules but doesn't specify exit severity; WARN is conservative; can escalate to Stage 6 agent review).

### Q6: Tool timeout values?
**Would have asked:** Each tool has different performance characteristics. What timeouts should be applied?  
**Assumption made:** Reference M902-02 TOOL_TIMEOUTS dict (ruff 60s, mypy 120s, etc.). Apply same pattern: import-linter 60s, semgrep 120s, eslint 60s, jscpd 120s, radon/lizard 60s. Spec Agent documents in Requirement 06.  
**Confidence:** HIGH (M902-02 provides precedent; tool vendors recommend similar ranges).

### Q7: Should Spec Agent define exact semgrep rules?
**Would have asked:** Semgrep custom rules for SRP violations, circular imports, and data ownership are complex. Should spec enumerate exact rule IDs or defer to implementation?  
**Assumption made:** Spec Agent will document rule CATEGORIES and PATTERNS (e.g., "semgrep rules must detect: controller → repository direct imports; domain → infrastructure imports; service → HTTP handler calls"). Exact YAML rule definitions deferred to Implementation Agent with reference to code_governance.md patterns. Tests will encode expected detections.  
**Confidence:** MEDIUM (semgrep rule syntax is implementation detail; spec must freeze what violations are detected, not exact YAML).

---

## Resolved Ambiguities from Ticket

### AC1: Gate runs import-linter, eslint-plugin-boundaries, semgrep, jscpd, radon/lizard
**Resolved:** Plan includes Task 4 (Implementation) with tool orchestration code. Spec (Task 1) will freeze tool invocation patterns, argument lists, and timeout handling.

### AC2–AC6: Detection rules (SRP, dependency, cross-layer mutation, duplication, complexity)
**Resolved:** Spec (Task 1) will enumerate detection rules with reference to code_governance.md Stage 3 sections. Implementation (Task 4) will implement detection via tool output parsing and rule matching.

### AC7: Flags async safety violations
**Resolved:** Assumption Q4 above; semgrep rules will detect blocking I/O in async, unbounded spawning, improper cancellation.

### AC8: Implemented as `ci/scripts/gates/architecture_enforcement_check.py`
**Resolved:** Path confirmed in execution plan. Module structure matches M902-01 gate framework (run() function, gate schema output).

### AC9: Integrated into gate_registry.json
**Resolved:** Task 6 (Integration) will create/update registry entry with stage 3, blocking mode flags, description.

### AC10: Tested with violation vectors
**Resolved:** Tasks 2–3 (Test Design, Test Break) will include tests injecting SRP violations, circular imports, duplication clusters, complexity spikes, async safety violations. All mocked (no real code injected).

---

## No Blocking Issues

- M902-01 (Gate Framework) — COMPLETE
- M902-02 (Static Analysis Tools) — COMPLETE
- code_governance.md — READ and understood
- No child tickets or gating dependencies
- No external blockers

**Plan is unblocked and ready for execution.**

---

## Execution Plan Location

`project_board/execution_plans/M902-11_stage_3_architecture_enforcement_gate.md`

---

## Next Step

Advance ticket Stage to SPECIFICATION; increment Revision to 2; set Next Responsible Agent to Spec Agent; route to Task 1 (Specification freeze).

