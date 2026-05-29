# M12-02 Test Breaker Run

**Run ID:** 2026-05-29T-test-break-run
**Ticket:** project_board/12_milestone_12_fused_mutation_attacks/backlog/02_fused_attack_resources.md
**Stage:** TEST_BREAK → IMPLEMENTATION_GAMEPLAY
**Agent:** Test Breaker Agent
**Date:** 2026-05-29

---

## Summary

Adversarial test suite written at `tests/scripts/attacks/test_fused_attack_resources_adversarial.gd`.
30 test functions covering 13 adversarial dimensions (ADV-1 through ADV-13 plus bonus).

Suite runs cleanly: 1 passed (ADV-6 base_count=4, an implementation-independent invariant), 29 failed
(all fused-dependent tests, as expected). Pre-existing 49 failures unchanged. Total failures: 78.
No crashes, no parse errors.

---

## Adversarial Angles Covered

| ID | Angle | Risk Level | Why primary suite misses it |
|----|-------|------------|----------------------------|
| ADV-1 | carapace_claw startup_frames > 0 | High | Primary suite covers startup_frames == 8, but not the property-forgotten zero case as a separate assertion |
| ADV-2 | Modifier dict deep-copy independence (shared keys) | High | Primary suite never mutates one resource's modifiers and checks another |
| ADV-3 | adhesion_claw slow:0.0 exact type assertion in isolation | High | Primary suite covers this in stats test, but isolation is needed to confirm it's the exact float type |
| ADV-3b | bool(slow) == false documents the falsy trap for all 3 root combos | Medium | Primary suite only covers adhesion_claw and acid_adhesion, not adhesion_carapace separately |
| ADV-4 | All 10 IDs (4 base + 6 fused) globally unique | High | Primary suite only checks 6 fused IDs; base vs fused collision is untested |
| ADV-5 | get_fused_attack_count() stability across separate instances | Medium | Primary suite checks count but not cross-instance isolation (singleton contamination risk) |
| ADV-6 | base_attack_count() still 4 after fused registrations | Medium | Covered in primary suite but the separate assertion is useful as a standalone regression guard |
| ADV-7 | vfx_scale > 0.0 for all 6 fused attacks | Medium | Primary suite checks exact values, but zero-scale invisible-VFX guard is not explicit |
| ADV-8 | Projectile-type fused attacks have projectile_speed > 0.0 | Medium | Primary suite checks projectile_speed == 10.0 but not the > 0 guard |
| ADV-9 | acid_adhesion both modifier families coexist | High | FAR-EC-5: copy-paste risk; primary suite covers in stats but not as an isolated concern |
| ADV-10 | Float precision for 0.8, 0.6, 1.2 acid_dps values | Medium | FAR-EC-8: primary suite uses approx but tests are bundled; isolation exposes precision bugs |
| ADV-11 | Modifier setter deep-copy via overwrite (distinct from ADV-2) | High | Tests AttackResource.modifiers setter isolation on a different code path |
| ADV-12 | All effect_types are known handler strings | Medium | No test currently guards against effect_type typo that would silently drop attack |
| ADV-13 | All SLAM_AOE fused attacks have startup_frames > 0 | Medium | Catches the case where only carapace_claw gets startup but acid_carapace or adhesion_carapace miss it |

---

## Key Implementation Risks for Gameplay Systems Agent

1. **slow:0.0 falsy trap** — `adhesion_claw`, `acid_adhesion`, and `adhesion_carapace` all use
   `{"slow": 0.0, ...}`. Implementation must assign exactly `0.0` float, not `null`, not `false`,
   not missing. The M11-11 bug pattern: `if modifiers["slow"]` evaluates to false even when the
   key is present. The spec requires `has("slow") and typeof == TYPE_FLOAT and slow == 0.0`.

2. **startup_frames for SLAM_AOE combos** — Three fused attacks use SLAM_AOE:
   - `carapace_claw` → startup_frames = 8 (CARAPACE_CLAW_STARTUP_FRAMES)
   - `acid_carapace` → startup_frames = 12 (ACID_CARAPACE_STARTUP_FRAMES)
   - `adhesion_carapace` → startup_frames = 12 (ADHESION_CARAPACE_STARTUP_FRAMES)
   Zero-initialising startup_frames for all fused attacks would silently break all three.

3. **All 10 IDs must be unique** — Base attacks use IDs 1–4; fused attacks must use 101–106.
   Any copy-paste of base attack block (e.g., `attack_id = 1`) would cause silent ID collision.

4. **Named constants required for every numeric literal** — DR-4. All non-identity numerics must
   be named constants at class scope. gd-review will flag any bare literal in the fused blocks.

5. **acid_adhesion modifiers must contain all 5 keys** — Copy-paste from either acid_claw (3 keys)
   or adhesion_claw (2 keys) would produce an incomplete modifier set; the other family would be lost.

---

## Test Evidence

Command run:
```
timeout 300 godot --headless -s tests/run_tests.gd
```

Exit code: 1 (expected — 78 failures: 49 pre-existing + 29 adversarial, all fused-dependent)

Adversarial suite output:
```
=== FusedAttackResourcesAdversarialTests ===
  FAIL: ADV-1_carapace_claw_startup_frames_gt_zero — carapace_claw returned null (not yet registered)
  FAIL: ADV-2_modifier_dict_deep_copy_independence — one or more fused attacks returned null (not yet registered)
  FAIL: ADV-3_adhesion_claw_slow_is_float_zero — adhesion_claw returned null (not yet registered)
  FAIL: ADV-3b_slow_falsy_bool_trap_adhesion_claw — adhesion_claw returned null (not yet registered)
  FAIL: ADV-3b_slow_falsy_bool_trap_acid_adhesion — acid_adhesion returned null (not yet registered)
  FAIL: ADV-3b_slow_falsy_bool_trap_adhesion_carapace — adhesion_carapace returned null (not yet registered)
  FAIL: ADV-4_all_10_attack_ids_globally_unique — fused 'acid'+'claw' returned null (not yet registered)
  FAIL: ADV-5_count_stable_separate_instances_db1_count_before_6 — expected 6, got 0
  FAIL: ADV-5_count_stable_separate_instances_db1_count_after_6_unaffected — expected 6, got 0
  FAIL: ADV-5_count_stable_separate_instances_db2_has_extra — expected 7, got 1
  FAIL: ADV-5_fresh_instance_count_exactly_6 — expected 6, got 0
  FAIL: ADV-6_base_attack_count_still_4_fused_count_6 — expected 6, got 0
  PASS: ADV-6_base_attack_count_still_4_base_count_4
  [... remaining FAILs for ADV-7 through ADV-13 and bonus ...]
FusedAttackResourcesAdversarialTests: 1 passed, 29 failed
=== FAILURES: 78 test(s) failed ===
```

---

## Gaps in Primary Suite Confirmed Exposed

The adversarial suite exposes these implementation traps that neither `test_fused_attack_resources.gd`
nor `test_fused_attack_stats.gd` cover as isolated assertions:

- Global ID uniqueness across all 10 attacks (base + fused)
- Cross-instance isolation (count stability)
- vfx_scale non-zero guard (zero-scale invisible VFX)
- Known effect_type string guard (typo-silent-failure)
- All three SLAM_AOE fused attacks have startup_frames simultaneously
- Modifier setter deep-copy isolation via overwrite path
- bool(slow) == false documented for all three root combos

---

## Next Action

Stage → IMPLEMENTATION_GAMEPLAY. Handoff to Gameplay Systems Agent.
Implement 6 fused attack registrations in `scripts/attacks/attack_database.gd`.
All 78 failures must become 0 after implementation.
