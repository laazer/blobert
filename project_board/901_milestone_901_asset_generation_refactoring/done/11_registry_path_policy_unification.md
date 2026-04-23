# Registry Path Policy Unification

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Consolidate all registry path normalization and allowlist enforcement into shared package service modules so API routes do not carry a second security policy implementation.

Target overlap:
- `asset_generation/web/backend/routers/registry.py` (`_normalize_registry_relative_glb_path`)
- `blobert_asset_gen.services.registry` (or transitional `asset_generation/python/src/model_registry/service.py`) allowlist/validation logic

## Acceptance Criteria

- [ ] Path canonicalization/validation API is exposed from package service layer.
- [ ] API registry router delegates path checks to shared service API.
- [ ] Duplicated allowlist prefixes are removed from router.
- [ ] Traversal, encoding, extension, and forbidden path class tests pass through shared policy.
- [ ] No behavioral regression in existing registry endpoints.

## Dependencies

- Backend-Python Import Adapter

## Execution Plan

# Project: Registry Path Policy Unification
**Description:** Consolidate registry path canonicalization and allowlist enforcement into one shared Python service policy so backend routers delegate all path-security decisions through a single fail-closed contract.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Freeze unified registry path policy contract at the service layer. | Spec Agent | Ticket description/AC, current router helper `_normalize_registry_relative_glb_path`, current service allowlist/validation logic in `blobert_asset_gen.services.registry` (or transitional `asset_generation/python/src/model_registry/service.py`) | Functional + non-functional specification defining canonicalization, allowlist, traversal rejection, encoding handling, extension policy, forbidden class taxonomy, and router-to-service delegation contract | None | Spec defines one authoritative path-policy API and maps every listed path class (traversal/encoding/extension/forbidden) to deterministic outcomes with fail-closed semantics | Assumes transitional service path may still be active; spec must freeze migration-safe adapter surface so implementation can target either location without route contract drift |
| 2 | Author primary RED behavioral tests for shared policy and router delegation. | Test Designer Agent | Frozen spec from Task 1, backend router tests, Python service tests, current registry endpoint behavior | RED tests validating service policy API and router delegation for valid/invalid paths, canonicalization parity, allowlist enforcement, and regression-safe endpoint behavior | 1 | Tests fail when router reintroduces local policy or when service policy misclassifies protected path cases; assertions are runtime/behavioral (not prose) | Assumes current harness can isolate path normalization and encoded-input variants deterministically across backend and Python service layers |
| 3 | Add adversarial/edge RED tests for malformed encoded and bypass-style inputs. | Test Breaker Agent | Spec and Task 2 tests | Additional RED tests for double-encoding, mixed separator traversal, unicode/percent-encoding abuse, extension spoofing, and forbidden path-class bypass attempts | 2 | Edge tests expose realistic security gaps and lock strict expected behavior with deterministic outcomes | Risk of environment-specific path semantics (OS/pathlib/url decoding differences); assumptions must be checkpointed and resolved conservatively |
| 4 | Implement shared path policy API and migrate registry router to delegate exclusively. | Implementation Backend Agent | Approved RED suites (Tasks 2-3), frozen spec, current backend router/service modules | Service-layer canonicalization/validation API, router refactor removing `_normalize_registry_relative_glb_path` + duplicated allowlist constants, compatibility-preserving endpoint behavior | 3 | All policy decisions flow through service API, duplicated router policy removed, and all targeted tests pass without endpoint regression | Risk of subtle behavior drift in normalization order; implementation must preserve existing accepted paths unless spec explicitly tightens for security |
| 5 | Validate completion evidence, static quality, and AC traceability before downstream progression. | Static QA Agent then Acceptance Criteria Gatekeeper Agent | Implemented diff, full test command outputs, lints/static diagnostics | Verification artifact proving AC closure with command-backed evidence for service + backend tests and static QA, plus explicit no-regression claims | 4 | Required suites pass, security path classes are covered through shared policy tests, and gatekeeper can map every AC to executable evidence | Assumes CI/local execution environments expose consistent path behavior; if mismatch appears, block with explicit taxonomy of environment-specific divergence |

## Notes

- Treat this as a security ticket; preserve fail-closed behavior.

---

## Functional and Non-Functional Specification

### Requirement R1 - Authoritative Service-Layer Path Policy API

#### 1. Spec Summary
- **Description:** A single service-layer API shall perform all registry path canonicalization and validation decisions for registry-backed GLB paths. The API must be the only authority for path-security classification used by backend routers.
- **Constraints:** Router-local helpers for path normalization/allowlist enforcement must be removed from active decision flow. Service API must be fail-closed (invalid/ambiguous input is rejected).
- **Assumptions:** During migration, implementation may target `blobert_asset_gen.services.registry` or transitional `asset_generation/python/src/model_registry/service.py`, but exported policy behavior is identical.
- **Scope:** Registry policy functions in Python service layer and all backend call sites that currently evaluate path safety.

#### 2. Acceptance Criteria
- AC-R1.1: Service layer exposes one policy entrypoint (or tightly-coupled entrypoint set) that accepts untrusted registry-relative candidate paths and returns deterministic accept/reject outcomes.
- AC-R1.2: Policy API outputs canonicalized relative path for accepted inputs and does not return partially normalized paths for rejected inputs.
- AC-R1.3: For identical input, policy API returns identical classification and canonicalization output across repeated calls in the same environment.
- AC-R1.4: Router code does not duplicate policy decisions (no secondary allowlist/prefix/extension/traversal checks after service decision).
- AC-R1.5: Any internal policy-processing error is surfaced as a deterministic rejection class (fail-closed) rather than permissive fallback.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Transitional coexistence of two service module paths can lead to divergent behavior.
- **Impact:** Backend behavior may vary by import target.
- **Mitigation:** Contract requires one behaviorally authoritative API surface and parity regardless of physical module location.
- **Risk:** Silent permissive fallback if policy function raises.
- **Impact:** Path traversal or unsafe path acceptance.
- **Mitigation:** Explicit fail-closed requirement with deterministic rejection outcome.

#### 4. Clarifying Questions
- None. Conservative assumptions recorded via checkpoint protocol.

### Requirement R2 - Canonicalization and Normal Form Contract

#### 1. Spec Summary
- **Description:** Path canonicalization must convert accepted inputs to one normalized registry-relative form before downstream path join/use.
- **Constraints:** Accepted output uses forward-slash separators, no leading slash, and no dot-segment (`.`/`..`) components. Canonicalization must be deterministic and independent of caller origin.
- **Assumptions:** Registry operations consume relative logical paths, not absolute filesystem paths.
- **Scope:** Canonicalization behavior inside service policy API and consumed output at router boundaries.

#### 2. Acceptance Criteria
- AC-R2.1: Input variants that represent the same safe logical path (for example redundant separators or harmless `./`) resolve to one canonical relative output.
- AC-R2.2: Inputs resolving outside allowed registry scope are rejected, never canonicalized into accepted output.
- AC-R2.3: Accepted canonical output is stable under re-application (canonicalize(canonical_output) == canonical_output).
- AC-R2.4: Canonicalization result does not contain platform-specific separators.
- AC-R2.5: Empty, whitespace-only, or effectively empty-after-normalization inputs are rejected.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Platform-dependent normalization differences.
- **Impact:** Different behavior between local dev and CI environments.
- **Mitigation:** Contract defines platform-agnostic canonical output rules.
- **Risk:** Over-normalization can accidentally accept unsafe paths.
- **Impact:** Security boundary bypass.
- **Mitigation:** Require post-normalization safety validation before acceptance.

#### 4. Clarifying Questions
- None.

### Requirement R3 - Allowlist and Forbidden Path-Class Taxonomy

#### 1. Spec Summary
- **Description:** Service policy must enforce one authoritative allowlist policy and one explicit forbidden-path taxonomy covering traversal, encoded bypass, extension violations, and class-level forbidden locations.
- **Constraints:** Allowlist prefixes/classes must be centralized in service policy. Router-local duplicate constants or shadow lists are disallowed in active enforcement.
- **Assumptions:** Existing allowed registry classes remain valid unless explicitly tightened for security in this ticket.
- **Scope:** Service policy allowlist checks and forbidden-path classification outcomes consumed by registry routes.

#### 2. Acceptance Criteria
- AC-R3.1: Allowlist prefixes/classes are defined once in service policy and referenced by routers only through service API.
- AC-R3.2: Rejections are classified into deterministic forbidden classes (minimum: traversal, encoding abuse, extension violation, out-of-allowlist/forbidden class).
- AC-R3.3: Inputs that decode/normalize into forbidden classes are rejected even if raw input appears prefixed with an allowed segment.
- AC-R3.4: Extension policy is enforced after decoding/canonicalization and rejects spoofed/multi-extension bypass patterns that violate expected registry file type policy.
- AC-R3.5: Forbidden absolute-path classes (rooted filesystem paths, drive-qualified paths, UNC-like patterns where applicable) are always rejected.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Encoded and mixed-separator payloads may evade naive prefix checks.
- **Impact:** Unauthorized file access.
- **Mitigation:** Taxonomy explicitly requires decode + normalize + validate ordering with forbidden-class checks.
- **Risk:** Extension checks applied too early or too late.
- **Impact:** Extension spoofing acceptance.
- **Mitigation:** Require extension validation against canonicalized decoded path.

#### 4. Clarifying Questions
- None.

### Requirement R4 - Router Delegation and Regression-Safe Endpoint Behavior

#### 1. Spec Summary
- **Description:** `asset_generation/web/backend/routers/registry.py` must delegate all path-policy decisions to service API and preserve endpoint behavior except where security hardening explicitly rejects previously unsafe inputs.
- **Constraints:** No route signature changes, no payload schema changes, and no unrelated endpoint behavior changes. Security hardening changes must be explainable by policy contract.
- **Assumptions:** Existing endpoint contracts for successful safe paths remain unchanged.
- **Scope:** Registry router path-handling flow and service invocation seam.

#### 2. Acceptance Criteria
- AC-R4.1: Router path normalization helper `_normalize_registry_relative_glb_path` is removed from active policy enforcement path.
- AC-R4.2: Router does not maintain duplicate allowlist prefixes for decision-making after migration.
- AC-R4.3: For representative valid inputs previously accepted, endpoint behavior and response semantics remain unchanged.
- AC-R4.4: For representative invalid/unsafe inputs, rejection behavior is driven by service policy results and remains deterministic.
- AC-R4.5: Router unit/integration behavior proves delegation is authoritative (reintroducing local policy duplication would break tests).

#### 3. Risk & Ambiguity Analysis
- **Risk:** Removing router helper can unintentionally alter benign-path behavior.
- **Impact:** Regressions for valid registry loads.
- **Mitigation:** Regression requirement explicitly preserves behavior for safe path cohort.
- **Risk:** Dual enforcement (router + service) can create disagreement.
- **Impact:** Non-deterministic accept/reject behavior.
- **Mitigation:** Contract forbids router-side secondary policy logic.

#### 4. Clarifying Questions
- None.

### Requirement R5 - Non-Functional Security, Determinism, and Testability Requirements

#### 1. Spec Summary
- **Description:** The unified policy must be secure-by-default, deterministic, and directly testable with runtime behavioral evidence across service and backend layers.
- **Constraints:** No prose-only tests as evidence. Policy checks must run in bounded deterministic steps without network or external mutable dependency requirements.
- **Assumptions:** Existing test harnesses can exercise both service policy API and registry router behavior with encoded and adversarial inputs.
- **Scope:** Quality expectations for downstream test design and implementation validation.

#### 2. Acceptance Criteria
- AC-R5.1: Required behavioral evidence includes traversal, encoding, extension, and forbidden-class scenarios through shared policy API.
- AC-R5.2: Behavioral evidence includes router-delegation scenarios proving no local policy duplication.
- AC-R5.3: Policy outcomes are deterministic and repeatable across runs with identical inputs.
- AC-R5.4: Security posture is fail-closed for unknown/malformed classes and internal classification errors.
- AC-R5.5: Implementation does not introduce additional documentation artifacts beyond ticket/checkpoint updates required by workflow.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Tests focus on implementation details rather than runtime outcomes.
- **Impact:** Security regressions may pass unnoticed.
- **Mitigation:** Contract mandates observable behavior assertions as primary evidence.
- **Risk:** Undefined behavior for malformed encoding edge cases.
- **Impact:** Inconsistent reject/accept outcomes.
- **Mitigation:** Require deterministic reject classification for malformed/ambiguous encodings.

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
- Tests: Passed (ticket command evidence reports M901-11 service contract, adversarial path-policy coverage, router delegation, and endpoint regression suites all green)
- Static QA: Passed (ticket command evidence reports no new lints in touched files)
- Integration: Passed (ticket is in milestone `done/` and acceptance criteria evidence is sufficient for closure)

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
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/done/11_registry_path_policy_unification.md",
  "spec_revision": 2,
  "requirements": [
    "R1 Authoritative service-layer path policy API",
    "R2 Canonicalization and normal form contract",
    "R3 Allowlist and forbidden path-class taxonomy",
    "R4 Router delegation with regression-safe endpoint behavior",
    "R5 Non-functional security/determinism/testability constraints"
  ],
  "test_design_focus": [
    "Behavioral service-policy tests for traversal/encoding/extension/forbidden class outcomes",
    "Router delegation tests proving no active local policy duplication",
    "Deterministic fail-closed classification for malformed and adversarial encoded inputs"
  ]
}
```

## Status
Proceed

## Reason
All listed acceptance criteria have explicit command-backed evidence in this ticket (shared service policy API, router delegation, duplicate router allowlist removal, traversal/encoding/extension/forbidden-path coverage, and no-regression suites). Stage is `COMPLETE` because folder/state enforcement is now satisfied with the ticket under milestone `done/`.

## Command Evidence

- `uv run pytest tests/model_registry/test_m901_11_registry_path_policy_service_contract.py` (working dir: `asset_generation/python`) -> `15 passed`
- `uv run pytest tests/test_m901_11_registry_router_path_policy_delegation_contract.py tests/test_registry_load_existing_allowlist_router.py tests/test_registry_atrad_cross_cutting.py` (working dir: `asset_generation/web/backend`) -> `42 passed`
- `ReadLints` on touched files (`asset_generation/python/src/model_registry/service.py`, `asset_generation/web/backend/routers/registry.py`, `asset_generation/web/backend/tests/test_m901_11_registry_router_path_policy_delegation_contract.py`) -> `No linter errors found`
- `uv run pytest tests/model_registry/test_service.py -k "allowlist or extension or GLB or glb"` (working dir: `asset_generation/python`) -> `14 passed`
- `uv run pytest tests/model_registry/test_service_registry_fix_adversarial.py -k "GLB or glb or uppercase or extension"` (working dir: `asset_generation/python`) -> `1 passed`
