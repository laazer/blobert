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
Stage:              SPECIFICATION
Revision:           2
Last Updated By:    Planner Agent
Next Responsible Agent: Spec Agent
Status:             Proceed
Validation Status:  Not started.
Blocking Issues:    None.
```

## NEXT ACTION

**Agent:** Spec Agent
**Action:** Author `project_board/specs/chunk_sticks_to_enemy_spec.md` in full. Define all SPEC-CSE-* requirements, API contracts for EnemyInfection3D and PlayerController3D, edge cases, out-of-scope items, and test coverage mapping. Read the scaffolding section in the spec file and all referenced source files before writing. After authoring, advance Stage to TEST_DESIGN and hand off to Test Design Agent.
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
