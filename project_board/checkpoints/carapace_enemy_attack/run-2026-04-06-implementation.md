# carapace_enemy_attack — implementation

### [carapace_enemy_attack] IMPLEMENTATION — Telegraph min_hold parameter
**Would have asked:** None — planner checkpoint assumed optional `min_hold_seconds` on `begin_ranged_attack_telegraph`.
**Assumption made:** Implemented `begin_ranged_attack_telegraph(min_hold_seconds := -1.0)` with `_telegraph_min_hold_sec` stored per telegraph; reset on emit and death preempt.
**Confidence:** High

### [carapace_enemy_attack] IMPLEMENTATION — Hitbox typing
**Would have asked:** `EnemyAttackHitbox` not always in analyzer scope for `var` types.
**Assumption made:** `Area3D` storage + `set("damage_amount", damage_amount)` for exports.
**Confidence:** High
