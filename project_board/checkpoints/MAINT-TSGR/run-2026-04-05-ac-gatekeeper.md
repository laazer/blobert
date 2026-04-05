# MAINT-TSGR / run-2026-04-05-ac-gatekeeper

- **Ticket:** `project_board/maintenance/done/test_suite_green_and_runner_exit_codes.md`
- **Agent:** Acceptance Criteria Gatekeeper
- **Date:** 2026-04-05

## Evidence run

- `bash ci/scripts/verify_tsgr_runner_contract.sh` → exit 0 (`verify_tsgr_runner_contract.sh: OK (MAINT-TSGR static contract).`)
- `timeout 300 ci/scripts/run_tests.sh` → exit 0; Godot `=== ALL TESTS PASSED ===`; Python `419 passed, 240 subtests passed in 2.63s`

## AC matrix

| AC | Gate |
|----|------|
| Combined Godot + Python; non-zero on failure/timeout/import mask | `run_tests.sh` + `verify_tsgr_runner_contract.sh` + spec TSGR-1..5 |
| Full run exit 0 clean tree | Re-run above |
| CLAUDE.md + lefthook consistent | Read `CLAUDE.md` Common Commands; `lefthook.yml` → `godot-tests.sh` / `py-tests.sh` |
| Closure evidence | This checkpoint + ticket `Validation Status` |

## Environment note

Full `run_tests.sh` was executed with an unrestricted shell (`godot` on PATH, existing `.venv`). Restricted sandboxes must supply the same toolchain or expect false failures.

## Outcome

Stage **COMPLETE**; ticket `git mv` to `project_board/maintenance/done/`.
