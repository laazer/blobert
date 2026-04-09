# TICKET: 06_editor_load_existing_models_allowlist

Title: Model editor — load existing exports from disk (draft + in-use only, canonical roots)

## Description

Add a **Load / Open existing** flow in the 3D model editor that **only** lists models under the project’s **canonical enemy/player export directories** (per spec), and **only** entries that are **draft** or **currently in-use** in the registry. Reject with a clear error any path outside the allowlist or ad-hoc “pick any file” dialogs for misc GLBs.

## Specification

### Requirement LEMA-F1 — Eligible candidate set is registry-backed and allowlist-jail constrained

#### 1. Spec Summary
- **Description:** The backend-provided candidate list for "Load/Open existing" is derived from registry records only (not raw filesystem scans) and includes only model entries with `draft == true` or `in_use == true`. Candidate `path` values must be canonical `python_root`-relative `.glb` paths under MRVC allowlist roots (`animated_exports/`, `exports/`, `player_exports/`, `level_exports/`).
- **Constraints:** Exclude any registry rows that fail path validation (absolute paths, traversal segments, non-allowlisted prefixes, non-`.glb` extensions). Exclude on-disk `.glb` files that are not represented in registry records. Candidate identity is registry-based (`family` + `version_id` for enemies; `path` for player active visual).
- **Assumptions:** "In-use" means entries currently marked `in_use` in persisted registry state; no supplemental source of "in-use" is introduced in this ticket.
- **Scope:** Backend candidate derivation contract and data eligibility filtering for the Load/Open workflow.

#### 2. Acceptance Criteria
- **LEMA-F1.1:** Candidate responses include only entries where registry flags satisfy `(draft == true) OR (in_use == true)`.
- **LEMA-F1.2:** Candidate responses never include paths outside MRVC allowlist roots or with non-`.glb` suffixes.
- **LEMA-F1.3:** `.glb` files present on disk but absent from registry are absent from candidate responses.
- **LEMA-F1.4:** Candidate responses are deterministic for a fixed registry state (stable sort by `family`, then `version_id`/`path`).

#### 3. Risk & Ambiguity Analysis
- Registry/file drift can hide manually copied assets; this is intentional for safety but may surprise operators.
- Mixed validity manifests (valid + invalid paths) require explicit behavior: invalid rows are excluded from candidates and surfaced through validation errors in load attempts.
- If all entries are filtered out, UI must handle empty-state without offering fallback arbitrary path selection.

#### 4. Clarifying Questions
- No open questions for this requirement.

### Requirement LEMA-F2 — Load/Open API contract and rejection behavior

#### 1. Spec Summary
- **Description:** Opening an existing model is performed through constrained API operations that accept registry identity and resolve to validated allowlisted paths. Any direct path payload is normalized and revalidated under jail rules before use. Out-of-jail or malformed targets are rejected with explicit error status/messages.
- **Constraints:** No endpoint or UI callback accepts raw absolute filesystem paths, `res://` free-form paths, or traversal input as load targets. Error layering follows ARGLB/M21 jail patterns: malformed target (`400`), out-of-jail/forbidden (`403`), missing registry target/file (`404`), dependency/import unavailable (`503`).
- **Assumptions:** Existing registry API surface in `asset_generation/web/backend/routers/registry.py` is the integration point; this ticket may add/extend constrained payload shapes but must preserve existing endpoint compatibility for unrelated flows.
- **Scope:** Backend open/load request validation contract and error semantics for this ticket's workflow.

#### 2. Acceptance Criteria
- **LEMA-F2.1:** Valid registry-backed request returns a success payload containing resolved canonical model path used for editor load.
- **LEMA-F2.2:** Traversal attempts (`..`, encoded traversal, mixed separators) are rejected and never resolve to files outside allowlisted roots.
- **LEMA-F2.3:** Raw arbitrary path attempts (`/abs/path.glb`, `res://...`, unknown prefixes) are rejected with deterministic error status and message.
- **LEMA-F2.4:** Missing or stale registry references (record exists but file missing) return deterministic not-found behavior without fallback to arbitrary file browsing.

#### 3. Risk & Ambiguity Analysis
- URL decoding/normalization can cause inconsistent traversal handling unless all validation occurs after canonical normalization.
- File-missing states are common during manual asset cleanup; error messages must distinguish "not in allowlist" from "not found" for debugging.
- If API permits both identity and path in payloads, precedence must be deterministic; safest contract is identity-only for this workflow.

#### 4. Clarifying Questions
- No open questions for this requirement.

### Requirement LEMA-F3 — Editor UI workflow prohibits arbitrary path entry

#### 1. Spec Summary
- **Description:** The editor presents a dedicated "Load/Open existing" picker populated exclusively from constrained backend candidate data. Users select from listed rows; there is no text input, native file chooser, drag/drop path, or other mechanism for entering arbitrary model paths in this flow.
- **Constraints:** Non-eligible entries are not displayed. The UI must not expose disabled rows for out-of-contract files because candidate generation is registry-backed only. Error states from backend are surfaced with actionable copy and do not unlock manual path overrides.
- **Assumptions:** Existing UI architecture has a registry panel where this picker can be colocated without introducing a second model-source workflow.
- **Scope:** Frontend behavior and UX constraints for this ticket's load/open interaction.

#### 2. Acceptance Criteria
- **LEMA-F3.1:** Visible picker rows correspond one-to-one with backend candidate payload entries.
- **LEMA-F3.2:** UI offers no controls that allow loading arbitrary OS paths or free-form `res://` paths.
- **LEMA-F3.3:** When candidate list is empty, UI renders explicit empty-state guidance (for example: "No draft or in-use registry models available") and provides no bypass action.
- **LEMA-F3.4:** On backend rejection, UI displays clear error text and preserves current editor model state (no partial or fallback load).

#### 3. Risk & Ambiguity Analysis
- Legacy generic file-input hooks can accidentally reintroduce unrestricted loading if not removed from this workflow path.
- Hiding non-registry files may prompt operator confusion; UX copy should explain registry-backed visibility rules.
- Error handling must avoid stale optimistic UI state when load fails.

#### 4. Clarifying Questions
- No open questions for this requirement.

### Requirement LEMA-F4 — Security invariants for traversal/path-injection resistance

#### 1. Spec Summary
- **Description:** The allowlist jail is enforced server-side for all load/open operations regardless of client behavior. Security checks treat client payloads as untrusted and verify resolved canonical paths remain under canonical roots before file access.
- **Constraints:** Validation must cover plain traversal, URL-encoded traversal, mixed separators, repeated encoding, and malformed null-byte or control-character payloads where framework parsing permits them.
- **Assumptions:** M21 assets-router jail patterns are the reference implementation pattern for normalization and jail checks.
- **Scope:** Security behavior for API validation and file resolution.

#### 2. Acceptance Criteria
- **LEMA-F4.1:** Traversal/path-injection test vectors cannot escape allowlisted roots.
- **LEMA-F4.2:** No code path falls back from rejected payload to a permissive "best effort" load.
- **LEMA-F4.3:** Security rejections are observable and deterministic (status + reason), enabling adversarial test assertions.

#### 3. Risk & Ambiguity Analysis
- Differences between HTTP/client normalization and Python path normalization can leave edge cases untested if only one layer is asserted.
- Symlink behavior under canonical roots can undermine jail assumptions if resolved-path checks are incomplete.
- Overly broad exception handling can mask security failures as generic errors.

#### 4. Clarifying Questions
- No open questions for this requirement.

### Requirement LEMA-NF1 — Determinism, compatibility, and observability

#### 1. Spec Summary
- **Description:** The feature preserves existing registry endpoint compatibility outside this workflow, produces deterministic response ordering and error semantics, and emits actionable logs/messages for validation and rejection events.
- **Constraints:** Do not change MRVC registry schema. Do not introduce additional manifest files. Keep behavior deterministic for repeatable tests.
- **Assumptions:** Existing logging and error plumbing in FastAPI router/service stack is available for structured error details.
- **Scope:** Non-functional requirements affecting testability, maintenance, and downstream integration.

#### 2. Acceptance Criteria
- **LEMA-NF1.1:** Existing registry CRUD/slot behaviors unrelated to load-existing remain behaviorally compatible.
- **LEMA-NF1.2:** Candidate list and error response shapes are stable enough for deterministic frontend and backend tests.
- **LEMA-NF1.3:** Rejections include actionable detail (category and offending input class) without leaking host filesystem internals.
- **LEMA-NF1.4:** Project validation command `timeout 300 ci/scripts/run_tests.sh` is designated as required completion gate for this ticket.

#### 3. Risk & Ambiguity Analysis
- Contract drift across backend/frontend can create brittle tests if response fields are not fixed.
- Excessively verbose error details can leak sensitive paths; excessively terse details reduce debuggability.
- Preserving compatibility while tightening validation may require explicit migration handling in tests.

#### 4. Clarifying Questions
- No open questions for this requirement.

## Acceptance Criteria

- No UI path loads arbitrary `res://` or OS paths outside allowlisted roots.
- Draft and in-use models from registry appear in the picker; unrelated files in the same folder are hidden or disabled per spec.
- Automated test proves traversal / path injection cannot escape jail (mirror M21 assets-router patterns if applicable).
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

## Dependencies

- `01_spec_model_registry_draft_versions_and_editor_contract`
- M21

---

# Project: Model Editor Existing-Model Allowlist
**Description:** Add a secure existing-model load workflow that only allows canonical enemy/player export roots and only registry-backed draft/in-use entries.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Produce normative allowlist/load specification for backend + frontend contracts | Spec Agent | Ticket AC, dependency ticket `01_spec_model_registry_draft_versions_and_editor_contract`, M21 assets-router jail patterns, existing registry routes/service behavior | Spec section or spec artifact defining canonical roots, in-use/draft inclusion rules, endpoint/status/error contract, and explicit non-goals (no arbitrary file-pick path) | None | Spec unambiguously defines accepted/rejected paths, response shapes, and UI behavior for hidden/disabled non-eligible entries | Risk: "in-use" semantics can be interpreted differently; assumption: active game-model assignments are canonical in-use source |
| 2 | Author deterministic primary tests that encode the spec contract | Test Designer Agent | Task 1 spec, backend router/service files, frontend registry/editor picker components | Failing tests for allowlisted listing, open-by-id/path restrictions, UI picker filtering to draft/in-use only, and clear user-facing errors for rejected paths | 1 | Tests fail on current behavior and each acceptance criterion is mapped to at least one test | Risk: Existing test fixtures may not include representative registry states; assumption: fixtures can seed draft + in-use models |
| 3 | Add adversarial tests for traversal/injection and jail escape attempts | Test Breaker Agent | Task 1 spec + Task 2 suites, M21 traversal hardening patterns | Additional failing adversarial tests for `..`, encoded traversal, absolute paths, symlink-like edge cases (where applicable), and mixed-valid/invalid payload handling | 2 | Adversarial suite proves no escape outside canonical roots and no fallback arbitrary file load path remains | Risk: URL/path normalization differences between client/server test harnesses; assumption: tests normalize expectations per framework behavior |
| 4 | Implement backend allowlist enforcement and secure candidate resolution | Implementation Backend Agent | Approved tests, spec, current backend registry routes/services | Backend code updates that source candidates from registry metadata and enforce canonical-root jail on any load/open path resolution with explicit error codes/messages | 2, 3 | Backend primary + adversarial tests pass; no endpoint accepts out-of-jail paths; non-registry files are excluded from selectable candidates | Risk: overlap with existing assets router may duplicate logic; assumption: shared jail utility can be reused or mirrored safely |
| 5 | Implement frontend load-existing picker constrained to registry-backed draft/in-use entries | Implementation Frontend Agent | Spec, frontend tests, backend contract from Task 4 | UI flow for "Load/Open existing" that consumes constrained backend data, disables/hides unrelated files, blocks manual arbitrary path input, and surfaces clear error messaging | 4 | Frontend tests pass and UI offers no arbitrary path pathway while preserving draft/in-use discoverability | Risk: current component architecture may expose generic file input path hooks; assumption: those hooks can be removed or fenced for this flow |
| 6 | Execute full validation and AC traceability handoff | Acceptance Criteria Gatekeeper Agent | Completed implementation, all test artifacts, ticket AC list | Validation matrix in ticket mapping ACs to test evidence and command outputs, including full suite run | 4, 5 | `timeout 300 ci/scripts/run_tests.sh` exits 0 and AC1-AC4 are explicitly evidenced | Risk: unrelated flaky tests may obscure feature readiness; assumption: targeted reruns can isolate failures before full-suite confirmation |

## Notes
- Tasks are sequential and independently executable once dependencies are met.
- No task permits arbitrary filesystem browsing outside canonical export roots.
- Ambiguity resolved conservatively via checkpoint: registry-backed draft + active in-use entries are the only picker-visible candidates.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
9

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- AC evidence — no arbitrary `res://`/OS-path UI load path: `asset_generation/web/frontend/src/components/Editor/ModelRegistryPane.tsx` wires `Load / Open Existing` only through backend candidates (`fetchLoadExistingCandidates`) and candidate-derived open requests (`toOpenExistingRequest`) with no free-form path input, native file chooser, or arbitrary-path control in this workflow.
- AC evidence — draft/in-use registry models appear, unrelated files hidden: backend candidate derivation in `asset_generation/web/backend/routers/registry.py` is registry-backed, allowlist constrained, and filtered to `(draft == true) OR (in_use == true)` with deterministic ordering; frontend candidate-key mapping tests in `asset_generation/web/frontend/src/components/Editor/ModelRegistryPane.slot_contract.test.ts` assert one-to-one rendering/request mapping from backend payload only.
- AC evidence — traversal/path-injection cannot escape jail: backend load-existing contract tests in `asset_generation/web/backend/tests/test_registry_load_existing_allowlist_router.py` cover traversal/control-char/raw-path rejection, explicit 400/403/404 layering, no permissive fallback, and pass (`12 passed` via `arch -arm64 uv run --project asset_generation/python --extra dev python -m pytest asset_generation/web/backend/tests/test_registry_load_existing_allowlist_router.py -q`).
- AC evidence — required project validation gate: `timeout 300 ci/scripts/run_tests.sh` exits `0`.
- Supporting UI contract evidence: explicit empty-state guidance is covered by `asset_generation/web/frontend/src/components/Editor/ModelRegistryPane.copy.test.ts`; frontend suite passes (`npm test` in `asset_generation/web/frontend` → `9 passed` files, `66 passed` tests).

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
{}
```

## Status
Proceed

## Reason
All ticket-level acceptance criteria have explicit backend/frontend test and validation evidence recorded in `Validation Status`; ticket is eligible for human closeout.
