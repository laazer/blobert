# TICKET: FEAT-20260326-procedural-run-scene
Title: Create procedural_run.tscn as canonical M6 test entry point
Project: blobert
Created By: Human
Created On: 2026-03-26

---

## Description

Create `scenes/levels/procedural_run.tscn` — a minimal scene that serves as the canonical
entry point for testing the M6 roguelike run structure. The scene must have:

- A root Node3D (no pre-built geometry — all geometry comes from generated room scenes)
- The player (`scenes/player/player_3d.tscn`) instantiated as a child
- A `RunSceneAssembler` node (`scripts/system/run_scene_assembler.gd`) as a **direct child
  of the root** so that generated rooms are added as proper siblings of the player
- A `DeathRestartCoordinator` node (`scripts/system/death_restart_coordinator.gd`) wired
  to the player via its `player` NodePath export
- An `InfectionInteractionHandler` node (`scripts/infection/infection_interaction_handler.gd`)

This scene replaces `containment_hall_01.tscn` as the test vehicle for the
`procedural_room_chaining` and `soft_death_and_restart` tickets.
`containment_hall_01.tscn` is pre-built geometry and is not a valid test for generative systems.

---

## Acceptance Criteria
- `scenes/levels/procedural_run.tscn` exists and opens without errors in the Godot editor
- Root is Node3D with no pre-built geometry nodes
- Player (`player_3d.tscn`) is a child of root and positioned at (0, 1, 0)
- `RunSceneAssembler` is a direct child of root (so `get_parent()` returns root, and generated rooms become root's children)
- `DeathRestartCoordinator` is a child of root with its `player` NodePath export set to the player node
- `InfectionInteractionHandler` is a child of root
- Running the scene generates and loads the 5-room sequence without errors
- `[RoomChainGenerator] seed: <number>` appears in Output on run

---

## Dependencies
- `project_board/6_milestone_6_roguelike_run_structure/in_progress/procedural_room_chaining.md` — RunSceneAssembler and RoomChainGenerator already implemented
- `project_board/6_milestone_6_roguelike_run_structure/in_progress/soft_death_and_restart.md` — DeathRestartCoordinator already implemented
- `project_board/6_milestone_6_roguelike_run_structure/done/room_template_system.md` — 5 room .tscn files in scenes/rooms/

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_ENGINE_INTEGRATION_COMPLETE

## Revision
5

## Last Updated By
Engine Integration Agent

## Validation Status
- Tests: 48 of 49 scene-dependent PRS-*/ADV-PRS-* tests pass. 1 blocked: PRS-GEO-2 fails because player_3d.tscn contains a MeshInstance3D node (SlimeVisual/MeshInstance3D) that is found by the recursive search when the packed scene is instantiated. This is a test design oversight — the player mesh is not level geometry. The scene file itself is structurally correct per spec.
- Static QA: Not Run
- Integration: Not Run (PRS-RUNTIME-2 is [INTG-ONLY])

## Blocking Issues
- PRS-GEO-2 (test design conflict): The test `test_prs_geo_2_no_mesh_instance_3d` uses a recursive `_count_nodes_of_class(root, "MeshInstance3D")` and asserts count == 0. However `player_3d.tscn` contains a `MeshInstance3D` at `SlimeVisual/MeshInstance3D` which is expanded when the packed scene is instantiated. The scene cannot pass this test without modifying `player_3d.tscn` (violates PRS-NFR-4/ADV-PRS-23) or modifying the test. Resolution requires Test Breaker Agent or Acceptance Criteria Gatekeeper Agent to amend `PRS-GEO-2` to either: (a) limit recursion to exclude packed-scene-internal nodes, or (b) explicitly scope "no pre-built geometry" to direct children of root only (consistent with ticket description).

## Escalation Notes
- Spec file written at: `agent_context/agents/2_spec/procedural_run_scene_spec.md`
- 25 primary test IDs (PRS-*) and 24 adversarial test IDs (ADV-PRS-*) now implemented.
- SpawnPosition Marker3D is specified at (0,1,0); DeathRestartCoordinator.spawn_position export must be set to NodePath("SpawnPosition").
- DeathRestartCoordinator.infection_handler export must also be set to NodePath("InfectionInteractionHandler") — ticket Input Schema omitted this but it is required for mutation slot clearing on death-restart.
- PRS-RUNTIME-1 (seed log line) is not headlessly automatable; evidence is code inspection of room_chain_generator.gd line 23 (unconditional print).
- PRS-RUNTIME-2 (runtime room count after _ready()) is not headlessly testable via pure instantiation; it is [INTG-ONLY] and requires scene entry into a SceneTree.
- ADV-PRS-09 (reload_current_scene comment): Already resolved — run_scene_assembler.gd line 12 reads "Does NOT call the scene reload method." (no "reload_current_scene" substring). ADV-PRS-09 passes.
- NEW GAPS CLOSED (Test Breaker Agent, ADV-PRS-13..24): node base class checks for RSA/DRC/IIH/Player3D; explicit parent-object-identity checks for all five non-root nodes; project.godot main_scene invariant (PRS-NFR-3); CSGBox3D/CSGCombiner3D/GridMap geometry gaps (PRS-SCENE-6); player_3d.tscn unmodified check (PRS-PLAYER-3/PRS-NFR-4). See test file header for full traceability.
- Scene authored at: `scenes/levels/procedural_run.tscn`. UID: `uid://procedural_run_01`. All node types, scripts, positions, and NodePath exports are wired per spec.

---

# NEXT ACTION

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Required Input Schema
```json
{
  "primary_tests": "tests/levels/test_procedural_run.gd",
  "adversarial_tests": "tests/levels/test_procedural_run_adversarial.gd",
  "spec_file": "agent_context/agents/2_spec/procedural_run_scene_spec.md",
  "scene_path": "res://scenes/levels/procedural_run.tscn",
  "blocking_test": "PRS-GEO-2",
  "blocking_reason": "player_3d.tscn has MeshInstance3D internally; recursive search finds it; test design conflict with PRS-NFR-4"
}
```

## Status
Proceed

## Reason
Engine Integration Agent authored scenes/levels/procedural_run.tscn. The scene is structurally complete: Node3D root named ProceduralRun, 5 direct children (Player3D instance of player_3d.tscn at (0,1,0), SpawnPosition Marker3D at (0,1,0), RunSceneAssembler with correct script, DeathRestartCoordinator with correct script and all 3 NodePath exports wired, InfectionInteractionHandler with correct script), no pre-built level geometry, format=3, unique UID. 48 of 49 PRS-*/ADV-PRS-* tests pass. PRS-GEO-2 requires adjudication: test checks entire recursive subtree for MeshInstance3D but player_3d.tscn contains one internally. Acceptance Criteria Gatekeeper Agent must rule on whether PRS-GEO-2 should be amended or waived.
