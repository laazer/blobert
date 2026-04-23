# Backend Error Mapping Unification

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Complete

---

## Description

Remove repetitive `try/except` blocks across API routers by centralizing domain-exception to HTTP mapping.

## Acceptance Criteria

- [x] Shared mapper/decorator handles common domain exceptions consistently.
- [x] Registry/run/files/assets API routers reduce repeated exception mapping blocks.
- [x] HTTP status semantics remain unchanged for current consumers.
- [x] Structured logging is preserved or improved.
- [x] Regression tests verify status and payload parity for common failure paths.

## Dependencies

- Backend Registry Service Extraction and Router Thinning

## Execution Plan

# Project: Backend Error Mapping Unification
**Description:** Consolidate repeated backend router `try/except` HTTP translation into one shared error-mapping boundary so API behavior stays backward compatible while reducing duplication and drift risk.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Freeze unified error taxonomy and router-to-mapper delegation contract. | Spec Agent | This ticket, existing router exception handling in `asset_generation/web/backend/routers/assets.py`, `asset_generation/web/backend/routers/meta.py`, and related API routers; current domain exceptions raised by backend services and Python bridge layers | Functional/non-functional spec that defines canonical domain-exception classes, deterministic HTTP status/detail mapping, logging contract, and explicit router responsibilities after unification | None | Every acceptance criterion is mapped to deterministic runtime outcomes with no ambiguity in exception ownership or HTTP semantics | Assumes current API consumers depend on existing status semantics; if historical behavior conflicts across routers, spec must select conservative parity baseline and record rationale |
| 2 | Author RED regression tests proving failure-path status/payload parity under shared mapping. | Test Designer Agent | Approved spec from Task 1, existing backend contract tests, representative failure fixtures across registry/run/files/assets flows | New failing tests that encode expected status code + payload + core error-shape parity for common domain failures and malformed input/service exceptions | 1 | Tests fail on current duplicated handling and pass only when shared mapping preserves existing semantics | Risk of overfitting to incidental error message text; tests should prioritize contractually relevant payload shape and status semantics |
| 3 | Add adversarial RED coverage for edge and fallback exception paths. | Test Breaker Agent | Spec and Task 2 suite | Additional failing tests for unknown exception fallback behavior, mapping precedence conflicts, and logging-preservation expectations where contractually observable | 2 | Edge tests reveal inconsistent/unmapped branches and enforce fail-closed behavior for unmapped/unsafe exception cases | Assumes existing test harness can inject mapper-target exceptions deterministically; otherwise define fixture seam in tests without implementation leakage |
| 4 | Implement shared error-mapping helper/decorator and refactor targeted routers to delegate to it. | Implementation Backend Agent | Frozen spec, RED tests from Tasks 2-3, current router/service modules | Production code introducing shared mapper boundary and router refactors removing repeated blocks while preserving API contracts and logging quality | 3 | Duplicated per-router exception mapping is removed from active paths and all contract tests pass without API behavior regressions | Risk of accidental behavioral drift in status/detail wording; implementation must preserve externally visible semantics unless spec explicitly permits normalization |
| 5 | Validate quality gates and acceptance closure evidence. | Static QA Agent then Acceptance Criteria Gatekeeper Agent | Implementation diff, lints, test outputs, acceptance criteria list | QA + gatekeeper validation that all ACs have runtime-backed evidence and no unresolved regression risks remain | 4 | Required suites pass, touched-file lint checks are clean, and AC traceability to test evidence is explicit and complete | Assumes no hidden routers outside scoped APIs depend on copied mapping logic; if discovered, record as follow-on risk without silently expanding scope |

## Notes

- Dependency `13_backend_registry_service_extraction_and_router_thinning` is already completed (`done/`), so this ticket is not dependency-blocked at planning exit.
- In autonomous checkpoint mode, conservative assumption is to preserve existing HTTP semantics exactly unless the spec explicitly documents a safe normalization rule.

## Functional Specification

### Requirement R1 - Shared Error-Mapping Boundary

#### 1. Spec Summary
- **Description:** The backend exposes a single shared mapping boundary (helper, adapter, or decorator) that receives exceptions from router execution paths and deterministically returns the HTTP response contract for the caller.
- **Constraints:** Mapping logic must not be reimplemented independently inside each targeted router endpoint after unification.
- **Assumptions:** No assumptions.
- **Scope:** API routers for registry/run/files/assets flows covered by this ticket.

#### 2. Acceptance Criteria
- For every targeted router endpoint, domain-exception-to-HTTP translation executes through the shared mapping boundary rather than per-endpoint duplicated `try/except` translation blocks.
- The shared boundary supports deterministic handling for known mapped exception classes and deterministic fallback for unknown exceptions.
- Runtime behavior remains endpoint-compatible with pre-unification contracts (status code and response shape) for mapped failure paths.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Hidden exception translation branches may remain in router code and create drift.
- **Risk:** Router refactors may accidentally alter control flow and bypass mapping.
- **Ambiguity:** Exact implementation form (decorator vs callable helper) is intentionally open; behavior contract is fixed.

#### 4. Clarifying Questions
- None blocking. Conservative assumption: any eligible form is acceptable if all runtime contracts pass unchanged.

### Requirement R2 - Canonical Exception Taxonomy and Mapping Precedence

#### 1. Spec Summary
- **Description:** A canonical taxonomy defines which exception categories are mapped explicitly and in what precedence order when exceptions share inheritance relationships.
- **Constraints:** Specific exception mappings must take precedence over generic/base exception mappings. Mapping order must be stable and deterministic.
- **Assumptions:** Existing domain exceptions currently raised by backend services and Python bridge layers remain the source of truth for known failure types.
- **Scope:** Exceptions raised by service and bridge layers that propagate to targeted routers.

#### 2. Acceptance Criteria
- Mapping rules define a deterministic precedence model that prevents ambiguous matches.
- When a raised exception matches both a specific and generic mapping, the specific mapping is selected.
- Unmapped exceptions follow fallback behavior defined in R4.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Inheritance-based overlap can produce inconsistent status mapping if precedence is implicit.
- **Risk:** Future exception classes added without mapping can silently degrade client-facing behavior.
- **Ambiguity:** Exact list of exception classes is derived from observed service contracts and must be explicitly enumerated by implementation documentation/comments or mapping table artifact.

#### 4. Clarifying Questions
- None blocking. Conservative assumption: preserve current route-visible status semantics where class-level overlaps exist.

### Requirement R3 - Router Delegation Contract

#### 1. Spec Summary
- **Description:** Targeted routers are responsible for transport concerns (request parsing, dependency wiring, response return), while the shared mapping boundary owns exception-to-HTTP translation.
- **Constraints:** Routers must not embed independent status/detail translation for mapped domain exceptions once delegation is in place.
- **Assumptions:** Dependency extraction from ticket 13 remains available and stable.
- **Scope:** `assets`, `meta`, registry-adjacent, and run/files routes in scope of this ticket.

#### 2. Acceptance Criteria
- Router failure handling for mapped exceptions delegates to shared boundary.
- Endpoint signatures, route paths, and successful-response behavior remain unchanged by this refactor.
- Endpoint failure response status and payload shape remain parity-compatible with current consumers.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Over-thinning routers can accidentally shift non-error responsibilities into mapper layer.
- **Risk:** Scope creep into unrelated routers can raise regression exposure.
- **Ambiguity:** "Reduce repeated blocks" is interpreted as removing duplication in active code paths; inert/dead code is out of scope.

#### 4. Clarifying Questions
- None blocking. Conservative assumption: limit refactor strictly to listed API families and observed duplicated mappings.

### Requirement R4 - Fallback and Safety Contract for Unknown Exceptions

#### 1. Spec Summary
- **Description:** Exceptions not explicitly mapped must resolve through a fail-closed fallback contract that is safe for external clients and useful for internal diagnostics.
- **Constraints:** Client-facing payload for unknown exceptions must avoid leaking sensitive stack or environment internals.
- **Assumptions:** Internal logs are available to preserve diagnostic detail.
- **Scope:** All unhandled exceptions escaping targeted router service calls.

#### 2. Acceptance Criteria
- Unknown/unmapped exceptions return a deterministic internal-error HTTP status and safe generic client detail.
- Internal structured logs capture full exception context sufficient for debugging.
- Fallback behavior is consistent across all routers migrated to the shared boundary.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Exposing raw exception detail may leak internals.
- **Risk:** Over-generic fallback can reduce debuggability unless logs preserve detail.
- **Ambiguity:** Exact generic detail string may vary as long as it remains safe and stable enough for consumers.

#### 4. Clarifying Questions
- None blocking. Conservative assumption: preserve existing safe detail text when already generic; otherwise normalize to safe generic text.

### Requirement R5 - HTTP Contract Parity for Existing Consumers

#### 1. Spec Summary
- **Description:** Refactor must preserve current externally visible semantics for common failure paths consumed by clients.
- **Constraints:** Parity is evaluated on contractually relevant fields: HTTP status code and core error payload shape/keys. Incidental wording differences should be avoided unless needed for safety.
- **Assumptions:** Current behavior is considered baseline truth for in-scope endpoints.
- **Scope:** Common failure paths in registry/run/files/assets APIs.

#### 2. Acceptance Criteria
- For each mapped common failure path, status code is unchanged relative to baseline behavior.
- Payload structure remains compatible (required keys and semantic meaning unchanged).
- Any intentional normalization is explicitly documented and shown to be non-breaking.

#### 3. Risk & Ambiguity Analysis
- **Risk:** String-level assertions in tests can overconstrain harmless wording differences.
- **Risk:** Behavior drift across endpoints may be introduced during consolidation.
- **Ambiguity:** "Common failure paths" means documented and currently exercised domain failure scenarios, not exhaustive theoretical exceptions.

#### 4. Clarifying Questions
- None blocking. Conservative assumption: preserve exact status semantics; keep payload-shape compatibility as the minimum client contract.

### Requirement R6 - Structured Logging Preservation/Improvement

#### 1. Spec Summary
- **Description:** Error handling continues to emit structured logs for failure events, with route and exception context preserved or enhanced after unification.
- **Constraints:** Logging must not degrade from structured to unstructured-only messages for mapped/fallback failures.
- **Assumptions:** Existing logging framework and sinks remain unchanged.
- **Scope:** Logs emitted during mapped and fallback failure handling for targeted routers.

#### 2. Acceptance Criteria
- Error events retain machine-parseable context fields (exception category plus route/operation context).
- Unknown exception fallback logs include sufficient detail to diagnose root cause internally.
- Refactor does not remove existing critical error logging events from in-scope failure paths.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Centralization may accidentally drop route-specific context fields.
- **Risk:** Logging changes may pass HTTP tests while reducing observability.
- **Ambiguity:** Exact field names may differ if semantics are preserved and at least equivalent context remains available.

#### 4. Clarifying Questions
- None blocking. Conservative assumption: maintain existing keys when feasible; additive fields are allowed.

## Non-Functional Specification

### Requirement N1 - Determinism and Maintainability

#### 1. Spec Summary
- **Description:** Error mapping outcomes must be deterministic for a given exception type and endpoint context, with one authoritative mapping location to reduce drift.
- **Constraints:** No duplicate active mapping tables across targeted routers.
- **Assumptions:** Standard Python exception dispatch semantics apply.
- **Scope:** Shared mapper boundary and in-scope routers.

#### 2. Acceptance Criteria
- Mapping decisions are reproducible and order-stable.
- Refactor reduces duplicated translation logic in targeted routers.
- New exception mappings can be added in one place without route-level copy edits.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Partial migration leaves dual sources of truth.
- **Ambiguity:** "One place" allows helper decomposition but requires one authoritative mapping contract.

#### 4. Clarifying Questions
- None blocking.

### Requirement N2 - Backward Compatibility and Safety

#### 1. Spec Summary
- **Description:** Changes must be backward compatible for current clients and must not increase information leakage in error responses.
- **Constraints:** No breaking changes to route signatures or expected error status classes for common failures.
- **Assumptions:** Current clients rely on status semantics and baseline payload shape.
- **Scope:** External HTTP behavior for in-scope routes.

#### 2. Acceptance Criteria
- No new unsafe internal details are exposed in client error payloads.
- Existing client integrations remain valid for common failure scenarios.
- Any intentional behavior adjustment is documented as non-breaking and safety-motivated.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Minor payload drift can still break strict clients.
- **Risk:** Safety hardening can inadvertently alter status semantics.
- **Ambiguity:** Compatibility focuses on observable contract, not internal stack traces/log wording.

#### 4. Clarifying Questions
- None blocking.

### Requirement N3 - Testability and Traceability

#### 1. Spec Summary
- **Description:** Specification must map directly to behavioral tests that prove runtime contracts for mapped and fallback failures.
- **Constraints:** Tests must validate executable behavior, not prose or comments.
- **Assumptions:** Existing backend test harness can trigger representative service-layer exceptions.
- **Scope:** Test Designer and Test Breaker handoff for this ticket.

#### 2. Acceptance Criteria
- Each acceptance criterion in ticket-level AC has at least one corresponding runtime-verifiable test condition.
- Tests assert status semantics and payload-shape contract for representative mapped failures.
- Tests include at least one unknown-exception fallback behavior assertion per mapped boundary path class.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Overreliance on message-string equality can create brittle tests.
- **Risk:** Missing fallback-path coverage may hide critical regressions.
- **Ambiguity:** Logging assertions should focus on semantic presence of structured context, not exact formatting.

#### 4. Clarifying Questions
- None blocking.

## Acceptance Criteria to Requirement Traceability

- AC1 Shared mapper/decorator consistency -> R1, R2, R3, N1
- AC2 Router duplication reduction -> R3, N1
- AC3 HTTP status semantics unchanged -> R5, N2
- AC4 Structured logging preserved/improved -> R6, N2
- AC5 Regression tests for status/payload parity -> R5, N3, R4

## Explicit Out-of-Scope

- Introducing new public API endpoints or changing route signatures.
- Rewriting non-targeted routers that do not currently participate in duplicated mapping.
- Broad logging framework replacement.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- AC1 (`Shared mapper/decorator handles common domain exceptions consistently`): **Evidence present**. Shared boundary exists in `asset_generation/web/backend/services/error_mapping.py` (`map_exception_to_http`, `ErrorMappingRule`), and in-scope routers call it from exception paths (`asset_generation/web/backend/routers/registry.py`, `asset_generation/web/backend/routers/assets.py`, `asset_generation/web/backend/routers/run.py`).
- AC2 (`Registry/run/files/assets API routers reduce repeated exception mapping blocks`): **Evidence present (scoped closure)**. `registry`, `assets`, and `run` continue delegating domain/service exception translation through `map_exception_to_http`; `files` router (`asset_generation/web/backend/routers/files.py`) is transport/path-validation only and raises direct `HTTPException` for request-shape/path guard outcomes, with no duplicated domain-exception translation block to refactor under this ticket scope.
- AC3 (`HTTP status semantics remain unchanged for current consumers`): **Evidence present for covered paths**. `asset_generation/web/backend/tests/test_backend_error_mapping_behavior.py` and `asset_generation/web/backend/tests/test_m901_12_registry_delete_router_service_delegation_contract.py` assert preserved status/detail behavior for mapped failures (e.g., 503 import-unavailable, 403 forbidden target class, 404 unknown target, 409 conflicts, 400 validation failures).
- AC4 (`Structured logging is preserved or improved`): **Evidence present**. Structured fallback logging assertions now cover assets, registry, and run routes in `asset_generation/web/backend/tests/test_backend_error_mapping_behavior.py` via `test_unknown_failure_logs_structured_context_for_assets_fallback`, `test_unknown_failure_logs_structured_context_for_registry_fallback`, and `test_unknown_failure_logs_structured_context_for_run_fallback` (asserting `route` and `exception_type` structured fields).
- AC5 (`Regression tests verify status and payload parity for common failure paths`): **Evidence present**. Targeted suite pass: `asset_generation/web/backend/tests/test_backend_error_mapping_behavior.py asset_generation/web/backend/tests/test_m901_12_registry_delete_router_service_delegation_contract.py asset_generation/web/backend/tests/test_m901_11_registry_router_path_policy_delegation_contract.py` -> `29 passed`.
- Referenced backend import-adapter contract suite stabilized: `asset_generation/web/backend/tests/test_m901_10_backend_python_import_adapter_contract.py` -> `12 passed` after `python_bridge` bootstrap fallback compatibility fix for minimal-root test environments.
- Integration evidence summary: no remaining targeted-suite failures for this ticket scope; acceptance criteria closure is explicitly evidenced.

## Blocking Issues
- None.

## Escalation Notes
- Gatekeeper re-evaluation completed against ticket-local evidence. AC1-AC5 each map to explicit Validation Status evidence (implementation locations, scoped routing rationale, regression/status parity tests, and structured logging assertions), with no unresolved acceptance-criteria gaps.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/done/14_backend_error_mapping_unification.md",
  "stage": "COMPLETE",
  "revision": 8,
  "required_fixes_or_evidence": [],
  "targeted_test_commands": [],
  "deliverable": "Human acknowledgement and downstream milestone/project-board bookkeeping."
}
```

## Status
Proceed

## Reason
All AC1-AC5 have explicit, criterion-level evidence in Validation Status with no unresolved blocking gaps; workflow state is now defensibly complete and ready for human finalization/bookkeeping.
