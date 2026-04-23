# Backend-Python Import Adapter

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Replace per-router `sys.path` mutation and repeated Blender-stub bootstrap with a single adapter module. This creates one reliable boundary for importing asset-generation services during the transition to a unified `blobert_asset_gen` package architecture.

Target duplication:
- `asset_generation/web/backend/routers/registry.py`
- `asset_generation/web/backend/routers/meta.py`
- `asset_generation/web/backend/routers/assets.py`

## Acceptance Criteria

- [ ] New adapter module centralizes Python root path injection and Blender stub initialization.
- [ ] Routers stop mutating `sys.path` directly.
- [ ] Registry/meta/assets routes import Python modules through adapter only.
- [ ] Adapter exposes package-root resolution abstraction that can switch from `asset_generation/python/src` to `asset_generation/python/blobert_asset_gen` without router changes.
- [ ] Existing backend tests pass without route behavior regressions.
- [ ] Adapter has focused tests for import/bootstrap behavior in test environment.

## Dependencies

- None (recommended first ticket for follow-on consolidation work).

## Execution Plan

# Project: Backend-Python Import Adapter
**Description:** Replace duplicated router-local Python import bootstrap logic with one backend adapter boundary that supports current and future asset-generation package roots without route-level changes.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Freeze adapter contract and migration invariants for router import/bootstrap behavior. | Spec Agent | Ticket AC, existing router files (`registry.py`, `meta.py`, `assets.py`), current bootstrap behavior in backend service layer | Written specification defining adapter API, bootstrap lifecycle, error semantics, logging expectations, and package-root resolution abstraction (`src` vs `blobert_asset_gen`) | None | Spec explicitly maps each acceptance criterion to observable runtime behaviors and defines backward-compatible router contract with no endpoint signature changes | Assumes current duplicated setup behavior is functionally equivalent across target routers; risk of hidden router-specific side effects must be called out and covered in test requirements |
| 2 | Author primary behavioral tests for adapter and router integration seams. | Test Designer Agent | Frozen spec from Task 1, backend test harness, route fixtures/mocks | RED tests for adapter bootstrap/idempotency/import path resolution plus router usage contracts (no direct `sys.path` mutation in routers) | 1 | Tests fail for missing/incorrect adapter behavior and validate runtime outcomes rather than prose; coverage includes import success, import failure, fallback/selection behavior, and startup sequencing | Assumes test harness can isolate import side effects and environment mutations; risk of brittle global interpreter state if tests are not sandboxed |
| 3 | Add adversarial and edge-case tests for import/bootstrap failure taxonomy. | Test Breaker Agent | Spec and Task 2 tests | Additional RED tests covering malformed root config, missing module trees, repeated bootstrap calls, concurrent route initialization, and fail-closed behavior | 2 | Edge tests demonstrate meaningful gaps, then lock conservative expected behavior for ambiguous failure modes | Risk that concurrency expectations are environment-dependent; assumptions must be checkpointed and expressed as deterministic contracts |
| 4 | Implement backend adapter module and migrate routers to consume it exclusively. | Implementation Backend Agent | Green/RED test suite from Tasks 2-3, spec contract, existing backend router/service code | New shared adapter module (e.g., `backend/services/python_bridge.py`), migrated routers without local bootstrap duplication, compatibility-safe package-root resolver abstraction | 3 | All adapter and router tests pass; routers no longer mutate `sys.path` directly; imports flow only through adapter boundary; API endpoints unchanged | Risk of import-cycle regressions between backend services and router modules; assumption that adapter can initialize stubs once without behavior drift |
| 5 | Validate regression safety, static quality, and acceptance-criteria traceability for handoff. | Static QA Agent then Acceptance Criteria Gatekeeper Agent | Implemented code and full test outputs | Verification report with command-backed evidence for backend tests, adapter-focused tests, lint/static checks, and AC-by-AC closure | 4 | Required test/static suites pass; no endpoint regressions; each AC has concrete executable evidence; ticket ready for downstream implementation/integration progression | Assumes CI/local environment has consistent Python path/tooling; risk that omitted integration commands leave hidden regressions, which must be marked as blocking if unverifiable |

## Notes

- Keep public API endpoints unchanged.
- This ticket is the migration seam for package convergence; all follow-on tickets should consume bridge APIs rather than hardcoding import roots.

---

## Functional and Non-Functional Specification

### Requirement R1 - Shared Adapter Boundary and Router Migration

#### 1. Spec Summary
- **Description:** A single backend adapter module shall own Python import bootstrap behavior currently duplicated in `registry.py`, `meta.py`, and `assets.py`. Routers must consume adapter APIs only and stop mutating `sys.path` directly.
- **Constraints:** Endpoint paths, HTTP methods, request/response schemas, status codes, and route registration behavior must remain unchanged. Router modules may import adapter symbols but must not contain route-local Python-root injection or Blender-stub bootstrap logic after migration.
- **Assumptions:** Adapter module path is under backend service layer (for example `asset_generation/web/backend/services/python_bridge.py`) and is treated as the sole import/bootstrap entrypoint for target routers.
- **Scope:** `asset_generation/web/backend/routers/registry.py`, `asset_generation/web/backend/routers/meta.py`, `asset_generation/web/backend/routers/assets.py`, and one new backend service adapter module.

#### 2. Acceptance Criteria
- AC-R1.1: Exactly one adapter module exists that exposes runtime import/bootstrap entrypoints used by all three target routers.
- AC-R1.2: `registry.py`, `meta.py`, and `assets.py` contain no direct `sys.path` mutation statements after migration.
- AC-R1.3: `registry.py`, `meta.py`, and `assets.py` invoke adapter APIs for Python-side imports/bootstrap instead of duplicating local setup logic.
- AC-R1.4: Router behavior remains backward-compatible at runtime (same observable route contracts and startup behavior).
- AC-R1.5: If adapter bootstrap cannot establish required import prerequisites, the resulting failure surface is deterministic and routed through adapter-defined error semantics rather than route-local ad hoc exceptions.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Hidden router-specific side effects in current duplicated setup could be lost when consolidating.
- **Impact:** One or more routes may fail to initialize or may import wrong modules at runtime.
- **Mitigation:** Adapter contract explicitly includes per-router parity requirement and shared bootstrap sequencing guarantees.
- **Risk:** Consolidation can accidentally create circular imports between routers and services.
- **Impact:** Runtime import-time exceptions and startup failure.
- **Mitigation:** Adapter remains dependency leaf for routers (routers import adapter; adapter does not import routers).

#### 4. Clarifying Questions
- None. Conservative assumption logged via checkpoint protocol.

### Requirement R2 - Python Root Resolution Abstraction

#### 1. Spec Summary
- **Description:** Adapter shall provide a package-root resolution abstraction capable of selecting current root (`asset_generation/python/src`) and future root (`asset_generation/python/blobert_asset_gen`) without router-level code changes.
- **Constraints:** Root resolution must be deterministic, centrally defined, and externally configurable only through adapter-approved configuration inputs. Routers must not branch on root selection.
- **Assumptions:** Current environment defaults to `asset_generation/python/src` unless an explicit adapter-level override selects the future package root.
- **Scope:** Adapter root-resolution logic and its call sites in target routers.

#### 2. Acceptance Criteria
- AC-R2.1: Adapter exposes a root-resolution API/abstraction that returns exactly one active Python package root for the process.
- AC-R2.2: Root-resolution supports both candidate roots (`.../python/src` and `.../python/blobert_asset_gen`) and can switch between them without router file edits.
- AC-R2.3: Resolution precedence is deterministic and documented in adapter contract (for example: explicit override > detected valid path > conservative default).
- AC-R2.4: If no valid root is resolvable, adapter fails closed with explicit error classification instead of silently proceeding with partial setup.
- AC-R2.5: Resolved root is reused across adapter import operations in the same process lifecycle unless adapter is explicitly reconfigured.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Multiple valid roots present simultaneously may create ambiguous module selection.
- **Impact:** Wrong module tree imported, causing subtle behavior divergence.
- **Mitigation:** Contract requires explicit deterministic precedence and fail-closed ambiguity handling.
- **Risk:** Path probing that mutates global state before validation.
- **Impact:** Polluted `sys.path` with invalid entries.
- **Mitigation:** Validate candidate root before committing path injection.

#### 4. Clarifying Questions
- None.

### Requirement R3 - Bootstrap Lifecycle and Idempotency

#### 1. Spec Summary
- **Description:** Adapter shall own Blender-stub initialization and Python import bootstrap lifecycle with idempotent behavior across repeated route/module access in the same process.
- **Constraints:** Bootstrap side effects must not multiply across repeated calls; repeated invocations must be safe and behaviorally equivalent to first successful initialization.
- **Assumptions:** Backend may trigger adapter bootstrap from multiple routers within one process and expects consistent shared state.
- **Scope:** Adapter initialization entrypoint, internal lifecycle flags/state, and router invocation semantics.

#### 2. Acceptance Criteria
- AC-R3.1: First successful adapter bootstrap performs required initialization steps exactly once per process lifecycle.
- AC-R3.2: Subsequent bootstrap calls are no-op or equivalent idempotent passes with no duplicate side effects (no repeated path insertion, no repeated conflicting stub init).
- AC-R3.3: Adapter bootstrap sequencing is explicit and stable: resolve root -> validate -> configure import path -> initialize stubs -> import requested modules.
- AC-R3.4: Failures in any bootstrap phase produce deterministic error outcomes and do not leave adapter in a false-success state.
- AC-R3.5: Recovery semantics are defined: after a failed bootstrap, subsequent attempts either retry from a clean state or deterministically re-emit prior failure based on contract.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Partial initialization can leave global interpreter state inconsistent.
- **Impact:** Non-deterministic route behavior depending on call order.
- **Mitigation:** Contract requires explicit failure-state handling and deterministic retry/re-emit semantics.
- **Risk:** Concurrent bootstrap calls may race on global state.
- **Impact:** Duplicate writes or inconsistent flags.
- **Mitigation:** Adapter contract requires concurrency-safe idempotency semantics suitable for multi-route initialization.

#### 4. Clarifying Questions
- None.

### Requirement R4 - Error Taxonomy and Observability Contract

#### 1. Spec Summary
- **Description:** Adapter shall classify and surface import/bootstrap failures through a stable, testable taxonomy so callers can differentiate root-resolution failures, missing module trees, bootstrap initialization failures, and import failures.
- **Constraints:** Errors must be actionable and deterministic. Sensitive filesystem details should not be leaked beyond what existing backend diagnostics already permit.
- **Assumptions:** Existing backend error handling will consume adapter-raised exceptions or adapter-returned error envelopes without route API contract changes.
- **Scope:** Adapter error classes/envelopes, logging/emitted diagnostics, and router integration points.

#### 2. Acceptance Criteria
- AC-R4.1: Adapter defines distinct failure categories for at least: unresolved root, invalid root layout, stub/bootstrap initialization failure, and target module import failure.
- AC-R4.2: Failure category emitted for a given root cause is stable across runs for the same inputs.
- AC-R4.3: Router integration relies on adapter failure signals; routers do not reclassify failures via duplicated local heuristics.
- AC-R4.4: Error text/metadata includes enough context for debugging (which phase failed) while preserving existing security constraints and not exposing unnecessary internals.
- AC-R4.5: Adapter logs/diagnostic events (if present in backend conventions) are emitted once per failure event and are not duplicated by each router.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Overly broad catch-all errors can hide true failure mode.
- **Impact:** Hard-to-debug regressions and weak testability.
- **Mitigation:** Contract enforces phase-specific taxonomy and deterministic mapping.
- **Risk:** Excessive logging on repeated failures.
- **Impact:** noisy diagnostics and possible operational confusion.
- **Mitigation:** Idempotent failure reporting policy with one event per concrete failure instance.

#### 4. Clarifying Questions
- None.

### Requirement R5 - Verification and Non-Functional Constraints

#### 1. Spec Summary
- **Description:** Ticket completion requires executable evidence that adapter centralization is behavior-preserving for backend routes and that new adapter-specific contracts are covered by focused tests.
- **Constraints:** Verification must be behavior-based (runtime assertions), not prose-based tests. No unnecessary documentation artifacts are created for this ticket.
- **Assumptions:** Existing backend test harness can run route-level regression checks and adapter-focused unit/integration tests in local/CI environment.
- **Scope:** Backend test suite updates and quality gates for adapter migration.

#### 2. Acceptance Criteria
- AC-R5.1: Existing backend tests covering registry/meta/assets route behavior pass after migration with no route behavior regression attributable to adapter change.
- AC-R5.2: Focused adapter tests exist and validate at minimum: root resolution selection, bootstrap idempotency, successful import path flow, and deterministic failure taxonomy behavior.
- AC-R5.3: Adapter tests isolate global interpreter side effects so tests are repeatable and independent (no test-order dependence).
- AC-R5.4: Route modules are statically free of direct `sys.path` mutation and duplicate bootstrap snippets.
- AC-R5.5: Specification produces complete, testable contracts for downstream Test Designer and Implementation agents without requiring additional requirement interpretation.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Tests that only check source text instead of runtime behavior can pass while runtime contract fails.
- **Impact:** False confidence and production regressions.
- **Mitigation:** Require executable behavior assertions for adapter lifecycle and route integration outcomes.
- **Risk:** Test isolation around global import state may be brittle.
- **Impact:** flaky tests and non-deterministic CI results.
- **Mitigation:** Explicit non-functional requirement for sandboxed/resettable interpreter state in adapter test design.

#### 4. Clarifying Questions
- None.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
9

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: Passed (`uv run --project /Users/jacobbrandt/workspace/blobert/asset_generation/python --directory /Users/jacobbrandt/workspace/blobert python -m pytest asset_generation/python/tests/ci/test_import_standardization_behavior.py::test_import_backend_registry_pipeline_after_canonical_path_injection -q` => `1 passed in 0.32s`; `uv run --project /Users/jacobbrandt/workspace/blobert/asset_generation/python --directory /Users/jacobbrandt/workspace/blobert/asset_generation/web/backend python -m pytest tests/test_m901_10_backend_python_import_adapter_contract.py -q` => `12 passed in 0.35s`; `uv run --project /Users/jacobbrandt/workspace/blobert/asset_generation/python --directory /Users/jacobbrandt/workspace/blobert/asset_generation/web/backend python -m pytest tests/test_meta_router.py -q` => `2 passed in 0.48s`; `uv run --project /Users/jacobbrandt/workspace/blobert/asset_generation/python --directory /Users/jacobbrandt/workspace/blobert/asset_generation/web/backend python -m pytest tests/test_assets_router.py -q` => `38 passed in 0.55s`; `uv run --project /Users/jacobbrandt/workspace/blobert/asset_generation/python --directory /Users/jacobbrandt/workspace/blobert/asset_generation/web/backend python -m pytest tests/test_registry_load_existing_allowlist_router.py -q` => `16 passed in 0.49s`)
- Static QA: Passed (`ReadLints` on `asset_generation/web/backend/main.py`, `asset_generation/web/backend/routers/meta.py`, `asset_generation/web/backend/routers/assets.py`, `asset_generation/web/backend/routers/registry.py`, and `asset_generation/web/backend/services/python_bridge.py` reported no linter errors)
- Integration: Passed (ticket now resides under `project_board/**/done/` and completion-state alignment requirement is satisfied; AC closure evidence remains backed by adapter-focused and router regression suites plus static QA)

## Blocking Issues
- None.

## Escalation Notes
- Gatekeeper closure approved: all listed acceptance criteria have explicit evidence in validation artifacts, and folder-stage consistency now satisfies workflow enforcement.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/done/10_backend_python_import_adapter.md",
  "implementation_summary": [
    "Added backend adapter module `services/python_bridge.py` to centralize root resolution, idempotent sys.path bootstrap, Blender stub bootstrap, and module import taxonomy.",
    "Migrated `routers/registry.py`, `routers/meta.py`, and `routers/assets.py` to import python-side modules exclusively through adapter APIs.",
    "Removed direct per-router python bootstrap duplication and switched `main.py` to initialize through shared adapter."
  ],
  "validation_evidence": [
    "uv run --project /Users/jacobbrandt/workspace/blobert/asset_generation/python --directory /Users/jacobbrandt/workspace/blobert/asset_generation/web/backend python -m pytest tests/test_m901_10_backend_python_import_adapter_contract.py -q",
    "uv run --project /Users/jacobbrandt/workspace/blobert/asset_generation/python --directory /Users/jacobbrandt/workspace/blobert/asset_generation/web/backend python -m pytest tests/test_meta_router.py -q",
    "uv run --project /Users/jacobbrandt/workspace/blobert/asset_generation/python --directory /Users/jacobbrandt/workspace/blobert/asset_generation/web/backend python -m pytest tests/test_assets_router.py -q",
    "uv run --project /Users/jacobbrandt/workspace/blobert/asset_generation/python --directory /Users/jacobbrandt/workspace/blobert/asset_generation/web/backend python -m pytest tests/test_registry_load_existing_allowlist_router.py -q",
    "ReadLints on touched backend adapter/router files"
  ]
}
```

## Status
Proceed

## Reason
All acceptance criteria have explicit evidence via adapter-focused tests, backend router regression suites, and clean static QA, and the ticket now satisfies required `done/` folder-to-`COMPLETE` stage consistency; proceed with human closeout.
