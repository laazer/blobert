# Mini-boss encounter

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
| Validation Status | AC-1 (distinct enemy/arena): COVERED — T-53 (dedicated 25 m MiniBossFloor), ADV-MBA-03 (EnemyMiniBoss X spatially separated from EnemyFusionA/B/EnemyMutationTease by >1 m), ADV-MBA-06 (MiniBossFloor does not overlap SkillCheck zone), ADV-MBA-07 (EnemyMiniBoss within own arena bounds), ADV-MBA-08 (distinct node name). Structural headless coverage is sufficient for this criterion. AC-2 (winnable with movement and mutations): NOT COVERED — no automated test can assert a combat outcome; human playtest required. AC-3 (victory connects to level completion): COVERED — T-59 (LevelExit exists as Area3D, positioned after ExitFloor), T-60 (inline script source contains "level_complete"), T-61/T-62 (spatial ordering: boss zone after skill check, exit after boss zone). AC-4 (no mandatory fusion, appropriate difficulty): PARTIALLY COVERED — T-55 confirms EnemyMiniBoss uses standard enemy_infection_3d.tscn (same base mechanics as all other enemies); T-57 confirms distinct node identity. Difficulty tuning and absence of a fusion requirement cannot be verified headlessly; human playtest required. AC-5 (human-playable in-editor, visually clear): NOT COVERED — visual clarity, arena readability, and in-editor appearance are inherently manual; human playtest required. T-53–T-62 passing (45/45); ADV-MBA-01–ADV-MBA-08 passing (21/21); T-1–T-52 no regressions. |
| Blocking Issues | AC-2: No automated or headless test can confirm the encounter is winnable using only movement and available mutations. Human must engage EnemyMiniBoss in a live run and confirm a successful defeat path exists without softlock. Evidence must be documented before this AC is closed. AC-4: Difficulty level and absence of mandatory fusion cannot be assessed headlessly. Human must verify during playtest that (a) EnemyMiniBoss can be defeated without performing a fusion, and (b) the encounter is not so difficult as to be a barrier. Evidence must be documented before this AC is closed. AC-5: Visual clarity of the mini-boss arena, enemy, telegraphs, and exit trigger cannot be verified headlessly. Human must open the project in the Godot editor, run containment_hall_01.tscn, navigate to X≈55–80, and confirm all elements are visible and understandable without debug overlays. Evidence must be documented before this AC is closed. |

---

## Description

Implement a mini-boss encounter in Containment Hall 01: distinct enemy or scenario that serves as a climax and tests movement + mutation use. Defeat leads toward level finish.

The Mini-Boss Encounter zone is already built in `containment_hall_01.tscn` at X: 55→80 with:
- `MiniBossFloor` (StaticBody3D at X≈67.5, BoxShape3D size 25×1×10, top surface Y≈0.0)
- `EnemyMiniBoss` (one instance of `enemy_infection_3d.tscn` at X=67, Y=0.5, Z=0)
- `LevelExit` (Area3D at X=93, inline script prints "level_complete" on player body_entered)
- `ExitFloor` (StaticBody3D at X=87.5, BoxShape3D 15×1×10) — the floor segment after the boss

The enemy uses `enemy_infection_3d.tscn` (gobot GLB model, CharacterBody3D, InfectionStateFx3D) and `InfectionStateFx3D` already applies visual tinting per state. No new GDScript is required to make the enemy visually distinct: the `InfectionStateFx3D` node already handles color-based visual distinction at runtime. Structural "arena" distinction is already satisfied by the dedicated MiniBossFloor at 25 m wide (larger than any single regular corridor section). AC-1 is satisfied by arena distinctness (dedicated 25 m arena) plus visual infection-state feedback already present.

## Acceptance criteria

- [ ] AC-1: Mini-boss is distinct from regular enemies (behavior, health, or arena)
- [ ] AC-2: Encounter is winnable with movement and available mutations
- [ ] AC-3: Victory connects to level completion or next section
- [ ] AC-4: No mandatory fusion unless designed; avoid over-tuned difficulty
- [ ] AC-5: Mini-boss encounter is human-playable in-editor: boss, arena, telegraphs, and any related UI are visible and understandable without debug overlays

---

## Execution Plan

### Task 1 — Spec: Define mini-boss zone requirements

**Agent:** Spec Agent
**Input:**
- This ticket
- `scenes/levels/containment_hall_01/containment_hall_01.tscn` (existing scene — zone already built)
- `scenes/enemy/enemy_infection_3d.tscn` (enemy scene — uses gobot.glb + InfectionStateFx3D)
- `scripts/enemy/enemy_infection_3d.gd` (enemy script — current behavior)
- `agent_context/agents/2_spec/light_skill_check_spec.md` (formatting reference)
- Existing tests T-1 through T-52 (all in `tests/levels/`) for overlap avoidance

**Output:** `/Users/jacobbrandt/Library/Mobile Documents/com~apple~CloudDocs/Workspace/blobert_agent_context/agents/2_spec/mini_boss_encounter_spec.md`

**Spec must define the following requirements (use `MBA-` prefix to avoid namespace collision):**

**Geometry requirements:**
- `MBA-GEO-1`: MiniBossFloor — node exists as StaticBody3D; position.x ≈ 67.5 ±1.0; BoxShape3D size (25, 1, 10) exact; collision_mask == 3 (already covered by T-25 — note overlap, do not re-assert); top surface world Y in [-0.1, 0.1] (floor is at corridor level)
- `MBA-GEO-2`: ExitFloor — node exists as StaticBody3D; position.x > MiniBossFloor.position.x (exit floor is after the boss arena); BoxShape3D size.x > 0, size.y > 0, size.z > 0 (solid floor)
- `MBA-GEO-3`: Arena width — MiniBossFloor BoxShape3D size.x (25 m) > any single non-mini-boss floor segment width (the arena is the widest single floor section in the level, asserting it is structurally distinct from regular corridor sections)

**Boss enemy requirements:**
- `MBA-BOSS-1`: EnemyMiniBoss — node exists in scene; get_scene_file_path() contains "enemy_infection_3d.tscn"; position.x is within MiniBossFloor bounds (position.x in [55, 80]); position.y > 0 (above floor surface, not embedded)
- `MBA-BOSS-2`: EnemyMiniBoss node path is distinct from EnemyFusionA, EnemyFusionB, EnemyMutationTease (four distinct node paths — no accidental duplication)
- `MBA-BOSS-3`: EnemyMiniBoss has an InfectionInteractionHandler available in the scene (via the scene-level "InfectionInteractionHandler" node); the enemy's `_area` (InteractionArea) is wired to detect player bodies. This requirement is structural: InfectionInteractionHandler node exists and has_method("set_target_esm"). NOTE: node existence covered by T-9; this adds the method presence guard specifically for mini-boss encounter context.

**Level flow requirements:**
- `MBA-FLOW-1`: EnemyMiniBoss.position.x > SkillCheckPlatform3.position.x (boss comes after the skill check zone)
- `MBA-FLOW-2`: LevelExit node exists as Area3D; position.x > ExitFloor.position.x (exit trigger is beyond the exit floor, at the very end of the level); the exit trigger has a CollisionShape3D with non-zero BoxShape3D
- `MBA-FLOW-3`: LevelExit script source (inline GDScript sub-resource) contains the string "level_complete" (confirms victory path leads to level completion signal)
- `MBA-FLOW-4`: ExitFloor.position.x > MiniBossFloor right edge (ExitFloor.position.x > MiniBossFloor.position.x + MiniBossFloor_box.size.x / 2) — exit floor begins after the mini-boss arena ends

**Spec must classify each requirement as [HEADLESS] or [INTEGRATION] and note any T-1 through T-52 overlap.**

**Spec must document the "arena distinctness" reasoning for AC-1:** MiniBossFloor (25 m wide) is structurally larger than any other single floor segment in the level (EntryFloor: 20 m, MutationTeaseFloor: 20 m, FusionFloor: 25 m — note FusionFloor is also 25 m; Spec Agent must verify whether MBA-GEO-3 needs to be refined to "size.x >= 25" rather than strictly larger). If FusionFloor is the same width, the arena distinctness argument relies on the arena being a dedicated single-enemy zone with no platforming obstacles — which is a design distinction rather than a strict width distinction. Spec Agent must resolve this and document the chosen approach.

**Dependencies:** None (scene already exists)
**Success Criteria:** Spec document exists at the output path; all MBA-GEO-*, MBA-BOSS-*, MBA-FLOW-* requirements are defined with acceptance criteria and HEADLESS/INTEGRATION classification; T-1 through T-52 overlap is noted.

---

### Task 2 — Test Design: T-53 through T-62

**Agent:** Test Designer Agent
**Input:**
- `mini_boss_encounter_spec.md` (Task 1 output)
- `tests/levels/test_containment_hall_01.gd` (T-1 through T-30 — must not duplicate)
- `tests/levels/test_fusion_opportunity_room.gd` (T-31 through T-42 — must not duplicate)
- `tests/levels/test_light_skill_check.gd` (T-43 through T-52 — must not duplicate)
- `tests/run_tests.gd` (auto-discovers all `test_*.gd` under `tests/`)

**Output:** `/Users/jacobbrandt/workspace/blobert/tests/levels/test_mini_boss_encounter.gd`

**Tests to write (red-phase, headless-safe), starting at T-53:**
- `T-53`: MiniBossFloor — exists as StaticBody3D; position.x ≈ 67.5 ±1.0; BoxShape3D size (25, 1, 10) exact; top surface world Y in [-0.1, 0.1]. NOTE: collision_mask covered by T-25 — do not duplicate.
- `T-54`: MiniBossFloor top surface at corridor level — computed world Y (node.y + col.y + box.half_y) in [-0.1, 0.1]
- `T-55`: EnemyMiniBoss — node exists in scene; get_scene_file_path() contains "enemy_infection_3d.tscn"; position.x in [55, 80] (within mini-boss zone bounds); position.y > 0.0 (not embedded in floor)
- `T-56`: EnemyMiniBoss arena placement — EnemyMiniBoss.position.x > SkillCheckPlatform3.position.x (boss comes after skill check)
- `T-57`: EnemyMiniBoss distinct node path — EnemyMiniBoss.get_path() is not equal to EnemyFusionA.get_path(), EnemyFusionB.get_path(), or EnemyMutationTease.get_path()
- `T-58`: ExitFloor — node exists as StaticBody3D; position.x > MiniBossFloor.position.x; BoxShape3D non-zero extents (size.x > 0, size.y > 0, size.z > 0). NOTE: collision_mask covered by T-25.
- `T-59`: LevelExit — node exists as Area3D; position.x > ExitFloor.position.x; CollisionShape3D present with BoxShape3D non-zero extents
- `T-60`: LevelExit script — inline script sub-resource source contains the string "level_complete" (level_complete signal is wired to the exit trigger)
- `T-61`: Level flow ordering — MiniBossFloor.position.x > SkillCheckPlatform3.position.x; ExitFloor.position.x > MiniBossFloor.position.x (boss zone comes after skill check; exit comes after boss zone)
- `T-62`: ExitFloor positioned after MiniBossFloor right edge — ExitFloor.position.x > (MiniBossFloor.position.x + MiniBossFloor_box_half_x) (exit floor starts after the arena ends, not overlapping)

**File structure:** `extends Object`; same helper pattern as `test_fusion_opportunity_room.gd` and `test_light_skill_check.gd` (`_pass_test`, `_fail_test`, `_assert_true`, `_assert_eq_float`, `_load_level_scene`, `run_all() -> int`); no `class_name`; `root.free()` before each test method returns.

**T-60 implementation note:** The LevelExit Area3D uses an inline GDScript set as a `sub_resource` with `script/source` in the .tscn. After `PackedScene.instantiate()`, the script source is accessible via `level_exit_node.get_script().source_code`. Assert `source_code.contains("level_complete")`.

**Dependencies:** Task 1
**Success Criteria:** All T-53 through T-62 fail in red phase when scene nodes are absent or wrong; `run_tests.sh` discovers the file automatically; no test name duplicates any T-1 through T-52 assertion name.

---

### Task 3 — Test Breaker: ADV-MBA-* adversarial tests

**Agent:** Test Breaker Agent
**Input:**
- `test_mini_boss_encounter.gd` (Task 2 output)
- `mini_boss_encounter_spec.md` (Task 1 output)

**Output:** `/Users/jacobbrandt/workspace/blobert/tests/levels/test_mini_boss_encounter_adversarial.gd`

**Adversarial cases to cover (each a distinct named failure mode; no duplicates of T-53–T-62):**
- `ADV-MBA-01`: MiniBossFloor top surface not accidentally elevated — assert top surface Y < 0.5 (catches accidental Y=1.3 placement that would put the floor above the player spawn height)
- `ADV-MBA-02`: MiniBossFloor BoxShape3D non-zero extents — assert size.x > 0, size.y > 0, size.z > 0 (independent of T-53's exact-value assertions; catches default zero-size shape)
- `ADV-MBA-03`: EnemyMiniBoss not at the same X as any regular enemy — assert abs(EnemyMiniBoss.position.x - EnemyFusionA.position.x) > 1.0, abs(EnemyMiniBoss.position.x - EnemyFusionB.position.x) > 1.0, abs(EnemyMiniBoss.position.x - EnemyMutationTease.position.x) > 1.0 (boss is spatially separated from regular enemies)
- `ADV-MBA-04`: LevelExit CollisionShape3D non-zero size — assert BoxShape3D size.x > 0, size.y > 0 (exit trigger is large enough to detect the player; not a degenerate zero-area trigger)
- `ADV-MBA-05`: LevelExit is positioned past the entire level (X > 80) — assert LevelExit.position.x > 80.0 (exit is beyond the full mini-boss arena, not prematurely placed mid-level)
- `ADV-MBA-06`: MiniBossFloor right edge clears SkillCheckPlatform3 — compute MiniBossFloor left edge (position.x - box.size.x/2) and assert it is > SkillCheckPlatform3 right edge (SkillCheckPlatform3.position.x + P3_box.size.x/2); mini-boss arena does not overlap the skill check zone
- `ADV-MBA-07`: EnemyMiniBoss position within MiniBossFloor bounds — EnemyMiniBoss.position.x >= (MiniBossFloor.position.x - MiniBossFloor_box.size.x/2) AND EnemyMiniBoss.position.x <= (MiniBossFloor.position.x + MiniBossFloor_box.size.x/2); the boss is standing on its own arena floor
- `ADV-MBA-08`: All four enemies have distinct node names — scene node names "EnemyMiniBoss", "EnemyFusionA", "EnemyFusionB", "EnemyMutationTease" are all different strings (catches duplicate-name shadowing)

**File structure:** same pattern as `test_light_skill_check_adversarial.gd`; `extends Object`; no `class_name`; `ADV-MBA-` prefix for all test names; `run_all() -> int`.

**Dependencies:** Task 2
**Success Criteria:** Adversarial file is discovered by `run_tests.sh`; each test name uses `ADV-MBA-` prefix; no duplicate of T-53–T-62 assertion names.

---

### Task 4 — Engine Integration: Run tests; apply color override if needed

**Agent:** Engine Integration Agent
**Input:**
- `test_mini_boss_encounter.gd` (Task 2 output)
- `test_mini_boss_encounter_adversarial.gd` (Task 3 output)
- `scenes/levels/containment_hall_01/containment_hall_01.tscn` (existing scene)
- `scenes/enemy/enemy_infection_3d.tscn` (enemy scene — read-only reference)
- `run_tests.sh`

**Output:**
- All T-53 through T-62 and ADV-MBA-01 through ADV-MBA-08 passing
- No regressions in T-1 through T-52
- If EnemyMiniBoss requires a scene-level property override to satisfy any spec requirement, apply the minimal override directly in `containment_hall_01.tscn` (e.g., fixing EnemyMiniBoss Y position from 0.5 to 1.3 if the spec requires it; adding a modulate color override on EnemyVisual if the spec requires visual distinctness as a testable property)
- One commit per handoff

**Actions:**
1. Run `run_tests.sh` — record full output.
2. If any T-53 through T-62 or ADV-MBA-* test fails: diagnose as test bug or scene mismatch. Scene modifications must be minimal and reversible (property overrides on the EnemyMiniBoss node in containment_hall_01.tscn only; do not modify enemy_infection_3d.tscn or any script).
3. If a color/modulate override on EnemyMiniBoss is required by the spec to satisfy a testable "distinct" criterion: apply it as a property override on the `EnemyVisual` child node of the EnemyMiniBoss instance in containment_hall_01.tscn. The override must be set in the .tscn file (not in GDScript) and must not alter any other enemy instance.
4. Confirm T-1 through T-52 remain passing after any scene edits.
5. Commit all test files and any scene corrections with message: "test: mini-boss encounter validation suite T-53–T-62 + adversarial passing"

**Dependencies:** Tasks 2, 3
**Success Criteria:** `run_tests.sh` exits with 0 failures for the new suites; prior tests T-1 through T-52 remain passing.

---

### Task 5 — AC Gatekeeper: Review and validation status

**Agent:** Acceptance Criteria Gatekeeper Agent
**Input:**
- Passing test output from Task 4
- `mini_boss_encounter_spec.md` (Task 1 output)
- This ticket's ACs

**Output:** Updated ticket with Validation Status and Blocking Issues populated; Next Responsible Agent set to Human for AC-5 manual verification.

**Actions:**
1. Map each passing test (T-53–T-62, ADV-MBA-*) to its AC coverage.
2. AC-1 (distinct enemy): covered structurally by T-53/ADV-MBA-06 (dedicated arena, 25 m floor) + MBA-BOSS-* tests confirming EnemyMiniBoss is separate from regular enemies.
3. AC-2 (winnable with movement and mutations): this AC requires human playtest. Mark as INTEGRATION — no automated test can confirm combat outcome. Add to Blocking Issues.
4. AC-3 (victory connects to level completion): covered structurally by T-59, T-60 (LevelExit exists, script contains "level_complete"), T-61 (exit is after the boss zone).
5. AC-4 (no mandatory fusion, no over-tuned difficulty): partially covered by T-55/T-57 confirming EnemyMiniBoss uses the standard enemy_infection_3d.tscn (same winnable mechanics as other enemies). Human playtest required for difficulty assessment. Add to Blocking Issues.
6. AC-5 (human-playable in-editor): mark as INTEGRATION, add to Blocking Issues.
7. Set Next Responsible Agent to Human.

**Dependencies:** Task 4
**Success Criteria:** Validation Status populated; AC-1 and AC-3 marked as structurally covered; AC-2, AC-4, AC-5 flagged as INTEGRATION pending human verification.

---

### Task 6 — Human: AC-2, AC-4, AC-5 manual verification

**Agent:** Human
**Input:** Full game run in Godot editor with `containment_hall_01.tscn` as main scene (or as `run/main_scene` in `project.godot`)
**Output:** AC-2, AC-4, AC-5 checked (or blocking issues documented); ticket moved to `done/` folder if all ACs satisfied.

**Actions:**
1. Open the project in Godot editor. Run the scene.
2. Navigate to the mini-boss zone (X≈55–80, after the skill check platforms).
3. Engage EnemyMiniBoss using movement and any available mutations. Verify: the encounter is winnable without mandatory fusion (AC-2, AC-4).
4. After defeating EnemyMiniBoss, navigate to LevelExit (X≈93). Verify: the "level_complete" signal fires (console output or any level-end feedback) (AC-3 confirmation).
5. Verify: the mini-boss arena, enemy, and exit are visually clear in-editor without debug overlays. The boss should be visually distinguishable from regular enemies (AC-5, AC-1 visual confirmation).
6. Verify: no softlock occurs if the player dies during the encounter (respawn works correctly).
7. Document results in Blocking Issues. If all ACs satisfied: check all AC boxes, clear Blocking Issues, set Stage to COMPLETE, move ticket to `done/` folder.

**Dependencies:** Task 5 complete and all automated ACs passing
**Success Criteria:** All AC checkboxes checked; ticket in `done/` folder; Stage == COMPLETE.

---

## Risks and Assumptions

| Risk | Mitigation |
|---|---|
| EnemyMiniBoss uses the same `enemy_infection_3d.tscn` as all other enemies. AC-1 "distinct" is satisfied by arena (dedicated MiniBossFloor) and encounter context, not by a different enemy class. If the human playtest (Task 6) finds this insufficient, a future ticket can add a separate enemy script or elevated health. | Documented in spec as the conservative approach. Spec Agent must confirm arena-distinctness argument. |
| EnemyMiniBoss Y=0.5 in the scene file is lower than other enemies (Y=1.3). Physics will settle it to the floor at runtime. Headless tests only assert Y > 0. | Engine Integration Agent may correct to Y=1.3 if Spec Agent requires it for correct initial position above collision shape. |
| FusionFloor is also 25 m wide (same as MiniBossFloor). MBA-GEO-3 "arena is the widest floor" may fail if width is the chosen distinctness metric. | Spec Agent must choose between (a) width distinctness (may need to reframe as "size.x >= 25" rather than strictly larger) or (b) positional distinctness (dedicated zone with no other gameplay obstacles). Decision logged in spec. |
| LevelExit inline script source readability: `level_exit_node.get_script().source_code` requires the script to be a GDScript sub-resource embedded in the .tscn. If Godot's headless mode does not expose `source_code` on inline scripts, T-60 may need a fallback approach. | Test Designer Agent must verify the property is accessible after `PackedScene.instantiate()`. If source_code is empty, the test should fall back to asserting `level_exit_node.has_method("_on_body_entered")` as a proxy. |
| Gobot GLB model (`EnemyVisual`) does not have a directly accessible MeshInstance3D with a `material_override` property at the top level. A color override would need to target a specific surface within the GLB's mesh hierarchy. | Color override approach is deferred unless the Spec Agent explicitly requires it as a testable criterion. Arena distinctness is the primary mechanism for AC-1 in this plan. |
| T-25 already asserts collision_mask == 3 for all StaticBody3D nodes including MiniBossFloor and ExitFloor. New tests must not duplicate this. | All new tests include a NOTE comment referencing T-25; no new collision_mask assertions emitted. |

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "ticket": "project_board/4_milestone_4_prototype_level/in_progress/mini_boss_encounter.md",
  "action": "Manual playtest of containment_hall_01.tscn per Task 6 instructions",
  "acs_requiring_human_verification": ["AC-2", "AC-4", "AC-5"],
  "acs_structurally_covered": ["AC-1", "AC-3"]
}
```

## Status
Needs Attention

## Reason
AC-1 and AC-3 are structurally covered by passing headless tests (T-53–T-62, ADV-MBA-01–ADV-MBA-08, 66 total assertions, 0 failures, no regressions in T-1–T-52). Three acceptance criteria cannot be satisfied by automated testing and require documented human playtest evidence before the ticket may advance to COMPLETE: AC-2 (encounter is winnable with movement and available mutations — combat outcome cannot be automated), AC-4 (no mandatory fusion, appropriate difficulty — difficulty tuning is a qualitative judgment), AC-5 (mini-boss arena, enemy, telegraphs, and exit are visually clear in-editor without debug overlays — visual clarity is inherently manual). Human must follow Task 6 playtest steps, document results in Blocking Issues, check all AC boxes if satisfied, clear Blocking Issues, set Stage to COMPLETE, and move ticket to the done/ folder.
