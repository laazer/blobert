# Weakening system

**Epic:** Milestone 2 – Infection Loop  
**Ticket ID:** weakening_system  
**Status:** Proceed  
**Revision:** 3  
**Last Updated By:** Test Designer Agent  
**Next Responsible Agent:** Test Breaker Agent  

---

## Workflow State

**Stage:** TEST_BREAK  
**Blocking Issues:** None  
**Next Action:** Test Breaker Agent to design adversarial test suite targeting edge cases, invalid inputs, rapid transitions, and null handling based on test_weakening_system.gd and test_weakening_system_adversarial.gd.


---

## Description

Implement the weakening system: enemies can be weakened (e.g. by chunk attack or specific interaction) so they become infectable. Define threshold, feedback, and transition to weakened state.

## Acceptance criteria

- [ ] Enemies transition to weakened state when condition is met (e.g. HP/damage threshold)
- [ ] Weakened state is clearly distinguishable (visual or UI cue)
- [ ] Weakened enemies can be infected (hook for infection interaction)
- [ ] Tuning (threshold, duration if any) is configurable
- [ ] Weakening behavior is human-playable in-editor: enemies, weakened cues, and any related UI are visible and understandable without debug overlays

---

## Implementation Notes (Planner)

### Current State  
- **EnemyStateMachine** (scripts/enemy_state_machine.gd): Fully implements weaken/infect/death state machine. States: idle, active, weakened, infected, dead. Transitions are well-defined.
- **EnemyInfection3D** (scripts/enemy_infection_3d.gd): Integrates state machine and detects chunk contact via Area3D. Calls `apply_weaken_event()` on chunk body entered. Weaken trigger is **chunk contact**, not HP/damage threshold.
- **Visual Feedback** (scripts/infection_state_fx_3d.gd): Detects state changes and applies blink effect (0.35s duration at 10 Hz). Renders to enemy visual. State labels pending refinement.
- **Test Coverage**: test_infection_state_fx_adversarial.gd exercises weakened state transitions; full infection loop is tested.

### Interpretation of AC  
Per checkpoint: chunk contact is the weakening **condition** (physical "damage" contact), satisfying AC#1. AC#4 "tuning" refers to configurable @export parameters (blink duration, visual colors, label text). AC#5 "human-playable" is verified via test_movement_3d.tscn human playtest.

### Planner Decomposition  
1. **Spec Agent**: Formalize visual distinctness (color tint, label text, contrast), define configurable @exports, document integration with infection loop.
2. **Test Designer**: Define test cases for state-to-visual mapping, particle/blink timing, readability.
3. **Test Breaker**: Adversarial suite for rapid transitions, edge cases, invalid inputs.
4. **Implementation Generalist**: Complete visual refinements (exact tint colors, label positioning), expose @export tuning knobs, ensure readability at standard camera distance.
5. **Integration**: Human playtest in test_movement_3d.tscn, verify AC satisfaction.
6. **Deployment**: Move to COMPLETE when all AC are verified.

### Checkpoints Logged  
See /project_board/CHECKPOINTS.md for autonomous decisions on:
- Trigger mechanism (chunk contact vs HP threshold)
- Configurable scope (@export parameters)
- Human-playable verification (test_movement_3d.tscn)
- Integration with infection_interaction_spec.md
- Current implementation status (mostly complete, needs visual polish + tuning + playtest)
