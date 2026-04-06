# acid_enemy_attack — run-2026-04-06-autopilot

### [acid_enemy_attack] Planning — dependency tickets
**Would have asked:** `hitbox_and_damage_system` and `attack_telegraph_system` are still in backlog; should this ticket block?
**Assumption made:** Implement minimal combat hooks on `PlayerController3D` plus `EnemyAnimationController` ranged telegraph so acid attack meets AC without waiting on those tickets.
**Confidence:** Medium

### [acid_enemy_attack] Spec — damage numbers
**Would have asked:** AC does not specify impact or DoT tick damage values.
**Assumption made:** Use exported defaults on projectile (`impact_damage` 8, `dot_tick_damage` 4) so designers can tune in the inspector.
**Confidence:** Medium
