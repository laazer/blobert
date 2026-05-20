# M902-20 — Test Design Run

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/20_todo_validation_gates.md`

**Stage:** TEST_DESIGN → TEST_BREAK

**Spec:** `project_board/specs/902_20_todo_validation_spec.md`

**Tests:** `tests/ci/test_todo_validation_gate.py`

## Outcome

- Added 30+ behavioral test functions across T1–T7, attribution, discovery, `run()` contract, FAIL payload, path security, registry, and determinism.
- Fixtures use `todos-latest.json` under `project_board/checkpoints/<ticket_id>/` layout (via `tmp_path` + `chdir` or `checkpoints_dir` override on `run()`).
- No markdown prose assertions.

## Pytest collection (expected red)

```
ERROR collecting tests/ci/test_todo_validation_gate.py
...
from gates.todo_validation_check import run as gate_run
E   ModuleNotFoundError: No module named 'gates.todo_validation_check'
```

## Next

Test Breaker Agent — adversarial cases (fenced JSON, mtime fallback, wrong expected_agent).
