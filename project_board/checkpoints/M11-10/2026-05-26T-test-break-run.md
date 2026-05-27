# M11-10 Test Breaker Run — 2026-05-26

**Agent:** Test Breaker Agent
**Ticket:** M11-10 (Carapace Player Attack)
**Stage:** TEST_BREAK → IMPLEMENTATION_GAMEPLAY

## Summary

Wrote 34 adversarial tests in `tests/scripts/attacks/test_carapace_attack_adversarial.gd` (887 lines). Combined with 42 primary behavioral tests from `test_carapace_attack.gd`, total test coverage is 76 tests across both files.

## Adversarial Categories Covered (23)

1. Zero-radius slam (degenerate attack_range=0.0)
2. Boundary precision (epsilon beyond, negative range)
3. Dead enemy receives take_damage call + signal
4. Dying enemy killed by slam damage mid-processing
5. Mix of alive, dead, and bare (no take_damage) enemies
6. Double/triple-tap active guard blocking
7. Grounded immediate damage
8. Airborne _is_active during wait
9. 15-enemy stress test (no cap)
10. Degenerate knockback (multiple enemies at origin)
11. Near-degenerate tiny offset knockback
12. Cooldown slowest-of-all-mutations validation
13. Database duplicate registration overwrites
14. Database invalid inputs (empty id, null resource)
15. Duck-type guard (BareEnemy + normal mix)
16. Knockback direction mutations (toward, none, zero-mag, unknown)
17. 3D positioning (Z-axis, diagonal boundary in/out)
18. Knockback Z-component zeroing
19. Modifiers isolation and deep-copy
20. VFX signal isolation (no melee_vfx from slam)
21. No-floor parent defaults to grounded
22. Facing independence (left vs right facing same result)
23. Player offset position (query uses actual pos, not origin)
24. Determinism (identical runs produce identical results)
25. Extreme damage/knockback (float overflow/NaN/INF)
26. VFX position matches player position
27. Sequential slams both succeed (state reset)
28. Carapace strongest single-hit damage of all base mutations

## Gaps Found

All 10 requested edge cases are covered. Additional 13 adversarial dimensions were added to stress the implementation beyond primary test coverage. Key vulnerabilities exposed:
- Zero/negative attack_range degenerate configurations
- DyingEnemy killed mid-slam (state transition during processing)
- BareEnemy without take_damage mixed with normal enemies
- Knockback direction string mutations ("toward", "none", unknown strings)
- 3D diagonal boundary math (sqrt(12) ≈ 3.464 > 3.0 radius)
- Knockback Z-zeroing (delta.z = 0 before normalize)
- Modifiers dict mutation leaks between AttackResource instances

## No Checkpoints Needed

No ambiguity or design decisions required during this run.
