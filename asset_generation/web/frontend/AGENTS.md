# WEB FRONTEND — ASSET EDITOR KNOWLEDGE BASE

**App:** Blobert Asset Editor (Vite + React + TypeScript)  
**Port:** 5173 (dev); proxies `/api` → backend :8000

## Dual validation (runtime contract)

Pilot GET responses are parsed with **Zod** before use:

| File | Role |
|------|------|
| `src/schemas.ts` | Zod schemas (`.strict()` — every API field must be declared) |
| `src/api-client.ts` | `validatedFetch`, `getModelRegistry`, `getMetaEnemies`, `getHealth` |
| `src/api/client.ts` | Higher-level helpers; registry/meta pilots delegate to `api-client` |
| `src/types/index.ts` | Hand-written types for components (`ModelRegistryPayload`, etc.) |

**If the backend adds a field** (e.g. `build_options` on registry version rows): update `schemas.ts` and `types/index.ts`, add a drift fixture under `scripts/fixtures/dual_validation/`, extend `src/schemas.pilot.test.ts`. Regenerating `api.types.ts` alone is **not** sufficient.

See `README.md` → Dual validation (M902-25).

## OpenAPI types

`src/api.types.ts` is generated — `npm run sync-api-types`. Use for compile-time typing of non-pilot routes; keep in sync with backend via hook or manual sync after router changes.

## Commands

```bash
cd asset_generation/web/frontend
npm run dev
npm test -- --run
npx tsc --noEmit
npm run sync-api-types
```

## Agent role

Multi-agent workflow: **Implementation Frontend Agent** — `agent_context/agents/misc_agents/implementation_frontend_v1.md`.
