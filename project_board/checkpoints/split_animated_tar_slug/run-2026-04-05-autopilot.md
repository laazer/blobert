# split_animated_tar_slug — autopilot run 2026-04-05

Single-ticket maintenance: extract `AnimatedTarSlug` to `animated_tar_slug.py`; registry + import via `animated_enemies.py`.

## Implementation notes

- Added `TestTarSlugClass` (BPG-CLASS-38..44) and `BPG_ADV_SPLIT_06` registry identity vs `animated_tar_slug` module.
- Removed dead imports from `animated_enemies.py` (`BaseEnemy`, blender_utils, armature_builders, material_system) after extraction — factory module is import-only.
- Updated `PROJECT_STRUCTURE.md` and `docs/ARCHITECTURE_SUMMARY.md`.

## Validation

`cd asset_generation/python && uv run pytest tests/ -q` → 380 passed, 221 subtests.
