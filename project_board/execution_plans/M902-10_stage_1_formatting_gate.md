# M902-10 Execution Plan: Stage 1 — Formatting & Re-stage Gate

**Project:** blobert  
**Milestone:** 902 — Agent Predictability Improvements  
**Ticket:** M902-10 — Stage 1 Formatting & Re-stage Gate  
**Created:** 2026-05-18  
**Planner Agent:** This plan  
**Status:** PLANNING COMPLETE → Ready for SPECIFICATION  

---

## Project Description

Implement Stage 1 of an 8-stage governance pipeline: auto-format staged code (Python, TypeScript, Godot) and re-stage if formatting was applied. If no changes, exit cleanly to Stage 2. Gate is non-blocking (shadow mode) and follows the M902-01 validation gate framework.

---

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | **SPECIFICATION:** Freeze Stage 1 gate functional + non-functional requirements, acceptance criteria, output contract, and 25+ test vectors | Spec Agent | Ticket M902-10 ACs; planning checkpoint (checkpoint_v1.md); M902-01 gate framework; M902-09 diff classification spec (for context); code_governance.md Stage 1 definition | `project_board/specs/902_10_formatting_gate_spec.md` (v1.0) with: (1) 8 requirements (module path, formatter tools, diff detection, re-staging, error handling, output schema, NFR, deferred scope); (2) 25+ test vectors (6 basic per-formatter + 8 mixed scenarios + 5 error cases + 4 edge cases + 2 NFR); (3) output contract (gate success/failure schema matching M902-01); (4) exit behavior (early-exit semantics when no changes); (5) acceptance criteria mapped to requirements; (6) risk analysis (formatter availability, git unavailability, timeout handling); (7) clarifying questions resolved | M902-01 (COMPLETE—provides gate framework); M902-09 (informational; diff classification context) | Spec is unambiguous and implementable; all 7 ticket ACs covered; test vectors cover all requirements; output schema is frozen; no open questions remain | Q1–Q7 resolved in planning checkpoint; assume sequential formatter execution (safe default); assume skip+WARN on missing tools (graceful degradation); assume re-staging uses `git add` + stdout message; see checkpoint for full assumption list |
| 2 | **TEST_DESIGN:** Design comprehensive behavioral test suite covering all requirements and all 25+ test vectors | Test Designer Agent | Spec from Task 1 (902_10_formatting_gate_spec.md); gate framework patterns from M902-01; pytest fixtures + git integration examples from M902-09 test_diff_classification_gate.py | `tests/ci/test_formatting_check.py` (600–700 LOC) with: (1) test module fixtures (real git staging area setup/teardown); (2) 6 per-formatter basic tests (black, ruff format, prettier, gdformat, black+ruff combined, prettier+gdformat combined); (3) 8+ mixed scenario tests (mixed formatters, mixed file types, some changed+some unchanged); (4) 5+ error/failure tests (formatter timeout, subprocess error, git unavailable); (5) 4+ edge case tests (empty files, binary files, symlinks, large files); (6) output contract tests (all schema fields present, types correct, routes match); (7) NFR tests (performance <5s, graceful degradation); (8) full test traceability (each test ID → AC from spec) | Task 1 (Spec must be complete first) | All 25+ test vectors implemented; each test is independently runnable; fixtures are deterministic (real git, not mocks); no external tool dependencies (mock subprocess where needed for error cases); traceability matrix complete; syntax validated via `python -m py_compile` | Formatters may not be installed (mock with subprocess.patch); git unavailable in some test envs (test with monkeypatch); performance sensitive to system load (use relaxed thresholds in tests); see checkpoint protocol for test design patterns |
| 3 | **TEST_BREAK:** Design adversarial and stress test suite covering mutations, boundary conditions, concurrency, and determinism | Test Breaker Agent | Spec + implementation (once Task 4 completes) from Task 1; behavioral tests from Task 2; checkpoint protocol adversarial patterns (from M902-09 test_break.md) | `tests/ci/test_formatting_check_adversarial.py` (400–500 LOC) with: (1) 12+ mutation tests (invert logic: "if changes found" → "if no changes", swap formatter order, omit git add, omit message); (2) 8+ boundary tests (exactly 0 changes, exactly 1 byte changed, max-size file, empty staging area); (3) 5+ stress tests (many staged files, many formatters active, rapid re-runs); (4) 4+ concurrency tests (parallel gate invocations, thread safety); (5) 4+ determinism tests (same input → same output, no flakiness on re-run); (6) 7+ exception handling tests (git command fails, formatter times out, permission denied on re-stage); (7) 6+ schema/type validation tests (output dict structure, field types, enum values) | Tasks 1–2 (Spec + behavioral tests); Task 4 (Implementation must exist for adversarial testing) | All 50+ adversarial tests written; 100% pass on clean implementation; tests catch code regressions (mutation tests); all exception paths validated; determinism verified across multiple runs; concurrency safety validated | See M902-09 test-break checkpoint for patterns; assume gate implementation follows M902-01 contract; assume formatters are deterministic; see checkpoint for test design patterns |
| 4 | **IMPLEMENTATION_BACKEND:** Build gate module that runs formatters, detects changes, re-stages if needed | Implementation Agent | Spec from Task 1 (902_10_formatting_gate_spec.md); test suite from Tasks 2–3; M902-01 gate framework + patterns; code_governance.md formatter list | `ci/scripts/gates/formatting_check.py` (250–350 LOC) with: (1) `run(inputs: dict) → dict` function matching gate framework signature; (2) formatter invocation logic (black → ruff format → prettier → gdformat in sequence); (3) diff-before/after detection using `git diff` on temp files before/after format; (4) if changes: `git add`, return PASS with message "Re-staged formatted code; please review and commit"; (5) if no changes: return PASS with message "Code is already formatted"; (6) exception handling explicit (no bare except; log + re-raise); (7) graceful degradation (skip + WARN if formatter tool not installed); (8) output contract conforming to M902-01 schema (status, gate, timestamp, message, classification, artifacts, duration_ms); plus `ci/scripts/gate_registry.json` updated with new entry for formatting_check gate | Tasks 1–3 (Spec must be frozen; tests must be designed) | Module is syntactically valid Python; all 25+ test vectors pass; all 50+ adversarial tests pass; output schema matches M902-01; no bare except clauses; git operations are safe (stash/unstash, no data loss); performance <5s; exception handling explicit | Formatters may not be installed (test graceful skip); git may not be available (test explicit error message); subprocess hangs (test timeout logic); see checkpoint for assumptions |
| 5 | **STATIC_QA:** Run linting, code review, diff-cover preflight to ensure code quality | Static QA Agent | Implementation from Task 4; existing linting rules in repo | Verification that: (1) ruff/flake8 pass on `ci/scripts/gates/formatting_check.py` (no import errors, no undefined names, no style violations); (2) diff-cover preflight passes (Python file coverage requirements met; run `bash ci/scripts/diff_cover_preflight.sh`); (3) code review findings logged (if any) to checkpoint; (4) no bare except clauses (automated check via semgrep or grep pattern); (5) git operations verified as safe (stash/unstash/add reviewed manually); (6) output contract spot-checked against M902-01 schema | Task 4 (Implementation must be complete and committed) | All linting passes; diff-cover preflight passes (or skip if no threshold set); no blocker-level code review findings; exception handling verified; git safety verified | Linting may flag stylistic issues (fix as needed); diff-cover may require additional test coverage (resolve with Task 2–3); see workflow_enforcement_v1 diff-cover section for skip conditions |
| 6 | **INTEGRATION:** Wire gate into CI/CD automation and document exit behavior | Integration Agent | Implementation + tests from Tasks 4–5; M902-01 gate runner; milestone README | (1) Verify gate is callable via gate runner: `python ci/scripts/gate_runner.py formatting_check --upstream-agent Implementation --downstream-agent Stage2 --ticket-id M902-10` exits 0 and produces valid JSON result; (2) create or update `project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md` with new "## Stage 1 Formatting Gate" section documenting: (a) what the gate does, (b) when it runs (recommended by diff classification for "formatting_and_stage_1" route), (c) example invocation, (d) what happens if changes are re-staged (user must review and re-commit), (e) link to spec; (3) verify gate registry entry is correct and module path resolves; (4) document deferred scope (no lefthook/CI/CD integration yet; that is M903+); (5) optional: create lightweight integration test in `tests/ci/test_gate_runner_formatting.py` (20–30 lines) that invokes gate via gate runner and validates result JSON schema | Tasks 4–5 (Implementation + static QA must be complete) | Gate callable and produces correct output; README section ≤50 lines, clear and actionable; registry entry valid; deferred scope documented; optional integration test passes | Registry may require manual editing (verify JSON syntax); README may need revision (review style + link validity); gate runner may be unavailable (should not happen; M902-01 is COMPLETE) |
| 7 | **ACCEPTANCE_CRITERIA_GATEKEEPER:** Validate all 7 ticket ACs are satisfied and move to done/ | AC Gatekeeper Agent | All deliverables from Tasks 1–6; ticket M902-10; acceptance criteria checklist | Verification document in checkpoint confirming: (1) AC1: Gate runs black, ruff format, prettier, gdformat ✓ (Task 4 implementation + Task 2 test vectors); (2) AC2: Detects if formatting changed ✓ (Task 4 diff logic); (3) AC3: If changes, commits message + re-stages + exits ✓ (Task 4 git add + message); (4) AC4: If no changes, exits cleanly ✓ (Task 4 no-op path); (5) AC5: Implemented as `ci/scripts/gates/formatting_check.py` ✓ (Task 4 exact path); (6) AC6: Tested with unformatted samples ✓ (Tasks 2–3 test vectors); (7) AC7: Exit behavior documented ✓ (Task 1 spec + Task 6 README). Update ticket: Stage → COMPLETE, move to `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/`, commit all changes, push to origin | All prior tasks (1–6) must be COMPLETE | All 7 ACs satisfied with evidence; all tests passing (25+ behavioral + 50+ adversarial); code review passed; diff-cover passed; gate callable and produces correct output; README updated; ticket moved to done/ and committed | Blocking issues: if any AC fails, set Stage → BLOCKED, document blocker in checkpoint, route to responsible agent for remediation |

---

## Stage Transitions

```
PLANNING (this run)
    ↓ (Planner outputs plan → Spec Agent takes over)
SPECIFICATION (Task 1, Spec Agent)
    ↓ (Spec frozen, ready for test design)
TEST_DESIGN (Task 2, Test Designer Agent)
    ↓ (Behavioral tests designed, ready for adversarial)
TEST_BREAK (Task 3, Test Breaker Agent)
    ↓ (All tests designed, ready for implementation)
IMPLEMENTATION_BACKEND (Task 4, Implementation Agent)
    ↓ (Code written, tests passing)
STATIC_QA (Task 5, Static QA Agent)
    ↓ (Linting + code review passed)
INTEGRATION (Task 6, Integration Agent)
    ↓ (Gate wired, docs updated)
ACCEPTANCE_CRITERIA_GATEKEEPER (Task 7, AC Gatekeeper)
    ↓
COMPLETE (move to done/)
```

---

## Dependencies & Critical Path

**Hard (blocking) dependencies:**
- **M902-01** (Validation Gate Framework) — Status: **COMPLETE** ✓
  - Provides: `gate_runner.py`, `gate_registry.json`, success/failure schemas
  - Unblocks: All tasks (gate module must follow M902-01 contract)

**Soft (informational) dependencies:**
- **M902-09** (Diff Classification Gate) — Status: **COMPLETE** ✓
  - Provides context: Stage 0 routes requests to Stage 1 (formatting)
  - Does not block: M902-10 is independent; both run separately
- **Code Governance** (`bot_vault/architecture/code_governance.md`)
  - Provides: Stage 1 definition + formatter list
  - Does not block: Informational only

**Critical path:** Task 1 (Spec) → Task 2 (Test Design) → Task 3 (Test Break) → Task 4 (Implementation) → Task 5 (Static QA) → Task 6 (Integration) → Task 7 (Acceptance)
- **Estimated duration:** ~4–5 agent runs (assuming 2–3 tasks per run; see M902-09 for reference: COMPLETE in 8 runs over 2026-05-18)
- **No parallel work possible** within single ticket (sequentially dependent)

---

## Acceptance Criteria Traceability

| Ticket AC | Task(s) | Verification |
|-----------|---------|--------------|
| AC1: Gate runs black, ruff format, prettier, gdformat on staged files | Tasks 1, 4 | Implementation lists formatters in sequence; tests verify each formatter invoked |
| AC2: Detects if formatting changed files | Tasks 1, 4 | Diff logic implemented; test vectors cover changed/unchanged cases |
| AC3: If formatting changed: message → re-stage → exit | Tasks 1, 4 | Git add + message logic implemented; tests verify behavior |
| AC4: If no changes: exit to Stage 2 | Tasks 1, 4 | No-op path tested; message reflects "already formatted" |
| AC5: Implemented as `ci/scripts/gates/formatting_check.py` | Task 4 | Module created at exact path; imports as Python module |
| AC6: Tested with unformatted code samples | Tasks 2, 3 | Test vectors include unformatted examples per formatter type |
| AC7: Exit behavior documented | Tasks 1, 6 | Spec (Task 1) + README section (Task 6) document early-exit semantics |

---

## Risk Register

| Risk ID | Description | Severity | Mitigation Strategy | Task(s) |
|---------|-------------|----------|---------------------|---------|
| R1 | Formatter not installed in test environment | Medium | Spec (Task 1): skip + WARN on missing tools. Tests (Task 2): mock subprocess. Implementation (Task 4): graceful degradation. | 1, 2, 4 |
| R2 | Git unavailable or staging area inaccessible | Medium | Spec (Task 1): define error behavior. Implementation (Task 4): catch OSError, log, return FAIL. Tests (Task 2–3): mock git failures. | 1, 2, 3, 4 |
| R3 | Formatter hangs (infinite loop, large file) | Low-Medium | Spec (Task 1): require timeout. Implementation (Task 4): subprocess timeout=30s default. Tests (Task 3): stress test large files. | 1, 3, 4 |
| R4 | Diff-before/after comparison is expensive | Low | Spec (Task 1): define performance target (<5s). Implementation (Task 4): use efficient diff. Tests (Task 3): performance test. | 1, 3, 4 |
| R5 | Multiple formatters conflict (black vs ruff) | Low | Spec (Task 1): assume formatters compose correctly. Implementation (Task 4): run sequentially. Tests (Task 3): mutation test formatter order. | 1, 3, 4 |
| R6 | Output message unclear or misleading | Low | Spec (Task 1): freeze message templates. Implementation (Task 4): match spec exactly. Tests (Task 2): assert message text. | 1, 2, 4 |

---

## Assumptions

1. **Formatter availability:** Tools may not be installed; gate gracefully skips + warns (not FAIL).
2. **Git available:** Gate assumes `git` is on PATH; errors are logged + propagated (not swallowed).
3. **Sequential execution safe:** Running formatters in sequence (black → ruff format → prettier → gdformat) is safe; each formatter fixes code for the next stage.
4. **Idempotency not tested:** Formatters are assumed well-behaved by upstream maintainers; gate does not validate idempotent output.
5. **No playground/sandbox artifacts:** All staged files are production/test code; no temporary artifacts interfere with formatting.
6. **Subprocess non-interactive:** Formatters produce no interactive prompts; all output is captured and logged.
7. **Re-staging idempotent:** Calling `git add` multiple times on same staged files is safe (it is).
8. **Exceptions must propagate:** No bare except clauses; all errors logged + re-raised (per CLAUDE.md).

---

## Success Criteria Summary

**For Plan Approval:**
- [x] All 7 tasks are independent, sequential, and unambiguous
- [x] All hard dependencies are satisfied (M902-01 COMPLETE)
- [x] All acceptance criteria are mapped to tasks
- [x] All risks are identified and mitigation strategies defined
- [x] All assumptions are logged
- [x] No blocking issues or ambiguities remain
- [x] Plan is ready for execution by Spec Agent (Task 1)

---

## Next Steps

**Next Responsible Agent:** Spec Agent  
**Next Task:** Task 1 — SPECIFICATION  
**Input:** This execution plan + planning checkpoint  
**Output Expected:** `project_board/specs/902_10_formatting_gate_spec.md` (v1.0, DRAFT)  
**Timeline:** Ready for immediate execution

---

## Reference Files

- Ticket: `/Users/jacobbrandt/workspace/blobert/project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/10_stage_1_formatting_and_restage_gate.md`
- Planning Checkpoint: `/Users/jacobbrandt/workspace/blobert/project_board/checkpoints/M902-10/2026-05-18T-planning.md`
- M902-01 Spec: `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_01_gate_runner_spec.md`
- M902-09 Spec: `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_09_diff_classification_gate_spec.md`
- M902-09 Planning: `/Users/jacobbrandt/workspace/blobert/project_board/checkpoints/M902-09/2026-05-18T-planning.md`
- Code Governance: `/Users/jacobbrandt/workspace/blobert/bot_vault/architecture/code_governance.md`
- Workflow Enforcement: `/Users/jacobbrandt/workspace/blobert/agent_context/agents/common_assets/workflow_enforcement_v1.md`
- Checkpoint Protocol: `/Users/jacobbrandt/workspace/blobert/agent_context/agents/common_assets/checkpoint_protocol_v1.md`
