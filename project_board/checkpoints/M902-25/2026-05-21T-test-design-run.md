# M902-25 Test Designer run

**Agent:** Test Designer Agent  
**Date:** 2026-05-21  
**Spec:** `project_board/specs/902_25_pydantic_zod_validation_spec.md`

## Deliverables

| File | Requirement | Scenarios |
|------|-------------|-----------|
| `asset_generation/web/backend/tests/test_response_models_pilot.py` | Req 09 | 4 valid drift + 14 invalid drift; health/registry/meta TestClient (registry invalid → 500) |
| `asset_generation/web/frontend/src/schemas.pilot.test.ts` | Req 05, 09 | 4 valid + 14 invalid Zod `.parse` |
| `asset_generation/web/frontend/src/api-client.pilot.test.ts` | Req 06 | getHealth ok; getModelRegistry ApiValidationError; 503 ApiHttpError; getMetaEnemies fallback |
| `asset_generation/web/frontend/scripts/fixtures/dual_validation/*.json` | Req 09 | 4 valid + 14 invalid shared fixtures |

## Spec gaps (for Test Breaker)

- AnimatedBuildControlDef **valid** nested control fixture not yet in drift suite (only empty `{}` controls); add snapshot with int/select/bool arms.
- OpenAPI component schema assertions deferred to implementation QA (Req 10).
- Component integration tests (Req 07) not in this suite — Test Breaker or implementation.

## Traceability

| Spec AC | Test |
|---------|------|
| AC-02.3, AC-03.3, AC-04.2 | Drift parametrize both layers |
| AC-03.1, AC-04.1 | TestClient route tests with mocks |
| AC-06.1–06.3 | `api-client.pilot.test.ts` |
| AC-09.1 | 4 valid + 14 invalid fixture-driven cases |

## Red-phase verification

```text
$ cd asset_generation/web/frontend && npm test -- src/schemas.pilot.test.ts src/api-client.pilot.test.ts
 FAIL  src/api-client.pilot.test.ts
Error: Failed to load url ./api-client (resolved id: ./api-client) in .../src/api-client.pilot.test.ts. Does the file exist?
 FAIL  src/schemas.pilot.test.ts
Error: Failed to load url zod (resolved id: zod) in .../src/schemas.pilot.test.ts. Does the file exist?
 Test Files  2 failed (2)
      Tests  no tests
```

```text
$ cd asset_generation/web/backend && uv run python -m pytest tests/test_response_models_pilot.py -q --tb=line
FAILED tests/test_response_models_pilot.py::test_registry_route_rejects_invalid_manifest_before_http_200
assert 200 == 500
ERROR (18) — ModuleNotFoundError: No module named 'models' (models.responses not implemented)
4 passed, 1 failed, 18 errors
```
