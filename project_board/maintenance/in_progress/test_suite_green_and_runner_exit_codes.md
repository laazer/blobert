# TICKET: test_suite_green_and_runner_exit_codes

Title: Restore green test suites and harden the combined Godot + Python test runner (correct exit codes)

## Description

Some tests are currently failing locally or in automation; the project should treat **all** committed suites as the quality gate. In parallel, the canonical way to run tests must **exit non-zero** when anything errors or fails—no swallowed steps, no silent success when a phase broke.

**Godot:** `tests/run_tests.gd` already documents exit `0` / `1` based on `run_all()` failure counts; verify that engine crashes, unloadable suites, and `timeout` kills still surface as non-zero to the shell. Today **`ci/scripts/run_tests.sh`** runs only headless Godot and uses `timeout 120 godot --headless --import ... || true` with stderr discarded, which **masks import/reimport failures** and always continues into the test run—those choices should be revisited so real failures fail the script (or be narrowly scoped with documented exceptions).

**Python:** Asset pipeline tests live under `asset_generation/python/tests/` and are invoked by **`.lefthook/scripts/py-tests.sh`** (pre-push) via `pytest`; that path is **not** part of `ci/scripts/run_tests.sh`, so a “full test” habit can miss Python failures. Pytest already returns non-zero on failure when run directly; the gap is **orchestration** and ensuring one entry point runs both suites and aggregates exit status.

Deliver a single documented entry point (extend `ci/scripts/run_tests.sh` and/or add a thin repo-root wrapper that delegates to it—align with `CLAUDE.md` / contributor docs) that:

1. Runs Godot headless tests (`tests/run_tests.gd` with bounded `timeout`).
2. Runs `asset_generation/python` tests (`pytest` the same way as lefthook: `.venv` / `uv run` / `python3` fallback, or document required env).
3. Exits **non-zero** if either step fails or times out; does not use `|| true` (or equivalent) on critical steps without an explicit, logged bypass.

Then **fix or quarantine** every failing Godot and Python test so that entry point exits **0** on `main` (or document skipped tests with a tracked follow-up—default preference is fix in place).

## Acceptance Criteria

- `ci/scripts/run_tests.sh` (or the documented replacement) runs **both** Godot and Python suites and exits **non-zero** when Godot tests fail, Python tests fail, either process times out, or Godot fails during import/reimport—except where a **narrow, commented** exception is explicitly approved and still logs errors.
- Full run completes with **exit 0** on a clean tree (all tests passing).
- `CLAUDE.md` (or equivalent contributor doc) points at the updated command; lefthook / CI references stay consistent so pre-push and manual runs agree.
- Evidence attached to ticket closure: command used + last lines of output showing pass, or list of fixed test files.

## Dependencies

- None required

## Specification

Formal spec (requirements **TSGR-1**–**TSGR-8**, traceable to acceptance criteria):  
`project_board/specs/test_suite_green_and_runner_exit_codes_spec.md`

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_GENERALIST

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: `verify_tsgr_runner_contract.sh` + adversarial pytest module (`test_tsgr_runner_contract.py`: hollow-guard, cwd independence, process boundary, Python mirrors for TSGR-1/2/4/5/6); **6 failed, 8 passed** on 2026-04-05 (RED until runner/doc/hook implementation)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Implementation Generalist Agent

## Required Input Schema
```json
{
  "action": "implementation",
  "ticket_path": "project_board/maintenance/in_progress/test_suite_green_and_runner_exit_codes.md",
  "spec_path": "project_board/specs/test_suite_green_and_runner_exit_codes_spec.md"
}
```

## Status
Proceed

## Reason
Adversarial TSGR contract tests landed; implement `run_tests.sh` / hooks / `CLAUDE.md` per spec until static verifier + pytest module go green, then TSGR-7 suite fixes.
