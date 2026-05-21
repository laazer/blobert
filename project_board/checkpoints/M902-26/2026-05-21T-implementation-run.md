# M902-26 Implementation Run (Backend)

## Delivered (Req 11)

- `asset_generation/web/backend/AGENTS.md` — **API contract tests (M902-26)** runbook: schema authority (live OpenAPI, committed cache, optional live server URL), steps when endpoints change, `pytest tests/api/ -q`, links to spec M902-24/25/26.

## Test evidence

```text
cd asset_generation/python && uv run pytest tests/api/ -q
........................................................................ [ 82%]
...............                                                          [100%]
87 passed in 1.25s
```

Full log: `project_board/checkpoints/M902-26/pytest-api-2026-05-21.txt`

## Linter evidence

```text
cd asset_generation/python && uv run --extra dev ruff check src tests main.py
All checks passed!
```

Log: `project_board/checkpoints/M902-26/ruff-impl-2026-05-21.txt`

## CI integration evidence (Req 10)

Contract tests under `asset_generation/python/tests/api/` are included in canonical Python CI because both entry points run **`pytest tests/`** from `asset_generation/python/` (parent of `tests/api/`).

| Entry | Path | Relevant lines |
|-------|------|----------------|
| `ci/scripts/run_tests.sh` | repo root | Line 21–22: `bash "$ROOT/.lefthook/scripts/py-tests.sh"` after Godot suite |
| `.lefthook/scripts/py-tests.sh` | `asset_generation/python` | `PYTEST_COV_ARGS=( tests/ -q ... )` — collects all of `tests/` including `tests/api/` |

No separate `tests/api/` glob is required; `tests/api/*.py` is discovered automatically.

## Known deviations / follow-ups

- Tier B routes still use anchor validation until full Pydantic `response_model` coverage (spec deferred boundary).
- Adversarial notes: optional SSE httpx hardening; `sse_starlette` event-loop bleed if many SSE tests share one session (see test-break checkpoint).

## AC matrix (implementation scope)

| Req | Status | Evidence |
|-----|--------|----------|
| 01–10 | Complete (prior agents) | 87 contract tests green |
| 11 | Complete | `backend/AGENTS.md` runbook section |
| 12 | Complete | No weakening of `tests/web/test_registry_api.py` |
