Title:
Enemy Floating Status Effect Indicators

Description:
Extend the floating enemy UI with compact status effect indicators shown above the health bar (or merged into the same widget). Indicators communicate active combat states such as poison, slow, stun, weaken, and infection progress so players can make tactical decisions at a glance.

Acceptance Criteria:
- Active status effects render as icons/badges above each enemy health bar
- Multiple simultaneous effects are supported and displayed in deterministic order
- Expired effects are removed immediately from the indicator list
- Indicator stack has a max visible count; overflow is represented with a `+N` badge
- Indicator visuals update in real time when effects are added, refreshed, or removed
- Unknown/unmapped effect IDs render a safe fallback icon (no missing-resource errors)

Scope Notes:
- No tooltip or hover description text in this ticket
- No per-effect duration countdown text in this ticket
- Status effect gameplay logic is out of scope; this is display-layer integration only
- Precise icon art polish can iterate later; placeholders are acceptable initially

## Implementation Notes

**Godot Runtime (`scripts/`, `scenes/`)**
- Add status icon container to the world-space enemy UI scene from ticket 01
- Subscribe UI to enemy status-effect state updates (add/remove/refresh events)
- Add stable sort policy for icon ordering (for example: stun > weaken > poison > slow > infection)
- Add fallback resource path for unknown status IDs

**Tests**
- Add tests for multi-effect render order and overflow behavior
- Add tests ensuring removal on expiration and fallback icon behavior
- Add regression test proving status-only updates do not break health bar updates

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0
