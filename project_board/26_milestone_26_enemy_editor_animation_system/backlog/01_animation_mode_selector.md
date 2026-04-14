Title:
Animation Mode Selector (Static / Move / Stretch)

Description:
Add a top-level animation panel with a mode selector offering three options: Static (no animation), Move (locomotion-style oscillation), and Stretch (elastic scale deformation loop). This is the foundational control for the entire animation system — all per-part configuration in subsequent tickets layers on top of the selected mode. Currently no animation controls exist in the editor.

Acceptance Criteria:
- An "Animation" panel is visible in the editor with a clearly labeled mode selector: Static / Move / Stretch
- Static mode disables all animation parameters; the 3D preview shows no motion
- Move mode produces a looping body oscillation animation (bounce or sway) in the 3D preview
- Stretch mode produces a looping elastic scale deformation in the 3D preview
- Preview playback starts automatically when a non-static mode is selected; stops when Static is selected
- Mode selection serializes to enemy config JSON
- Switching modes does not reset other editor settings (color, texture, eye, rotation)

Scope Notes:
- No custom keyframing or timeline; Move and Stretch are parameter-driven loops only
- Animation preview is viewport-only; no export in this ticket
- Loop speed is a fixed default in this ticket (speed control is in ticket 02)

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0
