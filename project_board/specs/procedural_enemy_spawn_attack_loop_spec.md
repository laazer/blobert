# Procedural Enemy Spawn + Attack Loop Specification (M10-01)

Status: Approved for implementation handoff  
Ticket: `project_board/10_milestone_10_procedural_enemies_in_level/in_progress/01_spec_procedural_enemy_spawn_attack_loop.md`  
Owner: Spec Agent  
Revision: 1

## Scope and Traceability

This specification defines the runtime contract for:
- how combat rooms declare which generated enemy scene(s) may spawn;
- spawn anchor naming and transform invariants;
- static scene content vs runtime wiring ownership between room scenes and run assembly systems;
- per-family attack-loop behavior contract and state gating;
- deterministic headless validation hooks.

Referenced code paths (authoritative current behavior baseline):
- `scripts/system/run_scene_assembler.gd`
- `scripts/system/room_chain_generator.gd`
- `scenes/rooms/room_combat_01.tscn`
- `scenes/rooms/room_combat_02.tscn`
- `scenes/enemies/generated/*.tscn`
- `scripts/enemy/enemy_infection_3d.gd`
- `scripts/enemy/enemy_state_machine.gd`
- `scripts/enemy/acid_spitter_ranged_attack.gd`
- `scripts/enemy/adhesion_bug_lunge_attack.gd`
- `scripts/enemy/carapace_husk_attack.gd`
- `scripts/enemy/claw_crawler_attack.gd`
- `scripts/system/enemy_visual_variant_selector.gd`

## ADR Decisions (Resolved Ambiguities)

1. **ADR-01: Room-owned declaration source**
   - Decision: Combat rooms own enemy spawn declarations through room-local metadata/exports (not a shared global spawn registry).
   - Rationale: `run_scene_assembler.gd` already assembles room instances category-first; per-room ownership keeps room semantics local and avoids cross-room coupling.
   - Rejected: global shared enemy registry as authoritative spawn source for room composition.

2. **ADR-02: Runtime-generated enemy instantiation**
   - Decision: Combat rooms no longer hardcode a live enemy instance as the normative contract; runtime spawn from generated scenes is the normative path.
   - Rationale: Existing combat rooms currently embed `enemy_infection_3d.tscn`, which conflicts with generated-scene selection goals.
   - Compatibility: Existing embedded instance is legacy-compatible during transition but is non-authoritative.

3. **ADR-03: State gate interpretation**
   - Decision: Attack scripts MUST treat `dead` as hard stop; `weakened` and `infected` remain attack-capable unless a family contract explicitly disables them.
   - Rationale: Current scripts gate only on `dead`; state constants are lowercase in `EnemyStateMachine`.
   - Rejected: implicit disable of attacks for `weakened`/`infected` without explicit family rule.

---

### Requirement R1 — Combat room enemy scene declaration contract

#### 1. Spec Summary
- **Description:** Each combat room scene must declare a deterministic list of spawnable enemy families and per-family count bounds. Declarations are room-local data consumed at runtime after room instantiation.
- **Constraints:** Declarations apply only to combat categories selected by `RoomChainGenerator` via `run_scene_assembler.gd` sequence/pool flow. Non-combat rooms ignore declaration fields.
- **Assumptions:** Runtime spawn service resolves family -> generated `.tscn` path using manifest-backed family/version records.
- **Scope:** Combat room scenes under `scenes/rooms/` used by `POOL["combat"]`.

#### 2. Acceptance Criteria
- AC-R1.1: A combat room declaration format exists and is uniform across all combat room scenes in use by `POOL["combat"]`.
- AC-R1.2: Declaration supports at minimum: `family`, `min_count`, `max_count`; `min_count <= max_count`; both non-negative integers.
- AC-R1.3: Runtime selection of visual variant for a declared family uses `enemy_visual_variant_selector.gd` eligibility rules (in-use and non-draft only).
- AC-R1.4: If a declared family has zero eligible generated variants, spawn for that family is skipped and a warning is emitted; run assembly does not crash.
- AC-R1.5: Existing hardcoded room enemy node(s) are ignored or removed from authoritative spawn counts; they cannot cause double-spawn against declaration counts.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Current combat rooms contain pre-placed enemy instances, creating transitional double-spawn risk.
- **Risk:** Declaration schema drift across rooms can cause inconsistent runtime parsing.
- **Ambiguity handled:** Whether declarations live in shared registry vs room scenes resolved by ADR-01.

#### 4. Clarifying Questions
- None. Conservatively resolved by ADR-01/02.

---

### Requirement R2 — Spawn anchor naming and transform invariants

#### 1. Spec Summary
- **Description:** Combat room spawn points must be represented by `Marker3D` anchors named using a strict prefix convention and validated transform rules.
- **Constraints:** `Entry` and `Exit` anchors remain reserved for room chain placement and cannot be repurposed as enemy spawn anchors.
- **Assumptions:** World is effectively 2.5D; spawn lane uses `z = 0` convention unless explicitly overridden by room contract extension.
- **Scope:** Combat room scene graph and runtime spawn placement.

#### 2. Acceptance Criteria
- AC-R2.1: Enemy spawn anchors use name pattern `EnemySpawn_<index>` (1-based contiguous index, no gaps).
- AC-R2.2: Each anchor must be a direct or descendant `Marker3D` under the room root.
- AC-R2.3: Anchor local `z` must equal `0.0` (tolerance <= 0.01) unless room explicitly opts into nonzero z-lane (not part of this ticket).
- AC-R2.4: Anchor local `y` must be on/above room floor surface; if below floor, spawn is rejected with warning and fallback anchor search continues.
- AC-R2.5: When no valid enemy spawn anchors exist, runtime uses a deterministic fallback point at room midpoint `(Entry.x + Exit.x)/2`, floor-adjusted y, `z=0`.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Existing rooms currently do not define `EnemySpawn_*` anchors; fallback will be exercised initially.
- **Risk:** Floor-height derivation may differ by room geometry; requires conservative y validation.
- **Ambiguity handled:** Spawn anchor naming not present in repository baseline; resolved with strict prefix and deterministic fallback.

#### 4. Clarifying Questions
- None. Conservative naming and fallback selected to unblock deterministic tests.

---

### Requirement R3 — Runtime assembly ownership boundaries

#### 1. Spec Summary
- **Description:** `RunSceneAssembler` remains responsible for room chain instantiation/positioning; enemy spawn population is a post-room-instantiation runtime phase and must not mutate room-chain generation semantics.
- **Constraints:** `RoomChainGenerator` stays pure deterministic `RefCounted` and enemy spawn logic must not move into it.
- **Assumptions:** Room category sequencing (`intro`, `combat`, `combat`, `mutation_tease`, `boss`) remains unchanged for this contract.
- **Scope:** `run_scene_assembler.gd`, room scenes, and enemy spawn wiring layer.

#### 2. Acceptance Criteria
- AC-R3.1: Room assembly order and cursor/exit positioning behavior of `RunSceneAssembler` remains unchanged.
- AC-R3.2: Enemy spawn population executes only after combat room instance exists in tree (or deferred equivalent) and before gameplay begins for that room.
- AC-R3.3: Spawned enemy root node contract must be `EnemyInfection3D` runtime behavior-compatible (signals, state machine, attack script attachment by `mutation_drop`).
- AC-R3.4: Spawn pipeline validates generated scene path existence under `scenes/enemies/generated/` before instantiation.
- AC-R3.5: Spawn pipeline failure in one room/family does not abort entire run scene assembly.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Deferred add-child timing in current `RunSceneAssembler` can create race if spawn logic assumes immediate tree presence.
- **Risk:** Generated scenes currently use `EnemyBase`; integration must preserve expected `EnemyInfection3D` interactions or provide adapter path.
- **Ambiguity handled:** Static vs runtime ownership split resolved by preserving current room-chain ownership and adding post-instantiation spawn phase.

#### 4. Clarifying Questions
- None. Conservative no-regression boundary chosen.

---

### Requirement R4 — Attack-loop family contract and state interactions

#### 1. Spec Summary
- **Description:** Each enemy family attack loop is defined by aggro trigger range, telegraph behavior, cooldown bounds, and state gating against `EnemyStateMachine`.
- **Constraints:** Family behavior must match current baseline scripts unless explicitly versioned. `dead` is universal no-attack state.
- **Assumptions:** State values are lowercase (`idle`, `active`, `weakened`, `infected`, `dead`) as defined in `enemy_state_machine.gd`.
- **Scope:** Attack scripts in `scripts/enemy/*_attack.gd` and enemy runtime integration in `enemy_infection_3d.gd`.

#### 2. Acceptance Criteria
- AC-R4.1: **Acid Spitter** (`mutation_drop="acid"`): engages when player distance `<= attack_range` (default 8.0), telegraphs then fires projectile, then cooldown (default 3.0s).
- AC-R4.2: **Adhesion Bug** (`mutation_drop="adhesion"`): engages at `<= attack_range` (default 3.0), telegraphs then lunge window, optional player root on hit, then cooldown (default 2.0s).
- AC-R4.3: **Carapace Husk** (`mutation_drop="carapace"`): engages at `<= attack_range` (default 6.0), telegraph, charge with collision/range stop, deceleration, cooldown (default 4.0s).
- AC-R4.4: **Claw Crawler** (`mutation_drop="claw"`): engages at `<= attack_range` (default 2.0), two-swipe combo with inter-swipe pause and cooldown (default 1.2s).
- AC-R4.5: For all families, attack acquisition requires player in group `player`; null player target yields no attack cycle start.
- AC-R4.6: For all families, `EnemyStateMachine` state `dead` blocks attack cycle start and execution continuation where checked.
- AC-R4.7: `weakened` and `infected` states do not automatically suppress attacks in v1 contract; suppression would require explicit per-family rule update.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Family tuning defaults are exports and can drift scene-by-scene; tests must assert bounds/behavioral invariants, not only literal defaults.
- **Risk:** Some scripts rely on animation telegraph signals with timer fallback; signal wiring regressions can deadlock attack loops.
- **Ambiguity handled:** Ticket mentions WEAKENED/INFECTED uppercase; canonical runtime values are lowercase and mapped via ADR-03.

#### 4. Clarifying Questions
- None. State semantics resolved with conservative baseline-preserving rule.

---

### Requirement R5 — Headless validation hooks and testability contract

#### 1. Spec Summary
- **Description:** Runtime contracts must expose deterministic, headless-verifiable outcomes without requiring full physics fidelity.
- **Constraints:** Tests may use physics-skipped or controlled-frame progression patterns; assertions must target observable node/state outcomes.
- **Assumptions:** Godot headless tests under existing test harness are the enforcement vehicle.
- **Scope:** Scene assembly, enemy spawn declarations/anchors, generated scene existence, attack loop start/cooldown transitions.

#### 2. Acceptance Criteria
- AC-R5.1: A headless check can enumerate combat rooms selected by assembler and verify declaration schema validity.
- AC-R5.2: A headless check can resolve declared family to at least one eligible generated scene path and assert file existence.
- AC-R5.3: A headless check can validate spawn anchor discovery rules (prefix, index continuity, z=0 invariant, fallback behavior).
- AC-R5.4: A headless check can validate family attack cycle enters active/cooldown states when player proxy enters aggro range.
- AC-R5.5: A headless check can validate dead-state suppression of attacks for every family script.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Over-reliance on real-time timers can cause flaky headless tests; deterministic time stepping is required.
- **Risk:** Physics-dependent collisions (e.g., carapace charge wall stop) need bounded scenario harnesses to stay deterministic.
- **Ambiguity handled:** Optional physics-skipped patterns accepted as long as contractual outcomes are still asserted.

#### 4. Clarifying Questions
- None. Conservative deterministic hooks chosen.

---

### Requirement R6 — Non-functional requirements

#### 1. Spec Summary
- **Description:** Performance, determinism, robustness, and backward compatibility constraints for spawn/attack contract implementation.
- **Constraints:** No regressions to room generation determinism and no hard dependency on editor-only state.
- **Assumptions:** Generated enemy scene set under `scenes/enemies/generated/` remains finite and versioned.
- **Scope:** Runtime assembly and enemy behavior integration.

#### 2. Acceptance Criteria
- AC-R6.1: Spawn resolution for a combat room must be deterministic given identical room declaration data and RNG seed inputs.
- AC-R6.2: Missing generated scene resources or invalid declaration entries produce warnings/errors without process crash.
- AC-R6.3: Runtime per-frame attack logic must remain O(1) per enemy instance (no per-frame global scene scans beyond existing single player lookup baseline).
- AC-R6.4: Transition compatibility: existing rooms without `EnemySpawn_*` anchors still function via fallback placement.
- AC-R6.5: Logging for spawn/selection failure must include room scene path, family, and failure reason.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Determinism can be broken if randomization occurs without seed-coupled RNG.
- **Risk:** Backward compatibility path may hide invalid room data too long; warnings must be actionable.
- **Ambiguity handled:** Compatibility retained while enforcing stricter future contract through warnings and tests.

#### 4. Clarifying Questions
- None. Non-functional constraints are explicit and testable.

---

## Downstream Handoff (Binding)

- Ticket `02_wire_generated_enemies_combat_rooms` must implement R1/R2/R3/R6 first.
- Ticket `03_procedural_enemy_attack_loop_runtime` must implement/validate R4/R5 with state-gating coverage.
- Any deviation from ADR-01/02/03 requires explicit ticket-level ADR update before implementation.
