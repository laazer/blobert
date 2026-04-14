# Epic: Milestone 24 – Keyboard Orbital Aim System

**Goal:** Aim in the 3D sandbox is a single normalized angle θ on a conceptual ring around the player, driven by keyboard snap (IJKL), fine rotation (U/O), optional precision (Shift), optional soft assist, and clear visuals — all tunable and responsive within the same frame as input.

## Scope

- **Core model:** θ in degrees (or radians internally) normalized to \[0°, 360°); unit direction derived for gameplay (projectiles, abilities, etc.).
- **Ring model:** Fixed gameplay radius; separate visual radius for presentation.
- **Primary input:** IJKL cardinal snap, dual-key 45° diagonals with a short simultaneous window (~50 ms), held dual-key resolution, consistent 3+ key policy.
- **Secondary input:** U/O counter-clockwise / clockwise with tap step vs hold ramp, acceleration curve, min/max speed, opposite-input cancel.
- **Precision:** Shift (or chosen modifier) reduces tap step and hold acceleration ramp.
- **Interaction:** Snap overrides rotation for the frame; no fighting or drift when idle.
- **Optional:** Soft aim assist (configurable strength, threshold, toggle); visual ring, aim indicator, optional cardinal highlights and tick marks.
- **Quality bar:** Same-frame aim updates, clean wrap at 360°, smooth rotation motion, no sticky grid-lock feel (design validation).

## Out of Scope

- Mouse or gamepad aim (separate milestone if needed)
- Full HUD redesign beyond aim-specific feedback
- Network multiplayer prediction (single-player / local first)

## Dependencies

- M1 (Core Movement) — `PlayerController3D` and 3D sandbox as integration surface
- M11 (Base Mutation Attacks) — consumers of aim direction once attacks need θ (can land core aim before every attack is wired)

## Exit Criteria

All acceptance criteria in the milestone tickets are met in-engine, with exported tuning for every parameter listed under AC-12.x, automated or manual test evidence for edge cases (wrap, U+O cancel, snap precedence), and a short playtest note for AC-13.x soft goals.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
