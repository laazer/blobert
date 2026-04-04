# Spec: death_animation_playthrough

Ticket: `project_board/7_milestone_7_enemy_animation_wiring/backlog/death_animation_playthrough.md`

Related: `project_board/specs/wire_animations_to_generated_scenes_spec.md` (root `AnimationPlayer` SHALL expose `Death` on all 12 generated scenes).

---

## DAP-1 Requirement — Death lifecycle and despawn timing

### 1. Spec Summary

- **Description:** When an enemy’s `EnemyStateMachine` transitions to canonical state `"dead"` (via `apply_death_event()` or any future equivalent hook that sets the same state), the enemy node SHALL enter a **death sequence** that (a) plays the `Death` animation on the root `AnimationPlayer` to completion, (b) disables physics/collision interaction for the duration, (c) blocks targeting/absorb/infection/chunk-attach semantics for that enemy, and (d) calls `queue_free()` on the enemy root **only after** the `Death` animation has completed. The enemy root MUST NOT be freed while `Death` is still playing.
- **Constraints:** `EnemyStateMachine` remains pure (`RefCounted`); no Node APIs inside ESM. `EnemyAnimationController` already latches death (`_death_latched`) and stops dispatching other clips once `Death` starts — implementation MAY extend this controller or coordinate from `EnemyInfection3D` (or a dedicated child) provided the observable contract below holds. Completion MUST be derived from Godot 4 `AnimationPlayer` end-of-play semantics for the `Death` clip (e.g. `animation_finished` with matching animation name, or an equivalent documented signal/callback that fires exactly once when a non-looping clip reaches its end).
- **Assumptions:** (1) For all in-scope scenes, the `Death` clip exists and is **non-looping** so a single completion event is well-defined (guaranteed by WAGS for generated enemies). (2) `apply_death_event()` is idempotent on ESM (second call is no-op); death sequence start still MUST occur only once per enemy instance.
- **Scope:** All **12** generated enemy scenes: families `adhesion_bug`, `acid_spitter`, `claw_crawler`, `carapace_husk` × variants `_animated_00`, `_animated_01`, `_animated_02` under `res://scenes/enemies/generated/` (same path scheme as `tests/scenes/enemies/test_enemy_scene_animation_wiring.gd`). Any other enemy scene that uses `EnemyInfection3D` + root `AnimationPlayer` + `EnemyAnimationController` SHOULD follow the same contract unless explicitly excluded in a ticket.

### 2. Acceptance Criteria

- **DAP-1.1** Given an instantiated enemy whose ESM transitions to `"dead"`, `queue_free()` on the enemy root (the `CharacterBody3D` / `EnemyInfection3D` instance) SHALL NOT run until after the root `AnimationPlayer` reports completion of the `Death` animation.
- **DAP-1.2** From the first frame after `Death` begins through completion, the enemy’s **CharacterBody3D** SHALL NOT participate in collision as a blocker or mover: `collision_layer` and `collision_mask` SHALL both be `0` (or an equivalent project-approved method that yields no physics contact with world/player/chunks). Restoring collision before `queue_free()` is NOT required.
- **DAP-1.3** While the death sequence is active (same window as DAP-1.2), `EnemyInfection3D` SHALL NOT emit `chunk_attached` for new chunk contacts (existing behavior checks `get_state() == "dead"` in `_on_body_entered`; this SHALL remain true for the full window until free, not only after immediate state flip).
- **DAP-1.4** **Absorb:** `InfectionAbsorbResolver.can_absorb(esm)` is only true in `"infected"`; once dead, absorb is already impossible. Defense in depth: `InfectionInteractionHandler` input paths for absorb/infect SHALL NOT mutate inventory or ESM when `_target_esm.get_state() == "dead"` even if a stale target reference exists.
- **DAP-1.5** **Infect:** `apply_infection_event()` on ESM only transitions from `"weakened"`; dead is unchanged. Handler SHALL NOT call `apply_infection_event()` when target state is `"dead"`.
- **DAP-1.6** **Targeting / UI:** While target ESM is `"dead"`, absorb prompt availability (`set_absorb_available`) SHALL remain false (follows from `can_absorb` + DAP-1.4).
- **DAP-1.7** If the enemy node leaves the tree or is freed by the engine (e.g. level unload, parent `queue_free()`) **during** the death sequence, no deferred callback or signal handler MAY dereference the enemy or `AnimationPlayer` without `is_instance_valid()` (or `is_inside_tree()`) checks; no errors logged at default log level solely due to normal unload.
- **DAP-1.8** The contract SHALL be verified for **at least one variant per family** (four scenes minimum) or parameterized over all 12 paths per test-designer alignment with `test_enemy_scene_animation_wiring.gd` patterns.

### 3. Risk & Ambiguity Analysis

- **Order of operations:** If collision is disabled before `AnimationPlayer.play("Death")`, visual is unchanged; if `play` fails silently, completion might never fire — tests SHOULD cover “Death plays” observably (e.g. `current_animation` / playing state).
- **Stale handler target:** Player can remain spatially overlapping when collision drops; handler must not apply actions on dead ESM (DAP-1.4/1.5).
- **Chunk DoT:** While enemy is dying but not yet freed, `PlayerController3D` chunk timers may still run; ESM transitions from weaken/infect are no-ops when not in the right state; absorb path triggers `apply_death_event` then death sequence — spec does not require stopping DoT timers early unless tests prove a bug; implementer SHALL ensure no double-free or invalid chunk reparent when enemy frees after animation.
- **Mini-boss:** `EnemyInfection3D.is_mini_boss_unit()` uses the same scene family; death playthrough applies unless a future ticket exempts it.

### 4. Clarifying Questions

- None for baseline delivery; WAGS guarantees `Death` exists on all 12 scenes.

---

## DAP-2 Requirement — Animation controller interaction

### 1. Spec Summary

- **Description:** `EnemyAnimationController` SHALL start `Death` when ESM state is `"dead"` (existing behavior). It SHALL NOT switch to another clip after `Death` has started for that instance. Any new logic that delays `queue_free()` MUST NOT call `play()` on a different clip after death latch.
- **Constraints:** Implementation MAY connect to `animation_finished` on the same `AnimationPlayer` referenced by the controller; callbacks MUST be idempotent (single free).
- **Assumptions:** Root `AnimationPlayer` is the one wired per WAGS (`EnemyInfection3D._wire_glb_libraries_to_root_animation_player` / generator).
- **Scope:** `res://scripts/enemies/enemy_animation_controller.gd` and coordinating scripts owned by engine-integration / gameplay as per ticket plan.

### 2. Acceptance Criteria

- **DAP-2.1** After `_death_latched` is true, `_physics_process` SHALL NOT invoke `animation_player.play()` for any clip other than the initial `Death` play that set the latch (i.e. no accidental restart loop that resets `Death` mid-timeline).
- **DAP-2.2** `trigger_hit_animation()` SHALL NOT run while `_death_latched` (already true; MUST remain).

### 3. Risk & Ambiguity Analysis

- If `Death` length is zero or animation is removed at runtime, completion may fire immediately or never — WAGS + adversarial tests own missing-clip behavior; minimum bar is no crash on unload (DAP-1.7).

### 4. Clarifying Questions

- None.

---

## DAP-3 Requirement — Non-functional

### 1. Spec Summary

- **Description:** Full automated suite SHALL pass. Tests for this ticket SHALL be deterministic, headless-safe, and aligned with existing enemy test utilities.
- **Constraints:** Follow `CLAUDE.md`: use `run_tests.sh` / `timeout 300 godot -s tests/run_tests.gd`; do not rely on `--check-only`.
- **Assumptions:** Test scene pattern matches `tests/scenes/enemies/test_enemy_scene_animation_wiring.gd` where applicable.
- **Scope:** `tests/**` as authored by Test Designer / Breaker.

### 2. Acceptance Criteria

- **DAP-NF1** `run_tests.sh` exits `0` with the new tests merged.
- **DAP-NF2** New tests SHALL document traceability to DAP-1.x / DAP-2.x IDs in comments or test names.

### 3. Risk & Ambiguity Analysis

- Flaky timing: prefer signal-based or frame-synchronized assertions over fixed `await` wall-clock where possible.

### 4. Clarifying Questions

- None.

---

## DAP-4 Out of scope

- Changing `EnemyStateMachine` state diagram beyond existing `dead` transition.
- New VFX/audio for death.
- Non-generated enemy prototypes without the WAGS clip set.

---

## File touch list (informative for implementers)

Primary: `scripts/enemy/enemy_infection_3d.gd`, `scripts/enemies/enemy_animation_controller.gd`, `scripts/infection/infection_interaction_handler.gd`, and `scripts/player/player_controller_3d.gd` **only if** chunk/absorb interactions require explicit dead-state guards beyond current ESM rules.
