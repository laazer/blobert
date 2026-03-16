# Chunk sticks to enemy on contact

**Epic:** Milestone 3 – Dual Mutation + Fusion
**Status:** In Progress

---

## Description

When a thrown chunk contacts an enemy, the chunk should stick to (attach to) the enemy rather than bouncing off or passing through. The chunk can only be recalled (reabsorbed by the player) after the enemy has been absorbed. This makes the infection loop feel more intentional — the player commits a chunk to an enemy and must complete the absorb to get it back.

## Acceptance criteria

- [ ] Chunk sticks to enemy on contact (moves with enemy, no physics bounce)
- [ ] Stuck chunk cannot be recalled until the enemy is absorbed
- [ ] After enemy absorb, chunk detaches and becomes recallable normally
- [ ] One-chunk and two-chunk flows both handled correctly (no state corruption)
- [ ] Behavior is human-playable in-editor: chunk visibly attached to enemy, recall blocked until absorb, all clear without debug overlays

---

## WORKFLOW STATE

```
Stage:              INTEGRATION
Revision:           7
Last Updated By:    Acceptance Criteria Gatekeeper Agent
Next Responsible Agent: Human
Status:             Needs Attention
Validation Status:
  Tests (Primary):    126 assertions, 0 failures — TC-CSE-001..TC-CSE-072.
                      AC1 (chunk sticks on contact): TC-CSE-020..025 PASS.
                      AC2 (recall blocked until absorb): TC-CSE-030..032 PASS.
                      AC3 (detach + recallable after absorb): TC-CSE-040..044 PASS.
                      AC4 (one-chunk and two-chunk flows): TC-CSE-060..062 PASS.
  Tests (Adversarial): 185 assertions, 0 failures — 20 mutation categories.
                      AC4 further reinforced across multi-chunk and edge-case paths.
  Static QA:         All Critical and Warning GDScript issues verified resolved in committed code.
  Full Suite:        0 failures across entire test suite.
  Integration (Manual — PENDING):
    AC5 has NOT been performed. Requirement: "Behavior is human-playable in-editor: chunk
    visibly attached to enemy, recall blocked until absorb, all clear without debug overlays."
    This criterion is inherently visual and runtime-interactive; it cannot be satisfied by
    automated tests alone. No documented evidence of a human playtest session exists.
Blocking Issues:
  - AC5: Human manual playtest required. Criterion states chunk must be visibly attached to
    enemy, recall must be blocked until absorb completes, and all behavior must be clear
    without debug overlays — in a live in-editor session. No evidence of this check having
    been performed has been documented anywhere in the ticket or Validation Status.
    Ticket must remain in INTEGRATION until a human performs and documents this check.
Escalation Notes:   AC1–AC4 are fully covered by 311 total automated assertions across primary
                    and adversarial suites with 0 failures. The sole remaining gate is the
                    manual AC5 playtest. Once a human runs the in-editor session, confirms
                    the behavior described in AC5, and documents the result here, Stage may
                    be advanced to COMPLETE.
```

## NEXT ACTION

**Next Responsible Agent:** Human
**Required Input Schema:** Open `res://scenes/levels/sandbox/test_movement_3d.tscn` in the Godot editor. Throw a chunk at an enemy and confirm: (1) chunk visibly attaches and moves with the enemy, (2) recall input is blocked while chunk is stuck, (3) after the enemy is absorbed the chunk detaches and can be recalled, (4) all behavior is observable without debug overlays. Document the result in Validation Status and, if passing, advance Stage to COMPLETE and move ticket to `02_complete/`.
**Status:** Needs Attention
**Reason:** AC1–AC4 are fully evidenced by 126 primary assertions (TC-CSE-020..025, TC-CSE-030..032, TC-CSE-040..044, TC-CSE-060..062) and 185 adversarial assertions across 20 mutation categories, all with 0 failures. AC5 is a mandatory manual playtest criterion that has not yet been performed or documented. Ticket is held in INTEGRATION until a human completes and records that check.

---

## Artifact Paths

| Artifact | Path |
|---|---|
| Spec | `project_board/specs/chunk_sticks_to_enemy_spec.md` |
| Primary tests | `tests/chunk/test_chunk_sticks_to_enemy.gd` |
| Adversarial tests | `tests/chunk/test_chunk_sticks_to_enemy_adversarial.gd` |
| Ticket | `project_board/3_milestone_3_dual_mutation_fusion/in_progress/chunk_sticks_to_enemy.md` |
| EnemyInfection3D | `scripts/enemy/enemy_infection_3d.gd` |
| PlayerController3D | `scripts/player/player_controller_3d.gd` |
| Chunk scene | `scenes/chunk/chunk_3d.tscn` |
| Chunk script | `scripts/chunk/chunk_3d.gd` |
