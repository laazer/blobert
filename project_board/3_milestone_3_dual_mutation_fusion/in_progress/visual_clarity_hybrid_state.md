# Visual clarity for hybrid state

**Epic:** Milestone 3 – Dual Mutation + Fusion
**Status:** In Progress

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | IMPLEMENTATION_PRESENTATION |
| Revision | 5 |
| Last Updated By | Test Breaker Agent |
| Next Responsible Agent | Presentation Agent |
| Validation Status | Proceed |
| Blocking Issues | — |

## NEXT ACTION
Presentation Agent: implement all spec changes in `infection_ui.gd` and `player_controller_3d.gd` and `game_ui.tscn`. All primary (40 passing + 13 red-phase) and adversarial (41 passing + 3 red-phase) tests must go green. Red-phase failures to fix: (1) declare 8 color constants on InfectionUI per spec NF-1 and Named Color Constants table; (2) update `_update_slot_display` to 4-param signature per API-2; (3) add `_update_fusion_display()` per API-3; (4) add `_get_fusion_active_label()` per API-4; (5) add `FusionActiveLabel` Label node to `game_ui.tscn` per API-5; (6) add `is_fusion_active() -> bool` to `PlayerController3D` per API-1; (7) add `_post_fusion_flash_until_ms: int = 0` and `_prev_both_filled: bool = false` fields per VCH-3-AC-1.

---

## Description

Ensure hybrid state (two mutations, post-fusion) has clear visual feedback so the player understands what is equipped and when fusion is available or active.

## Acceptance criteria

- [ ] Two-slot state is visible (e.g. both mutations shown)
- [ ] Hybrid state is distinguishable from single-mutation state
- [ ] Fusion trigger or result has readable feedback
- [ ] Works with existing infection/absorb visuals
- [ ] Hybrid visuals are human-playable in-editor: all cues are visible at target camera settings and understandable without debug overlays

---

## Execution Plan

### Context summary

The UI layer is fully owned by `InfectionUI` (`scripts/ui/infection_ui.gd`, `scenes/ui/game_ui.tscn`). The relevant scene nodes already present are:

- `MutationSlot1Label` / `MutationIcon1` — slot 1 state (driven by `_update_slot_display`)
- `MutationSlot2Label` / `MutationIcon2` — slot 2 state (driven by `_update_slot_display`)
- `FusePromptLabel` — shown when both slots filled (driven by `_process`)
- `AbsorbPromptLabel`, `AbsorbFeedbackLabel` — absorb cues (existing, unchanged)

The player exposes `_fusion_active: bool` and `_fusion_timer: float` (both already declared in `player_controller_3d.gd`).

The three new visual states that need distinguishable presentation are:

1. **Two-slot filled** — both `MutationSlot1Label` / `MutationSlot2Label` active; currently rendered in the same light-green (`Color(0.9, 1.0, 0.9)`) as a single filled slot — indistinguishable from having only slot 1 filled.
2. **Fusion active** — `_fusion_active == true` on the player — currently zero visual indicator beyond the speed effect itself.
3. **Post-fusion / slots cleared** — both slots empty immediately after fusion — currently identical to the initial "never absorbed" state.

### Task breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author spec: define color contracts, fusion-active indicator node, and post-fusion empty-slot visual contract | Spec Agent | This ticket + `infection_ui.gd`, `game_ui.tscn`, `player_controller_3d.gd` fields `_fusion_active`/`_fusion_timer` | `visual_clarity_hybrid_state_spec.md` with named color constants, node names, and per-state contracts for all three visual states | None | Spec document exists; all three states have distinct, named color or style contracts; post-fusion empty state has at least one distinguishable cue vs never-absorbed empty | Assumption: no new scene nodes required — existing Label + ColorRect nodes are sufficient. If a fusion-active indicator needs a new node, spec must name it and define its scene position. |
| 2 | Design primary test suite: one test per AC per state | Test Design Agent | `visual_clarity_hybrid_state_spec.md` | `tests/ui/test_infection_ui_hybrid_visuals.gd` (primary suite, headless-safe, drives InfectionUI or minimal stubs) | Task 1 | Test file loads and runs; covers: single-slot vs dual-slot color difference, fusion-active indicator visible when `_fusion_active=true`, fusion-active indicator hidden when `_fusion_active=false`, FusePromptLabel visibility on both-filled/not-filled | InfectionUI depends on scene tree nodes; tests must use stub slot objects and stub player objects. Pattern established in `tests/scenes/levels/test_3d_scene.gd` should be consulted. |
| 3 | Design adversarial test suite: break dual-slot same-color, absent fusion indicator, and post-fusion indistinguishability | Test Breaker Agent | `visual_clarity_hybrid_state_spec.md` + primary test suite from Task 2 | Adversarial cases appended to or alongside primary suite | Tasks 1, 2 | At least 6 adversarial cases covering: (a) both slots same color as single-slot, (b) fusion-active indicator absent/hidden when fusion active, (c) fusion-active indicator visible when fusion not active (false positive), (d) post-fusion empty state identical to pre-absorb empty state, (e) FusePromptLabel stays visible after fusion resolves and slots clear, (f) slot label text unchanged while color is the only distinguisher | Adversarial suite must remain headless-safe. |
| 4 | Implement: color differentiation for two-slot state + fusion-active indicator in InfectionUI | Presentation Agent | Spec from Task 1, test suite from Tasks 2–3, `infection_ui.gd`, `game_ui.tscn` | Modified `infection_ui.gd` (color logic in `_update_slot_display` and new `_update_fusion_display` method); new `FusionActiveLabel` node in `game_ui.tscn` | Tasks 1, 2, 3 | All primary and adversarial tests pass; `run_tests.sh` green; no regressions to existing absorb/slot tests | `InfectionUI._process` already reads `_player`; `_player.is_fusion_active()` is the required accessor (defined in spec API-1). |
| 5 | Static QA: review `infection_ui.gd` changes for null-safety, no bare field access, no new global state | Static QA Agent | Modified `infection_ui.gd` from Task 4 | QA report; any blocking issues returned to Presentation Agent before advancing | Task 4 | Zero critical issues; all player field accesses are null-guarded; no new autoloads or singletons introduced | — |
| 6 | Integration + in-editor verification | Human | `test_movement_3d.tscn` running in editor; two enemies absorbed, fuse triggered | Confirmation that all three states (dual-slot, fusion-active, post-fusion empty) are visually distinct without debug overlays | Task 5 | All acceptance criteria checked off | Human must run at camera angle matching release target settings (Z=0 plane, side view). |

### Assumptions logged to CHECKPOINTS.md

Three planning decisions were recorded (see CHECKPOINTS.md `## Run: 2026-03-17T00:00:00Z`):

1. **Fusion-active indicator via existing player field read** — InfectionUI will read `_player.is_fusion_active()` (new public accessor) each frame in `_process`; no new signal required. Confidence: High.
2. **New FusionActiveLabel node required** — A separate `FusionActiveLabel` Label node is added to `game_ui.tscn`; `FusePromptLabel` is not repurposed. Confidence: High.
3. **Post-fusion empty state cue** — A 600 ms timed flash (`_post_fusion_flash_until_ms`) on `MutationIcon1`/`MutationIcon2` using `COLOR_SLOT_POST_FUSION` (white) distinguishes post-fusion from never-absorbed. Confidence: Medium.

Spec-agent decisions are in `## Run: 2026-03-17T01:00:00Z` of CHECKPOINTS.md.

### Dependencies on other tickets

- `fusion_rules_and_hybrid.md` — DONE. `PlayerController3D.apply_fusion_effect`, `_fusion_active`, `_fusion_timer` are implemented.
- `two_mutation_slots.md` — DONE. `MutationSlotManager`, dual-slot labels/icons are wired in InfectionUI.

No blocking dependencies remain. This ticket is self-contained within the Presentation domain.
