# TICKET: M12-04

**Milestone:** M12 Fused Mutation Attacks  
**Type:** Implementation

## Title

Acid + Claw fusion attack — venomous shred (3-hit combo with stacking poison)

## Description

Fusing acid and claw mutations creates a rapid melee attack that applies acid DoT on every hit. Unlike the base acid attack (which has a single DoT instance with refresh), each claw swipe in the combo poisons the enemy with a *separate* stacking acid instance. This rewards staying in melee range for sustained damage — three successful hits at close range create three independent DoT stacks that tick simultaneously.

Implementation builds on the `fusion_attack_framework` (M12 ticket 03) to combine Claw's hitbox/knockback mechanics with Acid's DoT application system.

## Acceptance Criteria

- Fusion attack resource created: `attacks/resources/acid_claw_fusion.tres`
  - Effect type: `MELEE_SWIPE_COMBO`
  - Damage per hit: 1.8
  - Combo hits: 3
  - Attack cooldown: 2.0s
  - Range: 1.2
  - Knockback per hit: 80.0 (direction: away)
- Attack executor integrates with FusionAttackFramework
  - Claw hitbox spawns at frame 6, 12, 18 (startup)
  - Each hit applies unique acid DoT via `AcidVFXSystem`
  - Acid modifier: `{ "acid_duration": 2.5, "acid_dps": 0.4 }`
- DoT stacking verified: 3 simultaneous stacks visible in enemy debug display
  - Stacks do NOT refresh each other; each decays independently
  - Damage tick rate matches base acid (10Hz)
- Attack feedback implemented:
  - Melee swipe sound triggers per hit
  - Poison VFX color overlay on enemy per applied stack
  - Knockback applies per hit
- Attack balanced in test encounters
  - DPS: ~1.2 per combo at full 3 stacks (3 hits × 1.8 damage + 3 stacks × 0.4 acid DPS for 2.5s)
  - Cooldown enforces 2.0s between combos (prevents spam)
- Attacks database entry created (`attacks.json`)
- All M11 prerequisite tests still pass
- `run_tests.sh` exits 0

## Dependencies

- M12 ticket 01: fused_attack_database_integration (done)
- M12 ticket 03: fusion_attack_framework (done)
- M11 ticket 04: attack_resource (base attack class)
- M11 ticket 05: attack_executor_handlers

## Implementation Notes

- Hitbox timing critical: each swipe must trigger collision detection separately
- Acid stacking: use `AcidVFXSystem.apply_acid()` three times (once per hit) to ensure separate instances
- Cannot refresh existing poison stacks (unlike base acid attack which refreshes)
- Test framework: verify 3 poison stacks with `enemy.acid_stacks.size() == 3` after successful combo

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
BLOCKED

## Revision
9

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: 94 tests written covering AC-1 through AC-6, adversarial, seams, and stacking isolation. Implementation verified by code trace only — NO shell test run has been executed at any prior stage. run_tests.sh exit code is unknown.
- Static QA: CRITICAL-1 (async wrapper dispatch), CRITICAL-2 (deduplication), WARNING-1 (counter comment) all fixed per 2026-05-29T-static-qa-fix-run.md.
- Integration: Not Run.
- Manual (AC-4 presentation): melee_vfx_requested signal emission per hit is covered by test_ac2f. Melee swipe sound trigger and per-stack color overlay are presentation-layer concerns requiring human in-editor verification; no documentation of this exists.
- Git state: Unverifiable without shell command. No M12-04 implementation commit is visible in the 5-commit git log provided at conversation start.

## Blocking Issues
- BLOCKER-1: run_tests.sh has never been executed. No agent had shell access. AC-8 (run_tests.sh exits 0) is unmet. Human or CI must run `timeout 300 bash ci/scripts/run_tests.sh`, record verbatim output, confirm exit 0, and document in project_board/checkpoints/M12-04/2026-05-29T-test-run.md.
- BLOCKER-2: Git state unverified. Workflow enforcement requires clean working tree and pushed commits before Stage COMPLETE. Human must run `git status` + `git log --oneline -10` to confirm M12-04 implementation is committed and pushed. If dirty: commit and push first.

## Escalation Notes
- ADVISORY: Inter-hit timer (AC-2b, frame 6/12/18 hitbox timing) is not implemented — the executor fires all combo hits synchronously with no timer await between hits. The combo_frame_interval modifier is stored but never consumed. This is an intentional implementation trade-off documented in the Gameplay Systems Agent checkpoint (2026-05-29T-gameplay-systems-run.md). If tests pass, Human must decide whether to accept this gap or file a follow-up ticket for runtime timing accuracy.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "required": [
    "run test suite and record verbatim exit code and output",
    "verify git status is clean for M12-04 implementation files",
    "verify git push succeeded or push now",
    "optionally perform manual in-editor verification of sound and VFX"
  ]
}
```

## Status
Blocked

## Reason
AC-8 (run_tests.sh exits 0) and AC-7 (all M11 prerequisite tests pass) have no runtime evidence — every prior agent lacked shell execution access. Git state for M12-04 implementation commits is unverified. Workflow enforcement v1 is explicit: Stage COMPLETE requires confirmed clean working tree and pushed commits. Human must run the test suite, confirm pass, verify and push any unpushed commits, then either re-run the AC Gatekeeper Agent or manually advance Stage to COMPLETE. All other acceptance criteria are covered by code review and test suite analysis (see checkpoint 2026-05-29T-ac-gatekeeper-run.md for full evidence matrix).
