# M902-24 Test Break Run

**Run id:** `2026-05-21T-test-break-run`  
**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/24_openapi_typescript_generation.md`  
**Stage:** TEST_BREAK → IMPLEMENTATION_FRONTEND  
**Agent:** Test Breaker Agent

---

## Outcome

Adversarial module `tests/web_frontend/test_sync_api_types_adversarial.py` added (12 cases) covering exit 5 generation failure, empty/whitespace cache, read-only output paths, `BLOBERT_SYNC_SKIP_FETCH` strictness, and concurrent output writes.

---

## Adversarial matrix

| Dimension | Class | Tests | Gap exposed |
|-----------|-------|-------|-------------|
| Error handling | `TestGenerationFailureExit5` | 3 | Fake `npx` shim, read-only dir/file → exit **5** + `generation failed` |
| Null & Empty | `TestEmptyCacheAdversarial` | 3 | Zero-byte, `{}`, whitespace-only cache → exit **4** |
| Assumption checks | `TestBlobertSyncSkipFetchEdgeCases` | 5 | Only `1` skips fetch; `true`/`0` edge cases |
| Concurrency | `TestConcurrentOutputWrites` | 1 | Parallel runs same output path |

---

## Pytest (adversarial module)

```text
$ uv run --project asset_generation/python pytest tests/web_frontend/test_sync_api_types_adversarial.py -v --tb=short
12 failed (sync-api-types.sh not implemented — bash exit 127)
```

Expected red until `asset_generation/web/frontend/scripts/sync-api-types.sh` lands.

---

## Gaps flagged for implementation

1. **Exit 5:** `openapi-typescript` failure and non-writable output must stderr `generation failed` and leave no usable output.
2. **Empty cache:** Zero-byte, `{}`, and whitespace-only files are **invalid cache** (exit **4**), not “no cache” (exit **3**).
3. **`BLOBERT_SYNC_SKIP_FETCH`:** Only exact `1` skips live fetch; `true` must still attempt fetch then cache fallback; `0` enables fetch.
4. **Skip + missing cache:** `BLOBERT_SYNC_SKIP_FETCH=1` without cache file → exit **3** (`no cache`), not **4**.
5. **Read-only output:** Cannot overwrite read-only file or write into read-only parent directory.
6. **Concurrency:** Two parallel runs to the same `BLOBERT_OPENAPI_OUTPUT` must both exit **0** with valid non-empty TS (atomic write).

---

## Implementation notes (Req 02 / execution plan Task 4)

- Prepend auto-generated banner before write; validate output non-empty after `openapi-typescript`.
- Use atomic cache/output writes (temp file + `mv`) for concurrent `predev` safety.
- Validate cache with `jq` or `python -c` JSON parse + `openapi` field `^3\.` before generation branch.
- `BLOBERT_SYNC_SKIP_FETCH` compare with `[ "$BLOBERT_SYNC_SKIP_FETCH" = "1" ]` only.
- Seed `scripts/fixtures/openapi.cached.json` on first green run.

Spec: `project_board/specs/902_24_openapi_typescript_gen_spec.md` (Failure Taxonomy, Req 02 env table).

---

### [M902-24] TEST_BREAK — stage naming

**Would have asked:** `IMPLEMENTATION_FRONTEND` vs `IMPLEMENTATION_GENERALIST`?

**Assumption made:** Ticket is asset editor frontend (`asset_generation/web/frontend/`); use `IMPLEMENTATION_FRONTEND` per workflow enum.

**Confidence:** High
