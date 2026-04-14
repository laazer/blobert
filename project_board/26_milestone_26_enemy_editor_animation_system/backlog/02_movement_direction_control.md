Title:
Movement Direction & Speed Controls

Description:
When Move mode is active, expose a direction selector and a speed/intensity slider so users can control the primary axis and magnitude of the body's locomotion loop. This lets users distinguish a vertically bobbing enemy from one that sways side-to-side, without requiring per-part overrides.

Acceptance Criteria:
- Direction selector is visible only when animation mode is "Move"
- At least 3 direction options are available: Vertical (up/down), Lateral (left/right), Forward (z-axis)
- A speed/intensity slider is present (normalized 0–1 range; both extremes must produce visible, non-degenerate motion)
- Changes to direction or intensity update the preview animation in real time with no page reload
- Both direction and intensity serialize to enemy config JSON
- Switching to a different direction does not reset speed or other animation settings

Scope Notes:
- Direction applies to the whole body, not individual parts (per-part overrides are in ticket 03)
- No diagonal or compound direction inputs in this ticket
- No physics-based movement — purely additive procedural oscillation
- Stretch mode does not use this direction selector (Stretch has no directional axis)

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0
