# M12-02 Static QA Fix Run — 2026-05-29

**Ticket:** project_board/12_milestone_12_fused_mutation_attacks/backlog/02_fused_attack_resources.md
**Agent:** Gameplay Systems Agent
**Stage transition:** STATIC_QA (targeted fix pass)

---

## Changes Made

### Fix 1 — Stale "Tests are RED" comment removal

**File:** `tests/scripts/attacks/test_fused_attack_resources.gd`

Removed the comment block in the Design notes section that read:
> Tests are RED on clean checkout: fused attacks are not yet registered in
> _register_defaults(). All get_fused_attack() calls return null until
> implementation adds the 6 registration blocks.

Implementation is merged. These four lines were misleading any reader doing a clean checkout.

**File:** `tests/scripts/attacks/test_fused_attack_stats.gd`

Removed the comment line in Design notes that read:
> Tests are RED on clean checkout (fused attacks not yet registered).

---

### Fix 2 — Remove frozen base-stat constants; use live DB lookups in FAR-7 test

**File:** `tests/scripts/attacks/test_fused_attack_stats.gd`

Removed 14-line frozen constants block:
```
# Base attack stats for FAR-7 meaningful-distinction comparisons.
# Source: scripts/attacks/attack_database.gd constants at M12-02 freeze.
const _BASE_CLAW_DAMAGE := 3.0
const _BASE_CLAW_COOLDOWN := 0.8
const _BASE_CLAW_RANGE := 1.5
const _BASE_CLAW_KNOCKBACK := 2.0
const _BASE_ACID_DAMAGE := 1.0
const _BASE_ACID_COOLDOWN := 2.0
const _BASE_ACID_PROJECTILE_SPEED := 8.0
const _BASE_CARAPACE_DAMAGE := 4.0
const _BASE_CARAPACE_KNOCKBACK := 5.0
const _BASE_ADHESION_DAMAGE := 1.0
const _BASE_ADHESION_COOLDOWN := 2.5
```

In `test_far7_fused_attacks_differ_from_base_components`, replaced all 10 uses of those constants with live DB lookups:

```gdscript
var base_claw = db.get_base_attack("claw")
var base_acid = db.get_base_attack("acid")
var base_carapace = db.get_base_attack("carapace")
var base_adhesion = db.get_base_attack("adhesion")
```

Guard added: if any base lookup returns null, test fails explicitly rather than comparing against null.

Comparison sites changed (before → after):
- `acid_claw.damage > _BASE_CLAW_DAMAGE` → `acid_claw.damage > base_claw.damage`
- `adhesion_claw.cooldown > _BASE_CLAW_COOLDOWN` → `adhesion_claw.cooldown > base_claw.cooldown`
- `adhesion_claw.damage > _BASE_ADHESION_DAMAGE` → `adhesion_claw.damage > base_adhesion.damage`
- `carapace_claw.attack_range > _BASE_CLAW_RANGE` → `carapace_claw.attack_range > base_claw.attack_range`
- `carapace_claw.damage > _BASE_CARAPACE_DAMAGE` → `carapace_claw.damage > base_carapace.damage`
- `acid_adhesion.projectile_speed > _BASE_ACID_PROJECTILE_SPEED` → `acid_adhesion.projectile_speed > base_acid.projectile_speed`
- `acid_adhesion.cooldown > _BASE_ADHESION_COOLDOWN` → `acid_adhesion.cooldown > base_adhesion.cooldown`
- `acid_carapace.damage > _BASE_ACID_DAMAGE` → `acid_carapace.damage > base_acid.damage`
- `adhesion_carapace.knockback_magnitude < _BASE_CARAPACE_KNOCKBACK` → `adhesion_carapace.knockback_magnitude < base_carapace.knockback_magnitude`
- `adhesion_carapace.damage > _BASE_ADHESION_DAMAGE` → `adhesion_carapace.damage > base_adhesion.damage`

---

## Scope Boundary

Deferred (explicitly out of scope per ticket instructions):
- `_register_defaults()` refactor
- `_make_db` triplication
- Magic string constants

---

## Test Execution Note

This agent environment does not have access to a shell tool and cannot execute
`timeout 300 godot --headless -s tests/run_tests.gd` or `task hooks:gd-review` directly.

The logic changes are mechanically correct:
- All frozen constants were removed and their sole consumer (FAR-7 test function) was updated to use live lookups from the same DB instance that is already constructed and verified non-null at that point in the test.
- The AttackDatabaseNode.get_base_attack() API is confirmed present in scripts/attacks/attack_database.gd (line 304).
- The AttackResource fields accessed (`.damage`, `.cooldown`, `.attack_range`, `.projectile_speed`, `.knockback_magnitude`) are all standard fields on AttackResource.
- No behavioral change to any test assertion logic — only the source of the comparison values changed from compile-time frozen literals to runtime DB reads.

The human or orchestrator must run:
```
timeout 300 godot --headless -s tests/run_tests.gd
task hooks:gd-review -- tests/scripts/attacks/test_fused_attack_stats.gd tests/scripts/attacks/test_fused_attack_resources.gd
```
and confirm passing before marking this complete.

---

## Assumptions Made

None. All API calls verified against attack_database.gd source before use.
