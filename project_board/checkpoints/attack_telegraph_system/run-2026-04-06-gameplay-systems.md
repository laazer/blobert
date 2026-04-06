# attack_telegraph_system — Gameplay Systems implementation

**Stage:** IMPLEMENTATION_GENERALIST → STATIC_QA  
**Ticket:** `project_board/8_milestone_8_enemy_attacks/in_progress/attack_telegraph_system.md`

**Outcome:** `EnemyAnimationController` holds telegraph until wall-clock `ATS2_MIN_TELEGRAPH` (0.3 s) from start when Attack clip ends early; acid/adhesion use `maxf(telegraph_fallback_seconds, 0.3)` fallback timers, re-entry and double-finish guards, `CONNECT_ONE_SHOT` preserved. Added `carapace_husk_attack.gd` and `claw_crawler_attack.gd` (minimal telegraph + cooldown stub) and `EnemyInfection3D` wiring for `mutation_drop` `carapace` / `claw`.

**Validation:** `timeout 300 godot -s tests/run_tests.gd` exit 0; `AttackTelegraphSystemTests` 20/20, `AttackTelegraphSystemAdversarialTests` 45/45.
