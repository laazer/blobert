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
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: **AC Gatekeeper 2026-04-05:** `bash ci/scripts/verify_tsgr_runner_contract.sh` → exit 0 (TSGR-1..6 static contract). `timeout 300 ci/scripts/run_tests.sh` → exit 0; Godot ends with `=== ALL TESTS PASSED ===`; Python phase **419 passed** via `.lefthook/scripts/py-tests.sh` (tail: `419 passed, 240 subtests passed`). Prior handoff: `uv run pytest tests/ci/test_tsgr_runner_contract.py -q` → **14 passed**. **TSGR-2.4 bypass:** none. **Environment:** full runner expects `godot` on PATH (CLAUDE.md / direnv `bin/godot`) and a working `asset_generation/python` pytest environment; stripped sandboxes without those tools are not equivalent to CI/local—run outside restricted automation or match PATH/venv.
- Static QA: `ci/scripts/run_tests.sh`: `set -e`; `timeout 120 godot --headless --import` then `timeout 300 godot --headless -s tests/run_tests.gd`; no `|| true` / stderr discard on import; Python calls `bash "$ROOT/.lefthook/scripts/py-tests.sh"` (TSGR-3 DRY). `lefthook.yml` pre-push `godot-tests` / `py-tests` invoke `.lefthook/scripts/godot-tests.sh` and `py-tests.sh` with matching bounded import + test timeouts. `CLAUDE.md` Common Commands names `timeout 300 ci/scripts/run_tests.sh` as canonical full suite.
- Integration: Same evidence as Tests; no additional manual AC.

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "action": "ticket_complete",
  "ticket_path": "project_board/maintenance/done/test_suite_green_and_runner_exit_codes.md",
  "spec_path": "project_board/specs/test_suite_green_and_runner_exit_codes_spec.md",
  "notes": "Implementation changed files listed in MAINT-TSGR implementation checkpoint; optional push/merge per team process."
}
```

## Status
Complete

## Reason
All acceptance criteria have objective coverage: combined runner + non-zero contract (`verify_tsgr_runner_contract.sh` + `run_tests.sh` source), full suite green (re-run exit 0), CLAUDE.md/lefthook/CI alignment verified, closure evidence and fixed-artifact trail in checkpoints/spec (TSGR-8). Stage COMPLETE; ticket moved to `maintenance/done/`.
