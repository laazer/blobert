# Registry Mutation Service Boundary

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Move registry mutation logic currently implemented in API route helpers into shared package service modules so business rules live in one domain/service layer.

Target overlap:
- `asset_generation/web/backend/routers/registry.py` (`_find_enemy_version`, `_apply_enemy_version_delete`, player-active delete flow)
- `blobert_asset_gen.services.registry` (or transitional `asset_generation/python/src/model_registry/service.py`)

## Acceptance Criteria

- [ ] Service layer provides public APIs for enemy-version delete and player-active-visual delete.
- [ ] API delete endpoints become thin transport wrappers (request validation + HTTP mapping only).
- [ ] Manifest save/validate behavior remains atomic and unchanged.
- [ ] Delete confirmation semantics (`confirm`, `confirm_text`, sole in-use guard) are preserved.
- [ ] Existing deletion tests pass; new tests cover service-level delete behavior.

## Dependencies

- Registry Path Policy Unification

## Execution Plan

# Project: Registry Mutation Service Boundary
**Description:** Move enemy-version and player-active-visual registry deletion mutation rules from backend route helpers into one shared service-layer boundary while preserving existing API contracts, atomicity guarantees, and delete confirmation guardrails.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Freeze mutation service boundary contract and router-to-service delegation rules for delete flows. | Spec Agent | Ticket description/acceptance criteria, current delete helper logic in `asset_generation/web/backend/routers/registry.py`, current service API surface in `blobert_asset_gen.services.registry` or transitional `asset_generation/python/src/model_registry/service.py`, and dependency ticket outputs from Registry Path Policy Unification | Functional and non-functional specification defining public service APIs for enemy-version delete and player-active-visual delete, strict confirmation semantics (`confirm`, `confirm_text`, sole in-use guard), atomic manifest save/validate behavior, and unchanged endpoint payload/path contracts | None | Spec maps each acceptance criterion to deterministic runtime outcomes and defines service-owned business rules vs router-owned transport concerns without ambiguity | Assumes dependency behavior from path policy work is available for reference; if unresolved, spec must explicitly version-lock assumptions and route dependency uncertainty through checkpoints |
| 2 | Author primary RED behavioral tests for service-level delete mutations and thin router wrappers. | Test Designer Agent | Approved spec from Task 1, existing backend registry delete tests, existing Python registry service tests, current endpoint contracts | RED tests proving service-layer delete behavior (enemy-version + player-active-visual), confirmation guardrails, sole in-use protections, atomic save/validate invariants, and router delegation limited to validation + HTTP mapping | 1 | Tests fail when business logic remains in router helpers, when service APIs violate guardrails, or when endpoint compatibility drifts | Risk of over-coupling tests to helper internals; tests must assert observable runtime behavior only |
| 3 | Expand adversarial RED coverage for destructive delete edge conditions and confirmation abuse. | Test Breaker Agent | Spec and Task 2 test suite | Additional RED tests for malformed confirmation values, mismatched `confirm_text`, race-like sequencing around sole in-use checks, and invalid mutation requests that must fail closed without partial manifest mutation | 2 | Edge tests expose mutation safety gaps and enforce deterministic failure taxonomy for destructive operations | Assumes existing fixtures can simulate in-use and manifest mutation states deterministically |
| 4 | Implement service-boundary extraction and migrate router delete endpoints to transport-only wrappers. | Implementation Backend Agent | Frozen spec, approved RED tests from Tasks 2-3, current router/service modules | Refactored service APIs for both delete flows, router code with HTTP-only concerns, preserved payload/path contracts, and unchanged atomic manifest behavior | 3 | All delete mutation decisions execute in service layer, router helpers no longer host business rules, and all targeted test suites pass | Risk of subtle regression in exception-to-HTTP mapping after delegation; implementation must preserve response semantics |
| 5 | Validate static quality, behavioral evidence, and acceptance-criteria traceability for handoff readiness. | Static QA Agent then Acceptance Criteria Gatekeeper Agent | Implementation diff, command outputs from required test suites, linter diagnostics | Verification evidence package proving AC closure with explicit mapping from tests to each acceptance criterion, plus no-regression confirmation for existing deletion flows | 4 | Required suites pass, no new lints from touched files, and gatekeeper can confirm ACs are satisfied with executable evidence | Assumes test commands remain stable across backend and Python package environments; any environment divergence must be documented and blocked conservatively |

## Notes

- Do not change endpoint paths or payload contracts in this ticket.

---

## Functional and Non-Functional Specification

### Requirement R1 - Service-Owned Enemy Version Delete API

#### 1. Spec Summary
- **Description:** A public service-layer delete API shall own all business rules for deleting one enemy version from a family, including target existence checks, delete eligibility (`draft` vs `in_use`), confirm/confirm_text validation, sole in-use guard, manifest mutation, validation, and atomic persistence.
- **Constraints:** The service API must preserve existing endpoint contract semantics for successful and failing deletes. It must support optional file deletion controlled by `delete_files`, using the resolved registry-relative path only after successful manifest save.
- **Assumptions:** Path canonicalization and allowlist enforcement are already delegated through the shared path policy API delivered by the completed dependency ticket.
- **Scope:** Service modules (`blobert_asset_gen.services.registry` or transitional `asset_generation/python/src/model_registry/service.py`) and deletion flow currently implemented in backend route helpers.

#### 2. Acceptance Criteria
- AC-R1.1: Service exposes a callable API for enemy-version delete that takes, at minimum, `python_root`, `family`, `version_id`, `confirm`, and the existing optional controls (`confirm_text`, `target_path`, `delete_files`).
- AC-R1.2: If target family/version does not exist, the service returns deterministic unknown-target failure behavior equivalent to current route-visible behavior.
- AC-R1.3: If target row path is missing or malformed, service fails closed with deterministic malformed-target behavior.
- AC-R1.4: If `confirm` is false, service rejects delete (no manifest mutation, no file deletion).
- AC-R1.5: `target_path` mismatch against resolved row path is rejected as forbidden-target mismatch, preserving current security semantics.
- AC-R1.6: Draft delete confirmation text behavior remains unchanged: if `confirm_text` is provided, it must equal `delete draft {family} {version_id}` after trimming; if omitted, delete may proceed.
- AC-R1.7: In-use delete confirmation text behavior remains unchanged: required text is exactly `delete in-use {family} {version_id}` after trimming.
- AC-R1.8: Deleting an in-use version that is the sole remaining live (non-draft, in_use=true) row in that family fails with conflict behavior; manifest remains unchanged.
- AC-R1.9: If target is neither draft nor in-use, delete fails with malformed-target behavior.
- AC-R1.10: Successful delete removes the specific version row and removes matching slot references for that version id.
- AC-R1.11: Successful delete validates mutated manifest and persists via atomic save operation; returned payload remains validated manifest.
- AC-R1.12: `delete_files=true` attempts filesystem deletion only after successful atomic manifest save; `delete_files=false` never attempts filesystem deletion.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Moving logic out of router can change failure-type mapping by accident.
- **Impact:** API clients may observe status/detail regressions despite equivalent core behavior.
- **Mitigation:** Service contract freezes current failure taxonomy and leaves transport mapping responsibility to router.
- **Risk:** File deletion attempted before durable manifest write.
- **Impact:** Data/file state divergence in partial-failure scenarios.
- **Mitigation:** Enforce post-save file deletion ordering as explicit requirement.

#### 4. Clarifying Questions
- None.

### Requirement R2 - Service-Owned Player Active Visual Delete API

#### 1. Spec Summary
- **Description:** A public service-layer delete API shall own all business rules for deleting `player_active_visual`, including confirmation enforcement, active-target existence checks, sole-active guard, player slot mutation, manifest validation, and atomic persistence.
- **Constraints:** Endpoint path and payload contracts remain unchanged. Existing behavior that unslots the current first assigned player slot must remain unchanged.
- **Assumptions:** Player manifest structure remains schema-compatible with current `player.versions` and `player.slots` usage.
- **Scope:** Service layer and router delete flow for `DELETE /api/registry/model/player_active_visual`.

#### 2. Acceptance Criteria
- AC-R2.1: Service exposes a callable API for player-active-visual delete that takes, at minimum, `python_root` and `confirm`.
- AC-R2.2: If `confirm` is false, service rejects delete (no manifest mutation).
- AC-R2.3: If `player_active_visual` is absent, service returns unknown-target failure behavior equivalent to current route-visible behavior.
- AC-R2.4: If assigned non-empty player slots count is less than or equal to one, service rejects delete with sole-active conflict behavior.
- AC-R2.5: On success, service unslots the first assigned non-empty slot id by replacing matching entries with empty string, preserving other slots.
- AC-R2.6: On success, service removes `player_active_visual` key from manifest.
- AC-R2.7: On success, service validates manifest and persists via atomic save; returned payload remains validated manifest.
- AC-R2.8: Service mutation remains all-or-nothing: any failure before save results in no persisted manifest changes.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Ambiguity about which slot to unslot when multiple assigned slots exist.
- **Impact:** Behavioral drift in active visual resolution.
- **Mitigation:** Contract preserves current deterministic rule: unslot first assigned non-empty slot entry.
- **Risk:** Hidden coupling to legacy `player_active_visual` consumers.
- **Impact:** Regressions in downstream reads.
- **Mitigation:** Require unchanged response shape and existing validation/persistence path.

#### 4. Clarifying Questions
- None.

### Requirement R3 - Router Becomes Transport-Only for Delete Endpoints

#### 1. Spec Summary
- **Description:** Backend delete endpoints become thin transport wrappers that perform request parsing and HTTP translation only. Business rules currently in `_find_enemy_version`, `_apply_enemy_version_delete`, and player-active delete flow move to service APIs.
- **Constraints:** Router must not duplicate mutation decision logic (eligibility, confirm text rules, sole guards, mutation ordering). Endpoint route paths, request schemas, and response payload contracts must stay unchanged.
- **Assumptions:** Existing FastAPI request models remain authoritative for payload structure.
- **Scope:** `asset_generation/web/backend/routers/registry.py` delete handlers and helper usage graph.

#### 2. Acceptance Criteria
- AC-R3.1: Enemy delete endpoint delegates mutation decisions and persistence to service delete API.
- AC-R3.2: Player-active delete endpoint delegates mutation decisions and persistence to service delete API.
- AC-R3.3: Router-local helper functions implementing delete business rules are removed from active delete decision path.
- AC-R3.4: Router retains only transport concerns: input deserialization, service invocation, and exception-to-HTTP mapping.
- AC-R3.5: Endpoint path patterns and request/response payload contracts remain backward compatible.
- AC-R3.6: Existing route-level deletion behavior remains observationally equivalent for success and failure classes.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Partial migration leaves split logic (router + service).
- **Impact:** Inconsistent behavior and hard-to-maintain policy surface.
- **Mitigation:** Explicitly prohibit duplicated business-rule enforcement in router.
- **Risk:** Over-thinning router may remove necessary transport validation.
- **Impact:** Incorrect status mapping or malformed request handling regressions.
- **Mitigation:** Preserve request-model validation and HTTP exception mapping responsibilities.

#### 4. Clarifying Questions
- None.

### Requirement R4 - Atomicity, Ordering, and Failure Safety Invariants

#### 1. Spec Summary
- **Description:** Delete flows must preserve current atomic manifest behavior: mutate in memory, validate, atomically save, then perform optional side effects. Failures before successful save must not persist partial manifest state.
- **Constraints:** Service implementation must continue to use the same validation and atomic save facilities (`validate_manifest` and atomic write path). No out-of-band persistence side channels.
- **Assumptions:** Atomic write helper semantics remain unchanged in this ticket.
- **Scope:** Service-layer delete APIs for enemy version and player active visual.

#### 2. Acceptance Criteria
- AC-R4.1: Both service delete APIs call manifest validation before persistence.
- AC-R4.2: Both service delete APIs persist through atomic save operation.
- AC-R4.3: If validation fails, no manifest write occurs.
- AC-R4.4: For enemy delete with `delete_files=true`, file unlink is attempted only after successful atomic manifest save.
- AC-R4.5: If optional file unlink fails, saved manifest remains valid and persisted; failure handling remains deterministic and documented by implementation behavior.
- AC-R4.6: No additional non-atomic mutation storage path is introduced.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Implementation may accidentally reorder side effects for convenience.
- **Impact:** Non-recoverable manifest/file divergence.
- **Mitigation:** Explicit ordering criteria and all-or-nothing manifest persistence requirements.
- **Risk:** Unclear post-save behavior if file unlink fails.
- **Impact:** Inconsistent observable outcomes.
- **Mitigation:** Spec fixes persistence precedence; implementer must preserve deterministic error/return semantics.

#### 4. Clarifying Questions
- None.

### Requirement R5 - Non-Functional Compatibility, Security, and Testability

#### 1. Spec Summary
- **Description:** The refactor must preserve externally observable API compatibility while improving layering. Security-sensitive confirmation and target-path checks must remain fail-closed. Outcomes must be runtime-testable at both service and endpoint layers.
- **Constraints:** No endpoint path changes, no request/response schema changes, no router reintroduction of business rules, and no prose-only evidence.
- **Assumptions:** Existing test suites and fixtures for registry deletion flows can be extended to service-level behavior assertions.
- **Scope:** Service delete APIs, backend router delete endpoints, and downstream test-design boundaries.

#### 2. Acceptance Criteria
- AC-R5.1: Existing deletion tests continue to pass without weakening assertions.
- AC-R5.2: New behavioral tests cover service-level enemy delete and player-active delete contracts.
- AC-R5.3: Tests include confirm/confirm_text guardrails, sole in-use/sole active guards, and target mismatch protections.
- AC-R5.4: Tests verify router layer is transport-only by asserting delegated observable behavior rather than helper internals.
- AC-R5.5: Failure and success outcomes are deterministic for identical inputs.
- AC-R5.6: No unnecessary documentation artifacts are introduced beyond required workflow/ticket updates.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Tests may accidentally assert internal helper structure.
- **Impact:** Brittle suite that misses true behavior regressions.
- **Mitigation:** Require observable runtime-output assertions at service and endpoint boundaries.
- **Risk:** Migration could subtly alter error detail text relied on by clients.
- **Impact:** Client parsing regressions.
- **Mitigation:** Preserve current semantics and error taxonomy; treat text/shape drift as regression unless explicitly justified.

#### 4. Clarifying Questions
- None.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: Passed
  - `cd asset_generation/python && uv run pytest tests/model_registry/test_m901_12_registry_mutation_service_boundary_contract.py tests/model_registry/test_service.py tests/model_registry/test_service_registry_fix_adversarial.py` (118 passed)
  - `cd asset_generation/web/backend && uv run pytest tests/test_m901_12_registry_delete_router_service_delegation_contract.py tests/test_registry_delete_router.py` (20 passed)
- Static QA: Passed (`ReadLints` on touched files reports no diagnostics)
- Integration: Not Run (not required for this ticket scope)
- Acceptance Criteria Coverage: Functional ACs are evidenced by the listed passing service-level and router-level test suites; no uncovered AC behavior is identified in ticket evidence.

## Blocking Issues
- None.

## Escalation Notes
- None.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/done/12_registry_mutation_service_boundary.md",
  "required_action": "Optional human spot-check or archival workflow continuation."
}
```

## Status
Proceed

## Reason
All listed acceptance criteria have explicit, passing test evidence and no uncovered behavior gaps are identified in the ticket evidence. Stage/folder consistency is now satisfied with this ticket in `done/`, so final Stage is set to `COMPLETE`.
