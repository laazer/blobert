Title:
Limb joints and end caps — multi-segment limb rigs with ball-joint visuals

Description:
Add optional multi-segment limb rigs with backward-compatible bone naming, procedural ball-joint visuals and configurable end primitives, starting from shared humanoid rig/mesh helpers and extending to other enemies as needed. Animation can stay on the first segment per limb initially to avoid a large motion rewrite.

Source plan: `/Users/jacobbrandt/.cursor/plans/limb_joints_and_end_caps_95ed5a73.plan.md`

### Architecture context

**Rig:** `HumanoidSimpleRig.rig_definition()` and `QuadrupedSimpleRig.rig_definition()` emit one `BoneSpec` per limb (`arm_l`, `arm_r`, `leg_*`). `BoneSpec`/`RigDefinition` are plain head/tail/parent chains; Blender edit bones already behave like ball joints in rotation — the missing piece is **visual** geometry and **multiple bones per limb**.

**Mesh:** Enemies such as `AnimatedImp.build_mesh_parts` use one horizontal `create_cylinder` per arm plus a `create_sphere` hand; legs are single cylinders. `create_sphere`/`create_cylinder`/`create_box` already exist in `core/blender_utils.py`.

**Skinning:** `bind_mesh_to_armature` uses automatic weights with proximity fallback.

**Animation:** `HumanoidBodyType` and `QuadrupedBodyType` keyframe fixed names from `BoneNames` (`arm_l`, `leg_fl`, …). Those must remain the **first bone** of each limb chain when `segments > 1`.

### Design decisions

**Bone naming (backward compatible):**
- Segment 0 keeps today's names: `arm_l`, `arm_r`, `leg_l`, `leg_r`, `leg_fl`, …
- Extra segments: `arm_l_1`, `arm_l_2`, … parented in order (`arm_l` → `arm_l_1` → …)
- No change to motion files in v1 — existing keyframes on `arm_l`/`leg_fl` still drive the whole limb

**Ball-and-socket in mesh:**
- At each interior joint, add a small sphere at the joint center
- Scale from existing limb radius via tuners: `LIMB_JOINT_BALL_SCALE` (ratio) and `LIMB_JOINT_VISUAL` (bool, default True)

**Segment count:**
- New `ClassVar[int]` tuners: `ARM_SEGMENTS` and `LEG_SEGMENTS` on `HumanoidSimpleRig` (default 1)
- Use `int(self._mesh("ARM_SEGMENTS"))` in both `rig_definition()` and `build_mesh_parts()` — rig and mesh must never diverge
- Clamp to 1–8

**End-of-limb shape:**
- New string tuners: `ARM_END_SHAPE` / `LEG_END_SHAPE` with values `none`, `sphere`, `box`
- `BaseAnimatedModel._mesh_str(name: str) -> str` reads `build_options["mesh"]` and validates against allowed tokens

**Shared implementation:**
- New `asset_generation/python/src/core/rig_models/limb_chain.py`: computes N colinear points from head→tail, emits N `BoneSpec`s with correct naming and `parent_name` chain
- New mesh helper (in `blender_utils.py` or `rig_models/limb_mesh.py`): given start/end, segment count, radius, euler, joint options, end shape — appends cylinders + joint spheres + optional end primitive to `self.parts`

### Rollout order

1. `limb_chain` helper + `HumanoidSimpleRig.rig_definition()` refactor for arms/legs; `_mesh_str` on `BaseAnimatedModel`
2. `AnimatedImp` — replace inline arm/leg cylinders with helper; fix `apply_themed_materials` indexing for dynamic part groups
3. `AnimatedCarapaceHusk` — same pattern, `ARM_END_SHAPE` default `none`
4. Quadruped extension is optional / follow-up

Acceptance Criteria:
- `limb_chain(head, tail, n, name)` returns exactly `n` `BoneSpec`s; first segment name equals the legacy bone name (e.g. `arm_l`); subsequent names are `arm_l_1`, `arm_l_2`, …; each bone's parent is the previous segment; positions interpolate linearly between head and tail
- With `ARM_SEGMENTS=1` and `LEG_SEGMENTS=1`, `HumanoidSimpleRig.rig_definition()` produces an identical bone list to the current implementation (regression: all existing `test_rig_ratios.py` assertions pass)
- `BaseAnimatedModel._mesh_str("ARM_END_SHAPE")` returns the string value from `build_options["mesh"]` if present and valid, otherwise returns the class default; invalid tokens raise `ValueError`
- `AnimatedImp` builds without error with `ARM_SEGMENTS=2, LEG_SEGMENTS=2`; the resulting armature contains `arm_l` and `arm_l_1`; `apply_themed_materials` does not raise `IndexError`
- `AnimatedCarapaceHusk` builds without error with default settings (single-segment, `ARM_END_SHAPE=none`) and still passes all existing tests
- All existing `asset_generation/python/tests` pass (no regressions)
- `ARM_SEGMENTS` / `LEG_SEGMENTS` surface in the frontend `BuildControls` panel automatically via existing mesh introspection (no additional wiring needed — ClassVar[int] discovery is sufficient)

## WORKFLOW STATE

- **Stage:** COMPLETE
- **Revision:** 5
- **Last Updated By:** Implementation (Cursor Agent)
- **Next Responsible Agent:** Human
- **Status:** Proceed
- **Validation Status:** `asset_generation/python/tests` — 496 passed (includes `test_limb_chain`, `test_mesh_str`, `test_humanoid_rig_segments`, regressions)
- **Blocking Issues:** None

## NEXT ACTION

None — feature implemented: `limb_chain`, `HumanoidSimpleRig` multi-segment arms/legs, `_mesh_str` / bool `_mesh`, `limb_mesh.append_segmented_limb_mesh`, `AnimatedImp` + `AnimatedCarapaceHusk` wired. Optional follow-up: quadruped `LEG_SEGMENTS_PER_LEG`, motion rotation distribution across chain bones.
