# M12-01 Test Break Run — 2026-05-29

**Stage:** TEST_BREAK
**Agent:** Test Breaker Agent
**Ticket:** `project_board/12_milestone_12_fused_mutation_attacks/backlog/01_fused_attack_database_integration.md`
**Spec:** `project_board/specs/fused_attack_database_integration_spec.md`
**Test file produced:** `tests/scripts/attacks/test_fused_combo_matrix_adversarial.gd`

---

## Summary

59 adversarial tests written across 26 test functions. All pass. Full suite exits 0.

```
FusedComboMatrixAdversarialTests: 59 passed, 0 failed
=== ALL TESTS PASSED ===
```

---

## Coverage matrix

| Spec ID | Adversarial category | Tests |
|---------|---------------------|-------|
| FADI-EC-1 / FADI-NF-4 | Self-fusion: registration rejected, lookup returns null, player dispatch falls back to base | 3 |
| FADI-EC-2 / FADI-3c | Composite cooldown active blocks re-fire; individual slot cds irrelevant | 2 |
| FADI-3d | Refire after composite cooldown expiry | 1 (within ec2 refire test, 4 assertions) |
| FADI-EC-3 / FADI-3b / FADI-DD-1 | Fused fire does NOT set individual slot keys; individual cd active does NOT block fused | 2 |
| FADI-EC-4 | Empty string slot A, slot B, both — registration and lookup | 4 |
| FADI-EC-5 / FADI-4c | Single slot filled routes to base, not fused | 1 |
| FADI-EC-6 | Individual slot timers isolated after fused fire | 1 |
| FADI-EC-7 | Key collision: adjacent concatenation distinct; 6 canonical keys distinct | 2 |
| FADI-5c / FADI-5b / FADI-DD-2 | Fallback does NOT set slot B; slot A cd value exact | 2 |
| FADI-7a | DEAD state blocks fused; HURT state blocks fused | 2 |
| FADI-1g / FADI-NF-5 | Null resource rejected; null does not overwrite existing | 2 |
| FADI-1c | Reverse registration overwrites same canonical key; last-write-wins | 1 |
| Order stress | 3 combos registered; no cross-contamination | 1 |
| Cooldown decay | Composite key decrements via _tick_controller_timers | 1 |
| FADI-NF-1 | Fresh db has zero fused attacks | 1 |
| Combinatorial | Invalid ops sequence does not corrupt state; valid registration succeeds after | 1 |

---

## Checkpoints logged (judgment ambiguity)

### [M12-01] TEST_BREAK — Self-fusion both-slots dispatch
**Would have asked:** When both slots are filled with the same mutation ID (not a registered self-fusion combo), does _try_attack fall back to slot A's base attack?
**Assumption made:** Yes. get_fused_attack("X","X") returns null (self-fusion rejected at registration), so the else branch fires get_base_attack(a_id). Test marked # CHECKPOINT.
**Confidence:** High — code at lines 467-474 confirms path.

### [M12-01] TEST_BREAK — Individual cooldown active does not block fused
**Would have asked:** Does the spec intend that an active individual-slot cooldown (e.g., from a prior base attack) should NOT prevent the fused attack from firing?
**Assumption made:** Yes. FADI-EC-3 explicitly states "individual-slot and composite-key cooldowns are independent." The gate at _try_attack line 479 reads cooldown_key (composite), not individual keys. Test marked # CHECKPOINT.
**Confidence:** High — FADI-EC-3 text and code both confirm.

---

## Implementation notes for Gameplay Systems Agent

The spec and existing implementation are correct. No code changes are required for M12-01 implementation scope. The following observation is passed forward as a heads-up only:

- The fallback cooldown key asymmetry (FADI-DD-2) is intentional per spec. Slot B's base attack is unreachable through `_try_attack()` when both slots are filled. No fix needed.
- The composite key format (`<sorted_lower>_<sorted_higher>`) is frozen. Key parity between `_try_attack()` inline sort and `_make_fused_key()` is verified by the combo matrix tests.
- Real `.tres` fused resources are M12-02 scope. The adversarial tests use synthetic `AttackResource` instances only.
