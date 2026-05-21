# M902-27 Implementation Run

## Deliverables

- `.lefthook/scripts/api-contract-check.sh` — sync-api-types → `tsc --noEmit` → contract pytest; frozen banners; cache fallback warning; no backend auto-start
- `lefthook.yml` — `api-contract-check` on `asset_generation/web/backend/**/*.py`, `stage: commit`
- `CLAUDE.md` — API contract pre-commit bullets
- `asset_generation/web/backend/AGENTS.md` — M902-27 runbook table

## Test evidence

```text
uv run pytest tests/ci/test_api_contract_precommit_hook.py -q
26 passed in 25.45s

cd asset_generation/python && uv run pytest tests/api/ -q
87 passed in 1.23s
```

## Deferred

- Manual dry-run D1–D5 (`project_board/checkpoints/M902-27/<run-id>-dry-run.md`) — Static QA / Integration per spec Req 07
