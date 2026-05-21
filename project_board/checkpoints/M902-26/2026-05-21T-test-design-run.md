# M902-26 — Test design run (2026-05-21)

**Agent:** Test Designer Agent  
**Stage:** TEST_DESIGN → TEST_BREAK

## Deliverables

| Artifact | Path |
|----------|------|
| Harness | `asset_generation/python/tests/api/openapi_contract.py` |
| Fixtures | `asset_generation/python/tests/api/conftest.py` |
| Health | `test_health_contract.py` |
| Meta | `test_meta_contract.py` |
| Files | `test_files_contract.py` |
| Registry | `test_registry_contract.py` |
| Run (JSON + SSE) | `test_run_contract.py` |
| Assets (JSON + binary) | `test_assets_contract.py` |
| Resolver unit | `test_openapi_contract_resolver.py` |
| Dev dep | `jsonschema>=4.23,<5` in `pyproject.toml` |

## Verification

```text
$ cd asset_generation/python && uv run pytest tests/api/ -q
.................................................................        [100%]
65 passed in 0.84s
```

## Spec traceability

- Req 01: harness + session `live_spec` / `OpenAPIContract.validate`
- Req 02: Tier A (3 pilot GETs) full schema; Tier B non-empty dict anchor
- Req 03: httpx ASGITransport; `python_root` monkeypatch; `mock_process_manager`
- Req 04–09: per-router modules aligned to endpoint freeze table
- Req 08: SSE error via HTTP; SSE happy via `done` event JSON shape parser test
- Req 10: `jsonschema` dev extra (implementation wires CI evidence)

## Notes for Test Breaker

- `_inline_all_refs` required for nested `$ref` in `MetaEnemiesResponse` / `ModelRegistryResponse`
- Default manifest has empty `player.versions`; use `registry_with_player_version` fixture
- DELETE enemy draft confirm text: `delete draft {family} {version_id}`
- DELETE player requires ≥2 slotted versions + prior PATCH active visual
