# Input hint polish for core mechanics

**Epic:** Milestone 2 – Infection Loop  
**Status:** Backlog

---

## Description

Upgrade on-screen input hints in the core movement and infection-loop scenes so a new player immediately understands move, jump, detach/recall, and absorb actions. Align hint text with actual input actions and keep layout readable across common aspect ratios.

## Acceptance criteria

- [ ] On-screen hints exist for: move (left/right), jump, detach/recall (shared input), and absorb in the infection-loop scene
- [ ] Hint text and glyphs use consistent naming with the `project.godot` input actions and key bindings
- [ ] Hints are placed at screen edges or HUD regions and do not overlap the central play area or HP/chunk UI
- [ ] Layout remains readable at common resolutions (e.g. 16:9 and 16:10) when run in-editor
- [ ] Hints can be globally toggled on/off via a single configuration point (e.g. autoload or project setting), without changing scene wiring

