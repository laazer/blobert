# Player HUD

**Epic:** Milestone 4 – Prototype Level
**Status:** Done

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | COMPLETE |
| Revision | 8 |
| Last Updated By | Human |
| Next Responsible Agent | — |
| Validation Status | All 10 AC satisfied. Tests: 253 passed / 0 failed. GDScript review clean. Human playtest confirmed: top-left HUD shows HP bar + chunk + cling, distinct mutation slot rows, no input hints visible by default, absorb prompt at bottom-center, no overlaps, readable without debug overlays. |
| Blocking Issues | — |

## NEXT ACTION

| Field | Value |
|---|---|
| Next Responsible Agent | Human |
| Status | Needs Attention |
| Reason | Acceptance criteria AC-1 through AC-9 are satisfied by explicit automated test coverage (253 passed, 0 failed). AC-10 ("HUD is human-readable in-editor without debug overlays") is inherently manual and cannot be auto-evidenced. A human must open the Godot editor, run the main scene, visually verify HUD legibility with no debug overlays, and document confirmation in Blocking Issues before this ticket advances to COMPLETE. |
| Required Input Schema | Human confirms: "AC-10 verified: opened Godot editor, ran main scene, confirmed all HUD elements are legible and no debug overlays appear in normal play. Date: YYYY-MM-DD." |

---

## Description

Replace the current debug-style text labels scattered across the screen with a proper player HUD. All status information (HP, chunk state, wall cling, mutation slots) should live in a dedicated, visually coherent overlay that makes game state easy to read at a glance. Debug/test text should only appear when explicitly enabled — not in normal play.

## Acceptance criteria

- [ ] HP bar and HP value are displayed in a fixed HUD region (e.g. top-left panel)
- [ ] Chunk status (Attached / Detached) is shown in the HUD, not as a raw text label
- [ ] Wall cling state is shown in the HUD, not as a raw text label
- [ ] Mutation slot 1 and slot 2 are shown as distinct HUD elements (icon + label), clearly separated and readable
- [ ] Absorb prompt ("Press R to Absorb") appears contextually and does not overlap other HUD elements
- [ ] Absorb feedback ("Absorbed!") flash is positioned so it does not overlap slot labels or HP
- [ ] Input hint labels (Move, Jump, Detach, Absorb) are grouped and toggled via `InputHintsConfig` — hidden by default in normal play
- [ ] No two HUD elements overlap each other at the default viewport resolution (3200×1880)
- [ ] All existing `infection_ui.gd` data bindings (HP, chunk, cling, slot manager, absorb available) are preserved — only layout and presentation change
- [ ] HUD is human-readable in-editor without debug overlays

---

## Execution Plan

### Overview

This is a layout and presentation reorganization. No logic changes to `infection_ui.gd` data bindings are permitted. All changes are confined to:
1. `scenes/ui/game_ui.tscn` — node positions, HPBar node type, Hints visibility default
2. `scripts/ui/input_hints_config.gd` — default value change (`true` → `false`)

Node names must not change (all `get_node_or_null("NodeName")` calls in `infection_ui.gd` use flat paths from the CanvasLayer root). All leaf nodes remain direct children of `GameUI` CanvasLayer — no nesting into containers.

### Key constraints

- Target resolution: 3200×1880
- Node names: immutable (see CHECKPOINT above)
- `infection_ui.gd`: read-only for this ticket
- `HPBar`: replace `TextureProgressBar` with `ProgressBar` (same node name, same `Range` base class)
- `InputHintsConfig.input_hints_enabled`: change default from `true` to `false`
- Legacy nodes `MutationSlotLabel` and `MutationIcon`: keep, reposition below dual-slot rows, `visible = false` default

### Layout regions (at 3200×1880)

| Region | Nodes | X range | Y range |
|---|---|---|---|
| Top-left status strip | HPBar, HPLabel, ChunkStatusLabel, ClingStatusLabel | 20–400 | 8–180 |
| Mid-left mutation panel | MutationIcon1+MutationSlot1Label, MutationIcon2+MutationSlot2Label | 20–400 | 200–300 |
| Fusion-active notice | FusionActiveLabel | 20–300 | 310–340 |
| Mutation count | MutationLabel | 20–300 | 350–375 |
| Legacy compat (hidden) | MutationSlotLabel, MutationIcon | 20–300 | 390–415 |
| Contextual center-bottom | AbsorbPromptLabel, FusePromptLabel, AbsorbFeedbackLabel | 1400–1800 | 1800–1870 |
| Input hints (hidden default) | Hints > MoveHint, JumpHint, DetachRecallHint, AbsorbHint | 1300–2000 | 12–120 |

### Task table

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|---|---|---|---|---|---|---|
| 1 | Author HUD layout specification | Spec Agent | This ticket; `scenes/ui/game_ui.tscn`; `scripts/ui/infection_ui.gd`; layout regions table above; all five CHECKPOINT decisions | A spec document at `agent_context/agents/2_spec/player_hud_spec.md` defining: exact `offset_*` values for every named node at 3200×1880; the `ProgressBar` replacement contract; the `InputHintsConfig` default change; verification method for the no-overlap AC | None | Spec document exists; every named node in `game_ui.tscn` has a specified position; no-overlap rule is expressible as a set of bounding-box disjointness assertions | Node names must be preserved exactly; spec must not introduce new node names not in the existing scene |
| 2 | Implement HUD layout in `game_ui.tscn` | Presentation Agent | `player_hud_spec.md`; current `scenes/ui/game_ui.tscn` | Updated `scenes/ui/game_ui.tscn` with all nodes repositioned per spec; `HPBar` replaced with `ProgressBar`; legacy nodes set `visible = false`; `Hints` children positioned per spec | Task 1 | Scene opens in Godot editor without errors; all nodes at specified positions; HPBar is a `ProgressBar` node; no nodes overlap at 3200×1880 as verified by bounding-box checks in the test suite | Godot `.tscn` format requires correct node type string for `ProgressBar`; uid must remain stable — do not change `uid="uid://cgame_ui001"` |
| 3 | Change `InputHintsConfig` default to `false` | Presentation Agent | `scripts/ui/input_hints_config.gd` | Updated `scripts/ui/input_hints_config.gd` with `var input_hints_enabled: bool = false` | Task 1 | File diff shows only the `true` → `false` change; `run_tests.sh` passes (no test depends on the default being `true`) | `input_hint_label.gd` reads config at `_init()` time and will now hide hints by default — verify no test instantiates hints in a scene where they must be visible |
| 4 | Write HUD layout verification tests | Spec Agent or Test Design Agent | `player_hud_spec.md`; list of named nodes and their specified bounding boxes | A test file at `tests/ui/test_player_hud_layout.gd` that: loads `game_ui.tscn`; asserts each node's offset values match the spec; asserts no two node bounding boxes overlap; asserts `HPBar` is a `ProgressBar` (not `TextureProgressBar`) | Task 1 | Test file parses cleanly; tests fail before Task 2 (red phase); tests pass after Task 2 (green phase) | `game_ui.tscn` instantiation in headless test requires CanvasLayer to be added to the scene tree; use `add_child` pattern consistent with existing UI tests |
| 5 | Verify all existing tests pass | Engine Integration Agent | Completed Tasks 2 and 3; test suite at `tests/` | `run_tests.sh` output showing zero failures | Tasks 2, 3, 4 | `run_tests.sh` exits 0; no regressions in infection_ui, mutation slot, fusion, or chunk tests | Any path change to nodes accessed by `infection_ui.gd` would break existing tests — the no-rename constraint prevents this |

### Out of scope

- Visual styling (fonts, colors, themes) — existing colors and font sizes are preserved
- New data bindings or new logic in `infection_ui.gd`
- Any node renames
- Audio or animation
- Save/load of HUD state

