# MAINT-EMSI — enemy_model_scale_input

Run started 2026-04-05 (autopilot maintenance backlog).

### [MAINT-EMSI] Planning — uniform scale application strategy
**Would have asked:** Should uniform scaling be implemented by multiplying every primitive `location` and `scale` in archetypes, by a parent empty + join, or another Blender export–friendly path?
**Assumption made:** Spec will require a single uniform multiplier applied consistently to all world-space positions and primitive scale tuples passed into `create_sphere` / `create_cylinder` (and numeric literal offsets in those calls), leaving Euler rotations unchanged—unless measurement proves a different approach is required for export determinism.
**Confidence:** Medium

### [MAINT-EMSI] Planning — invalid scale values
**Would have asked:** What is the contract for `scale <= 0`, NaN, or non-finite values?
**Assumption made:** Public API accepts positive finite floats only; values outside that domain are undefined and may be rejected (e.g. `ValueError` from the factory) with the spec stating the rule explicitly. Tests focus on the valid domain plus default `1.0`.
**Confidence:** Medium

### [MAINT-EMSI] Planning — instance attribute naming vs Blender `object.scale`
**Would have asked:** Should the multiplier on `BaseModelType` be named `scale` despite Blender mesh objects also having `scale`?
**Assumption made:** Factory keyword remains `scale=` for AC alignment; the instance stores the multiplier under a distinct name (e.g. `geometry_scale` or `uniform_scale`) to reduce confusion in archetype code that manipulates Blender objects.
**Confidence:** High

### [MAINT-EMSI] Planning — downstream callers
**Would have asked:** Are there non-test callers of `create_model` that must be updated in the same change?
**Assumption made:** Repo search shows only `asset_generation/python/tests/enemies/test_base_models_factory.py` invokes `ModelTypeFactory.create_model`; adding an optional/defaulted parameter satisfies backward compatibility without mandatory caller edits.
**Confidence:** High
