# MAINT-EMSI — Acceptance Criteria Gatekeeper (2026-04-05)

**Ticket:** `project_board/maintenance/done/enemy_model_scale_input.md`  
**Run:** `run-2026-04-05-ac-gatekeeper`

## Evidence executed

- `cd asset_generation/python && uv run pytest tests/enemies/test_enemy_model_scale_input.py -q` → 19 passed, 19 subtests passed
- `cd asset_generation/python && uv run pytest tests/ -q` → 405 passed, 240 subtests passed
- `timeout 300 ci/scripts/run_tests.sh` → exit 0, `=== ALL TESTS PASSED ===` (RID leak warnings unchanged)

## AC matrix

| AC | Evidence |
|----|----------|
| `create_model` accepts scale; default preserves behavior | EMSI-1 tests + EMSI-3.1 parity (omit vs `scale=1.0`) |
| All `base_models/` archetypes honor contract | EMSI-3.1/3.2 for `insectoid`, `blob`, `humanoid` |
| Unit tests: default + non-1.0 without full Blender render | Mocked primitive kwargs; EMSI-3.2, 3.2b |
| `run_tests.sh` / Python suite passes | Full `tests/` + `run_tests.sh` |

## Actions

- WORKFLOW STATE: Stage `COMPLETE`, Revision 7, Validation Status AC summary + re-verify commands
- NEXT ACTION: Human, Proceed
- `git mv` `in_progress/enemy_model_scale_input.md` → `maintenance/done/enemy_model_scale_input.md`

## Outcome

COMPLETE
