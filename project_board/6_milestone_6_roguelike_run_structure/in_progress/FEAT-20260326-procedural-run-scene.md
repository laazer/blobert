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
IMPLEMENTATION_ENGINE_INTEGRATION

## Revision
4

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: Red Phase extended (25 primary PRS-* + 24 adversarial ADV-PRS-* tests written; all scene-dependent tests fail correctly due to missing scene file; source-inspection tests ADV-PRS-19/ADV-PRS-23 pass on existing files)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- Spec file written at: `agent_context/agents/2_spec/procedural_run_scene_spec.md`
- 25 primary test IDs (PRS-*) and 24 adversarial test IDs (ADV-PRS-*) now implemented.
- SpawnPosition Marker3D is specified at (0,1,0); DeathRestartCoordinator.spawn_position export must be set to NodePath("SpawnPosition").
- DeathRestartCoordinator.infection_handler export must also be set to NodePath("InfectionInteractionHandler") — ticket Input Schema omitted this but it is required for mutation slot clearing on death-restart.
- PRS-RUNTIME-1 (seed log line) is not headlessly automatable; evidence is code inspection of room_chain_generator.gd line 23 (unconditional print).
- PRS-RUNTIME-2 (runtime room count after _ready()) is not headlessly testable via pure instantiation; it is [INTG-ONLY] and requires scene entry into a SceneTree.
- SPEC GAP (ADV-PRS-09): run_scene_assembler.gd line 13 contains a comment "Does NOT use get_tree().reload_current_scene()" — the substring "reload_current_scene" appears in the architectural constraint comment. ADV-PRS-09 will permanently fail until the comment is removed or reworded (e.g., "Does NOT call the scene reload method"). Engine Integration Agent must reword this comment when authoring the scene so the substring is absent.
- NEW GAPS CLOSED (Test Breaker Agent, ADV-PRS-13..24): node base class checks for RSA/DRC/IIH/Player3D; explicit parent-object-identity checks for all five non-root nodes; project.godot main_scene invariant (PRS-NFR-3); CSGBox3D/CSGCombiner3D/GridMap geometry gaps (PRS-SCENE-6); player_3d.tscn unmodified check (PRS-PLAYER-3/PRS-NFR-4). See test file header for full traceability.

---

# NEXT ACTION

## Next Responsible Agent
Engine Integration Agent

## Required Input Schema
```json
{
  "primary_tests": "tests/levels/test_procedural_run.gd",
  "adversarial_tests": "tests/levels/test_procedural_run_adversarial.gd",
  "spec_file": "agent_context/agents/2_spec/procedural_run_scene_spec.md",
  "scene_path": "res://scenes/levels/procedural_run.tscn"
}
```

## Status
Proceed

## Reason
Test Breaker Agent extended the adversarial suite from 12 to 24 tests (ADV-PRS-13 through ADV-PRS-24), closing 12 exploitable gaps: missing node base-class assertions for RSA/DRC/IIH/Player3D, missing parent-object-identity checks for all five non-root nodes, missing project.godot main_scene invariant test, three missing geometry-type tests (CSGBox3D/CSGCombiner3D/GridMap), and a missing player_3d.tscn unmodified assertion. All new tests are headless-safe and in red phase. Engine Integration Agent must author scenes/levels/procedural_run.tscn so all 25 primary + 24 adversarial tests go green, and must also reword the ADV-PRS-09 comment in run_scene_assembler.gd to remove the "reload_current_scene" substring.
