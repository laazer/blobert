# M902-20 — Test Break Run

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/20_todo_validation_gates.md`

**Stage:** TEST_BREAK → IMPLEMENTATION_GENERALIST

**Spec:** `project_board/specs/902_20_todo_validation_spec.md`

**Tests:** `tests/ci/test_todo_validation_gate.py`, `tests/ci/test_todo_validation_gate_adversarial.py`

## Outcome

- Added `tests/ci/test_todo_validation_gate_adversarial.py` with 28 test functions (+ parametrized variants).
- Coverage matrix: attribution bypass (6), malformed artifacts (9+), snapshot merge/fallback (4), fenced JSON in md (5), path traversal (6+), combinatorial/order (3), timing_diagnostics (3).
- Suite remains red until `ci/scripts/gates/todo_validation_check.py` and registry entry exist.

## Pytest collection (verbatim, expected red)

```
ERROR collecting tests/ci/test_todo_validation_gate.py
...
from gates.todo_validation_check import run as gate_run
E   ModuleNotFoundError: No module named 'gates.todo_validation_check'

ERROR collecting tests/ci/test_todo_validation_gate_adversarial.py
...
from gates.todo_validation_check import run as gate_run
E   ModuleNotFoundError: No module named 'gates.todo_validation_check'
```

## Implementation handoff

1. Implement `validate_todos` + `run()` per spec Req 01–07.
2. Register `todo_validation_check` in `ci/scripts/gate_registry.json`.
3. Satisfy adversarial cases: fail-closed invalid `todos-latest` (no fallback), mtime `todos-*.json`, fenced JSON precedence, path rejection, optional `timing_diagnostics`.

## Next

Implementation Agent (Generalist) — CI gate module + registry.
