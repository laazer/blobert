# Spec: Chunk Sticks to Enemy on Contact

**Ticket:** chunk_sticks_to_enemy.md
**Epic:** Milestone 3 — Dual Mutation + Fusion
**Spec Status:** DRAFT — awaiting Spec Agent authoring

---

## Purpose

This file is the canonical specification destination for the `chunk_sticks_to_enemy` feature.

It must be authored by the **Spec Agent** as Task 1 of the execution plan.

The Spec Agent must define:

1. All numbered requirements (SPEC-CSE-*) covering the behavioral contract.
2. The precise API additions to `EnemyInfection3D` (new signals, new fields).
3. The precise additions to `PlayerController3D` (new fields, recall-guard logic, absorb signal handler).
4. Edge-case rules for: chunk already recalled before absorb, absorb fires with no chunk stuck, dual-chunk partial scenarios, enemy freed while chunk is stuck.
5. Out-of-scope items that must NOT be implemented to keep this ticket bounded.
6. Test coverage mapping: every requirement must map to at least one test ID.

---

## Scaffolding (to be replaced by Spec Agent)

### Known design decisions (from Planner checkpoints)

- Stuck state lives in `PlayerController3D` only — `MovementSimulation` is NOT modified.
- Recall is blocked by a controller guard, not a simulation flag.
- `PlayerController3D` connects to `InfectionInteractionHandler.absorb_resolved` signal.
- Two independent flag pairs: (`_chunk_stuck_on_enemy`, `_chunk_stuck_enemy`) and (`_chunk_2_stuck_on_enemy`, `_chunk_2_stuck_enemy`).
- Attachment mechanism: chunk `freeze = true` + reparented as child of enemy node.
- On absorb: chunk un-parented back to scene root, `freeze = false`, stuck flag cleared.
- `EnemyInfection3D` gains `chunk_attached(chunk: RigidBody3D)` signal.
- `PlayerController3D` connects to `chunk_attached` per enemy in the scene.

### Files the Spec Agent must read before writing this spec

- `/Users/jacobbrandt/workspace/blobert/scripts/player/player_controller_3d.gd`
- `/Users/jacobbrandt/workspace/blobert/scripts/enemy/enemy_infection_3d.gd`
- `/Users/jacobbrandt/workspace/blobert/scripts/infection/infection_interaction_handler.gd`
- `/Users/jacobbrandt/workspace/blobert/scripts/movement/movement_simulation.gd`
- `/Users/jacobbrandt/workspace/blobert/scenes/chunk/chunk_3d.tscn`
- `/Users/jacobbrandt/workspace/blobert/project_board/CHECKPOINTS.md` (chunk_sticks_to_enemy entries)
