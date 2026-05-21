# M902-24 Test Designer run

**Agent:** Test Designer Agent  
**Date:** 2026-05-21  
**Spec:** `project_board/specs/902_24_openapi_typescript_gen_spec.md`

## Deliverables

| File | Scenarios |
|------|-----------|
| `tests/web_frontend/test_sync_api_types_script.py` | T1 cache/skip-fetch, cache fallback stderr, T2 exit 3, T3 live fetch, T4 corrupt/2.0 cache, T5 tsc, T6 path keys, curl precheck |
| `asset_generation/web/frontend/src/api/syncApiTypes.test.ts` | T1, offline fallback, T2, T4, T6 banner + paths |

## Spec gaps (for Test Breaker / Spec)

- Exit **5** (`generation failed`) not covered in primary suite — execution plan Task 3 adversarial.
- `npm run sync-api-types` / `predev` propagation — Implementation Agent + optional npm script subprocess test.
- README prose — not tested (by design per test realism guardrail).

## Red-phase verification

Commands run from repo root; expect failures until `scripts/sync-api-types.sh` and generated artifacts exist.

```text
$ python -m pytest tests/web_frontend/test_sync_api_types_script.py -q --tb=line
FAILED ... test_script_exists_and_is_executable
AssertionError: missing sync script at .../asset_generation/web/frontend/scripts/sync-api-types.sh
... 9 failed, 0 passed (curl precheck skipped after script-missing guard)
```

```text
$ cd asset_generation/web/frontend && npm test -- src/api/syncApiTypes.test.ts
FAIL ... script exists and is executable — fs.existsSync(SYNC_SCRIPT) false
... 6 failed (exit 127: No such file or directory for sync-api-types.sh)
```
