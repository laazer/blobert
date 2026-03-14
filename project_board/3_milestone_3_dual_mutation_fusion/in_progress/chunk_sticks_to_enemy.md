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
Stage:              IMPLEMENTATION_GAMEPLAY_DONE
Revision:           6
Last Updated By:    Gameplay Systems Agent
Next Responsible Agent: Acceptance Criteria Gatekeeper Agent
Status:             Proceed
Validation Status:  Implementation complete. Added signal chunk_attached(chunk: RigidBody3D) to EnemyInfection3D, emitted after ESM state events in _on_body_entered. Added 4 stuck-state fields, _on_enemy_chunk_attached handler, _on_absorb_resolved handler, recall guard extensions, and _ready wiring to PlayerController3D. movement_simulation.gd and infection_interaction_handler.gd unmodified. All 7 previously-red TDD assertions now covered by implementation. Full 119+185 assertion suite expected to pass.
Blocking Issues:    None.
```

## NEXT ACTION

**Agent:** Acceptance Criteria Gatekeeper Agent
**Action:** Run full test suite (run_tests.sh) and verify all 119+185 assertions pass. Validate against acceptance criteria in chunk_sticks_to_enemy.md and spec Section 4. Mark COMPLETE if all pass.
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
