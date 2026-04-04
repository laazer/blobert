### [death_animation_playthrough] Post-review — missing Death clip despawn

**Would have asked:** Should enemies without a `Death` animation stay in the tree or despawn immediately?

**Assumption made:** GDScript reviewer flagged CRITICAL: latching without `play("Death")` never fired `animation_finished`, leaving a collision-disabled zombie. When `AnimationPlayer.has_animation(&"Death")` is false, call `_queue_enemy_root_for_deletion()` immediately after latch (same tick).

**Confidence:** High
