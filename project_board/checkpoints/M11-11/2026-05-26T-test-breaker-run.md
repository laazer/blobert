# M11-11 Test Breaker Run — 2026-05-26

## Summary

Adversarial test suite produced: `tests/scripts/attacks/test_adhesion_attack_adversarial.gd`
- **50 tests**, **852 lines**
- All 10 requested edge-case categories covered
- Implementation domain: GDScript gameplay (routes to Gameplay Systems Agent)

## Gaps Discovered

| # | Gap | Test(s) | Runtime Seam |
|---|-----|---------|--------------|
| 1 | Root duration boundary at exactly 1.0s — `_tick_slowness` uses `<=` so exact match expires | `test_root_duration_exactly_at_boundary` | `EnemyEffectTracker._tick_slowness()` |
| 2 | Zero/negative duration in `set_slowness()` silently no-ops (no error) | `test_root_duration_zero_duration_rejected`, `test_root_negative_duration_rejected` | `EnemyEffectTracker.set_slowness()` |
| 3 | Duplicate registration silently overwrites without warning | `test_duplicate_registration_overwrites` | `AttackDatabaseNode.register_base_attack()` |
| 4 | Dead enemy still receives `take_damage()` and `apply_slowness()` from projectile — no `is_dead()` guard in projectile path | `test_dead_enemy_still_receives_body_entered`, `test_dead_enemy_slow_still_dispatched` | `PlayerProjectile3D._on_body_entered()` |
| 5 | Negative slow multiplier passes through to `apply_slowness()` unchecked (clamped downstream by `maxf(0.0, ...)`) | `test_slow_negative_value_passes_through`, `test_effect_tracker_clamps_negative_multiplier` | `AttackExecutor._apply_modifiers()` → `EnemyEffectTracker.set_slowness()` |
| 6 | Zero-speed projectile never moves but still can hit overlapping bodies and despawns correctly on lifetime | `test_zero_speed_projectile_*` | `PlayerProjectile3D._physics_process()` |
| 7 | Modifier dictionary from resource is `.duplicate(true)` in executor (verified) — mutations to projectile mods don't leak back | `test_modifiers_dict_is_duplicated_not_shared` | `AttackExecutor._handle_projectile_spit()` |

## Implementation Notes for Gameplay Systems Agent

1. **Falsy-zero fix (ADHA-3)**: Both `AttackExecutor._apply_modifiers()` (line 124-127) and `PlayerProjectile3D._apply_modifiers()` (line 76-79) currently use `if slow_val and slow_val > 0.0`. Fix: change default to `null`, check `!= null`. The adversarial suite has 7 tests that will fail until this fix is applied.

2. **Wall collision despawn (ADHA-5)**: `PlayerProjectile3D._on_body_entered()` currently has no `else` branch for non-damageable bodies. Add: `else: _consumed = true; queue_free()`. The adversarial suite has 4 tests targeting wall-then-enemy ordering that will fail until this is implemented.

3. **Adhesion registration (ADHA-1, ADHA-2)**: Add adhesion block to `AttackDatabaseNode._register_defaults()`. Pattern matches existing claw/acid/carapace.

4. **Dead enemy gap**: The projectile path does NOT check `is_dead()` before calling `take_damage()` / `apply_slowness()`. The spec notes EnemyBase guards on `_is_dead` internally, so the projectile itself does not need to guard. Tests document this as a known gap — the guard lives in EnemyBase, not the projectile.

## Checkpoints

No ambiguity checkpoints needed — all edge cases are deterministic from the spec.
