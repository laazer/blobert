Title:
Attack Editor with Ability Assignment

Description:
Add attack authoring in the "Attacks" pane where each attack type can reference one or more ability models and define attack-level metadata such as trigger type, cooldown, windup, and recovery. This enables composition: abilities are reusable components, while attack types package those components into concrete executable actions for either enemies or the player.

Acceptance Criteria:
- Users can create, edit, clone, and delete attack definitions
- Each attack has required fields: `id`, `name`, `trigger`, `cooldown_seconds`, `windup_seconds`, `recovery_seconds`
- Users can assign one or more ability models to a single attack type from the current ability catalog
- Assigned ability list supports ordering with explicit priority index (top-to-bottom execution order) for each attack type
- Attacks with missing required fields or zero assigned abilities are marked invalid and cannot be saved
- Attack type records persist via API and reload with assignment links intact

Scope Notes:
- No runtime simulation of full attack behavior in this ticket
- No conditional branching graph editor inside attacks
- Assignment ordering can be up/down controls; drag-and-drop ordering is optional and out of scope
- Attack clone copies assignments and metadata but generates a new ID

## Web Editor Implementation

**Python / FastAPI (`asset_generation/web/backend/` + `asset_generation/python/src/`)**
- Add a new backend router (for example `routers/attacks.py`) with endpoints:
  - `GET /api/attacks`
  - `POST /api/attacks`
  - `PUT /api/attacks/{attack_id}`
  - `DELETE /api/attacks/{attack_id}`
- Define Pydantic models for attack payloads including `ability_refs: list[str]` and timing fields; support multiple ability refs per single attack type
- Validate that all `ability_refs` exist in `ability_models` at save time
- Persist attacks in model registry JSON under a dedicated key (for example `attack_models`)

**Frontend (`asset_generation/web/frontend/src/`)**
- Add API client methods for attack CRUD endpoints
- Extend store with `attackModels` collection and assignment operations (`addAbilityToAttack`, `removeAbilityFromAttack`, `moveAbilityRef`)
- Build `AttackEditor.tsx` with attack metadata form and an "Assigned Abilities" section sourced from existing ability models; the same attack type must allow multiple assigned models
- Show validation state inline and disable save when invalid

**Tests**
- Backend: `test_attacks_router.py` covering CRUD, missing-ability reference rejection, and required field validation
- Python pipeline tests: assignment integrity checks across `attack_models` and `ability_models`
- Frontend (Vitest): `AttackEditor.test.tsx` covering assignment flow, ordering controls, and save disablement when invalid

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0
