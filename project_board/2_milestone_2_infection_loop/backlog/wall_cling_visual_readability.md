# Wall cling visual readability

**Epic:** Milestone 2 – Infection Loop  
**Status:** Backlog

---

## Description

Make wall cling state visually obvious so a human can tell when the slime is clinging, sliding, or free-falling without debug overlays. Build on the existing wall-cling simulation and controller wiring; this ticket adds art/FX and optional HUD indication only.

## Acceptance criteria

- [ ] While wall clinging, the player sprite clearly indicates cling state (e.g. pose tilt toward wall, outline, or color tint)
- [ ] Any optional wall-cling slide effect (e.g. small particle trail along the wall) is visible but not distracting
- [ ] When leaving cling (jump away or release), cling visuals are removed within one frame; no lingering cling indicator
- [ ] A secondary indicator (icon or text) reflects cling ON/OFF and matches `_current_state.is_wall_clinging`
- [ ] Visuals work for both left and right walls (correct mirroring) and remain readable at normal camera distances

