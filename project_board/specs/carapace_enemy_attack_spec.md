# Specification: carapace_enemy_attack

Normative IDs **CEA-1** … **CEA-10** for the carapace family charge attack (`CarapaceHuskAttack`).

## CEA-1 — Script and wiring

- `res://scripts/enemy/carapace_husk_attack.gd` defines `class_name CarapaceHuskAttack` extending `Node`.
- `EnemyInfection3D` adds this node as `CarapaceHuskAttack` when `mutation_drop == "carapace"` (existing generator path).

## CEA-2 — Range and cooldown

- `@export var attack_range: float = 6.0` — max distance from enemy to player to **start** an attack cycle (idle → wind-up).
- `@export var cooldown_seconds: float = 4.0` — applied after the attack cycle fully completes (after deceleration ends).

## CEA-3 — Wind-up (≥ 0.6 s wall-clock)

- Before the charge **active phase**, total wall-clock time from telegraph start to charge start is **≥ 0.6 s**.
- `EnemyAnimationController.begin_ranged_attack_telegraph(min_hold_seconds)` accepts `min_hold_seconds >= 0` and enforces `max(ATS2_MIN_TELEGRAPH, min_hold_seconds)` as the minimum hold (see ATS extension).
- Carapace calls `begin_ranged_attack_telegraph(0.6)` when Attack clip exists; fallback timer path uses `maxf(telegraph_fallback_seconds, 0.6)`.

## CEA-4 — Charge kinematics

- After wind-up, the enemy moves along **world X** toward the player: `signf(player.x - enemy.x)` with zero → `+1.0`.
- `@export var charge_speed: float = 16.0`
- `@export var max_charge_range: float = 6.0` — max **horizontal** distance traveled from **charge start position** along X before the charge stops (in addition to wall / hit stops).

## CEA-5 — Velocity ownership

- During charge and deceleration, `enemy_writes_velocity_x_this_frame()` returns **true** so `EnemyInfection3D` does not zero `velocity.x`.
- `EnemyInfection3D` treats `CarapaceHuskAttack` like `AdhesionBugLungeAttack` for this gate.

## CEA-6 — Stop conditions

Charge ends when **any** of:

1. **Player hit** — `EnemyAttackHitbox` successfully damages the player during this charge (one hit per charge via HADS-5), or
2. **Wall** — after `move_and_slide`, `CharacterBody3D` reports a slide collision whose normal has `|n.x| > 0.4` while charging, or
3. **Max range** — `abs(enemy.global_position.x - _charge_start_x) >= max_charge_range`.

## CEA-7 — Damage and knockback (HADS)

- Child `EnemyAttackHitbox` (or equivalent) with defaults:
  - `@export damage_amount: float = 35.0` (greater than default 10 / adhesion lunge implicit low damage)
  - `@export knockback_strength: float = 22.0` (greater than default 8)

## CEA-8 — Deceleration

- After charge ends (any CEA-6), `velocity.x` is **not** left at full charge speed: apply decay (e.g. multiply by `0.82` per physics frame or lerp toward 0) until `abs(velocity.x) < 0.15`, then set `0.0` and start cooldown.

## CEA-9 — Telegraph integration

- `@export var telegraph_fallback_seconds: float = 0.35` — only used when Attack clip / controller path fails; still **≥ 0.6 s** wall-clock via `maxf(..., 0.6)`.

## CEA-10 — Death / invalid

- No new attack cycle when `EnemyStateMachine` state is `dead` (same as other attack nodes).

## Non-functional

- Headless tests may call internal helpers or `_apply_hit` on hitbox per HADS patterns; production path uses `set_hitbox_active(true)` during charge.
