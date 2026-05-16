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
COMPLETE

## Revision
6

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: 48 of 49 PRS-*/ADV-PRS-* tests pass. The single failing test, PRS-GEO-2, is a spec/test design defect — not an AC violation — as ruled below. All remaining 48 tests provide explicit structural, wiring, position, script-path, and geometry coverage of each AC.
- PRS-GEO-2 ruling: The ticket AC states "Root is Node3D with no pre-built geometry nodes." The .tscn file contains zero geometry definitions (no StaticBody3D, MeshInstance3D, CSGBox3D, CSGCombiner3D, GridMap, or sub-resources of any kind). The test implementation uses a recursive subtree walk that descends into the player_3d.tscn packed scene instance, finding the player's internal SlimeVisual/MeshInstance3D. This MeshInstance3D is the player's mesh renderer, is not authored in procedural_run.tscn, and is not level geometry by any reasonable definition. The AC text does not say "recursively including sub-scene internals." The spec text PRS-SCENE-6 over-specifies by writing "anywhere in the subtree" — this is a spec defect that conflicts with PRS-NFR-4 (player_3d.tscn must not be modified), making the test impossible to satisfy without violating another spec requirement. The AC is met; the test is defective. The test file is noted as having a known design conflict for future remediation.
- Static QA: Not required for a pure .tscn scene file with no authored GDScript. The authored scripts (run_scene_assembler.gd, death_restart_coordinator.gd, infection_interaction_handler.gd) were validated by their own tickets.
- Integration (PRS-RUNTIME-1): Not headlessly automatable. Evidence by code inspection: room_chain_generator.gd line 23 contains an unconditional `print("[RoomChainGenerator] seed: %d" % seed)` call. This fires on every call to generate(), which is called unconditionally from RunSceneAssembler._on_run_started(). The log line will appear on every run. Human verification required to confirm in-editor output.
- Integration (PRS-RUNTIME-2): [INTG-ONLY] — requires a live SceneTree. Cannot be headlessly automated. Structural evidence is strong: RunSceneAssembler._on_run_started() iterates SEQUENCE (5 entries), loads each room PackedScene from POOL, instantiates it, and calls level_root.add_child(room). All 5 room .tscn files confirmed present (room_template_system ticket is COMPLETE). Human verification required to confirm child count in-editor.
- Manual verification items explicitly escalated to Human: (a) seed log line in Output panel, (b) 5-room child count after _ready(), (c) absence of push_error during a clean run.

## Blocking Issues
None. PRS-GEO-2 is ruled a spec/test design defect, not an unmet acceptance criterion. All ticket ACs are covered by explicit test evidence or documented manual verification requirements.

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
- PRS-GEO-2 defect noted for future remediation: the test should limit its recursive walk to direct children of root, or explicitly exclude sub-scene-internal nodes, to be consistent with the AC text and PRS-NFR-4.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "manual_verification_items": [
    "Open scenes/levels/procedural_run.tscn in the Godot editor and run the scene. Confirm '[RoomChainGenerator] seed: <integer>' appears in the Output panel (AC: seed log line).",
    "After running, confirm ProceduralRun node in the Remote tree has at least 5 room children beyond the initial 5 (AC: 5-room sequence loads without errors).",
    "Confirm no push_error appears in the Output panel during a clean run (AC: no errors on run)."
  ]
}
```

## Status
Proceed

## Reason
All acceptance criteria have explicit test or integration coverage. 48 of 49 PRS-*/ADV-PRS-* tests pass, covering all structural, wiring, position, script-path, and geometry ACs. The single failing test (PRS-GEO-2) is ruled a spec/test design defect: it recurses into player_3d.tscn sub-scene internals and finds the player's mesh renderer, which is not level geometry and is not authored in procedural_run.tscn. Satisfying PRS-GEO-2 as written would require modifying player_3d.tscn, which is prohibited by PRS-NFR-4 — the test is irreconcilably defective and does not reflect an unmet AC. Two runtime ACs (seed log line; 5-room sequence on run) are inherently manual/integration-only items; strong code-inspection evidence supports both, and they are explicitly escalated for human verification. Ticket is COMPLETE pending human manual verification of the three items listed above.
