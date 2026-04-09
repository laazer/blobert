# TICKET: 08_runtime_spawn_random_enemy_visual_variant

Title: Runtime — random visual variant per enemy type among active in-use versions

## Description

When spawning an enemy of a given **type/family**, choose **uniformly or weighted-random** among **in-use** version entries in the registry (same `EnemyBase` / collision / animation contract; different GLB/visual only). If exactly one version exists, behavior matches today. Integrate at the **single spawn choke point** used by procedural runs and sandbox (coordinate with M10 `02_wire_generated_enemies_combat_rooms` and follow-on spawn helpers).

## Acceptance Criteria

- Two consecutive spawns of the same type can yield different visuals when multiple versions are registered (manual or automated note).
- Draft models never selected.
- `timeout 300 ci/scripts/run_tests.sh` exits 0 (unit or scene test where feasible).

## Dependencies

- `01_spec_model_registry_draft_versions_and_editor_contract`
- `05_editor_ui_game_model_selection` (registry must hold version lists)
- M10 — `02_wire_generated_enemies_combat_rooms` (soft; sandbox can prove behavior first)

---

# Project: Runtime Enemy Visual Variant Selection
**Description:** Introduce deterministic-contract runtime selection of non-draft, in-use visual variants per enemy family, then wire selection through the shared runtime spawn choke point used by sandbox and procedural combat-room flows.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Produce formal spawn-variant specification (selection semantics, eligibility filters, failure behavior, and integration boundaries). | Spec Agent | This ticket; `project_board/9_milestone_9_enemy_player_model_visual_polish/done/01_spec_model_registry_draft_versions_and_editor_contract.md`; `project_board/9_milestone_9_enemy_player_model_visual_polish/done/05_editor_ui_game_model_selection.md`; `project_board/10_milestone_10_procedural_enemies_in_level/backlog/02_wire_generated_enemies_combat_rooms.md`; runtime entrypoints (`scripts/system/run_scene_assembler.gd`, current room/spawn helpers). | Written spec with requirement IDs covering: (a) uniform random default over in-use versions, (b) draft exclusion invariant, (c) single-version no-op parity, (d) shared choke-point contract for sandbox + procedural use, (e) deterministic test hooks/seed strategy. | None | Spec is unambiguous, maps to AC bullets, and defines exact files/interfaces the implementation will change. | Assumes weighted selection is deferred; if existing registry weights already exist, spec may allow optional extension without changing default behavior. |
| 2 | Author primary behavioral tests for runtime variant selection and spawn-path integration. | Test Designer Agent | Approved spec from Task 1; relevant tests under `tests/levels/`, `tests/rooms/`, and registry API/unit suites where needed. | Failing tests that prove: consecutive same-family spawns can resolve to different in-use visuals; drafts are never selected; single-version families remain stable; sandbox/procedural path consumes same selection helper/contract. | 1 | New tests fail for the right reason before implementation and include clear requirement traceability IDs. | Current spawn choke point may be partially in M10 backlog; tests should target the smallest currently executable seam and document deferred integration assertions. |
| 3 | Expand adversarial coverage for selection fairness/invariants and malformed registry states. | Test Breaker Agent | Task 2 tests + Task 1 spec. | Additional failing adversarial tests for: empty eligible list handling, malformed or duplicate version metadata, deterministic behavior under seeded randomness, no draft leakage under mixed registry state, and stable behavior when only one active version exists. | 2 | Adversarial suite closes bypass paths and prevents silent fallback to draft or non-eligible entries. | Assumes runtime can consume registry snapshot safely without editor context; if not, tests encode conservative fail-closed behavior. |
| 4 | Implement runtime selector + choke-point integration in gameplay/runtime code. | Engine Integration Agent | Approved spec + failing primary/adversarial tests. | Code changes to add or update a shared enemy visual-resolution helper, wire it at runtime spawn choke point(s), preserve existing EnemyBase/collision/animation contract, and keep draft versions excluded. | 3 | All Task 2/3 tests pass; implementation touches only required runtime surfaces and keeps behavior unchanged when one version is available. | If M10 combat-room wiring is not yet merged, implement helper + currently reachable integration seam and leave explicit TODO-free contract hooks documented in ticket state notes. |
| 5 | Run static QA + full integration validation, then gate against acceptance criteria. | Acceptance Criteria Gatekeeper Agent | Implemented code/tests from Task 4. | Verification evidence including targeted suites and `timeout 300 ci/scripts/run_tests.sh` output; AC matrix mapped to tests/manual note; final routing decision (Proceed/Blocked/Complete). | 4 | Command exits 0; AC evidence explicitly shows variant diversity, draft exclusion, and no regression in existing spawn flow. | RNG-dependent checks can be flaky if underspecified; gatekeeper should require deterministic seed control in tests to avoid non-reproducible outcomes. |

## Specification

### Requirement RSEVV-F1 — Eligible visual variant set resolution

#### 1. Spec Summary
- **Description:** For a spawn request targeting an enemy family/type slug, runtime must construct an eligible visual variant list from registry entries marked both non-draft and in-use for that same family/type. Eligibility is evaluated at spawn time from the current runtime-visible registry snapshot.
- **Constraints:** Eligibility filtering must not widen or reinterpret registry semantics defined by upstream registry contracts; entries outside the requested family/type are never considered.
- **Assumptions:** Registry data available to runtime includes enough per-version metadata to determine family/type identity and draft/in-use status.
- **Scope:** Runtime selection helper and its immediate caller(s) at the spawn choke point.

#### 2. Acceptance Criteria
- For a family/type with versions `{v1(in-use, non-draft), v2(in-use, non-draft), v3(draft), v4(not in-use)}`, eligible set is exactly `{v1, v2}`.
- If no versions are eligible, runtime must fail closed (explicit error or spawn refusal) rather than silently selecting a draft or out-of-scope entry.
- Eligibility decision is invariant to ordering of version records in registry input.

#### 3. Risk & Ambiguity Analysis
- Risk: malformed registry entries could bypass filters if status keys are missing or loosely typed.
- Risk: family/type alias drift (different slugs for same enemy concept) can produce empty eligible sets unexpectedly.
- Ambiguity: exact shape of registry snapshot consumed by runtime may vary by integration seam; implementation must normalize at one seam only.

#### 4. Clarifying Questions
- Which concrete runtime API currently provides the registry snapshot for spawn-time consumption in sandbox and procedural paths?

### Requirement RSEVV-F2 — Selection semantics (uniform default, optional weight extension)

#### 1. Spec Summary
- **Description:** When eligible set size is `N > 1`, runtime selects exactly one variant using uniform random probability over eligible entries by default. Weighted random is out of scope unless existing registry metadata already defines stable, validated weights; if weights exist, default behavior remains uniform unless explicitly enabled by existing contract.
- **Constraints:** No deterministic preference for first/last entry; exactly one winner per spawn request.
- **Assumptions:** Existing gameplay does not depend on deterministic variant identity when multiple eligible variants are available.
- **Scope:** Variant picker logic only; not editor controls or registry schema expansion.

#### 2. Acceptance Criteria
- With two eligible variants and deterministic seeded RNG, repeated spawn attempts produce both variants across a bounded run (for example, at least one selection of each within 20 picks under fixed seed and stable algorithm).
- Without seed override, selector uses normal runtime randomness path.
- If optional weights are absent, invalid, or disabled by contract, selector falls back to uniform behavior.

#### 3. Risk & Ambiguity Analysis
- Risk: flaky tests if randomness is validated without seed control.
- Risk: introducing weighted branch accidentally changes baseline spawn distribution and causes unintended balance drift.
- Ambiguity: if pre-existing weight metadata exists, the enabling condition must be explicit and testable.

#### 4. Clarifying Questions
- Does any current runtime consumer already require weighted behavior from registry metadata today?

### Requirement RSEVV-F3 — Single-version parity and contract preservation

#### 1. Spec Summary
- **Description:** If eligible set size is exactly one, runtime must resolve the same visual deterministically every time and preserve current gameplay contract (same enemy logic script, collision behavior, attack wiring, and animation-controller integration).
- **Constraints:** This ticket may alter only visual variant resolution; no behavior divergence is allowed in combat/movement contracts.
- **Assumptions:** Existing enemy scene/script architecture already decouples visuals from behavior logic.
- **Scope:** Spawn resolution output and downstream spawn invocation parameters.

#### 2. Acceptance Criteria
- For a family/type with one eligible version, consecutive spawns always resolve that same version.
- Existing spawn consumers continue instantiating expected enemy behavior classes/components.
- No new required configuration fields are introduced for families with one eligible version.

#### 3. Risk & Ambiguity Analysis
- Risk: accidental coupling between visual asset path and script attachment could change behavior.
- Risk: hidden reliance on visual path string in downstream systems could regress.
- Ambiguity: some generated scenes may embed both visual and logic assumptions; integration tests must detect parity breakage.

#### 4. Clarifying Questions
- Are there any known spawn consumers that branch behavior by visual asset path string instead of family/type?

### Requirement RSEVV-F4 — Shared spawn choke-point integration

#### 1. Spec Summary
- **Description:** A single shared runtime seam must perform visual variant resolution and be consumed by both sandbox and procedural spawn flows. If M10 procedural wiring is incomplete, current reachable seam must still adopt the shared helper contract so future integration is additive rather than duplicative.
- **Constraints:** Duplicate ad-hoc selection logic across spawn call sites is disallowed.
- **Assumptions:** A practical choke point exists or can be introduced without broad refactor.
- **Scope:** Runtime spawn orchestration surfaces (for example scene assembler/spawn helpers) and selector helper interface.

#### 2. Acceptance Criteria
- Sandbox spawn path invokes shared selector seam.
- Procedural path either invokes same seam now or is contractually wired to consume it at existing integration boundary without changing selector semantics.
- No alternate spawn path retains legacy direct visual selection logic once this ticket’s implementation is complete.

#### 3. Risk & Ambiguity Analysis
- Risk: partial M10 progress can hide additional spawn entrypoints and cause logic drift.
- Risk: integration done in two tickets may temporarily leave dual behavior unless constrained now.
- Ambiguity: definitive “single choke point” file/function name may evolve as M10 lands; requirement is semantic, not path-string specific.

#### 4. Clarifying Questions
- Which currently shipping procedural entrypoint is authoritative for spawn instantiation in this branch state?

### Requirement RSEVV-F5 — Deterministic test hook for randomness

#### 1. Spec Summary
- **Description:** Selector contract must support deterministic test execution via injected RNG seam, seed parameter, or equivalent mechanism that avoids mutating global randomness state used by unrelated systems.
- **Constraints:** Deterministic hook is for testing and controlled runtime scenarios; normal gameplay path remains unchanged when hook is absent.
- **Assumptions:** Test harness can access selector seam directly or through spawn seam wrapper.
- **Scope:** Selector function signature and test-facing invocation pathway.

#### 2. Acceptance Criteria
- Given same eligible set and same deterministic hook/seed, repeated runs produce identical selection sequence.
- Deterministic hook is optional; absence does not throw or change existing call contracts beyond documented optional parameters.
- Tests can assert draft exclusion and single-version parity without probabilistic flakiness.

#### 3. Risk & Ambiguity Analysis
- Risk: using global RNG seed could couple unrelated tests and create order-dependent failures.
- Risk: exposing deterministic knobs to production paths without guardrails may encourage misuse.
- Ambiguity: exact seam shape (callable RNG vs seed vs wrapper object) is implementation-defined, but behavior must satisfy deterministic reproducibility.

#### 4. Clarifying Questions
- Should deterministic hook be limited to internal runtime/testing APIs, or exposed through any external tooling surface?

### Requirement RSEVV-NF1 — Reliability and fail-closed behavior

#### 1. Spec Summary
- **Description:** Runtime must prefer explicit failure over unsafe fallback when eligibility cannot be proven (for example empty eligible set, malformed status fields).
- **Constraints:** No silent substitution to draft versions or unrelated family visuals.
- **Assumptions:** Existing error handling path can propagate spawn refusal safely.
- **Scope:** Selector/seam error path semantics.

#### 2. Acceptance Criteria
- Empty eligible set is surfaced as explicit non-success outcome.
- Malformed candidate metadata cannot be interpreted as eligible by default.
- Failure path is observable to tests (return status, error signal, or equivalent deterministic contract).

#### 3. Risk & Ambiguity Analysis
- Risk: overly hard failure may reduce resilience if registry data transiently incomplete.
- Ambiguity: exact signaling mechanism may vary by runtime surface; must still be machine-testable.

#### 4. Clarifying Questions
- Which existing spawn error channel is the canonical place for fail-closed selector outcomes?

### Requirement RSEVV-NF2 — Performance and allocation envelope

#### 1. Spec Summary
- **Description:** Variant resolution overhead per spawn must remain bounded and lightweight relative to spawn itself; avoid repeated full-registry rescans when a narrower family/type subset is available.
- **Constraints:** No heavy per-spawn allocations or synchronous file I/O introduced by selector logic.
- **Assumptions:** Registry snapshot is already in memory during runtime spawn operations.
- **Scope:** Selector implementation internals and spawn seam call frequency.

#### 2. Acceptance Criteria
- Selector complexity is linear in candidate count for target family/type, not total unrelated registry entries where avoidable.
- No new runtime disk access is required to select a variant.
- Spawn path remains functionally responsive under repeated spawns in sandbox/procedural loops.

#### 3. Risk & Ambiguity Analysis
- Risk: naive filtering over full registry for every spawn can scale poorly in large registries.
- Ambiguity: precise performance budget is not formally benchmarked in this ticket; guardrails are qualitative but testable via structure and absence of I/O.

#### 4. Clarifying Questions
- Is there an existing cached per-family active-version index that selector should reuse?

### Requirement RSEVV-NF3 — Observability and diagnosability

#### 1. Spec Summary
- **Description:** Selection outcomes and fail-closed cases must be diagnosable during development/test runs without requiring debugger attachment.
- **Constraints:** Logging/diagnostic output must not leak unrelated sensitive host path details.
- **Assumptions:** Existing project logging patterns can be reused for spawn/runtime systems.
- **Scope:** Runtime diagnostics at selector/seam boundary.

#### 2. Acceptance Criteria
- When selection succeeds, diagnostics can identify selected family/type and resolved variant identity in a test-observable form.
- When selection fails, diagnostics identify failure class (for example no eligible variants) without exposing forbidden path details.
- Diagnostic behavior is stable enough for deterministic assertions where tests rely on explicit status channels.

#### 3. Risk & Ambiguity Analysis
- Risk: insufficient diagnostics will slow defect isolation in mixed sandbox/procedural flows.
- Risk: overly verbose logging may create noise and mask real failures.
- Ambiguity: final diagnostic channel (return object vs logger-only) depends on existing runtime conventions.

#### 4. Clarifying Questions
- Should selector emit structured diagnostics through return values, logs, or both for this milestone?

## Notes
- Tasks are sequential and independently executable once dependencies are satisfied.
- Conservative checkpoint assumptions applied: default selection policy is uniform random among in-use versions; weighted behavior is out-of-scope unless already contractually present in registry metadata.
- Ambiguity boundary: this ticket owns runtime selection contract and current spawn seam integration; cross-ticket room-wiring changes from M10 remain soft dependencies and must not block sandbox proof path.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
10

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- AC1 satisfied: variant diversity evidenced by `test_rsevv_t_02_same_family_can_resolve_different_visuals` (same family can resolve different visuals with deterministic sequence control).
- AC2 satisfied: draft/ineligible exclusion evidenced by `test_rsevv_t_03_draft_and_not_in_use_never_selected` plus adversarial guards (`test_rsevv_adv_03_malformed_status_metadata_is_rejected_fail_closed`, `test_rsevv_adv_05_rng_out_of_range_values_are_clamped_and_never_leak_ineligible`).
- AC3 satisfied: `timeout 300 ci/scripts/run_tests.sh` recorded exit code `0` (2026-04-09).
- Folder-stage consistency satisfied: ticket resides in milestone `done/` path and is eligible for Stage `COMPLETE`.

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
  "ticket_path": "project_board/9_milestone_9_enemy_player_model_visual_polish/done/08_runtime_spawn_random_enemy_visual_variant.md",
  "workflow_module": "agent_context/agents/common_assets/workflow_enforcement_v1.md",
  "checkpoint_protocol": "agent_context/agents/common_assets/checkpoint_protocol_v1.md"
}
```

## Status
Proceed

## Reason
All listed acceptance criteria have explicit test/run evidence and folder-stage consistency is now satisfied in `done/`; ticket is closed and routed to Human for normal post-closure handling.
