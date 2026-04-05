# MAINT-TSGR — test_suite_green_and_runner_exit_codes

Run: 2026-04-05 — Implementation Generalist Agent

## Outcome

- **`ci/scripts/run_tests.sh`:** `set -e`; bounded `timeout 120 godot --headless --import` (no `2>/dev/null`, no `|| true`); `timeout 300` Godot `tests/run_tests.gd`; Python phase delegates to `.lefthook/scripts/py-tests.sh` (TSGR-3 DRY).
- **`.lefthook/scripts/godot-tests.sh`:** `timeout 120 "$GODOT" --import` + `timeout 300` test run; removed stderr discard and `|| true` (TSGR-2 / TSGR-6.2). `bin/godot` already injects `--headless`.
- **`CLAUDE.md`:** Canonical `timeout 300 ci/scripts/run_tests.sh`; Godot-only one-liner; bounded fail-fast import note (TSGR-6.1).

## Evidence (TSGR-8)

| ID | Command / note |
|----|----------------|
| TSGR-1..6 | `bash ci/scripts/verify_tsgr_runner_contract.sh` → `OK (MAINT-TSGR static contract).` |
| TSGR-1..6 | `cd asset_generation/python && uv run pytest tests/ci/test_tsgr_runner_contract.py -q` → `14 passed` |
| TSGR-7 | `timeout 300 ci/scripts/run_tests.sh` → exit `0`; Godot `=== ALL TESTS PASSED ===`; pytest `419 passed` |
| TSGR-2.4 | No import bypass. |

## Touched files

- `ci/scripts/run_tests.sh`
- `.lefthook/scripts/godot-tests.sh`
- `CLAUDE.md`

## Would have asked

- None.

## Assumption made

- Comment headers in `run_tests.sh` must not contain `py-tests`/`pytest` before the `run_tests.gd` line so static line-order checks stay valid.

## Confidence

High.

---

**Checkpoint:** Implementation complete; handoff to **AC Gatekeeper Agent** (Stage **STATIC_QA**, Revision **6**).
