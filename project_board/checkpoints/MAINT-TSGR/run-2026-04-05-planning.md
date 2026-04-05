# MAINT-TSGR — test_suite_green_and_runner_exit_codes

Run started 2026-04-05 (autopilot maintenance backlog).

## Execution Plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author a formal specification for the unified test runner, exit-code contract, and documentation alignment | Spec Agent | Maintenance ticket AC; `ci/scripts/run_tests.sh`; `.lefthook/scripts/py-tests.sh`; `tests/run_tests.gd` exit semantics; `CLAUDE.md` Common Commands | `project_board/specs/test_suite_green_and_runner_exit_codes_spec.md` (or project-standard spec path/name) with requirement IDs mapping to each AC | — | Spec defines: (a) canonical entry point(s) and whether a repo-root wrapper is required; (b) Godot bounded `--import` / reimport behavior without masking failures—no silent `|| true` unless spec documents a narrow exception with logging; (c) stderr/stdout policy for import and test phases; (d) Python phase invocation order parity with `.lefthook/scripts/py-tests.sh` (`.venv` → `uv run --extra dev` → `python3` + clear failure when pytest missing); (e) aggregated exit status when either phase fails or `timeout` kills a step; (f) how Godot engine crash vs test assertion failure surfaces to the shell; (g) policy for fixing vs quarantining failing tests with follow-up tracking | Import can hang (LEARNINGS); spec must keep bounded `timeout` and document trade-offs. Shell-level automated tests may be limited—spec should state verification method (commands + expected exit codes). |
| 2 | Design behavioral / integration verification mapped to spec requirement IDs | Test Designer Agent | Approved spec from task 1 | Test plan and any new tests the repo can host (e.g. Godot `tests/` cases for game logic failures, `asset_generation/python/tests/` additions, or documented gatekeeper command matrix if shell-only) | 1 | Every spec ID that demands observable behavior has a listed verification path; pre-implementation run shows expected failures/red state where TDD applies | Runner orchestration may be verified only via scripted CI commands—avoid brittle full-Godot crash tests unless already a project pattern. |
| 3 | Adversarial review of the test design | Test Breaker Agent | Spec + test design from tasks 1–2 | Gap list and strengthened cases where justified | 1, 2 | Blind spots documented and either closed with new cases or explicitly accepted with rationale | — |
| 4 | Implement runner changes, doc updates, and make all committed suites green | Implementation Generalist Agent | Spec, finalized tests | Updated `ci/scripts/run_tests.sh` (and wrapper if spec requires); DRY or delegated call to shared Python test logic if spec mandates; `CLAUDE.md` and any CI/lefthook references consistent; failing Godot/Python tests fixed or quarantined per spec | 1–3 (implement after red tests exist where TDD applies) | `timeout 300` (or spec-defined bounds) on full canonical command exits **0** on clean tree; non-zero when a phase fails, times out, or import/reimport fails per spec; no unapproved swallowing of errors | CI environment may lack `uv` or `.venv`—spec’s fallback path must be implementable locally and in CI. |
| 5 | Static QA (lint/shell conventions per project) | Static QA Agent | Implementation from task 4 | Clean static pass or documented waivers | 4 | Project static checks pass where applicable | — |
| 6 | Integration validation and evidence for closure | Acceptance Criteria Gatekeeper Agent (or Human if policy requires) | Green implementation | Ticket closure evidence: exact command(s), tail of output showing pass, list of touched test files | 4–5 | AC matrix satisfied; Validation Status and COMPLETE handoff per workflow | Full suite runtime; flaky tests. |

### [MAINT-TSGR] Planning — import failure vs hang

**Would have asked:** Should a failing `--import` always abort before tests, or should the spec allow a documented bypass when import is flaky?

**Assumption made:** Default is fail-fast on import/reimport failure; any bypass is narrow, commented, and still logs errors—Spec Agent encodes this explicitly.

**Confidence:** High

### [MAINT-TSGR] Planning — single source for Python invocation

**Would have asked:** Should `run_tests.sh` source/call `.lefthook/scripts/py-tests.sh` or should shared logic move to a neutral path?

**Assumption made:** Spec chooses one approach that eliminates drift between pre-push and CI; Implementation follows the spec (prefer one callable script or extracted function to avoid duplicate resolution logic).

**Confidence:** Medium

---

**Checkpoint:** Planning complete; ticket advanced to SPECIFICATION, Revision 2, Next Spec Agent.
