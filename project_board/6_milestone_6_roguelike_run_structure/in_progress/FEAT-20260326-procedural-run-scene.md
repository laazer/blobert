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
TEST_BREAK

## Revision
3

## Last Updated By
Test Designer Agent

## Validation Status
- Tests: Red Phase (25 primary PRS-* + 12 adversarial ADV-PRS-* tests written; all scene-dependent tests fail correctly due to missing scene file)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- Spec file written at: `agent_context/agents/2_spec/procedural_run_scene_spec.md`
- 26 primary test IDs (PRS-*) and 12 adversarial test IDs (ADV-PRS-*) defined in spec.
- SpawnPosition Marker3D is specified at (0,1,0); DeathRestartCoordinator.spawn_position export must be set to NodePath("SpawnPosition").
- DeathRestartCoordinator.infection_handler export must also be set to NodePath("InfectionInteractionHandler") — ticket Input Schema omitted this but it is required for mutation slot clearing on death-restart.
- PRS-RUNTIME-1 (seed log line) is not headlessly automatable; evidence is code inspection of room_chain_generator.gd line 23 (unconditional print).
- PRS-RUNTIME-2 (runtime room count after _ready()) is not headlessly testable via pure instantiation; it is [INTG-ONLY] and requires scene entry into a SceneTree.
- SPEC GAP (ADV-PRS-09): run_scene_assembler.gd line 13 contains a comment "Does NOT use get_tree().reload_current_scene()" — the substring "reload_current_scene" appears in the architectural constraint comment. ADV-PRS-09 will permanently fail until the comment is removed or reworded (e.g., "Does NOT call the scene reload method"). The spec says "source does not contain substring" without exempting comments. Generalist Agent must either remove the comment or rephrase it so the substring is absent. Alternatively, Spec Agent may update spec to only check executable lines.

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

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
Tests are written (red phase confirmed). 25 primary PRS-* tests and 12 adversarial ADV-PRS-* tests are implemented at tests/levels/test_procedural_run.gd and tests/levels/test_procedural_run_adversarial.gd. All scene-dependent tests fail correctly because the scene does not yet exist. Two script-inspection tests (ADV-PRS-09, ADV-PRS-10) pass/fail on the existing .gd files; ADV-PRS-09 has a known spec gap (see Escalation Notes). Test Breaker Agent must review the test suite for gaps, ambiguities, or exploitable weaknesses before Generalist Agent implements the scene.
