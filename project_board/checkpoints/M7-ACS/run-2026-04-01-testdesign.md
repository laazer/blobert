# M7-ACS TestDesign Checkpoints — run-2026-04-01-testdesign

---

### [M7-ACS] TestDesign — test file path: spec says tests/unit/ but project uses tests/scripts/enemy/

**Would have asked:** ACS-9 specifies the test file path as `tests/unit/test_enemy_animation_controller.gd`, but no `tests/unit/` directory exists in the project. All existing enemy tests live under `tests/scripts/enemy/`. The task brief also references `tests/scripts/enemies/` (plural). Which path is authoritative?

**Assumption made:** Use `tests/scripts/enemy/test_enemy_animation_controller.gd` — matching the actual project convention (singular `enemy`, under `tests/scripts/`). The test runner discovers all `test_*.gd` files recursively, so any path under `tests/` works. Using the existing convention keeps the suite cohesive. The `tests/unit/` path in the spec is treated as a logical grouping label, not a literal directory requirement.

**Confidence:** High

---

### [M7-ACS] TestDesign — stub type compatibility: @export var animation_player: AnimationPlayer

**Would have asked:** ACS-8 notes that GDScript `@export var animation_player: AnimationPlayer` accepts stub assignment at runtime via duck typing. However, the test file must assign a plain RefCounted-based inner class to that export. Will GDScript emit a type error at assignment time in headless mode?

**Assumption made:** GDScript does not enforce export type annotations at runtime assignment (only in the editor inspector). The stub will be assigned via `controller.animation_player = stub_instance` after instantiation. This is confirmed by the spec note in ACS-8 section 3. Tests define the stub as a plain Object (extends Object via inner class) and assign it. No type error will occur at runtime.

**Confidence:** High

---

### [M7-ACS] TestDesign — EnemyAnimationController requires Node tree for _ready() and _physics_process()

**Would have asked:** `EnemyAnimationController` extends `Node`, which means `_ready()` and `_physics_process()` are lifecycle callbacks driven by the scene tree. In headless tests with no scene tree, `_ready()` will not be called automatically. How should tests invoke initialization and per-frame logic?

**Assumption made:** Tests call `_ready()` and `_physics_process(0.016)` directly as regular methods. GDScript allows calling `_ready()` explicitly even without a scene tree — it is just a regular function. `_physics_process(delta)` likewise takes a float argument. This pattern avoids any scene tree dependency and keeps tests fully headless. The stub parent (for velocity reads) is handled by overriding `get_parent()` — since EnemyAnimationController extends Node, it has `get_parent()`, but in headless instantiation `get_parent()` returns null. The controller must be tested with a mock parent. Resolution: inject velocity directly via a stub that the controller reads through the parent reference, OR use a lightweight inner-class fake parent. Since we cannot override `get_parent()` in GDScript, the implementation will need to call `get_parent()` at runtime. In tests, we attach the controller as a child of a fake Node that has a `velocity` property. We create a minimal inline Node subclass with a velocity field.

**Confidence:** Medium

---

### [M7-ACS] TestDesign — parent Node with velocity property in headless tests

**Would have asked:** ACS-4 resolution reads `get_parent().velocity`. In headless tests with no scene tree, `get_parent()` on a bare Node instance returns null (the node is not added to a tree). How do tests provide a parent with a velocity property without adding nodes to the scene tree?

**Assumption made:** Create a `StubParent` inner class (extends Node) with a `var velocity: Vector3` property. In each test, create a `StubParent` instance and call `controller.add_child(stub_parent)` is NOT possible headlessly. Instead, the test calls `stub_parent.add_child(controller)` — adding the controller as a child of the stub parent — which makes `controller.get_parent()` return `stub_parent` WITHOUT requiring a scene tree (Godot's Node.add_child sets the parent pointer even outside a scene tree). This is standard GDScript test practice for Node-based scripts in this project.

**Confidence:** High

---

### [M7-ACS] TestDesign — _ready_ok internal flag access from tests

**Would have asked:** ACS-3 requires the controller to use an internal bool `_ready_ok`. Tests T-ACS-01, T-ACS-02, T-ACS-03 must read this flag. Is it acceptable to read a private/internal variable directly in tests, given GDScript has no true access modifiers?

**Assumption made:** Yes. GDScript has no private enforcement. Tests access `controller._ready_ok` directly. This is consistent with existing test patterns in the project (e.g., `_hit_active`, `_death_latched` are also read directly). The spec explicitly lists these as internal variables tests should inspect.

**Confidence:** High

---

### [M7-ACS] TestDesign — play() call counting for idempotency and latch tests

**Would have asked:** Tests T-ACS-11, T-ACS-12, T-ACS-14 require asserting that `play()` was NOT called on a given tick. How is call-count tracked given the stub is a plain Object?

**Assumption made:** Add a `play_call_count: int = 0` field to `StubAnimationPlayer` that increments on every `play()` call. Tests save the count before a tick, call `_physics_process(0.016)`, then assert count did not increase. This is purely additive to the required stub interface (ACS-8) and does not change the production contract.

**Confidence:** High

---

### [M7-ACS] TestDesign — Death blend time is 0.0 not blend_time export

**Would have asked:** ACS-7 says Death is triggered with `play("Death", 0.0)` (zero blend), not `blend_time`. Test T-ACS-10 must assert exactly `play("Death", 0.0)`. The stub must record the blend argument separately from the clip name.

**Assumption made:** The stub records both `last_played_name: String` and `last_played_blend: float` per the ACS-8 spec. T-ACS-10 asserts `last_played_blend == 0.0` in addition to `last_played_name == "Death"`. This matches the spec exactly.

**Confidence:** High

---

### [M7-ACS] TestDesign — parse error vs runtime failure: EnemyAnimationController not yet implemented

**Would have asked:** The test file uses `EnemyAnimationController` as a typed identifier. Since the implementation file does not exist, GDScript fails to parse the test file entirely (RUNNER ERROR), which crashes the test runner. Should test-break stage tests be allowed to crash the runner, or must they parse cleanly and fail at runtime?

**Assumption made:** Tests must parse cleanly. GDScript parse errors crash the entire runner, breaking all other suites. The correct pattern is to use dynamic loading via `load("res://scripts/enemies/enemy_animation_controller.gd")` and fall back to a failure if the file does not exist. All type annotations that reference `EnemyAnimationController` are replaced with untyped (`var controller`) or the result of `load().new()`. This allows the file to parse at all times. When the implementation does not exist, all 22+ tests fail with a clear message. When the implementation lands, tests pass.

**Confidence:** High

---
