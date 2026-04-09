# TICKET: 07_editor_delete_draft_and_in_use_models

Title: Editor — delete draft exports and delete in-use models (safety rules)

## Description

Implement **delete draft** (remove registry entry + files or orphan handling per spec) and **delete in-use** with mandatory safeguards: e.g. block delete when sole version for a type, require confirmation, or auto-reassign pool — exactly as specified in `01_spec_model_registry_draft_versions_and_editor_contract`.

## Specification

### Requirement DDIM-F1 — Delete draft flow enforces registry/file consistency and explicit operator intent

#### 1. Spec Summary
- **Description:** The system MUST support deleting an enemy draft version (`draft=true`) by identity (`family`, `version_id`) with deterministic outcomes: registry row removal and delete behavior bounded by MRVC D1 (`project_board/specs/model_registry_draft_versions_spec.md`, MRVC-9). When file delete mode is enabled for D1, the targeted `.glb` is deleted only under allowlisted roots; companion files may be removed only when they are deterministic orphans of that deleted draft.
- **Constraints:** The delete-draft path applies only to enemy versions that exist and are currently draft. It MUST NOT be used for non-draft versions, unknown identities, or non-enemy targets. All path checks MUST satisfy MRVC allowlist/traversal constraints before touching disk.
- **Assumptions:** Dependency `01_spec_model_registry_draft_versions_and_editor_contract` remains authoritative. This ticket specifies behavior and validation semantics, not a schema revision.
- **Scope:** Backend delete-draft behavior in registry router/service and frontend destructive-action UX for draft deletion.

#### 2. Acceptance Criteria
- **DDIM-F1.1:** Given a registry entry at `enemies[family].versions[*]` with `id=version_id` and `draft=true`, delete-draft removes exactly that version record and no other version records.
- **DDIM-F1.2:** If D1 file deletion is enabled, the corresponding `.glb` path for the deleted draft is deleted from disk only when it resolves under allowlisted roots; otherwise request is rejected with no mutation.
- **DDIM-F1.3:** Delete-draft for any non-draft target is rejected deterministically (client-visible failure category + stable message class), with no registry or filesystem side effects.
- **DDIM-F1.4:** Repeating the same delete-draft request after a successful delete yields deterministic stale-target behavior (not-found or equivalent stale rejection), with no additional side effects.
- **DDIM-F1.5:** UI requires explicit confirmation before executing draft delete whenever file deletion can occur; cancel path performs no API call.

#### 3. Risk & Ambiguity Analysis
- Draft/file drift can occur when registry row exists but file is already missing; implementation must define deterministic stale-file handling without partial writes.
- Concurrent delete and patch operations on the same version can race; write path needs atomic manifest persistence and all-or-nothing mutation semantics.
- Companion-file deletion is potentially ambiguous; only deterministic orphan-safe removal is permitted.

#### 4. Clarifying Questions
- No open questions for this requirement.

### Requirement DDIM-F2 — Delete in-use flow preserves playable model invariants

#### 1. Spec Summary
- **Description:** Deletion of in-use models MUST enforce MRVC D3/D4/D5 invariants. For enemies, deleting an in-use version is allowed only when the target is not the sole in-use version in that family (D3). Deleting the sole in-use version is blocked (D4). For player active visual, deleting the only active path is blocked (D5).
- **Constraints:** Safety checks MUST execute against the latest persisted manifest state immediately before write. No delete path may bypass invariant checks through direct path-target deletion.
- **Assumptions:** Invariant authority comes from MRVC-9 matrix and current manifest fields (`draft`, `in_use`, `player_active_visual`).
- **Scope:** Guard decision logic, guarded delete confirmation UX, and deterministic registry state transitions for allowed in-use deletion.

#### 2. Acceptance Criteria
- **DDIM-F2.1:** For enemies, delete of in-use target succeeds only when at least one other in-use, non-draft version remains in the same family after deletion.
- **DDIM-F2.2:** For enemies, delete of in-use target is rejected when it would leave the family with zero in-use versions (sole-version guard).
- **DDIM-F2.3:** For player active visual, delete request is rejected when target equals the only active player path and no replacement has been committed first.
- **DDIM-F2.4:** Allowed in-use delete requires explicit confirmation text that names the target family + version id and states the effect on spawn eligibility.
- **DDIM-F2.5:** After any successful in-use delete, manifest remains valid per MRVC validation and any family slot references to removed version ids are either deterministically removed in the same transaction or request is rejected before mutation.

#### 3. Risk & Ambiguity Analysis
- Enemy family invariants and player active-path invariants differ; if both are handled in one code path, branching errors can leak unsafe deletes.
- Slot cleanup policy for deleted in-use entries is a high-risk consistency point; mutation must be transactional.
- Cross-session edits can invalidate pre-confirmation UI assumptions; backend must remain final arbiter at execution time.

#### 4. Clarifying Questions
- No open questions for this requirement.

### Requirement DDIM-F3 — Delete API/UI contracts surface explicit confirmation and error semantics

#### 1. Spec Summary
- **Description:** Delete operations MUST expose explicit, machine-testable request and response semantics for success, validation failure, forbidden path class, not found, and invariant conflict. UI MUST present differentiated confirmation copy for draft delete vs in-use delete and preserve local state on failures.
- **Constraints:** No implicit deletion from row-click or selection-change events. Delete requests must be explicit operator actions with target identity that the backend re-validates.
- **Assumptions:** Existing `/api/registry` router + `model_registry.service` are extension points; endpoint naming may vary but behavior contract in this requirement is normative.
- **Scope:** API contract semantics, UI confirmation dialogs, error display behavior, and post-success refresh/invalidation semantics.

#### 2. Acceptance Criteria
- **DDIM-F3.1:** API responses use deterministic failure classes: malformed payload/target validation (`400`), forbidden path class (`403`), unknown target (`404`), and invariant violation conflict (`409`) where applicable to safeguarded in-use deletion.
- **DDIM-F3.2:** Error payloads are non-leaky: they MUST NOT expose host absolute paths or internal stack traces; messages identify actionable class only.
- **DDIM-F3.3:** UI confirmation copy for draft delete states irreversible delete behavior (registry-only vs registry+file outcome); in-use delete copy states guardrails and potential rejection reasons.
- **DDIM-F3.4:** On failed delete, editor selection and form state remain unchanged, and user receives actionable feedback (for example: "add another in-use version first").
- **DDIM-F3.5:** On successful delete, UI refresh removes deleted target from lists and any selected/dependent view state in a single deterministic refresh cycle (no stale row remnants).

#### 3. Risk & Ambiguity Analysis
- Existing router patterns may currently collapse invariant conflicts into generic validation failures; implementation must preserve deterministic category mapping.
- If UI performs optimistic removal without authoritative response, failed deletes can desync displayed registry state.
- Failure taxonomy must remain stable enough for deterministic tests without coupling to fragile full-string text.

#### 4. Clarifying Questions
- No open questions for this requirement.

### Requirement DDIM-NF1 — Determinism, safety, and regression compatibility

#### 1. Spec Summary
- **Description:** Delete behavior MUST be deterministic, atomic, and regression-safe across backend service, API surface, and editor state handling. The feature MUST not alter unrelated MRVC registry contracts.
- **Constraints:** No schema-version change in this ticket. No expansion of allowlist roots. No weakening of traversal/path normalization protections.
- **Assumptions:** Existing backend/frontend test harnesses can construct manifests with draft-only, mixed in-use, sole-in-use, stale-target, and slot-reference states.
- **Scope:** Non-functional requirements for reliability, observability, security hygiene, and compatibility with current registry/list/load workflows.

#### 2. Acceptance Criteria
- **DDIM-NF1.1:** Primary + adversarial test design covers: successful draft delete, blocked sole in-use delete, allowed non-sole in-use delete, stale-target repeat delete, and forbidden/malformed path classes.
- **DDIM-NF1.2:** Backend manifest mutation for successful delete is atomic (no partial update where registry row changes but related required state cleanup does not).
- **DDIM-NF1.3:** Existing non-delete routes (`get model`, patch flags, slots, load-existing) retain prior contract behavior except where delete-related consistency requires deterministic updates.
- **DDIM-NF1.4:** Full gate remains `timeout 300 ci/scripts/run_tests.sh` exit 0.
- **DDIM-NF1.5:** Delete flow observability is sufficient for deterministic assertion (stable status class, stable reason category, and post-state checks), without sensitive path leakage.

#### 3. Risk & Ambiguity Analysis
- Shared mutation helpers increase regression blast radius; tests must isolate delete-specific behavior and unchanged behavior.
- Concurrent mutation determinism can be hard to verify without explicit stale-target assertions.
- UI and backend can drift if success/failure refresh semantics are not tied to authoritative API results.

#### 4. Clarifying Questions
- No open questions for this requirement.

## Acceptance Criteria

- Draft delete and in-use delete are implemented with explicit confirmations and deterministic backend safety guards per MRVC D1-D5.
- Invariant violations (for example, deleting sole in-use enemy version or sole active player visual) are blocked with deterministic, non-leaky failures and no side effects.
- Test suites cover successful delete, blocked delete, repeated stale-target delete, and allowlist/path-safety rejection behavior.
- Post-delete state is valid MRVC manifest state with no stale references to deleted versions.
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

## Dependencies

- `01_spec_model_registry_draft_versions_and_editor_contract`
- `05_editor_ui_game_model_selection` (soft)
- `06_editor_load_existing_models_allowlist` (soft)
- M21

---

# Project: Editor Delete Draft And In-Use Models
**Description:** Deliver deterministic and safe delete workflows for draft and in-use registry models with explicit confirmations, invariant guards, and coverage for destructive-path edge cases.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Produce normative delete safety specification aligned to MRVC contract | Spec Agent | Ticket description/AC, `01_spec_model_registry_draft_versions_and_editor_contract`, current registry/router/frontend model-management flows | Spec section defining draft-delete and in-use-delete contract, invariant guards, confirmation requirements, and error/status semantics | None | Spec removes ambiguity for allowed vs rejected delete cases and defines deterministic post-delete state behavior | Risk: dependency spec ambiguity around replacement policy; assumption: MRVC dependency remains authoritative |
| 2 | Author primary deterministic tests for draft-delete and in-use-delete workflows | Test Designer Agent | Task 1 spec, backend registry router/service modules, frontend registry/editor components | Failing tests for successful draft delete, guarded in-use delete rejection/allowed path, UI confirmation behavior, and post-delete state refresh | 1 | Each acceptance criterion maps to at least one deterministic failing test before implementation | Risk: fixtures may not capture all in-use state variants; assumption: test fixtures can be extended without schema changes |
| 3 | Add adversarial tests for safety invariants and destructive-path edge cases | Test Breaker Agent | Task 1 spec + Task 2 tests, existing adversarial patterns in model registry tests | Additional failing adversarial tests for repeated delete/idempotency handling, stale target references, race-like mixed state updates, and forbidden invariant-breaking deletes | 2 | Adversarial suite proves no code path can produce undefined active-model state after delete operations | Risk: race simulation limits in unit-level harness; assumption: conservative deterministic assertions are sufficient |
| 4 | Implement backend delete logic for draft and in-use paths with invariant enforcement | Implementation Backend Agent | Approved spec/tests, backend registry services/routers | Backend implementation satisfying delete contracts, deterministic guard responses, atomic state updates, and canonical-root-safe file handling | 2, 3 | Backend primary + adversarial tests pass with explicit status/error semantics and no invariant violations | Risk: shared mutation helpers may introduce regressions; assumption: change scope can stay module-local with targeted reuse |
| 5 | Implement frontend confirmation UX and robust state refresh for delete operations | Implementation Frontend Agent | Spec contract, frontend tests, backend API behavior from Task 4 | UI actions for draft/in-use delete with explicit confirmation copy, guarded error surfacing, and deterministic list/state refresh on success/failure | 4 | Frontend tests pass; UI exposes no implicit destructive action and no stale deleted entries remain visible | Risk: existing component state caching may require careful invalidation; assumption: current store/query patterns support deterministic refresh |
| 6 | Execute AC traceability, full validation, and handoff readiness review | Acceptance Criteria Gatekeeper Agent | Completed implementation and all test artifacts | Ticket validation matrix mapping ACs to concrete test evidence and command outputs, including full suite gate | 4, 5 | `timeout 300 ci/scripts/run_tests.sh` exits 0 and AC evidence explicitly proves safe draft/in-use delete behavior | Risk: unrelated test instability may obscure final validation; assumption: targeted reruns can isolate non-feature flakes |

## Notes
- Tasks are sequential and independently executable once dependencies are satisfied.
- Delete behavior authority is dependency-driven: this ticket implements, but does not reinterpret, MRVC deletion policy.
- Any unresolved destructive-operation ambiguity must be checkpointed and resolved conservatively toward safety.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
11

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: Full suite gate evidenced: `timeout 300 ci/scripts/run_tests.sh` completed with exit 0.
- Tests: Targeted delete backend suite evidenced: `uv run --project asset_generation/python --extra dev pytest asset_generation/web/backend/tests/test_registry_delete_router.py -q` -> `12 passed in 0.24s`.
- Tests: Targeted frontend delete behavior suite evidenced: `npm test -- src/components/Editor/ModelRegistryPane.delete_flow.test.ts src/components/Editor/ModelRegistryPane.copy.test.ts src/api/registry_model_selection_client.test.ts` -> `3 passed`, `21 passed`.
- Integration: Frontend implementation now enforces explicit delete confirmation before API execution and cancel path performs no API call (`DDIM-F1.5`) via `executeEnemyDeleteFlow` and `buildEnemyDeletePlan`.
- Integration: Failed delete path preserves local editor state by avoiding success-sync mutations and surfacing actionable API error feedback (`DDIM-F3.4`).
- Integration: Successful delete path runs deterministic refresh synchronization (`syncFromRegistry`) to remove deleted targets from registry-driven lists and dependent selection state in one cycle (`DDIM-F3.5`).
- Integration: Combined backend delete guards/tests and frontend confirmation/refresh behavior provide explicit AC coverage for draft delete safety, in-use invariant blocking, stale-target determinism, path-safety rejection classes, and valid post-delete manifest state (`DDIM-F1`, `DDIM-F2`, `DDIM-F3`, `DDIM-NF1`).

## Blocking Issues
- None.

## Escalation Notes
- AC gate review complete: acceptance criteria are evidenced by targeted backend/frontend suites plus full-gate run. Ticket is ready for human folder move to milestone `done/`.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "ticket_path": "project_board/9_milestone_9_enemy_player_model_visual_polish/in_progress/07_editor_delete_draft_and_in_use_models.md",
  "next_step": "Move ticket to project_board/9_milestone_9_enemy_player_model_visual_polish/done/",
  "notes": "Gatekeeper AC review complete; evidence recorded in Validation Status."
}
```

## Status
Proceed

## Reason
All listed acceptance criteria have explicit evidence via backend/frontend targeted delete suites and a passing full-gate run (`timeout 300 ci/scripts/run_tests.sh`). Human ownership is now only the folder transition to `done/` and normal merge workflow.
