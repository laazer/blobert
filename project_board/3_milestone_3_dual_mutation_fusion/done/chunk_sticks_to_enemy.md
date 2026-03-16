# Chunk sticks to enemy on contact

**Epic:** Milestone 3 – Dual Mutation + Fusion
**Status:** In Progress

---

## Description

When a thrown chunk contacts an enemy, the chunk should stick to (attach to) the enemy rather than bouncing off or passing through. The chunk can only be recalled (reabsorbed by the player) after the enemy has been absorbed. This makes the infection loop feel more intentional — the player commits a chunk to an enemy and must complete the absorb to get it back.

## Acceptance criteria

- [x] Chunk sticks to enemy on contact (moves with enemy, no physics bounce)
- [x] Stuck chunk cannot be recalled until the enemy is absorbed
- [x] After enemy absorb, chunk detaches and becomes recallable normally
- [x] One-chunk and two-chunk flows both handled correctly (no state corruption)
- [x] Behavior is human-playable in-editor: chunk visibly attached to enemy, recall blocked until absorb, all clear without debug overlays

---

## WORKFLOW STATE

```
Stage:              COMPLETE
Revision:           8
Last Updated By:    Human
Next Responsible Agent: Human
Status:             Proceed
Validation Status:
  Tests (Primary):    126 assertions, 0 failures — TC-CSE-001..TC-CSE-072.
  Tests (Adversarial): 185 assertions, 0 failures — 20 mutation categories.
  Static QA:         All Critical and Warning GDScript issues resolved.
  Full Suite:        0 failures across entire test suite.
  Integration (Manual — PASS 2026-03-16):
    Human playtest confirmed: chunk visibly attaches and moves with enemy on contact,
    recall is blocked while stuck, chunk detaches and becomes recallable after absorb,
    no debug overlays. Note: initial build had chunk_attached only emitting on infect
    hit — fixed to emit on all hits (weaken + infect) before close.
Blocking Issues:    None.
```

## NEXT ACTION

**Agent:** None
**Action:** Ticket closed. All acceptance criteria confirmed.
**Status:** Complete

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
