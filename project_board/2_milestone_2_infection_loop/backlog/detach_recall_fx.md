# Detach & recall visual feedback

**Epic:** Milestone 2 – Infection Loop  
**Status:** Backlog

---

## Description

Add lightweight visual feedback for the detach and recall actions so they are clearly readable without relying on HP/chunk HUD alone. This includes distinct cues for detach, recall start, and chunk reabsorption, using placeholder-friendly shapes, color, and simple effects.

## Acceptance criteria

- [ ] On detach, the player receives a brief, readable feedback cue (e.g. flash/pulse on the slime body, small burst at the chunk spawn position, or short screen shake)
- [ ] On recall start, there is a distinct cue indicating recall (e.g. Line2D “tendril” between chunk and player, or a clear color/outline change on the chunk for the travel window)
- [ ] On reabsorption, there is a clear confirmation cue (e.g. brief flash on player and/or chunk disappearance effect) that is visually distinct from detach
- [ ] Visuals do not block control; movement and input responsiveness remain unchanged during detach and recall
- [ ] Implementation is limited to scenes and presentation scripts; HP math and `simulate()` in `movement_simulation.gd` are unchanged

