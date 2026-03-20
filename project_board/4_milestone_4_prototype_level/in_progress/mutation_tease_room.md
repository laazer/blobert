# Mutation tease room

**Epic:** Milestone 4 – Prototype Level
**Status:** In Progress

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | INTEGRATION |
| Revision | 5 |
| Last Updated By | Engine Integration Agent |
| Next Responsible Agent | Acceptance Criteria Gatekeeper Agent |
| Validation Status | All headless tests pass (T-63–T-72, ADV-MTR-01–ADV-MTR-06): 0 failures |
| Blocking Issues | None |

---

## Description

Design and implement a room that teases the first mutation: player can see or briefly experience the mutation before full acquisition so the loop is communicated.

## Acceptance criteria

- [ ] Room is part of Containment Hall 01 and reachable
- [ ] Tease is clear (e.g. locked door, preview enemy, or scripted moment)
- [ ] Connects to first real mutation acquisition in level flow
- [ ] No dead ends or softlocks
- [ ] Mutation tease room is human-playable in-editor: environment, tease object/NPC, and any UI prompts are visible and understandable without debug overlays

---

## Planning Output

### Context

The Mutation Tease Room zone is already built in `containment_hall_01.tscn` at X: -10→10 with:
- `MutationTeaseFloor` — StaticBody3D at X=0 (identity transform), BoxShape3D size (20, 1, 10), CollisionShape3D Y offset -0.5
- `MutationTeasePlatform` — StaticBody3D at X=0, BoxShape3D size (4, 1, 6), CollisionShape3D Y offset +0.3 (top surface world Y = 0.8)
- `EnemyMutationTease` — one instance of `enemy_infection_3d.tscn`, position Y=1.3 (above platform top surface Y=0.8)

The tease is communicated by placing the enemy on an elevated platform the player can see before engaging. There is no locked door or scripted moment.

This ticket is about **validating** the existing zone. Tests T-63 through T-72 are new. Next test ID after last complete suite is T-63.

### Spec IDs

All new spec requirement IDs use the prefix `MTR-` (Mutation Tease Room).

| Req ID | Category | Description |
|---|---|---|
| MTR-GEO-1 | Floor geometry | MutationTeaseFloor type, X position, BoxShape3D exact size |
| MTR-GEO-2 | Platform geometry | MutationTeasePlatform type, X position, BoxShape3D exact size, top surface Y elevated |
| MTR-ENC-1 | Enemy placement | EnemyMutationTease scene path, Y above platform top surface |
| MTR-FLOW-1 | Level flow placement | Zone precedes FusionFloor (right edge of tease floor <= left edge of fusion floor) |
| MTR-FLOW-2 | Zone distinctness | EnemyMutationTease name is distinct from EnemyFusionA, EnemyFusionB, EnemyMiniBoss |

### Test plan (T-63 through T-72)

All tests reside in `tests/levels/test_mutation_tease_room.gd`.
All tests are headless-safe: no physics tick, no await, no signal emission, no input simulation.
Tolerance for float comparisons follows established precedent (±1.0 m for zone center X, ±2.0 for platform X, exact for BoxShape3D dimensions).

| ID | Spec Req | Description |
|---|---|---|
| T-63 | MTR-GEO-1 | MutationTeaseFloor exists as StaticBody3D; position.x ≈ 0 ±1.0; BoxShape3D size (20, 1, 10) exact |
| T-64 | MTR-GEO-1 | MutationTeaseFloor top surface world Y in [-0.1, 0.1] (floor at corridor level) |
| T-65 | MTR-GEO-2 | MutationTeasePlatform exists as StaticBody3D; position.x ≈ 0 ±2.0; BoxShape3D size (4, 1, 6) exact |
| T-66 | MTR-GEO-2 | MutationTeasePlatform top surface world Y in [0.5, 1.5] (elevated above corridor floor) |
| T-67 | MTR-ENC-1 | EnemyMutationTease node exists; get_scene_file_path() contains "enemy_infection_3d.tscn" |
| T-68 | MTR-ENC-1 | EnemyMutationTease.position.y > MutationTeasePlatform.position.y (enemy above platform origin) |
| T-69 | MTR-FLOW-1 | MutationTeaseFloor right edge <= FusionFloor left edge (tease zone precedes fusion zone) |
| T-70 | MTR-FLOW-2 | EnemyMutationTease name is distinct from EnemyFusionA, EnemyFusionB, EnemyMiniBoss names |
| T-71 | MTR-GEO-2 | MutationTeasePlatform.position.y >= MutationTeaseFloor.position.y (platform not below floor) |
| T-72 | MTR-GEO-1 | MutationTeaseFloor collision_mask == 3 (covered by T-25 in test_containment_hall_01; this test documents FOR traceability via a NOTE comment with no new assertion — T-25 is the primary) |

Note: T-72 is a traceability stub only. The Test Designer must add a NOTE comment in the test file pointing to T-25 and emit no redundant assertion, consistent with the established pattern (T-43 NOTE, T-44 NOTE, etc.).

### Adversarial test plan (ADV-MTR-01 through ADV-MTR-06)

All adversarial tests reside in the same file `tests/levels/test_mutation_tease_room.gd`, using the naming convention `test_adv_mtr_NN_*`.

| ID | Adversarial scenario | Oracle |
|---|---|---|
| ADV-MTR-01 | MutationTeaseFloor CollisionShape3D extents are non-zero (size.x > 0, size.y > 0, size.z > 0) | Non-zero extents guard distinct from exact-value T-63 |
| ADV-MTR-02 | MutationTeasePlatform CollisionShape3D extents are non-zero | Non-zero extents guard distinct from exact-value T-65 |
| ADV-MTR-03 | EnemyMutationTease.position.y > 0 (enemy not embedded in floor at Y=0 or below) | Enemy is above ground plane |
| ADV-MTR-04 | All four enemy node names are pairwise distinct strings (EnemyMutationTease, EnemyFusionA, EnemyFusionB, EnemyMiniBoss) | Exact name equality assertions + pairwise distinctness, following ADV-MBA-08 pattern |
| ADV-MTR-05 | MutationTeaseFloor.position.x is within X: -12 to 12 (zone bounds check) | Catches floor accidentally placed outside tease zone |
| ADV-MTR-06 | MutationTeasePlatform top surface Y > MutationTeaseFloor top surface Y (platform is elevated relative to floor top, not just node origin) | Computed top-surface comparison using col.position.y + box.half_y for both nodes |

### INTEGRATION-only acceptance criteria (not automatable)

These are verified by human playthrough in the Godot editor only:

- The player can reach EnemyMutationTease from the entry spawn without obstacles blocking the path.
- The enemy on the platform is visible from the corridor approach (camera can see it).
- The zone connects forward to the FusionFloor (player can walk/jump from tease zone into fusion zone).
- No dead ends or softlocks: player can exit the tease zone in both directions.

### Execution plan for downstream agents

**Task 1 — Spec Agent** ✓ COMPLETE
- Input: This planning document, containment_hall_01_spec.md (for style and format reference), mini_boss_encounter_spec.md (for nearest analogous spec)
- Output: `agent_context/agents/2_spec/mutation_tease_room_spec.md`
- Content: Full spec with MTR-GEO-1, MTR-GEO-2, MTR-ENC-1, MTR-FLOW-1, MTR-FLOW-2; scene-confirmed values from the tscn; HEADLESS vs INTEGRATION classification per requirement; T-25 collision_mask overlap note; zone adjacency note (right edge of MutationTeaseFloor = 10.0; FusionFloor left edge = 10.0 — zones are adjacent, use <= for flow comparison)
- Success: Spec file exists, all AC are HEADLESS or INTEGRATION classified, no ambiguous assertions

**Task 2 — Test Designer Agent**
- Input: mutation_tease_room_spec.md
- Output: `tests/levels/test_mutation_tease_room.gd` (T-63 through T-72, ADV-MTR-01 through ADV-MTR-06)
- NFR: extends Object, no class_name, run_all() -> int, no physics tick, no await, scene freed before method returns, no duplicate test names with T-1 through T-62
- Success: File passes parse, run_tests.sh reports T-63 through T-72 all FAIL in red phase (scene nodes exist but assertions are structurally correct and would pass with proper values)

**Task 3 — Test Breaker Agent**
- Input: mutation_tease_room_spec.md, tests/levels/test_mutation_tease_room.gd
- Output: ADV-MTR-01 through ADV-MTR-06 added to test_mutation_tease_room.gd
- Success: All adversarial tests FAIL against a hypothetical minimal-but-wrong scene (e.g., floor at Y=5, enemy at Y=0, wrong node name)

**Task 4 — Engine Integration Agent**
- Input: mutation_tease_room_spec.md, tests/levels/test_mutation_tease_room.gd, existing containment_hall_01.tscn
- Scope: The zone nodes are already in the scene. This agent verifies that T-63 through T-72 and ADV-MTR-01 through ADV-MTR-06 all PASS against the existing scene. If any fail, author the minimal scene change needed to make them pass without altering any other zone.
- Success: run_tests.sh exits 0 with T-63 through T-72 and ADV-MTR-01 through ADV-MTR-06 all showing PASS

**Task 5 — AC Gatekeeper + Learning Agent**
- Input: run_tests.sh output, acceptance criteria from this ticket
- Output: Ticket stage set to COMPLETE, moved to 02_complete/; Learning Agent records key decisions in memory graph
- Success: All HEADLESS AC pass; INTEGRATION AC documented with explicit human-playthrough note; ticket closed

---

## NEXT ACTION

## Next Responsible Agent
Engine Integration Agent

## Required Input Schema
```json
{
  "spec_file": "agent_context/agents/2_spec/mutation_tease_room_spec.md",
  "output_path": "tests/levels/test_mutation_tease_room.gd",
  "prior_test_files": [
    "tests/levels/test_containment_hall_01.gd",
    "tests/levels/test_fusion_opportunity_room.gd",
    "tests/levels/test_light_skill_check.gd",
    "tests/levels/test_mini_boss_encounter.gd"
  ]
}
```

## Status
Proceed

## Reason
All headless tests T-63 through T-72 and ADV-MTR-01 through ADV-MTR-06 pass against the existing containment_hall_01.tscn with no scene modifications required. The scene geometry confirmed: MutationTeaseFloor at X=0 with BoxShape3D (20,1,10) and top surface Y=0.0; MutationTeasePlatform with BoxShape3D (4,1,6) and top surface Y=0.8; EnemyMutationTease at Y=1.3; right edge of tease floor (10.0) <= left edge of FusionFloor (10.0). INTEGRATION-only acceptance criteria (human playthrough) remain for the Acceptance Criteria Gatekeeper Agent to verify.
