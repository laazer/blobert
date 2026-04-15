Title:
Ability Model CRUD & Typed Parameter Schema

Description:
Implement CRUD for reusable ability models with a typed parameter schema so attacks can reference stable, validated building blocks. Ability models represent capability-level logic metadata (e.g., projectile burst, leap strike, shield pulse) and include strongly typed fields required by downstream generation and runtime consumers.

Acceptance Criteria:
- Users can create, rename, update, and delete ability models from the "Ability Models" pane
- Each ability model has required fields: `id`, `name`, `ability_type`, `parameters`, and `version`
- `parameters` are validated against an ability-type schema (required keys, number/string/bool types, min/max ranges)
- Duplicate model IDs are rejected with inline error feedback
- Deleting an ability model that is referenced by an attack is blocked with a clear dependency message
- Ability models persist via API and reload correctly on editor refresh

Scope Notes:
- Schema is static and code-defined for this milestone (no dynamic schema authoring UI)
- Versioning is integer increment on save; no branching/version graph support
- Soft-delete/archive is out of scope; hard delete with dependency guard only
- No import/export file dialog in this ticket

## Web Editor Implementation

**Python / FastAPI (`asset_generation/web/backend/` + `asset_generation/python/src/`)**
- Add a new backend router (for example `routers/abilities.py`) with endpoints:
  - `GET /api/abilities`
  - `POST /api/abilities`
  - `PUT /api/abilities/{ability_id}`
  - `DELETE /api/abilities/{ability_id}`
- Define Pydantic request/response models for ability payloads with typed `parameters`
- Add schema validation helpers in Python pipeline-side model-registry module so backend and pipeline share one source of truth for ability model structure
- Persist ability models in model registry JSON under a dedicated top-level key (for example `ability_models`)

**Frontend (`asset_generation/web/frontend/src/`)**
- Add API client methods for ability CRUD endpoints
- Extend `store/useAppStore.ts` with `abilityModels` collection, selected model, and optimistic/pessimistic save flow
- Build `AbilityModelEditor.tsx` form with fields for identity/type and a parameter editor that renders inputs from the selected `ability_type` schema
- Show inline validation and API error states in the ability pane

**Tests**
- Backend: `test_abilities_router.py` covering create/update/delete/list, duplicate ID rejection, and schema validation failures
- Python pipeline tests: registry schema round-trip for `ability_models`
- Frontend (Vitest): `AbilityModelEditor.test.tsx` covers validation messaging, successful save, and deletion blocked when referenced

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0
