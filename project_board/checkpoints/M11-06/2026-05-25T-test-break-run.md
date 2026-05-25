# M11-06 Test Breaker Run — 2026-05-25

**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/in_progress/06_attack_database_integration.md`
**Spec:** `project_board/specs/attack_database_integration_spec.md`
**Stage:** TEST_BREAK → IMPLEMENTATION_GAMEPLAY
**Agent:** Test Breaker Agent

## Summary

50 adversarial tests added across 2 files:
- `tests/scripts/attacks/test_attack_database_adversarial.gd` — 30 tests (585 lines)
- `tests/scripts/attacks/test_attack_database_controller_adversarial.gd` — 20 tests (732 lines)

Combined with primary suite: 48 (primary) + 50 (adversarial) = 98 total tests.

All adversarial tests are RED (AttackDatabase not yet implemented, controller lacks attack methods).

## Adversarial Coverage Matrix

| Dimension | Tests Added | Coverage |
|-----------|-------------|----------|
| **Null & Empty** | whitespace id, sequential null, valid-then-null, both-empty fused | 6 |
| **Boundary** | long id, numeric string id, epsilon cooldown, large delta, small delta, zero delta, large cooldown, tiny velocity | 10 |
| **Type/Structure** | case sensitivity base+fused, underscore in id | 3 |
| **Invalid/Corrupt** | combinatorial invalid sequence, fused self-lookup | 2 |
| **Stress/Load** | 100 base attacks, 50 fused attacks, 20 concurrent cooldowns | 3 |
| **Mutation Testing** | overwrite same ref, resource property change, triple overwrite, fused cooldown key, attack in all permitted states | 5 |
| **Key Collision** | EC-23 base vs fused key, fused canonical alphabetical, prefix collision | 4 |
| **Isolation** | instance isolation, base↔fused no leak, fused not populating base | 4 |
| **Determinism** | registration order, attack cooldown consistency | 2 |
| **Cooldown Lifecycle** | full cycle (attack→tick→re-attack), negative cooldown, rapid sequential | 4 |
| **Slot Permutations** | EC-20 slot B only | 1 |
| **Facing Edge Cases** | large positive/negative, Y-only, Z-only, tiny negative | 5 |

## Spec Gaps Identified

1. **Whitespace mutation_id**: Spec ADB-3 only rejects `""` explicitly. Whitespace-only IDs like `" "` are technically storable. Conservative test assumes they are stored (no guard in spec).
2. **Negative cooldown**: Spec ADB-9 says "clamp to 0.0 via max(0.0, value - delta)." A negative initial cooldown from the resource is still set by _try_attack then clamped on next tick. The gap is that _try_attack doesn't validate cooldown >= 0 before setting.
3. **Fused cooldown key clarity**: Spec ADB-9 says fused key is canonical key. The test verifies a cooldown value of 3.0 appears in the dictionary rather than testing the exact key string, since the canonical key format depends on implementation of `_make_fused_key`.

## Checkpoint Assumptions

### [M11-06] TEST_BREAK — Whitespace mutation_id storability
**Would have asked:** Should whitespace-only mutation_ids like `" "` be rejected alongside empty strings?
**Assumption made:** They are storable per spec (only `""` is explicitly rejected in ADB-3 step 1).
**Confidence:** Medium

### [M11-06] TEST_BREAK — Slot B only attack selection
**Would have asked:** When slot A is empty but slot B is filled, does _try_attack use slot B's mutation_id?
**Assumption made:** Yes — spec ADB-7 step 3 says "If only one slot is filled: use that slot's mutation_id." Implementation must iterate both slots.
**Confidence:** High

### [M11-06] TEST_BREAK — Fused cooldown key verification
**Would have asked:** Should the test verify the exact canonical fused key string in _mutation_cooldowns?
**Assumption made:** Test verifies a cooldown entry with the expected value (3.0) exists rather than asserting the exact key string, since key format is an internal detail of `_make_fused_key`.
**Confidence:** High

## Files Created

- `tests/scripts/attacks/test_attack_database_adversarial.gd` (30 tests, 585 lines)
- `tests/scripts/attacks/test_attack_database_controller_adversarial.gd` (20 tests, 732 lines)

## Test Status

All 50 adversarial tests: **RED** (implementation pending)
Primary 48 tests: **RED** (46) + **GREEN** (2 — policy matrix tests)
