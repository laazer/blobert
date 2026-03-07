# Wall cling visual readability

**Epic:** Milestone 2 – Infection Loop  
**Status:** In Progress

---

## Description

Make wall cling state visually obvious so a human can tell when the slime is clinging, sliding, or free-falling without debug overlays. Build on the existing wall-cling simulation and controller wiring; this ticket adds art/FX and optional HUD indication only.

## Acceptance criteria

- [ ] While wall clinging, the player sprite clearly indicates cling state (e.g. pose tilt toward wall, outline, or color tint)
- [ ] Any optional wall-cling slide effect (e.g. small particle trail along the wall) is visible but not distracting
- [ ] When leaving cling (jump away or release), cling visuals are removed within one frame; no lingering cling indicator
- [ ] A secondary indicator (icon or text) reflects cling ON/OFF and matches `_current_state.is_wall_clinging`
- [ ] Visuals work for both left and right walls (correct mirroring) and remain readable at normal camera distances

---

## Execution Plan

**Overview:** Decompose wall cling visual feedback into spec-design-test-implementation tasks. The ticket requires: (1) sprite-level visual indication of cling state, (2) optional particle slide effect, (3) instantaneous cleanup on detach, (4) HUD status indicator (already in place), and (5) correct mirroring for left/right walls. Conservative approach prioritizes simple, non-distracting visuals: color tint + optional low-cost particle trail.

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Formalize wall cling visual strategy: choose between sprite tilt, outline, or color tint; define exact tint colors (default idle vs. cling); specify optional particle trail (emission rate, particle size, cost constraints); confirm HUD label scope (already present, no change required); clarify edge cases (horizontal cling, detach cleanup, cling timer interaction). | Spec Agent | This ticket, code review of `player_controller.gd`, `player.tscn`, `infection_state_fx.gd` patterns, existing wall-cling simulation in movement_simulation.gd. | Spec document (e.g. `wall_cling_visual_readability_spec.md`) defining: visual approach (recommended = color tint + optional low-cost particles), tint color values (default green, cling = brighter/warmer green), particle emission conditions (only while sliding), HUD label already complete (AC#4), and mirroring scope (direction-agnostic tint). | None | Spec maps each AC to concrete visuals; clarifies whether particles are required or optional; confirms HUD scope; provides exact color values for implementation. | Assumes simple modulate-based tint is preferred over sprite rotation/tilt for minimal cost and direction-agnostic design. Particle trail scope is optional (AC#2 says "optional"). |
| 2 | Define primary test cases for cling visuals: sprite modulate matches cling state, tint is applied/removed in correct frames, particles emit only while sliding (if included), HUD label updates to ON/OFF, no visual lag or FPS impact. | Test Designer | Spec from Task 1, existing test patterns from `test_infection_loop.gd`, `infection_state_fx.gd` implementation. | Primary test file(s) (e.g. `tests/test_cling_visuals.gd` or integrated into `test_human_playable_core.gd`) asserting: modulate color values when clinging vs. idle, tint applied/removed within one frame of state change, particle emitter status matches cling + slide state, HUD label text contains ON/OFF. | Task 1 | Tests validate that cling visuals are applied only when `is_wall_clinging == true`, removed immediately on false, and HUD updates in sync. Tests run headless and pass against current/future code. | Tests focus on state → visual mapping (color values, HUD text) rather than pixel-perfect rendering; human playtest provides final visual confirmation. |
| 3 | Design adversarial tests covering edge cases: repeated cling transitions, detach while sliding, cling on left vs. right walls, particle cleanup on detach, and visual stability under high-frequency state changes. | Test Breaker | Spec, primary tests from Task 2, existing movement/physics tests. | Adversarial test file(s) exercising rapid cling/detach, left/right walls, and particle behavior; all registered. | Task 2 | All adversarial tests pass; no visual glitches, tint lag, or particle leaks under stress; cling indicator correctly mirrored on both walls. | Assumes movement state machine is already robust (per wall_cling spec and movement_controller tickets); FX layer must cleanly follow state changes. |
| 4 | Implement cling state FX presenter script (e.g. `cling_state_fx.gd`) that reads `PlayerController.is_wall_clinging_state()` each frame and applies modulate tint and optional particles. Follow `infection_state_fx.gd` pattern for consistency. | Presentation Agent | Spec from Task 1, current `player_controller.gd`, `player.tscn`, `infection_state_fx.gd` as reference, test cases from Task 2. | New script `scripts/cling_state_fx.gd` (or integrated into player controller if scope is minimal) that polls cling state, applies/removes tint, and optionally manages particle emitter. Tint transitions are instantaneous (no fade). Particle trail is low-cost: 1–2 particles per 0.1s while sliding, ~5 particles max concurrently. | Task 1, Task 2 | Script correctly applies cling tint and removes it within one frame of state change; particle emitter is enabled only during cling+slide; no FPS impact. All primary and adversarial tests pass. | Assumes Polygon2D `modulate` property is the correct mechanism for tinting (no shader required). Particle trail is optional; if budget is tight, can be omitted and added in a follow-up. |
| 5 | Verify wall cling state tracking in `MovementSimulation.simulate()`: ensure `is_wall_clinging` transitions are correct and no additional backend changes are needed. | Implementation Backend | `movement_simulation.gd`, specs for wall cling and chunk detach. | Verification report or commit confirming no changes needed (state tracking already correct) OR minimal fixes to movement_simulation.gd to ensure cling state is accurate. | Task 1 | `is_wall_clinging` is reliably updated by simulation and correctly reflects actual cling eligibility (wall contact + not coyote/grace-period edge cases). | Assumes cling state machine is already spec-compliant from previous tickets (wall_cling.md, movement_controller.md). |
| 6 | Integrate cling_state_fx.gd into `player.tscn`: attach presenter as child node, wire references to PlayerController and PlayerVisual, add optional CPUParticles2D child if particles are in-scope. Test in-editor. | Engine Integration Agent | Deliverable from Task 4, `player.tscn`, test scenes. | Updated `player.tscn` with attached FX presenter node and optional particle emitter. Scene loads without errors. Running `test_movement.tscn` or `test_movement_3d.tscn`, initiating wall cling, tint change and HUD update are visible. | Task 4, Task 5 | Scene loads; FX presenter is active; cling tint is applied/removed on state change; particle emitter (if present) emits only while clinging and sliding; HUD label updates. No regression in movement or collision behavior. | Assumes scene file edits are straightforward and no major refactors are needed. Particle emitter setup may require Godot 4.x CPUParticles2D tuning (emission rate, particle lifetime). |
| 7 | Static QA review of cling_state_fx.gd and integration: code quality, error handling, visual clarity, performance (no FPS drop, particle count stable), and AC compliance. | Static QA Agent | All prior tasks, code review tools, test results. | QA report confirming: code follows patterns from `infection_state_fx.gd`, no unused variables, error handling is present, visual output is clear and non-distracting, performance is stable, all AC (1–5) are met. | Task 6 | QA sign-off: code is production-ready, visuals are readable without debug overlays, mirroring works correctly, particle trail (if present) does not cause FPS drop. | Assumes artist/designer review (Task 8) will provide final visual polish recommendations. |
| 8 | Manual playtest of wall cling visuals: load `test_movement.tscn`, initiate wall cling on left and right walls, verify tint is visible and distinct, verify particle trail (if enabled) is smooth and non-distracting, verify tint clears on jump/detach, verify HUD label synchronization, and sign off on AC satisfaction. | Presentation Agent | Integrated scene, QA report from Task 7, standard Godot editor. | Playtest report documenting: all AC are satisfied (checkbox attestation), visual quality assessment (tint distinctness, particle smoothness, readability at camera distance), any glitches observed, and recommendations for future polish. | Task 6, Task 7 | All five AC are manually verified and checked. Cling tint is visible and does not over-saturate/desaturate the player. Particle trail is smooth and not distracting. Tint clears instantly on detach. HUD updates in sync. Mirroring is correct on left/right walls. Visual is readable on typical display without debug overlays. | Playtest is subjective. If significant readability issues arise (e.g., tint too subtle), implementation may iterate before sign-off. Conservative: assume 1–2 minor color/particle tweaks may be needed. |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_FRONTEND

## Revision
4

## Last Updated By
Test Breaker Agent

## Next Responsible Agent
Presentation Agent

## Status
Proceed

