# M902-28 Implementation Run

**Date:** 2026-05-20  
**Agent:** Implementation Agent (Generalist) / Autopilot orchestrator

## Changes

- `lefthook.yml`: `pre-push.parallel: true` (was `false`)
- `lefthook.yml` header: parallel behavior, opt-out notes
- `CLAUDE.md`: Hooks / Pre-Push section documents parallel pre-commit/pre-push, `LEFTHOOK=0`, `LEFTHOOK_EXCLUDE`, sequential override
- `tests/ci/test_parallel_hook_execution_adversarial.py`: mutation test targets `parallel: true` baseline

## Validation

```text
python -m pytest tests/ci/test_parallel_hook_execution.py tests/ci/test_parallel_hook_execution_adversarial.py -q
30 passed in 3.57s

bash ci/scripts/verify_tsgr_runner_contract.sh
verify_tsgr_runner_contract.sh: OK (MAINT-TSGR static contract).
```

## Baseline timing (representative)

| Scenario | Notes |
|----------|--------|
| Pre-commit (parallel) | 7 commands; each skipped when glob has no staged match — typically sub-minute when only `.py` or only `.gd` staged |
| Pre-push sequential (before) | `godot-tests` then `py-tests` when both globs match — wall time ≈ sum of both suites |
| Pre-push parallel (after) | Overlap when both triggered — expected wall time ≈ max(godot, python), not sum |

Full wall-clock pre-push with both suites: measure locally via `LEFTHOOK_VERBOSE=1 git push` on a branch touching `.gd` and `asset_generation/python/**/*.py` (Integration/Human follow-up).

## Safety

- Godot hook writes under `.godot/`; Python hook writes `asset_generation/python/coverage.xml` — no shared path (T4/T5 tests).
