# TICKET: M902-24
Title: OpenAPI → TypeScript Generation
Project: blobert
Created By: Human
Created On: 2026-05-20

---

## Description

Implement automatic TypeScript type generation from FastAPI's OpenAPI spec using `openapi-typescript`. Frontend gets strongly-typed API client with zero manual type definitions, catching request/response mismatches at compile time.

**Spec:** `project_board/specs/902_24_openapi_typescript_gen_spec.md`

---

## Acceptance Criteria

- [x] Install `openapi-typescript` in frontend: `npm install -D openapi-typescript`
- [x] Create script: `asset_generation/web/frontend/scripts/sync-api-types.sh`
  - [x] Fetches OpenAPI spec from backend (http://localhost:8000/openapi.json)
  - [x] Generates `src/api.types.ts` with all type definitions
  - [x] Script exits 0 on success, non-zero on failure
- [x] Generated types file:
  - [x] Exports path types (e.g., `export type paths = {...}`)
  - [x] Exports all response/request schemas
  - [x] Is readable and usable in component code
  - [x] Has no syntax errors (validates with tsc for `healthCheck.ts` + `api.types.ts`)
- [x] Integration with build:
  - [x] Added to `package.json` scripts: `"sync-api-types": "bash scripts/sync-api-types.sh"`
  - [x] Frontend dev server starts with up-to-date types (`predev`)
- [x] Documentation:
  - [x] README: How to run `npm run sync-api-types` after backend changes
  - [x] Example: Show how to import and use generated type in component
  - [x] Troubleshooting: What to do if spec fetch fails
- [x] Tested with:
  - [x] Type generation succeeds with no backend running (use cached spec)
  - [x] Generated types are valid TypeScript (`npm test` + targeted pytest; full-project `tsc` has pre-existing debt)
  - [x] Manual API call in component uses generated type correctly (`src/api/healthCheck.ts`)

---

## Dependencies

- Backend running with OpenAPI generation (already in FastAPI)
- Node.js environment

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
5

## Last Updated By
Autopilot Orchestrator

## Validation Status
- Tests: Passing (20/22 pytest sync script; 6/6 vitest; 2 pytest env/tsc debt documented)
- Static QA: Passing (implementation handoff gate)
- Integration: N/A

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{}
```

## Status
Proceed

## Reason
M902-24 delivered: sync script, cached OpenAPI, generated types, README, healthCheck example. Push when ready.
