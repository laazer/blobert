# M902-10 Specification Checkpoint

**Ticket:** M902-10 — Stage 1 Formatting & Re-stage Gate  
**Agent:** Spec Agent (Autonomous)  
**Timestamp:** 2026-05-18T (SPECIFICATION)  
**Revision:** 3  

---

## Specification Summary

**Task:** Produce complete functional and non-functional specification for Stage 1 Formatting & Re-stage Gate.

**Inputs:**
- Ticket M902-10: `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/10_stage_1_formatting_and_restage_gate.md`
- Planning checkpoint: `project_board/checkpoints/M902-10/2026-05-18T-planning.md` (all Q1–Q7 resolved)
- M902-01 Spec: `project_board/specs/902_01_gate_runner_spec.md` (gate framework)
- M902-09 Spec: `project_board/specs/902_09_diff_classification_gate_spec.md` (context; Stage 0 routing)
- Code Governance: `bot_vault/architecture/code_governance.md` (Stage 1 definition, exception handling rules)
- Workflow enforcement: `agent_context/agents/common_assets/workflow_enforcement_v1.md`
- Checkpoint protocol: `agent_context/agents/common_assets/checkpoint_protocol_v1.md`

**Output:**
- Spec file: `project_board/specs/902_10_formatting_gate_spec.md` (1.0 DRAFT)

**Status:** COMPLETE

---

## Specification Scope & Content

**8 Requirements:**
1. Gate Module and Registry Entry — Module implementation, run() function contract, registry entry
2. Output Contract and Schema — Success/failure schemas, message templates, field definitions
3. Formatter Invocation and Change Detection — Sequential formatter execution, file extension mapping, diff detection logic
4. Re-staging Logic — Git add workflow, user expectations, constraints
5. Error Handling and Graceful Degradation — Three error categories (unavailable, failed, git-failed), explicit exception propagation
6. Output Contract Validation and Schema Conformance — Validation checklist, JSON serializability
7. Non-Functional Requirements (NFR) — Performance targets (<5s), reliability, memory, testability, logging
8. Deferred Scope and Future Work (M903+) — Explicit out-of-scope features (CI/CD integration, lefthook, orchestration, formatter tuning)

**Acceptance Criteria (7 ACs):**
- AC1: Gate runs black, ruff format, prettier, gdformat → Req-03
- AC2: Detects if formatting changed → Req-03
- AC3: If formatting changed: message + re-stage + exit → Req-04
- AC4: If no changes: exit cleanly → Req-03
- AC5: Implemented as `ci/scripts/gates/formatting_check.py` → Req-01
- AC6: Tested with unformatted code samples → Req-03
- AC7: Exit behavior documented → Req-01 + Req-04

**Test Vectors (25+ examples):**
- 6 basic formatter tests (black, ruff, prettier, gdformat, black+ruff, all three)
- 8 mixed scenario tests (partial formatting, mixed languages, empty staging, large files, many files, config-only, binary+code, comment-only)
- 5 error/failure tests (formatter unavailable, timeout, formatter error, git unavailable, git add fails)
- 4 edge case tests (empty file, symlink, file deleted, long filename)
- 2 NFR tests (performance <5s, idempotency)

**Output Contract:**
- Success schema: status=PASS, gate=formatting_check, timestamp (ISO 8601), ticket_id, message, artifacts, duration_ms, formatting_changed (optional), formatters_applied (optional)
- Failure schema: status=FAIL, gate=formatting_check, violations array with (file, line, rule, message)
- Message templates frozen for all scenarios (formatting changed, no changes, formatter unavailable, errors)

**Risk Register:** 10 identified risks with mitigation strategies
**Dependencies:** M902-01 COMPLETE (provides gate framework); M902-09 COMPLETE (informational context)
**Assumptions:** 8 documented (formatter availability, git available, sequential safe, idempotency not tested, etc.)

---

## Decisions Made (Checkpoint Log)

### [M902-10] SPECIFICATION — Formatter invocation design
**Would have asked:** Should Stage 1 run formatters in parallel or sequentially? What about caching results?
**Assumption made:** Sequential execution (black → ruff format → prettier → gdformat) is the safe default per Q1 in planning checkpoint. Parallel execution and caching are deferred to M903 performance optimization. Requirement-03 explicitly locks sequential order.
**Confidence:** HIGH (frozen in planning.md Q1)

### [M902-10] SPECIFICATION — Re-staging and user workflow
**Would have asked:** Should gate auto-commit changes, or only re-stage?
**Assumption made:** Gate only re-stages via `git add`; user controls the final commit. This is safer (user has chance to review) and aligns with Q2 from planning. Requirement-04 documents this expectation.
**Confidence:** HIGH (frozen in planning.md Q2)

### [M902-10] SPECIFICATION — Graceful degradation on missing formatters
**Would have asked:** Should gate FAIL if a formatter is not installed, or skip it gracefully?
**Assumption made:** Skip with WARN-level violation (graceful degradation per Q5 in planning). If all formatters are unavailable, gate returns PASS with WARN violations; user understands nothing was formatted via message and violations array. Requirement-05 documents error handling categories.
**Confidence:** HIGH (frozen in planning.md Q5)

### [M902-10] SPECIFICATION — Change detection methodology
**Would have asked:** How to detect whether formatter changed files? Exact diff vs binary-safe diff?
**Assumption made:** Exact binary-safe diff using `git diff` or `diff` utility (all bytes count, whitespace counts). Q7 in planning froze this. Requirement-03 documents diff logic.
**Confidence:** HIGH (frozen in planning.md Q7)

### [M902-10] SPECIFICATION — Exception handling per code_governance.md
**Would have asked:** What exception handling patterns are required?
**Assumption made:** Per code_governance.md Section: Exception Handling Rules (CRITICAL SYSTEM RULE), no bare `except:` or silent swallowing. All exceptions must: (1) propagate, (2) transform, or (3) observe + propagate. Explicit recovery is allowed only when spec defines it (e.g., skip unavailable formatter). Requirement-05 codifies these rules.
**Confidence:** HIGH (governance document source of truth)

### [M902-10] SPECIFICATION — Out-of-scope features and M903 boundary
**Would have asked:** What belongs in this ticket vs M903 orchestration?
**Assumption made:** M902-10 is a standalone gate module; M903 is responsible for: CI/CD hook integration, lefthook wiring, orchestration logic (when to run Stage 1), user-facing UI. Requirement-08 explicitly documents deferred scope and prevents over-engineering.
**Confidence:** MEDIUM-HIGH (based on execution plan Task 1 description; alignment with 8-stage pipeline design)

### [M902-10] SPECIFICATION — Test vector coverage and depth
**Would have asked:** How many test vectors are "25+"?
**Assumption made:** Minimum 25 test vectors covering: 6 basic (one per formatter), 8 mixed scenarios, 5 error paths, 4 edge cases, 2 NFR (performance, idempotency). All vectors tied to requirements and acceptance criteria. This ensures high coverage without over-specifying (actual count may vary 25–35 depending on test designer's choices).
**Confidence:** MEDIUM (25 is ballpark; test designer may refine)

### [M902-10] SPECIFICATION — Performance and stress NFR
**Would have asked:** What are realistic performance targets for the gate?
**Assumption made:** <5 seconds for typical staging area (10–100 files, <10 MB total); <30s timeout per formatter; <500ms per diff comparison. These are targets, not hard limits. Requirement-07 defines NFR as soft targets (SLA-like) with relaxed test thresholds.
**Confidence:** MEDIUM (based on M902-09 gate performance; may refine after implementation)

---

## Clarifying Questions Resolved (Carry-over from Planning)

All clarifying questions from planning checkpoint (Q1–Q7) have been resolved and incorporated into the spec:

| Q# | Question | Resolution |
|---|----------|-----------|
| Q1 | Sequential vs parallel formatter execution? | Sequential (safe default per Req-03; parallel deferred to M903) |
| Q2 | Re-staging semantics? | Git add + message + exit (no auto-commit per Req-04) |
| Q3 | Staged-files-only vs working tree? | Staged-files-only via git index (per Req-01) |
| Q4 | Exceptions propagate? | Yes; no bare except (per Req-05 and code_governance.md) |
| Q5 | Missing formatter = FAIL or WARN? | WARN + skip (graceful degradation per Req-05) |
| Q6 | Idempotency testing required? | Out of scope; formatters assumed well-behaved (Req-08 deferred) |
| Q7 | Exact vs case-insensitive diff? | Exact binary-safe diff (per Req-03) |

**No new clarifying questions raised.** All scope boundaries are frozen.

---

## Specification Completeness Validation

Per workflow_enforcement_v1.md **Spec exit gate** requirement:

Before Test Designer Agent advances Stage to TEST_DESIGN, orchestrator must run:
```bash
python ci/scripts/spec_completeness_check.py project_board/specs/902_10_formatting_gate_spec.md --type generic
```

Expected result: **PASS** (all sections present, test vectors ≥25, output contract frozen, no ambiguities).

**Ticket type:** `generic` (not destructive, api, randomness, or load-open; standard gate spec).

---

## Specification Quality Checklist

- [x] 8 requirements, each with 1. Spec Summary, 2. Acceptance Criteria, 3. Risk & Ambiguity Analysis, 4. Clarifying Questions
- [x] All 7 ticket acceptance criteria mapped to requirements
- [x] 25+ test vectors with expected behavior (categorized: basic, mixed, error, edge, NFR)
- [x] Output contract and message templates frozen
- [x] All assumptions documented with confidence levels
- [x] All risks identified with mitigation strategies
- [x] Exception handling rules from code_governance.md incorporated
- [x] Deferred scope explicitly documented (prevents over-engineering)
- [x] No ambiguities or open questions remaining
- [x] Spec is testable by Test Designer and implementable by Implementation Agent
- [x] Spec does not include code or test implementations (declarative spec only)

**Specification Status: DRAFT v1.0 — READY FOR TEST_DESIGN**

---

## Next Steps

**Next Responsible Agent:** Test Designer Agent  
**Next Task:** TEST_DESIGN (Task 2 in execution plan)  
**Input:** `project_board/specs/902_10_formatting_gate_spec.md` (this spec)  
**Expected Output:** `tests/ci/test_formatting_check.py` with 25+ behavioral tests  
**Timeline:** Ready for immediate handoff

---

## Files Produced/Modified

- **Created:** `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_10_formatting_gate_spec.md` (1.0 DRAFT, 800+ lines)
- **Modified:** None (spec only)
- **Checkpoint log:** This file (`/Users/jacobbrandt/workspace/blobert/project_board/checkpoints/M902-10/2026-05-18T-specification.md`)

---

## Signature

- **Spec Agent (Autonomous)** — 2026-05-18 (SPECIFICATION complete)
- **Next: Test Designer Agent** — Proceed to TEST_DESIGN
