# Containment Hall 01 layout

**Epic:** Milestone 4 – Prototype Level
**Status:** In Progress

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | INTEGRATION |
| Revision | 7 |
| Last Updated By | Acceptance Criteria Gatekeeper Agent |
| Next Responsible Agent | Human |
| Validation Status | AC-1 through AC-4 fully covered by automated tests (38 tests, all passing, run_tests.sh exits 0). AC-5 requires human manual verification — no automated test can confirm visual readability, enemy/geometry visibility, and absence of debug overlays in-editor. |
| Blocking Issues | AC-5 ("Level is human-playable in-editor: player, enemies, geometry, and key points of interest are visible and readable without debug overlays") has no automated or documented manual verification. A human must open `scenes/levels/containment_hall_01/containment_hall_01.tscn` in the Godot editor, press Play, and confirm: (a) player spawns visibly at the entry corridor, (b) all 4 enemies are visible and distinguishable in their assigned zones, (c) all zone floors and platforms are visible with no missing meshes, (d) no debug overlays or collision shape wireframes are visible during play, (e) the level exit trigger fires and logs "level_complete" when the player reaches the exit corridor. Evidence of this verification must be documented before Stage can advance to COMPLETE. |
| Escalation Notes | AC-1 evidence: T-1 (scene loads), T-2/T-3 (player spawn at -25,1,0), T-4/T-5/T-6 (exit Area3D exists and wired). AC-2 evidence: T-18 through T-23 (6 named zone floors present). AC-3 evidence: T-11/T-25 (BoxShape3D, collision_mask=3), T-17/T-28 (RespawnZone monitors falls), LeftWall and RightWall StaticBody3D nodes present. AC-4 evidence: T-2/T-3 (SpawnPosition Marker3D at -25,1,0), T-30 (LevelExit Area3D at X>=88). |

## NEXT ACTION

| Field | Value |
|---|---|
| Next Responsible Agent | Human |
| Status | BLOCKED on manual verification |
| Reason | Acceptance criteria AC-1 through AC-4 are fully satisfied by the 38-test automated suite (run_tests.sh exits 0, zero regressions). AC-5 — human-playable in-editor without debug overlays — cannot be satisfied by any automated test and has not yet been documented as completed by a human reviewer. The ticket cannot advance to COMPLETE until a human opens containment_hall_01.tscn in the Godot editor, plays through the level, and confirms all five sub-items listed in Blocking Issues above. Once confirmed, a human or delegated agent should update Validation Status with the verification evidence and set Stage to COMPLETE. |
| Required Input Schema | Human confirmation note documenting: editor version used, each of the 5 sub-items in Blocking Issues confirmed as pass or fail, and any visual defects found. |

---

## Description

Build Containment Hall 01 as the first playable level: layout, collision, spawn point, and exit so the level is traversable and supports the full loop.

## Acceptance criteria

- [ ] Level is loadable and playable from start to finish
- [ ] Layout includes space for mutation tease, fusion opportunity, and mini-boss
- [ ] Collision and boundaries prevent falling out of world
- [ ] Start and finish points are defined and functional
- [ ] Level is human-playable in-editor: player, enemies, geometry, and key points of interest are visible and readable without debug overlays

---

## Execution Plan

### Summary

Build `scenes/levels/containment_hall_01/containment_hall_01.tscn` as a new 3D side-scrolling level (2.5D: X/Y plane, Z=0). The level is a linear hall with four spatially distinct zones laid out left-to-right along the X axis. All geometry uses `StaticBody3D` + `CollisionShape3D` + `MeshInstance3D` (BoxMesh / CSGBox3D). No custom art is required. All gameplay systems (infection, mutation, fusion, HUD) are complete and wired via `InfectionInteractionHandler` + `GameUI` exactly as in `test_movement_3d.tscn`.

### Zone Layout (X axis, left → right)

| Zone | X range | Purpose |
|---|---|---|
| Entry corridor | -30 → -10 | Player spawn; flat floor, wall boundaries |
| Mutation Tease Room | -10 → 10 | 1 enemy on elevated platform; infect/absorb to earn first mutation |
| Fusion Opportunity Room | 10 → 35 | 2 enemies on separate platforms; earn both slots → fuse |
| Light Skill Check | 35 → 55 | Moving or gap platforms requiring jump/cling; no enemy required |
| Mini-Boss Encounter | 55 → 80 | 1 strengthened enemy; absorb to complete the loop |
| Exit corridor | 80 → 95 | Level exit trigger (Area3D) → print/log "level complete" |

### Task Table

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|---|---|---|---|---|---|---|
| 1 | Author full specification for Containment Hall 01 | Spec Agent | This ticket; zone layout table above; `test_movement_3d.tscn` as structural reference; `player_controller_3d.gd` for spawn and group contracts | `agent_context/agents/2_spec/containment_hall_01_spec.md` defining: scene file path, node tree, zone dimensions (X/Y/Z extents), platform heights, all StaticBody3D sizes and positions, spawn Marker3D position, exit Area3D position and size, respawn zone position and size, enemy instance count and positions per zone, InfectionInteractionHandler node name, GameUI node name, camera orthographic vs perspective setting, and any required script extensions | None | Spec document covers all zones; each AC maps to at least one spec section; no undefined coordinates remain | Zone widths are assumed; Spec Agent must confirm platform jump heights are reachable with default `jump_height = 120.0` in `player_controller_3d.gd`; skill-check gap width must be verified as crossable |
| 2 | Design test suite for scene structure and zone traversability | Test Design Agent | Spec from Task 1; `tests/scenes/levels/test_3d_scene.gd` as pattern reference | `tests/levels/test_containment_hall_01.gd` with tests for: scene loads without error, spawn Marker3D exists at expected position, exit Area3D exists and has CollisionShape3D, player group membership confirmed, InfectionInteractionHandler present, all StaticBody3D floor nodes have non-zero CollisionShape3D, respawn zone present with valid spawn_point NodePath | Task 1 | All tests are headless-safe (no physics tick required); red phase fails because scene does not yet exist | Level scene does not exist at test-design time — tests must use `ResourceLoader.load()` with null-check to confirm absence (red) then presence (green) |
| 3 | Build Containment Hall 01 scene geometry and wiring | Engine Integration Agent | Spec from Task 1; `test_movement_3d.tscn` as wiring reference; enemy scene at `scenes/enemy/enemy_infection_3d.tscn`; player scene at `scenes/player/player_3d.tscn`; `scripts/world/respawn_zone.gd` | New file `scenes/levels/containment_hall_01/containment_hall_01.tscn` containing: all zone floors and walls as StaticBody3D nodes, player spawn Marker3D, exit Area3D with script printing "level_complete", respawn Area3D with spawn_point wired, 4 enemy instances at specified zone positions, InfectionInteractionHandler node, GameUI instance (from `scenes/ui/game_ui.tscn`), WorldEnvironment + DirectionalLight3D, Player3D instance at spawn position | Task 1, Task 2 | All Task 2 tests pass green; scene opens in Godot editor without errors; player can walk from start to exit in a single play session with no fall-through geometry | Engine Integration Agent must not modify `test_movement_3d.tscn`; `project.godot` main scene remains pointing at `test_movement_3d.tscn` unless explicitly changed by spec |
| 4 | Adversarial test extension — collision and boundary validation | Test Break Agent | Task 2 test file; spec from Task 1; `test_movement_3d.tscn` as reference for collision layer values | Extended adversarial tests added to `tests/levels/test_containment_hall_01.gd`: verify floor collision_mask includes layer 1 (player layer), verify no floor StaticBody3D has zero-size shape, verify respawn zone shape is large enough to catch a falling player (Y extent >= 8 m), verify exit Area3D has monitoring = true | Task 3 | Adversarial tests fail before Task 3 (red phase: scene absent); pass after Task 3 (scene built correctly) | Collision layer values (layer 1 = player, layer 2 = enemy) assumed from `test_movement_3d.tscn` existing floor node |
| 5 | Set Containment Hall 01 as playable main scene for manual QA | Engine Integration Agent | Completed scene from Task 3; `project.godot` current value `run/main_scene` | `project.godot` updated so `run/main_scene = "res://scenes/levels/containment_hall_01/containment_hall_01.tscn"`; note in commit message that `test_movement_3d.tscn` remains valid and can be restored | Task 3, Task 4 (all tests green) | Running `godot` (or pressing Play in editor) loads Containment Hall 01 directly; all Task 2 + Task 4 tests still pass after `project.godot` change | Changing main scene affects `run_tests.sh` only if tests rely on the main scene being `test_movement_3d.tscn`; check test runner for hardcoded scene paths before changing |

### Key Architectural Decisions (resolved as checkpoints)

1. **New scene, not a modification of `test_movement_3d.tscn`.** The sandbox is preserved for unit testing. Containment Hall 01 is a new file at `scenes/levels/containment_hall_01/containment_hall_01.tscn`.
2. **Geometry via `StaticBody3D` + `BoxMesh` + `BoxShape3D`.** No CSGBox3D (runtime-only, cannot be baked). No custom art. Matches existing floor in `test_movement_3d.tscn`.
3. **Wiring mirrors `test_movement_3d.tscn` exactly.** `InfectionInteractionHandler` node as sibling of Player3D; GameUI instance; RespawnZone Area3D; SpawnPosition Marker3D. No new autoloads or scripts required.
4. **Four enemy instances total.** One in Mutation Tease Room, two in Fusion Opportunity Room, one in Mini-Boss Encounter. All use the existing `scenes/enemy/enemy_infection_3d.tscn`.
5. **Exit trigger is a simple Area3D** with an inline script that emits a signal or prints "level_complete" when a body in group "player" enters. No scene-transition system is required for this ticket.
