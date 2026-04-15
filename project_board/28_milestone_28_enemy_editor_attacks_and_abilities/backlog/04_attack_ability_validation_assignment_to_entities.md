Title:
Validation, Registry Round-Trip, and Enemy/Player Attack Assignment

Description:
Complete the end-to-end flow by validating ability/attack graphs, persisting them in registry JSON, and allowing users to assign one or more attack models to either the current enemy config or player config. This ticket ties authored data to output payloads used by the asset pipeline for both entity types.

Acceptance Criteria:
- Save validation rejects circular or invalid references (attack -> missing ability, entity -> missing attack)
- The editor exposes an "Assigned Attacks" control on both enemy and player configuration panels
- Users can assign/unassign attack models to the current enemy or player and define execution order
- Assigned attacks serialize into enemy and player config JSON in a stable, deterministic order
- Reloading an enemy or player with assigned attacks restores links correctly in the editor UI
- A validation summary panel lists blocking errors and non-blocking warnings before export

Scope Notes:
- Validation summary can be text-based; no advanced graph visualization required
- No automatic fix-up/migration for broken legacy references in this ticket
- No combat DPS simulation or balancing heuristics
- Export order follows explicit user ordering, otherwise fallback sort by attack ID

## Web Editor Implementation

**Python / FastAPI (`asset_generation/web/backend/` + `asset_generation/python/src/`)**
- Add validation service logic (for example `services/attack_ability_validation.py`) to verify cross-reference integrity among `ability_models`, `attack_models`, enemy `assigned_attacks`, and player `assigned_attacks`
- Expose validation endpoint such as `POST /api/attacks/validate` returning `errors[]` and `warnings[]`
- Extend enemy and player config save/load routes to include `assigned_attacks: list[str]`
- Ensure model registry serializers write deterministic key/order output for stable diffs

**Frontend (`asset_generation/web/frontend/src/`)**
- Add enemy-level and player-level assigned-attacks UI components (multi-select list with move up/down ordering)
- Add validation panel in the Attacks/Abilities tab with blocking/non-blocking message buckets
- Wire pre-export validation call; block save/export on blocking validation errors
- Ensure enemy and player config load hydrates assigned attacks and highlights missing references gracefully

**Tests**
- Backend: `test_attack_ability_validation.py` covering happy path, missing references, and deterministic ordering guarantees
- Backend API: route tests for validation endpoint and enemy/player config assigned-attack persistence
- Frontend (Vitest): `EntityAttackAssignment.test.tsx` for enemy/player assign-unassign/reorder and validation rendering

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0
