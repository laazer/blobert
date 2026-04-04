# Checkpoint log — death_animation_playthrough — run-2026-04-04-planning

### [death_animation_playthrough] PLANNING — enemy removal call site
**Would have asked:** After absorb, `InfectionAbsorbResolver.resolve_absorb` sets ESM to `dead`, but no `queue_free()` on `EnemyInfection3D` appears in `scripts/`. Should despawn be owned by `EnemyInfection3D`, `EnemyAnimationController`, `PlayerController3D`, or a new small coordinator?
**Assumption made:** **EnemyInfection3D** (or its animation child via callback) owns the lifecycle: on death, disable collision/targeting, play `Death` to completion via existing `EnemyAnimationController`, then `queue_free()` the enemy root. Spec will nail the exact signal edge (`animation_finished` vs timer) and any coordinator API.
**Confidence:** Medium

### [death_animation_playthrough] PLANNING — mini-boss / scaled instances
**Would have asked:** `EnemyInfection3D.is_mini_boss_unit()` exists; must the death playthrough rules differ for mini-boss (e.g. no despawn)?
**Assumption made:** Same acceptance criteria apply unless the spec documents an explicit exception; mini-boss uses the same scene stack and must not crash on unload during death.
**Confidence:** Medium

### [death_animation_playthrough] PLANNING — dependency wire_animations
**Would have asked:** Is `wire_animations_to_generated_scenes` complete enough to unblock this ticket?
**Assumption made:** Yes — ticket lives in M7 backlog after a completed `done/wire_animations_to_generated_scenes.md`; planning treats root `AnimationPlayer` + `Death` clip availability as baseline. If a family lacks `Death`, implementation fails AC and must regenerate assets or gate in spec.
**Confidence:** High
