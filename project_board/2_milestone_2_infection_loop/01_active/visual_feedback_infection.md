# Visual feedback for infection

**Epic:** Milestone 2 – Infection Loop  
**Status:** In Progress

---

## Description

Add visual feedback for infection flow: weakened state, infected state, and absorb so the player can read the loop without relying on UI alone.

## Acceptance criteria

- [ ] Weakened enemy has visible cue (e.g. VFX, color, animation)
- [ ] Infected enemy has visible cue distinct from weakened
- [ ] Absorb has clear feedback (e.g. pull, particle, short animation)
- [ ] Feedback is readable at target camera distance and does not block gameplay
- [ ] Infection visual feedback is human-playable in-editor: all cues are visible on typical displays and understandable without debug overlays

---

## Execution Plan

**Overview:** Enhance infection state visual feedback (weakened, infected) with distinct, readable cues, and implement absorb feedback. Primary scope is 2D variant (`infection_state_fx.gd`, `test_infection_loop.tscn`); 3D variant (`infection_state_fx_3d.gd`) can follow in a separate ticket. Spec defines exact visual mechanics; tests validate readability and absence of gameplay interference; implementation refines existing state-tint logic and adds absorb particle/animation; presentation ensures all cues are human-readable without debug overlays.

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Define authoritative spec for visual feedback: weakened and infected state cues (color, sprite, particle, animation), absorb feedback (particle, pull suggestion, or animation), readability requirements (camera distance, contrast, legibility), and constraints (no gameplay interference, playable on typical display without debug overlays). | Spec Agent | This ticket, `infection_state_fx.gd`, `infection_state_fx_3d.gd`, existing infection interaction/state machine architecture, CHECKPOINTS `[visual_feedback_infection]`. | Spec document (e.g. `project_board/specs/visual_feedback_infection_spec.md`) defining: exact color values for weakened/infected/idle, particle/animation triggers, absorb feedback timing and mechanics, camera framing assumptions, and minimum contrast/legibility standards. | None | Spec maps each AC to concrete visuals and clarifies absorb feedback scope (particles, pull, UI cue, or combination). | Assumes 2D is primary scope for this ticket; 3D follows separately. Existing state-tint + label are starting points, not hard constraints. |
| 2 | Design primary tests validating visual feedback readability and state transitions: weakened/infected colors are distinct and apply correctly, state label renders and is readable, absorb feedback triggers at the right time, and no visual feedback blocks player movement/interaction. | Test Designer | Spec from Task 1, existing infection interaction tests, `infection_state_fx.gd` and test scene structure. | Primary test file(s) in `tests/` asserting: color modulate values for each state, state label visibility/text, absorb feedback presence, and scene graph integrity (no orphaned VFX nodes). Registered in test runner. | Task 1 | Tests validate that weakened vs infected produce visually distinct outputs and absorb feedback is triggered; tests run headless and pass against current/future code. | Tests focus on deterministic state → visual mapping (color values, label text) rather than pixel-perfect rendering or artist subjective judgment; human playtest in AC5 provides final validation. |
| 3 | Design adversarial tests covering edge cases: repeated weakens, rapid infect transitions, absorb during state change, and ensuring no visual glitches, duplicate FX, or softlocks due to feedback logic. | Test Breaker | Spec, primary tests from Task 2, existing state machine tests. | Adversarial test file(s) exercising state transition edge cases and FX cleanup; all registered. | Task 2 | Adversarial suite passes; no visual artifacts or state inconsistencies under repeated/overlapping transitions. | Assumes state transitions are already robust (per enemy_state_machine tickets); FX layer must cleanly follow state changes without introducing new softlocks. |
| 4 | Refine and validate 2D weakened/infected state visual feedback (color tints, state label, distinct appearance): enhance `infection_state_fx.gd` if needed (e.g. adjust color contrast, label positioning, animation smoothness) and verify readability in test scene at standard camera distance. | Presentation Agent | Spec from Task 1, current `infection_state_fx.gd`, test scene `test_infection_loop.tscn`, primary/adversarial tests. | Updated `infection_state_fx.gd` with refined color values, label styling, and optional light animations (e.g. subtle pulse for infected state); changes preserve backwards compatibility with existing test harness. In-editor verification: state changes are immediately visible and distinct without debug overlays. | Task 1, Task 2 | Weakened (amber-ish) and infected (purple-ish) are visually distinct at target camera distance; state label is legible and positioned consistently; all tests remain green. | Color values may require iterative adjustment based on human playtest feedback; assumes monitor contrast and Godot display are baseline (no exotic color profiles assumed). |
| 5 | Implement absorb visual feedback (particles, animation, or pull cue) in the absorb flow: wire absorb event (from `InfectionAbsorbResolver` or `InfectionInteractionHandler`) to a new or enhanced FX presenter that spawns particles, animates a visual cue, or suggests pull (e.g. brief scale animation on enemy or player). | Presentation Agent | Spec from Task 1, existing `InfectionAbsorbResolver`, `detach_recall_fx_presenter.gd` (for reference), test scene. | New or updated presenter (e.g. `infection_absorb_fx.gd` or integrated into `infection_state_fx.gd`) that subscribes to absorb-resolved event and plays a short, readable feedback sequence. Absorb feedback is triggered reliably, completes without blocking player input, and is visible at target camera distance. | Task 1, Task 4 | Absorb feedback is consistently triggered when absorb succeeds, is readable without debug overlays, and does not interfere with subsequent gameplay. | Particles and scale animations are lightweight placeholders; full visual polish (particle art, custom sprites) can follow in future tickets. Assumes Godot AnimationPlayer or Tween are available for timing. |
| 6 | Integrate visual feedback (state tint, label, absorb FX) into the 2D test scene and ensure wiring with infection state machine and absorb resolver is complete. | Engine Integration Agent | Spec, refined state FX from Task 4, absorb FX from Task 5, test scene structure. | Updated `test_infection_loop.tscn` with finalized FX nodes, proper parent-child relationships, and signal connections. Scene is ready for human playtest. | Task 4, Task 5 | Scene loads without errors; all FX nodes are instantiated; state changes trigger visual updates; absorb events trigger absorb feedback; no integration regressions in infection interaction flow. | Assumes existing scene structure is stable and no major refactors are needed; minor node reorganization (e.g. FX node reparenting) is in-scope. |
| 7 | Validate 2D visual feedback in-editor: verify all AC are satisfied (weakened cue, infected cue distinct from weakened, absorb feedback, readability, no debug overlay required) by playing `test_infection_loop.tscn` on a standard display. Capture any issues (glitches, illegibility, gameplay interference) for refinement. | Presentation Agent | All prior tasks, test scene, standard Godot editor viewport. | Human playtest report documenting: all AC are satisfied (with checkbox attestation), any visual glitches observed, contrast/legibility assessment, and any refinement recommendations for future polish. | Task 6 | All five AC are manually verified and checked as satisfied. Weakened and infected are visually distinct, absorb feedback is clear, readability is confirmed on typical display, and all cues are visible without debug overlays. | Playtest is subjective; if significant readability issues arise (e.g. colors too similar, label too small), implementation may iterate before handoff. Conservative confidence: assume AC5 requires minor color/positioning tweaks. |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
SPECIFICATION

## Revision
1

## Last Updated By
Planner Agent

## Validation Status
- Tests: Not Run (test design and implementation pending)
- Static QA: Not Run (implementation pending)
- Integration: Not Run (implementation and wiring pending)

## Blocking Issues
None identified; plan is complete and ready for Spec Agent handoff.

---

# NEXT ACTION

## Next Responsible Agent
Spec Agent

## Context for Next Agent
- Read this ticket and the execution plan above.
- Review CHECKPOINTS entries under `[visual_feedback_infection]` to understand key assumptions (2D primary scope, absorb feedback is visual-only, readability at standard camera distance).
- Reference existing implementations: `infection_state_fx.gd` (color tint + label, 2D), `infection_state_fx_3d.gd` (blink feedback, 3D), `detach_recall_fx_presenter.gd` (example presenter pattern).
- Consult test scene: `scenes/test_infection_loop.tscn` — run it to assess current visual feedback and identify gaps.
- Draft spec document (`project_board/specs/visual_feedback_infection_spec.md`): define exact color values, particles/animation scope, and AC-to-visual mapping.
- Update this ticket: set Stage to TEST_DESIGN, increment Revision, set Last Updated By to `Spec Agent`, set Next Responsible Agent to `Test Designer`.
