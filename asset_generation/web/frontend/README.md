# Blobert Asset Editor — Frontend

Vite + React + TypeScript UI for the asset editor. API requests are proxied to the FastAPI backend on port 8000 (`/api` → `http://127.0.0.1:8000`).

## OpenAPI → TypeScript types (M902-24)

Generated types live in `src/api.types.ts`. **Do not edit that file by hand.**

### Sync after backend API changes

```bash
cd asset_generation/web/frontend
npm run sync-api-types
```

`npm run dev` runs the same sync first via the `predev` lifecycle hook.

### What the script does

1. Fetches `http://127.0.0.1:8000/openapi.json` (override with `BLOBERT_OPENAPI_URL`)
2. On success, updates `scripts/fixtures/openapi.cached.json`
3. If fetch fails, uses the committed cache and prints `using cached OpenAPI` to stderr
4. Runs `openapi-typescript@7.13.0` to regenerate `src/api.types.ts`

### Example: typed health check

```typescript
import type { paths } from "./api.types";
import { fetchHealth } from "./api/healthCheck";

type HealthGet = paths["/api/health"]["get"];
// Or use the helper:
const body = await fetchHealth();
```

### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `fetch failed` and `no cache` (exit 3) | Start the backend (`task editor` or `uvicorn` on :8000), run `npm run sync-api-types` once, commit the updated cache |
| `invalid cache` (exit 4) | Restore `scripts/fixtures/openapi.cached.json` from git or regenerate with backend up |
| `generation failed` (exit 5) | Run `npm install` in this directory; ensure `openapi-typescript@7.13.0` is installed |
| `curl not found` (exit 2) | Install curl (macOS/Linux dev environments) |
| Stale path keys in components | Re-run `npm run sync-api-types` after router changes |

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `BLOBERT_OPENAPI_URL` | `http://127.0.0.1:8000/openapi.json` | Live spec URL |
| `BLOBERT_SYNC_SKIP_FETCH` | unset | Set to `1` to use cache only (tests) |
| `VITE_STUDIO_LAYOUT` | `1` in `.env.development` / `task editor` | Set to `1` to enable the Studio shell (`StudioLayout`) instead of `ThreePanelLayout`. Restart Vite after changing. |

## Dual validation (M902-25)

Runtime validation on three pilot GET endpoints: Pydantic on the backend, Zod on the frontend.

| Endpoint | Backend model | Zod schema | Client helper |
|----------|---------------|------------|---------------|
| `GET /api/health` | `HealthResponse` | `HealthResponseSchema` | `getHealth()` |
| `GET /api/registry/model` | `ModelRegistryResponse` | `ModelRegistryResponseSchema` | `getModelRegistry()` |
| `GET /api/meta/enemies` | `MetaEnemiesResponse` | `MetaEnemiesResponseSchema` | `getMetaEnemies()` |

- Schemas: `src/schemas.ts`
- Validated client: `src/api-client.ts` (`ApiHttpError`, `ApiValidationError`)
- Drift fixtures: `scripts/fixtures/dual_validation/` (pytest + Vitest)

When you change a pilot response shape in Python, update the matching Zod schema in `schemas.ts` and add/adjust drift fixtures. Regenerate OpenAPI types with `npm run sync-api-types` when routes change.

`fetchModelRegistry()` and `fetchEnemyPreviewMeta()` in `src/api/client.ts` delegate to the validated client for these pilots.

## Commands

```bash
npm run dev          # Vite dev server (port 5173)
npm run build        # tsc + production bundle
npm test             # Vitest
npm run sync-api-types
```
