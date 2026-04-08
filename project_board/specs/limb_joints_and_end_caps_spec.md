# Specification: Limb Joints and End Caps (M5-LJEC)

**Ticket:** `project_board/5_milestone_5_procedural_enemy_generation/in_progress/limb_joints_and_end_caps.md`
**Plan:** `project_board/specs/limb_joints_and_end_caps_plan.md`
**Checkpoint log:** `project_board/checkpoints/M5-LJEC/run-2026-04-07T14-00-00Z-spec.md`
**Spec Agent revision:** 2026-04-07

---

## Scope

All implementation is Python only, under `asset_generation/python/src/`. No Godot/GDScript changes. Tests run under `uv run pytest asset_generation/python/tests/ -q`. `QuadrupedSimpleRig` is explicitly out of scope for v1.

---

## Requirement LJEC-1: `limb_chain` function — new module

### 1. Spec Summary

- **Description:** A new pure-logic function `limb_chain(head, tail, n, name)` is added in a new module `asset_generation/python/src/core/rig_models/limb_chain.py`. It computes `n` colinear `BoneSpec` objects interpolated along the vector from `head` to `tail`, with a naming convention that preserves backward compatibility with existing bone names.
- **Constraints:**
  - Must import only `mathutils.Vector` and types from `..rig_types` (`BoneSpec`). No Blender `bpy` dependency.
  - The function is pure: no side effects, no global state mutation.
  - `n` must be clamped to the integer range `[1, 8]` before processing. Values below 1 are treated as 1; values above 8 are treated as 8.
  - `head` and `tail` are `mathutils.Vector` instances.
  - Returns a `list[BoneSpec]`.
- **Assumptions:** `mathutils.Vector` is available via the existing stub in `tests/conftest.py` → `blender_stubs.py`. The stub's `_Vector` does not implement `lerp()`; linear interpolation must be implemented via arithmetic or a helper that works with the stub's `_t` tuple, OR the stub must be extended to support `lerp()`. See LJEC-1 Risk.
- **Scope:** `asset_generation/python/src/core/rig_models/limb_chain.py` only.

### 2. Acceptance Criteria

**LJEC-1-AC1:** `limb_chain(head, tail, n, name)` returns a `list[BoneSpec]` of length exactly `n` (after clamping).

**LJEC-1-AC2 (naming — segment 0):** The first element's `name` attribute equals `name` exactly (e.g., if `name="arm_l"`, `result[0].name == "arm_l"`).

**LJEC-1-AC3 (naming — subsequent segments):** For index `i` in `1..n-1`, `result[i].name == f"{name}_{i}"`. Examples: `result[1].name == "arm_l_1"`, `result[2].name == "arm_l_2"`.

**LJEC-1-AC4 (parent chain):** `result[0].parent_name` is `None` (the caller must set the parent on the returned chain's first element — see LJEC-4-AC2 regarding how `rig_definition()` connects chains).

  Correction: `result[0].parent_name` carries the parent passed to the chain, not `None`. The caller passes a `parent_name: str | None` argument to `limb_chain`. `result[0].parent_name == parent_name`. `result[i].parent_name == result[i-1].name` for `i >= 1`.

**LJEC-1-AC5 (parent chain — internal):** For `i >= 1`, `result[i].parent_name == result[i-1].name`. Example with `name="arm_l"`, `n=3`: `result[1].parent_name == "arm_l"`, `result[2].parent_name == "arm_l_1"`.

**LJEC-1-AC6 (position interpolation — heads and tails):** Divide the segment from `head` to `tail` into `n` equal intervals. For segment `i` (0-indexed):
  - `result[i].head` = `head + (tail - head) * (i / n)`, i.e., linear interpolation at fraction `i/n`.
  - `result[i].tail` = `head + (tail - head) * ((i + 1) / n)`, i.e., linear interpolation at fraction `(i+1)/n`.
  - Consequence: `result[0].head == head`, `result[n-1].tail == tail`, and consecutive segments are contiguous (`result[i].tail == result[i+1].head` for all valid `i`).

**LJEC-1-AC7 (clamping — below minimum):** `limb_chain(h, t, 0, "arm_l")` returns a list of length 1 (clamped to 1). `limb_chain(h, t, -5, "arm_l")` returns a list of length 1.

**LJEC-1-AC8 (clamping — above maximum):** `limb_chain(h, t, 9, "arm_l")` returns a list of length 8. `limb_chain(h, t, 100, "arm_l")` returns a list of length 8.

**LJEC-1-AC9 (n=1 identity):** `limb_chain(head, tail, 1, "arm_l")` returns `[BoneSpec(name="arm_l", head=head, tail=tail, parent_name=<caller-supplied>)]` — identical semantics to a single-bone chain in the existing `rig_from_bone_map` call.

**LJEC-1-AC10 (return type):** Return type is `list[BoneSpec]`, not a tuple or generator.

### 3. Risk & Ambiguity Analysis

- **Risk — Vector arithmetic in stub:** The existing `_Vector` stub in `blender_stubs.py` supports `__eq__` and `__repr__` but does NOT implement `__add__`, `__sub__`, `__mul__`, or `lerp()`. Linear interpolation requires these operations. The implementation and tests must either: (a) extend the stub with arithmetic operators, or (b) implement interpolation using plain float arithmetic on vector components. The spec requires that the stub be extended minimally to support the arithmetic needed by `limb_chain`, or that `limb_chain` uses a helper that works with the stub as-is. This is flagged as a dependency for the Test Designer and Implementer.
- **Risk — `parent_name` on segment 0:** The AC above was amended mid-spec: `limb_chain` takes a `parent_name` argument so the caller can inject the chain's attachment point (e.g. `"spine"` for arm chains, `"root"` for leg chains). This is the only way the returned `BoneSpec`s are fully self-contained.

### 4. Clarifying Questions

None — resolved via checkpoint log `run-2026-04-07T14-00-00Z-spec.md`.

---

## Requirement LJEC-2: `limb_chain` function — full signature

### 1. Spec Summary

- **Description:** Precise function signature for `limb_chain`.
- **Constraints:** All parameters are positional-or-keyword. No `*args` or `**kwargs`.
- **Assumptions:** None beyond LJEC-1.
- **Scope:** `asset_generation/python/src/core/rig_models/limb_chain.py`.

### 2. Acceptance Criteria

**LJEC-2-AC1 (signature):**
```
def limb_chain(
    head: Vector,
    tail: Vector,
    n: int,
    name: str,
    parent_name: str | None = None,
) -> list[BoneSpec]:
```

**LJEC-2-AC2:** Module also exports `ALLOWED_END_SHAPES: Final[tuple[str, ...]] = ("none", "sphere", "box")` — the canonical set of valid string tokens for `ARM_END_SHAPE` / `LEG_END_SHAPE`. This constant is imported by `BaseAnimatedModel._mesh_str` and by `HumanoidSimpleRig`.

**LJEC-2-AC3:** The module is importable without Blender (`bpy`) present, i.e., the existing `tests/conftest.py` stubs are sufficient to import it.

### 3. Risk & Ambiguity Analysis

- Placing `ALLOWED_END_SHAPES` in `limb_chain.py` creates a mild coupling between the chain-generation module and the mesh-shaping concern. Alternative: place it in `humanoid_simple.py`. The conservative choice (limb_chain.py) keeps both the naming logic and the shape vocabulary together as the primary "limb" module. If the Test Designer or Implementer finds this awkward, the constant may be moved to `humanoid_simple.py` without changing the AC, provided `_mesh_str` still imports from the same authoritative source.

### 4. Clarifying Questions

None.

---

## Requirement LJEC-3: `BaseAnimatedModel._mesh_str` method

### 1. Spec Summary

- **Description:** A new method `_mesh_str(name: str, allowed: tuple[str, ...] | None = None) -> str` is added to `BaseAnimatedModel` in `asset_generation/python/src/enemies/base_animated_model.py`. It resolves a string-valued ClassVar (e.g. `ARM_END_SHAPE`) with optional override from `build_options["mesh"]`, and validates the resolved value against a set of allowed tokens.
- **Constraints:**
  - Must not modify or replace `_mesh`. They coexist.
  - When `allowed` is `None`, uses `ALLOWED_END_SHAPES` imported from `limb_chain.py` as the default allowed set.
  - Must raise `ValueError` (not `KeyError`, not `AttributeError`) if the resolved value is not in `allowed`.
  - The `name` argument must match a ClassVar attribute on the concrete subclass. If the attribute is missing entirely, `AttributeError` from `getattr` propagates naturally (not caught).
- **Assumptions:** `ALLOWED_END_SHAPES` is importable from `core.rig_models.limb_chain`.
- **Scope:** `asset_generation/python/src/enemies/base_animated_model.py`.

### 2. Acceptance Criteria

**LJEC-3-AC1 (fallback to class default — key absent):** When `build_options["mesh"]` does not contain `name`, returns `str(getattr(type(self), name))` (the ClassVar value).

**LJEC-3-AC2 (override from build_options — valid token):** When `build_options["mesh"]` contains `name` with a value that is in `allowed`, returns that string value.

**LJEC-3-AC3 (ValueError on invalid token — from override):** When `build_options["mesh"]` contains `name` with a value NOT in `allowed`, raises `ValueError` with a message that identifies the invalid token and the allowed options.

**LJEC-3-AC4 (ValueError on invalid token — from class default):** When the ClassVar default value is not in `allowed` (i.e., a programming error in the class definition), `_mesh_str` raises `ValueError`. This enforces that class authors cannot set an illegal default.

**LJEC-3-AC5 (allowed parameter passthrough):** If `allowed` is provided explicitly (not `None`), that tuple is used instead of `ALLOWED_END_SHAPES`. The method is not hardcoded to `ALLOWED_END_SHAPES`; the parameter allows future extensibility.

**LJEC-3-AC6 (return type is str):** The method always returns a `str`, never `None` or another type.

**LJEC-3-AC7 (method signature):**
```
def _mesh_str(self, name: str, allowed: tuple[str, ...] | None = None) -> str:
```

**LJEC-3-AC8 (example — ARM_END_SHAPE default):** Given a class with `ARM_END_SHAPE = "none"` and empty `build_options`, `self._mesh_str("ARM_END_SHAPE")` returns `"none"`.

**LJEC-3-AC9 (example — build_options override to "sphere"):** Given `build_options={"mesh": {"ARM_END_SHAPE": "sphere"}}`, `self._mesh_str("ARM_END_SHAPE")` returns `"sphere"`.

**LJEC-3-AC10 (example — build_options override to invalid):** Given `build_options={"mesh": {"ARM_END_SHAPE": "triangle"}}`, `self._mesh_str("ARM_END_SHAPE")` raises `ValueError`.

### 3. Risk & Ambiguity Analysis

- **AC4 edge case:** If a subclass mistakenly defines `ARM_END_SHAPE = "cylinder"` (not in `ALLOWED_END_SHAPES`), `_mesh_str` will raise on every call, not just on invalid overrides. This is intentional "fail-fast" behavior. Implementers must set valid defaults.
- **Type coercion:** The ClassVar value may be stored as str already. No coercion is needed (unlike `_mesh` which coerces to float/int). The value must be compared exactly (case-sensitive) against `allowed`.

### 4. Clarifying Questions

None.

---

## Requirement LJEC-4: `HumanoidSimpleRig` — new ClassVar tuners

### 1. Spec Summary

- **Description:** Six new `ClassVar` attributes are added to `HumanoidSimpleRig` in `asset_generation/python/src/core/rig_models/humanoid_simple.py`. These tuners control multi-segment limb rigs, joint visual geometry, and end-cap primitives.
- **Constraints:** All ClassVars are defined on `HumanoidSimpleRig`, not on concrete enemy subclasses (unless a subclass needs to override the default). Concrete enemy classes (`AnimatedImp`, `AnimatedCarapaceHusk`) inherit these defaults.
- **Assumptions:** ClassVar defaults listed below.
- **Scope:** `asset_generation/python/src/core/rig_models/humanoid_simple.py`.

### 2. Acceptance Criteria

**LJEC-4-AC1 (ARM_SEGMENTS):**
```python
ARM_SEGMENTS: ClassVar[int] = 1
```
Type: `ClassVar[int]`. Default: `1`. Meaning: number of bone segments per arm limb.

**LJEC-4-AC2 (LEG_SEGMENTS):**
```python
LEG_SEGMENTS: ClassVar[int] = 1
```
Type: `ClassVar[int]`. Default: `1`. Meaning: number of bone segments per leg limb.

**LJEC-4-AC3 (ARM_END_SHAPE):**
```python
ARM_END_SHAPE: ClassVar[str] = "none"
```
Type: `ClassVar[str]`. Default: `"none"`. Allowed values: `("none", "sphere", "box")` (from `ALLOWED_END_SHAPES`).

**LJEC-4-AC4 (LEG_END_SHAPE):**
```python
LEG_END_SHAPE: ClassVar[str] = "none"
```
Type: `ClassVar[str]`. Default: `"none"`. Allowed values: `("none", "sphere", "box")`.

**LJEC-4-AC5 (LIMB_JOINT_BALL_SCALE):**
```python
LIMB_JOINT_BALL_SCALE: ClassVar[float] = 1.4
```
Type: `ClassVar[float]`. Default: `1.4`. Meaning: scale factor relative to the limb cylinder radius at which joint spheres are sized. A value of `1.4` means the joint sphere radius = `arm_radius * 1.4`.

**LJEC-4-AC6 (LIMB_JOINT_VISUAL):**
```python
LIMB_JOINT_VISUAL: ClassVar[bool] = True
```
Type: `ClassVar[bool]`. Default: `True`. Meaning: when `True`, joint spheres are added between limb segments. When `False`, no joint spheres are added.

**LJEC-4-AC7 (LIMB_JOINT_VISUAL not surfaced in UI float sliders):** Because `LIMB_JOINT_VISUAL` is `ClassVar[bool]`, `_mesh` skips bool types (`type(base) is bool`), and `animated_build_options._mesh_numeric_defaults` also excludes bools. Therefore `LIMB_JOINT_VISUAL` does NOT appear as a float slider in `BuildControls`.

**LJEC-4-AC8 (ARM_SEGMENTS and LEG_SEGMENTS surface in BuildControls):** Because `ARM_SEGMENTS` and `LEG_SEGMENTS` are `ClassVar[int]` (and not in `_MESH_INT_KEYS_EXCLUDED`), they ARE picked up by `_mesh_numeric_defaults` via `dir(cls)` introspection and appear in `BuildControls` as float-type controls with int coercion. No additional wiring is required.

**LJEC-4-AC9 (tuner reading in rig_definition — ARM_SEGMENTS):** `rig_definition()` must read `ARM_SEGMENTS` via `int(self._mesh("ARM_SEGMENTS"))` (not directly via `getattr`) so that `build_options["mesh"]["ARM_SEGMENTS"]` overrides take effect.

**LJEC-4-AC10 (tuner reading in rig_definition — LEG_SEGMENTS):** Same as LJEC-4-AC9 for `LEG_SEGMENTS`.

### 3. Risk & Ambiguity Analysis

- **LIMB_JOINT_BALL_SCALE default value `1.4`:** The ticket says "scale from existing limb radius via tuners: `LIMB_JOINT_BALL_SCALE` (ratio)". No explicit default numeric value is given in the ticket. The value `1.4` was chosen as a conservative visually-reasonable default. This is flagged as a checkpoint assumption; if the Implementer or art direction requires a different default, this is a trivial change.
- **LIMB_JOINT_VISUAL read path:** Since it is a bool, `_mesh` will not override it from `build_options`. The mesh helper must read it directly: `type(self).LIMB_JOINT_VISUAL` or `self.__class__.LIMB_JOINT_VISUAL`.

### 4. Clarifying Questions

None.

---

## Requirement LJEC-5: `HumanoidSimpleRig.rig_definition()` refactored with `limb_chain`

### 1. Spec Summary

- **Description:** `rig_definition()` in `HumanoidSimpleRig` is refactored to delegate arm and leg bone construction to `limb_chain`. The three non-limb bones (`root`, `spine`, `head`) continue to be constructed directly as `BoneSpec` objects. The result is a `RigDefinition` whose `bones` tuple is built by concatenation.
- **Constraints:**
  - The new implementation must NOT use `rig_from_bone_map` for building the full list (since multi-segment limbs cannot be represented as a dict with unique keys for the non-first segments in order). Non-limb bones may be constructed as individual `BoneSpec` instances.
  - `limb_chain` calls use `int(self._mesh("ARM_SEGMENTS"))` and `int(self._mesh("LEG_SEGMENTS"))`.
  - `rig_from_bone_map` may be used internally for the three non-limb bones if desired, but the final `RigDefinition.bones` is assembled by concatenation.
  - `parent_name` argument to `limb_chain`: `"spine"` for both `arm_l` and `arm_r`; `"root"` for both `leg_l` and `leg_r`.
- **Assumptions:** See checkpoint log for ordering assumption.
- **Scope:** `asset_generation/python/src/core/rig_models/humanoid_simple.py`.

### 2. Acceptance Criteria

**LJEC-5-AC1 (n=1 backward compatibility — bone count):** With `ARM_SEGMENTS=1` and `LEG_SEGMENTS=1` (defaults), `rig_definition()` returns a `RigDefinition` with exactly 7 `BoneSpec` objects.

**LJEC-5-AC2 (n=1 backward compatibility — bone names):** Bone names in order are: `["root", "spine", "head", "arm_l", "arm_r", "leg_l", "leg_r"]` (same as current `rig_from_bone_map` insertion order).

**LJEC-5-AC3 (n=1 backward compatibility — bone positions):** With `ARM_SEGMENTS=1`, `LEG_SEGMENTS=1`, and all RIG_* ClassVars at their defaults, every `BoneSpec`'s `head` and `tail` are numerically identical to the current output. Concretely:
  - `arm_l.head == Vector((0, h * RIG_ARM_SHOULDER_Y, h * RIG_ARM_UPPER_Z))`
  - `arm_l.tail == Vector((0, h * RIG_ARM_OUTER_Y, h * RIG_ARM_LOWER_Z))`
  - (And likewise for `arm_r`, `leg_l`, `leg_r` per current code.)

**LJEC-5-AC4 (n=1 backward compatibility — parent names):** All parent names match the current implementation. `arm_l.parent_name == "spine"`, `leg_l.parent_name == "root"`, `spine.parent_name == "root"`, `head.parent_name == "spine"`, `root.parent_name == None`.

**LJEC-5-AC5 (n=2 arm segments — bone count):** With `ARM_SEGMENTS=2`, `LEG_SEGMENTS=1`, `rig_definition()` returns 9 bones (3 non-limb + 4 arm bones + 2 leg bones).

**LJEC-5-AC6 (n=2 arm segments — names):** With `ARM_SEGMENTS=2`: bones include `arm_l`, `arm_l_1`, `arm_r`, `arm_r_1`.

**LJEC-5-AC7 (n=2 arm segments — positions):** `arm_l.tail == arm_l_1.head` (contiguous). `arm_l_1.tail` == the original `arm_l.tail` from the n=1 case (i.e., the chain end point is unchanged).

**LJEC-5-AC8 (n=2 arm segments — parents):** `arm_l.parent_name == "spine"`, `arm_l_1.parent_name == "arm_l"`.

**LJEC-5-AC9 (bone ordering — parents before children):** For all values of `ARM_SEGMENTS` and `LEG_SEGMENTS` in `[1, 8]`, each bone in `rig_definition().bones` appears after all of its ancestors. This is a constraint imposed by `RigDefinition`'s docstring ("parents must appear before children").

**LJEC-5-AC10 (all existing test_rig_ratios.py tests pass unchanged):** No modifications to `test_rig_ratios.py` are required. The `test_import_humanoid_rig_matches_layout_defaults`, `test_rig_ratio_mesh_override_changes_spine_tail`, and `test_simple_rig_model_rig_ratio_without_mesh` tests must all pass.

### 3. Risk & Ambiguity Analysis

- **Ordering of non-limb vs. limb bones:** The current `rig_from_bone_map` inserts `root, spine, head, arm_l, arm_r, leg_l, leg_r` in that order. The refactored implementation must preserve this order exactly for LJEC-5-AC2/AC10 to hold.
- **`_rig_ratio` vs. `_mesh` for new tuners:** `ARM_SEGMENTS` and `LEG_SEGMENTS` must be read via `self._mesh("ARM_SEGMENTS")` (not `self._rig_ratio`). `_rig_ratio` calls `_mesh` internally when available, so either would work, but since these are int tuners (not float ratios), using `_mesh` directly with `int()` coercion is cleaner and explicit.

### 4. Clarifying Questions

None.

---

## Requirement LJEC-6: Limb mesh helper

### 1. Spec Summary

- **Description:** A new helper function (or set of functions) is created to build the Blender mesh parts for a single multi-segment limb. It appends objects to `self.parts` — cylinders for each segment, optional joint spheres between segments, and an optional end primitive.
- **Constraints:**
  - Location: new file `asset_generation/python/src/core/rig_models/limb_mesh.py`, OR added to `blender_utils.py`. Preferred: dedicated `limb_mesh.py` for testability isolation.
  - Calls `create_cylinder`, `create_sphere`, `create_box` from `blender_utils.py` — these require `bpy` at runtime. In tests, `bpy` is mocked.
  - Does not call `limb_chain` directly; rig and mesh are computed separately from the same segment count.
  - The function must track and return the count of parts it appended, so the caller can update `apply_themed_materials` indexing.
- **Assumptions:** See planning checkpoint on `_arm_part_count` / `_leg_part_count` tracking.
- **Scope:** `asset_generation/python/src/core/rig_models/limb_mesh.py` (new file).

### 2. Acceptance Criteria

**LJEC-6-AC1 (signature):**
```python
def build_limb_parts(
    parts_list: list,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    n: int,
    radius: float,
    euler_rotation,        # mathutils.Euler or compatible
    end_shape: str,        # one of ALLOWED_END_SHAPES
    joint_visual: bool,
    joint_ball_scale: float,
    scale: float = 1.0,
) -> int:
```
Returns the number of parts appended to `parts_list`.

**LJEC-6-AC2 (cylinder count):** Appends exactly `n` cylinders to `parts_list`. Each cylinder covers one linear segment of the limb.

**LJEC-6-AC3 (joint sphere placement — when joint_visual=True):** For each interior joint (between segment `i` and segment `i+1`, for `i` in `0..n-2`), appends one sphere to `parts_list`. Joint sphere center is the midpoint between the end of segment `i` and the start of segment `i+1` (which are the same point in a colinear chain). When `n=1`, there are no interior joints; no spheres are appended.

**LJEC-6-AC4 (joint sphere radius):** Joint sphere radius = `radius * joint_ball_scale`. The sphere is created via `create_sphere` with `scale=(r, r, r)` where `r = radius * joint_ball_scale`.

**LJEC-6-AC5 (joint sphere suppression — when joint_visual=False):** When `joint_visual=False`, no spheres are appended for interior joints regardless of `n`.

**LJEC-6-AC6 (end primitive — sphere):** When `end_shape == "sphere"`, appends one sphere at the `end` position with radius `radius * joint_ball_scale` (same scale as joint spheres for visual consistency).

**LJEC-6-AC7 (end primitive — box):** When `end_shape == "box"`, appends one box at the `end` position with scale `(radius * 2, radius * 2, radius * 2)`.

**LJEC-6-AC8 (end primitive — none):** When `end_shape == "none"`, no end primitive is appended.

**LJEC-6-AC9 (part count return value — n=1, no end shape, joint_visual irrelevant):** Returns `1` (one cylinder, no joints).

**LJEC-6-AC10 (part count return value — n=2, joint_visual=True, end_shape="none"):** Returns `3` (2 cylinders + 1 interior joint sphere).

**LJEC-6-AC11 (part count return value — n=2, joint_visual=True, end_shape="sphere"):** Returns `4` (2 cylinders + 1 interior joint sphere + 1 end sphere).

**LJEC-6-AC12 (part count return value — n=2, joint_visual=False, end_shape="sphere"):** Returns `3` (2 cylinders + 0 interior joint spheres + 1 end sphere).

**LJEC-6-AC13 (part count return value — n=1, joint_visual=True, end_shape="sphere"):** Returns `2` (1 cylinder + 0 interior joint spheres + 1 end sphere).

**LJEC-6-AC14 (scale applied):** All locations and scales passed to `create_*` functions are multiplied by the `scale` parameter (analogous to `_scaled_location` in `BaseAnimatedModel`).

**LJEC-6-AC15 (ValueError on invalid end_shape):** Raises `ValueError` if `end_shape` is not in `ALLOWED_END_SHAPES`.

### 3. Risk & Ambiguity Analysis

- **`euler_rotation` type:** Passing `mathutils.Euler` requires Blender at runtime. In tests, `Euler` is mocked. The function signature accepts the Euler object and passes it through to `create_cylinder` without introspection — this is safe with mocks.
- **Scale semantics:** The `scale` parameter in `build_limb_parts` mirrors `BaseAnimatedModel.scale`. The caller is responsible for passing `self.scale` when calling from an enemy's `build_mesh_parts`.
- **Part ordering:** The function appends parts in this order: for each segment `i` from 0 to n-1: (1) cylinder for segment `i`, then (2) if `joint_visual` and `i < n-1`, sphere for joint after segment `i`. Then after all segments: if `end_shape != "none"`, append the end primitive. This interleaved ordering (cylinder then its trailing joint) is the canonical ordering; `apply_themed_materials` must match.

### 4. Clarifying Questions

None.

---

## Requirement LJEC-7: `AnimatedImp` — fix `apply_themed_materials` for multi-segment arms

### 1. Spec Summary

- **Description:** `AnimatedImp.build_mesh_parts` is refactored to use the limb mesh helper for arms and legs. `apply_themed_materials` is updated to correctly assign materials regardless of segment count.
- **Constraints:**
  - Parts layout: `self.parts[0]` = body, `self.parts[1]` = head. Parts from index 2 onward are: left arm group, right arm group, left leg group, right leg group (each group produced by `build_limb_parts`).
  - `apply_themed_materials` must not rely on hardcoded part counts. It must use the tracked part counts from `build_mesh_parts`.
  - For `AnimatedImp`, the **end-cap sphere** (hand) for each arm must receive `enemy_mats["extra"]` material. All other arm parts (cylinders and joint spheres) receive `enemy_mats["limbs"]`. All leg parts receive `enemy_mats["limbs"]`.
  - `ARM_END_SHAPE` default for `AnimatedImp` is `"sphere"` (the current `hand = create_sphere(...)` behavior must be preserved via the helper's end primitive).
- **Assumptions:** `AnimatedImp.ARM_END_SHAPE` will be set to `"sphere"` (class-level override of `HumanoidSimpleRig`'s `"none"` default).
- **Scope:** `asset_generation/python/src/enemies/animated_imp.py`.

### 2. Acceptance Criteria

**LJEC-7-AC1 (ARM_END_SHAPE override):** `AnimatedImp.ARM_END_SHAPE: ClassVar[str] = "sphere"` is defined on the class.

**LJEC-7-AC2 (part tracking — instance variables):** After `build_mesh_parts` completes, `self` has attributes `_arm_part_count: int` and `_leg_part_count: int` storing the number of parts appended per arm and per leg respectively (the return value of `build_limb_parts` for one arm/leg call).

**LJEC-7-AC3 (apply_themed_materials — body and head):** `self.parts[0]` receives `enemy_mats["body"]`, `self.parts[1]` receives `enemy_mats["head"]`.

**LJEC-7-AC4 (apply_themed_materials — arm groups):** Starting from `part_index = 2`, for each of 2 arm sides (left, right): iterate over `_arm_part_count` parts; the last part in the group (the end-cap sphere) receives `enemy_mats["extra"]`; all preceding parts in the group receive `enemy_mats["limbs"]`. Advance `part_index` by `_arm_part_count` after each arm.

**LJEC-7-AC5 (apply_themed_materials — leg groups):** After both arm groups, for each of 2 leg sides: iterate over `_leg_part_count` parts; all parts receive `enemy_mats["limbs"]`. Advance `part_index` by `_leg_part_count` after each leg.

**LJEC-7-AC6 (no IndexError with ARM_SEGMENTS=2):** `AnimatedImp` built with `ARM_SEGMENTS=2`, `LEG_SEGMENTS=2` completes `build_mesh_parts` and `apply_themed_materials` without raising `IndexError` or any other exception.

**LJEC-7-AC7 (no IndexError with ARM_SEGMENTS=1 — regression):** `AnimatedImp` built with default `ARM_SEGMENTS=1`, `LEG_SEGMENTS=1` completes `build_mesh_parts` and `apply_themed_materials` without raising `IndexError`. This is the existing behavior and must not regress.

**LJEC-7-AC8 (part count with ARM_SEGMENTS=1, LIMB_JOINT_VISUAL=True, ARM_END_SHAPE="sphere"):** `_arm_part_count == 2` (1 cylinder + 0 interior joints + 1 end sphere). Total parts = 2 (body+head) + 2*2 (arms) + 2*1 (legs) = 8. Prior to this change, `self.parts` had 8 objects; regression check should count 8.

**LJEC-7-AC9 (part count with ARM_SEGMENTS=2, LIMB_JOINT_VISUAL=True, ARM_END_SHAPE="sphere"):** `_arm_part_count == 4` (2 cylinders + 1 interior joint sphere + 1 end sphere). `_leg_part_count == 1` (1 cylinder). Total parts = 2 + 2*4 + 2*1 = 12.

**LJEC-7-AC10 (LEG_END_SHAPE default for AnimatedImp):** `AnimatedImp.LEG_END_SHAPE` is NOT overridden; it inherits `"none"` from `HumanoidSimpleRig`. No end primitive is appended to leg groups.

### 3. Risk & Ambiguity Analysis

- **"last part in the group" for extra material:** AC4 identifies the end-cap sphere as the last part when `ARM_END_SHAPE="sphere"`. This requires the caller to know which is the last part. The safest implementation: apply `enemy_mats["limbs"]` to `parts[i]` for all but the last, then `enemy_mats["extra"]` to `parts[i + _arm_part_count - 1]`. This is only correct when `end_shape="sphere"` (i.e., an end cap is guaranteed). If `ARM_END_SHAPE="none"`, `AnimatedImp` would have no hand at all — this is an edge case for `AnimatedImp` where it should be noted that `ARM_END_SHAPE` must not be `"none"` if `extra` material assignment is expected.
- **`LIMB_JOINT_VISUAL` default:** `True` by default. For `AnimatedImp` single-segment arms, `LIMB_JOINT_VISUAL=True` has no effect (no interior joints with `n=1`). No override needed.

### 4. Clarifying Questions

None.

---

## Requirement LJEC-8: `AnimatedCarapaceHusk` — defaults and `apply_themed_materials` stability

### 1. Spec Summary

- **Description:** `AnimatedCarapaceHusk.build_mesh_parts` is refactored to use the limb mesh helper. `apply_themed_materials` must remain correct: `parts[0]` = body material, `parts[1]` = head material, `parts[2:]` = limbs material (all remaining parts, regardless of count).
- **Constraints:**
  - `AnimatedCarapaceHusk.ARM_END_SHAPE` is explicitly set to `"none"` (default behavior: no hand sphere; this matches current behavior where `AnimatedCarapaceHusk` has no hand sphere).
  - `apply_themed_materials` for `AnimatedCarapaceHusk` may continue to use the simple `for part in self.parts[2:]` pattern since all limb parts (segments + joint spheres) receive the same "limbs" material.
  - `LEG_END_SHAPE` inherits `"none"` from `HumanoidSimpleRig` (no override needed).
- **Assumptions:** `AnimatedCarapaceHusk` does not need `_arm_part_count`/`_leg_part_count` because its material assignment is uniform across all `parts[2:]`.
- **Scope:** `asset_generation/python/src/enemies/animated_carapace_husk.py`.

### 2. Acceptance Criteria

**LJEC-8-AC1 (ARM_END_SHAPE override):** `AnimatedCarapaceHusk.ARM_END_SHAPE: ClassVar[str] = "none"` is explicitly defined on the class (even though it matches the parent default — explicit is better than implicit for clarity).

**LJEC-8-AC2 (build without error — default settings):** `AnimatedCarapaceHusk` built with all defaults (`ARM_SEGMENTS=1`, `LEG_SEGMENTS=1`, `ARM_END_SHAPE="none"`) completes `build_mesh_parts` without error.

**LJEC-8-AC3 (apply_themed_materials — simple slice):** `apply_themed_materials` assigns `enemy_mats["body"]` to `parts[0]`, `enemy_mats["head"]` to `parts[1]`, and `enemy_mats["limbs"]` to every element of `parts[2:]`. This pattern is unchanged from the current implementation.

**LJEC-8-AC4 (no IndexError with default segments):** `apply_themed_materials` does not raise `IndexError` with the default single-segment settings.

**LJEC-8-AC5 (part count — default settings):** With `ARM_SEGMENTS=1`, `LEG_SEGMENTS=1`, `ARM_END_SHAPE="none"`, `LIMB_JOINT_VISUAL=True`: 2 (body+head) + 2*1 (arms, no end shape, no interior joints) + 2*1 (legs) = 6 parts total. This matches current behavior (current `build_mesh_parts` appends: body, head, arm_l, arm_r, leg_l, leg_r = 6 parts).

**LJEC-8-AC6 (regression — all existing tests pass):** All existing tests for `AnimatedCarapaceHusk` in `test_animated_enemy_classes.py` pass without modification.

### 3. Risk & Ambiguity Analysis

- **`apply_themed_materials` uses `self.parts[2:]` directly:** This pattern is robust because it doesn't hardcode a count — it assigns limb material to ALL parts after the first two. Adding joint spheres (when `ARM_SEGMENTS>1` and `LIMB_JOINT_VISUAL=True`) to `self.parts` will automatically receive the limbs material. No changes to `apply_themed_materials` logic are needed for `AnimatedCarapaceHusk`.

### 4. Clarifying Questions

None.

---

## Requirement LJEC-9: Backward compatibility guarantee (regression contract)

### 1. Spec Summary

- **Description:** With all ClassVar tuners at their defaults (`ARM_SEGMENTS=1`, `LEG_SEGMENTS=1`, `ARM_END_SHAPE="none"`, `LEG_END_SHAPE="none"`, `LIMB_JOINT_BALL_SCALE=1.4`, `LIMB_JOINT_VISUAL=True`), the output of `HumanoidSimpleRig.rig_definition()` must be numerically identical to the current pre-refactor implementation.
- **Constraints:** The n=1 identity holds for the rig only. Mesh output may differ slightly due to helper refactoring, but must be semantically equivalent (same primitives, same positions, same materials).
- **Assumptions:** None.
- **Scope:** `HumanoidSimpleRig`, `AnimatedImp`, `AnimatedCarapaceHusk`.

### 2. Acceptance Criteria

**LJEC-9-AC1:** All three tests in `asset_generation/python/tests/core/test_rig_ratios.py` pass without modification after the refactor.

**LJEC-9-AC2:** The `test_animated_enemy_classes.py` tests (all existing, pre-existing-to-this-ticket) pass without modification.

**LJEC-9-AC3:** The full pytest suite (`uv run pytest asset_generation/python/tests/ -q`) exits with code 0 after all tasks are complete.

**LJEC-9-AC4 (rig n=1 identity — numeric):** For `body_height=1.0` with all defaults, the 7-bone list from the refactored `rig_definition()` equals the current output. Specifically, for `arm_l`:
  - `head == Vector((0, 1.0 * 0.2, 1.0 * 0.6))` = `Vector((0, 0.2, 0.6))`
  - `tail == Vector((0, 1.0 * 0.5, 1.0 * 0.3))` = `Vector((0, 0.5, 0.3))`

### 3. Risk & Ambiguity Analysis

- The primary regression risk is in `rig_definition()` refactoring: if `limb_chain` interpolation introduces floating-point differences, tests using `==` on `Vector` objects may fail. Since the n=1 case does not interpolate (segment 0 spans the full head→tail), there is no floating-point accumulation. This risk is Low.

### 4. Clarifying Questions

None.

---

## Requirement LJEC-10: Frontend auto-surface for `ARM_SEGMENTS` / `LEG_SEGMENTS`

### 1. Spec Summary

- **Description:** `ARM_SEGMENTS` and `LEG_SEGMENTS`, being `ClassVar[int]` on `HumanoidSimpleRig`, will be discovered automatically by the existing `_mesh_numeric_defaults` introspection in `animated_build_options.py` and appear in the `BuildControls` panel as numeric controls.
- **Constraints:** No new Python or TypeScript code is required to wire these controls. The existing pipeline handles `ClassVar[int]` discovery, float-type control emission, and int coercion.
- **Assumptions:** `ARM_SEGMENTS` and `LEG_SEGMENTS` are not in `_MESH_INT_KEYS_EXCLUDED`.
- **Scope:** `asset_generation/python/src/utils/animated_build_options.py` (read-only for this requirement — no modifications needed).

### 2. Acceptance Criteria

**LJEC-10-AC1 (discovery):** After adding `ARM_SEGMENTS: ClassVar[int] = 1` and `LEG_SEGMENTS: ClassVar[int] = 1` to `HumanoidSimpleRig`, calling `_mesh_numeric_defaults("imp")` returns a dict containing `"ARM_SEGMENTS": 1` and `"LEG_SEGMENTS": 1`.

**LJEC-10-AC2 (control emission):** `animated_build_controls_for_api()` includes for the `"imp"` slug a float-type control entry with `"key": "ARM_SEGMENTS"` and `"default": 1.0`.

**LJEC-10-AC3 (int coercion in options_for_enemy):** When `options_for_enemy("imp", {"mesh": {"ARM_SEGMENTS": "2.7"}})` is called, the resulting `build_options["mesh"]["ARM_SEGMENTS"]` is `3` (int coercion: `int(round(2.7)) == 3`).

**LJEC-10-AC4 (no frontend task required):** The `BuildControls.tsx` component requires no modification. The slider appears automatically because the backend API response for `animated_build_controls` will include the new keys.

**LJEC-10-AC5 (not in exclusion list):** `_MESH_INT_KEYS_EXCLUDED` in `animated_build_options.py` must not contain `"ARM_SEGMENTS"` or `"LEG_SEGMENTS"`.

### 3. Risk & Ambiguity Analysis

- **UI quality:** The auto-surfaced control will be a float slider (e.g., `min: 0.05, max: 5.0, step: 0.05`) with int coercion, rather than a dedicated integer stepper UI. This is not ideal for the user but satisfies the AC. A future improvement (not in scope) could add a dedicated `int` type to the controls system.
- **`LIMB_JOINT_BALL_SCALE` also surfaced:** `LIMB_JOINT_BALL_SCALE: ClassVar[float]` will also appear in `BuildControls` automatically. This is correct behavior and requires no special handling.

### 4. Clarifying Questions

None.

---

## Non-Functional Requirements

### NFR-1: Test harness compatibility

All new pure-logic modules (`limb_chain.py`, `limb_mesh.py`) must be importable under `uv run pytest asset_generation/python/tests/` with the existing `conftest.py` → `ensure_blender_stubs()` mock setup. No new `conftest.py` changes are required to run pure-logic tests; mesh helper tests that invoke `create_*` functions will rely on the existing bpy mock (functions return `MagicMock` objects, which are appendable to lists).

### NFR-2: No Godot changes

All new and modified files are under `asset_generation/python/`. Zero Godot/GDScript files are modified.

### NFR-3: Ordering invariant for RigDefinition

All `RigDefinition.bones` tuples emitted by `rig_definition()` must satisfy the invariant: for every `BoneSpec` with a non-None `parent_name`, the parent bone appears earlier in the tuple. This is a pre-existing contract from `RigDefinition`'s docstring and must hold for all `n` in `[1, 8]`.

### NFR-4: No silent integer truncation

`limb_chain` must use integer division or explicit `int(n)` before clamping, not implicit float truncation, to ensure `limb_chain(h, t, 1.9, "arm_l")` either raises `TypeError` (preferred, since `n: int` is typed) or clamps correctly.

---

## Summary: Acceptance Criteria → Ticket AC mapping

| Ticket AC bullet | Covered by |
|---|---|
| `limb_chain(head, tail, n, name)` returns exactly `n` `BoneSpec`s; first segment name = legacy bone name; subsequent are `name_1`, `name_2`…; parent is previous segment; positions interpolate linearly | LJEC-1, LJEC-2 |
| With `ARM_SEGMENTS=1` / `LEG_SEGMENTS=1`, `rig_definition()` produces identical bone list; all `test_rig_ratios.py` assertions pass | LJEC-5, LJEC-9 |
| `BaseAnimatedModel._mesh_str("ARM_END_SHAPE")` returns string value if present and valid, class default otherwise; invalid raises `ValueError` | LJEC-3 |
| `AnimatedImp` builds without error with `ARM_SEGMENTS=2`, `LEG_SEGMENTS=2`; armature contains `arm_l` and `arm_l_1`; `apply_themed_materials` does not raise `IndexError` | LJEC-5-AC6, LJEC-7 |
| `AnimatedCarapaceHusk` builds without error with default settings; passes all existing tests | LJEC-8 |
| All existing `asset_generation/python/tests` pass | LJEC-9-AC3 |
| `ARM_SEGMENTS` / `LEG_SEGMENTS` surface in `BuildControls` automatically via ClassVar[int] introspection | LJEC-4-AC8, LJEC-10 |
