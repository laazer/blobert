# Run Contract Unification

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** In Progress

---

## Description

Unify command argument, environment, and output file contract used by CLI and API run routes. Today, `asset_generation/web/backend/routers/run.py` rebuilds behavior already encoded in Python entrypoints and generation scripts.

Target overlap:
- `asset_generation/web/backend/routers/run.py`
- `asset_generation/python/main.py`
- generator start-index and draft-subdir env behavior

## Acceptance Criteria

- [ ] Shared Python-side run contract module is introduced (command schema + env rules + output prediction).
- [ ] API run router delegates to shared contract module and removes duplicate `_build_command` / `_guess_output_file` logic.
- [ ] Run contract supports current commands: `animated`, `player`, `level`, `smart`, `stats`, `test`.
- [ ] `/api/run/stream` and `/api/run/complete` preserve current external behavior and response shape.
- [ ] Regression tests cover command parity and variant-index behavior.

## Specification

### Requirement RCU-1 — Canonical Run Contract Surface

#### 1. Spec Summary
- **Description:** A shared Python-side run contract module SHALL be the only owner of run input normalization and contract outputs for command invocation: command vector construction, environment overlay, start-index resolution, and output-file prediction.
- **Constraints:** Contract MUST support commands `animated`, `player`, `level`, `smart`, `stats`, `test`. Router transport/process lifecycle stays in router scope.
- **Assumptions:** Existing behavior in `asset_generation/web/backend/routers/run.py` and `asset_generation/python/main.py` is the compatibility baseline.
- **Scope:** Shared Python contract module + backend run-router delegation seam.

#### 2. Acceptance Criteria
- Allowed commands are accepted and normalized into command vectors beginning with `[python_executable, "main.py", cmd]`.
- Unknown commands are rejected with current endpoint semantics (`/complete` HTTP 400; `/stream` SSE error event).
- `count` is appended only when provided and command is not `smart` and not `test`.
- Optional flag parity is preserved:
  - `--description` when description exists.
  - `--difficulty` when difficulty exists.
  - `--finish` only for `animated|player`.
  - `--hex-color` only for `animated|player`.
- Contract returns a prediction value for supported combinations and `None` where current behavior cannot produce a deterministic artifact path.

#### 3. Risk & Ambiguity Analysis
- Hidden implicit defaults in CLI may drift from API assumptions.
- `enemy` semantic validation is intentionally not expanded in this ticket.
- `level` with `enemy=all` does not map cleanly to a single artifact.

#### 4. Clarifying Questions
- No blocking questions; conservative compatibility assumption applied.

### Requirement RCU-2 — Environment Policy and Variant Index Rules

#### 1. Spec Summary
- **Description:** Shared contract SHALL deterministically produce env overlays and resolved `start_index` for both `/stream` and `/complete`.
- **Constraints:** Preserve existing key behavior:
  - `PYTHONPATH` prepends `<python_root>`, `<python_root>/bin`, `<python_root>/src`.
  - `BLOBERT_BUILD_OPTIONS_JSON` set only when `build_options` is non-empty after trim.
  - `BLOBERT_EXPORT_USE_DRAFT_SUBDIR="1"` set only when `output_draft=true` and command in `animated|player|level`.
  - `BLOBERT_EXPORT_START_INDEX` follows override/auto rules below.
- **Assumptions:** Filesystem-based next-index scan logic is authoritative baseline.
- **Scope:** Contract env/start-index API and consumers.

#### 2. Acceptance Criteria
- If `replace_variant_index` is provided and command in `animated|player|level`, then `start_index=replace_variant_index` and env includes `BLOBERT_EXPORT_START_INDEX`.
- `animated` auto-index path:
  - Applies when `cmd=animated`, `enemy` exists, and `enemy!="all"`.
  - Scans `animated_exports/` or `animated_exports/draft/`.
  - Pattern `<enemy>_animated_*.glb`; two-digit suffix extraction; `start_index=max+1` or `0`.
  - Sets `BLOBERT_EXPORT_START_INDEX`.
- `player` auto-index path:
  - Applies when `cmd=player` and `enemy` exists.
  - Scans `player_exports/` or `player_exports/draft/`.
  - Pattern `player_slime_<enemy>_*.glb`; two-digit suffix extraction; `start_index=max+1` or `0`.
  - Sets `BLOBERT_EXPORT_START_INDEX`.
- For commands not matching above, `start_index` remains `0` unless fixed override applies.

#### 3. Risk & Ambiguity Analysis
- Filesystem race can still occur with external concurrent writers.
- Non-two-digit suffix files are intentionally ignored.
- Empty `build_options` must not set build-options env key.

#### 4. Clarifying Questions
- No blocking questions.

### Requirement RCU-3 — Output File Prediction Contract

#### 1. Spec Summary
- **Description:** Shared contract SHALL predict output file path strings from normalized inputs + resolved `start_index` with current path formulas.
- **Constraints:** Prediction is path-only best-effort (no existence guarantee). Count clamping parity (`1..99`) is preserved.
- **Assumptions:** Existing naming formulas are compatibility baseline.
- **Scope:** Shared predictor used by `/stream` and `/complete`.

#### 2. Acceptance Criteria
- `animated` + enemy => `animated_exports/{draft?}{enemy}_animated_{last:02d}.glb`.
- `player` + enemy => `player_exports/{draft?}player_slime_{enemy}_{last:02d}.glb`.
- `level` + enemy => `level_exports/{draft?}{enemy}_{last:02d}.glb`.
- `test` => `animated_exports/spider_animated_00.glb`.
- `last = start_index + n - 1`, where `n = clamp(count_or_1, 1..99)`.
- Unsupported/insufficient input combinations return `None`.

#### 3. Risk & Ambiguity Analysis
- `level all` remains compatibility behavior even if not semantically a single output artifact.
- Predictor can drift if generator naming changes outside contract ownership.

#### 4. Clarifying Questions
- No blocking questions; compatibility-first assumption retained for `level all`.

### Requirement RCU-4 — Router Delegation and External Behavior Preservation

#### 1. Spec Summary
- **Description:** `/api/run/stream` and `/api/run/complete` SHALL delegate command/env/output decisions to shared contract while preserving current external behavior.
- **Constraints:** Process manager lifecycle, timeout flow, and `/complete` start-failure error mapping remain unchanged.
- **Assumptions:** Current payload field sets and status codes are frozen compatibility surface.
- **Scope:** Backend run router refactor boundaries only.

#### 2. Acceptance Criteria
- Router no longer owns duplicated `_build_command`/`_guess_output_file` logic; equivalent decisions come from shared contract.
- `/stream` parity:
  - Unknown command => SSE `error` with `exit_code=-1`.
  - Existing running process => SSE `error` with `exit_code=-1`.
  - Success => SSE `done` with `exit_code=0` and predicted `output_file`.
  - Non-zero exit => SSE `error` with process exit code and fixed error message.
- `/complete` parity:
  - Unknown command => HTTP 400 with `detail`.
  - Existing running process => HTTP 409 with `detail` + `run_id`.
  - Timeout => HTTP 504 with bounded logs, `timed_out=true`, and unchanged poll/kill guidance.
  - Success => HTTP 200 with `exit_code=0`, bounded logs, predicted `output_file`, `run_id`.
  - Failure => HTTP 200 with non-zero `exit_code`, bounded logs, `output_file=None`, `run_id`, and fixed error message.
- Successful `animated` runs with concrete family (`enemy` not `all`) still attempt post-run registry sync; sync failures remain non-fatal.

#### 3. Risk & Ambiguity Analysis
- Refactor risk: accidental status/payload drift.
- Contract must not absorb transport/process concerns.

#### 4. Clarifying Questions
- No blocking questions.

### Requirement RCU-5 — Non-Functional Constraints

#### 1. Spec Summary
- **Description:** Ticket outcome SHALL improve maintainability and testability without API-surface expansion.
- **Constraints:** No process-manager redesign, no endpoint schema redesign, no generator naming redesign.
- **Assumptions:** Regression tests assert behavior outcomes rather than internal helper names.
- **Scope:** Determinism, compatibility, maintainability, and fail-closed command handling.

#### 2. Acceptance Criteria
- Deterministic contract: same normalized input yields same command/env/prediction output.
- Backward compatibility: `/stream` and `/complete` external semantics unchanged.
- Maintainability: command/env/output decision logic is centralized in one shared module.
- Security posture: command handling stays allowlist-based; no new broad env passthrough behavior is introduced.

#### 3. Risk & Ambiguity Analysis
- Weak parity tests could allow silent drift.
- Future command additions require centralized contract + test updates.

#### 4. Clarifying Questions
- No blocking questions.

## Dependencies

- Backend-Python Import Adapter

## Execution Plan

# Project: Run Contract Unification
**Description:** Centralize CLI/API run command construction, environment policy, and output-path prediction into one shared Python contract so backend routes delegate behavior rather than re-encoding it, while preserving current `/api/run` external semantics.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Freeze the shared run-contract behavior boundary and compatibility requirements. | Spec Agent | Ticket acceptance criteria; current implementations in `asset_generation/web/backend/routers/run.py` and `asset_generation/python/main.py`; existing generator env conventions (start-index, draft-subdir); current command families (`animated`, `player`, `level`, `smart`, `stats`, `test`) | A complete specification that defines canonical command schema, env merge/override rules, output-file prediction rules, ownership boundaries (contract vs router transport), and backward-compatibility constraints for stream/complete endpoints | None | Every AC maps to deterministic runtime behavior with explicit parity constraints and no unresolved ambiguity on command/env/output contracts | Risk: hidden implicit CLI defaults not documented in code; assumption: existing run behavior is authoritative baseline unless safety issue is discovered and documented |
| 2 | Encode primary behavioral contracts for command/env/output parity against the frozen spec. | Test Designer Agent | Approved spec from Task 1; existing backend tests including run-router behavior suites; Python-side run command tests | RED tests asserting command list support, env-policy parity (including variant/start-index and draft-subdir behavior), and unchanged response shape/transport semantics for `/api/run/stream` and `/api/run/complete` | 1 | Tests fail until unification is implemented and will pass only when shared contract + router delegation preserve baseline behavior | Risk: brittle assertions on incidental command-string formatting; assumption: tests should assert contract-relevant command tokens/env keys/output prediction outcomes |
| 3 | Add adversarial coverage for malformed inputs and fail-closed run-contract behavior. | Test Breaker Agent | Task 1 spec and Task 2 tests | Additional RED tests for malformed command requests, invalid variant index inputs, unsupported command types, and edge env/output prediction collisions with deterministic fail-closed expectations | 2 | Edge-case tests expose unsafe fallback paths and enforce deterministic, safe error behavior without widening API surface | Risk: overcoupling tests to current exception text; assumption: focus on status/error-shape and command/env/output safety invariants |
| 4 | Implement shared run-contract module and refactor run router to delegate contract logic. | Implementation Backend Agent | Frozen spec; failing tests from Tasks 2-3; current run router and Python entrypoint modules | Production changes introducing shared run contract module, removing duplicate `_build_command` / `_guess_output_file` logic from router paths, and preserving transport/process-manager responsibilities in router layer | 3 | All contract/adversarial tests pass; run router uses shared contract API for command/env/output decisions; supported commands remain complete and behavior-compatible | Risk: accidental behavioral drift in endpoint payload fields or output prediction; assumption: process manager lifecycle/timeout orchestration remains untouched per ticket notes |
| 5 | Validate gates and acceptance traceability for handoff readiness. | Static QA Agent then Acceptance Criteria Gatekeeper Agent | Implementation diff, targeted/backend test outputs, lint/static checks, acceptance criteria | QA/gatekeeper evidence that ACs are fully satisfied with runtime-backed proof and no unresolved regression risk | 4 | Required tests and static checks pass; AC-to-evidence traceability is explicit and complete; ticket is ready to advance beyond implementation phases | Risk: partial suite pass masking command-family regressions; assumption: targeted plus related regression suites are required before closure |

## Notes

- Keep this ticket contract-focused; do not redesign process manager lifecycle.
- Dependency `Backend-Python Import Adapter` is already complete (`project_board/901_milestone_901_asset_generation_refactoring/done/10_backend_python_import_adapter.md`), so no planning-stage dependency block applies.
- Autonomous checkpoint assumption applied: because workflow-state fields were absent in this ticket file, revision baseline was conservatively initialized at `0` and incremented to `1` for this state transition.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: Passed (`asset_generation/python/tests/utils/test_run_contract_behavior.py` and backend run-router command/delegation regression suites; Python review checkpoint records 18/18 targeted tests passing after import-order fix).
- Static QA: Passed at ticket scope (organization/import-order review findings resolved; no unresolved static-quality findings documented for changed contract/router surfaces).
- Integration: Passed at ticket scope (router parity for `/api/run/stream` + `/api/run/complete`, supported command allowlist `animated|player|level|smart|stats|test`, variant-index behavior, and output prediction parity evidenced in checkpointed regression coverage).

## Blocking Issues
- None.

## Escalation Notes
- Stage-folder consistency is now satisfied (`done/` placement confirmed). Acceptance criteria evidence remains explicit and unchanged; gate reopened to mark ticket complete without altering scope/spec/AC text.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/done/15_run_contract_unification.md",
  "stage": "COMPLETE",
  "revision": 7,
  "dependencies": [
    "project_board/901_milestone_901_asset_generation_refactoring/done/10_backend_python_import_adapter.md"
  ],
  "planning_contract": "Execution-plan tasks 1-5 in this ticket",
  "deliverable": "Archive-ready ticket with unchanged AC evidence trail and complete-state workflow closure."
}
```

## Status
Proceed

## Reason
All acceptance criteria retain explicit objective evidence in ticket/checkpoint records, and stage-folder consistency is now satisfied, so the ticket can be treated as complete and handed to Human for any final archive/coordination tasks.
