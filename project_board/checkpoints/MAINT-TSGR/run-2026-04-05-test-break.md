# MAINT-TSGR — test_suite_green_and_runner_exit_codes

Run: 2026-04-05 — Test Breaker Agent

## Outcome

- **Adversarial pytest extensions** in `asset_generation/python/tests/ci/test_tsgr_runner_contract.py`:
  - **Hollow-verifier guard:** `bash -n`, required source fragments (`_check_*`, `TSGR-2`, `set -u`).
  - **cwd independence:** same exit code and stderr from repo root vs arbitrary temp cwd (ROOT must not follow subprocess cwd).
  - **Process boundary:** on success, stdout must contain `OK (MAINT-TSGR static contract)`; on failure, stderr must contain `TSGR contract:` and `MAINT-TSGR`.
  - **Defense-in-depth mirrors** (bash verifier still authoritative; Python catches gutted verifier or drift): `run_tests.sh` / `godot-tests.sh` non-comment `--import` lines (TSGR-2); `run_tests.gd` lines timeout + no `|| true` (TSGR-4/5); `run_tests.sh` `set -e` (TSGR-4); Python phase + path context (TSGR-1); optional Godot-before-Python line order when Python phase exists (TSGR-1); TSGR-3 DRY delegate when inline `uv`/`.venv` appears; `CLAUDE.md` canonical path + pytest/asset_generation + fail-fast wording (TSGR-6).
- **`# CHECKPOINT` comments** in test module mark adversarial intent for reviewers.
- **Baseline (unchanged RED):** `pytest tests/ci/test_tsgr_runner_contract.py` → **6 failed, 8 passed** (2026-04-05, `.venv/bin/python -m pytest`).

## Spec ↔ adversarial matrix

| Dimension | Tests |
|-----------|--------|
| Mutation / hollow script | `test_TSGR_verifier_source_retains_required_probes`, `test_TSGR_verifier_bash_syntax_ok`, success stdout banner |
| Boundary / cwd | `test_TSGR_verifier_invocation_independent_of_subprocess_cwd` |
| Order dependency | `test_TSGR_when_python_phase_present_godot_before_python_line_order` |
| Duplicate TSGR checks | Python mirrors for TSGR-1/2/4/5/6 alongside `verify_tsgr_runner_contract.sh` |
| TSGR-4.3 (timeout kill) | Still not statically proven; integration/stub `timeout` remains a gap |

## Would have asked

- Whether to add a hermetic temp-tree test that copies `run_tests.sh` stubs — deferred (heavier, higher maintenance).

## Assumption made

- Duplicating selected grep rules in Python is acceptable maintenance cost for defense-in-depth until a single shared parser exists.

## Confidence

High for static adversarial coverage; medium for long-term duplication cost vs bash verifier.

---

**Checkpoint:** Test break complete; handoff to **Implementation Generalist Agent** (Stage **IMPLEMENTATION_GENERALIST**, Revision **5**).
