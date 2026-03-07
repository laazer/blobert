# Specification: Visual Feedback for Infection States and Absorb

**Ticket:** `project_board/2_milestone_2_infection_loop/01_active/visual_feedback_infection.md`  
**Revision:** 1.0  
**Date:** 2026-03-07  
**Owner:** Spec Agent  
**Scope:** 2D infection visual feedback (3D deferred to separate ticket)

---

## Executive Summary

This specification defines the authoritative visual contract for infection state transitions (idle → weakened → infected → dead) and absorb feedback in the 2D infection loop. The goal is to enable the player to read the infection state progression visually without relying on UI alone, ensuring all states are distinct, readable at standard gameplay camera distance, and do not interfere with player input or movement.

**Primary Components:**
- Weakened state visual cue (color tint + state label)
- Infected state visual cue (distinct from weakened, color tint + state label)
- Absorb feedback (particle effect + optional animation)
- State label styling and positioning

---

## Requirements

### Functional Requirements

#### F1: Weakened State Visual Feedback
**Requirement:** When an enemy transitions from idle/active to weakened state, a distinct visual cue must be applied to the enemy sprite/visual.

**Details:**
- **Color Tint:** Apply `Color(1.0, 0.85, 0.5, 1.0)` (warm amber/tan) to the enemy's EnemyVisual CanvasItem `modulate`.
- **State Label:** Display a Label node with text "Weakened" in color `Color(1.0, 0.9, 0.6, 1.0)` (light amber).
- **Trigger:** Label `_update_state_label()` is invoked whenever `_esm.get_state()` returns `"weakened"`.
- **Persistence:** Tint and label remain visible until the enemy transitions to a different state (infected, dead, or reverted to idle).
- **Parent-Child Relationship:** Label node (StateLabel) must be a child of the InfectionStateFX node; it reads state from the parent EnemyInfection's EnemyStateMachine.

**Acceptance Criteria:**
- Weakened color tint is applied to the sprite via `modulate`.
- State label "Weakened" is visible and legible on a standard display.
- Label color contrasts against typical enemy sprites.

---

#### F2: Infected State Visual Feedback
**Requirement:** When an enemy transitions from weakened to infected state, a second distinct visual cue must differentiate infected from weakened.

**Details:**
- **Color Tint:** Apply `Color(0.75, 0.5, 1.0, 1.0)` (purple/violet) to the enemy's EnemyVisual CanvasItem `modulate`.
- **State Label:** Display a Label node with text "Infected" in color `Color(0.85, 0.65, 1.0, 1.0)` (light purple/lavender).
- **Trigger:** Label `_update_state_label()` is invoked whenever `_esm.get_state()` returns `"infected"`.
- **Persistence:** Tint and label remain visible until the enemy transitions to dead or any reset state.
- **Distinctiveness:** Purple must be visually distinct from amber (weakened) at the target camera distance; contrast ratio must exceed 3:1 in standard editor viewport lighting.

**Acceptance Criteria:**
- Infected color tint is applied and clearly different from weakened.
- State label "Infected" is visible and legible.
- Weakened and infected are distinguishable at target gameplay camera distance without toggling debug overlays.

---

#### F3: Idle State Visual Feedback
**Requirement:** When an enemy is in idle or active state (not yet weakened), default visual feedback must apply.

**Details:**
- **Color Tint:** Apply `Color(1.0, 1.0, 1.0, 1.0)` (white, no tint) to the enemy's EnemyVisual `modulate`.
- **State Label:** Hide the state label (set `visible = false`).
- **Trigger:** This state is the default and applies when `_esm.get_state()` is neither weakened, infected, nor dead.

**Acceptance Criteria:**
- Idle enemies render with no color tint (default appearance).
- No state label is visible for idle enemies.

---

#### F4: Dead State Visual Feedback
**Requirement:** When an enemy is dead (killed via absorb or other means), a dimmed, desaturated appearance must indicate the dead state.

**Details:**
- **Color Tint:** Apply `Color(0.25, 0.25, 0.25, 0.5)` (dark gray with 50% alpha) to the enemy's EnemyVisual `modulate`.
- **State Label:** Display a Label node with text "Dead" in color `Color(0.5, 0.5, 0.5, 0.8)` (medium gray, slightly transparent).
- **Trigger:** Label `_update_state_label()` is invoked whenever `_esm.get_state()` returns `"dead"`.
- **Intent:** The dimmed appearance signals that the enemy is no longer interactive and cannot be infected or absorbed.

**Acceptance Criteria:**
- Dead enemies are visibly darker and grayed-out.
- State label "Dead" is visible but distinctly less vibrant than weakened/infected.

---

#### F5: State Label Rendering and Positioning
**Requirement:** All state labels (Weakened, Infected, Dead) must be rendered above the enemy sprite and remain readable without overlapping critical gameplay elements.

**Details:**
- **Node Structure:** StateLabel must be a direct child of InfectionStateFX or a designated UI layer above the enemy.
- **Z-Index / Rendering:** Label must render above the enemy sprite (higher z-value or CanvasLayer).
- **Position:** Label offset (if configurable) defaults to immediately above enemy center (e.g., offset = Vector2(0, -30)).
- **Font Size and Style:** Use the Godot default font or a configured font; minimum readable size is 12pt on a 1920×1080 display.
- **Visibility Toggle:** Controlled by `_update_state_label()` state logic; visible only for weakened, infected, dead; hidden for idle/active.

**Acceptance Criteria:**
- Label is clearly visible above the enemy.
- Label does not obscure the player character or movement area.
- Label text is readable at typical gameplay camera distance.

---

#### F6: Absorb Feedback
**Requirement:** When an enemy transitions from infected to dead via absorb (InfectionAbsorbResolver.resolve_absorb), a visual feedback sequence must play to confirm the absorb action.

**Details:**

**Timing:**
- Absorb feedback begins immediately upon `resolve_absorb()` call (when the enemy transitions to dead).
- Feedback duration is 0.3–0.5 seconds (short, non-blocking).
- Feedback completes before the next frame's input processing.

**Particle Effect (Primary):**
- A small particle burst (5–15 particles) emanates from the enemy's center position.
- Particles move outward in a radial pattern and fade over 0.3 seconds.
- Particle color is white or light cyan (e.g., `Color(0.8, 1.0, 1.0, 1.0)`).
- Particle size is small (2–5 pixels, scaling down to 0 by end of lifetime).
- Particles do not collide with the player and do not alter gameplay physics.

**Optional Scale/Animation:**
- On absorb, the enemy (or a visual overlay) briefly scales up (1.0 → 1.1) over 0.1 seconds, then returns to normal.
- This provides an additional visual "pop" to confirm absorb success.
- Animation is optional; particles alone satisfy the requirement if well-implemented.

**Integration:**
- Absorb feedback is triggered in the absorb flow, likely via a new `InfectionAbsorbFXPresenter` or enhancement to `infection_state_fx.gd`.
- The presenter subscribes to absorb-resolved events (via a signal from `InfectionAbsorbResolver` or direct call from `InfectionInteractionHandler`).
- Particles spawn at the enemy's global position and are cleaned up after their lifetime expires.

**Acceptance Criteria:**
- Absorb feedback plays visibly when absorb succeeds (enemy goes infected → dead).
- Feedback completes in 0.3–0.5 seconds and does not block player input.
- Particles are visible at target camera distance.
- Feedback does not occur for non-absorb deaths or state transitions.

---

#### F7: No Gameplay Interference
**Requirement:** Visual feedback (colors, labels, particles) must not interfere with player movement, input, collision detection, or enemy behavior.

**Details:**
- **Physics:** State colors and animations are purely visual (via modulate or animation nodes), not physics bodies.
- **Input:** State labels and particles do not capture mouse/input events; they are read-only rendering.
- **Collisions:** Particle effects are non-physical (not part of the physics simulation); they do not alter enemy or player collision response.
- **Performance:** All feedback is lightweight (color assignments, label visibility toggles, simple animation tweens) and maintains 60 FPS in typical test scenes.

**Acceptance Criteria:**
- Player can move and interact normally while all state feedback is active.
- No input is lost or misdirected due to labels or particles.
- Enemy collision behavior is unchanged by state feedback.
- Frame rate remains ≥ 60 FPS during infection state transitions and absorb feedback.

---

### Non-Functional Requirements

#### NF1: Readability at Target Camera Distance
**Requirement:** All visual feedback (color tints, state labels) must be readable and distinguishable at the standard 2D gameplay camera distance and zoom level.

**Details:**
- **Camera Distance Assumption:** Standard in-editor viewport with orthogonal 2D camera at default zoom (camera position adjusted so enemies are ~ 64–256 pixels tall on screen).
- **Display Assumption:** Standard desktop display at 1920×1080 resolution; no extreme zoom or mobile scaling in this ticket.
- **Color Contrast:** Weakened (amber) and infected (purple) tints must have a contrast ratio of at least 3:1 against default enemy sprite color and against each other.
- **Label Legibility:** State labels must be ≥ 12pt font and positioned to avoid overlap with sprites; text must be readable without squinting or toggling debug overlays.

**Validation Method:**
- Manual playtest in `test_infection_loop.tscn` with human eye verification on a typical screen.
- No automated color-contrast checker is required; human judgment in Task 7 is the authority.

---

#### NF2: Scope: 2D Only (3D Deferred)
**Requirement:** This specification applies only to the 2D infection visual feedback (scripts: `infection_state_fx.gd`, scenes: `test_infection_loop.tscn`, enemies: `enemy_infection.gd`).

**Details:**
- 3D variant (`infection_state_fx_3d.gd`, `test_infection_loop_3d.tscn`, `enemy_infection_3d.gd`) is explicitly out of scope for this ticket.
- A separate ticket will be created if 3D visual feedback is needed.
- Any 3D-specific considerations (particle systems for 3D, camera distance adjustments) are ignored in this spec.

---

#### NF3: State Transitions and Idempotency
**Requirement:** Visual feedback must respond correctly to all valid state transitions and ignore invalid ones.

**Details:**

**Valid Transitions (from EnemyStateMachine):**
- idle → weakened (apply amber tint + "Weakened" label)
- weakened → infected (apply purple tint + "Infected" label)
- infected → dead (apply dim gray tint + "Dead" label, trigger absorb feedback)
- Any state → dead (if dead is reached from states other than infected, still apply dead visual, but absorb feedback is triggered only if absorb event is explicitly signaled)

**Invalid/Idempotent Transitions:**
- weakened → weakened (no change; label and tint already applied)
- infected → infected (no change)
- infected → weakened (not allowed by EnemyStateMachine; visual remains infected if this occurs)
- idle → infected (not allowed; idle must transition through weakened first)

**Reactive Logic:**
- Visual feedback is driven by `_esm.get_state()` in `_process()`, so any state change is immediately reflected visually without explicit event handling.

---

#### NF4: Label Text Content Constraint
**Requirement:** State label text must be exactly one of: "Weakened", "Infected", "Dead", or hidden.

**Details:**
- No abbreviated text (e.g., "W" for weakened), debug text, or procedurally generated labels.
- No special characters or formatting (bold, italics, etc.) unless specified.
- Label text must match the defined set exactly for consistency and testing.

---

#### NF5: Color Value Immutability for This Ticket
**Requirement:** The specified color values are the authoritative baseline for this ticket and should not be changed during implementation or integration.

**Details:**

| State | RGB Color | Hex | Rationale |
|-------|-----------|-----|-----------|
| Idle | (1.0, 1.0, 1.0, 1.0) | FFFFFF | White; no tint |
| Weakened | (1.0, 0.85, 0.5, 1.0) | FFD680 | Warm amber/tan |
| Infected | (0.75, 0.5, 1.0, 1.0) | BF80FF | Purple/violet |
| Dead | (0.25, 0.25, 0.25, 0.5) | 404040 + 50% alpha | Dark gray, dimmed |

- If future playtests reveal that color choices are hard to distinguish or do not meet AC, a follow-up ticket can refactor colors; for now, these values are locked.
- Implementation agents may adjust label text colors slightly (e.g., ±0.05 brightness) for improved contrast, but enemy sprite tint colors are fixed.

---

#### NF6: Backward Compatibility
**Requirement:** Changes to `infection_state_fx.gd` must not break existing tests, scenes, or other modules that depend on infection state presentation.

**Details:**
- Existing `InfectionStateFX` methods (`_process()`, `_modulate_for_state()`, `_update_state_label()`, `_get_visual_node()`) must continue to work.
- The StateLabel node must be created or found via `get_node_or_null()` to avoid errors if it does not exist in legacy scenes.
- New absorb feedback logic must be contained in a separate presenter or optional method so it does not impact state-tint logic.

---

#### NF7: Lightweight Animation and Performance
**Requirement:** All animations and particle effects must be lightweight and maintain 60 FPS under typical test scene load.

**Details:**
- Particle effects must use Godot's built-in Particles2D with a small emission rate (≤ 50 particles/sec) and short lifetime (0.3–0.5 sec).
- State-label updates are simple visibility/text assignments (O(1) per frame).
- Color tint changes are direct modulate assignments (O(1) per frame).
- No heavy computations, no quadratic loops, no shader recompilation per state change.
- Absorb animation (if implemented) uses Tween or AnimationPlayer for efficient scheduling.

---

#### NF8: Documentation and Code Comments
**Requirement:** All visual feedback logic must be well-documented so future agents can understand and extend it.

**Details:**
- `infection_state_fx.gd` must include clear comments explaining state-to-visual mappings.
- Absorb presenter (if new) must document trigger event, particle configuration, and lifetime management.
- Color constants may be extracted to module-level constants or a configuration dict for maintainability.

---

## Acceptance Criteria Mapping

This section maps the five high-level AC from the ticket to concrete, verifiable requirements.

| AC # | Acceptance Criterion | Mapped Requirements | Verification Method |
|------|----------------------|---------------------|---------------------|
| 1 | Weakened enemy has visible cue (e.g. VFX, color, animation) | F1 (weakened color + label) | Verify weakened enemies render with amber tint and "Weakened" label |
| 2 | Infected enemy has visible cue distinct from weakened | F2 (infected color + label, distinct from F1) | Verify infected enemies render with purple tint and "Infected" label; confirm purple ≠ amber visually |
| 3 | Absorb has clear feedback (e.g. pull, particle, short animation) | F6 (absorb particle effect ± scale anim) | Trigger absorb and observe particle burst and/or scale animation at enemy center |
| 4 | Feedback is readable at target camera distance and does not block gameplay | NF1 (readability), F7 (no interference) | Human playtest: confirm labels are legible, colors are distinct, player movement is unaffected |
| 5 | Infection visual feedback is human-playable in-editor: all cues are visible on typical displays and understandable without debug overlays | NF1, F1–F6, F7 | Run test scene in Godot editor on standard display; verify all cues (weakened, infected, absorb) are visible and readable without debug console or log |

---

## Implementation Constraints and Assumptions

### Scope Boundaries
- **2D only:** 3D variant is a separate ticket.
- **Existing infrastructure:** This spec assumes `EnemyStateMachine`, `InfectionAbsorbResolver`, `InfectionInteractionHandler`, and `InfectionUI` are already implemented and functional (per the completed infection_interaction ticket).
- **Test scene:** `test_infection_loop.tscn` is the primary validation scene; other scenes may inherit the visual feedback but are not required for this ticket.

### State Machine Contract
- `EnemyStateMachine` provides `get_state()` that returns one of: `"idle"`, `"active"`, `"weakened"`, `"infected"`, `"dead"`.
- `InfectionStateFX` reads state via `get_esm()` and `get_state()` reactively in `_process()`.
- No additional state-machine modifications are required for this ticket.

### Absorb Event Wiring
- `InfectionAbsorbResolver.resolve_absorb()` is the canonical absorb function; it calls `esm.apply_death_event()` to transition the enemy to dead.
- Visual feedback (particles) should be triggered either:
  - Via a signal from `InfectionAbsorbResolver` (preferred, if the resolver is enhanced to emit a signal), OR
  - Via a direct call from `InfectionInteractionHandler` to a feedback presenter, OR
  - Via polling dead state and absorb context in the presenter (fallback).
- Implementation agents will choose the cleanest integration point.

### Godot Version and Availability
- Assumes Godot 4.x with CanvasItem.modulate, Label, and Particles2D available.
- Assumes AnimationPlayer or Tween for optional absorb scale animation.

---

## Out-of-Scope Items

The following are explicitly out of scope for this ticket and may be addressed by future work:

1. **3D variant:** `enemy_infection_3d.gd` and 3D test scenes.
2. **Advanced particle art:** Colored sprites, trails, or custom particle shapes; simple white/cyan particle dots are sufficient.
3. **Sound design:** No audio feedback for state transitions or absorb; audio may be added in a future ticket.
4. **Animation polish:** State transition animations are transitions are simple color tweens or instant; advanced skeletal animation or sprite swaps are out of scope.
5. **Dynamic camera scaling:** No zoom-responsive label sizing; standard viewport readability is assumed.
6. **Mobile or exotic display support:** Only standard desktop 1920×1080 assumed.
7. **Persistence or save/load:** Visual feedback is session-scoped; cross-scene persistence is out of scope.

---

## Test Strategy (High-Level)

Tests are designed by the Test Designer Agent based on this spec. High-level strategy:

### Primary Tests (Task 2)
- Verify `_modulate_for_state()` returns correct color values for each state.
- Verify state label visibility and text match state (weakened → "Weakened", infected → "Infected", etc.).
- Verify state label is hidden for idle state.
- Verify absorb feedback is triggered when absorb event is signaled (if available via signal).

### Adversarial Tests (Task 3)
- Repeated weaken/infect transitions → colors and labels update correctly each time.
- Rapid state changes (idle → weakened → infected → dead in quick succession) → no visual glitches, duplicate labels, or FX.
- Absorb triggered while state is changing → particles and animations complete cleanly.
- Dead state from non-absorb sources (e.g. manual esm.apply_death_event) → dead visual applies without spurious absorb feedback.

---

## Revisions and Future Work

### Revision 1.0 (Current)
- Initial specification covering weakened/infected state cues, absorb feedback, and readability requirements.
- Locked color values and label text for baseline AC validation.

### Future Revisions (Post-Playtest)
- If human playtest (Task 7) reveals readability issues (e.g., colors too similar), a new revision may adjust color values and increment version to 1.1.
- If absorb feedback is deemed too subtle or too loud, animation/particle parameters can be tuned in a revision without breaking the spec contract.
- 3D variant specification will be created in a separate ticket.

---

## Glossary

| Term | Definition |
|------|------------|
| **State Tint** | A color modulate applied to the EnemyVisual CanvasItem; e.g., weakened tint is (1.0, 0.85, 0.5, 1.0). |
| **State Label** | A Label node child of InfectionStateFX that displays the current state name ("Weakened", "Infected", "Dead") or is hidden for idle. |
| **Absorb Feedback** | Visual cue (particle burst and/or scale animation) that plays when an infected enemy is absorbed and transitions to dead. |
| **Target Camera Distance** | Standard 2D gameplay camera zoom/position at which enemies are typically 64–256 pixels tall on screen; reflects default in-editor viewport. |
| **Readability** | The human perception that a visual element (color, label, particle) is clear and distinguishable without debug overlays or excessive zoom. |
| **Idempotent** | A state transition that has no visible effect if repeated (e.g., weakened → weakened does not change appearance). |

---

## Sign-Off

This specification is **ready for implementation**. All acceptance criteria have been mapped to concrete functional and non-functional requirements. The existing `infection_state_fx.gd` serves as the foundation for state-tint and label logic; absorb feedback will be integrated via a presenter pattern. Implementation agents should follow this spec strictly; deviations require a new CHECKPOINT entry and assumption logging before proceeding.

**Spec Author:** Spec Agent  
**Date:** 2026-03-07  
**Next Stage:** TEST_DESIGN (Test Designer Agent)
