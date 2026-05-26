# M11-08 AC Gatekeeper Run — 2026-05-26

## Ticket
`project_board/11_milestone_11_base_mutation_attacks/done/08_claw_player_attack.md`

## Stage
COMPLETE (Revision 7)

## Evidence Matrix

| AC # | Criterion | Evidence | Status |
|------|-----------|----------|--------|
| 1 | Swipe hitbox ~1.5 units in front of player | `attack_range=1.5`, `HITBOX_RANGE_FACTOR=0.5` → center 0.75, radius 0.75, span 0–1.5. Tests: boundary hit at 1.5, miss at 1.501, behind-player miss. | PASS |
| 2 | Swipe animation / VFX placeholder | `melee_vfx_requested` signal with Color.ORANGE_RED, scale 1.2. Emits on hit and whiff. Tests: CPA-6a/6b/6d, ADV_vfx_once. | PASS |
| 3 | On hit, enemy takes damage | `_apply_damage()` calls `target.take_damage(3.0, knockback)`. Tests: CPA-7b asserts damage==3.0, CPA-5a asserts exactly 1 hit. | PASS |
| 4 | WEAKENED → INFECTED | `infect_weakened` modifier with pre-damage state capture. Dead guard via `is_dead()`. Tests: CPA-3a–3j, CPA-4a–4b, ADV_five_weakened, ADV_kill_infect. | PASS |
| 5 | Cooldown 0.8s | `CLAW_COOLDOWN=0.8`. Tests: CPA-1d, CPA-5b, ADV_cd_0_8 (asserts <1.0). | PASS |
| 6 | Hitbox active one frame only | Synchronous query in `_handle_melee_swipe()`, no Area3D persistence, `_is_active` guard. Tests: CPA-5a/5c, ADV_active_block. | PASS |
| 7 | run_tests.sh exits 0 | 133/133 pass (79 primary + 54 adversarial). | PASS |

## Git Gate
- Implementation committed: `b05731b`
- Spec + checkpoints committed: `b543fb3`
- Ticket COMPLETE + move to done/: `04f57ba`
- Pre-commit hooks: all pass (gd-review, gd-organization, commit-msg-conventional)

## Linter Fix
Extracted numeric tuning literals in `attack_database.gd` to named constants (`CLAW_DAMAGE`, `CLAW_COOLDOWN`, `CLAW_RANGE`, `CLAW_KNOCKBACK`, `CLAW_VFX_SCALE`) to satisfy gd-review pre-commit gate.

### [M11-08] COMPLETE — Linter literals fix
**Would have asked:** Should I fix the numeric literal linter findings in attack_database.gd, or route back to the implementation agent?
**Assumption made:** Extracted constants in-place since the change is mechanical (no behavioral change) and blocking the commit gate in autonomous mode.
**Confidence:** High
