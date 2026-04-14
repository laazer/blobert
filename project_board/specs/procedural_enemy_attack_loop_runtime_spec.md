# Procedural Enemy Attack Loop Runtime Specification (M10-03)

Status: Approved for test design handoff  
Ticket: `project_board/10_milestone_10_procedural_enemies_in_level/in_progress/03_procedural_enemy_attack_loop_runtime.md`  
Upstream spec: `project_board/specs/procedural_enemy_spawn_attack_loop_spec.md` (M10-01)  
Owner: Spec Agent  
Revision: 1

## Purpose

This document **specializes** M10-01 Requirements **R4** (attack-loop family contract) and **R5** (headless validation) for **procedurally spawned** combat-room enemies: instances created from `res://scenes/enemies/generated/*.tscn` via `RunSceneAssembler` spawn pipeline. It binds “continuous attack loop,” M8 plumbing reuse, ESM/stub behavior, `.attacks.json` authority, and test parity (run-assembled vs isolated room) to **observable, testable** contracts.

## Scope and Traceability

| M10-01 ref | M10-03 coverage |
|------------|-----------------|
| R4 family attack ranges, telegraphs, cooldowns, state gating | R1–R3, R6 |
| R5 headless hooks for attack cycle + dead suppression | R4–R5 |
| R3.3 spawn compatibility (`mutation_drop`, attack attachment) | R1–R3 |

**In scope:** Runtime wiring after `RunSceneAssembler._spawn_enemies_for_combat_room` (or successor) adds generated instances to the room tree; family attack scripts; `EnemyAnimationController`; telegraph/hitbox paths used by M8; deterministic tests under `timeout 300 ci/scripts/run_tests.sh`.

**Out of scope for this spec:** Changing Python export of `.attacks.json`; registry editor UX; new enemy families beyond the four in M10-01 R4.

**Authoritative code references (baseline for contracts):**

- `scripts/system/run_scene_assembler.gd` — spawn, metadata (`enemy_family`, `mutation_drop` meta)
- `scripts/enemies/enemy_base.gd` — generated root script; `get_esm()` → `GeneratedEnemyEsmStub`
- `scripts/enemies/enemy_generated_esm_stub.gd` — stub ESM API
- `scripts/enemy/enemy_infection_3d.gd` — M8 host: `_ensure_*_attack_if_needed`, real `EnemyStateMachine`, `EnemyAnimationController.setup`
- `scripts/enemy/enemy_state_machine.gd` — state strings (`idle`, `active`, `weakened`, `infected`, `dead`)
- `scripts/enemy/acid_spitter_ranged_attack.gd`, `adhesion_bug_lunge_attack.gd`, `carapace_husk_attack.gd`, `claw_crawler_attack.gd`
- `scripts/enemies/enemy_animation_controller.gd` — `EnemyAnimationController`

---

## ADR Decisions (M10-03)

### ADR-M10-03-01 — Attack script host contract (M8 parity)

- **Decision:** Procedurally spawned enemies MUST satisfy the **same host contract** that M8 family attack scripts expect today: a parent node that those scripts can bind to for `get_esm()`, `global_position`, tree membership, and `EnemyAnimationController` resolution **without** introducing a second parallel damage/telegraph pipeline.
- **Rationale:** Current family attack scripts obtain the enemy reference by casting `get_parent()` to `EnemyInfection3D` in `_ready()`. Generated roots today use `EnemyBase`; if attack children are absent or the cast fails, **no attack loop runs**.
- **Normative implementation paths (any one is acceptable if ACs hold):**
  1. Generated scenes (or post-spawn wiring) use `EnemyInfection3D` as the behavioral root with the same `_ensure_*_attack` and animation wiring path as `enemy_infection_3d.gd`, **or**
  2. A thin adapter/wrapper node that is typed compatibly with attack scripts and delegates to generated visuals, **or**
  3. A coordinated refactor of **all four** family attack scripts (and dependent tests) to a documented duck-typed interface—acceptable only if full M8 regression and new M10-03 ACs remain green.
- **Rejected:** Room-local one-off scripts that reimplement telegraph/projectile/melee hit logic for generated enemies.

### ADR-M10-03-02 — `GeneratedEnemyEsmStub` vs `EnemyStateMachine`

- **Decision:** The object returned from the host’s `get_esm()` MUST implement **at minimum** the attack-gating surface used by M8 scripts: `get_state() -> String` with **`dead` blocking** further attack cycle progression per M10-01 R4.6 / R5.5. Animation-driven state names SHOULD remain consistent with `EnemyStateMachine` where `EnemyAnimationController` or infection systems depend on them.
- **Rationale:** Stub currently returns `"idle"` only; that satisfies range/cooldown loops but **fails** dead-state suppression contract if the enemy never transitions to a stub-visible `dead`. Implementation either wires a **real** `EnemyStateMachine` into the generated host path or extends stub (or replacement) so death/infection flows can set `dead` equivalently.
- **Rejected:** Leaving procedural enemies unable to pass dead-state suppression tests while claiming M10-01 R5.5 coverage.

### ADR-M10-03-03 — `.attacks.json` timing authority (this milestone)

- **Decision:** For M10-03, **authoritative** attack timing (cooldowns, telegraph fallbacks, active windows) remains the **family `*_attack.gd` exports** plus **`EnemyAnimationController`** / `AnimationPlayer` clip signals and documented timer fallbacks—matching current M8 behavior. Companion `.attacks.json` beside pipeline exports is **optional**: runtime **need not** load it for this milestone if clip/script timing satisfies ACs.
- **Rationale:** No Godot runtime loader is normatively specified in M10-01 for JSON; introducing mandatory JSON coupling expands pipeline and test surface without a locked schema in gameplay code.
- **Future:** If JSON is wired later, it must **not** add a duplicate hitbox/damage path; it may only **parameterize** existing script exports or controller timings behind one pipeline.

### ADR-M10-03-04 — `mutation_drop` parity

- **Decision:** Effective `mutation_drop` on spawned instances MUST match the family’s M10-01 R4 identifier (`acid`, `adhesion`, `carapace`, `claw`) for attack selection. Assembler may set `mutation_drop` via scene export and/or meta; the **effective** value used by `_ensure_*_attack` (or equivalent) MUST match the generated scene’s intended family so exactly **one** family attack node type is attached per instance.
- **Rationale:** Prevents wrong script attachment or double attachment when both meta and export differ.

---

### Requirement R1 — M8 attack plumbing on procedural instances

#### 1. Spec Summary

- **Description:** After spawn, each procedural combat enemy that is expected to fight MUST have the correct M8 family attack `Node` attached under the same rules as `EnemyInfection3D._ensure_*_attack_if_needed` (by `mutation_drop`), using the existing scripts under `scripts/enemy/*_attack.gd`. Telegraph and hitbox/projectile behavior MUST use the same code paths as hand-placed M8 enemies—**no** second projectile spawner, duplicate `Area3D` hitboxes, or parallel cooldown logic in room or assembler code.
- **Constraints:** No editor-only manual step; wiring runs on standard game and headless test instantiation paths.
- **Assumptions:** Four families from M10-01 R4 only; generated `.tscn` includes `EnemyAnimationController` and visual `AnimationPlayer` wiring per M7.
- **Scope:** Post-spawn enemy instance under combat room root; excludes boss/special rooms not in `POOL["combat"]` unless explicitly included in ticket.

#### 2. Acceptance Criteria

- AC-R1.1: For each spawned instance with `mutation_drop` in `{acid, adhesion, carapace, claw}`, the tree contains exactly one corresponding attack node (`AcidSpitterRangedAttack`, `AdhesionBugLungeAttack`, `CarapaceHuskAttack`, or `ClawCrawlerAttack`) after the same lifecycle point used for `EnemyInfection3D` (post-ready / deferred wiring as implemented).
- AC-R1.2: Family attack scripts’ `_physics_process` (or equivalent tick) runs with a non-null enemy reference (host contract per ADR-M10-03-01).
- AC-R1.3: Telegraph start uses `EnemyAnimationController` when available, with existing timer fallbacks unchanged in semantics from M8 baseline.
- AC-R1.4: No additional attack/damage scripts are added by `RunSceneAssembler` beyond spawning the scene and setting declared metadata unless documented as the single extension point for `_ensure_*` delegation.

#### 3. Risk & Ambiguity Analysis

- **Risk:** `EnemyBase` vs `EnemyInfection3D` type mismatch silences attacks silently (null `_enemy`).
- **Risk:** Double attachment if scene prefab already contains attack nodes and assembler adds another.
- **Edge case:** `mutation_drop` meta from declaration overrides export; spec requires single effective value and one script.

#### 4. Clarifying Questions

- None; ADR-M10-03-01 resolves host type ambiguity.

---

### Requirement R2 — Continuous attack loop (more than one cycle)

#### 1. Spec Summary

- **Description:** While the player remains in aggro range (per family `attack_range` export defaults in M10-01 R4) and the enemy is not `dead`, the enemy MUST **complete at least two** distinct attack cycles (telegraph → active phase → recovery/cooldown → eligible again) across a bounded test scenario. This is the machine-verifiable reading of “attacks more than once.”
- **Constraints:** Respects cooldown exports; does not require overlapping cycles.
- **Assumptions:** Test provides a `player` group member within range for the required duration (deterministic positioning).
- **Scope:** At least one representative family in automated test; all four families remain covered by M10-01 R4 script contracts.

#### 2. Acceptance Criteria

- AC-R2.1: Automated test asserts **≥ 2** completed attack cycles for a chosen procedural-spawned family (e.g. counter of `_on_telegraph_finished` equivalents, projectile spawns, or documented internal cycle counter observable in headless mode).
- AC-R2.2: Between cycles, cooldown semantics hold: no second active phase starts until cooldown elapses (within frame/timer precision used in existing M8 tests).
- AC-R2.3: If player leaves range mid-cycle, behavior matches existing family script (no new requirement beyond current M8).

#### 3. Risk & Ambiguity Analysis

- **Risk:** Flaky real-time tests; mitigate with `SceneTreeTimer` / physics process stepping patterns already used in `tests/scripts/enemy/`.
- **Edge case:** `attack_cycle_active` stuck true if telegraph signal never fires—existing M8 fallbacks must remain intact.

#### 4. Clarifying Questions

- None.

---

### Requirement R3 — Run-assembled vs isolated scene parity

#### 1. Spec Summary

- **Description:** Attack-loop wiring MUST **not** depend on whether the combat room was opened from a full run assembly or instantiated in isolation for tests. Same spawn metadata application and attack wiring MUST apply whenever `RunSceneAssembler` (or its extracted spawn API) places generated enemies in the room.
- **Constraints:** Tests may call the same public/spawn hook the assembler uses rather than duplicating spawn logic in test-only code paths.
- **Assumptions:** Room scene path is one of `RunSceneAssembler.POOL["combat"]` entries.
- **Scope:** Parity of **wiring**, not necessarily identical RNG variant picks unless test fixes seed.

#### 2. Acceptance Criteria

- AC-R3.1: Headless test documents two modes: (A) instantiate combat room + invoke assembler spawn routine on that room instance; (B) full minimal run graph if already test-supported—or (A) alone if equivalent to production path per code structure.
- AC-R3.2: In both documented modes, AC-R1 and AC-R2 observable outcomes hold for the same declaration configuration (family, counts) when RNG is controlled or min==max.

#### 3. Risk & Ambiguity Analysis

- **Risk:** Test-only duplicate spawn code diverges from production; forbidden—test must call shared API.

#### 4. Clarifying Questions

- None.

---

### Requirement R4 — Headless validation hooks (M10-01 R5 specialization)

#### 1. Spec Summary

- **Description:** Extend deterministic headless coverage so procedural-spawned enemies meet M10-01 R5.4/R5.5 **in context**: attack cycle under range, and **dead** suppresses further attacks. Uses existing test harness (`tests/run_tests.gd` / `ci/scripts/run_tests.sh`).
- **Constraints:** No reliance on interactive play; deterministic time advancement only.
- **Assumptions:** Godot headless CI remains the enforcement vehicle.
- **Scope:** New or extended tests under `tests/system/` or `tests/scripts/enemy/` with trace IDs mapped to this spec.

#### 2. Acceptance Criteria

- AC-R4.1: At least one automated test proves **≥ 2** attack cycles for a procedural spawn (R2).
- AC-R4.2: At least one automated test proves **no new attack cycle** starts after host ESM (or equivalent) is `dead` for each family script path, **on procedural host** (ADR-M10-03-02).
- AC-R4.3: `timeout 300 ci/scripts/run_tests.sh` exits `0` with these tests enabled. If a limitation is discovered, ticket must document **BLOCKED** with skip justification—**not** silent omission.

#### 3. Risk & Ambiguity Analysis

- **Risk:** Setting `dead` on procedural host may require new public test hook; document minimal surface.

#### 4. Clarifying Questions

- None.

---

### Requirement R5 — Non-functional requirements

#### 1. Spec Summary

- **Description:** Performance, determinism, and logging constraints for attack loops on procedural spawns.
- **Constraints:** No per-frame global scans beyond existing “first node in group `player`” pattern in family scripts unless an approved follow-on ticket changes that.
- **Assumptions:** Enemy count per room stays bounded by declaration `max_count`.
- **Scope:** Combat room runtime during active combat.

#### 2. Acceptance Criteria

- AC-R5.1: Attack evaluation remains **O(1) per enemy per frame** (same as current `_physics_process` in family scripts).
- AC-R5.2: Given fixed seed + fixed declarations, spawn positions and variant picks remain deterministic per existing assembler rules; attack cycle counts in tests are reproducible.
- AC-R5.3: Wiring failures (missing controller, missing attack script load) log with **room path**, **family**, and **reason**; do not crash entire run assembly.

#### 3. Risk & Ambiguity Analysis

- **Risk:** Logging noise in hot paths; logs should trigger on failure/setup, not every frame.

#### 4. Clarifying Questions

- None.

---

### Requirement R6 — Explicit out-of-scope / compatibility notes

#### 1. Spec Summary

- **Description:** Document boundaries so implementers do not conflate M10-03 with M15 ESM refactor or JSON loader work.
- **Constraints:** None beyond milestone boundaries.
- **Assumptions:** M10-02 completed for spawn declarations and generated scene paths.
- **Scope:** This ticket only.

#### 2. Acceptance Criteria

- AC-R6.1: Implementation notes in code or ticket reference **this spec** and ADR-M10-03-01–04 when touching spawn or attack wiring.
- AC-R6.2: Replacing `GeneratedEnemyEsmStub` with full `EnemyStateMachine` parity is allowed if AC-R4.2 and infection/chunk interactions remain correct or explicitly deferred with planner approval.

#### 3. Risk & Ambiguity Analysis

- **Risk:** Scope creep into full ESM refactor; contain to minimum for dead gating + animation integration.

#### 4. Clarifying Questions

- None.

---

## Downstream Handoff (Binding)

- **Test Designer Agent:** Map AC-R1.x–R6.x to test IDs; prefer `tests/system/test_procedural_enemy_attack_loop_runtime_contract.gd` (new) or disciplined extension of existing suites with clear trace comments. Reuse patterns from `tests/system/test_procedural_enemy_spawn_attack_loop_contract.gd` and `tests/scripts/enemy/test_attack_telegraph_system.gd`.
- **Implementer:** Satisfy ADR-M10-03-01 first (host/attack attachment); then ADR-M10-03-02 (dead gating); verify R2/R3 with shared assembler spawn API.

## Test ID prefix suggestion

`PEAR-T-##` (Procedural Enemy Attack Runtime) — assign in TEST_DESIGN stage.
