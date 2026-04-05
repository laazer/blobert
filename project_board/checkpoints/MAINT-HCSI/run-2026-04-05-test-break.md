# MAINT-HCSI checkpoint — Test Breaker (2026-04-05)

**Run:** test-break  
**Ticket:** `project_board/maintenance/in_progress/hud_components_scale_input.md`  
**Spec:** `project_board/specs/hud_components_scale_input_spec.md`

## Outcome

- Extended `tests/ui/test_hud_components_scale_input.gd` with adversarial coverage (all gated on `hud_scale` like existing HCSI tests):
  - **Fractional scale:** `hud_scale = 0.5` — HPBar global width ratio (mutation: implementation only validated at `2.0`).
  - **Order / idempotency:** `1.0 → 2.0 → 1.0` — HPBar and `Hints` container sizes must match baseline (no cumulative scale).
  - **HCSI-3 triangulation:** `MutationIcon1` vs `HPBar` at `hud_scale = 1.25` — same X scale factor.
  - **Hints container vs leaf:** `Hints` `Control` vs `MoveHint` scale factor at `2.0` — subtree uniformity (HCSI-3.2).
  - **Type coercion:** `set("hud_scale", 2)` (int-like) — read-back `TYPE_FLOAT` and value `2.0` (HCSI-1).
  - **Non-finite input:** `NAN` / `INF` — sampled nodes (`HPBar`, `MutationIcon2`, `Hints`) must keep finite, sane global rects (spec: clamp/reject extreme `s`).
  - **Zero / negative:** `0.0`, `-1.0` — HPBar global rect finite and non-negative sizes (defensive; spec recommends `s > 0`).
  - **Stress ratio:** `hud_scale = 4.0` — linear width ratio on HPBar (catches premature clamping).
- Helper `_global_rect_is_finite_sane()` plus `# CHECKPOINT` on encoded assumptions (uniform subtree, float export, sane global geometry after bad writes).

## Verification

`timeout 300 godot --headless -s tests/run_tests.gd` — suite exit **1**; `tests/ui/test_hud_components_scale_input.gd` reports **12 failed** (2026-04-05): single root cause — `hud_scale` not yet on `GameUI` / `infection_ui.gd` (expected pre-implementation). Same failure mode for original HCSI-1/5/6 and new adversarial tests.

## Would have asked

- None; execution plan task 4 assigns Implementation Frontend for `game_ui.tscn` / `infection_ui.gd`.

## Assumption made

- Stage advanced to `IMPLEMENTATION_FRONTEND` and `Next Responsible Agent` to `Implementation Frontend Agent` per MAINT-HCSI planning row 4 and workflow enum (Godot UI scene + script), not `IMPLEMENTATION_GENERALIST`.

## Confidence

High for new cases tied to HCSI-3/HCSI-5 and spec edge notes; implementation may need to satisfy non-finite/zero tests via explicit clamping or validation in the setter.
