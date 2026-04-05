# MAINT-TSGR — test_suite_green_and_runner_exit_codes

Run: 2026-04-05 — Test Designer Agent

## Outcome

- **Static verifier:** `ci/scripts/verify_tsgr_runner_contract.sh` (executable). Encodes TSGR-1 (Godot then Python, path context), TSGR-2 (bounded import, no `|| true` / `2>/dev/null` on import lines; skips `#` comment false positives), TSGR-3 (DRY: no inline `.venv`/`uv` resolver without delegating to `py-tests.sh` or `ci/scripts/*.sh`), TSGR-4 (`set -e` + Godot test line under `timeout`), TSGR-5 (no `|| true` on `run_tests.gd` line), TSGR-6 (`CLAUDE.md`: `ci/scripts/run_tests.sh`, Python/pytest mention, fail-fast wording).
- **Pytest hook:** `asset_generation/python/tests/ci/test_tsgr_runner_contract.py` → runs the bash verifier from repo root (`test_TSGR_static_combined_runner_contract`).
- **Ticket:** Stage **TEST_BREAK**, Revision **4**, Next **Test Breaker Agent**.

## Spec ↔ verification map

| Spec ID | Verification |
|---------|----------------|
| TSGR-1.1–1.2 | `run_tests.sh` contains pytest or `py-tests.sh`, path context; Godot test line before Python line; `set -e` supports missing-pytest failure once shell invokes resolver |
| TSGR-2.1–2.3 | Import lines (non-comment): `timeout`, no `|| true`, no `2>/dev/null` |
| TSGR-3.1–3.3 | DRY guard on duplicate resolver; behavioral parity relies on implementation sourcing shared/`py-tests.sh` — adversarial cases for Test Breaker |
| TSGR-4.1–4.2 | `set -e` + no masking on Godot test line |
| TSGR-4.3 | **Gap:** `timeout` killing a child is not statically proven; recommend Test Breaker or integration harness with stub `godot`/`timeout` if needed |
| TSGR-5.1–5.3 | No `|| true` on `run_tests.gd` invocation |
| TSGR-6.1–6.3 | `CLAUDE.md` checks + `godot-tests.sh` same import/test-timeout rules as CI script |
| TSGR-7–8 | Not automated here (full green run + gatekeeper evidence) |

## Baseline (2026-04-05)

- `timeout 300 godot --headless -s tests/run_tests.gd` → exit **0**, `=== ALL TESTS PASSED ===` (headless RID leak messages unchanged).
- `verify_tsgr_runner_contract.sh` → exit **1**, **10** failed checks (expected until implementation).
- `pytest tests/ci/test_tsgr_runner_contract.py` → **fails** with same contract output (RED until MAINT-TSGR implementation).

## Assumptions

- Implementers may satisfy TSGR-3 by calling `.lefthook/scripts/py-tests.sh` or a new `ci/scripts/` helper that `py-tests.sh` also uses; verifier accepts `bash`/`source`/`.` to that helper.

**Confidence:** High

---

**Checkpoint:** Test design complete; handoff to Test Breaker Agent.
