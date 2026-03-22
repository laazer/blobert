Title:
Build room template system

Description:
Define room categories and author initial templates for each. Categories:
intro (1), combat (3+), mutation_tease (2), fusion_opportunity (1), cooldown (1), boss (1).
Rooms connect via standardized entry/exit door nodes so the layout system can chain them.

Acceptance Criteria:
- Each room is a self-contained .tscn with Entry and Exit Marker3D nodes
- At minimum: 1 intro, 2 combat, 1 mutation_tease, 1 boss room authored
- Rooms load and unload cleanly without memory leaks
- Entry/exit positions are consistent enough for seamless transitions

---

## Dependencies
- None (rooms are authored from scratch; no existing script is modified)

---

## Design Decisions (resolved — see CHECKPOINTS.md [RTS] entries)

| Decision | Resolved Value |
|---|---|
| Scene directory | `scenes/rooms/` |
| Standard room width | 30 units (boss: 40 units) |
| Entry Marker3D position | local (0, 1, 0) — left edge of room, 1m above floor |
| Exit Marker3D position | local (30, 1, 0) standard; (40, 1, 0) boss |
| Floor top surface Y | 0.0 (consistent with containment_hall_01 convention) |
| Nodes NOT in room scenes | Player3D, RespawnZone, InfectionInteractionHandler, GameUI |
| Nodes IN room scenes | Entry Marker3D, Exit Marker3D, floor geometry, WorldEnvironment, DirectionalLight3D, enemies (where appropriate) |
| Minimum room set | 5 rooms: 1 intro, 2 combat, 1 mutation_tease, 1 boss |
| File naming | `room_<category>_<variant>.tscn` e.g. `room_combat_01.tscn` |
| Root node name | PascalCase mirror of filename: `RoomCombat01` |
| Test directory | `tests/rooms/` |
| Enemy authoring | Instanced directly in .tscn (no runtime spawner script) |

---

## Execution Plan

### Task 1 — Spec Agent: Write room_template_system_spec.md

**Input:**
- This ticket
- CHECKPOINTS.md [RTS] entries
- `/Users/jacobbrandt/Library/Mobile Documents/com~apple~CloudDocs/Workspace/blobert_agent_context/agents/2_spec/containment_hall_01_spec.md` (geometry conventions reference)
- `scenes/levels/containment_hall_01/containment_hall_01.tscn` (floor geometry patterns)

**Output:**
`/Users/jacobbrandt/Library/Mobile Documents/com~apple~CloudDocs/Workspace/blobert_agent_context/agents/2_spec/room_template_system_spec.md`

Spec must define:
- RTS-STRUCT: Scene file contract for all 5 rooms (path, root node name, node types)
- RTS-ENTRY: Entry Marker3D position contract (exact local coords, tolerance ±0.01)
- RTS-EXIT: Exit Marker3D position contract (exact local coords, tolerance ±0.01)
- RTS-GEO: Floor geometry contract per room category (StaticBody3D, BoxShape3D size, CollisionShape3D offset)
- RTS-ENC: Enemy placement contract per room category (which rooms have enemies, positions, scene path)
- RTS-LOAD: Scene loadability contract (ResourceLoader.load() returns non-null PackedScene; instantiate and free without error)
- RTS-NO-PLAYER: Contract that Player3D, RespawnZone, InfectionInteractionHandler, GameUI are NOT present
- RTS-ENV: WorldEnvironment + DirectionalLight3D present in each room (for standalone preview)

Geometry constraints (spec must document exact values):

**room_intro_01.tscn** (`RoomIntro01`):
- Floor: StaticBody3D `IntroFloor`, size (30, 1, 10), node position (15, 0, 0), CollisionShape3D/MeshInstance3D offset (0, -0.5, 0)
- No enemies
- Entry (0, 1, 0), Exit (30, 1, 0)

**room_combat_01.tscn** (`RoomCombat01`):
- Floor: StaticBody3D `CombatFloor`, size (30, 1, 10), node position (15, 0, 0), offset (0, -0.5, 0)
- One enemy: `EnemyCombat01` at (15, 0.5, 0) — standing on floor (floor top Y=0, enemy origin Y=0.5)
- Entry (0, 1, 0), Exit (30, 1, 0)

**room_combat_02.tscn** (`RoomCombat02`):
- Floor: StaticBody3D `CombatFloor`, size (30, 1, 10), node position (15, 0, 0), offset (0, -0.5, 0)
- One elevated platform: StaticBody3D `CombatPlatform`, size (4, 1, 6), node position (15, 0, 0), CollisionShape3D/MeshInstance3D offset (0, 0.3, 0) — top at Y=0.8
- One enemy: `EnemyCombat01` at (15, 1.3, 0) — on platform (top Y=0.8, enemy origin Y=1.3)
- Entry (0, 1, 0), Exit (30, 1, 0)

**room_mutation_tease_01.tscn** (`RoomMutationTease01`):
- Floor: StaticBody3D `MutationTeaseFloor`, size (30, 1, 10), node position (15, 0, 0), offset (0, -0.5, 0)
- One elevated platform: StaticBody3D `MutationTeasePlatform`, size (4, 1, 6), node position (15, 0, 0), CollisionShape3D/MeshInstance3D offset (0, 0.3, 0) — top at Y=0.8
- One enemy: `EnemyMutationTease` at (15, 1.3, 0) — on platform
- Entry (0, 1, 0), Exit (30, 1, 0)

**room_boss_01.tscn** (`RoomBoss01`):
- Floor: StaticBody3D `BossFloor`, size (40, 1, 10), node position (20, 0, 0), offset (0, -0.5, 0)
- One boss enemy: `EnemyBoss` at (20, 0.5, 0) — standing on floor, scale Transform3D(1.75, 0, 0, 0, 1.75, 0, 0, 0, 1.75, 20, 0.5, 0) (matches EnemyMiniBoss in containment_hall_01)
- Room width: 40 units; Exit Marker3D at (40, 1, 0)
- Entry (0, 1, 0), Exit (40, 1, 0)

**collision_mask:** All StaticBody3D nodes use `collision_mask = 3` (consistent with containment_hall_01 convention).

**Spec must also define test IDs** for each requirement using prefix `RTS-`:
- RTS-LOAD-1 through RTS-LOAD-5: scene load/instantiate/free for each of the 5 rooms
- RTS-STRUCT-1 through RTS-STRUCT-5: root node name and type per room
- RTS-ENTRY-1 through RTS-ENTRY-5: Entry Marker3D local position per room
- RTS-EXIT-1 through RTS-EXIT-5: Exit Marker3D local position per room
- RTS-GEO-1 through RTS-GEO-5: floor geometry per room (type, BoxShape3D size, top surface Y in [-0.1, 0.1])
- RTS-ENC-1: intro room has NO enemy children (node count guard)
- RTS-ENC-2 through RTS-ENC-5: combat/tease/boss rooms have the correct enemy count and scene path
- RTS-NO-PLAYER-1: none of the 5 rooms contain a node with name "Player3D", "RespawnZone", "InfectionInteractionHandler", or "InfectionUI"
- RTS-ADV-1 through RTS-ADV-10: adversarial tests (Entry/Exit names exact match, room width between Entry.x and Exit.x, marker Y > floor top, collision_mask == 3, no player node by class check)

**Success criteria:** Spec is deterministic; all geometry values are exact or have stated tolerances; no open questions.

---

### Task 2 — Test Designer Agent: Write test suites for room template system

**Input:**
- room_template_system_spec.md (from Task 1)
- This ticket
- Pattern reference: `tests/levels/test_containment_hall_01.gd`, `tests/levels/test_mini_boss_encounter.gd`

**Output (two files):**
- `tests/rooms/test_room_templates.gd` — primary suite covering RTS-LOAD-*, RTS-STRUCT-*, RTS-ENTRY-*, RTS-EXIT-*, RTS-GEO-*, RTS-ENC-*, RTS-NO-PLAYER-*
- `tests/rooms/test_room_templates_adversarial.gd` — adversarial suite covering RTS-ADV-*

**Constraints:**
- All tests headless-safe: `ResourceLoader.load()` + `PackedScene.instantiate()` + node property reads + `root.free()`; no physics tick, no await
- Pattern: `extends Object`, no `class_name`, `func run_all() -> int`
- Red phase: when scene files do not yet exist, `ResourceLoader.load()` returns null; tests report FAIL with clear message
- Green phase: all assertions pass after scene files are authored in Task 3
- Test IDs assigned per spec RTS-* prefix

**Success criteria:** Test runner `timeout 300 godot -s tests/run_tests.gd` discovers and runs both new files; red phase produces explicit FAIL (not crash) for all 5 missing scenes.

---

### Task 3 — Engine Integration Agent (Generalist): Author the 5 room .tscn files

**Input:**
- room_template_system_spec.md (from Task 1)
- test suites from Task 2 (defines pass criteria)
- `scenes/levels/containment_hall_01/containment_hall_01.tscn` (geometry pattern reference)
- `scenes/enemy/enemy_infection_3d.tscn` (enemy scene path — all enemies use this)

**Output (5 new files, directory `scenes/rooms/` must be created):**
- `scenes/rooms/room_intro_01.tscn`
- `scenes/rooms/room_combat_01.tscn`
- `scenes/rooms/room_combat_02.tscn`
- `scenes/rooms/room_mutation_tease_01.tscn`
- `scenes/rooms/room_boss_01.tscn`

**Constraints:**
- No existing files modified
- Each scene file is a valid Godot 4 `.tscn` (format=3 header, correct uid, correct ext_resource references)
- UIDs must be unique and not collide with existing scene UIDs in the project
- All geometry values match the spec exactly
- Enemy instances use `res://scenes/enemy/enemy_infection_3d.tscn`
- `physics_interpolation_mode = 1` on all enemy instances (consistent with containment_hall_01)
- collision_mask = 3 on all StaticBody3D nodes

**Success criteria:** All RTS-* tests pass (green phase) with `timeout 300 godot -s tests/run_tests.gd`; all pre-existing tests continue to pass.

---

### Task 4 — Static QA Agent: Run full test suite and confirm no regressions

**Input:**
- All files from Tasks 1–3
- `tests/run_tests.gd`

**Actions:**
- Run `timeout 300 godot -s tests/run_tests.gd`
- Confirm all RTS-* tests pass
- Confirm all pre-existing test IDs continue to pass
- Report any failures with exact test ID and failure message

**Success criteria:** Exit code 0 from test runner. Zero regressions.

---

## Test ID Reference (RTS-* prefix)

| ID | Description |
|---|---|
| RTS-LOAD-1..5 | Each room scene loads as non-null PackedScene, instantiates, frees |
| RTS-STRUCT-1..5 | Root node is Node3D with correct name per room |
| RTS-ENTRY-1..5 | Entry Marker3D exists as direct child, local position (0, 1, 0) ±0.01 |
| RTS-EXIT-1..5 | Exit Marker3D exists as direct child, at (30,1,0) or (40,1,0) ±0.01 |
| RTS-GEO-1..5 | Floor StaticBody3D exists with BoxShape3D; top surface Y in [-0.1, 0.1] |
| RTS-ENC-1 | Intro room has no enemy-type children |
| RTS-ENC-2..5 | Combat/tease/boss rooms have exactly 1 enemy with correct scene path |
| RTS-NO-PLAYER-1 | None of 5 rooms contain Player3D, RespawnZone, InfectionInteractionHandler, or InfectionUI |
| RTS-ADV-1..10 | Adversarial: marker names exact, width check (Exit.x - Entry.x > 0), Entry.y > 0, Exit.y > 0, col_mask == 3, etc. |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
INTEGRATION

## Revision
6

## Last Updated By
Engine Integration Agent

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: PARTIAL — all RTS-* tests pass except RTS-ADV-16 (4 failures) due to test design defect (EnemyVisual child node inside enemy_infection_3d.tscn contains "Enemy" substring, causing recursive count to return 2 instead of expected 1). All primary RTS-LOAD-*, RTS-STRUCT-*, RTS-ENTRY-*, RTS-EXIT-*, RTS-GEO-*, RTS-ENC-*, RTS-NO-PLAYER-*, RTS-ADV-1 through RTS-ADV-15, RTS-ADV-17 through RTS-ADV-24 pass. Pre-existing failures (RSM-SIGNAL-*, SDR-*, ADV-RSM-*, ADV-SDR-*) are unrelated to this ticket.
- Static QA: Not Run
- Integration: Pending human visual check

## Blocking Issues
None — rooms need human visual check. RTS-ADV-16 test defect should be resolved by Acceptance Criteria Gatekeeper Agent.

## Escalation Notes
- RTS-ADV-16 test counts "Enemy" substring recursively across entire scene tree. `enemy_infection_3d.tscn` contains a child node named `EnemyVisual`, which causes the count to be 2 per room. Fix options: (1) update RTS-ADV-16 to count only direct children of room root, or (2) rename EnemyVisual in enemy_infection_3d.tscn. Both require agent outside Engine Integration scope. CHECKPOINT logged.
- UIDs used: uid://room_intro_01, uid://room_combat_01, uid://room_combat_02, uid://room_mutation_tease_01, uid://room_boss_01. No collision with existing project UIDs verified.

---

# NEXT ACTION

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Required Input Schema
```json
{
  "scene_files": [
    "scenes/rooms/room_intro_01.tscn",
    "scenes/rooms/room_combat_01.tscn",
    "scenes/rooms/room_combat_02.tscn",
    "scenes/rooms/room_mutation_tease_01.tscn",
    "scenes/rooms/room_boss_01.tscn"
  ],
  "test_results": "All RTS-* pass except RTS-ADV-16 (4 failures, test design defect — see CHECKPOINTS.md)",
  "open_issue": "RTS-ADV-16 test design defect: EnemyVisual child counts as 'Enemy' in recursive substring search"
}
```

## Status
Proceed

## Reason
Engine Integration Agent authored all 5 room .tscn files in scenes/rooms/. All primary RTS-* and adversarial tests pass except RTS-ADV-16 which has a test design defect — the recursive "Enemy" substring count includes EnemyVisual inside the instanced enemy sub-scene. Rooms require human visual check. Acceptance Criteria Gatekeeper Agent must decide whether to fix the test or accept the rooms as correct per the spec.
