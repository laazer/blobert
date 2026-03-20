# Light skill check

**Epic:** Milestone 4 – Prototype Level
**Status:** In Progress

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | IMPLEMENTATION_ENGINE |
| Revision | 4 |
| Last Updated By | Test Breaker Agent |
| Next Responsible Agent | Engine Integration Agent |
| Validation Status | Not started |
| Blocking Issues | None |

---

## Description

Add a light skill check (e.g. platforming, timing, or simple combat) that uses movement and optionally one mutation so the level has a moment of challenge without being a full boss.

The Light Skill Check zone is already built in `containment_hall_01.tscn` as the section at X: 35→55 with:
- `SkillCheckFloorBase` (StaticBody3D at X=45, CollisionShape Y=-4.5, BoxShape3D 20×1×10) — pit floor at top surface Y≈-4.0
- `SkillCheckPlatform1` (StaticBody3D at X=39, BoxShape3D 4×1×6, top surface Y≈0.0)
- `SkillCheckPlatform2` (StaticBody3D at X=44, BoxShape3D 4×1×6, top surface Y≈0.0) — gap from P1 ≈ 1.0 m
- `SkillCheckPlatform3` (StaticBody3D at X=51, BoxShape3D 8×1×6, top surface Y≈0.0) — gap from P2 ≈ 1.0 m
- `RespawnZone` (Area3D, CollisionShape offset (32.5, -5, 0), BoxShape3D 130×8×15) — catches falls below Y≈-1, respawns player at `SpawnPosition` (-25, 1, 0)

This ticket is about **validating** the existing zone, not building new content.

## Acceptance criteria

- [ ] AC-1: Skill check is passable with core movement (and optionally one mutation)
- [ ] AC-2: Failure has clear consequence (e.g. damage, retry) and no softlock
- [ ] AC-3: Difficulty is "light": completable in a few attempts by target audience
- [ ] AC-4: Placed appropriately in level flow (e.g. before or after fusion)
- [ ] AC-5: Skill check encounter is human-playable in-editor: layout, hazards, and any instructional UI are visible and understandable without debug overlays

---

## Execution Plan

### Task 1 — Spec: Light Skill Check spec document

**Agent:** Spec Agent
**Input:** This ticket; `scenes/levels/containment_hall_01/containment_hall_01.tscn` (already built); physics derivation values in `agent_context/agents/2_spec/containment_hall_01_spec.md` (max jump range ≈ 1.98 m, safe gap ≤ 1.5 m); `agent_context/agents/2_spec/fusion_opportunity_room_spec.md` (formatting reference); existing tests T-1 through T-42 for overlap avoidance.
**Output:** `/Users/jacobbrandt/Library/Mobile Documents/com~apple~CloudDocs/Workspace/blobert_agent_context/agents/2_spec/light_skill_check_spec.md`
**Spec must define:**
- `SKC-GEO-1`: SkillCheckFloorBase — node exists as StaticBody3D at X≈45, BoxShape3D size (20, 1, 10), collision_mask=3; top surface Y≈-4.0 (pit floor, not at corridor level)
- `SKC-GEO-2`: SkillCheckPlatform1 — node exists as StaticBody3D at X≈39, BoxShape3D size (4, 1, 6), top surface Y in [-0.1, 0.1]
- `SKC-GEO-3`: SkillCheckPlatform2 — node exists as StaticBody3D at X≈44, BoxShape3D size (4, 1, 6), top surface Y in [-0.1, 0.1]; gap from P1 right edge to P2 left edge > 0 and ≤ 1.5 m (within safe jump range)
- `SKC-GEO-4`: SkillCheckPlatform3 — node exists as StaticBody3D at X≈51, BoxShape3D size (8, 1, 6), top surface Y in [-0.1, 0.1]; gap from P2 right edge to P3 left edge > 0 and ≤ 1.5 m
- `SKC-RETRY-1`: RespawnZone — Area3D present; script path contains "respawn_zone.gd"; `spawn_point` NodePath is non-empty and resolves to `SpawnPosition`; CollisionShape3D BoxShape3D size X ≥ 20 (covers the zone width)
- `SKC-RETRY-2`: SpawnPosition — Marker3D present; position.y ≥ 0 (not in the pit); position.x < 35 (before the skill check zone, ensuring retry starts at the zone entrance, not mid-zone)
- `SKC-PLACE-1`: Zone X range — SkillCheckFloorBase X origin in [40, 50]; SkillCheckPlatform1 X < SkillCheckPlatform2 X < SkillCheckPlatform3 X (platforms are ordered left-to-right)
- `SKC-PLACE-2`: Zone placement in level flow — SkillCheckPlatform1 X > FusionPlatformB X (skill check comes after fusion zone); SkillCheckPlatform3 X < MiniBossFloor X origin (skill check comes before mini-boss zone)
- `SKC-FLOW-1` (INTEGRATION only): Player can traverse all three platforms in sequence without mutation; falling triggers RespawnZone and player reappears at SpawnPosition without softlock
**Spec must classify each AC as [HEADLESS] or [INTEGRATION].**
**Note:** collision_mask == 3 for all StaticBody3D nodes is already covered by T-25 — spec must note this overlap and mark as "satisfied by T-25."
**Dependencies:** None (scene already exists)
**Success Criteria:** Spec document exists at the output path; all requirements are traceable to the ACs above; headless vs. INTEGRATION classification is explicit for every AC.
**Status:** COMPLETE — spec at `/Users/jacobbrandt/Library/Mobile Documents/com~apple~CloudDocs/Workspace/blobert_agent_context/agents/2_spec/light_skill_check_spec.md`

---

### Task 2 — Test Designer: Light Skill Check validation tests

**Agent:** Test Designer Agent
**Input:** `light_skill_check_spec.md` (Task 1 output); `tests/levels/test_containment_hall_01.gd` (T-1 through T-30 — must not duplicate); `tests/levels/test_fusion_opportunity_room.gd` (T-31 through T-42 — must not duplicate); `tests/run_tests.gd` (auto-discovers all `test_*.gd` under `tests/`)
**Output:** `/Users/jacobbrandt/workspace/blobert/tests/levels/test_light_skill_check.gd`
**Tests to write (red-phase, headless-safe), starting at T-43:**
- `T-43`: SkillCheckFloorBase — exists as StaticBody3D; position.x ≈ 45 ±1.0; BoxShape3D size (20, 1, 10) exact; collision_mask == 3 already covered by T-25 (add a NOTE comment, do not duplicate)
- `T-44`: SkillCheckPlatform1 — exists as StaticBody3D; position.x ≈ 39 ±0.5; BoxShape3D size (4, 1, 6) exact; top surface Y (node.y + col.y + box.half_y) in [-0.1, 0.1]
- `T-45`: SkillCheckPlatform2 — exists as StaticBody3D; position.x ≈ 44 ±0.5; BoxShape3D size (4, 1, 6) exact; top surface Y in [-0.1, 0.1]
- `T-46`: SkillCheckPlatform3 — exists as StaticBody3D; position.x ≈ 51 ±0.5; BoxShape3D size (8, 1, 6) exact; top surface Y in [-0.1, 0.1]
- `T-47`: P1→P2 gap reachability — gap (P2 left edge − P1 right edge) > 0 and ≤ 1.5 m; approx 1.0 m ±0.3
- `T-48`: P2→P3 gap reachability — gap (P3 left edge − P2 right edge) > 0 and ≤ 1.5 m; approx 1.0 m ±0.3
- `T-49`: RespawnZone — node exists as Area3D; script path contains "respawn_zone.gd"; `spawn_point` NodePath is non-empty
- `T-50`: SpawnPosition — node exists as Marker3D; position.x < 35 (before skill check zone); position.y ≥ 0 (not in pit)
- `T-51`: Zone ordering — SkillCheckPlatform1.position.x < SkillCheckPlatform2.position.x < SkillCheckPlatform3.position.x
- `T-52`: Zone placement in level flow — SkillCheckPlatform1.position.x > FusionPlatformB.position.x; SkillCheckPlatform3.position.x < MiniBossFloor.position.x
**File structure:** `extends Object`; same helper pattern as `test_fusion_opportunity_room.gd` (`_pass_test`, `_fail_test`, `_assert_true`, `_assert_eq_float`, `_load_level_scene`, `run_all() -> int`); no `class_name`; scene cleanup before method returns.
**Note on T-25 overlap:** Tests must NOT re-assert collision_mask for SkillCheckFloorBase, SkillCheckPlatform1–3; include a comment in each test noting "collision_mask covered by T-25."
**Dependencies:** Task 1
**Success Criteria:** All T-43 through T-52 fail (red phase) if scene nodes are absent; `run_tests.sh` discovers the file automatically; no test name duplicates any T-1 through T-42 name.

---

### Task 3 — Test Breaker: Adversarial extension

**Agent:** Test Breaker Agent
**Input:** `test_light_skill_check.gd` (Task 2 output); `light_skill_check_spec.md` (Task 1 output)
**Output:** `/Users/jacobbrandt/workspace/blobert/tests/levels/test_light_skill_check_adversarial.gd`
**Adversarial cases to cover (each a distinct named failure mode; no duplicates of T-43–T-52):**
- Platform top surface at corridor level: all three platforms top surface Y in [-0.1, 0.1] — if any platform is accidentally elevated (e.g. Y=1.5), a player would get stuck under it
- SkillCheckFloorBase top surface is below corridor level: assert SkillCheckFloorBase top surface Y < -1.0 (confirms it is a pit floor, not at player level)
- RespawnZone CollisionShape3D covers the pit: assert BoxShape3D size.x ≥ 20 (wide enough to catch any fall within the zone); size.y ≥ 6 (deep enough to catch falls from corridor level to pit floor)
- RespawnZone CollisionShape3D Y center < 0: assert the CollisionShape3D local Y offset is negative (zone is below corridor level, not above it)
- SpawnPosition is not inside the pit: assert SpawnPosition.position.y ≥ 0 AND SpawnPosition.position.y ≤ 3 (player respawns at corridor height, not in the pit and not floating)
- Platform3 is wider than Platform1 and Platform2: assert SkillCheckPlatform3 BoxShape3D size.x > SkillCheckPlatform1 BoxShape3D size.x (P3 is the landing pad — it must be wider, giving the player a larger safe zone)
- No platform has size.x == 0 or size.z == 0: assert all three platforms have non-zero box extents in X and Z (catches default zero-size shape assignment)
- Platform X ordering is strictly increasing with minimum spacing: assert P2.x − P1.x ≥ 3 m and P3.x − P2.x ≥ 3 m (platforms are not bunched together, ensuring the gaps are physically meaningful)
**Dependencies:** Task 2
**Success Criteria:** Adversarial file is discovered by `run_tests.sh`; each adversarial test has a distinct name using `ADV-SKC-` prefix; no test duplicates T-43–T-52 assertions.

---

### Task 4 — Engine Integration: Run tests, fix any failures

**Agent:** Engine Integration Agent
**Input:** `test_light_skill_check.gd` (Task 2 output); `test_light_skill_check_adversarial.gd` (Task 3 output); `containment_hall_01.tscn` (existing scene); `run_tests.sh`
**Output:** All T-43 through T-52 and all ADV-SKC-* tests passing; no regressions in T-1 through T-42; a commit with message "test: light skill check validation suite T-43–T-52 + adversarial passing"
**Actions:**
1. Run `run_tests.sh` — record output.
2. If any T-43 through T-52 or ADV-SKC-* test fails, diagnose: failure is either a test bug or a scene mismatch. Scene modifications to fix failures must not alter the skill check zone's fundamental design (platforms at X≈39, 44, 51; 1 m gaps; RespawnZone present).
3. If any T-1 through T-42 regression is introduced, diagnose and resolve before proceeding.
4. Commit all passing test files and any scene corrections.
**Dependencies:** Tasks 2, 3
**Success Criteria:** `run_tests.sh` exits with 0 failures; output confirms T-43 through T-52 PASS and all ADV-SKC-* PASS; prior tests T-1 through T-42 remain passing.

---

### Task 5 — AC Gatekeeper: Review

**Agent:** Acceptance Criteria Gatekeeper Agent
**Input:** Passing test output from Task 4; `light_skill_check_spec.md`; this ticket's ACs
**Output:** Updated ticket with Validation Status populated per AC; Blocking Issues set if any AC is unverifiable by automated tests; Next Responsible Agent set to Human for AC-5 manual verification
**Actions:**
1. Map each passing test (T-43–T-52, ADV-SKC-*) to its AC coverage.
2. Confirm AC-1 (passable with core movement) is structurally covered by T-47, T-48 (gap ≤ 1.5 m = within jump range).
3. Confirm AC-2 (failure has consequence, no softlock) is covered by T-49, T-50 (RespawnZone present, SpawnPosition at corridor level), and ADV-SKC-* respawn zone geometry tests.
4. Confirm AC-4 (appropriate placement) is covered by T-52 (after fusion, before mini-boss).
5. Flag AC-3 and AC-5 as INTEGRATION — require human playthrough; add to Blocking Issues.
**Dependencies:** Task 4
**Success Criteria:** Validation Status table populated; AC-1, AC-2, AC-4 marked as covered by automated tests; AC-3 and AC-5 marked as INTEGRATION pending human verification.

---

### Task 6 — Human: AC-3 and AC-5 manual verification

**Agent:** Human
**Input:** Full game run in Godot editor with `containment_hall_01.tscn` as main scene (or the scene set as `run/main_scene` in `project.godot`)
**Output:** AC-3 and AC-5 checked; ticket moved to `done/` folder
**Actions:**
1. Open the project in Godot editor. Run the scene.
2. Navigate to the skill check zone (X≈35–55 area, after the fusion platforms).
3. Attempt to cross all three platforms with core movement (no mutation needed).
4. Verify: crossing is possible in a few attempts (AC-3 — "light" difficulty).
5. Deliberately fall off a platform. Verify: player respawns at SpawnPosition (before the skill check), no softlock, retry is possible without restarting the scene.
6. Verify: the zone layout is visually clear in-editor — platforms are visible and distinguishable, the pit below is apparent, no debug overlays required to understand the hazard (AC-5).
7. Document results in Blocking Issues. If all satisfied: check AC-3 and AC-5, clear Blocking Issues, set Stage to COMPLETE, move ticket to `done/` folder.
**Dependencies:** Task 5 complete and all automated ACs passing
**Success Criteria:** AC-3 and AC-5 checkboxes checked; ticket in `done/` folder; Stage == COMPLETE.

---

## Risks and Assumptions

| Risk | Mitigation |
|---|---|
| Platform gaps (≈1.0 m) are within the player's comfortable jump range (safe gap ≤ 1.5 m per spec derivation), but the derivation assumes no Z-axis movement; if the player drifts in Z the landing pad may be narrower than expected | ADV-SKC-* test asserts platform Z depth (size.z ≥ 6) provides enough landing area; AC-5 human verification confirms feel |
| `RespawnZone.spawn_point` NodePath resolves to `SpawnPosition` which is at X=-25 — this is the level entrance, not a checkpoint just before the skill check. Failing sends the player back to the very start. | T-50 asserts SpawnPosition.x < 35 (documents the current behavior). AC-3 human test will assess whether full-level retry is "light." If it's too punishing, a future ticket can add a per-zone checkpoint. No change to the zone is required for this ticket. |
| T-25 (collision_mask == 3 for all StaticBody3D) already covers SkillCheckPlatform1–3 and SkillCheckFloorBase. New tests must not duplicate this assertion. | All new tests include a comment noting T-25 coverage; no new collision_mask assertions are emitted. |
| No existing containment_hall_01_spec.md section documents the skill check zone geometry (the existing spec covers the full scene structure but not the per-zone AC mapping for this ticket). | Spec Agent derives from scene file values, which are deterministic and confirmed in the Description above. |
| The scene's SkillCheckFloorBase has top surface at Y≈-4.0 (a pit floor), which differs from the corridor platforms at Y≈0.0. An agent reading the floor node name without checking geometry might assume it is the walkable floor of the skill check zone. | Spec explicitly documents SkillCheckFloorBase as the pit floor (SKC-GEO-1), not the walkable surface. ADV-SKC-* test asserts top surface Y < -1.0 to guard against misinterpretation. |

---

# NEXT ACTION

## Next Responsible Agent
Engine Integration Agent

## Required Input Schema
```json
{
  "ticket": "project_board/4_milestone_4_prototype_level/in_progress/light_skill_check.md",
  "spec": "agent_context/agents/2_spec/light_skill_check_spec.md",
  "scene": "scenes/levels/containment_hall_01/containment_hall_01.tscn",
  "primary_tests": "tests/levels/test_light_skill_check.gd",
  "adversarial_tests": "tests/levels/test_light_skill_check_adversarial.gd",
  "test_runner": "tests/run_tests.gd"
}
```

## Status
Proceed

## Reason
Adversarial test suite complete. All eight ADV-SKC-01 through ADV-SKC-08 tests written in `tests/levels/test_light_skill_check_adversarial.gd`. Each test targets a distinct failure mode not covered by the T-43–T-52 compound tests: pit-floor Y invariant (ADV-SKC-01), RespawnZone width (ADV-SKC-02), RespawnZone depth (ADV-SKC-03), RespawnZone Y-center sign (ADV-SKC-04), SpawnPosition corridor-height bounds (ADV-SKC-05), P3-wider-than-P1 landing pad invariant (ADV-SKC-06), non-zero platform extents on X and Z axes (ADV-SKC-07), and minimum center-to-center platform spacing (ADV-SKC-08). Engine Integration Agent should run `run_tests.sh`, confirm T-43–T-52 and all ADV-SKC-* pass, and commit.
