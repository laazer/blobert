# TICKET: 09_automated_tests_registry_allowlist_delete

Title: Automated tests — registry API, allowlisted load, draft promotion, deletion invariants

## Description

Add **pytest** (backend) and/or **frontend** tests as appropriate to lock: registry read/write, draft vs in-use filtering, allowlisted path rejection, and post-delete invariants. Complements per-ticket tests in `04`–`07`; this ticket is the **cross-cutting** suite so refactors do not regress the contract.

## Specification

### Requirement ATRAD-F1 — Cross-cutting registry contract coverage baseline

#### 1. Spec Summary
- **Description:** This ticket MUST add automated contract tests that verify registry read/write behavior already defined by milestone tickets `04`-`07` and dependency spec `01` (MRVC). Coverage is cross-cutting: tests prove shared registry contract behavior remains stable when unrelated refactors occur.
- **Constraints:** Tests MUST assert externally observable behavior only (HTTP status/body or service return values and persisted manifest state), not private implementation details. The suite MUST include at least backend pytest coverage. Frontend tests are required only when behavior cannot be fully proven at API/service layer.
- **Assumptions:** Existing contracts from completed tickets `04`, `05`, `06`, and `07` are authoritative and must be reused, not redefined.
- **Scope:** New test files in existing repo test layout under `asset_generation/web/backend/tests`, `asset_generation/python/tests`, and optionally `asset_generation/web/frontend` tests.

#### 2. Acceptance Criteria
- **ATRAD-F1.1:** At least one deterministic test verifies registry write followed by read reflects persisted mutation for a contract-relevant field used by tickets `04`-`07`.
- **ATRAD-F1.2:** At least one deterministic negative test verifies invalid mutation request does not alter persisted registry state.
- **ATRAD-F1.3:** All tests introduced by this ticket map to named ATRAD requirement IDs in comments or test IDs for traceability.

#### 3. Risk & Ambiguity Analysis
- Existing tests in `04`-`07` may overlap; this ticket must avoid duplicate-value tests that only restate identical assertions without cross-cutting coverage intent.
- Over-coupling to exact error strings can cause brittle failures; status/reason-category assertions are preferred unless strings are contractually fixed.
- Cross-layer drift risk exists if only UI tests are written; backend/service baseline coverage is mandatory.

#### 4. Clarifying Questions
- No open questions for this requirement.

### Requirement ATRAD-F2 — Allowlist/path-rejection contract must stay enforced

#### 1. Spec Summary
- **Description:** The suite MUST verify that registry/model loading paths outside canonical allowlist roots are rejected deterministically and do not mutate state or leak host path details.
- **Constraints:** Test vectors MUST include plain traversal and encoded traversal/path-injection classes already covered by ticket `06` contract direction. Assertions MUST check deterministic rejection class (for example `400`/`403` class expected by router contract) and no permissive fallback.
- **Assumptions:** Canonical roots and jail semantics from `06_editor_load_existing_models_allowlist` remain authoritative.
- **Scope:** Backend router/service tests are mandatory. Frontend API-client tests are optional unless UI-only error-surfacing contract needs reinforcement.

#### 2. Acceptance Criteria
- **ATRAD-F2.1:** At least one test rejects a path outside allowlisted roots and asserts no state mutation side effects.
- **ATRAD-F2.2:** At least one test rejects traversal/injection form (`..`, encoded traversal, mixed separators, or equivalent) with deterministic failure classification.
- **ATRAD-F2.3:** Rejection payload assertions confirm non-leaky behavior (no host absolute path or stack trace content in user-facing message fields).

#### 3. Risk & Ambiguity Analysis
- URL/path normalization differences between client and backend can hide bypasses; tests should run at the enforcing layer (backend) for security-critical vectors.
- Overly broad exception handling may collapse security failures into generic 500 responses; tests should pin expected contract class.
- If fixture state is invalid, failures may misattribute cause; test setup must isolate path-validation from unrelated schema errors.

#### 4. Clarifying Questions
- No open questions for this requirement.

### Requirement ATRAD-F3 — Draft entries excluded from default game-pool reader

#### 1. Spec Summary
- **Description:** The suite MUST enforce that default game-pool/spawn-eligible readers do not return draft entries unless explicitly requested by a non-default path. This guards regression of ticket `04` draft/in-use gating.
- **Constraints:** Tests MUST verify default reader behavior, not merely UI filtering. If an optional explicit include-draft mode exists, it must be asserted separately and must not alter default behavior.
- **Assumptions:** Default "game pool" corresponds to spawn-eligible or equivalent runtime-facing registry consumer semantics from `04`/`05`.
- **Scope:** Backend/service tests for spawn-eligible/default consumer are required; frontend-only assertions are insufficient.

#### 2. Acceptance Criteria
- **ATRAD-F3.1:** Given mixed draft and in-use versions in one family, default game-pool reader returns only in-use non-draft entries.
- **ATRAD-F3.2:** Given only draft versions available, default game-pool reader returns empty or fallback behavior exactly as defined by upstream contract, never draft leakage.
- **ATRAD-F3.3:** Test assertions explicitly prove draft exclusion is contract behavior (not incidental fixture artifact).

#### 3. Risk & Ambiguity Analysis
- Confusion between "in_use" and slot-based selection can produce false positives; tests must bind to the contract exposed by current default reader.
- Fallback behavior (empty vs legacy default) differs by consumer; this ticket must reuse existing contract per dependency ticket instead of redefining it.
- Regression risk is high if only positive-path coverage exists; negative mixed-state fixtures are required.

#### 4. Clarifying Questions
- No open questions for this requirement.

### Requirement ATRAD-F4 — Delete invariants regression suite (from ticket `07`)

#### 1. Spec Summary
- **Description:** The suite MUST include deterministic delete-invariant coverage pulled from `07_editor_delete_draft_and_in_use_models`: one blocked invariant case and one allowed delete case with valid post-state.
- **Constraints:** Required minimum scenarios:
  1) blocked deletion when deleting sole in-use version (or equivalent guarded invariant),
  2) allowed deletion when invariant is satisfiable (for example non-sole in-use), followed by post-delete state checks.
  Repeated stale-target delete behavior should be asserted for determinism where feasible.
- **Assumptions:** Status taxonomy from `07` (including invariant conflict class) remains authoritative.
- **Scope:** Backend delete contract tests are mandatory. Frontend confirmation tests are optional unless backend cannot encode the behavior under test.

#### 2. Acceptance Criteria
- **ATRAD-F4.1:** Blocked invariant scenario returns deterministic failure class and leaves registry/filesystem state unchanged.
- **ATRAD-F4.2:** Allowed delete scenario succeeds and resulting registry state has no stale references to removed version in guarded structures.
- **ATRAD-F4.3:** At least one post-success read assertion proves invariant-preserving final state.
- **ATRAD-F4.4:** At least one stale-target repeat delete assertion verifies deterministic second-call behavior (for example not-found/stale rejection with no extra side effects).

#### 3. Risk & Ambiguity Analysis
- Testing only blocked cases may miss over-restrictive regressions; testing only allowed cases may miss safety regressions. Both are required.
- State cleanup expectations can vary by endpoint; assertions must target contract-defined outcomes only.
- Concurrent mutation edge cases may be hard to simulate; deterministic sequential stale-target checks are the conservative baseline.

#### 4. Clarifying Questions
- No open questions for this requirement.

### Requirement ATRAD-NF1 — Determinism, placement, and execution gate

#### 1. Spec Summary
- **Description:** Test artifacts must be deterministic, colocated with existing milestone layout, and runnable in CI/local without flake-sensitive timing assumptions.
- **Constraints:** New tests must live alongside existing conventions under `asset_generation/web` and `tests/` paths, avoid sleep-based timing dependence, and use stable fixtures with isolated registry state. Completion gate remains `timeout 300 ci/scripts/run_tests.sh` exit 0.
- **Assumptions:** Existing test harnesses for backend/frontend are available and can be extended without introducing new infrastructure.
- **Scope:** Non-functional obligations for test quality, maintainability, and pipeline integration.

#### 2. Acceptance Criteria
- **ATRAD-NF1.1:** New tests are placed in existing repo test layout and do not create ad-hoc parallel test frameworks.
- **ATRAD-NF1.2:** Tests are deterministic across repeated runs with fixed fixtures.
- **ATRAD-NF1.3:** Full project gate command is documented as mandatory completion evidence: `timeout 300 ci/scripts/run_tests.sh` exits 0.
- **ATRAD-NF1.4:** AC-to-test traceability is explicitly documented in ticket validation notes at later stages.

#### 3. Risk & Ambiguity Analysis
- Fixture reuse can introduce hidden coupling; test design should isolate each requirement with explicit setup state.
- Overly broad full-suite-only assertions can hide requirement gaps; targeted tests per requirement ID are required.
- Environment-specific failures outside ticket scope may block closure and must be recorded as blockers with ownership routing.

#### 4. Clarifying Questions
- No open questions for this requirement.

## Acceptance Criteria

- New tests live next to existing M21 test layout (`asset_generation/web` / `tests/` per repo convention).
- Covers at minimum: reject path outside allowlist; draft not in default “game pool” reader; one delete scenario from `07_editor_delete_draft_and_in_use_models`.
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

## Dependencies

- `01_spec_model_registry_draft_versions_and_editor_contract`
- `04_editor_ui_draft_status_for_exports` through `07_editor_delete_draft_and_in_use_models` (soft — tests can grow incrementally)

---

# Project: M9-ATRAD Cross-Cutting Contract Test Suite
**Description:** Add and harden automated contract coverage for registry API, allowlisted model loading, draft filtering, and delete invariants so refactors across tickets `04`-`07` cannot regress behavior.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Produce a formal, test-authoring-ready contract specification for ATRAD scope and AC traceability. | Spec Agent | Ticket AC, dependency tickets `01` and `04`-`07`, existing registry router/service contracts. | Specification block or spec artifact defining API invariants, reader semantics (draft vs in-use), allowlist rejection behavior, delete invariants, and exact test obligations for this ticket. | None | Every AC maps to explicit behavioral clauses and deterministic expected outcomes, including one required delete scenario from `07`. | Risk: ambiguity from "and/or frontend tests as appropriate"; assumption: backend contract tests are mandatory baseline, frontend tests only when UI-only behavior is not provable at API layer. |
| 2 | Author primary deterministic tests for registry + allowlist + delete invariants per spec. | Test Designer Agent | Approved ATRAD spec, current backend test layout in `asset_generation/web/backend/tests`, relevant frontend test layout if required by spec. | New/updated primary tests that fail when contract regresses and pass on compliant implementation; includes path-outside-allowlist rejection, draft exclusion from default game pool, and at least one delete invariant scenario. | 1 | New tests are deterministic, colocated by repo convention, and initially red only when true implementation gap exists; test IDs or comments map back to spec clauses. | Risk: fixture overlap with tests from tickets `04`-`07`; assumption: reuse existing fixtures to avoid duplicate setup and keep runtime bounded. |
| 3 | Expand adversarial and edge-case coverage to prevent bypass/regression vectors. | Test Breaker Agent | ATRAD primary tests, spec constraints, known failure classes (encoded traversal, malformed payloads, idempotency drift). | Additional adversarial tests stressing traversal encoding, malformed/ambiguous model references, and delete-state invariants under repeated operations. | 2 | Adversarial suite introduces meaningful failure modes not already covered and remains deterministic/non-flaky. | Risk: over-constraining implementation details; assumption: tests enforce externally observable contracts only (status, body shape, state invariants). |
| 4 | Implement or adjust backend/frontend behavior only where new ATRAD tests expose real contract gaps. | Implementation Generalist Agent | Failing ATRAD primary/adversarial tests, spec contract, existing registry API/service/UI code. | Minimal production code deltas that satisfy ATRAD suite without broad refactors; no behavior drift outside declared contract. | 2, 3 | All ATRAD tests pass locally; no unrelated regressions introduced in touched areas. | Risk: touching shared registry paths may affect prior milestone tickets; assumption: smallest-surface fixes and strict regression re-runs mitigate spillover. |
| 5 | Run static QA and full-suite validation with bounded commands and AC evidence mapping. | Acceptance Criteria Gatekeeper Agent | Passing implementation branch, ATRAD test evidence, ticket AC list. | Validation report in ticket showing targeted and full-suite command evidence; go/no-go against AC. | 4 | `timeout 300 ci/scripts/run_tests.sh` exits 0 and ticket ACs are explicitly traced to concrete tests/evidence. | Risk: unrelated suite instability blocking completion; assumption: if unrelated failure appears, document blocker with evidence and route ownership precisely. |

## Notes
- Tasks are sequential and independently executable once dependencies are satisfied.
- Contract tests are authoritative for behavior; implementation follows tests/spec, not vice versa.
- Keep scope constrained to cross-cutting ATRAD regression prevention, not feature expansion beyond `04`-`07`.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- AC evidence present for coverage scope in ticket-level criteria bullet 2: targeted backend ATRAD suite exists and passes at `asset_generation/web/backend/tests/test_registry_atrad_cross_cutting.py` with deterministic assertions for allowlist rejection, draft exclusion from default pool reader semantics, and delete invariants.
- AC evidence present for placement in ticket-level criteria bullet 1: tests are located under existing backend test layout (`asset_generation/web/backend/tests`) with no ad-hoc framework introduced.
- AC evidence present for ticket-level criteria bullet 3 / ATRAD-NF1.3: orchestrator execution of mandatory full gate command `timeout 300 ci/scripts/run_tests.sh` exited `0` (full suite passed).

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
  "ticket_path": "project_board/9_milestone_9_enemy_player_model_visual_polish/in_progress/09_automated_tests_registry_allowlist_delete.md",
  "next_step": "No further agent action required for this ticket; proceed with human workflow completion handling.",
  "notes": "Acceptance criteria are fully evidenced in Validation Status, including targeted ATRAD coverage and full-suite gate command pass."
}
```

## Status
Proceed

## Reason
All listed acceptance criteria now have explicit objective evidence in-ticket: required ATRAD backend coverage is documented and the mandatory full gate command `timeout 300 ci/scripts/run_tests.sh` is recorded as exit `0`; ticket is valid for COMPLETE state.
