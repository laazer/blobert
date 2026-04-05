# MAINT-HCSI — implementation checkpoint (2026-04-05)

## Outcome

- `InfectionUI` exposes `@export var hud_scale` (backing `_hud_scale_value`) with getter/setter; default `1.0`; sanitizes non-finite → `1.0`, non-positive → `0.0`.
- Direct `Control` children of `GameUI` use uniform `Control.scale` + `pivot_offset` (0,0).
- `Hints`: `scale` stays `Vector2.ONE`; container size tracks `hud_scale` via runtime `offset_right` / `offset_bottom` = base `2000×102` × s; each direct hint child gets the same `hud_scale` on `scale` (nested labels did not match HPBar global-rect ratios when only the parent was scaled under `CanvasLayer`).
- `game_ui.tscn`: `Hints` explicit layout `0,0,2000,102` at authoring (matches script constants).

## Assumption (conservative)

- If `Hints` pack bounds change in the scene, update `_HINTS_PACK_BASE_W` / `_HINTS_PACK_BASE_H` in `infection_ui.gd` to match `offset_right` / `offset_bottom` at `hud_scale == 1.0`.

## Evidence

- `timeout 300 ci/scripts/run_tests.sh` — exit 0 (`=== ALL TESTS PASSED ===`).

## Confidence

High (full suite green).
