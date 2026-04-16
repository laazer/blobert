# Blog Context Capsule — M25-06 Mouth & Tail Extras

- **Ticket ID:** M25-06
- **Goal:** Add toggled mouth (smile/grimace/flat/fang/beak) and tail (spike/whip/club/segmented/curled + length) geometry extras to all 6 animated enemies, plus frontend disabled-state rules
- **Outcome:** COMPLETE
- **Commit SHAs:** 73133a9 (implementation + org fixes), dc4158b (adversarial tests)
- **Checkpoint log:** project_board/checkpoints/M25-MTE/

## Surprises / Rework

- **4 enemy files had mouth/tail code in `apply_themed_materials()` instead of `build_mesh_parts()`** — tests patch at module level and call `build_mesh_parts()`, so code had to be in that method. Fixed for spider, imp, claw_crawler, carapace_husk.
- **None shape coercion bug** — `str(None)` produced `"None"` as a shape string, which would be forwarded to geometry builders as a literal. Fixed with `or` guard: `str(build_options.get("mouth_shape") or "smile")`.
- **tail_length ordering** — was placed after `static_float`, but spec requires it before all other floats. Fixed in `animated_build_controls_for_api()`.
- **Pre-commit org violations** required a post-implementation extraction step: `animated_build_options.py` hit 969 lines (limit 900) and `AnimatedSpider` class hit 454 lines (limit 350). Extracted `_eye_shape_pupil_control_defs`, `_mouth_control_defs`, `_tail_control_defs` into new `animated_build_options_appendage_defs.py`; spider eye geometry helpers into `animated_spider_eye_helpers.py`.
- **Test import path bug** in two test files: used `src.core.animated_enemy_builder.AnimatedEnemyBuilder` (wrong); fixed to `src.enemies.animated.AnimatedEnemyBuilder`.
- **diff-cover required** a new `test_blender_utils_mouth_tail.py` with 26 tests to bring coverage to 87% (above 85% gate).
