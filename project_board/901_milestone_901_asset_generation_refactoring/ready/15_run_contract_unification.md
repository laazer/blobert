# Run Contract Unification

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Unify command argument, environment, and output file contract used by CLI and API run routes. Today, `asset_generation/web/backend/routers/run.py` rebuilds behavior already encoded in Python entrypoints and generation scripts.

Target overlap:
- `asset_generation/web/backend/routers/run.py`
- `asset_generation/python/main.py`
- generator start-index and draft-subdir env behavior

## Acceptance Criteria

- [ ] Shared Python-side run contract module is introduced (command schema + env rules + output prediction).
- [ ] API run router delegates to shared contract module and removes duplicate `_build_command` / `_guess_output_file` logic.
- [ ] Run contract supports current commands: `animated`, `player`, `level`, `smart`, `stats`, `test`.
- [ ] `/api/run/stream` and `/api/run/complete` preserve current external behavior and response shape.
- [ ] Regression tests cover command parity and variant-index behavior.

## Dependencies

- Backend-Python Import Adapter

## Execution Plan

1. Extract run command contract into Python package module.
2. Refactor API run router to consume extracted contract API.
3. Preserve timeout and process-manager behavior at transport layer.
4. Add parity tests against current route behavior.
5. Validate with existing run route and python command tests.

## Notes

- Keep this ticket contract-focused; do not redesign process manager lifecycle.
