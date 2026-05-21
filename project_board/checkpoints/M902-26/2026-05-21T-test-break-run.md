# M902-26 — Test Break run (2026-05-21)

## Outcome

Adversarial suite added: `asset_generation/python/tests/api/test_api_contract_adversarial.py` (22 cases). Full `tests/api/` **87 passed** (`uv run pytest tests/api/ -q`).

## Gaps documented for Implementation

| Gap | Evidence | Notes |
|-----|----------|-------|
| SSE httpx + sse-starlette | Order-dependent failure on `test_run_stream_invalid_cmd_error_contract` when httpx SSE used earlier | Adversarial tests use `_run_stream` generator; consider migrating remaining httpx SSE tests |
| Harness extra-key path | `validate_response` rejects via jsonschema `additionalProperties` before explicit `unexpected top-level keys` branch | Both messages accepted in adversarial mutation test |
| Req 11 runbook | Still pending in backend `AGENTS.md` | Handoff to Implementation Agent |

## Adversarial coverage matrix

| Dimension | Tests |
|-----------|-------|
| Mutation / extra keys | `test_tier_a_extra_top_level_key_rejected_by_harness`, live Tier A GET trio |
| Cache drift | `test_live_openapi_path_keys_are_subset_of_cached`, symmetric cache-only guard |
| Malformed JSON | files PUT, registry load_existing/open POST |
| Unicode paths | files read/write, assets texture + GLB |
| SSE edges | parser malformed/empty/done/log; `_run_stream` log, busy, done |

## Checkpoint (judgment)

### [M902-26] TEST_BREAK — OpenAPI cache symmetry

**Would have asked:** Should cache-only paths fail CI or only live-not-in-cache?

**Assumption made:** Fail on both directions (strict path-set equality).

**Confidence:** Medium

### [M902-26] TEST_BREAK — SSE transport

**Would have asked:** Keep httpx integration tests for SSE or generator-only?

**Assumption made:** New adversarial SSE tests use `_run_stream`; mark httpx SSE as fragile in gaps table.

**Confidence:** High

## pytest evidence

```
87 passed in 1.29s
```
