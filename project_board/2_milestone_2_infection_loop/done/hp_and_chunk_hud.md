# HP & chunk HUD

**Epic:** Milestone 2 – Infection Loop  
**Status:** Backlog

---

## Description

Add a minimal but readable HUD to show slime HP and chunk state in both the core movement prototype and infection-loop scenes, built on the existing `current_hp`, `max_hp`, and `has_chunk` fields. This ticket is presentation-only: no changes to simulation or HP math.

## Acceptance criteria

- [ ] A non-debug HP bar plus numeric value is visible in `test_movement.tscn` and `test_infection_loop.tscn`, updating every frame from the player’s current HP
- [ ] HP display clearly reflects HP reduction on detach and HP restoration on recall
- [ ] A chunk state indicator (icon or text) clearly shows attached vs detached (driven by `has_chunk`) and is visible during normal play
- [ ] HUD layout stays readable at default resolution and camera framing and does not overlap critical play space
- [ ] Implementation lives in scenes / UI scripts only; `movement_simulation.gd` and HP formulas are unchanged

