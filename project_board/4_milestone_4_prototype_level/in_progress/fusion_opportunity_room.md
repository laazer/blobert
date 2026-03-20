# Fusion opportunity in level

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
| Validation Status | AC-1 COVERED: T-31 (FusionFloor origin X, BoxShape3D size exact), T-34 (gap arithmetic), ADV-FOR-03 (floor Y at ground level), ADV-FOR-07 (all-axis non-zero extent) — all passing in 253-test suite. AC-2 COVERED: T-35/T-36 (enemy scene path contains "enemy_infection_3d.tscn"; enemy Y above platform node origin), ADV-FOR-02/ADV-FOR-21 (enemy Y above platform top surface using col offset + half-height formula), ADV-FOR-09/ADV-FOR-10 (distinct node instances with different names) — all passing. AC-3 COVERED: T-37 (has_method "get_mutation_slot_manager"), T-38 (returns non-null after tree insertion; get_slot_count()==2), ADV-FOR-04 (exact int equality), ADV-FOR-12 (get_slot(0) and get_slot(1) non-null) — all passing. AC-4 COVERED: T-39 (can_fuse false with 0 slots, true with both filled), T-40 (resolve_fusion clears both slots; no-op with 0 slots), ADV-FOR-05 (null manager no crash), ADV-FOR-06 (can_fuse(null) guard), ADV-FOR-11 (empty id never fills slot), ADV-FOR-13/ADV-FOR-14 (get_slot out-of-range returns null), ADV-FOR-15 (fill-consume-refill idempotency), ADV-FOR-16 (one slot cleared → can_fuse false), ADV-FOR-19 (player without apply_fusion_effect → slots still cleared), ADV-FOR-20 (third fill overwrites slot B) — all passing. AC-5 COVERED: T-41 (all six HUD nodes non-null in game_ui.tscn), T-42 (non-zero size, within 3200×1880, FusePromptLabel and FusionActiveLabel visible==false by default), ADV-FOR-08/ADV-FOR-18 (FusePromptLabel and FusionActiveLabel hidden standalone assertions), ADV-FOR-17 (MutationIcon1/2 are ColorRect type) — all passing. AC-6 NOT COVERED: Requires human in-editor playthrough; no automated test can verify the full weaken→infect→absorb×2→G flow end-to-end. No evidence of this verification having been performed is documented. Static QA: GDScript review returned 0 CRITICAL issues. |
| Blocking Issues | AC-6 unverified — human manual playthrough has not been performed or documented. Required evidence: human opens containment_hall_01.tscn in Godot editor, completes the full weaken→infect→absorb EnemyFusionA (Slot 1 fills) → weaken→infect→absorb EnemyFusionB (Slot 2 fills) → press G (fusion activates, both slots clear, FUSION ACTIVE label appears) in a single uninterrupted session without crash or soft-lock, and documents the result in this ticket. Ticket cannot advance to COMPLETE until this is recorded. |

---

## Description

Include a fusion opportunity in the level: area or encounter where player can obtain two mutations and perform at least one fusion as part of the 6–8 minute flow.

The level (`containment_hall_01.tscn`) is already built. The Fusion Opportunity Room zone is X: 10→35, containing `FusionFloor` (origin X=22.5, size 25×1×10), `FusionPlatformA` (X=15) and `FusionPlatformB` (X=28), with enemies `EnemyFusionA` at (15, 1.3, 0) and `EnemyFusionB` at (28, 1.3, 0). `InfectionInteractionHandler` is wired in the scene and owns a `MutationSlotManager` (two slots) and a `FusionResolver`. `GameUI` (`game_ui.tscn`) provides `FusePromptLabel`, `FusionActiveLabel`, `MutationSlot1Label`, `MutationSlot2Label`, `MutationIcon1`, and `MutationIcon2`. The `fuse` input action drives `FusionResolver.resolve_fusion` from `InfectionInteractionHandler._process`.

This ticket is about **validating and documenting** that the zone correctly supports the two-mutation-then-fuse flow, not building it from scratch.

## Acceptance Criteria

- [ ] AC-1: Zone geometry is correct — `FusionFloor` spans X≈10–35, platforms A and B are present at correct positions, with collision enabled (BoxShape3D, collision_mask=3)
- [ ] AC-2: Two enemies (`EnemyFusionA`, `EnemyFusionB`) are positioned on their respective platforms (within ±0.5 m) and are instances of `enemy_infection_3d.tscn`
- [ ] AC-3: `InfectionInteractionHandler` node is present in scene, has script, and exposes `get_mutation_slot_manager()` returning a manager with `get_slot_count() == 2`
- [ ] AC-4: `FusionResolver.can_fuse` returns true only when both slots are filled; `resolve_fusion` with both slots filled clears both slots and would call `apply_fusion_effect` on the player
- [ ] AC-5: `GameUI` scene contains the required HUD nodes: `FusePromptLabel`, `FusionActiveLabel`, `MutationSlot1Label`, `MutationSlot2Label`, `MutationIcon1`, `MutationIcon2` — all with non-zero size and within viewport bounds
- [ ] AC-6: (INTEGRATION — human) Player can complete the full flow in-editor: move to FusionPlatformA, weaken/infect/absorb EnemyFusionA → Slot 1 fills; move to FusionPlatformB, weaken/infect/absorb EnemyFusionB → Slot 2 fills; press G → fusion activates, both slots clear, FUSION ACTIVE label appears

## Dependencies

- `containment_hall_01_layout.md` — scene geometry baseline (existing tests T-1 through T-30 already cover scene load, geometry, enemies, wiring)
- `two_mutation_slots.md` (COMPLETE) — MutationSlotManager, dual-slot fill logic
- `fusion_rules_and_hybrid.md` (COMPLETE) — FusionResolver, fusion trigger and effect
- `player_hud.md` (COMPLETE) — GameUI HUD nodes and layout

---

## Execution Plan

### Task 1 — Spec: Fusion Opportunity Room spec document
**Agent:** Spec Agent
**Input:** This ticket; `containment_hall_01.tscn` (already read); `agent_context/agents/2_spec/` directory; existing spec files for reference style
**Output:** `/Users/jacobbrandt/workspace/blobert/agent_context/agents/2_spec/fusion_opportunity_room_spec.md`
**Spec must define:**
- `FUSE-GEO-1`: FusionFloor origin X, size; floor spans X≈10–35
- `FUSE-GEO-2`: FusionPlatformA at X=15, size 4×1×6; platform top surface Y≈0.3
- `FUSE-GEO-3`: FusionPlatformB at X=28, size 4×1×6; platform top surface Y≈0.3
- `FUSE-GEO-4`: Gap between PlatformA and PlatformB (X: 17–26 = 9 m gap, reachable by player jump)
- `FUSE-ENC-1`: EnemyFusionA at (15, 1.3, 0) ±0.5 m; EnemyFusionB at (28, 1.3, 0) ±0.5 m
- `FUSE-ENC-2`: Both enemies are instances of `res://scenes/enemy/enemy_infection_3d.tscn`
- `FUSE-WIRE-1`: InfectionInteractionHandler present, scripted, manager returns 2 slots
- `FUSE-WIRE-2`: FusionResolver.can_fuse gate; resolve_fusion clears both slots
- `FUSE-HUD-1`: HUD nodes present in GameUI with non-zero size, within 3200×1880 viewport
- `FUSE-FLOW-1` (INTEGRATION only): Full weaken→infect→absorb×2→fuse flow observable in-editor
**Dependencies:** None (scene already exists)
**Success Criteria:** Spec document exists; all requirements traceable to ACs; headless-testable ACs are distinguished from INTEGRATION ACs
**STATUS: COMPLETE** — `agent_context/agents/2_spec/fusion_opportunity_room_spec.md` delivered.

### Task 2 — Test Design: Fusion Opportunity Room validation tests
**Agent:** Test Designer Agent
**Input:** `fusion_opportunity_room_spec.md` (Task 1 output); existing `tests/levels/test_containment_hall_01.gd` (tests T-1 through T-30 already exist — new tests must not duplicate them, must start numbering at T-31); `tests/run_tests.gd` (auto-discovers all `test_*.gd` under `tests/`)
**Output:** New test file `/Users/jacobbrandt/workspace/blobert/tests/levels/test_fusion_opportunity_room.gd`
**Tests to write (red-phase, headless-safe):**
- `T-31`: FusionFloor X position ≈ 22.5 ±0.5 (origin); BoxShape3D size.x == 25, size.y == 1, size.z == 10 (exact)
- `T-32`: FusionPlatformA X=15 ±0.5; BoxShape3D size == (4,1,6) exact; top surface Y in [0.5, 1.2]
- `T-33`: FusionPlatformB X=28 ±0.5; BoxShape3D size == (4,1,6) exact; top surface Y in [0.5, 1.2]
- `T-34`: Platform gap: right edge of PlatformA to left edge of PlatformB is > 0 m and <= 10 m; gap ≈ 9.0 m ±0.5 (NOTE: collision_mask is already covered by T-25 — do NOT duplicate)
- `T-35`: EnemyFusionA scene path contains "enemy_infection_3d.tscn"; EnemyFusionA.position.y > FusionPlatformA.position.y (NOTE: position exact values already covered by T-24 — do NOT duplicate)
- `T-36`: EnemyFusionB scene path contains "enemy_infection_3d.tscn"; EnemyFusionB.position.y > FusionPlatformB.position.y (NOTE: position exact values already covered by T-24)
- `T-37`: InfectionInteractionHandler has_method("get_mutation_slot_manager") returns true (NOTE: node existence and script path already covered by T-9 and T-16 — do NOT duplicate)
- `T-38`: After adding scene to tree, InfectionInteractionHandler.get_mutation_slot_manager() returns non-null; get_slot_count() == 2 (requires tree insertion via Engine.get_main_loop())
- `T-39`: FusionResolver.can_fuse returns false when 0 slots filled; true when both filled (pure unit test, no scene load required)
- `T-40`: FusionResolver.resolve_fusion with both slots filled → slots both clear; with 0 slots filled → slots remain unchanged (pure unit test)
- `T-41`: GameUI (game_ui.tscn) has FusePromptLabel, FusionActiveLabel, MutationSlot1Label, MutationSlot2Label, MutationIcon1, MutationIcon2 — all non-null
- `T-42`: Each of those HUD nodes has non-zero size (width > 0, height > 0), is within 3200×1880; FusePromptLabel.visible == false; FusionActiveLabel.visible == false by default
**Note:** Tests T-39 and T-40 are pure unit tests (no scene load); T-38 requires adding scene to tree; T-41/T-42 load game_ui.tscn directly. The file extends Object and uses the same pattern as `test_containment_hall_01.gd`.
**Dependencies:** Task 1
**Success Criteria:** All T-31 through T-42 fail (red phase) before implementation; run_tests.sh discovers the file automatically

### Task 3 — Test Breaker: Adversarial extension
**Agent:** Test Breaker Agent
**Input:** `test_fusion_opportunity_room.gd` (Task 2 output); `fusion_opportunity_room_spec.md`
**Output:** New file `/Users/jacobbrandt/workspace/blobert/tests/levels/test_fusion_opportunity_room_adversarial.gd`
**Adversarial cases to cover:**
- Platform gap reachability: assert gap width (PlatformB.left_edge - PlatformA.right_edge) <= 10 m (conservative jump range from movement sim)
- Enemy Y height on platform: EnemyFusionA.position.y > FusionPlatformA.position.y (enemy must be above platform, not embedded below it)
- Slot manager slot count exact: assert `get_slot_count() == 2`, not 0 or 1
- FusionResolver.resolve_fusion with null player: no crash, slots still consumed
- FusionResolver.resolve_fusion with null slot_manager: no crash, no side effects
- FusePromptLabel visible=false by default (must not show until conditions met)
- FusionActiveLabel visible=false by default
**Dependencies:** Task 2
**Success Criteria:** Adversarial file discovered by run_tests.sh; each adversarial test is a distinct, named failure mode; no test duplicates a T-31–T-42 assertion

### Task 4 — Static QA
**Agent:** Static QA Agent
**Input:** `test_fusion_opportunity_room.gd`; `test_fusion_opportunity_room_adversarial.gd`; `fusion_opportunity_room_spec.md`
**Output:** QA report confirming: no parse errors, no duplicate test names, correct `run_all()` signature, no `await` or physics dependency, traceability table maps each T-ID to a spec AC
**Dependencies:** Tasks 2, 3
**Success Criteria:** No issues found, or all issues are filed as blocking issues on this ticket

### Task 5 — Integration: Human playthrough verification (AC-6)
**Agent:** Human
**Input:** Full game run in Godot editor with `containment_hall_01.tscn` as main scene; run `run_tests.sh` to confirm T-31–T-42 and adversarial suite all pass
**Output:** Ticket AC-6 checked; ticket moved to `done/`
**Dependencies:** Tasks 1–4 complete and passing
**Success Criteria:** Player can complete weaken→infect→absorb×2→G fusion in a single uninterrupted play session; FUSION ACTIVE label appears; no crash or soft-lock

---

## Risks and Assumptions

| Risk | Mitigation |
|---|---|
| `containment_hall_01.tscn` does not have `InfectionInteractionHandler` wired to `GameUI` for the fuse prompt (prompt stays hidden) | T-38 will detect missing slot manager wiring; AC-6 will detect missing visual feedback |
| Platform gap (9 m between PlatformA right edge and PlatformB left edge) may exceed player jump range | Adversarial T covers gap <= 10 m; if gap is too wide, a scene fix is needed before INTEGRATION |
| Existing tests T-1 through T-30 in `test_containment_hall_01.gd` already partially cover FusionFloor/PlatformA/PlatformB geometry (T-20, T-21, T-27) — new tests must not duplicate | Spec Agent has cross-referenced existing test file; T-34 remapped to gap assertion; T-35/T-36 remapped to scene-path + Y-guard assertions; T-37 remapped to has_method guard |
| No `containment_hall_01_spec.md` exists yet — Spec Agent must derive from scene and this ticket | Documented; acceptable given scene is fully built |

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "ticket": "project_board/4_milestone_4_prototype_level/in_progress/fusion_opportunity_room.md",
  "scene": "scenes/levels/containment_hall_01/containment_hall_01.tscn",
  "action": "Open containment_hall_01.tscn in Godot editor. Run the scene. Complete the full flow: move to FusionPlatformA, weaken/infect/absorb EnemyFusionA (verify Slot 1 fills); move to FusionPlatformB, weaken/infect/absorb EnemyFusionB (verify Slot 2 fills); press G (verify fusion activates: both slots clear, FUSION ACTIVE label appears, no crash or soft-lock). Document result in Blocking Issues. If successful, check AC-6 checkbox, clear Blocking Issues, set Stage to COMPLETE, move ticket to done/ folder."
}
```

## Status
Needs Attention

## Reason
AC-1 through AC-5 are fully evidenced by automated tests (T-31–T-42 primary suite, ADV-FOR-01–21 adversarial suite, 253 total passing, 0 failing) and GDScript static review (0 CRITICAL issues). AC-6 requires human in-editor playthrough verification; no automated test can satisfy this criterion and no prior human verification is documented in this ticket. Stage is held at INTEGRATION. Ticket cannot advance to COMPLETE until a human performs and documents the AC-6 playthrough described in Blocking Issues.
