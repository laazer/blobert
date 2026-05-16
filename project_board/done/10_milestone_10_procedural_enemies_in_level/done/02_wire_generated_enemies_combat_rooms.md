# TICKET: 02_wire_generated_enemies_combat_rooms

Title: Wire generated enemy scenes into combat room templates for procedural runs

## Description

Combat rooms loaded by `RunSceneAssembler` (`res://scenes/rooms/room_combat_*.tscn`) must spawn **game-ready generated enemy scenes** from `res://scenes/enemies/generated/` (or the current canonical output of `generate_enemy_scenes.gd`), not ad-hoc placeholders. Placement uses existing room conventions (e.g. `Marker3D` spawn anchors or documented node paths) so enemies appear at stable positions when the room is instantiated during a run.

Define which **enemy_id / family** each combat template uses (at least one variant per family intended for M10), and ensure instances are `EnemyInfection3D` (or the agreed wrapper) with correct collision layers, `enemy_family`, `mutation_drop`, and animation root wiring consistent with M5/M7.

## Acceptance Criteria

- At least one `room_combat_*.tscn` used in `RunSceneAssembler.POOL["combat"]` instantiates enemies from **generated** `.tscn` paths (not legacy generic enemy stubs), or a small documented spawn helper under the room root achieves the same at `_ready()`.
- Spawned enemies load without error when the full run sequence is started from the main game path (no editor-only manual instance requirement).
- `enemy_id` / `enemy_family` / `mutation_drop` match the generated scene contract used elsewhere (see `tests/scenes/enemies/` patterns).
- `timeout 300 ci/scripts/run_tests.sh` exits 0 (new or updated tests as needed).

## Dependencies

- `01_spec_procedural_enemy_spawn_attack_loop` (soft if spec and impl are parallelized — prefer spec first)
- M5 — generated scenes and `EnemyBase` metadata
- M6 — `RunSceneAssembler` / room pool
- M9 — coordinate mesh/material readiness (soft; wiring may land before final art)

## Functional and Non-Functional Specification

### Requirement R1 — Canonical generated-enemy source and declaration ownership

#### 1. Spec Summary
- **Description:** Combat-room enemy wiring must consume generated enemy scenes from the canonical generator output root, with `res://scenes/enemies/generated/` as the normative v1 source. Combat-room declarations are the authoritative source for what families can spawn in each room.
- **Constraints:** No global cross-room enemy declaration registry is introduced in this ticket. Any future root change must be explicitly versioned and declared.
- **Assumptions:** `RunSceneAssembler.POOL["combat"]` remains the source for active combat room templates.
- **Scope:** `room_combat_*.tscn` templates used in procedural runs and their runtime spawn declaration data.

#### 2. Acceptance Criteria
- AC-R1.1: Every combat room currently referenced by `RunSceneAssembler.POOL["combat"]` exposes a deterministic declaration block for enemy spawning.
- AC-R1.2: Declaration entries include at minimum `enemy_family`, `min_count`, and `max_count`, with integer bounds and `0 <= min_count <= max_count`.
- AC-R1.3: At least one declaration path per M10 family (`acid`, `adhesion`, `carapace`, `claw`) exists across the combat room set.
- AC-R1.4: Declared scene source resolves to generated assets from the canonical root; legacy non-generated placeholders are not authoritative.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Mixed legacy room content can create double-spawn behavior.
- **Risk:** Declaration shape drift between combat rooms can break parser consistency.
- **Ambiguity resolved:** Canonical source root flexibility is handled through checkpointed assumption: v1 locks to `res://scenes/enemies/generated/` unless explicitly versioned.

#### 4. Clarifying Questions
- Would future generator-output relocation require runtime fallback search or strict fail-fast?  
  Resolved for this ticket: strict canonical root in v1, with explicit versioned migration only.

---

### Requirement R2 — Room-level wiring strategy and spawn anchor contract

#### 1. Spec Summary
- **Description:** Enemy placement in combat rooms must be deterministic via room-owned anchor conventions (preferred `Marker3D` anchors) with a defined runtime fallback if anchors are missing.
- **Constraints:** `Entry` and `Exit` markers remain reserved for room-chain placement and cannot be repurposed as enemy anchors.
- **Assumptions:** Existing room scenes may initially rely on fallback while transitioning to explicit enemy anchors.
- **Scope:** Combat room scene graphs and runtime spawn placement behavior.

#### 2. Acceptance Criteria
- AC-R2.1: Enemy spawn anchors follow `EnemySpawn_<index>` naming (1-based, contiguous without gaps per room).
- AC-R2.2: Anchor nodes are `Marker3D` instances reachable from room root.
- AC-R2.3: Anchor local `z` is constrained to lane convention (`z == 0.0` with tolerance <= 0.01).
- AC-R2.4: If zero valid anchors are present, runtime uses deterministic room fallback placement rather than failing run assembly.
- AC-R2.5: Spawn ordering across anchors is deterministic given identical room data and RNG seed.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Existing room assets may not yet include valid enemy anchors.
- **Risk:** Improper fallback can silently place enemies in invalid geometry.
- **Ambiguity resolved:** Canonical approach is room-owned anchors with deterministic fallback, not ad-hoc per-room script behavior.

#### 4. Clarifying Questions
- Should this ticket require all combat rooms to be fully anchorized immediately?  
  Resolved for this ticket: no; fallback is allowed but must be deterministic and testable.

---

### Requirement R3 — Spawned scene runtime contract (`EnemyInfection3D` compatibility)

#### 1. Spec Summary
- **Description:** Spawned generated enemy instances must be runtime-compatible with `EnemyInfection3D` behavior and metadata contract.
- **Constraints:** Direct `EnemyInfection3D` roots are preferred; wrapper/adaptor is allowed only if behavior is equivalent at runtime.
- **Assumptions:** Generated scenes expose or can be mapped to required metadata fields.
- **Scope:** Spawned instance root type, family metadata, mutation metadata, collision and animation wiring.

#### 2. Acceptance Criteria
- AC-R3.1: Spawned instances expose effective `enemy_family` and `mutation_drop` values consistent with generated-scene contract expectations.
- AC-R3.2: Spawned instances are behavior-compatible with `EnemyInfection3D` runtime integration (state machine and attack script wiring available through direct root or strict adaptor).
- AC-R3.3: Collision layers/masks are valid for enemy-vs-player interaction path used by current combat runtime.
- AC-R3.4: Animation root wiring required by enemy runtime and attacks remains intact after spawn integration.
- AC-R3.5: Missing or malformed metadata in one declaration path emits actionable warning and skips that spawn path without crashing full run setup.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Some generated scenes may still be rooted differently, creating integration drift.
- **Risk:** Metadata mismatch can silently degrade behavior unless explicitly validated.
- **Ambiguity resolved:** Wrapper permissibility is limited to strict compatibility, not arbitrary substitution.

#### 4. Clarifying Questions
- Must wrappers be forbidden outright to simplify tests?  
  Resolved for this ticket: wrappers allowed only under strict equivalence constraints to avoid blocking existing assets.

---

### Requirement R4 — RunSceneAssembler integration boundaries and failure handling

#### 1. Spec Summary
- **Description:** Generated-enemy spawn wiring is integrated into combat room runtime without changing room-chain assembly ordering semantics.
- **Constraints:** `RunSceneAssembler` room sequencing and room placement contract are preserved.
- **Assumptions:** Spawn wiring executes after room instance materializes but before combat starts.
- **Scope:** `RunSceneAssembler` combat-room instantiation phase and immediate post-instantiation spawn phase.

#### 2. Acceptance Criteria
- AC-R4.1: Room sequence/category flow remains unchanged from pre-ticket behavior.
- AC-R4.2: Spawn wiring runs automatically on standard game path entry (no editor/manual intervention).
- AC-R4.3: Generated scene path resolution/instantiation failure is isolated to failed spawn entries and does not abort whole run assembly.
- AC-R4.4: Failure logs include room identifier, family, and reason for diagnosis.
- AC-R4.5: Legacy embedded generic enemy stubs do not produce duplicate authoritative enemy population once generated wiring is active.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Timing races can occur if spawn hooks run before room node hierarchy is ready.
- **Risk:** Partial-failure handling can hide severe content issues if warnings are not actionable.
- **Ambiguity resolved:** Integration is additive post-instantiation wiring, not a rewrite of assembler room-chain logic.

#### 4. Clarifying Questions
- Should first spawn failure hard-stop run startup for fast feedback?  
  Resolved for this ticket: no; isolate failures, log explicitly, keep run functional.

---

### Requirement R5 — Non-functional requirements (determinism, robustness, and validation)

#### 1. Spec Summary
- **Description:** Wiring must satisfy deterministic behavior, robustness under missing content, and full regression validation through existing CI entrypoint.
- **Constraints:** No editor-only dependence; no nondeterministic scene-selection side effects outside seed-driven behavior.
- **Assumptions:** The main validation gate remains `timeout 300 ci/scripts/run_tests.sh`.
- **Scope:** Procedural run startup path, combat-room spawn consistency, and automated verification workflow.

#### 2. Acceptance Criteria
- AC-R5.1: Identical seed + identical room declarations produce identical family/variant spawn outcomes.
- AC-R5.2: Missing generated assets or invalid declarations do not crash process; they produce explicit warnings/errors with context.
- AC-R5.3: Runtime overhead remains bounded to per-room/per-spawn operations (no unbounded global scan introduced by this ticket).
- AC-R5.4: Full regression command `timeout 300 ci/scripts/run_tests.sh` exits `0` after implementation and required test updates.
- AC-R5.5: Specification-to-test traceability exists: every AC in R1-R5 maps to at least one deterministic test assertion in downstream TEST_DESIGN output.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Determinism can regress if variant selection bypasses existing seeded selection path.
- **Risk:** CI pass criteria may be blocked by unrelated pre-existing failures.
- **Ambiguity resolved:** This ticket still requires green full-suite result as acceptance gate; if external failures exist, they must be documented as blockers by downstream agents.

#### 4. Clarifying Questions
- If unrelated CI failures persist, should this ticket be blocked or conditionally advanced?  
  Resolved for this ticket: conditional advancement is not allowed for closure; blockers must be explicitly documented.

## WORKFLOW STATE

Stage: COMPLETE
Revision: 15
Last Updated By: Acceptance Criteria Gatekeeper Agent
Next Responsible Agent: Human
Status: Proceed
Validation Status: Acceptance-criteria gate review completed with explicit closure evidence. Automated validation is documented as passing via `timeout 300 godot --headless -s tests/run_tests.gd` exit 0 and `timeout 300 ci/scripts/run_tests.sh` exit 0. Ticket-level closure evidence states arbitration constraints are resolved and implemented in current runtime wiring/tests, and ticket residence in milestone `done/` now satisfies Stage/folder enforcement for `COMPLETE`.
Blocking Issues: None.
Escalation Notes: Ticket is eligible for human handoff/merge review; no unresolved acceptance-criteria evidence gaps identified in ticket record.

## NEXT ACTION

Next Responsible Agent: Human
Required Input Schema: {"ticket_path":"project_board/10_milestone_10_procedural_enemies_in_level/done/02_wire_generated_enemies_combat_rooms.md","required_handoff_action":"human_merge_or_follow_on_repo_handoff","evidence":{"godot_headless":"timeout 300 godot --headless -s tests/run_tests.gd -> exit 0","full_ci":"timeout 300 ci/scripts/run_tests.sh -> exit 0","arbitration":"resolved_and_implemented","folder_rule":"ticket_in_done_path_and_stage_complete_aligned"}}
Status: Proceed
Reason: All acceptance criteria have explicit documented evidence (automated test exits and arbitration-resolution note), and Stage/folder consistency is now satisfied; ticket can be treated as complete.
