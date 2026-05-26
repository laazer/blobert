# M11-09 Test Design Run — 2026-05-26

## Summary

Test Designer Agent authored 33 behavioral tests for the acid player attack (M11-09) in `tests/scripts/attacks/test_acid_attack.gd` (683 lines).

## Test Coverage Map

| APA Req | Tests | Count |
|---------|-------|-------|
| APA-1 | test_apa1_acid_resource_properties | 1 (14 assertions) |
| APA-2 | test_apa2a..test_apa2d | 4 |
| APA-3 (executor) | test_apa3a..test_apa3e | 5 |
| APA-3 (projectile) | test_apa3f..test_apa3j | 5 |
| APA-4 | test_apa4a..test_apa4b | 2 |
| APA-5 | test_apa5a..test_apa5c | 3 |
| APA-6 | test_apa6a..test_apa6d | 4 |
| APA-7 | test_apa7a..test_apa7d | 4 |
| Edge cases | test_ec6..test_ec15 | 5 |
| **Total** | | **33** |

## Expected Failures (pre-implementation)

The following tests will fail until implementation is complete:
- APA-2a/2b/2c/2d: acid not yet registered in `_register_defaults()`
- APA-3b/3g/3i/3j: WEAKENED doubling not yet in `_apply_modifiers()`
- APA-6a/6b/6d: `color` property not yet on PlayerProjectile3D

## Checkpoints

No ambiguities encountered. All spec requirements were clear and testable.
