# claw_enemy_attack — planning (orchestrator)

### [claw_enemy_attack] PLANNING — Two telegraphs in one combo
**Would have asked:** Should swipe 2 reuse `begin_ranged_attack_telegraph()` or a shorter timer-only wind-up?
**Assumption made:** Both swipes call `begin_ranged_attack_telegraph()` (ATS-2 floor 0.3s) for consistent minimal telegraph; `combo_pause_seconds` is wall-clock between swipe windows only.
**Confidence:** Medium

### [claw_enemy_attack] PLANNING — Per-hit damage vs carapace
**Would have asked:** Exact numeric cap for “lower than other families”?
**Assumption made:** Default `damage_per_hit` 7.0 and `knockback_per_hit` 4.0; tests assert `< 35` damage to stay below carapace single-hit default.
**Confidence:** Medium
