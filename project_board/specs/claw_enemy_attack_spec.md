# Specification: claw_enemy_attack

Normative IDs **CLA-1** … **CLA-9** for the claw family 2-hit melee combo (`ClawCrawlerAttack`).

## CLA-1 — Script and wiring

- `res://scripts/enemy/claw_crawler_attack.gd` defines `class_name ClawCrawlerAttack` extending `Node`.
- `EnemyInfection3D` adds `ClawCrawlerAttack` when `mutation_drop == "claw"` (existing path).

## CLA-2 — Trigger range and cooldown

- `@export var attack_range: float = 2.0` — distance to player to start a full combo.
- `@export var cooldown_seconds: float = 1.2` — starts after the **second** swipe window ends (hit or timeout).

## CLA-3 — Two-hit combo

- Each full attack is **exactly two** swipe windows in sequence: swipe 1 → pause → swipe 2.
- `@export var combo_pause_seconds: float = 0.12` — wall-clock gap between end of swipe 1 window and start of telegraph for swipe 2.

## CLA-4 — Telegraph per swipe

- `@export var telegraph_fallback_seconds: float = 0.35` — default ≥ ATS-2 / ADV-ATS-08b export floor (0.3).
- Each swipe is preceded by `EnemyAnimationController.begin_ranged_attack_telegraph()` when Attack exists, else `maxf(telegraph_fallback_seconds, 0.3)` timer (ATS-2 floor alignment with other families).

## CLA-5 — Hitbox (HADS)

- Each swipe arms one `EnemyAttackHitbox` (`set_hitbox_active(true)`), re-armed for swipe 2 after swipe 1 disarms (HADS-5 one hit per activation).
- `@export var swipe_hit_window_seconds: float = 0.18` — max duration each swipe stays armed if no overlap hit.

## CLA-6 — Damage and knockback (lower per hit)

- Defaults: `damage_per_hit` **7.0**, `knockback_per_hit` **4.0** — both below carapace single-hit defaults (35 / 22) documented in `carapace_enemy_attack` spec.

## CLA-7 — Hitbox placement

- Hitbox center offset along X toward player (`sign` from player − enemy), ~0.55 m in front of enemy origin; Y/Z aligned with enemy.

## CLA-8 — Death

- No new combo when `EnemyStateMachine` state is `dead`.

## CLA-9 — Velocity

- Claw does **not** drive enemy horizontal velocity; no `enemy_writes_velocity_x_this_frame` contract.

## Non-functional

- Headless tests validate exports, combo structure markers, and damage bound vs carapace; full combo timing in editor is optional.
