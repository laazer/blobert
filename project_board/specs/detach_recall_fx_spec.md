# Detach & Recall Visual Feedback — Functional and Non-Functional Specification

**Ticket:** detach_recall_fx.md  
**Epic:** Milestone 2 – Infection Loop  
**Authority:** Spec Agent (workflow enforcement v1)

---

## 1. Scope and Constraints

- **Scope:** Visual feedback for three events: detach, recall start, chunk reabsorption. Implementation is presentation-only plus minimal engine wiring (signals on PlayerController). HP math and `simulate()` in `movement_simulation.gd` are unchanged.
- **Constraints:** Placeholder-friendly visuals (shapes, color, simple effects). No blocking of control; movement and input responsiveness unchanged. Signals emitted from `player_controller.gd` at defined points; presentation subscribes and plays cues.
- **Assumptions:** Per CHECKPOINTS.md [detach_recall_fx] Planner: presentation is signal-driven; controller may add signal declarations and emit calls; all scenes using PlayerController show the same feedback; placeholder-friendly scope.

---

## 2. Signal Contract (Engine Integration)

PlayerController must declare and emit the following signals. Emit points are defined so that presentation and tests can rely on a single source of truth per event.

| Signal name        | Signature | Emit point |
|--------------------|-----------|------------|
| `detach_fired`     | `(player_position: Vector2, chunk_position: Vector2)` | Exactly once per detach when the chunk was successfully added to the scene tree (emit only in the controller success path; not emitted if add_child is skipped, e.g. null parent). Emitted immediately after add_child and `_chunk_node` are set. On that frame, `player_position` and `chunk_position` are equal (chunk spawned at player). |
| `recall_started`   | `(player_position: Vector2, chunk_position: Vector2)` | Exactly once when a recall sequence begins: when `recall_pressed and not _recall_in_progress` has just been evaluated true and `_recall_in_progress` is set to true. `chunk_position` is the current global position of the chunk node at that frame. |
| `chunk_reabsorbed` | `(player_position: Vector2, chunk_position: Vector2)` | Exactly once per successful reabsorption, immediately before the chunk node is queued for free (before `_chunk_node.queue_free()`). Positions are the current global positions at that frame. Not emitted when recall is cancelled (e.g. chunk destroyed externally). |

- **Ordering:** For a single detach→recall→reabsorb cycle, the order of emission is: `detach_fired` → (later) `recall_started` → (after _RECALL_TRAVEL_TIME) `chunk_reabsorbed`.
- **No emit on cancel:** If recall is cancelled (chunk invalidated before reabsorption), `chunk_reabsorbed` is not emitted.

---

## 3. Requirements

### Requirement DRF-1 — Detach visual cue

#### 1. Spec Summary
- **Description:** When the controller emits `detach_fired`, the presentation layer must produce a brief, readable visual cue so the player recognizes that a detach occurred. The cue may be a flash/pulse on the slime body, a small burst at the chunk spawn position, a short screen shake, or an equivalent placeholder-friendly effect.
- **Constraints:** Cue must be brief and must not block input or movement. Implementation only in presentation scripts and/or scene nodes; no changes to `movement_simulation.gd` or HP logic.
- **Assumptions:** Presentation subscribes to `detach_fired`; cue may use the signal arguments `player_position` and `chunk_position` for placement.
- **Scope:** Any scene that uses PlayerController.

#### 2. Acceptance Criteria
- AC-1.1: When `detach_fired` is emitted, at least one visible feedback (e.g. flash, burst, or screen shake) is triggered.
- AC-1.2: The feedback is readable as “detach” (distinguishable from recall start and reabsorb).
- AC-1.3: The feedback does not block control: movement and input responsiveness are unchanged during and after the cue.
- AC-1.4: Implementation is testable (e.g. via a testable state flag or node property that indicates “detach cue was triggered”) so that automated tests can verify the presentation layer responded.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Cue duration too long could feel like blocking even if input is not disabled. Mitigation: spec requires “brief” and NFR (DRF-NF1) forbids blocking.
- **Edge case:** Rapid double detach (e.g. two emissions in quick succession). Presentation should handle multiple cues without crashing; overlapping cues are acceptable.

#### 4. Clarifying Questions
- None; resolved by “placeholder-friendly” and “brief” with NFR.

---

### Requirement DRF-2 — Recall start visual cue

#### 1. Spec Summary
- **Description:** When the controller emits `recall_started`, the presentation layer must produce a distinct cue indicating that recall has begun (e.g. Line2D “tendril” between chunk and player, or a clear color/outline change on the chunk for the travel window).
- **Constraints:** Cue must not block input or movement. Implementation only in presentation scripts and/or scene nodes.
- **Assumptions:** Presentation subscribes to `recall_started`; may use `player_position` and `chunk_position` for positioning (e.g. tendril endpoints).
- **Scope:** Any scene that uses PlayerController.

#### 2. Acceptance Criteria
- AC-2.1: When `recall_started` is emitted, at least one visible feedback (e.g. tendril, outline/color change) is triggered.
- AC-2.2: The feedback is readable as “recall in progress” and is distinct from detach and reabsorb cues.
- AC-2.3: The feedback does not block control.
- AC-2.4: Implementation is testable so that automated tests can verify the presentation layer responded to `recall_started`.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Tendril or line effect might need per-frame updates during recall travel. Spec does not require continuous animation; a one-shot cue (e.g. outline change for the duration) is acceptable. If a tendril is used, it may be updated by presentation until reabsorb or cancel.
- **Edge case:** Recall start without a prior detach in the same session is not possible per current controller logic; no extra handling required for this spec.

#### 4. Clarifying Questions
- None.

---

### Requirement DRF-3 — Reabsorption visual cue

#### 1. Spec Summary
- **Description:** When the controller emits `chunk_reabsorbed`, the presentation layer must produce a clear confirmation cue (e.g. brief flash on player and/or chunk disappearance effect) that is visually distinct from detach and from recall start.
- **Constraints:** Cue must not block input or movement. Implementation only in presentation scripts and/or scene nodes. Chunk node may be freed by the controller immediately after the signal; presentation must not assume the chunk node remains valid after the signal returns.
- **Assumptions:** Presentation subscribes to `chunk_reabsorbed`; may use signal arguments for a final position-based effect (e.g. flash at chunk_position) before the node is gone.
- **Scope:** Any scene that uses PlayerController.

#### 2. Acceptance Criteria
- AC-3.1: When `chunk_reabsorbed` is emitted, at least one visible feedback (e.g. flash, disappearance effect) is triggered.
- AC-3.2: The feedback is readable as “reabsorb confirmed” and is distinct from detach and recall start.
- AC-3.3: The feedback does not block control.
- AC-3.4: Implementation is testable so that automated tests can verify the presentation layer responded to `chunk_reabsorbed`.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Using the chunk node after the signal may cause use-after-free. Spec constrains: use only the passed `chunk_position` (and `player_position`) for effects; do not hold references to the chunk node after handling the signal.
- **Edge case:** Recall cancel: `chunk_reabsorbed` is not emitted, so no reabsorb cue is required in that path.

#### 4. Clarifying Questions
- None.

---

### Requirement DRF-4 — Controller emits signals at correct points

#### 1. Spec Summary
- **Description:** PlayerController declares the three signals and emits them at the exact frames and under the conditions defined in the Signal Contract (Section 2). No change to movement simulation or HP/timer logic beyond adding signal declarations and emit calls.
- **Constraints:** No changes to `movement_simulation.gd`. No new gameplay logic, timers, or HP math in the controller. Signal names and signatures must match the contract.
- **Assumptions:** Emit points are as in Section 2; chunk and player positions are read from the same frame as the emit.
- **Scope:** `player_controller.gd` only.

#### 2. Acceptance Criteria
- AC-4.1: The three signals are declared with the exact names and signatures in the Signal Contract.
- AC-4.2: `detach_fired` is emitted exactly once per logical detach (has_chunk true→false), after the chunk is added to the tree and _chunk_node is set, with positions at that frame.
- AC-4.3: `recall_started` is emitted exactly once when a recall begins (recall_pressed and not _recall_in_progress, then _recall_in_progress set to true), with current player and chunk global positions.
- AC-4.4: `chunk_reabsorbed` is emitted exactly once per successful reabsorption, immediately before queue_free of the chunk node, with current player and chunk global positions. Not emitted when recall is cancelled.
- AC-4.5: All existing tests (movement, detach, recall, HP, etc.) still pass; no change to `simulate()` or MovementState semantics.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Emitting after queue_free would make chunk_position invalid. Contract explicitly requires emit before queue_free.
- **Edge case:** Parent is null on detach (chunk not added); contract says emit is after the block that adds the chunk, so if add_child is skipped, emit should still occur with positions at detach frame (player_position = global_position, chunk_position = same) for consistency, or emit may be skipped when add_child is skipped. Conservative: emit only when chunk was successfully added (so presentation always has a valid chunk in tree when it receives detach_fired). Spec assumes chunk is added when we emit; if add_child path is skipped due to null parent, controller already has push_error and does not set _chunk_node — in that case has_chunk may still be false but there is no chunk node. For spec clarity: emit `detach_fired` only when the chunk was successfully added to the tree (i.e. inside the `else` branch after add_child). That way tests and presentation never see detach_fired without a valid chunk.

#### 4. Clarifying Questions
- None. Emit only on successful add_child path (else branch) for detach_fired.

---

### Requirement DRF-NF1 — Non-blocking and simulation unchanged (NFR)

#### 1. Spec Summary
- **Description:** Visual feedback must not block player control. Movement and input responsiveness remain unchanged during detach and recall. No changes to `movement_simulation.gd`: no HP math changes, no changes to `simulate()` signature or behavior.
- **Constraints:** Presentation must not disable input, pause the scene tree, or block the main thread for a perceptible duration. `movement_simulation.gd` is unchanged.
- **Assumptions:** “Unchanged” means no edits to that file for this feature; signal emission in the controller does not alter simulation inputs or outputs.
- **Scope:** Entire feature (controller + presentation).

#### 2. Acceptance Criteria
- AC-NF1.1: During and after detach, recall start, and reabsorb cues, movement (velocity, position updates) and input handling behave as before; no intentional input suppression or movement freeze.
- AC-NF1.2: `movement_simulation.gd` has no code changes for this ticket (no HP math, no simulate() changes).
- AC-NF1.3: Automated tests can verify non-blocking (e.g. input or movement state can be asserted in the same frame or next frame after a signal; no need for pixel/visual assertions).

#### 3. Risk & Ambiguity Analysis
- **Risk:** Heavy VFX (e.g. many particles) could cause frame drops. Spec does not require performance targets; “do not block control” is about logical blocking (input/movement), not FPS. If needed, adversarial tests can assert that input is still processed.
- **Edge case:** Rapid detach/recall sequences must not deadlock or drop inputs.

#### 4. Clarifying Questions
- None.

---

## 4. Acceptance Criteria to Spec Mapping

| Ticket AC | Spec requirement(s) |
|-----------|----------------------|
| On detach, brief readable feedback cue | DRF-1 (AC-1.1, AC-1.2) |
| On recall start, distinct cue (e.g. tendril, color/outline) | DRF-2 (AC-2.1, AC-2.2) |
| On reabsorption, clear confirmation distinct from detach | DRF-3 (AC-3.1, AC-3.2) |
| Visuals do not block control | DRF-1 (AC-1.3), DRF-2 (AC-2.3), DRF-3 (AC-3.3), DRF-NF1 (AC-NF1.1) |
| Implementation limited to scenes/presentation; HP and simulate() unchanged | DRF-4 (emit-only in controller), DRF-NF1 (AC-NF1.2) |

---

## 5. Testability Notes (for Test Designer)

- **Controller signals:** Tests can connect to the three signals and assert emission count and argument types/values (e.g. player_position and chunk_position are Vector2, and ordering detach_fired → recall_started → chunk_reabsorbed for a full cycle).
- **Presentation response:** Spec requires a testable indication that the presentation layer reacted (e.g. a property or state set when a cue is triggered). Tests need not perform pixel or visual assertions; they may use direct signal emission or minimal scene load to verify that the presentation layer updates that state when the corresponding signal is received.
- **Edge cases (Test Breaker):** Rapid detach/recall, recall cancel (chunk destroyed before reabsorb), no chunk when recall pressed, signal ordering, and non-blocking (input/movement not stalled).

---

**End of specification.**
