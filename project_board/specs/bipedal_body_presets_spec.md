# Specification: Bipedal Body Presets (M25-05)

## Overview

Add `body_type` (`select_str`: `default`, `standard_biped`, `no_leg_biped`) to all animated enemy build controls, validate in `options_for_enemy`, and apply silhouette multipliers in Blender builders per slug family.

## Functional requirements

1. **BT-1 — Control surface**: `animated_build_controls_for_api()` includes `body_type` for every slug in `ANIMATED_SLUGS`, with label "Body Type", hint mentioning preview updates after regeneration, and options exactly `default`, `standard_biped`, `no_leg_biped`.

2. **BT-2 — Defaults**: `_defaults_for_slug` sets `body_type` to `default` for animated slugs.

3. **BT-3 — Merge / coerce**: `options_for_enemy` accepts top-level `body_type`; unknown values coerce to `default`; valid presets pass through.

4. **BT-4 — Geometry**: Each animated enemy `build_mesh_parts` applies preset-specific scale multipliers (humanoid / blob / quadruped families) so `standard_biped` reads taller with clearer limb separation where applicable, and `no_leg_biped` reads lower/wider with shortened legs.

5. **BT-5 — Rig alignment**: Humanoid leg segment count used for mesh matches `HumanoidSimpleRig` / `_segment_count` after presets (e.g. at least two segments for standard biped when preset demands).

6. **BT-6 — Non-goals**: `player_slime` does not receive `body_type`; arm configuration unchanged by preset alone.

## Non-functional

- Serialization: `body_type` is a top-level key in merged build options (not under `mesh`).

## Test coverage

- Python: `test_body_type_control.py` — exposure, coercion, valid presets per slug.
- Frontend: Vitest meta load — `body_type` row and `setAnimatedBuildOption` for `no_leg_biped`.
