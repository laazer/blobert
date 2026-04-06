# adhesion_enemy_attack — run-2026-04-07-autopilot

### [adhesion_enemy_attack] Planning — M15 navigation dependency
**Would have asked:** Ticket lists M15 (Enemy Navigation); lunge before full AI may look odd.
**Assumption made:** Implement range-gated lunge toward player on X anyway; it is valid for sandbox enemies that stand near the player.
**Confidence:** High

### [adhesion_enemy_attack] Spec — shared hitbox system
**Would have asked:** AC references shared hitbox; only projectile overlap exists for acid.
**Assumption made:** Use horizontal proximity during the active lunge window as hit registration (same spirit as a melee hitbox).
**Confidence:** Medium
