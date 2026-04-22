# Backend Registry Service Extraction and Router Thinning

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** In progress

---

## Description

Refactor `asset_generation/web/backend/routers/registry.py` into a thin transport layer backed by explicit package service objects. Move manifest mutation/query workflows out of route handlers and into shared service modules.

## Acceptance Criteria

- [x] Registry router no longer contains direct domain mutation helpers.
- [x] Query and mutation workflows live in package service module(s).
- [x] Router responsibilities are limited to request validation, response mapping, and status codes.
- [x] Existing registry endpoint behavior remains backward compatible.
- [x] Registry API tests pass unchanged or with minimal transport-only updates.

## Dependencies

- Backend-Python Import Adapter
- Registry Mutation Service Boundary

## Execution Plan

# Project: Backend Registry Service Extraction and Router Thinning
**Description:** Extract the remaining load-existing / identity-resolution workflow helpers from `routers/registry.py` into dedicated backend service modules, leaving the router as a thin transport layer. Preserve all registry HTTP behavior and error mapping.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Define service-module seams (`registry_query`, `registry_mutation`) and what must *not* remain in the router. | Spec Agent | Ticket, current `routers/registry.py` | Spec with deterministic invariants and explicit “router-only” rules | None | Invariants are testable without reading prose-only docs | Assumes `src.model_registry.service` remains authoritative domain engine |
| 2 | Add regression tests for extraction + import binding semantics (including FastAPI `from import` patch targets). | Test Designer Agent | Spec | RED tests for mechanical extraction + import binding | 1 | Tests fail if helpers return to the router or patch targets stop working | Tests must be runtime behavior, not board markdown matching |
| 3 | Move query helpers to `services/registry_query.py` and add `services/registry_mutation.py` import seam; keep router transport-only. | Implementation Backend Agent | Spec + tests | Green refactor, router imports service functions, behavior unchanged | 2 | All targeted registry backend suites pass; diff-cover policy passes for python changes | Risk: FastAPI modules bind imported names; tests must patch `routers.registry.<name>` not only `services.registry_query` |

---

## Functional and Non-Functional Specification

### Requirement R1 - Extract load-existing / identity query workflows
#### 1. Spec Summary
- **Description:** Functions that scan registry JSON, normalize candidate GLB paths, and resolve identity targets must not live in `routers/registry.py` as ad-hoc helpers.
- **Constraints:** Preserve all HTTP-visible responses, status code mapping, and “fail closed” path policy delegation through `src.model_registry.service` normalization.
- **Assumptions:** Prior tickets already centralized *policy*; this ticket centralizes *composition* of those policy calls and registry scanning.

#### 2. Acceptance Criteria
- **AC-R1.1:** `services.registry_query` exposes the extracted workflow entrypoints (including load-existing candidate generation + identity path resolution + HTTP-normalization helper for GLB strings).
- **AC-R1.2:** The router file must not define the extracted helper functions (mechanically verifiable by AST in tests).

### Requirement R2 - Explicit mutation service import seam
#### 1. Spec Summary
- **Description:** Router continues to use `import_asset_module("src.model_registry.service")` indirectly via a single `services.registry_mutation.load_model_registry_service()` seam for consistency and future `blobert_asset_gen` renames.
#### 2. Acceptance Criteria
- **AC-R2.1:** Router `_load_service()` is a thin wrapper over `load_model_registry_service()`.

### Requirement R3 - Transport-only router
#### 1. Spec Summary
- **Description:** `routers/registry.py` is limited to models, route declarations, and HTTP mapping. Domain orchestration for load-existing and identity open flows is implemented outside the router in `services/`.
#### 2. Acceptance Criteria
- **AC-R3.1:** `open_load_existing` and `get_load_existing_candidates` route bodies do not re-implement the extracted scanning loops locally.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

COMPLETE

## Revision

1

## Last Updated By

Acceptance Criteria Gatekeeper Agent

## Validation Status

- Backend targeted suites (command): `cd asset_generation/web/backend && uv run pytest tests/test_m901_13_backend_registry_service_extraction_contract.py tests/test_m901_11_registry_router_path_policy_delegation_contract.py tests/test_registry_load_existing_allowlist_router.py tests/test_registry_delete_router.py tests/test_registry_atrad_cross_cutting.py tests/test_registry_model_selection_router.py -q` → `85 passed`
- Diff coverage gate (command): `bash ci/scripts/diff_cover_preflight.sh` → `PASS` (`Coverage: 93%` of diff vs `origin/main`)
- Lints: `read_lints` on touched router/service/test files → no issues

## Blocking Issues

- None

## Escalation Notes

- `from services.registry_query import ...` creates local name bindings; tests that monkeypatch `services.registry_query` may not affect `routers.registry` imports — patch `routers.registry.<symbol>` for transport-level seams.

---

# NEXT ACTION

## Next Responsible Agent

Human

## Required Input Schema

```json
{
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/done/13_backend_registry_service_extraction_and_router_thinning.md",
  "action": "git push after reviewing local workspace (repo has other unrelated unstaged WIP if present)."
}
```

## Status

Proceed

## Reason

Service extraction landed with registry suites green, diff-cover gate green, and router-only AST guardrails. Ticket moved to milestone `done/` to satisfy board/workflow state consistency.
