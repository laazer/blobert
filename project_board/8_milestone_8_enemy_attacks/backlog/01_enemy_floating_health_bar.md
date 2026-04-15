Title:
Enemy Floating Health Bar (World-Space)

Description:
Add a world-space health bar above each active enemy so the player can quickly read damage impact during combat. The bar should track enemy position in 3D space, update in real time from current HP, and hide when the enemy is at full health unless recently damaged.

Acceptance Criteria:
- Each spawned enemy renders a floating health bar anchored above its head/body center
- Bar fill is driven by enemy current HP / max HP and updates immediately on damage/heal
- Bar is visible for damaged enemies and hidden for full-health enemies after a short timeout
- Bar always faces the camera (billboard behavior) and remains readable while moving
- Bar is removed when the enemy dies or is despawned (no orphan UI nodes)
- Feature can be toggled with a project/debug flag for performance testing

Scope Notes:
- No numeric HP text in this ticket; fill bar only
- No team/faction coloring in this ticket
- No boss-specific oversized bars in this ticket
- Multiplayer authority/sync behavior is out of scope

## Implementation Notes

**Godot Runtime (`scripts/`, `scenes/`)**
- Add a reusable world-space UI scene for health bars (for example `scenes/ui/enemy_health_bar_3d.tscn`)
- Wire enemy HP change events from enemy health/state component to the UI node
- Attach/detach health bar lifecycle to enemy spawn/despawn hooks
- Implement camera-facing billboard update each frame or via node billboard mode

**Tests**
- Add coverage verifying HP ratio updates the bar correctly
- Add coverage verifying full-health auto-hide and damaged re-show behavior
- Add coverage verifying bar cleanup on enemy death/despawn

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0
