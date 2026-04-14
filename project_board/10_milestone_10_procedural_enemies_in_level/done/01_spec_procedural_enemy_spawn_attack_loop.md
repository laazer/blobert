# TICKET: 01_spec_procedural_enemy_spawn_attack_loop

Title: Specification — procedural enemy spawn points, scene selection, and attack-loop contract

## Description

Author `project_board/specs/procedural_enemy_spawn_attack_loop_spec.md` that locks contracts before large implementation churn:

- How combat rooms declare **which** generated `.tscn`(s) to spawn (per-room list vs shared registry vs export from room template data).
- **Spawn anchor** naming and transform rules (Marker3D paths, floor height, Z=0 convention).
- Interaction with **RoomChainGenerator** / `RunSceneAssembler` — what is static in `.tscn` vs filled at runtime.
- **Attack loop** expectations per family (aggro range, cooldown bounds, relationship to `EnemyStateMachine` states WEAKENED/INFECTED).
- **Test plan** hooks for headless validation (minimal scene tree checks, file existence, optional physics-skipped patterns).

## Acceptance Criteria

- Spec file exists at `project_board/specs/procedural_enemy_spawn_attack_loop_spec.md`.
- Spec references current code paths (`run_scene_assembler.gd`, combat room scenes, `scenes/enemies/generated/`, enemy attack entry points).
- Ambiguities called out with ADR-style decisions where the repo already chose an approach.
- Downstream tickets (`02_wire_generated_enemies_combat_rooms`, `03_procedural_enemy_attack_loop_runtime`) can be implemented without re-negotiating spawn/attack contracts.

## Dependencies

- M5 / M6 / M8 — existing behavior to document

## Execution Plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Inventory current spawn and attack-loop behavior across runtime and scene assets | Code Explorer Agent | Ticket AC, `scripts/level/run_scene_assembler.gd`, combat room scenes, `scenes/enemies/generated/`, enemy state/attack scripts | Evidence list of current contracts (scene references, spawn anchors, runtime injection points, attack entry points) | None | Evidence covers every path referenced in AC and identifies authoritative files by feature area | Risk: generated assets may be stale; assume repository state is source of truth unless code comments explicitly mark deprecated paths |
| 2 | Resolve contract decisions for scene-selection and spawn-anchor ownership | Spec Agent | Task 1 evidence + ticket description alternatives (per-room list vs shared registry vs template export) | ADR-style decision set documenting chosen approach and rejected alternatives with rationale | 1 | Decision section maps each ambiguity to one explicit contract and leaves no unresolved branching in spawn ownership | Risk: mixed legacy patterns may conflict; assume one normative path can be designated with compatibility notes |
| 3 | Define attack-loop behavioral contract per enemy family/state boundaries | Spec Agent | Task 1 evidence + `EnemyStateMachine` behavior around WEAKENED/INFECTED + enemy attack scripts | Normative contract for aggro trigger expectations, cooldown bounds, and allowed state transitions affecting attacks | 1 | Contract specifies observable behavior and integration boundaries without engine-implementation detail leakage | Risk: family behavior drift across scenes; assume current scripted behavior is baseline for v1 contract |
| 4 | Author full specification document with traceability and headless test hooks | Spec Agent | Outputs from Tasks 1-3 + ticket AC | `project_board/specs/procedural_enemy_spawn_attack_loop_spec.md` with sections for scene declaration, anchors, runtime assembly, attack loop, and test hooks | 2, 3 | Spec path exists; all AC bullets are directly addressed; code-path citations are explicit and unambiguous | Risk: over-specifying implementation details could constrain downstream changes; assume contract-first wording with implementation notes separated |
| 5 | Produce executable test-design plan for contract enforcement | Test Designer Agent | Final spec from Task 4 | Test matrix covering headless scene tree checks, generated-scene existence checks, and attack-loop behavior checks for ticket `03` | 4 | Matrix maps each contract clause to at least one deterministic test and identifies which ticket owns each test | Risk: some runtime checks may require lightweight harness adaptation; assume physics-skipped strategy acceptable when deterministic |
| 6 | Implement spawn wiring and runtime attack loop per approved spec in downstream tickets | Engine Integration Agent (Ticket 02), Gameplay Systems Agent (Ticket 03) | Spec + test plan from Tasks 4-5 | Ticket `02` and `03` implementation-ready contract handoff package and delivery sequence | 5 | Downstream agents can execute without reopening spawn/attack contract negotiations | Risk: cross-agent sequencing drift; assume strict dependency order (`02` spawn wiring before `03` behavior tuning) |

## WORKFLOW STATE

Stage: COMPLETE
Revision: 10
Last Updated By: Acceptance Criteria Gatekeeper Agent
Next Responsible Agent: Human
Status: Proceed
Validation Status:
- AC1 closure evidence: `project_board/specs/procedural_enemy_spawn_attack_loop_spec.md` exists at the required path.
- AC2 closure evidence: spec cites required code paths (`scripts/system/run_scene_assembler.gd`, combat room scenes, `scenes/enemies/generated/`, enemy attack entry points).
- AC3 closure evidence: ADR-01/02/03 call out ambiguities and record chosen contracts plus rejected alternatives.
- AC4 closure evidence: downstream handoff maps ticket `02_wire_generated_enemies_combat_rooms` and `03_procedural_enemy_attack_loop_runtime` to explicit requirement groups, preventing re-negotiation of spawn/attack contracts.
- Validation method: post-move-to-`done/` document audit completed against ticket acceptance criteria and workflow enforcement rules.
- Closure state: acceptance-criteria gate is closed; all listed AC items have explicit in-ticket evidence with no unresolved specification gaps.
Blocking Issues:
- None.

## NEXT ACTION

Next Responsible Agent: Human
Required Input Schema: None.
Status: Proceed
Reason: Post-move acceptance-criteria closure re-run confirms full AC coverage, `done/` folder and `COMPLETE` stage are consistent, and no gatekeeper blockers remain.
