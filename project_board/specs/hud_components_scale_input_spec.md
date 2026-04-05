# Spec: hud_components_scale_input (MAINT-HCSI)

**Ticket:** `project_board/maintenance/in_progress/hud_components_scale_input.md`  
**Spec Date:** 2026-04-05  
**Spec Agent Revision:** 1  

**Traceability (ticket acceptance criteria):**

| Ticket AC | Spec coverage |
|-----------|----------------|
| Single documented scale parameter; default preserves current layout at `1.0` | HCSI-1, HCSI-2 |
| All interactive/readout HUD in `game_ui.tscn` scale together (incl. input hints under same tree) | HCSI-3, HCSI-4, HCSI-5 |
| `run_tests.sh` exits 0; `tests/ui/` (and any other affected tests) updated if pixel/offset assertions break | HCSI-6, HCSI-7 |

---

## Background and Context

- **Shipped HUD:** `res://scenes/ui/game_ui.tscn` — root node `GameUI` is a `CanvasLayer` with `scripts/ui/infection_ui.gd` attached. All gameplay HUD controls are **direct children** of that `CanvasLayer` today, plus the `Hints` `Control` subtree (`MoveHint`, `JumpHint`, `DetachRecallHint`, `AbsorbHint`, each with `input_hint_label.gd` where applicable).
- **Runtime API:** `InfectionUI` resolves widgets via `get_node_or_null("<Name>")` on **self** (the `CanvasLayer`). Examples: `HPBar`, `HPLabel`, `Hints`, `MutationIcon1`, `FusePromptLabel`, etc.
- **External tests:** `tests/ui/test_player_hud_layout.gd` loads `game_ui.tscn` as `CanvasLayer` and asserts `offset_*` and overlap using `_node_rect(ui, node_name)` / `ui.get_node("Hints")`. `tests/levels/test_fusion_opportunity_room.gd` T-41/T-42 require `ui.get_node_or_null("<Name>")` for six fusion HUD nodes to resolve on the **loaded root** (`GameUI`).
- **Constraint:** `CanvasLayer` is not a `Control`; it has no `scale` property for uniform UI scaling. Any `Control`-based scaling must apply under the layer root without breaking the **documented node path contract** (see HCSI-4).

---

## Requirement HCSI-1: Single HUD scale parameter (surface + documentation)

### 1. Spec Summary

**Description:** Introduce exactly **one** runtime-adjustable **HUD scale** value: a uniform floating-point factor named in code as `hud_scale` **or** `scale` on the script that owns the HUD (prefer a single exported name; if both exist, they must alias the same backing field — no competing knobs).

- **Default:** `1.0` when the scene is instantiated from `game_ui.tscn` with no overrides.
- **Documentation:** A short comment block or class-level doc on `InfectionUI` (or the designated owner script) states: (a) what the parameter does (uniform scale of the packaged HUD), (b) default `1.0`, (c) where designers/authors set it (`@export`, scene inspector, or documented autoload — pick one primary story and mention alternatives if any).

**Constraints:** Do not introduce a second independent float that also multiplies layout or fonts for the same HUD subtree (avoid “scale + separate font scale” unless they are strictly derived from one master value).

**Assumptions:** No assumptions about persistence across sessions unless the ticket is extended; this spec covers in-session/scene configuration only.

**Scope:** `game_ui.tscn` and `scripts/ui/infection_ui.gd` (plus minimal helper if needed); not other scenes.

### 2. Acceptance Criteria

- **HCSI-1.1:** Exactly one primary HUD scale parameter is visible to designers (exported on the scene’s root script **or** single documented setter used by scenes).
- **HCSI-1.2:** Default value in `game_ui.tscn` / script default is `1.0`.
- **HCSI-1.3:** Code comment or class doc answers: purpose, default, where to set.

### 3. Risk & Ambiguity Analysis

- **Risk:** Naming collision with `CanvasLayer` or `Node2D` `scale` if type changes — mitigated by keeping root as `CanvasLayer` with script property name clarified in docs.
- **Edge case:** Scene instance overrides in non-main scenes — out of scope unless they use `game_ui.tscn`.

### 4. Clarifying Questions

- None for MVP; optional future: project-wide settings resource.

---

## Requirement HCSI-2: Default `1.0` preserves legacy layout appearance

### 1. Spec Summary

**Description:** At **`hud_scale == 1.0`** (or the chosen parameter name), the **authoring layout** of `game_ui.tscn` remains the single source of truth: all `offset_*` and `theme_override_font_sizes` in the scene file stay **numerically unchanged** from the pre-feature baseline. Scaling is applied **without** rewriting those numbers for the default case.

**Observable parity:** For `1.0`, the effective on-screen size and relative placement of every control listed in HCSI-3 must match the pre-implementation behavior for the same viewport and default scene (within normal floating-point tolerance in tests, e.g. `<= 1e-3` where comparisons are used).

**Constraints:** Implementations that bake scale into edited `offset_*` at `1.0` (changing stored scene numbers) are **non-compliant** unless they produce **bit-for-bit equivalent** geometry to the legacy scene — the intended approach is apply transform/scaling in the scene tree or theme pipeline, not silently retune offsets.

**Assumptions:** Tests run in the project’s standard headless/viewport configuration as today.

**Scope:** Packaged `game_ui.tscn` only.

### 2. Acceptance Criteria

- **HCSI-2.1:** Scene file `offset_*` and per-control `theme_override_font_sizes` values are not altered solely to “simulate” `1.0`; scale factor applies on top of legacy numbers.
- **HCSI-2.2:** At default scale, layout tests that compare **design-space** rects (see HCSI-6) pass with legacy expectations, or updated tests explicitly encode “design space unchanged + scale == 1” invariants per HCSI-6.

### 3. Risk & Ambiguity Analysis

- **Edge case:** Subpixel rounding when combining scale and anchors — document tolerance in tests.
- **Risk:** `Control.scale` pivot choice shifts perceived position — HCSI-5 mandates pivot behavior.

### 4. Clarifying Questions

- None.

---

## Requirement HCSI-3: In-scope HUD elements (must scale together)

### 1. Spec Summary

**Description:** Every **Control** node that ships inside `game_ui.tscn` as part of the player HUD **must** be affected by the same uniform HUD scale factor **simultaneously**. This includes:

- All labels, progress bar, and color rects that are **direct children** of the `GameUI` root: including but not limited to `AbsorbPromptLabel`, `FusePromptLabel`, `FusionActiveLabel`, `HPLabel`, `ChunkStatusLabel`, `ClingStatusLabel`, `HPBar`, `AbsorbFeedbackLabel`, `MutationIcon`, `MutationSlotLabel`, `MutationSlot1Label`, `MutationIcon1`, `MutationSlot2Label`, `MutationIcon2`, `MutationLabel`.
- The entire **`Hints`** subtree: root `Hints` and every child `Label` (e.g. `MoveHint`, `JumpHint`, `DetachRecallHint`, `AbsorbHint`) and any future hint labels added as children of `Hints` in the same scene.

**Interactive / readout:** All of the above are in scope; there is no exemption for “non-interactive” chrome.

**Constraints:** If a new control is added to `game_ui.tscn` under the scaled subtree, it is automatically in scope.

**Assumptions:** Optional core hint labels referenced by `_collect_input_hint_labels()` (`MoveHint`, `JumpHint`, `DetachHint`, `DetachRecallHint`, `AbsorbHint`) that are **not** present in the scene remain absent; any that **are** added later must live under the same scaled subtree.

**Scope:** Only nodes instanced from `game_ui.tscn`.

### 2. Acceptance Criteria

- **HCSI-3.1:** No shipped Control in `game_ui.tscn` remains at a fixed scale while others scale (single uniform factor for the whole packaged HUD subtree).
- **HCSI-3.2:** `Hints` and all descendant hint labels scale with the same factor as `HPBar` and fusion/slot widgets.

### 3. Risk & Ambiguity Analysis

- **Edge case:** `DetachHint` is collected by script but may be absent from scene — no failure if absent; if present, it must scale like siblings.

### 4. Clarifying Questions

- None.

---

## Requirement HCSI-4: Scene graph and node path contract (`GameUI` root)

### 1. Spec Summary

**Description:** After implementation, the **loaded** `game_ui.tscn` instance must satisfy:

- Root node **class** `CanvasLayer`, **name** `GameUI` (unchanged — satisfies `infection_interaction_handler.gd` and level tests that find `InfectionUI` by name on parent).
- Root script remains `InfectionUI` / `infection_ui.gd` unless Planner approves a split; this spec assumes script stays on root for `set_absorb_available` and existing call sites.
- **Path contract:** Every `get_node_or_null("ChildName")` used in `infection_ui.gd` for HUD widgets **from `self`** must resolve to the **same logical node** as before (same names). If controls are reparented under an intermediate `Control`, implementers **must** update `infection_ui.gd` (or use `NodePath` `@export`s) so **unqualified** names still resolve — **or** update **all** documented consumers. Minimum bar: all paths listed in `test_player_hud_layout.gd` T-6.4 and fusion T-41/T-42 must resolve **relative to the `GameUI` root node** after `instantiate()`.

**Concrete external paths that must remain valid on the instantiated root** (non-null where the scene defines the node):

- Flat: `HPBar`, `HPLabel`, `ChunkStatusLabel`, `ClingStatusLabel`, `Hints`, `AbsorbPromptLabel`, `FusePromptLabel`, `FusionActiveLabel`, `AbsorbFeedbackLabel`, `MutationIcon`, `MutationSlotLabel`, `MutationSlot1Label`, `MutationIcon1`, `MutationSlot2Label`, `MutationIcon2`, `MutationLabel`, and fusion suite nodes `FusePromptLabel`, `FusionActiveLabel`, `MutationSlot1Label`, `MutationSlot2Label`, `MutationIcon1`, `MutationIcon2`.
- Nested: `Hints/MoveHint`, etc., as today.

**Constraints:** Do not rename `GameUI` or root type without a separate ticket.

**Assumptions:** `infection_interaction_handler.gd` continues to cast/find `InfectionUI` as today.

**Scope:** `game_ui.tscn`, `infection_ui.gd`, and tests that load `game_ui.tscn`.

### 2. Acceptance Criteria

- **HCSI-4.1:** `GameUI` root is `CanvasLayer` named `GameUI` with `infection_ui.gd`.
- **HCSI-4.2:** T-6.4 binding list and T-41/T-42 `get_node_or_null` lookups succeed on the instantiated root (or tests are updated in the **same** change that intentionally breaks paths, with Planner approval — default is **no break**).
- **HCSI-4.3:** `get_node_or_null("Hints")` remains non-null; children used by layout tests remain addressable as `Hints/<Child>`.

### 3. Risk & Ambiguity Analysis

- **Risk:** Reparenting under `HudRoot` without updating accessors breaks runtime — mitigated by mandatory path updates or `%` unique names with exported paths.
- **Conflict:** Planning note suggested container — this spec **allows** container **if** HCSI-4.2 still holds (typically via script-side path prefix or `get_node` overrides).

### 4. Clarifying Questions

- None.

---

## Requirement HCSI-5: Uniform scale application (mechanism and pivot)

### 1. Spec Summary

**Description:** The HUD scale factor multiplies **all** in-scope controls uniformly (same scalar on X and Y). Acceptable mechanisms include, **non-exclusively**:

- A full-screen or full-layout `Control` parent with `scale = Vector2(s, s)` where `s` is the HUD scale; **or**
- Engine/theme features (`Window.content_scale_factor`, default font/theme scaling) **only if** they apply uniformly to the entire HCSI-3 subtree without splitting fonts from layout.

**Pivot / anchor:** If using `Control.scale`, set **pivot** (or position/anchor strategy) so that **at `s = 1.0`** control positions match legacy anchors. Document the chosen pivot in code (e.g. top-left of container vs center). Anchors must remain **valid** (no systematic drift off-screen at moderate `s` in 3200×1880 design space).

**Hit-testing:** Pointer/touch targets must follow the scaled visuals (Godot’s default `Control` scaling behavior is acceptable).

**Blur / filtering:** Ticket allows tradeoffs; if `Control.scale` causes texture/text blur, document one line in implementation notes — no mandatory mip policy.

**Constraints:** No double-application (e.g. multiply `theme_override_font_sizes` **and** `Control.scale` for the same intent unless values are derived from a single `s` so effective result is linear in `s`).

**Assumptions:** `s` is positive and finite for normal gameplay; extreme values may be clamped — if so, document min/max in code (Test Breaker may add adversarial tests).

**Scope:** Implementation detail inside `game_ui` / `infection_ui` subtree.

### 2. Acceptance Criteria

- **HCSI-5.1:** Changing `s` to `2.0` (example) approximately doubles apparent size of text and controls relative to `1.0` for the same scene (modulo pivot choice, documented).
- **HCSI-5.2:** At `1.0`, pivot/anchor choice does not offset controls relative to legacy layout (HCSI-2).
- **HCSI-5.3:** Interactive controls remain clickable in their visible bounds under non-1.0 scale in manual or automated checks as defined by Test Designer.

### 3. Risk & Ambiguity Analysis

- **Edge case:** Very large `s` may clip — acceptable if documented; tests may cap range.
- **Edge case:** `s` near 0 — behavior implementation-defined unless tests specify; recommend `> 0`.

### 4. Clarifying Questions

- None.

---

## Requirement HCSI-6: Test suite obligations (`run_tests.sh` and layout tests)

### 1. Spec Summary

**Description:** When implementation lands, **`ci/scripts/run_tests.sh`** (or project-standard `run_tests.sh` on PATH) **must exit 0**.

**Layout tests:** `tests/ui/test_player_hud_layout.gd` and any other test that asserts **raw** `offset_*` on nodes that move under a scaled parent **must** be updated to remain meaningful:

- **Preferred:** Assert **design-space** properties (scene-local `offset_*` unchanged at `1.0`) **and** assert **effective** scale factor or transformed global rect / `get_global_rect()` proportional to `s`; **or**
- Assert the scale property equals `s` and spot-check one or two global bounds.

**Inventory (non-exhaustive):** `tests/levels/test_fusion_opportunity_room.gd` T-41/T-42 use `get_node_or_null` on root and read `offset_*` — if nodes stay direct children with same offsets, tests may pass unchanged; if reparenting wraps controls, **either** keep direct named descendants on root **or** update fusion tests per HCSI-4.

**Assumptions:** Test Designer coordinates with this spec before implementation merges.

**Scope:** `tests/ui/` primary; `tests/levels/` and others only as required by graph changes.

### 2. Acceptance Criteria

- **HCSI-6.1:** `run_tests.sh` exits 0 after the feature.
- **HCSI-6.2:** No test file silently asserts obsolete pixel geometry; updated tests trace to HCSI-2/HCSI-5 in comments or test names where helpful.

### 3. Risk & Ambiguity Analysis

- **Risk:** Large diff in `test_player_hud_layout.gd` — schedule in same PR as scene/script change.

### 4. Clarifying Questions

- None.

---

## Requirement HCSI-7: Explicit out-of-scope

### 1. Spec Summary

**Description:** The following are **out of scope** unless a future ticket expands scope:

- HUD instances **not** loaded from `res://scenes/ui/game_ui.tscn` (e.g. inline `InfectionUI` or duplicate scenes in test-only `.tscn` files).
- Non-HUD UI (menus, pause overlays, editor-only UI).
- Persisting HUD scale to `user://` or project settings.

**Assumptions:** Other scenes may continue to use separate UI; they do not receive the knob automatically.

**Scope:** Clarifies ticket boundary only.

### 2. Acceptance Criteria

- **HCSI-7.1:** Spec and implementation notes do not require modifying out-of-scope scenes for AC satisfaction.

### 3. Risk & Ambiguity Analysis

- **Risk:** Playtesters expect global setting — deferred.

### 4. Clarifying Questions

- None.

---

## AC ↔ Requirement ID quick map

| Requirement | Ticket AC |
|-------------|-----------|
| HCSI-1, HCSI-2 | AC — single parameter; default preserves layout |
| HCSI-3, HCSI-4, HCSI-5 | AC — all shipped HUD elements scale together |
| HCSI-6 | AC — `run_tests.sh` green; meaningful HUD tests |
| HCSI-7 | Scope boundary (supports clean AC testing) |
