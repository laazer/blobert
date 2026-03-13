# Player HUD

**Epic:** Milestone 4 – Prototype Level
**Status:** Backlog

---

## Description

Replace the current debug-style text labels scattered across the screen with a proper player HUD. All status information (HP, chunk state, wall cling, mutation slots) should live in a dedicated, visually coherent overlay that makes game state easy to read at a glance. Debug/test text should only appear when explicitly enabled — not in normal play.

## Acceptance criteria

- [ ] HP bar and HP value are displayed in a fixed HUD region (e.g. top-left panel)
- [ ] Chunk status (Attached / Detached) is shown in the HUD, not as a raw text label
- [ ] Wall cling state is shown in the HUD, not as a raw text label
- [ ] Mutation slot 1 and slot 2 are shown as distinct HUD elements (icon + label), clearly separated and readable
- [ ] Absorb prompt ("Press R to Absorb") appears contextually and does not overlap other HUD elements
- [ ] Absorb feedback ("Absorbed!") flash is positioned so it does not overlap slot labels or HP
- [ ] Input hint labels (Move, Jump, Detach, Absorb) are grouped and toggled via `InputHintsConfig` — hidden by default in normal play
- [ ] No two HUD elements overlap each other at the default viewport resolution (3200×1880)
- [ ] All existing `infection_ui.gd` data bindings (HP, chunk, cling, slot manager, absorb available) are preserved — only layout and presentation change
- [ ] HUD is human-readable in-editor without debug overlays
