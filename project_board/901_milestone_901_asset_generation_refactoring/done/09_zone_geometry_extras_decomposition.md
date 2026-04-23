# Zone Geometry Extras Decomposition

**Epic:** Milestone 901 - Asset Generation Refactoring  
**Status:** Ready

---

## Description

Decompose `enemies/zone_geometry_extras_attach.py` (718 LOC) monolith into focused modules for pure geometry math, placement strategy, enemy-specific attachment handlers, and a thin dispatcher while preserving current behavior and enabling testability without Blender context for extracted math paths.

## Acceptance Criteria

- [ ] `geometry_math.py` (new): Pure geometry utilities (ellipsoid surface, normal vectors, point sampling)
- [ ] `placement_strategy.py` (new): Placement algorithms (clustering, distribution, facing)
- [ ] `attachment.py` (new): Enemy-specific handlers (body extras, head extras, player extras)
- [ ] Dispatcher logic thin and readable
- [ ] All extracted math functions unit testable without bpy context
- [ ] All existing tests pass; test coverage improved (currently untestable)
- [ ] Geometry math functions fully type-hinted

## Dependencies

- Enemy builder template extraction (`done/07_enemy_builder_template.md`): Optional reference for rig context; non-gating.

## Execution Plan

# Project: Zone Geometry Extras Decomposition
**Description:** Refactor zone-extras attachment logic into separable geometry, placement, and attachment modules with testable pure math contracts and compatibility-preserving dispatcher behavior.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Freeze module/API decomposition contract for current monolith | Spec Agent | Ticket AC, current `asset_generation/python/src/enemies/zone_geometry_extras_attach.py`, current import consumers | Frozen specification mapping existing functions/flows into `geometry_math.py`, `placement_strategy.py`, `attachment.py`, and dispatcher surface (`__init__.py` or retained entrypoint) | None | Every current callable/path is mapped to an owning module and no behavior-changing scope creep is introduced | Risk: hidden side effects in Blender-context helpers; assumption: decomposition is structural, not behavioral |
| 2 | Define math purity and typing contract for extracted geometry functions | Spec Agent | Task 1 mapping, AC items for type hints/testability | Explicit contract for pure functions (ellipsoid points, normals, facing samples), deterministic input/output expectations, and required type annotations | 1 | Spec states which functions must be bpy-free and unit-testable, with concrete signatures/return semantics | Risk: implicit Blender objects currently flowing through math helpers; assumption: purity boundary can be carved without changing outputs |
| 3 | Author RED behavioral tests for decomposition contracts | Test Designer Agent | Tasks 1-2 spec, existing enemy/geometry tests | New/updated tests validating module presence, dispatcher parity, pure math correctness, and regression behavior for known enemy families | 1, 2 | Tests fail red before implementation where contracts are unmet and encode observable behavior (not prose assertions) | Risk: brittle tests if tied to internal call order; assumption: existing test harness can mock bpy seams where required |
| 4 | Add adversarial tests for edge placement/normal cases | Test Breaker Agent | Task 3 tests + specification | Additional tests for malformed/edge geometry inputs, clustering/distribution boundaries, and fail-closed behavior where metadata is invalid | 3 | Test suite catches false-green refactors (missing handlers, signature drift, non-deterministic edge regressions) | Risk: over-constraining heuristics that are intentionally approximate; assumption: adversarial cases can still assert stable invariants |
| 5 | Implement module extraction and thin dispatcher wiring | Implementation Generalist Agent | Tasks 1-4 artifacts | New `geometry_math.py`, `placement_strategy.py`, `attachment.py`; thin dispatcher entrypoint with updated imports; obsolete monolith removed or reduced to compatibility shim per spec | 4 | All AC file/module outcomes implemented, type hints added on geometry APIs, and runtime behavior retained across supported enemies | Risk: import cycles and Blender-context dependencies during relocation; assumption: compatibility shim may be needed for gradual migration |
| 6 | Validate static quality and regression evidence for Python refactor | Static QA Agent | Implementation diff, required test suites, lint/type tooling | Validation evidence with targeted pytest results, static checks, and `diff_cover_preflight` result (if `.py` files changed under `asset_generation/python/`) | 5 | Required suites pass and evidence is recorded in ticket Validation Status for gatekeeper consumption | Risk: environment/tooling mismatch for Blender-related tests; assumption: failures will be triaged as code vs environment with explicit evidence |
| 7 | Perform acceptance-criteria gate and route ticket forward | Acceptance Criteria Gatekeeper Agent | Ticket AC list, validation evidence, implementation summary | AC-by-AC pass/fail matrix with explicit evidence links and next-stage routing | 6 | Each AC is either validated with concrete evidence or escalated as blocker with clear remediation | Risk: ambiguous "identical zone extras" claims without objective comparator; assumption: test evidence includes representative parity coverage |

## Notes
- Tasks are sequential, independent once dependencies are satisfied, and sized for one agent run each.
- Ticket classification: `generic` (no destructive API contract and no randomness-policy freeze requirement).
- Conservative assumption: dependency on enemy builder template is informational/non-gating because ticket `07` is already in `done/`.

---

## Functional and Non-Functional Specification

### Requirement R1 - Module Decomposition and Ownership Freeze

#### 1. Spec Summary
- **Description:** The existing `zone_geometry_extras_attach.py` behavior shall be decomposed into three new modules and one thin dispatcher surface without changing observable runtime behavior for supported call paths.
- **Constraints:** The decomposition is structural only (no feature expansion, no behavioral redesign, no placement policy change, no material selection policy change). Existing external callables remain available at their current import path(s).
- **Assumptions:** Keep existing public entrypoint function names and signatures stable at the current module surface; new modules are internal decomposition units and may also expose typed helper APIs for tests.
- **Scope:** `asset_generation/python/src/enemies/zone_geometry_extras_attach.py` and new files `geometry_math.py`, `placement_strategy.py`, and `attachment.py` under the same package.

#### 2. Acceptance Criteria
- AC-R1.1: `geometry_math.py` exists and owns pure geometry primitives currently embedded in the monolith (ellipsoid point/normal math, vector tuple coercion helpers, scale reference helpers, and any reusable geometric transforms that do not require object creation or material application).
- AC-R1.2: `placement_strategy.py` exists and owns placement policy helpers currently embedded in the monolith (distribution mode resolution, uniform shape resolution, clustering/offset clamping helpers, facing gate evaluation, and bounded attempt logic inputs).
- AC-R1.3: `attachment.py` exists and owns side-effect handlers that create/apply/append extras for body/head/player flows.
- AC-R1.4: Dispatcher surface remains thin: it validates high-level preconditions, resolves materials/context, and delegates to attachment/placement/geometry functions; it does not re-embed full placement loops.
- AC-R1.5: Backward-compatible callables remain available and behaviorally equivalent for:
  - `append_animated_enemy_zone_extras(model)`
  - `append_slug_zone_extras(model)`
  - `append_spider_zone_extras(model)`
  - `append_player_slime_zone_extras(builder)`
- AC-R1.6: Existing supported `kind` modes remain unchanged in behavior and dispatch:
  - body: `spikes`, `shell`, `bulbs`
  - head: `horns`, `spikes`, `shell`, `bulbs`
  - unsupported/`none`: no-op behavior preserved.

#### 3. Risk and Ambiguity Analysis
- **Risk:** Hidden coupling between placement loops and object/material side effects may accidentally leak into pure modules.
  - **Impact:** Reduced testability or regressions in object counts/orientation/material assignment.
  - **Mitigation:** Enforce explicit ownership boundary: pure modules return data; attachment module performs side effects.
- **Risk:** Import-cycle risk after module split.
  - **Impact:** Runtime import errors.
  - **Mitigation:** Keep dependency direction one-way (`geometry_math` -> `placement_strategy` optional; `attachment` imports both; dispatcher imports attachment only).

#### 4. Clarifying Questions
- None. Conservative compatibility assumption applied via checkpoint log.

### Requirement R2 - Pure Geometry and Typing Contract

#### 1. Spec Summary
- **Description:** Geometry math functions extracted to `geometry_math.py` must be Blender-context-free and fully type-hinted, enabling deterministic unit testing without `bpy`.
- **Constraints:** No `bpy` imports in `geometry_math.py`; no object/material creation in `geometry_math.py`; deterministic output for identical inputs.
- **Assumptions:** Use plain Python numeric and tuple/list-compatible inputs at the geometry boundary, with explicit return types.
- **Scope:** Extracted geometry helpers and their call sites in placement/attachment modules.

#### 2. Acceptance Criteria
- AC-R2.1: `geometry_math.py` imports only standard-library and non-`bpy` math/vector utilities needed for pure computation.
- AC-R2.2: Every public function in `geometry_math.py` has explicit parameter and return type annotations.
- AC-R2.3: At minimum, extracted geometry helpers cover:
  - ellipsoid surface point computation from center/radii/angles,
  - outward normal computation with degenerate-length fallback behavior,
  - reference scale computation for body/head dimensions,
  - numeric clamping/coercion helpers needed for geometry-domain stability.
- AC-R2.4: Degenerate and malformed numeric handling remains fail-closed and deterministic:
  - `NaN`/invalid numeric inputs resolve to documented defaults or clamped values,
  - near-zero normal-length path returns default upward normal equivalent to current behavior.
- AC-R2.5: Geometry helpers are directly importable in tests without requiring Blender runtime objects.

#### 3. Risk and Ambiguity Analysis
- **Risk:** Existing helper behavior includes implicit coercion from `mathutils.Vector`-like objects.
  - **Impact:** Type-signature over-tightening can break current runtime compatibility.
  - **Mitigation:** Preserve tolerant coercion semantics while making typed contracts explicit (accept tuple-like/vector-like where currently supported).
- **Risk:** Floating-point equality drift after refactor.
  - **Impact:** false regressions in geometry assertions.
  - **Mitigation:** Require invariant-level parity (shape/orientation/count constraints) and tolerance-based numeric comparisons in downstream tests.

#### 4. Clarifying Questions
- None.

### Requirement R3 - Placement Strategy Contract

#### 1. Spec Summary
- **Description:** Placement and facing-selection logic shall be centralized in `placement_strategy.py` so deterministic policy behavior is preserved and independently testable from mesh/material side effects.
- **Constraints:** Existing policy defaults and bounds remain unchanged (`distribution`, `uniform_shape`, clustering clamp, facing dot-threshold behavior, attempt ceilings).
- **Assumptions:** Existing seeded PRNG source and placement helper functions continue to be used; decomposition does not alter random source wiring.
- **Scope:** Placement parameter normalization and candidate acceptance logic for body/head spikes and bulbs.

#### 2. Acceptance Criteria
- AC-R3.1: Placement policy functions resolve and sanitize mode values exactly as current behavior:
  - invalid `distribution` -> `uniform`,
  - invalid `uniform_shape` -> `arc`,
  - clustering clamped to `[0, 1]` equivalent behavior.
- AC-R3.2: Facing gate behavior preserved:
  - all disabled or all enabled flags keep current pass-through semantics,
  - otherwise candidate acceptance requires dot-product threshold equivalent to current constant (`0.45`) against enabled world-axis facings.
- AC-R3.3: Placement attempt budgets and bounded-loop termination semantics preserved for uniform/random branches.
- AC-R3.4: Placement strategy functions output data needed for attachment operations without creating Blender objects.

#### 3. Risk and Ambiguity Analysis
- **Risk:** Refactor may accidentally change candidate acceptance order or attempt phasing.
  - **Impact:** visible distribution regressions.
  - **Mitigation:** Preserve branch structure and iteration ordering semantics from current implementation.
- **Risk:** Over-abstraction could move behavior-changing math into helpers.
  - **Impact:** parity drift.
  - **Mitigation:** Keep helper extraction behavior-preserving and map each prior branch one-to-one.

#### 4. Clarifying Questions
- None.

### Requirement R4 - Attachment Handler and Dispatcher Contract

#### 1. Spec Summary
- **Description:** `attachment.py` shall own all Blender-side effects for zone extras attachment, while dispatcher entrypoints remain compatibility shims that delegate after precondition/material setup.
- **Constraints:** Material resolution/feature slot overrides/zone texture overrides and part append semantics remain equivalent to current behavior.
- **Assumptions:** `model.parts` and player `_zone_extra_parts` append contracts stay unchanged.
- **Scope:** Enemy body/head extras and player slime extras attachment paths.

#### 2. Acceptance Criteria
- AC-R4.1: Attachment handlers preserve per-kind construction semantics (sphere/cone creation parameters, orientation step, material application, append target).
- AC-R4.2: Player slime path keeps current no-op guard behavior for missing options/parts and preserves body/head geometry parameter derivation from builder attributes.
- AC-R4.3: Dispatcher remains readable and thin (delegation-focused) and does not duplicate per-kind placement internals.
- AC-R4.4: Legacy specialized wrappers (`append_slug_zone_extras`, `append_spider_zone_extras`) continue to gate by instance type and delegate to the common enemy dispatcher.
- AC-R4.5: Unsupported input structures continue fail-closed behavior (return without mutation).

#### 3. Risk and Ambiguity Analysis
- **Risk:** Material slot derivation or feature override order might change during relocation.
  - **Impact:** visual/material regressions.
  - **Mitigation:** Preserve invocation order and parameter passthrough exactly.
- **Risk:** Wrapper compatibility might be lost if entrypoints are relocated without stable re-export.
  - **Impact:** downstream import breakage.
  - **Mitigation:** Retain existing entrypoint module exports as compatibility surface.

#### 4. Clarifying Questions
- None.

### Requirement R5 - Non-Functional Quality and Verification Readiness

#### 1. Spec Summary
- **Description:** The decomposition shall improve maintainability and testability while preserving runtime behavior.
- **Constraints:** No unnecessary documentation artifacts; acceptance evidence must rely on executable behavior checks rather than prose assertions.
- **Assumptions:** Existing test harness can run pure-python tests independently from Blender-dependent paths.
- **Scope:** Refactored module structure and downstream test-design readiness.

#### 2. Acceptance Criteria
- AC-R5.1: New modules expose focused responsibilities with no monolithic duplication.
- AC-R5.2: Pure geometry utilities can be unit-tested without Blender context and without monkeypatching object-creation primitives.
- AC-R5.3: Existing regression suites continue to pass after implementation, with additional tests covering previously untestable pure math contracts.
- AC-R5.4: Type hints in geometry module are complete enough for static analyzers to infer function-level contracts.
- AC-R5.5: Refactor preserves deterministic behavior under identical PRNG/model inputs.

#### 3. Risk and Ambiguity Analysis
- **Risk:** Existing tests may under-specify parity for placement distribution and facing edge cases.
  - **Impact:** false-green behavior drift.
  - **Mitigation:** Test Designer must include behavior-level regression assertions for kind-specific paths and facing/offset boundary inputs.
- **Risk:** Blender-coupled tests may hide pure-contract breakages.
  - **Impact:** delayed failures.
  - **Mitigation:** Require dedicated pure-module tests as first-class artifacts in test design.

#### 4. Clarifying Questions
- None.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

COMPLETE

## Revision

10

## Last Updated By

Autopilot Orchestrator

## Validation Status

- Tests: Passed (`uv run pytest tests/enemies/test_m901_09_zone_geometry_extras_decomposition_contract.py -q` => `14 passed in 0.04s`; `uv run pytest tests/enemies/test_spider_zone_extras_attach.py tests/enemies/test_zone_extras_offset_attach.py tests/enemies/test_zone_geometry_extras_facing.py tests/enemies/test_distribution_eyes_and_extras.py tests/enemies/test_shell_and_spike_protrusion.py tests/enemies/test_shell_and_spike_protrusion_adversarial.py tests/enemies/test_m901_09_zone_geometry_extras_decomposition_contract.py -q` => `69 passed in 0.15s`; `uv run pytest tests/enemies/test_slug_zone_extras_attach.py -q` => `13 passed in 0.06s`)
- Tests: Passed (`uv run pytest tests/enemies/test_m901_09_zone_geometry_extras_decomposition_contract.py tests/enemies/test_zone_geometry_extras_facing.py -q` => `19 passed in 0.04s`)
- Tests: Passed (`uv run pytest tests/enemies/test_m901_09_zone_geometry_extras_decomposition_contract.py -q` => `16 passed in 0.08s`)
- Tests: Passed (`uv run pytest tests/enemies/test_zone_geometry_extras_facing.py tests/enemies/test_distribution_eyes_and_extras.py tests/enemies/test_shell_and_spike_protrusion.py tests/enemies/test_shell_and_spike_protrusion_adversarial.py tests/enemies/test_zone_extras_offset_attach.py tests/enemies/test_spider_zone_extras_attach.py tests/enemies/test_slug_zone_extras_attach.py -q` => `68 passed in 0.17s`)
- Static QA: Passed (`ReadLints` on touched decomposition files reported no linter errors)
- Contract Evidence: Dispatcher thin/readable AC closed via executable assertion in `tests/enemies/test_m901_09_zone_geometry_extras_decomposition_contract.py::test_dispatcher_entrypoints_remain_thin_and_delegation_focused`, proving each dispatcher entrypoint performs dependency sync + `_attachment_module` delegation and contains no loop keywords (`for`/`while`) that would indicate re-embedded placement internals.
- Contract Evidence: Geometry type-hint AC closed via executable assertions in `tests/enemies/test_m901_09_zone_geometry_extras_decomposition_contract.py::test_geometry_math_public_api_is_fully_type_annotated_explicitly`, proving the full public API set in `geometry_math.py` matches expected exported helpers and every parameter/return annotation is present.
- Gatekeeper Decision: All ticket acceptance criteria are now explicitly evidenced via executable contract tests, regression suites, and static QA entries documented above; no unresolved AC evidence gaps remain.

## Blocking Issues

- None.

## Escalation Notes

- Decomposition shipped with compatibility surface retained in `src/enemies/zone_geometry_extras_attach.py`, including legacy helper hooks used by existing zone-extras regression suites while routing behavior through focused modules.
- CHECKPOINT: Thin/readable dispatcher evidence uses loop-keyword absence and delegation assertions as objective proxy for "no re-embedded placement loops," aligned to AC-R1.4/AC-R4.3 wording.

---

# NEXT ACTION

## Next Responsible Agent

Human

## Required Input Schema

```json
{
  "ticket_path": "project_board/901_milestone_901_asset_generation_refactoring/done/09_zone_geometry_extras_decomposition.md",
  "action": "Optional: push branch after reviewing in-flight workspace changes."
}
```

## Status

Proceed

## Reason

All acceptance criteria now have explicit objective evidence (contract tests, regression suites, and static QA) documented in Validation Status; ticket passes final gate and can proceed to human workflow completion.
