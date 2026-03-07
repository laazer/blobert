# Weakening System Specification

**Ticket:** weakening_system.md  
**Spec Version:** 1  
**Spec Author:** Spec Agent  
**Date:** 2026-03-07  
**Stage:** TEST_DESIGN  

---

## Executive Summary

The weakening system makes enemies susceptible to infection after a weakening event (e.g., chunk contact). This specification defines the complete behavioral contract, visual feedback requirements, configuration tuning, and test acceptance criteria for the weakening system, ensuring enemies transition clearly from normal to weakened to infectable state.

---

## Functional Requirements

### FR1: State Machine Foundation

**Description:** Enemies have a well-defined lifecycle state machine with a `weakened` state.

**Details:**
- State machine is implemented in `EnemyStateMachine` (pure simulation, no Node dependencies)
- Canonical states: `idle`, `active`, `weakened`, `infected`, `dead`
- An enemy in `idle` or `active` state can transition to `weakened` when a weaken event is triggered
- An enemy in `weakened` state can transition to `infected` when an infection event is triggered
- Once `infected`, the enemy cannot be weakened again (infection event is only valid from `weakened` state)
- An enemy in any non-`dead` state can transition to `dead` via a death event
- All invalid state transitions are no-ops and must not change state or trigger side effects
- The `reset()` method transitions any state back to `idle` (used for respawn/restart scenarios)

**Rationale:** A strict, well-defined state machine prevents undefined behavior (e.g., double-weaken, weaken-then-directly-die) and makes the system testable and predictable.

---

### FR2: Weakening Trigger Mechanism

**Description:** Enemies transition to the `weakened` state when a specific trigger event occurs.

**Details:**
- Primary trigger: **Chunk contact** — When a 3D projectile/chunk (body in group `"chunk"`) physically collides with an enemy's interaction area (`Area3D` node), the enemy applies the weaken event
- Trigger path: `Chunk → Area3D body_entered() → EnemyInfection3D._on_body_entered() → EnemyStateMachine.apply_weaken_event()`
- The chunk contact is treated as a "damage" or "weakening force"; no numerical health/damage tracking is required for this spec
- Repeated chunk contact against the same enemy is idempotent: calling `apply_weaken_event()` when already weakened has no effect
- Unchaining the weaken event from HP thresholds allows decoupled tuning of chunk behavior (damage dealing vs weakening)

**Rationale:** Chunk contact is simpler to test and tune than HP thresholds. It provides immediate, visible feedback (collision) and avoids complex health tracking in this iteration.

---

### FR3: Infection-Eligibility Gate

**Description:** A weakened enemy may be infectable, provided the preconditions are met.

**Details:**
- An enemy with state `weakened` is eligible for infection via `apply_infection_event()`
- Infection can be triggered by:
  1. **Chunk contact** (continuation): If a chunk enters a weakened enemy's area, the enemy applies the infection event in the same collision handler
  2. **Input action** (supplementary): If the player presses the `infect` input action while targeting a weakened enemy, `InfectionInteractionHandler` applies the infection event to the target
- Only one of these paths is required for the milestone; both are supported
- Once infected, the enemy cannot be re-infected (infection is only valid from `weakened` state)

**Rationale:** Supporting both chunk-based and input-based infection provides gameplay flexibility without forcing both in the test gate; Test Designer and Implementation can verify the path(s) most relevant to their scope.

---

### FR4: Visual Distinctness — Weakened State

**Description:** The weakened state is clearly visually distinguishable from idle, active, and infected states so a player can identify weakened enemies without debug information.

**Details:**
- **Primary visual feedback:** When an enemy transitions to `weakened`, the enemy visual (3D mesh or sprite) blinks for a fixed duration (default: 0.35 seconds at 10 Hz frequency)
- **Blink pattern:** On/off cycle at 10 Hz means the visual toggles visibility roughly every 50ms, creating a flashing effect
- **Duration:** Blink effect lasts 0.35 seconds, after which the visual returns to solid/opaque and remains visible until the next state change
- **Distinctness from infected:** The infected state also triggers a blink, but it can be coupled with a different visual effect (e.g., different color tint, particle effect, or sound) to distinguish it from weakened in future iterations
- **State label:** A text label (if present) displays the current state name, e.g., `"Weakened"`, `"Infected"`, `"Dead"`. Label presence is optional for this milestone but must not crash if missing
- **Readability criterion:** At a standard camera distance (similar to `test_movement_3d.tscn`), a player must be able to clearly identify the weakened state without external indicators

**Rationale:** Blinking provides immediate, non-intrusive feedback. The 0.35s duration is long enough to be noticeable but short enough to return to normal quickly for gameplay flow. The state label adds explicit confirmation for players who want text cues.

---

### FR5: Integration with Infection Interaction Loop

**Description:** The weakening system integrates seamlessly with the infection loop (target selection, absorb resolution, mutation granting).

**Details:**
- `EnemyInfection3D` holds an `EnemyStateMachine` and exposes it via `get_esm()` for external systems
- When the player enters the enemy's interaction area, `EnemyInfection3D._on_body_entered()` calls `InfectionInteractionHandler.set_target_esm()` to register the enemy as a candidate for infection/absorb
- When the player exits, `clear_target()` is called to deregister the target
- Chunk contact triggers `apply_weaken_event()` and then `apply_infection_event()` in the same handler, advancing the enemy through weakened → infected immediately if a chunk hits a non-weakened enemy
- `InfectionInteractionHandler` uses the target ESM state to determine if absorb is available (only when `can_absorb()` returns true from `InfectionAbsorbResolver`), and only allows the `infect` input action if the target is in the `weakened` state
- Absorption of an infected enemy via `InfectionAbsorbResolver.resolve_absorb()` kills the enemy (transitions to `dead`) and grants a mutation to the player

**Rationale:** Close integration ensures the weakening system is not isolated; all components (state machine, visual feedback, handlers, absorb logic) work as a cohesive feature.

---

## Non-Functional Requirements

### NFR1: Performance and Responsiveness

**Requirement:** The weakening system must not cause frame rate degradation or introduce input latency.

**Details:**
- State machine is pure simulation: `apply_*_event()` calls are O(1) and have no Node/physics dependencies, allowing unrestricted calls without frame impact
- Visual feedback (`infection_state_fx_3d.gd`) updates only once per `_process()` frame, not per event
- Blink timing is frame-rate independent: elapsed time is accumulated via delta, and blink cycles are computed as a function of time, not frame count
- Recommended target: maintained 60 FPS during active weakening/infection sequences

**Rationale:** Pure simulation and frame-synchronized updates ensure the feature scales to many simultaneous enemies without hiccups.

---

### NFR2: Idempotency and Robustness

**Requirement:** Repeated or invalid operations must not corrupt state or trigger unintended side effects.

**Details:**
- Calling `apply_weaken_event()` on an already-weakened enemy is a no-op (no state change, no re-trigger of visual effects)
- Calling `apply_infection_event()` on a non-weakened enemy is a no-op (cannot infect idle, active, infected, or dead enemies)
- Calling `apply_death_event()` on a dead enemy is a no-op (already dead)
- A null ESM, null visual node, or missing label node in FX handlers must not crash; the system degrades gracefully (skip update, log trace if needed, continue to next update)
- Rapid state transitions (e.g., weaken → infect → death in quick succession) must update visuals correctly and converge to a valid end state

**Rationale:** Robustness ensures edge cases don't break the game or create confusing states; idempotency allows safe re-triggering of events without manual state checks by callers.

---

### NFR3: Configuration and Tuning

**Requirement:** Visual and behavioral parameters must be configurable via `@export` properties, allowing designers to tweak feedback without recompiling scripts.

**Details:**
- `infection_state_fx_3d.gd` exposes:
  - `BLINK_DURATION_SECONDS` (default: 0.35): Duration of the blink effect when transitioning to weakened or infected
  - `BLINK_FREQUENCY_HZ` (default: 10.0): Number of on/off cycles per second
- Future enhancements may expose color tints (e.g., `weakened_tint`, `infected_tint`, `dead_dim_alpha`) as `@export` properties
- Configuration updates are live-safe: changing an `@export` value in the editor and playing the scene immediately uses the new value
- Default values are chosen to be perceptually clear without requiring extreme tint/alpha changes

**Rationale:** Tunable parameters let designers balance visual clarity, readability, and art direction without code changes.

---

### NFR4: Graceful Degradation and Null Handling

**Requirement:** Missing or null nodes must not cause crashes or silent failures.

**Details:**
- If `_visual` (the mesh or visual element) is null, the blink effect is skipped but the state machine continues normally
- If `_label` is null or missing, the state label is not updated, but the blink effect still renders
- If the parent enemy node is missing, FX handlers attempt to re-acquire it on the next `_process()` call
- No exception is thrown; all null cases are treated as degraded-but-functional

**Rationale:** Nodes may be deleted, reparented, or not yet instantiated in certain test scenarios; graceful handling keeps tests and gameplay robust.

---

## Acceptance Criteria Mapping

| AC | Requirement | Spec Section | Test Strategy |
|----|----|----|----|
| AC#1: Enemies transition to weakened state when condition is met | Chunk contact triggers state transition | FR2: Weakening Trigger Mechanism | Test: Chunk body enters area → state becomes `weakened` |
| AC#2: Weakened state is clearly distinguishable | Visual blink feedback plus optional state label | FR4: Visual Distinctness | Test: Blink effect renders; state label text is set and readable |
| AC#3: Weakened enemies can be infected | Infection event valid only from weakened state | FR3: Infection-Eligibility Gate | Test: Infection event from weakened → infected; repeated infection is no-op |
| AC#4: Tuning is configurable | @export parameters for blink duration, frequency, and future visual tweaks | NFR3: Configuration and Tuning | Test: Tweak @export values, verify effect in editor and tests |
| AC#5: Human-playable in-editor | Enemies and weakened cues visible without debug overlays in test_movement_3d.tscn | FR4 + Manual Integration | Human playtest: Load test_movement_3d.tscn, attack chunk at enemy, observe clear weakening feedback |

---

## Configuration Reference

### infection_state_fx_3d.gd — Visual Feedback Parameters

```gdscript
# Duration of blink effect when transitioning to weakened or infected
const BLINK_DURATION_SECONDS: float = 0.35

# Blink frequency in Hz (cycles per second)
const BLINK_FREQUENCY_HZ: float = 10.0
```

**Tuning Guidance:**
- **Longer duration** (e.g., 0.5s): More noticeable feedback, but slower return to normal
- **Shorter duration** (e.g., 0.2s): Quick feedback, but less visible for distant/small enemies
- **Higher frequency** (e.g., 15 Hz): More aggressive flashing, may cause visual strain
- **Lower frequency** (e.g., 5 Hz): Softer, slower blink, easier to see but less dramatic

---

## Boundary Conditions and Edge Cases

### Edge Case 1: Rapid Chunk Contact
**Scenario:** A chunk collides with an enemy multiple times in quick succession (e.g., ricocheting).  
**Behavior:** Each collision calls `apply_weaken_event()` and `apply_infection_event()`. If the enemy is already weakened, the first call transitions to infected; subsequent chunk contacts are no-ops.  
**Specification:** Idempotency (NFR2) ensures no state corruption or visual glitching.

### Edge Case 2: Player Input and Chunk Contact Simultaneously
**Scenario:** While a chunk is hitting an enemy, the player presses the `infect` input action.  
**Behavior:** Both events are valid and independent. The state machine processes both, and the last valid transition wins. If the enemy is already transitioning via chunk, the input action may be a no-op or redundant.  
**Specification:** No collision or priority rule is needed; the result is determined by the order of event calls and the strict state machine transitions (FR1).

### Edge Case 3: Enemy Spawns Already Weakened
**Scenario:** An NPC script or level designer pre-sets an enemy's state to `weakened` for a specific encounter.  
**Behavior:** The enemy renders with visual feedback and behaves as weakened. On infection or reset, it transitions normally.  
**Specification:** Allowed. The state machine does not enforce how states are initialized; external systems may set any valid state.

### Edge Case 4: Null Visual Node During Blink
**Scenario:** The enemy visual is deleted or reparented while a blink is in progress.  
**Behavior:** The FX handler detects the null and skips the visual update. The blink timer continues, and when a new visual is re-acquired, it's set to visible (NFR4: Graceful Degradation).  
**Specification:** Non-critical. Gameplay continues; visual feedback is temporarily lost but not terminal.

---

## Test Design Strategy

### Unit Tests (Pure Simulation)
- **State Transitions:** Verify `apply_weaken_event()`, `apply_infection_event()`, `apply_death_event()`, and `reset()` against the state machine contract
- **Idempotency:** Verify repeated transitions are no-ops when invalid
- **No-op Combinations:** Verify all invalid state pairs are no-ops (e.g., infect from idle, weaken from dead)

### Visual Feedback Tests
- **Blink Timing:** Verify blink duration and frequency match constants
- **State Label Mapping:** Verify label text matches state (e.g., "Weakened" when state is `weakened`)
- **Null Handling:** Verify no crashes when label or visual is null; system continues

### Integration Tests
- **Chunk Contact Wiring:** Chunk body enters area → `apply_weaken_event()` → `apply_infection_event()` → state is `infected`
- **Player Targeting:** Player enters area → `set_target_esm()` called; exiting → `clear_target()` called
- **Absorb Resolution:** Infection + absorb → enemy dead, mutation granted

### Adversarial / Edge-Case Tests
- **Rapid Transitions:** Weaken → infect → dead in succession; verify final state is correct and no visual corruption
- **Repeated Weaken:** Apply weaken 5x in a row; verify state is `weakened` and visual is stable
- **Scene Graph Integrity:** Verify no orphaned nodes or duplicate visual updates

### Human Playtest (Manual Acceptance)
- Load `test_movement_3d.tscn`
- Attack an enemy with a chunk
- Observe the enemy clearly enters a weakened state (blink + label visible)
- Trigger infection and absorb
- Verify the enemy disappears and mutation is visible in inventory

---

## Out of Scope

The following are explicitly out of scope for this specification and ticket:

1. **Persistent state:** Mutation or weakening state across scene reloads or level transitions
2. **Health/damage tracking:** Numeric HP or damage values; chunk weakening is binary, not damage-based
3. **Advanced visual effects:** Particle systems, shader tints, or animations beyond blink feedback (future enhancement)
4. **Difficulty modifiers:** Weaken cooldowns, reduced weaken chance, or dynamic threshold adjustments per difficulty
5. **Gameplay balance tuning:** Exact parameter values (blink duration, frequency) are provided as defaults; balance is deferred to Integration/Deployment

---

## Spec Decisions and Assumptions

### Decision 1: Chunk Contact as Primary Trigger (Medium Confidence)
**Alternative:** HP-based threshold (e.g., enemy is weakened if health < 50%)  
**Decision:** Chunk contact (physical collision) is the trigger.  
**Rationale:** Avoids complex health tracking; provides tactile, visible game mechanic; aligns with current `EnemyInfection3D` implementation.

### Decision 2: Blink Duration and Frequency Defaults (Medium Confidence)
**Alternative:** 0.2s or 0.5s duration; 5 Hz or 15 Hz frequency  
**Decision:** 0.35s duration, 10 Hz frequency.  
**Rationale:** Balances visibility and gameplay flow; 0.35s is long enough to be noticeable, 10 Hz is distinct without being obnoxious; both are configurable.

### Decision 3: State Label as Optional but Supported (Medium Confidence)
**Alternative:** Require label; forbid operations if label is missing  
**Decision:** Label is optional; system degrades gracefully if missing.  
**Rationale:** Allows flexible scene composition; some tests or scenes may not have UI; graceful null handling is more robust.

### Decision 4: Single Mutation on Absorb (Medium Confidence)
**Alternative:** Random mutation; multiple mutations from one absorb  
**Decision:** One fixed, configured mutation per absorb.  
**Rationale:** Simplifies testing and determinism; can be generalized in future tickets (randomness, multi-slot).

---

## Sign-Off

**Specification Status:** READY FOR TEST DESIGN  
**Next Stage:** TEST_DESIGN  
**Next Responsible Agent:** Test Designer Agent

This specification is complete and detailed enough to drive Test Design and Implementation. All functional requirements are defined, non-functional constraints are clear, and edge cases are documented.
