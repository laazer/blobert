# M902-24: OpenAPI → TypeScript Generation

**Status:** PENDING  
**Target:** 2026-07-01

## Overview

Implement automatic TypeScript type generation from FastAPI's OpenAPI spec using `openapi-typescript`. Frontend gets strongly-typed API client with zero manual type definitions, catching request/response mismatches at compile time.

## Acceptance Criteria

- [ ] Install `openapi-typescript` in frontend: `npm install -D openapi-typescript`
- [ ] Create script: `asset_generation/web/frontend/scripts/sync-api-types.sh`
  - [ ] Fetches OpenAPI spec from backend (http://localhost:8000/openapi.json)
  - [ ] Generates `src/api.types.ts` with all type definitions
  - [ ] Script exits 0 on success, non-zero on failure
- [ ] Generated types file:
  - [ ] Exports path types (e.g., `export type /api/registry = {...}`)
  - [ ] Exports all response/request schemas
  - [ ] Is readable and usable in component code
  - [ ] Has no syntax errors (validates with tsc)
- [ ] Integration with build:
  - [ ] Added to `package.json` scripts: `"sync-api-types": "bash scripts/sync-api-types.sh"`
  - [ ] Frontend dev server starts with up-to-date types
- [ ] Documentation:
  - [ ] README: How to run `npm run sync-api-types` after backend changes
  - [ ] Example: Show how to import and use generated type in component
  - [ ] Troubleshooting: What to do if spec fetch fails
- [ ] Tested with:
  - [ ] Type generation succeeds with no backend running (use cached spec)
  - [ ] Generated types are valid TypeScript (tsc --noEmit passes)
  - [ ] Manual API call in component uses generated type correctly

## Implementation Notes

- Use default config: `openapi-typescript` detects OpenAPI 3.0 from spec
- Store generated `src/api.types.ts` in git (or .gitignore if preferring always-fresh)
- Handle case where backend is not running (fallback to last-known spec)
- Consider: auto-run during `npm install` or require manual sync

## Example Output

```typescript
// src/api.types.ts (generated)
export interface paths {
  '/api/registry': {
    get: {
      responses: {
        200: {
          content: {
            'application/json': {
              asset_id: string;
              name: string;
              created_at: string;
            };
          };
        };
      };
    };
  };
}
```

## Spec Reference

See: `project_board/specs/902_24_openapi_typescript_gen_spec.md`

## Dependencies

- Backend running with OpenAPI generation (already in FastAPI)
- Node.js environment

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_FRONTEND

## Revision
4

## Last Updated By
Test Breaker Agent

## Validation Status
- Spec: `project_board/specs/902_24_openapi_typescript_gen_spec.md` (Revision 1)
- Tests: `tests/web_frontend/test_sync_api_types_script.py`, `tests/web_frontend/test_sync_api_types_adversarial.py`, `asset_generation/web/frontend/src/api/syncApiTypes.test.ts` (red until implementation)
- Handoff: `project_board/checkpoints/M902-24/todos-latest.json`, `handoff-latest.yaml` (test_breaker → implementation)
- Adversarial log: `project_board/checkpoints/M902-24/2026-05-21T-test-break-run.md`

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Implementation Frontend Agent

## Required Input Schema
```json
{
  "spec_path": "project_board/specs/902_24_openapi_typescript_gen_spec.md",
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/24_openapi_typescript_generation.md",
  "transition": "test_break_to_implementation",
  "adversarial_tests": "tests/web_frontend/test_sync_api_types_adversarial.py"
}
```

## Status
Proceed

## Reason
Adversarial suite covers exit 5, empty cache, read-only output, `BLOBERT_SYNC_SKIP_FETCH` edges, and concurrent writes. Implement `scripts/sync-api-types.sh`, deps, cache, `api.types.ts`, and package scripts per spec Req 02–04.
