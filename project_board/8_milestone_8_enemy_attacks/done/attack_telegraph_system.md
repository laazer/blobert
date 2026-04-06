# TICKET: attack_telegraph_system

Title: Enemy attack telegraphing — wind-up indicator before hitbox activates

## Description

Each enemy attack must be readable before it deals damage. Implement a telegraphing phase: a brief wind-up animation or visual indicator plays before the hitbox activates, giving the player time to react. The telegraph duration is configurable per family.

## Acceptance Criteria

- Wind-up phase lasts at minimum 0.3 seconds before hitbox activates
- A visual change occurs during wind-up (animation state change, color flash, or indicator node)
- Hitbox does NOT activate during wind-up — only after wind-up completes
- Telegraph duration is an exported variable, not hardcoded
- Works for all 4 enemy families
- `run_tests.sh` exits 0

## Dependencies

- `hitbox_and_damage_system`
- `animation_controller_script` (M7)

## Specification

- **Normative requirements:** `project_board/specs/attack_telegraph_system_spec.md` — **ATS-1** through **ATS-9**, **ATS-NF1**, **ATS-NF2**.
- **Summary:** Every covered attack splits a **telegraph** phase (wind-up: visible cue, ≥ 0.3 s wall-clock before the **active** phase) from damage-dealing behavior (projectiles, melee hit checks, player effects, or future attack `Area3D`). Durations are inspector-tunable via `@export` per family; `EnemyAnimationController` plays `"Attack"` when present with a completion signal, else a fallback timer plus alternate visual. Scope: **acid_spitter**, **adhesion_bug**, **carapace_husk**, **claw_crawler**. Ordering-only dependency on backlog `hitbox_and_damage_system` (hitboxes enable after telegraph).

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- **Tests:** `tests/scripts/enemy/test_attack_telegraph_system.gd` + `tests/scripts/enemy/test_attack_telegraph_system_adversarial.gd` — all passing as part of full suite.
- **Full pipeline:** `timeout 300 ci/scripts/run_tests.sh` exit **0** (Godot: `=== ALL TESTS PASSED ===`; Python: 419 passed, 2026-04-06).
- **AC — ≥0.3 s wind-up before active phase:** T-ATS-05 default `telegraph_fallback_seconds` ≥ 0.3 (acid/adhesion); ADV-ATS-02 `maxf`/0.3 clamp on fallback `create_timer`; ADV-ATS-03 wall-clock hold / named floor in `enemy_animation_controller.gd` + attack sources (ATS-2).
- **AC — visual change during wind-up:** T-ATS-07 — `"Attack"` clip current after `_begin_attack_cycle` (animation-state telegraph cue); fallback path covered by adversarial timer/NF2 tests where Attack clip absent.
- **AC — no hitbox/damage path during wind-up:** T-ATS-04 — no `AcidProjectile3D` spawn and no adhesion lunge velocity gate during telegraph; ADV-ATS-01/10 completion guards.
- **AC — telegraph duration exported (not hardcoded only):** T-ATS-05c `@export` on acid/adhesion; ADV-ATS-08 carapace/claw telegraph exports and default ≥ floor when scripts present.
- **AC — all four prototype families:** T-ATS-06 family slugs; T-ATS-08 + ADV-ATS-07/08 carapace/claw scripts and contracts; acid/adhesion wired behavior in T-ATS-04/07; `EnemyInfection3D` wires `CarapaceHuskAttack` / `ClawCrawlerAttack` per spec/ticket scope (minimal melee path vs full ranged/lunge tests).
- **AC — `run_tests.sh` exits 0:** recorded above.
- **Static QA:** No separate `godot --check-only` run (disallowed per project guidance); acceptance satisfied via spec alignment + passing primary/adversarial telegraph suites and full `run_tests.sh`.

## Blocking Issues

- None

## Escalation Notes

- Carapace/claw: behavioral coverage is contract-level (exports, NF2, script presence) plus infection wiring; acid/adhesion carry full T-ATS-04 integration tests. See checkpoint log if scope is ever tightened to parity tests for all four.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "spec_ref": "project_board/specs/attack_telegraph_system_spec.md",
  "ticket_path": "project_board/8_milestone_8_enemy_attacks/done/attack_telegraph_system.md",
  "ac_gatekeeper_log": "project_board/checkpoints/attack_telegraph_system/run-2026-04-06-ac-gatekeeper.md"
}
```

## Status
Proceed

## Reason
All acceptance criteria have explicit automated evidence in Validation Status (primary + adversarial telegraph tests, full `ci/scripts/run_tests.sh` exit 0 on 2026-04-06). Stage set to COMPLETE; ticket moved under milestone `done/`. Merge/push as usual.
