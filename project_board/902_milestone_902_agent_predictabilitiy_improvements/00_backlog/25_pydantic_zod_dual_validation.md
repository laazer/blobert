# M902-25: Pydantic + Zod Dual Validation

**Status:** PENDING  
**Target:** 2026-07-08

## Overview

Implement dual runtime validation: backend validates responses with Pydantic, frontend validates with Zod. Catches bad data at both boundaries before it reaches application logic. 100% runtime coverage.

## Acceptance Criteria

### Backend (Pydantic)

- [ ] All API response types use Pydantic models
  - [ ] Audit existing endpoints in `asset_generation/web/backend/routers/`
  - [ ] Convert dict returns to Pydantic BaseModel responses
  - [ ] Use `response_model` in FastAPI routes: `@app.get("/registry", response_model=AssetRegistry)`
- [ ] Pydantic models have:
  - [ ] Type annotations for all fields
  - [ ] Field validators where needed (e.g., uuid format, length constraints)
  - [ ] Docstrings describing each field
- [ ] Tested: Return a Pydantic model, FastAPI serializes it correctly
- [ ] Error handling: Invalid data raises Pydantic ValidationError (FastAPI converts to 422)

### Frontend (Zod)

- [ ] Install Zod: `npm install zod`
- [ ] Create `asset_generation/web/frontend/src/schemas.ts`:
  - [ ] Define Zod schemas matching backend Pydantic models
  - [ ] Export both schema and inferred type: `export type AssetRegistry = z.infer<typeof AssetRegistrySchema>`
- [ ] Create API client wrapper (`src/api-client.ts`):
  - [ ] Fetch function validates response with Zod
  - [ ] Returns typed data or throws validation error
  - [ ] Example:
    ```typescript
    export async function getRegistry() {
      const response = await fetch('/api/registry');
      const data = AssetRegistrySchema.parse(await response.json());
      return data; // type: AssetRegistry
    }
    ```
- [ ] Integrate into components:
  - [ ] Replace direct fetch calls with validated API client
  - [ ] Components receive only validated data
- [ ] Error handling:
  - [ ] Zod parse errors caught and logged
  - [ ] User sees helpful error message (not raw validation output)

### Synchronization

- [ ] Process for keeping Pydantic and Zod in sync:
  - [ ] Documentation: When backend model changes, update Zod schema
  - [ ] Optional: Script to auto-generate Zod from Pydantic (deferred to later ticket if complex)
  - [ ] Until then: manual sync with tests to catch drift
- [ ] Tested with 3+ endpoints: models match, validation passes on valid data, fails on invalid data

## Implementation Notes

- Pydantic models are source of truth on backend
- Zod schemas manually mirror Pydantic (no code generation yet)
- Validation happens at API boundary (request in, response out)
- Both use same type language (JSON primitives + constraints)

## Example: Registry Endpoint

**Backend (Pydantic):**
```python
from pydantic import BaseModel, Field
from datetime import datetime

class AssetRegistry(BaseModel):
    asset_id: str = Field(..., description="UUID")
    name: str = Field(..., min_length=1, max_length=255)
    created_at: datetime

@router.get("/registry", response_model=AssetRegistry)
def get_registry():
    return AssetRegistry(
        asset_id="550e8400-e29b-41d4-a716-446655440000",
        name="Player",
        created_at=datetime.utcnow()
    )
```

**Frontend (Zod):**
```typescript
import { z } from 'zod';

export const AssetRegistrySchema = z.object({
  asset_id: z.string().uuid(),
  name: z.string().min(1).max(255),
  created_at: z.coerce.date(),
});

export type AssetRegistry = z.infer<typeof AssetRegistrySchema>;

export async function getRegistry(): Promise<AssetRegistry> {
  const response = await fetch('/api/registry');
  return AssetRegistrySchema.parse(await response.json());
}
```

## Spec Reference

See: `project_board/specs/902_25_pydantic_zod_validation_spec.md`

## Dependencies

- M902-24 (OpenAPI → TypeScript Generation) — types inform Zod schemas
- Backend with Pydantic models (may need refactoring existing endpoints)
