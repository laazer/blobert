# TICKET: registry-fix-versions-slots-load
Title: Fix model registry: multiple versions, empty slots, easy load of existing models
Project: blobert
Created By: Human
Created On: 2026-04-11

---

## Description
the registry needs fixing. i still can't save more then one version of a model. i still can't save models to empty slots. and i still cant load existing models easily

**Spec:** `project_board/specs/registry-fix-versions-slots-load.md`

**Context (orchestrator):** Registry flow spans `asset_generation/web/frontend` (e.g. `SaveModelModal.tsx`, `ModelRegistryPane.tsx`), FastAPI `asset_generation/web/backend/routers/registry.py`, and Python `asset_generation/python/src/model_registry/service.py`. Save/slot operations currently gate on version existing in registry, `draft`/`in_use`, and non-empty slot lists in APIs.

---

## Acceptance Criteria
- User can persist **more than one** distinct version per model family without losing or blocking prior versions (inferred: clarify player vs enemy if both affected).
- User can assign a version into **empty** slot positions without erroneous rejection or dead ends in the UI/API (inferred).
- User can **load or select** existing registry models with a straightforward flow (search, picker, or documented minimal steps) and verified behavior (inferred).
- Automated tests cover the corrected registry behavior (Python API and/or frontend as appropriate); full Godot suite remains green where touched.
- No regression to atomic `model_registry.json` writes or existing spawn/slot invariants unless explicitly changed in spec.

---

## Dependencies
- `project_board/specs/registry-fix-versions-slots-load.md` (behavioral source of truth for this ticket)

---

## Execution plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Bind acceptance criteria to **exact behaviors** (multi-version persistence, empty slot semantics, load-existing UX, draft/in_use vs slot rules) for enemy **and** player where shared. | Spec Agent | This ticket; `asset_generation/python/src/model_registry/service.py`; `asset_generation/web/backend/routers/registry.py`; `SaveModelModal.tsx`; `ModelRegistryPane.tsx`; `registryLoadExisting.ts` | Spec section or `project_board/specs/*.md` per repo convention; explicit API contracts and UI states | None | Spec is reviewable; no ambiguous “fix registry” language; documents edge cases (empty `version_ids`, `""` slot placeholders, sync-before-slot) | Assumes both player and enemy in scope unless narrowed (see checkpoint). |
| 2 | Author **failing-first tests** for registry service + HTTP router: `put_enemy_slots` (non-empty list, `""` placeholders, draft/in_use rejection), `validate_manifest` slot arrays, `sync_discovered_animated_glb_versions` adding distinct version rows, and any new/changed endpoints. | Test Designer | Approved spec | New/updated tests under `asset_generation/python/tests/` and `asset_generation/web/backend/tests/test_registry_*.py` | 1 | Pytest passes for new tests once implementation exists (red→green in pipeline) | Test env must not mutate real `model_registry.json`; use fixtures/temp roots per existing patterns. |
| 3 | Author **frontend tests** for `SaveModelModal` and `ModelRegistryPane`: multi-variant save, targeting empty slot indices, error messages vs spec, load-existing selection path (mocked client). | Test Designer | Spec; existing `*.test.tsx` | Updated/added Vitest tests | 1 | Tests encode spec; CI frontend test task green after implementation | Mocks must match FastAPI response shapes. |
| 4 | Stress **adversarial** cases: duplicate slot IDs, all-empty slots, concurrent refresh, invalid family, patch ordering (slot put vs version patch). | Test Breaker | Spec + tests from 2–3 | Additional negative/edge tests marked `# CHECKPOINT` where assumption-driven | 2, 3 | New tests fail until implementation hardened or spec explicitly allows behavior | May surface spec gaps → bounce to Spec Agent. |
| 5 | Implement **Python registry core**: `service.py` (`put_enemy_slots`, validation, sync discovery, atomic save invariants), keeping spawn/slot rules consistent with spec. | Implementation Backend | Spec; tests 2+4 | Green Python + backend tests | 2, 4 | `bash .lefthook/scripts/py-tests.sh` (or project canonical) green for touched areas | Cross-family or Godot `res://` impact: escalate to Implementation Generalist if spec requires. |
| 6 | Implement **FastAPI router** alignment: status codes, request/validation errors, optional sync endpoint behavior if spec adds it. | Implementation Backend | Spec; `registry.py` | Green `test_registry_*` | 5 | Router matches spec; no silent 500s on valid UI payloads | Pydantic models stay strict per `CLAUDE.md`. |
| 7 | Implement **frontend**: `SaveModelModal.tsx`, `ModelRegistryPane.tsx`, `registrySlotOps.ts`, API client calls — including resolving **in_use/draft gating** vs “save to slot” UX (e.g. one-step promote, clearer errors, or pre-flight sync). | Implementation Frontend | Spec; tests 3+4 | Green frontend tests; manual smoke optional | 3, 4, 6 | `npm test` in `asset_generation/web/frontend` green | **`canAddEnemySlot` vs `nextEnemySlotsAfterAdd` eligibility mismatch** is a known risk; spec should define `in_use` requirement. |
| 8 | **Static QA** on touched TS/Python (Ruff, hooks as in `Taskfile.yml`). | Static QA Agent | Diff from 5–7 | Clean lint/review | 5, 6, 7 | `task hooks:py-review` / `task hooks:gd-review` only if GD touched; TS/ESLint per frontend | None. |
| 9 | **Integration**: `timeout 300 ci/scripts/run_tests.sh`; confirm no regression to Godot suite if any `res://` or shared constants touched. | Integration Agent | Green unit layers | Logged exit 0 in ticket Validation | 8 | Full suite green | Godot timeout discipline per `CLAUDE.md`. |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_BACKEND

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: Partial (Python + backend registry tests green including adversarial suite; Vitest still red on `canAddEnemySlot` / Add slot until R3 frontend implementation)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Implementation Backend Agent

## Required Input Schema
```json
{
  "ticket_path": "string",
  "spec_path": "project_board/specs/registry-fix-versions-slots-load.md"
}
```

## Status
Proceed

## Reason
Test Breaker added adversarial/edge tests (placeholder-only and long-placeholder PUT, player slot atomicity, multi-GLB sync stress, cross-family slot isolation, legacy `player_active_visual` load-existing candidates, repeated GET determinism, frontend filter/identity cases). Stage advances to backend implementation per execution plan task 5 (`service.py`, router alignment); frontend R3 reds remain for Implementation Frontend.
