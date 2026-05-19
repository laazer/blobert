# M902-10 Planning Checkpoint

**Ticket:** M902-10 — Stage 1 Formatting & Re-stage Gate  
**Agent:** Planner Agent  
**Timestamp:** 2026-05-18T (PLANNING)  
**Revision:** 2  

---

## Planning Summary

**Task:** Decompose M902-10 (Stage 1 Formatting & Re-stage Gate) into a fully executable 7-task plan.

**Inputs:**
- M902-10 ticket: `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/10_stage_1_formatting_and_restage_gate.md`
- Workflow enforcement: `agent_context/agents/common_assets/workflow_enforcement_v1.md`
- Checkpoint protocol: `agent_context/agents/common_assets/checkpoint_protocol_v1.md`
- M902-01 (Gate framework): COMPLETE, provides gate runner + registry + schemas
- M902-09 (Diff classification): COMPLETE, provides Stage 0 context
- Code governance: `bot_vault/architecture/code_governance.md` Stage 1 spec
- Ticket template: `agent_context/agents/common_assets/ticket_template_v2.md`

**Context:**
- M902-10 is Task 2 of a 3-ticket "Formatting Gate" decomposition (M902-10 planning is this run)
- Part of 8-stage governance pipeline (Stage 0=diff classification, Stage 1=formatting, Stages 2-8 TBD)
- Implements auto-formatting (black, ruff format, prettier, gdformat) with re-staging on changes
- Non-blocking (shadow mode by default); exits early if no changes
- Depends on M902-01 gate framework; integrates into gate registry
- No blocking on M902-09 (diff classification); parallel work; diff classification recommends "formatting_and_stage_1" route only when needed

---

## Clarifying Questions & Checkpoint Decisions

| # | Question | Assumption | Confidence |
|---|----------|-----------|------------|
| Q1 | Should Stage 1 run formatters sequentially (Python→TS→Godot) or in parallel? | Sequential (safer for staging/re-staging workflows; avoids race conditions). Parallel is deferred to M903 performance optimization. | HIGH |
| Q2 | How does re-staging work? If formatting changes files, how are changes presented to user? | Re-stage via `git add`, commit message to stdout, exit with message. User sees "Re-staged formatted code; please review and commit" and must re-run git commit. Not integrated into lefthook (deferred to M903+). | HIGH |
| Q3 | Does formatting gate run outside of staging area (on working tree)? Or only on staged files? | Only on staged files via `git diff --cached` + `git stash`. Does not modify working tree or unstaged changes. Safest semantics. | HIGH |
| Q4 | What if formatter fails (e.g., black syntax error)? | Log error, return FAIL with violation (file+line+rule). Do not swallow exception. Exit 1 in blocking mode. | HIGH |
| Q5 | Should gate skip files if formatter not installed? Or FAIL? | Skip file + WARN in output (e.g., "gdformat not installed, skipping .gd files"). Not a hard FAIL. Degrades gracefully. | MEDIUM |
| Q6 | Should gate validate formatting is idempotent? (Re-run formatter on formatted output should yield no changes.) | No; that is formatter-specific testing (upstream tool responsibility). Gate assumes formatters are well-behaved. | HIGH |
| Q7 | Should diff-before/after detect changes case-insensitively? Or exact match only? | Exact match (whitespace counts). Use `diff --no-index -u` on temp files before/after formatting. | HIGH |

**Decisions Logged:**
- Q1: Sequential execution (safe default; M903+ can optimize)
- Q2: Git re-staging semantics frozen (git add → message → exit)
- Q3: Staged-files-only (safer)
- Q4: Exceptions propagate; no swallowing
- Q5: Skip + WARN if tool unavailable
- Q6: Idempotency is out of scope
- Q7: Exact diff matching (binary-safe)

---

## Dependency Analysis

**Hard Dependencies (must be COMPLETE before this ticket advances to SPECIFICATION):**
- M902-01 (Validation Gate Framework) — **COMPLETE** ✓
  - Gate runner (`ci/scripts/gate_runner.py`)
  - Gate registry (`ci/scripts/gate_registry.json`)
  - Success/failure schemas (`ci/scripts/gate_schemas/`)
  - M902-10 gate module must follow M902-01 pattern

**Soft Dependencies (informational; no blocking):**
- M902-09 (Diff Classification Gate) — **COMPLETE** ✓
  - Provides context: Stage 0 routes "formatting_and_stage_1" → recommend Stage 1 runs
  - M902-10 does not depend on M902-09 output; both run independently
- Code governance (`bot_vault/architecture/code_governance.md`)
  - Defines Stage 1 as "Formatting Layer"
  - Lists formatters: black, ruff format, prettier, gdformat

**No Blocking Issues.** All dependencies are COMPLETE or informational.

---

## Execution Plan Outline

**Stage Transitions:** PLANNING → SPECIFICATION → TEST_DESIGN → TEST_BREAK → IMPLEMENTATION_BACKEND → STATIC_QA → INTEGRATION → COMPLETE

**7 Tasks (Sequential):**

1. **SPECIFICATION** (Spec Agent) — Freeze Stage 1 gate requirements, acceptance criteria, test vectors
2. **TEST_DESIGN** (Test Designer) — Design behavioral test suite (25+ vectors)
3. **TEST_BREAK** (Test Breaker) — Design adversarial/stress test suite (20+ vectors)
4. **IMPLEMENTATION_BACKEND** (Implementation Agent) — Build `ci/scripts/gates/formatting_check.py` module + update registry
5. **STATIC_QA** (Static QA Agent) — Linting, code review, diff-cover verification
6. **INTEGRATION** (Integration Agent) — Wire gate into CI/CD hooks/automation tooling
7. **ACCEPTANCE_CRITERIA_GATEKEEPER** (AC Gatekeeper) — Validate all 7 acceptance criteria; move to done/

---

## Acceptance Criteria Mapping

**Ticket AC1:** Gate runs formatters (black, ruff format, prettier, gdformat)  
→ Task 4 (Implementation) + Task 1 (Spec must freeze formatter list)

**Ticket AC2:** Detects if formatting changed files  
→ Task 1 (Spec) + Task 4 (Implementation must compare before/after diffs)

**Ticket AC3:** If formatting changed: commit message, re-stage, exit  
→ Task 1 (Spec) + Task 4 (Implementation must call git add + print message)

**Ticket AC4:** If no changes: proceed (exit cleanly)  
→ Task 1 (Spec) + Task 4 (Implementation)

**Ticket AC5:** Implemented as `ci/scripts/gates/formatting_check.py`  
→ Task 4 (Implementation) must create at exact path

**Ticket AC6:** Tested with unformatted code samples  
→ Task 2 (Test Design) + Task 3 (Test Break)

**Ticket AC7:** Exit behavior documented  
→ Task 1 (Spec) + Task 6 (Integration) must document in README

---

## Risk Register

| Risk ID | Description | Severity | Mitigation |
|---------|-------------|----------|------------|
| R1 | Formatter not installed in test env | Medium | Skip file + WARN; don't FAIL. Test with mock fixtures. |
| R2 | Re-staging fails (git unavailable, permissions) | Medium | Log git error; return FAIL with context. Exception handling explicit. |
| R3 | Formatter hangs (infinite loop, large file) | Low-Med | Wrap formatter calls in `timeout` subprocess; set 30s default. |
| R4 | Diff-before/after comparison is expensive | Low | Use small staged files in tests; performance test in Task 1 (NFR). |
| R5 | Multiple formatters interfere (black vs ruff conflict) | Low | Run sequentially; each formatter fixes code for next stage. Idempotency test deferred. |
| R6 | Gate outputs wrong message when no changes detected | Low | Test vectors cover message text; AC7 documents message. |

---

## Assumptions Summary

1. **Formatter availability:** Tools may not be installed; gate degrades gracefully (skip + WARN).
2. **Git available:** Gate assumes `git` is on PATH and staging area is accessible.
3. **No parallel formatting:** Sequential execution is safe; parallel is deferred.
4. **Idempotency not tested:** Formatters are assumed well-behaved by upstream maintainers.
5. **No playground/sandbox files:** Gate assumes all staged files are production/test code; no temporary artifacts in staging.
6. **Stdout/stderr captured:** Formatters produce no interactive prompts; all output is captured and logged.
7. **Re-staging is idempotent:** Calling `git add` multiple times on same staged files is safe (it is).

---

## Next Actions

**Next Responsible Agent:** Spec Agent  
**Next Task:** Write `project_board/specs/902_10_formatting_gate_spec.md` with:
- 8 requirements (module, formatters, diff detection, re-staging, error handling, schema, NFR, deferred scope)
- 7 acceptance criteria (one per AC in ticket)
- 25+ test vectors (6 per formatter type + mixed scenarios + error cases)
- Output contract (gate success/failure schema)
- Exit behavior (early-exit semantics frozen)
- Risk analysis + clarifying questions resolved (logged above)

**Input needed:** None; all context gathered.

**Blocking issues:** None.

---

## Specification Readiness Checklist

- [x] All hard dependencies analyzed and confirmed COMPLETE
- [x] All clarifying questions resolved via checkpoint protocol
- [x] All assumptions logged with confidence levels
- [x] Risk register created
- [x] Acceptance criteria mapped to tasks
- [x] 7-task execution plan designed
- [x] Stage transitions defined
- [x] Scope is clear (Stage 1 formatting; not orchestration, not blocking enforcement)
- [x] No game/asset changes required
- [x] No destructive/randomness/load-open API concerns (generic ticket type)

**Ready for SPECIFICATION phase.**

---

## Execution Plan (High-Level)

See `project_board/execution_plans/M902-10_stage_1_formatting_gate.md` (will be created in parallel or by Spec Agent).

---

## Signature

- **Planner Agent** — 2026-05-18 (PLANNING complete)
- **Next: Spec Agent** — Create spec at `project_board/specs/902_10_formatting_gate_spec.md`
