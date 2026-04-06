# carapace_enemy_attack — planning run

### [carapace_enemy_attack] PLANNING — Minimum telegraph vs global ATS-2 floor
**Would have asked:** `EnemyAnimationController` uses `ATS2_MIN_TELEGRAPH` = 0.3s for all `begin_ranged_attack_telegraph()` callers. Carapace AC requires ≥0.6s wind-up. Should we add a parameterized minimum (e.g. `begin_ranged_attack_telegraph(min_hold_seconds := 0.3)`), a carapace-only API, or handle the extra 0.3s only in `CarapaceHuskAttack` with an additional timer after the signal?
**Assumption made:** Spec Agent shall choose the smallest change that preserves acid/adhesion/claw behavior (still ≥0.3s where required) and guarantees carapace ≥0.6s wall-clock before active phase; preference order: optional parameter or override hook on `EnemyAnimationController` before duplicating telegraph logic in the attack node.
**Confidence:** Medium

### [carapace_enemy_attack] PLANNING — Heavy damage and knockback magnitudes
**Would have asked:** What numeric defaults for damage and knockback versus existing HADS / other enemies?
**Assumption made:** Spec defines `@export` defaults clearly greater than adhesion/lunge (document comparison points in spec); Test Designer encodes minimum thresholds or ratios vs a named baseline in tests.
**Confidence:** Medium

### [carapace_enemy_attack] PLANNING — Wall vs max range termination
**Would have asked:** Is “wall” strictly StaticBody3D collision, or any solid that stops `CharacterBody3D` slide?
**Assumption made:** Termination matches existing enemy movement contract: charge stops when `move_and_slide` reports collision along X or travel distance along X reaches `max_charge_range`; spec names exact predicates to mirror project patterns.
**Confidence:** Medium
