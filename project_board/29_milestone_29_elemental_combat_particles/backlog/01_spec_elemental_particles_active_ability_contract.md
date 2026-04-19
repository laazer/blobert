Title:
Spec — Elemental Particles & Active Ability Contract

Description:
Produce a normative specification for Milestone 29: how the game determines the **active ability’s element** at runtime, how that maps to particle presets, and which subsystems (player, attacks, enemies, terrain) subscribe to the same contract. This ticket is documentation-only; implementation is in subsequent tickets.

Acceptance Criteria:
- Spec file exists under `project_board/specs/` with a stable filename and **requirement IDs** (e.g. `ECP-R1`, `ECP-R2`, …) traceable to milestone README scope
- Spec lists the canonical element set and explicitly relates it to existing combat/attack type strings in code or generated data (cite concrete files after discovery)
- Spec defines **one** authoritative resolution order when multiple sources could disagree (e.g. active mutation slot vs. last-used attack vs. enemy family default), including fallback to `physical` or “no element burst”
- Spec names event or frame boundaries for: player idle/ambient loop, attack wind-up/hit/projectile spawn, enemy telegraph/hit, terrain contact — each with “must / should / may” for particle emission
- Spec includes non-functional constraints: max simultaneous particle systems per category, headless-test strategy, and a manual playtest checklist for visual verification
- Ticket references `project_board/29_milestone_29_elemental_combat_particles/README.md` and links forward to tickets `02`–`05` with a short responsibility matrix

Scope Notes:
- No Godot code changes required to close this ticket
- If discovery shows missing runtime hooks, document gaps as explicit follow-up tasks rather than blocking the spec file

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0
