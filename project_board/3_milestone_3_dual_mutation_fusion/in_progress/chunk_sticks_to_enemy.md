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
Stage:              IMPLEMENTATION_GAMEPLAY
Revision:           5
Last Updated By:    Test Breaker Agent
Next Responsible Agent: Gameplay Systems Agent
Status:             Proceed
Validation Status:  Adversarial suite authored at tests/chunk/test_chunk_sticks_to_enemy_adversarial.gd. 185 assertions pass, 0 fail. Targets 20 mutation categories (MUT-1..MUT-20) plus rapid-fire, cross-slot, boundary, stress, determinism, and assumption-check scenarios. Pre-existing TDD red-phase failures (7 assertions across primary suite) unchanged — implementation not yet written. 4 CHECKPOINT entries logged to project_board/CHECKPOINTS.md.
Blocking Issues:    None.
```

## NEXT ACTION

**Agent:** Gameplay Systems Agent
**Action:** Implement the feature per spec `project_board/specs/chunk_sticks_to_enemy_spec.md` and API contracts in Section 5. Modify `scripts/enemy/enemy_infection_3d.gd` (add chunk_attached signal, emit in _on_body_entered) and `scripts/player/player_controller_3d.gd` (4 new fields, _ready wiring, _on_enemy_chunk_attached handler, _on_absorb_resolved handler, recall guard extensions). All 119+185 test assertions must pass after implementation (the 7 currently-failing TDD-red assertions will flip to green).
**Blocking Issues:** None.

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
