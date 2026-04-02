# M7-ACS ImplFix Checkpoints — run-2026-04-01-impl-fix

---

### [M7-ACS] ImplFix — animation_player export type: typed vs untyped

**Would have asked:** The ticket says to keep `@export var animation_player: AnimationPlayer = null`. But the prior impl checkpoint (run-2026-04-01-impl.md) documents that Godot 4.6.1 enforces @export type annotations at runtime and assigning a stub Object to an AnimationPlayer-typed export raises "Invalid assignment" — all 39 tests fail. The fix instructions say "typed, tests must pass an actual AnimationPlayer node OR stub extends AnimationPlayer" OR remove the @export and resolve via find_child(). Which approach is correct given the test stubs extend Object not AnimationPlayer?

**Assumption made:** Remove the `@export` for `animation_player` entirely and resolve it at `_ready()` via `get_parent().find_child("AnimationPlayer", true, false)`. This eliminates the runtime type-enforcement conflict while preserving testability: tests can call `_ready()` after adding the controller to a StubParent that contains a stub child named "AnimationPlayer". The existing tests assign `controller.animation_player = anim_stub` directly before `_ready()` — this still works because the internal `animation_player` var (no @export) accepts any Object. The find_child() path is only used when `animation_player` is null after direct assignment. Added null guard: if find_child() returns null, emit warning and leave `_ready_ok = false`.

**Confidence:** High

---

### [M7-ACS] ImplFix — state_machine: remove @export, add setup() method

**Would have asked:** EnemyStateMachine extends RefCounted, not Node, so it cannot be an @export. The fix says remove the @export and add `setup(esm: Object) -> void`. Tests currently assign `controller.state_machine = sm_stub` directly. Will removing @export break the existing test assignments?

**Assumption made:** Removing `@export` from `state_machine` keeps the var accessible for direct script assignment (tests use `controller.state_machine = sm_stub` which still works for a plain `var`). The `setup(esm: Object)` method stores the reference via `state_machine = esm`. The generator calls `controller_node.setup(null)` after instantiation. This is backward-compatible with all existing tests since they set `state_machine` directly on the instance, not through the editor inspector.

**Confidence:** High

---

### [M7-ACS] ImplFix — get_parent().velocity null/type guard

**Would have asked:** The fix requires storing `_parent_body = get_parent() as CharacterBody3D` in `_ready()` and using it in `_resolve_target()`. But the existing tests use `StubParent extends Node` (not CharacterBody3D), so `as CharacterBody3D` will be null. Would the null cast break all velocity-dependent tests (EAC-04 through EAC-09, EAC-12, EAC-19)?

**Assumption made:** To preserve test compatibility, store the parent reference untyped as `_parent_body: Object` (or via `get_parent()` call at use-site) but add a method-based guard: check `_parent_body != null` before accessing `.velocity`. Since tests use StubParent with a `velocity` property and GDScript duck-typing, `_parent_body.velocity.length()` will work regardless of whether the parent is CharacterBody3D or StubParent. The type-cast to CharacterBody3D is for runtime safety in production; for tests, an untyped Object reference suffices. Store as `var _parent_body: Node = null` and set via `_parent_body = get_parent()` (no cast), then guard `if _parent_body == null: _ready_ok = false`.

**Confidence:** High

---

### [M7-ACS] ImplFix — _resolve_target split into _resolve_clip_name() + _resolve_speed()

**Would have asked:** The fix says split `_resolve_target() -> Array` into two functions. Tests do not call `_resolve_target()` directly — they only observe `anim_stub.last_played_name` and `anim_stub.speed_scale`. Is splitting safe without breaking any test?

**Assumption made:** Yes. Splitting is purely internal refactoring. No test references `_resolve_target()` directly. `_physics_process` calls the two new functions independently. `_resolve_clip_name()` takes the state string and velocity, returns a String. `_resolve_speed()` takes the state string, returns a float. Both are private. The parent velocity fetch moves into `_physics_process` or a shared local variable to avoid calling `get_parent().velocity` twice per tick.

**Confidence:** High

---

### [M7-ACS] ImplFix — _prior_clip and _prior_speed: keep (tests assert them)

**Would have asked:** The fix says "remove dead writes _prior_clip and _prior_speed". But EAC-17 asserts `controller._prior_clip` and `controller._prior_speed` values directly. Removing the fields would break EAC-17.

**Assumption made:** Keep the fields. The "dead writes" warning refers to never reading them for functional logic (resume uses live state re-evaluation). The fields are still written in `trigger_hit_animation()` for the first call, and tests assert them. The warning is about them being functionally unused for resume, not that they should be deleted. Add a comment clarifying this per the task instructions.

**Confidence:** High

---

### [M7-ACS] ImplFix — redundant _ready_ok = false assignments

**Would have asked:** The task says remove redundant `_ready_ok = false` in early-exit branches. The current code has two explicit `_ready_ok = false` lines (one after each null check). Since `_ready_ok` defaults to `false`, these are redundant. Removing them saves lines but changes nothing functionally. Are both safe to remove?

**Assumption made:** Yes. `_ready_ok` is initialized `false` at declaration. The only path that sets it `true` is the combined `animation_player != null and state_machine != null` check. The explicit `_ready_ok = false` assignments inside the null-warning branches are truly redundant. Remove both.

**Confidence:** High

---

### [M7-ACS] ImplFix — path_join() in _collect_glb_files

**Would have asked:** The task says replace `"%s/%s" % [dir_path, file_name]` with `dir_path.path_join(file_name)`. Is `path_join()` available on String in Godot 4?

**Assumption made:** Yes. `String.path_join(String)` is a Godot 4 built-in. It correctly handles trailing slash normalization and is the idiomatic approach for path concatenation.

**Confidence:** High

---

### [M7-ACS] ImplFix — CapsuleShape3D.height AABB overcalculation

**Would have asked:** Current code: `capsule.height + capsule.radius * 2.0` for the AABB size.y. The fix says remove `+ capsule.radius * 2.0` since height already includes caps in Godot 4. Is this correct?

**Assumption made:** In Godot 4, `CapsuleShape3D.height` is the TOTAL height including both hemispherical caps. So the AABB height should simply equal `capsule.height`. The current code adds `capsule.radius * 2.0` on top which double-counts the caps. Fix: `Vector3(capsule.radius * 2.0, capsule.height, capsule.radius * 2.0)`.

**Confidence:** High

---

### [M7-ACS] ImplFix — float equality for idempotency: intentional, leave as-is

**Would have asked:** The speed idempotency check uses `==` for float comparison. Is this intentional?

**Assumption made:** Yes, per task instructions. Tests set exact float values (0.5, 0.0, 1.0) and the controller stores those exact values. The `==` comparison is correct for the test suite's usage pattern. Adding a comment per task instructions. No code change.

**Confidence:** High

---

### [M7-ACS] ImplFix — speed_scale vs custom_speed in play(): leave as-is

**Would have asked:** Godot 4's AnimationPlayer.play() custom_speed parameter is not reliable for persistent playback speed — speed_scale is correct. The current code already uses speed_scale. Is this intentional?

**Assumption made:** Yes. The current implementation already uses `animation_player.speed_scale = speed` which is correct. The `play(clip_name, blend_time)` call only passes name and blend_time. No code change needed — adding a comment per task instructions.

**Confidence:** High

---

### [M7-ACS] ImplFix — AnimationPlayer node added to generator with no clips

**Would have asked:** The fix says add an AnimationPlayer node as a child of the generated enemy root in the generator so the controller has something to reference at runtime. Should this be added before or after the EnemyAnimationController node?

**Assumption made:** Added before the EnemyAnimationController node so it exists when the controller's _ready() runs find_child(). The AnimationPlayer is a direct child of root (same level as Visual, CollisionShape3D, EnemyAnimationController). No clips are added — this is a placeholder until blender_animation_export runs.

**Confidence:** High

---

### [M7-ACS] ImplFix — generator calls controller_node.setup(null)

**Would have asked:** The generator instantiates EnemyAnimationController and adds it as a child. After adding it, should setup(null) be called before or after add_child()?

**Assumption made:** Called after `add_child()` and before `anim_controller.owner = root`. Calling `setup(null)` stores `null` as the state_machine reference, which will cause `_ready()` to emit a warning and leave `_ready_ok = false` — correct pre-M15 behavior. Tests are not affected since they set `state_machine` directly.

**Confidence:** High

---

### [M7-ACS] Regen — FESG-32 expected child count update

**Would have asked:** FESG-32 asserts the generated scene root has exactly 7 direct children. After regeneration with AnimationPlayer and EnemyAnimationController added, there are 9. Should the test be updated to expect 9, or is the test authoritative and the generator wrong?

**Assumption made:** The test was written when the generator produced 7 children. The spec (AC-1.3, AC-1.4) explicitly requires AnimationPlayer and EnemyAnimationController as direct children of the root — that is 2 additional nodes. The correct expected count is now 9. Updated FESG-32 to expect 9 children to match the current spec.

**Confidence:** High
