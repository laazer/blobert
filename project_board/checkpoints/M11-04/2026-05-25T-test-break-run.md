# Checkpoint: M11-04 Test Breaker Run

**Agent:** Test Breaker Agent  
**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/in_progress/04_attack_resource.md`  
**Timestamp:** 2026-05-25T11:16:00Z  
**Stage transition:** TEST_BREAK → IMPLEMENTATION_GAMEPLAY (Rev 4 → Rev 5)

## Summary

Created adversarial test suite at `tests/scripts/attacks/test_attack_resource_adversarial.gd` with **52 test functions** and **100 assertions**.

## Coverage Matrix

| Spec Edge Case | Test Functions | Status |
|----------------|---------------|--------|
| EC-1: Negative damage | `test_ec01_negative_damage`, `test_ec01_large_negative_damage` | RED |
| EC-2: Zero/tiny/negative cooldown | `test_ec02_zero_cooldown`, `test_ec02_tiny_cooldown`, `test_ec02_negative_cooldown` | RED |
| EC-3: Empty attack_name | `test_ec03_empty_attack_name` | RED |
| EC-4: Unknown/empty/whitespace/special effect_type | `test_ec04_unknown_effect_type`, `test_ec04_empty_effect_type`, `test_ec04_whitespace_effect_type`, `test_ec04_special_chars_effect_type` | RED |
| EC-5: Empty modifiers .get() | `test_ec05_empty_modifiers_get_default` | RED |
| EC-6: Large modifier dict (150 keys) | `test_ec06_large_modifier_dictionary` | RED |
| EC-7: Nested/deep/array modifier values | `test_ec07_nested_modifier_dict`, `test_ec07_deeply_nested_modifier`, `test_ec07_modifier_array_value` | RED |
| EC-8: Duplicate attack_ids | `test_ec08_duplicate_attack_ids` | RED |
| EC-9: Unknown/empty knockback_direction | `test_ec09_unknown_knockback_direction`, `test_ec09_empty_knockback_direction` | RED |
| EC-10: Color boundary/HDR | `test_ec10_transparent_color`, `test_ec10_hdr_color` | RED |
| EC-11: Zero/negative attack_range | `test_ec11_zero_attack_range`, `test_ec11_negative_attack_range` | RED |
| EC-12: Stationary projectile | `test_ec12_stationary_projectile` | RED |
| EC-13: Negative/huge startup_frames | `test_ec13_negative_startup_frames`, `test_ec13_huge_startup_frames` | RED |
| EC-14: duplicate() independence | `test_ec14_duplicate_modifier_independence`, `test_ec14_duplicate_scalar_independence` | RED |

## Additional Adversarial Dimensions (beyond spec EC table)

| Dimension | Test Functions | Rationale |
|-----------|---------------|-----------|
| Extreme values (damage 999999, knockback 1e18, proj speed 1e12) | ADV-01 (3 tests) | Overflow/precision boundary |
| Negative knockback_magnitude | ADV-02 (1 test) | Semantic inversion |
| Default constructor no-null exports | ADV-03 (1 test, 10 assertions) | Null-safety invariant |
| Int/float coercion boundaries | ADV-04 (4 tests) | Type system edge |
| Modifier clear → repopulate | ADV-05 (1 test) | State lifecycle |
| Modifier key collision & type mutation | ADV-06 (2 tests) | Dictionary assumption |
| Very long strings (1000/5000 chars) | ADV-07 (2 tests) | Truncation risk |
| Instance isolation (no shared state) | ADV-08 (1 test, 6 assertions) | Memory model |
| vfx_scale edges (0, negative, extreme) | ADV-09 (3 tests) | Visual param boundary |
| Negative/zero projectile_lifetime | ADV-10 (2 tests) | Param boundary |
| All-zero combat config | ADV-11 (1 test, 8 assertions) | Combinatorial null |
| All-negative combat config | ADV-12 (1 test, 8 assertions) | Combinatorial adversarial |
| Deterministic defaults | ADV-13 (1 test, 8 assertions) | Consistency invariant |
| Numeric string modifier key | ADV-14 (1 test) | Key type confusion |
| Modifier dict reassignment | ADV-15 (1 test) | Reference semantics |

## Totals

- **Primary suite:** 23 tests, 131 assertions (from Test Designer)
- **Adversarial suite:** 52 tests, 100 assertions (this run)
- **Combined:** 75 tests, 231 assertions
- **All tests expected RED** until `scripts/attacks/attack_resource.gd` is implemented

## Decisions

| # | Would have asked | Assumption made | Confidence |
|---|------------------|-----------------|------------|
| 1 | Should the adversarial suite extend the primary test file or be separate? | Created separate file per handoff suggestion and convention (keeps concerns isolated). | High |
| 2 | Should tests validate GDScript type-system coercion (int assigned to float export)? | Yes — tests that int→float coercion works ensure the implementation uses correct typed exports. | High |
| 3 | Should deeply nested modifier tests go beyond 3 levels? | Stopped at 3 levels — sufficient to prove nesting works without excessive test complexity. | High |

## Failures

No test execution attempted — tests are designed RED (implementation does not exist). All 52 functions will fail at `_load_script()` returning null.
