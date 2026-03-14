# Spec: Chunk Sticks to Enemy on Contact

**Ticket:** chunk_sticks_to_enemy.md
**Epic:** Milestone 3 — Dual Mutation + Fusion
**Spec Status:** FINAL
**Last Updated By:** Spec Agent
**Revision:** 1

---

## 1. Overview

When a thrown chunk contacts an enemy, it must freeze in place, reparent as a child of the enemy node, and remain attached until the enemy is fully absorbed. While a chunk is stuck on an enemy the player cannot recall that chunk. After the absorb signal fires, the chunk is un-parented, its physics are restored, and recall becomes possible again. The feature must handle two independent chunk slots with no cross-contamination.

---

## 2. Out-of-Scope Items

The following are explicitly excluded from this ticket to keep scope bounded.

- **MovementSimulation is NOT modified.** `movement_simulation.gd` has no knowledge of enemy contact, stuck state, or recall blocking. No new fields are added to `MovementState`.
- **No visual effects or SFX.** Particle effects, color changes, animations, and audio feedback for chunk attachment are out of scope. The chunk is visually positioned on the enemy because of the reparenting mechanism, which is sufficient.
- **No new UI.** No HUD, label, or prompt is added to indicate chunk stuck state.
- **EnemyStateMachine is NOT modified.** State transitions (weakened, infected, dead) are already implemented and unchanged.
- **InfectionAbsorbResolver is NOT modified.** Its method signatures and logic are unchanged.
- **InfectionInteractionHandler is NOT modified** except that `PlayerController3D` connects to its existing `absorb_resolved` signal at startup. No new signals, methods, or fields are added to the handler.
- **No persistence.** Stuck state is session-local; scene reload clears everything.
- **No per-frame position sync loop.** Position tracking is delegated to Godot's scene tree by reparenting; no `_physics_process` code is added to chase the enemy position.
- **Recall animation/tween to enemy.** The recall timer and travel animation are unchanged; recall is simply blocked (cannot start) while a chunk is stuck.
- **Chunk `group` tag changes.** The chunk's `"chunk"` group membership is unchanged.

---

## 3. Definitions

| Term | Meaning |
|---|---|
| **Slot 1** | The chunk tracked by `_chunk_node`, controlled by `detach` action |
| **Slot 2** | The chunk tracked by `_chunk_node_2`, controlled by `detach_2` action |
| **Stuck** | A chunk that has been frozen and reparented as a child of an enemy node |
| **Recallable** | A chunk that is not stuck and is a valid, live node (`is_instance_valid`) |
| **Absorb event** | `InfectionInteractionHandler.absorb_resolved(esm: EnemyStateMachine)` firing |
| **Enemy node** | An `EnemyInfection3D` instance in the scene |

---

## 4. Requirements

---

### Requirement SPEC-CSE-1 — EnemyInfection3D: chunk_attached Signal

#### 1. Spec Summary

- **Description:** `EnemyInfection3D` emits a new signal `chunk_attached(chunk: RigidBody3D)` when a body in the `"chunk"` group enters its `InteractionArea`. This signal fires regardless of the enemy's current infection state (idle, weakened, infected, dead). The signal is emitted after any existing state machine event calls (`apply_weaken_event`, `apply_infection_event`) on the same `_on_body_entered` frame.
- **Constraints:** The signal carries the chunk node reference, not the area. The signal must not fire for player bodies or any body not in the `"chunk"` group. The signal fires at most once per unique `body_entered` event — it does not fire continuously.
- **Assumptions:** `EnemyInfection3D` uses `Area3D` named `"InteractionArea"` connected to `body_entered`. This is confirmed by reading `enemy_infection_3d.gd` line 22–23.
- **Scope:** `scripts/enemy/enemy_infection_3d.gd` only.

#### 2. Acceptance Criteria

- **AC-CSE-1.1:** `EnemyInfection3D` declares `signal chunk_attached(chunk: RigidBody3D)` at class scope.
- **AC-CSE-1.2:** When `_on_body_entered` is called with a body that `is_in_group("chunk")`, `chunk_attached` is emitted with that body as the argument before `_on_body_entered` returns.
- **AC-CSE-1.3:** When `_on_body_entered` is called with a body that `is_in_group("player")`, `chunk_attached` is NOT emitted.
- **AC-CSE-1.4:** When `_on_body_entered` is called with a body in neither group, `chunk_attached` is NOT emitted.
- **AC-CSE-1.5:** `chunk_attached` carries a typed `RigidBody3D` parameter; emitting it with a non-`RigidBody3D` body is not required (it is the caller's responsibility to only emit for chunk bodies, which are `RigidBody3D` as confirmed by `chunk_3d.gd`).
- **AC-CSE-1.6:** Emitting `chunk_attached` does not change `_esm` state directly — state changes (`apply_weaken_event`, `apply_infection_event`) continue to occur in the same `_on_body_entered` call as before, and `chunk_attached` is emitted after those calls.

#### 3. Risk & Ambiguity Analysis

- **Risk:** If emission order (state event vs signal) matters to any subscriber, the strict ordering (state event first, then signal) defined here must be preserved to avoid subscribers reading a stale state.
- **Edge case:** Enemy in "dead" state when chunk arrives — signal still fires. Subscribers must handle this gracefully (see SPEC-CSE-3).

#### 4. Clarifying Questions

None. Resolved by reading existing code.

**Test mapping:** TC-CSE-001, TC-CSE-002, TC-CSE-003

---

### Requirement SPEC-CSE-2 — PlayerController3D: New Stuck-State Fields

#### 1. Spec Summary

- **Description:** `PlayerController3D` adds four new private fields to track the stuck state of each chunk slot independently.
- **Constraints:** All four fields must be declared at class scope. They must be initialized on declaration (not in `_ready`). The two slot fields must not share state or be cross-read.
- **Assumptions:** The existing pattern for per-slot fields (`_recall_in_progress`, `_recall_in_progress_2`, etc.) is followed. No assumptions about when these fields are set are made here; that is specified in SPEC-CSE-4 and SPEC-CSE-5.
- **Scope:** `scripts/player/player_controller_3d.gd` only.

#### 2. Acceptance Criteria

- **AC-CSE-2.1:** `var _chunk_stuck_on_enemy: bool = false` is declared at class scope.
- **AC-CSE-2.2:** `var _chunk_stuck_enemy: EnemyInfection3D = null` is declared at class scope.
- **AC-CSE-2.3:** `var _chunk_2_stuck_on_enemy: bool = false` is declared at class scope.
- **AC-CSE-2.4:** `var _chunk_2_stuck_enemy: EnemyInfection3D = null` is declared at class scope.
- **AC-CSE-2.5:** `_chunk_stuck_on_enemy` and `_chunk_2_stuck_on_enemy` are initialized to `false`; both enemy reference fields are initialized to `null`.
- **AC-CSE-2.6:** No field declared for slot 1 is used to determine the value of any field for slot 2, and vice versa.

#### 3. Risk & Ambiguity Analysis

- **Field type for enemy reference:** Using `EnemyInfection3D` as the type is correct given the signal contract in SPEC-CSE-1. If dynamic typing is needed for testing headlessly, `Node` may be used instead. See SPEC-CSE-6 (signal connection) for the type requirement at the connection site.
- **Assumption:** `_chunk_stuck_enemy` stores the `EnemyInfection3D` node that the chunk was attached to. This reference is used to match against the `esm`-bearing enemy in the absorb signal handler (SPEC-CSE-5).

#### 4. Clarifying Questions

None.

**Test mapping:** TC-CSE-010

---

### Requirement SPEC-CSE-3 — EnemyInfection3D Chunk Attachment Mechanism

#### 1. Spec Summary

- **Description:** When the `chunk_attached` signal fires, the receiving `PlayerController3D` handler must freeze the chunk and reparent it as a child of the emitting enemy node. This causes the chunk to move with the enemy in world space automatically via Godot's scene tree.
- **Constraints:**
  - `chunk.freeze = true` must be set before `reparent()` or `remove_child`/`add_child` so the chunk does not continue to apply physics forces while being moved.
  - The chunk's world-space position must be preserved during reparenting. Use `chunk.reparent(enemy_node, true)` (the second argument `true` means "keep global transform").
  - The chunk's `linear_velocity` must be zeroed (`Vector3.ZERO`) after `freeze = true` to prevent stored velocity from being applied on unfreeze.
  - Only the chunk node that belongs to the player (either `_chunk_node` or `_chunk_node_2`) should be reparented. If the arriving chunk node matches neither slot's `_chunk_node` nor `_chunk_node_2`, the signal is ignored.
- **Assumptions:** `reparent(new_parent, keep_global_transform: bool)` is the correct Godot 4 method for this. The chunk remains a `RigidBody3D` after reparenting (no type change).
- **Scope:** `PlayerController3D` signal handler for `chunk_attached`.

#### 2. Acceptance Criteria

- **AC-CSE-3.1:** On receiving `chunk_attached(chunk)`, the controller identifies which slot the chunk belongs to by comparing `chunk` identity to `_chunk_node` and `_chunk_node_2`.
- **AC-CSE-3.2:** If `chunk == _chunk_node` (slot 1 match): `_chunk_node.freeze = true`, `_chunk_node.linear_velocity = Vector3.ZERO`, `_chunk_node.reparent(enemy_node, true)`, `_chunk_stuck_on_enemy = true`, `_chunk_stuck_enemy = enemy_node`.
- **AC-CSE-3.3:** If `chunk == _chunk_node_2` (slot 2 match): `_chunk_node_2.freeze = true`, `_chunk_node_2.linear_velocity = Vector3.ZERO`, `_chunk_node_2.reparent(enemy_node, true)`, `_chunk_2_stuck_on_enemy = true`, `_chunk_2_stuck_enemy = enemy_node`.
- **AC-CSE-3.4:** If `chunk` matches neither slot, the handler is a no-op (no state changes, no errors).
- **AC-CSE-3.5:** After attachment, `_chunk_stuck_on_enemy` (or `_chunk_2_stuck_on_enemy`) is `true`.
- **AC-CSE-3.6:** After attachment, the chunk is a child of the enemy node in the scene tree.
- **AC-CSE-3.7:** `freeze = true` precedes `reparent()` in the execution order.
- **AC-CSE-3.8:** Attachment does NOT change `_current_state.has_chunk` or `_current_state.has_chunk_2` — the simulation state is unmodified.
- **AC-CSE-3.9:** If `chunk` is not a valid instance at signal receipt (`not is_instance_valid(chunk)`), the handler is a no-op.

#### 3. Risk & Ambiguity Analysis

- **Risk:** `reparent()` with `keep_global_transform=false` (the default) would teleport the chunk to the enemy's local origin. `keep_global_transform=true` must be used. This is the primary implementation hazard.
- **Risk:** If `freeze` is set after `reparent`, a brief physics tick may fire between the two operations, displacing the chunk. Order in AC-CSE-3.7 is normative.
- **Edge case:** If the chunk's parent is not the scene root at the time of `chunk_attached` (e.g. some other reparenting happened), `reparent()` still works correctly as long as it has a valid parent.
- **Edge case:** Enemy in "dead" state at attachment time — the handler still attaches. Detach on absorb (SPEC-CSE-5) handles all enemies regardless of whether state transitions occurred.

#### 4. Clarifying Questions

None.

**Test mapping:** TC-CSE-020, TC-CSE-021, TC-CSE-022, TC-CSE-023

---

### Requirement SPEC-CSE-4 — PlayerController3D: Recall Guard

#### 1. Spec Summary

- **Description:** While a chunk is stuck on an enemy (`_chunk_stuck_on_enemy == true` for slot 1; `_chunk_2_stuck_on_enemy == true` for slot 2), the controller must prevent recall from being initiated for that slot. The block is implemented at the `recall_pressed` / `recall_2_pressed` guard conditions in `_physics_process`.
- **Constraints:** The recall block is purely a controller-side check. `MovementSimulation.simulate()` is not modified. `_recall_in_progress` must never be set to `true` for a slot whose stuck flag is `true`.
- **Assumptions:** The existing `recall_pressed` logic (lines 168–178 of `player_controller_3d.gd`) and `recall_2_pressed` logic (lines 227–237) are each extended with an additional condition.
- **Scope:** `scripts/player/player_controller_3d.gd`, `_physics_process` only.

#### 2. Acceptance Criteria

- **AC-CSE-4.1:** The `recall_pressed` boolean for slot 1 is computed as:
  ```
  detach_just_pressed
  AND (not prev_has_chunk)
  AND _chunk_node != null
  AND is_instance_valid(_chunk_node)
  AND (not _chunk_stuck_on_enemy)
  ```
- **AC-CSE-4.2:** The `recall_2_pressed` boolean for slot 2 is computed as:
  ```
  detach_2_just_pressed
  AND (not prev_has_chunk_2)
  AND _chunk_node_2 != null
  AND is_instance_valid(_chunk_node_2)
  AND (not _chunk_2_stuck_on_enemy)
  ```
- **AC-CSE-4.3:** When `_chunk_stuck_on_enemy == true` and the player presses `detach`, `_recall_in_progress` remains `false` and `recall_started` signal is NOT emitted.
- **AC-CSE-4.4:** When `_chunk_2_stuck_on_enemy == true` and the player presses `detach_2`, `_recall_in_progress_2` remains `false` and `recall_2_started` signal is NOT emitted.
- **AC-CSE-4.5:** When `_chunk_stuck_on_enemy == false` (chunk is not stuck), recall behavior for slot 1 is unchanged from the pre-feature implementation.
- **AC-CSE-4.6:** When `_chunk_2_stuck_on_enemy == false` (chunk 2 is not stuck), recall behavior for slot 2 is unchanged from the pre-feature implementation.
- **AC-CSE-4.7:** The two slots' recall guards are evaluated independently. A stuck slot 1 does NOT block recall for slot 2, and vice versa.

#### 3. Risk & Ambiguity Analysis

- **Risk:** If the guard is placed after `if recall_pressed and not _recall_in_progress:` (inside the block rather than in the condition), recall would still be blocked, but only accidentally. The condition must be placed directly in the `recall_pressed` boolean to be testable in isolation.
- **Edge case:** Chunk is freed by another system (e.g. `queue_free` called externally) while stuck flag is true — `is_instance_valid(_chunk_node)` returning false already prevents recall from firing even without the stuck guard. The stuck flag remains `true` but is harmless when the chunk node is gone.

#### 4. Clarifying Questions

None.

**Test mapping:** TC-CSE-030, TC-CSE-031, TC-CSE-032

---

### Requirement SPEC-CSE-5 — Detach on Absorb: Signal Handler and State Restoration

#### 1. Spec Summary

- **Description:** `PlayerController3D` connects to `InfectionInteractionHandler.absorb_resolved(esm: EnemyStateMachine)` in `_ready()`. When the signal fires, the controller checks whether the `esm`-owning enemy matches the stored `_chunk_stuck_enemy` or `_chunk_2_stuck_enemy` reference. For each matching slot, the controller un-parents the chunk back to the scene root, restores `freeze = false`, and clears the stuck flags.
- **Constraints:**
  - The enemy reference match is done by comparing `enemy_node.get_esm() == esm` where `enemy_node` is `_chunk_stuck_enemy` or `_chunk_2_stuck_enemy`.
  - Both slots are checked independently in the same signal handler. One signal receipt can free both slots if both chunks are stuck on the same enemy.
  - The chunk is reparented back to the scene root of the level (i.e. the same parent it had before attachment, which is the parent of `PlayerController3D`).
  - After un-parenting, the chunk retains its current world position (use `reparent(scene_root, true)`).
  - After `reparent`, `freeze = false` is set so physics resumes.
  - `_chunk_stuck_on_enemy = false` and `_chunk_stuck_enemy = null` are set (slot 1). Equivalently for slot 2.
  - The stuck flag clearing must happen before the end of the signal handler, not deferred.
- **Assumptions:** `EnemyInfection3D.get_esm()` returns the `EnemyStateMachine` instance, confirmed in `enemy_infection_3d.gd` line 27. The `absorb_resolved` signal is confirmed in `infection_interaction_handler.gd` line 22.
- **Scope:** `scripts/player/player_controller_3d.gd`, new `_on_absorb_resolved` method + `_ready` connection.

#### 2. Acceptance Criteria

- **AC-CSE-5.1:** In `_ready()`, `PlayerController3D` locates `InfectionInteractionHandler` via `get_parent().get_node_or_null("InfectionInteractionHandler")` and connects its `absorb_resolved` signal to a new method `_on_absorb_resolved(esm: EnemyStateMachine)`.
- **AC-CSE-5.2:** If `InfectionInteractionHandler` is not present in the scene, the connection attempt is a no-op (guarded by `if handler != null`). No error is pushed.
- **AC-CSE-5.3:** `_on_absorb_resolved` checks slot 1: if `_chunk_stuck_on_enemy == true` and `_chunk_stuck_enemy != null` and `is_instance_valid(_chunk_stuck_enemy)` and `_chunk_stuck_enemy.get_esm() == esm`, then: `_chunk_node.reparent(get_parent(), true)`, `_chunk_node.freeze = false`, `_chunk_stuck_on_enemy = false`, `_chunk_stuck_enemy = null`.
- **AC-CSE-5.4:** `_on_absorb_resolved` checks slot 2: same logic applied to `_chunk_2_stuck_on_enemy`, `_chunk_2_stuck_enemy`, and `_chunk_node_2`.
- **AC-CSE-5.5:** Both slot checks execute unconditionally in the same call (slot 1 check does not prevent slot 2 check).
- **AC-CSE-5.6:** After the handler runs for a matching slot, `_chunk_stuck_on_enemy` (or `_chunk_2_stuck_on_enemy`) is `false`.
- **AC-CSE-5.7:** After the handler runs for a matching slot, the chunk's `freeze` property is `false`.
- **AC-CSE-5.8:** After the handler runs for a matching slot, the chunk is a direct child of `get_parent()` (the scene root), not of the enemy node.
- **AC-CSE-5.9:** After the handler runs for a matching slot, recall becomes possible on the next `detach` press (the stuck guard in SPEC-CSE-4 no longer blocks).
- **AC-CSE-5.10:** If the absorb signal fires but neither stuck flag is `true`, the handler is a no-op (no errors, no state changes).
- **AC-CSE-5.11:** If `_chunk_node` is `null` or not a valid instance when the handler fires for a slot-1 match, skip the un-parent/unfreeze steps but still clear `_chunk_stuck_on_enemy = false` and `_chunk_stuck_enemy = null`.
- **AC-CSE-5.12:** The `reparent` call for un-parenting uses `keep_global_transform = true`.

#### 3. Risk & Ambiguity Analysis

- **Risk:** If `_chunk_stuck_enemy` is freed before the absorb signal fires (e.g. the node is removed from the tree), `is_instance_valid` check prevents a crash. Assumption: enemy nodes are not freed before `absorb_resolved` fires, because `absorb_resolved` is emitted in `InfectionInteractionHandler._process` which runs while the node is still live.
- **Risk:** If `absorb_resolved` fires twice (duplicate signal emission), the second call will find stuck flags already `false` and be a no-op. This is safe.
- **Edge case:** The absorb_resolved signal does not carry the enemy `Node` reference — it carries the `EnemyStateMachine`. The match must use `enemy_node.get_esm() == esm`. This requires the stored `_chunk_stuck_enemy` to be the `EnemyInfection3D` node (not the ESM). This is confirmed by the field declarations in SPEC-CSE-2.
- **Edge case:** Two chunks stuck on two different enemies. Enemy A absorbed: only the slot whose `_chunk_stuck_enemy.get_esm() == esm_A` is freed. The other slot remains stuck until enemy B is absorbed.

#### 4. Clarifying Questions

None.

**Test mapping:** TC-CSE-040, TC-CSE-041, TC-CSE-042, TC-CSE-043, TC-CSE-044

---

### Requirement SPEC-CSE-6 — PlayerController3D: Signal Connection to Enemy chunk_attached

#### 1. Spec Summary

- **Description:** `PlayerController3D` must connect to the `chunk_attached` signal from every `EnemyInfection3D` node in the scene at startup. This allows the controller to respond to chunk-to-enemy contacts and perform the attachment logic in SPEC-CSE-3.
- **Constraints:** Connections are established in `_ready()`. The controller must enumerate all `EnemyInfection3D` nodes reachable from `get_parent()`. The connection target method is named `_on_enemy_chunk_attached(chunk: RigidBody3D, enemy: EnemyInfection3D)` and the enemy reference is bound as a `Callable` parameter (using `Callable.bind(enemy)` or equivalent).
- **Assumptions:** All enemies are direct or indirect children of `get_parent()`. This is the same root node used for `InfectionInteractionHandler` lookup.
- **Scope:** `scripts/player/player_controller_3d.gd`, `_ready()`.

#### 2. Acceptance Criteria

- **AC-CSE-6.1:** In `_ready()`, after the handler lookup, the controller calls `get_parent().find_children("*", "EnemyInfection3D", true, false)` (or equivalent `get_children` recursion) to collect all enemy nodes.
- **AC-CSE-6.2:** For each `enemy` in the collected list, `enemy.chunk_attached.connect(_on_enemy_chunk_attached.bind(enemy))` is called. The bound `enemy` reference is passed as the second argument to the handler.
- **AC-CSE-6.3:** If no enemies are found, no connections are made and no error is pushed.
- **AC-CSE-6.4:** `_on_enemy_chunk_attached(chunk: RigidBody3D, enemy: EnemyInfection3D)` is the method that implements SPEC-CSE-3 logic, receiving both the chunk and the emitting enemy as arguments.
- **AC-CSE-6.5:** Connecting to the same enemy signal twice (e.g. if `_ready` is called more than once) must not cause double-handling. A guard using `if not enemy.chunk_attached.is_connected(...)` or `connect(..., CONNECT_ONE_SHOT)` is not required for this milestone but the spec does not prohibit it.

#### 3. Risk & Ambiguity Analysis

- **Risk:** If enemies are added to the scene after `_ready()` fires (dynamically spawned), they will not be connected. For this milestone, all enemies are placed in the scene at design time, so dynamic addition is out of scope.
- **Risk:** Using `find_children` with `recursive=true` is required because enemies may be nested under environment nodes. The type filter `"EnemyInfection3D"` is used to avoid false matches.

#### 4. Clarifying Questions

None.

**Test mapping:** TC-CSE-050

---

### Requirement SPEC-CSE-7 — Dual-Chunk Independence Invariant

#### 1. Spec Summary

- **Description:** The stuck state for slot 1 and slot 2 must be strictly independent. An operation on slot 1 (attach, detach on absorb, recall guard) must not affect the stuck state or recall behavior of slot 2, and vice versa.
- **Constraints:** No shared boolean, no shared enemy reference, no shared counter is used to track stuck state across both slots. Each slot's state is solely determined by its own four fields.
- **Assumptions:** This mirrors the independence invariant for `has_chunk` / `has_chunk_2` established in `MovementSimulation` (SPEC-SCL-6).
- **Scope:** All modified code in `PlayerController3D` and `EnemyInfection3D`.

#### 2. Acceptance Criteria

- **AC-CSE-7.1:** With slot 1 stuck (`_chunk_stuck_on_enemy=true`) and slot 2 free (`_chunk_2_stuck_on_enemy=false`): pressing `detach_2` initiates recall for slot 2 normally (SPEC-CSE-4 AC-CSE-4.6 applies).
- **AC-CSE-7.2:** With slot 2 stuck (`_chunk_2_stuck_on_enemy=true`) and slot 1 free (`_chunk_stuck_on_enemy=false`): pressing `detach` initiates recall for slot 1 normally.
- **AC-CSE-7.3:** Absorbing enemy A (which has slot 1's chunk) does NOT clear `_chunk_2_stuck_on_enemy` or `_chunk_2_stuck_enemy`.
- **AC-CSE-7.4:** Absorbing enemy B (which has slot 2's chunk) does NOT clear `_chunk_stuck_on_enemy` or `_chunk_stuck_enemy`.
- **AC-CSE-7.5:** If both chunks are stuck on the same enemy, absorbing that enemy clears both slots (AC-CSE-5.5 applies — both checks run in the same handler call).

#### 3. Risk & Ambiguity Analysis

- **Edge case:** Both chunks thrown at the same enemy. `chunk_attached` fires twice (once per chunk). Each triggers its own `_on_enemy_chunk_attached` call. Slot 1 is attached on the first call, slot 2 on the second. After absorb, both are freed in the same `_on_absorb_resolved` call because both stored `_chunk_stuck_enemy` references match (AC-CSE-7.5).

#### 4. Clarifying Questions

None.

**Test mapping:** TC-CSE-060, TC-CSE-061, TC-CSE-062

---

### Requirement SPEC-CSE-8 — Edge Case: Absorb Fires with No Chunk Stuck

#### 1. Spec Summary

- **Description:** If `absorb_resolved` fires but neither `_chunk_stuck_on_enemy` nor `_chunk_2_stuck_on_enemy` is `true`, the handler must be a strict no-op: no state changes, no crashes, no errors pushed.
- **Constraints:** This covers the case where an enemy is absorbed without any chunk having been thrown at it.
- **Assumptions:** No assumption about call frequency or ordering.
- **Scope:** `_on_absorb_resolved` in `PlayerController3D`.

#### 2. Acceptance Criteria

- **AC-CSE-8.1:** With `_chunk_stuck_on_enemy=false` and `_chunk_2_stuck_on_enemy=false`, calling `_on_absorb_resolved(any_esm)` leaves all controller fields unchanged.
- **AC-CSE-8.2:** No `push_error` is called and no exception is raised.
- **AC-CSE-8.3:** `_recall_in_progress`, `_recall_in_progress_2`, `_chunk_node`, `_chunk_node_2` are all unchanged after the call.

#### 3. Risk & Ambiguity Analysis

None.

#### 4. Clarifying Questions

None.

**Test mapping:** TC-CSE-070

---

### Requirement SPEC-CSE-9 — Edge Case: Chunk Recalled Before Enemy Absorb

#### 1. Spec Summary

- **Description:** This edge case cannot occur under correct operation because SPEC-CSE-4 blocks recall while a chunk is stuck. However, if through external means (e.g. test code directly setting `_chunk_stuck_on_enemy = false`) a chunk is "unstuck" and then recalled before the enemy is absorbed, the subsequent `absorb_resolved` signal must not crash and must be a no-op for that slot.
- **Constraints:** No chunk node is freed by `_on_absorb_resolved` unless the stuck flag is `true`. If the stuck flag was already cleared before the signal fires, the handler finds the flag `false` and skips all cleanup.
- **Assumptions:** This is a defensive robustness requirement.
- **Scope:** `_on_absorb_resolved` in `PlayerController3D`.

#### 2. Acceptance Criteria

- **AC-CSE-9.1:** `_on_absorb_resolved` is written to check the stuck flag first; it does not attempt to access `_chunk_stuck_enemy` unless the corresponding stuck flag is `true`.
- **AC-CSE-9.2:** If `_chunk_stuck_on_enemy == false` for slot 1, the slot-1 block in `_on_absorb_resolved` is entirely skipped — no field reads on `_chunk_stuck_enemy`, no reparent, no freeze change.
- **AC-CSE-9.3:** Equivalent behavior applies to slot 2.

#### 3. Risk & Ambiguity Analysis

None.

#### 4. Clarifying Questions

None.

**Test mapping:** TC-CSE-071

---

### Requirement SPEC-CSE-10 — Edge Case: Enemy Node Freed While Chunk Is Stuck

#### 1. Spec Summary

- **Description:** If the enemy node is freed from the scene (e.g. via `queue_free`) while a chunk is reparented as its child, Godot will also free the chunk node (because the chunk is a child of the enemy). The controller must handle the case where `_chunk_node` (or `_chunk_node_2`) is no longer a valid instance when the absorb handler fires.
- **Constraints:** This is a safety valve requirement. The expected gameplay flow does not free the enemy node before `absorb_resolved` fires, but the code must be robust.
- **Scope:** `_on_absorb_resolved` in `PlayerController3D`.

#### 2. Acceptance Criteria

- **AC-CSE-10.1:** If `_chunk_stuck_on_enemy == true` and the stuck flag's slot chunk (`_chunk_node`) is `null` or `not is_instance_valid(_chunk_node)`, the un-parent and un-freeze steps are skipped without error.
- **AC-CSE-10.2:** The stuck flags (`_chunk_stuck_on_enemy`, `_chunk_stuck_enemy`) are still cleared even when the chunk node is invalid — the slot must return to a clean, ready state.
- **AC-CSE-10.3:** No `push_error`, no crash when `_chunk_node` is a freed instance.
- **AC-CSE-10.4:** Equivalent behavior applies to slot 2.

#### 3. Risk & Ambiguity Analysis

- **Risk:** If the stuck flag is not cleared when the chunk node is invalid, the recall guard (SPEC-CSE-4) will permanently block recall for that slot, creating a softlock.

#### 4. Clarifying Questions

None.

**Test mapping:** TC-CSE-072

---

### Requirement SPEC-CSE-11 — Non-Functional: MovementSimulation Unmodified

#### 1. Spec Summary

- **Description:** `movement_simulation.gd` and `MovementSimulation.MovementState` must not be modified in any way by this feature. No fields, methods, or constants are added or changed.
- **Constraints:** This is a strict non-modification constraint derived from the Planner checkpoint.
- **Assumptions:** No assumptions.
- **Scope:** `scripts/movement/movement_simulation.gd`.

#### 2. Acceptance Criteria

- **AC-CSE-11.1:** `git diff scripts/movement/movement_simulation.gd` produces no output after implementation of this feature.
- **AC-CSE-11.2:** All existing `MovementSimulation` tests continue to pass after the feature is implemented.

#### 3. Risk & Ambiguity Analysis

None.

#### 4. Clarifying Questions

None.

**Test mapping:** Covered by existing movement simulation test suite (TC-SCL-* series).

---

### Requirement SPEC-CSE-12 — Non-Functional: InfectionInteractionHandler Unmodified

#### 1. Spec Summary

- **Description:** `infection_interaction_handler.gd` must not be modified. `PlayerController3D` connects to the existing `absorb_resolved` signal; no new signals, fields, or methods are added to the handler.
- **Constraints:** Strict non-modification.
- **Assumptions:** The existing `absorb_resolved` signal signature `(esm: EnemyStateMachine)` is sufficient.
- **Scope:** `scripts/infection/infection_interaction_handler.gd`.

#### 2. Acceptance Criteria

- **AC-CSE-12.1:** `git diff scripts/infection/infection_interaction_handler.gd` produces no output after implementation.

#### 3. Risk & Ambiguity Analysis

None.

#### 4. Clarifying Questions

None.

**Test mapping:** Existing infection interaction tests continue to pass.

---

## 5. API Contracts

### 5.1 EnemyInfection3D Additions

```
# New signal (class scope)
signal chunk_attached(chunk: RigidBody3D)

# Existing _on_body_entered — extended to emit chunk_attached
func _on_body_entered(body: Node3D) -> void:
    # ... existing player block unchanged ...
    if body.is_in_group("chunk"):
        # ... existing weaken/infect block unchanged ...
        chunk_attached.emit(body as RigidBody3D)   # NEW — emitted last in the chunk block
```

**Notes:**
- No other changes to `EnemyInfection3D`.
- `get_esm()` is unchanged; it is used by `PlayerController3D._on_absorb_resolved` for ESM matching.

### 5.2 PlayerController3D Additions

```
# New fields (class scope, after existing _chunk_node_2 declarations)
var _chunk_stuck_on_enemy: bool = false
var _chunk_stuck_enemy: EnemyInfection3D = null
var _chunk_2_stuck_on_enemy: bool = false
var _chunk_2_stuck_enemy: EnemyInfection3D = null
```

```
# _ready() additions (after existing handler lookup)
func _ready() -> void:
    # ... existing setup unchanged ...
    var handler: InfectionInteractionHandler = get_parent().get_node_or_null("InfectionInteractionHandler")
    if handler != null:
        handler.absorb_resolved.connect(_on_absorb_resolved)
    var enemies: Array = get_parent().find_children("*", "EnemyInfection3D", true, false)
    for enemy in enemies:
        enemy.chunk_attached.connect(_on_enemy_chunk_attached.bind(enemy))
```

```
# New method: chunk_attached signal handler
func _on_enemy_chunk_attached(chunk: RigidBody3D, enemy: EnemyInfection3D) -> void:
    if not is_instance_valid(chunk):
        return
    if chunk == _chunk_node:
        _chunk_node.freeze = true
        _chunk_node.linear_velocity = Vector3.ZERO
        _chunk_node.reparent(enemy, true)
        _chunk_stuck_on_enemy = true
        _chunk_stuck_enemy = enemy
    elif chunk == _chunk_node_2:
        _chunk_node_2.freeze = true
        _chunk_node_2.linear_velocity = Vector3.ZERO
        _chunk_node_2.reparent(enemy, true)
        _chunk_2_stuck_on_enemy = true
        _chunk_2_stuck_enemy = enemy
    # else: not our chunk — ignore
```

```
# New method: absorb_resolved signal handler
func _on_absorb_resolved(esm: EnemyStateMachine) -> void:
    # Slot 1
    if _chunk_stuck_on_enemy and _chunk_stuck_enemy != null and is_instance_valid(_chunk_stuck_enemy):
        if _chunk_stuck_enemy.get_esm() == esm:
            if _chunk_node != null and is_instance_valid(_chunk_node):
                _chunk_node.reparent(get_parent(), true)
                _chunk_node.freeze = false
            _chunk_stuck_on_enemy = false
            _chunk_stuck_enemy = null
    # Slot 2
    if _chunk_2_stuck_on_enemy and _chunk_2_stuck_enemy != null and is_instance_valid(_chunk_2_stuck_enemy):
        if _chunk_2_stuck_enemy.get_esm() == esm:
            if _chunk_node_2 != null and is_instance_valid(_chunk_node_2):
                _chunk_node_2.reparent(get_parent(), true)
                _chunk_node_2.freeze = false
            _chunk_2_stuck_on_enemy = false
            _chunk_2_stuck_enemy = null
```

```
# recall_pressed guard (modified in _physics_process — slot 1)
var recall_pressed: bool = (
    detach_just_pressed
    and (not prev_has_chunk)
    and _chunk_node != null
    and is_instance_valid(_chunk_node)
    and (not _chunk_stuck_on_enemy)    # NEW
)

# recall_2_pressed guard (modified in _physics_process — slot 2)
var recall_2_pressed: bool = (
    detach_2_just_pressed
    and (not prev_has_chunk_2)
    and _chunk_node_2 != null
    and is_instance_valid(_chunk_node_2)
    and (not _chunk_2_stuck_on_enemy)  # NEW
)
```

---

## 6. Test Coverage Mapping

| Test ID | Requirement(s) Covered | Description |
|---|---|---|
| TC-CSE-001 | SPEC-CSE-1 | chunk_attached emitted when chunk body enters InteractionArea |
| TC-CSE-002 | SPEC-CSE-1 | chunk_attached NOT emitted for player body |
| TC-CSE-003 | SPEC-CSE-1 | chunk_attached NOT emitted for unlabeled body |
| TC-CSE-010 | SPEC-CSE-2 | PlayerController3D fields declared with correct types and defaults |
| TC-CSE-020 | SPEC-CSE-3 | Attachment: freeze=true set on slot-1 chunk when chunk_attached fires |
| TC-CSE-021 | SPEC-CSE-3 | Attachment: chunk reparented as child of enemy (slot 1) |
| TC-CSE-022 | SPEC-CSE-3 | Attachment: _chunk_stuck_on_enemy=true and _chunk_stuck_enemy=enemy after attach (slot 1) |
| TC-CSE-023 | SPEC-CSE-3 | Attachment: unrecognized chunk (not in either slot) is a no-op |
| TC-CSE-024 | SPEC-CSE-3 | Attachment: slot 2 mirrors slot 1 behavior independently |
| TC-CSE-025 | SPEC-CSE-3 | Attachment: linear_velocity zeroed on attach |
| TC-CSE-030 | SPEC-CSE-4 | Recall blocked for slot 1 when _chunk_stuck_on_enemy=true |
| TC-CSE-031 | SPEC-CSE-4 | Recall blocked for slot 2 when _chunk_2_stuck_on_enemy=true |
| TC-CSE-032 | SPEC-CSE-4 | Recall NOT blocked when stuck flags are false |
| TC-CSE-040 | SPEC-CSE-5 | _on_absorb_resolved: chunk un-parented and freeze=false on matching esm (slot 1) |
| TC-CSE-041 | SPEC-CSE-5 | _on_absorb_resolved: _chunk_stuck_on_enemy=false after handler (slot 1) |
| TC-CSE-042 | SPEC-CSE-5 | _on_absorb_resolved: slot 2 cleared independently on matching esm |
| TC-CSE-043 | SPEC-CSE-5 | _on_absorb_resolved: non-matching esm leaves stuck flags unchanged |
| TC-CSE-044 | SPEC-CSE-5 | Both slots freed when both stuck on same enemy (single absorb_resolved call) |
| TC-CSE-050 | SPEC-CSE-6 | _ready connects chunk_attached from all EnemyInfection3D nodes |
| TC-CSE-060 | SPEC-CSE-7 | Slot 1 stuck does not block slot 2 recall |
| TC-CSE-061 | SPEC-CSE-7 | Slot 2 stuck does not block slot 1 recall |
| TC-CSE-062 | SPEC-CSE-7 | Absorbing enemy A does not clear slot 2 stuck state (slot 2 stuck on enemy B) |
| TC-CSE-070 | SPEC-CSE-8 | absorb_resolved with no chunks stuck is a no-op |
| TC-CSE-071 | SPEC-CSE-9 | absorb_resolved after chunk already unstuck and recalled is a no-op |
| TC-CSE-072 | SPEC-CSE-10 | absorb_resolved with freed chunk node: flags cleared, no crash |

---

## 7. Files Modified by This Feature

| File | Change Type |
|---|---|
| `scripts/enemy/enemy_infection_3d.gd` | Add `chunk_attached` signal; emit in `_on_body_entered` |
| `scripts/player/player_controller_3d.gd` | Add 4 fields; extend `_ready`; add 2 new methods; extend `recall_pressed` guards |
| `scripts/movement/movement_simulation.gd` | **NOT MODIFIED** |
| `scripts/infection/infection_interaction_handler.gd` | **NOT MODIFIED** |
| `scripts/infection/infection_absorb_resolver.gd` | **NOT MODIFIED** |
| `scripts/chunk/chunk_3d.gd` | **NOT MODIFIED** |

---

## 8. Assumptions Summary

1. All enemies are present in the scene at `_ready()` time (no dynamic spawning).
2. `EnemyInfection3D.get_esm()` always returns the non-null `EnemyStateMachine` instance (confirmed in code).
3. `InfectionInteractionHandler` is always a sibling of `PlayerController3D` under the same parent node.
4. `absorb_resolved` fires exactly once per absorb and is not emitted before the enemy state transitions to "dead".
5. The `chunk_3d.tscn` root is always a `RigidBody3D` (confirmed by `assert` in `player_controller_3d.gd` line 184).
6. Chunk group membership (`"chunk"`) is already configured on `chunk_3d.tscn` — confirmed by existing `EnemyInfection3D._on_body_entered` chunk group check.
