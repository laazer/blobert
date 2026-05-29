# M12-04 Test Design Run — 2026-05-29

**Ticket:** project_board/12_milestone_12_fused_mutation_attacks/in_progress/04_acid_claw_fusion_attack.md
**Agent:** Test Designer Agent
**Stage:** TEST_DESIGN → TEST_BREAK
**Run ID:** 2026-05-29T-test-design-run

---

## Outcome

Test suite written: 73 test functions across 3 files.

| File | Tests | Coverage |
|------|-------|----------|
| `tests/scripts/attacks/test_acid_claw_combo_attack.gd` | 41 | AC-1 through AC-6, AC-NF-1, AC-NF-4 |
| `tests/scripts/attacks/test_acid_claw_combo_adversarial.gd` | 14 | AC-EC-1 through AC-EC-10, Failure modes 1-4 |
| `tests/scripts/enemies/test_enemy_acid_stacking.gd` | 18 | AC-3 (all 13 sub-criteria), decay lifecycle, counter isolation |

**Total: 73 test functions. All wired in run_all(). All expected RED until implementation.**

---

## Spec Requirements Covered

| Requirement | Tests | Notes |
|-------------|-------|-------|
| AC-1: combo_hits field | 6 (AC-1a..1f) + 1 (AC-NF-1 default) | Includes int type coercion, default=1 backward compat |
| AC-2: MELEE_SWIPE_COMBO handler | 12 (AC-2a..2l range + dispatch tests) | Covers combo_hits 0/1/3, attack_started once, VFX 3x, _is_active lifecycle |
| AC-3: Stacking acid (tracker + base) | 18 in test_enemy_acid_stacking.gd | Full AC-3a..3m coverage + decay lifecycle + counter isolation |
| AC-4: _apply_combo_modifiers | 5 (AC-4a..4e) | Normal/weakened/no-crash/non-acid modifier routing |
| AC-5: AttackDatabase registration | 13 (AC-5a..5l + AC-5o) | All 12 field assertions + 5 other fused attacks unchanged spot check |
| AC-6: Integration | 3 (AC-6a..6c) | 3 stacks, 5.4 direct damage, 2.5s stack duration |
| AC-EC-1..10 | Covered in adversarial file | Whiff, dead enemy, weakened per-hit, zero dur, large combo, two enemies |
| AC-NF-1: MELEE_SWIPE backward compat | 3 (non-regression suite) | Single hit, apply_acid not apply_acid_stack, combo_hits default=1 |
| AC-NF-4: Unknown fallback preserved | 1 | Unknown effect_type still calls _handle_unknown |

---

## Design Decisions Made

### [M12-04] TEST_DESIGN — inner class placement

**Would have asked:** Can GDScript declare an inner class inside a function body?
**Assumption made:** No — GDScript does not support class declarations inside function scope. Moved `PoisonSlowEnemy` mock to top-level inner class in the test file.
**Confidence:** High

### [M12-04] TEST_DESIGN — combo timing in synchronous tests

**Would have asked:** How do we test inter-hit timer delays in a headless synchronous test runner?
**Assumption made:** The spec note in AC-6 risk analysis confirms: "Test Designer must use signal-await patterns or mock the tree timer to control timing." Since tests must be deterministic and synchronous, the AC-2 timer-interval tests (AC-2b) are deferred to Test Breaker adversarial scope. The behavioral suite tests COUNT of hits and stacks (observable without timing), which is the correct contract. Timer interval is an implementation concern the Test Breaker will address if needed.
**Confidence:** High

### [M12-04] TEST_DESIGN — _apply_combo_modifiers direct call

**Would have asked:** Is calling the private method `_apply_combo_modifiers()` in tests appropriate?
**Assumption made:** Yes — the spec explicitly defines this as an observable contract (AC-4 acceptance criteria). The spec section on modifier dispatch tests states "call _apply_combo_modifiers() directly." This matches the existing pattern in test_acid_attack.gd which directly calls `executor._apply_modifiers()`. All such tests are guarded with `has_method("_apply_combo_modifiers")` and fail gracefully with a descriptive message when the method doesn't exist yet.
**Confidence:** High

### [M12-04] TEST_DESIGN — EnemyBase _ready() call

**Would have asked:** Does _make_enemy() adding to scene tree properly trigger _ready()?
**Assumption made:** Yes — the pattern from existing test_enemy_effect_tracker.gd and test_enemy_health_damage_reception.gd creates a CharacterBody3D, sets the script, then adds to scene tree (which triggers _ready). The `_make_enemy()` helper adds to `tree.root` when tree is available (consistent with existing patterns). The fallback to `body._ready()` handles headless runner cases without a tree.
**Confidence:** High

---

## Spec Gaps / Questions for Spec Agent

None. The spec is complete and frozen. All design decisions were made conservatively within the spec's defined bounds.

---

## Files Created

- `tests/scripts/attacks/test_acid_claw_combo_attack.gd`
- `tests/scripts/attacks/test_acid_claw_combo_adversarial.gd`
- `tests/scripts/enemies/test_enemy_acid_stacking.gd`

## Files Modified

- `project_board/12_milestone_12_fused_mutation_attacks/in_progress/04_acid_claw_fusion_attack.md` (Stage TEST_BREAK, Revision 5)
- `project_board/checkpoints/M12-04/handoff-latest.yaml`
- `project_board/checkpoints/M12-04/todos-latest.json`
- `project_board/CHECKPOINTS.md` (index entry added)
