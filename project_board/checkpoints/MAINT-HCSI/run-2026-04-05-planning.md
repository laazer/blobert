# MAINT-HCSI — hud_components_scale_input

Run started 2026-04-05 (autopilot maintenance backlog).

## Execution Plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author functional spec for unified HUD scale (default 1.0), scene/script contract, and test impact | Spec Agent | Ticket `hud_components_scale_input.md`; `scenes/ui/game_ui.tscn`; `scripts/ui/infection_ui.gd`; `scripts/ui/input_hint_label.gd`; `tests/ui/test_player_hud_layout.gd` (offset-based layout suite) | `agent_context/projects/...` or ticket-appended spec per project convention — **non-code** specification only | None | Spec covers: single scale parameter surface; all interactive/readout elements under packaged `game_ui.tscn` including `Hints` / `input_hint_label` children; behavior at 1.0 matches current visuals; chosen Godot mechanism (e.g. scaled `Control` subtree vs theme scaling) with pivot/anchors, hit-testing, and blur/art notes; explicit node-path strategy if reparenting (all `get_node` in `infection_ui.gd` remain valid or documented renames) | CanvasLayer root cannot be scaled as `Control`; reparenting breaks direct `get_node("HPBar")` unless paths updated. `scenes/test_infection_loop.tscn` has inline `InfectionUI` not instancing `game_ui.tscn` — clarify in spec whether in or out of scope. |
| 2 | Write/update behavioral tests for default scale and any spec-defined non-1.0 invariants | Test Designer | Approved spec from task 1 | New or extended tests under `tests/ui/` (and only other `tests/` paths if spec requires) | 1 | `run_tests.sh` green after implementation lands; layout tests remain meaningful: either still assert design-space `offset_*` on scene nodes, or assert scale property + transformed bounds per spec | `test_player_hud_layout.gd` heavily asserts exact `offset_*` on direct children of loaded `CanvasLayer` — structural change requires coordinated test updates. |
| 3 | Adversarial tests for scale edges and layout invariants | Test Breaker | Spec + tests from tasks 1–2 | Additional adversarial cases in `tests/ui/` or companion files | 2 | Mutations (zero/negative/huge scale, missing container) caught or explicitly spec-forbidden with tests | Over-constraining implementation if spec leaves bounds open. |
| 4 | Implement HUD scale in scene + `InfectionUI` (and related scripts) per spec | Implementation Frontend (or Generalist if cross-domain) | Spec, finalized tests | `game_ui.tscn` / `infection_ui.gd` changes; any minimal wiring (autoload export, project setting) per spec | 1–3 (implement after red tests exist per TDD) | AC: one documented knob default 1.0; all shipped HUD in `game_ui.tscn` scales together including input hints; `run_tests.sh` exits 0 | `infection_interaction_handler.gd` only references `InfectionUI` as `CanvasLayer` by name — root type/name must stay compatible unless spec changes contract. Fusion/start-flow tests in `tests/levels/` also load `game_ui.tscn` and assert root class/name. |
| 5 | GDScript review + full test run evidence | gdscript-reviewer (optional) + implementer | Task 4 diff | Review notes; logged test output | 4 | No new parse issues; reviewer sign-off per project process | Skippable if pipeline omits dedicated review stage. |

### [MAINT-HCSI] PLANNING — Scene graph vs. `get_node` contracts
**Would have asked:** If we introduce a scaled `Control` root under `CanvasLayer`, should every `infection_ui.gd` helper switch to nested paths (or `%` unique names)?
**Assumption made:** Spec must mandate one consistent resolution strategy so `_get_hp_bar()` et al. keep working; default expectation is reparent all HUD controls under one container and update paths (or use `NodePath` exports) — document in spec.
**Confidence:** High

### [MAINT-HCSI] PLANNING — Test suites outside `tests/ui/`
**Would have asked:** Do `test_fusion_opportunity_room.gd` / `test_start_finish_flow.gd` pixel or viewport assertions require updates for HUD scale?
**Assumption made:** Task 1 spec inventories all `game_ui.tscn` consumers in `tests/` that assert sizes or child paths; Task 4 extends tests if spec finds hard-coded pixel expectations beyond `tests/ui/`.
**Confidence:** Medium

---

**Resume:** Ticket `project_board/maintenance/in_progress/hud_components_scale_input.md` — Stage SPECIFICATION; next agent Spec Agent.
