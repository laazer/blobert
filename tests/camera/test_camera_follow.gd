# test_camera_follow.gd
#
# Headless behavioral tests for scripts/camera_follow.gd.
#
# This file is a plain Object subclass. It does not extend Node or SceneTree.
# The entry point is run_all(), which is called by tests/run_tests.gd.
#
# It may also be invoked via the top-level runner:
#   godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd
#
# Design notes:
#   - CameraFollow extends Camera2D. CameraFollow.new() creates a Camera2D subclass
#     instance without requiring a SceneTree. Godot loads all engine classes (including
#     Camera2D) in headless mode, so this is safe.
#   - _ready() is called explicitly with node._ready() because automatic dispatch
#     only occurs when the node is added to the scene tree.
#   - After each test the node is freed via node.free() to avoid accumulating
#     orphan nodes in the headless process.
#   - NF-03 (no movement math) is NOT tested here — it is a static analysis concern
#     owned by the Static QA Agent. See CHECKPOINTS.md [M1-004] Test Designer —
#     NF-03 not unit-testable; skipped.
#
# Spec coverage:
#   SPEC-37 — File/class structure: instantiation, Camera2D subclass identity
#   SPEC-38 — Exported configuration parameter defaults (pre-_ready())
#   SPEC-39 — _ready() initialization: all twelve Camera2D property assignments
#   SPEC-40 — Smoothing behavior: headless-verifiable ACs (AC-40.5, AC-40.6)
#   SPEC-41 — Drag margin behavior: headless-verifiable ACs (AC-41.1 through AC-41.7)
#   SPEC-42 — Level bounds limiting: headless-verifiable ACs (AC-42.1 through AC-42.6)
#   SPEC-45 — Non-functional: typeof() type checks for all @export vars (AC-45.1/NF-01,
#              AC-45.2/NF-02 proxies); NF-03 deferred to Static QA

class_name CameraFollowTests
extends Object

# ---------------------------------------------------------------------------
# EPSILON for floating-point comparisons.
# Matches the project-wide constant used in all test files.
# ---------------------------------------------------------------------------
const EPSILON: float = 1e-4

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _approx_eq(a: float, b: float) -> bool:
	return abs(a - b) < EPSILON


func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)


func _assert_true(condition: bool, test_name: String) -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected true, got false")


func _assert_false(condition: bool, test_name: String) -> void:
	if not condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected false, got true")


func _assert_approx(a: float, b: float, test_name: String) -> void:
	if _approx_eq(a, b):
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b) + " (delta " + str(abs(a - b)) + ")")


func _assert_int_eq(a: int, b: int, test_name: String) -> void:
	if a == b:
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b))


func _assert_type_eq(value: Variant, expected_type: int, test_name: String) -> void:
	var actual_type: int = typeof(value)
	if actual_type == expected_type:
		_pass(test_name)
	else:
		_fail(test_name, "got Variant.Type " + str(actual_type) + " expected " + str(expected_type))


# ===========================================================================
# SPEC-37 — File and class structure
# ===========================================================================

# AC-37.4 (proxy): CameraFollow is resolvable as a class name in headless mode.
# If camera_follow.gd is missing or malformed, CameraFollow.new() will either
# fail or return null. This test confirms the class can be instantiated.
func test_spec37_camera_follow_class_is_resolvable() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_true(node != null,
		"spec37 — CameraFollow class is resolvable; CameraFollow.new() returns non-null")
	node.free()


# AC-37.4 (inheritance): CameraFollow is a Camera2D subclass.
# is_class("Camera2D") on a CameraFollow instance must return true because
# CameraFollow extends Camera2D.
func test_spec37_camera_follow_is_camera2d_subclass() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_true(node.is_class("Camera2D"),
		"spec37 — CameraFollow.is_class(\"Camera2D\") returns true")
	node.free()


# AC-37.4: CameraFollow is also a Node2D (Camera2D extends Node2D).
func test_spec37_camera_follow_is_node2d() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_true(node.is_class("Node2D"),
		"spec37 — CameraFollow.is_class(\"Node2D\") returns true")
	node.free()


# AC-37.5 (proxy): CameraFollow has a callable _ready method.
# The class must define _ready() — we verify it is callable, which means the
# method exists on the instance (not just on the base Camera2D class as a no-op).
func test_spec37_ready_method_is_callable() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_true(node.has_method("_ready"),
		"spec37 — CameraFollow has a _ready() method defined")
	node.free()


# ===========================================================================
# SPEC-38 — Exported configuration parameter defaults (pre-_ready())
# ===========================================================================
# These tests read each @export var before calling _ready() to verify the
# declared default values are correct as initialized by GDScript's field
# initializer. AC-38.1 through AC-38.12 are covered below.

# AC-38.1: smoothing_enabled default is true.
func test_spec38_default_smoothing_enabled() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_true(node.smoothing_enabled == true,
		"spec38 — smoothing_enabled default is true")
	node.free()


# AC-38.2: smoothing_speed default is 5.0 (tolerance EPSILON).
func test_spec38_default_smoothing_speed() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_approx(node.smoothing_speed, 5.0,
		"spec38 — smoothing_speed default is 5.0")
	node.free()


# AC-38.3: drag_horizontal default is true.
func test_spec38_default_drag_horizontal() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_true(node.drag_horizontal == true,
		"spec38 — drag_horizontal default is true")
	node.free()


# AC-38.4: drag_vertical default is false.
func test_spec38_default_drag_vertical() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_false(node.drag_vertical,
		"spec38 — drag_vertical default is false")
	node.free()


# AC-38.5: drag_left_margin default is 0.2 (tolerance EPSILON).
func test_spec38_default_drag_left_margin() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_approx(node.follow_drag_left_margin, 0.2,
		"spec38 — follow_drag_left_margin default is 0.2")
	node.free()


# AC-38.6: drag_right_margin default is 0.2 (tolerance EPSILON).
func test_spec38_default_drag_right_margin() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_approx(node.follow_drag_right_margin, 0.2,
		"spec38 — follow_drag_right_margin default is 0.2")
	node.free()


# AC-38.7: drag_top_margin default is 0.2 (tolerance EPSILON).
func test_spec38_default_drag_top_margin() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_approx(node.follow_drag_top_margin, 0.2,
		"spec38 — follow_drag_top_margin default is 0.2")
	node.free()


# AC-38.8: drag_bottom_margin default is 0.2 (tolerance EPSILON).
func test_spec38_default_drag_bottom_margin() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_approx(node.follow_drag_bottom_margin, 0.2,
		"spec38 — follow_drag_bottom_margin default is 0.2")
	node.free()


# AC-38.9: limit_left default is -10000000 (exact integer equality).
func test_spec38_default_limit_left() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_int_eq(node.follow_limit_left, -10000000,
		"spec38 — follow_limit_left default is -10000000")
	node.free()


# AC-38.10: limit_right default is 10000000 (exact integer equality).
func test_spec38_default_limit_right() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_int_eq(node.follow_limit_right, 10000000,
		"spec38 — follow_limit_right default is 10000000")
	node.free()


# AC-38.11: limit_top default is -10000000 (exact integer equality).
func test_spec38_default_limit_top() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_int_eq(node.follow_limit_top, -10000000,
		"spec38 — follow_limit_top default is -10000000")
	node.free()


# AC-38.12: limit_bottom default is 10000000 (exact integer equality).
func test_spec38_default_limit_bottom() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_int_eq(node.follow_limit_bottom, 10000000,
		"spec38 — follow_limit_bottom default is 10000000")
	node.free()


# AC-38.16: Each @export variable is mutable — write a new value and read it back.
# Checked for one representative of each type (bool, float, int) to keep the
# suite focused; mutation tests for all twelve are in the adversarial suite.
func test_spec38_smoothing_enabled_is_mutable() -> void:
	var node: CameraFollow = CameraFollow.new()
	node.smoothing_enabled = false
	_assert_false(node.smoothing_enabled,
		"spec38 — smoothing_enabled is mutable; assigned false, read back false")
	node.free()


func test_spec38_smoothing_speed_is_mutable() -> void:
	var node: CameraFollow = CameraFollow.new()
	node.smoothing_speed = 12.5
	_assert_approx(node.smoothing_speed, 12.5,
		"spec38 — smoothing_speed is mutable; assigned 12.5, read back 12.5")
	node.free()


func test_spec38_limit_right_is_mutable() -> void:
	var node: CameraFollow = CameraFollow.new()
	node.follow_limit_right = 800
	_assert_int_eq(node.follow_limit_right, 800,
		"spec38 — follow_limit_right is mutable; assigned 800, read back 800")
	node.free()


# ===========================================================================
# SPEC-39 — _ready() initialization (post-_ready() Camera2D property values)
# ===========================================================================
# Each test: instantiate CameraFollow, call _ready() explicitly, then read the
# Camera2D built-in property (not the @export var) and assert the expected value.
# AC-39.1 through AC-39.12 are covered below. Additional non-default tests cover
# AC-39.13 (modified export value applied by _ready()).

# AC-39.1: After _ready(), position_smoothing_enabled == true (default).
func test_spec39_ready_sets_position_smoothing_enabled_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_true(node.position_smoothing_enabled == true,
		"spec39 — after _ready(), position_smoothing_enabled is true (default)")
	node.free()


# AC-39.2: After _ready(), position_smoothing_speed == 5.0 (default, tolerance EPSILON).
func test_spec39_ready_sets_position_smoothing_speed_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_approx(node.position_smoothing_speed, 5.0,
		"spec39 — after _ready(), position_smoothing_speed is 5.0 (default)")
	node.free()


# AC-39.3: After _ready(), drag_horizontal_enabled == true (default).
func test_spec39_ready_sets_drag_horizontal_enabled_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_true(node.drag_horizontal_enabled == true,
		"spec39 — after _ready(), drag_horizontal_enabled is true (default)")
	node.free()


# AC-39.4: After _ready(), drag_vertical_enabled == false (default).
func test_spec39_ready_sets_drag_vertical_enabled_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_false(node.drag_vertical_enabled,
		"spec39 — after _ready(), drag_vertical_enabled is false (default)")
	node.free()


# AC-39.5: After _ready(), drag_left_margin == 0.2 (default, tolerance EPSILON).
func test_spec39_ready_sets_drag_left_margin_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_approx(node.drag_left_margin, 0.2,
		"spec39 — after _ready(), drag_left_margin is 0.2 (default)")
	node.free()


# AC-39.6: After _ready(), drag_right_margin == 0.2 (default, tolerance EPSILON).
func test_spec39_ready_sets_drag_right_margin_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_approx(node.drag_right_margin, 0.2,
		"spec39 — after _ready(), drag_right_margin is 0.2 (default)")
	node.free()


# AC-39.7: After _ready(), drag_top_margin == 0.2 (default, tolerance EPSILON).
func test_spec39_ready_sets_drag_top_margin_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_approx(node.drag_top_margin, 0.2,
		"spec39 — after _ready(), drag_top_margin is 0.2 (default)")
	node.free()


# AC-39.8: After _ready(), drag_bottom_margin == 0.2 (default, tolerance EPSILON).
func test_spec39_ready_sets_drag_bottom_margin_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_approx(node.drag_bottom_margin, 0.2,
		"spec39 — after _ready(), drag_bottom_margin is 0.2 (default)")
	node.free()


# AC-39.9: After _ready(), limit_left == -10000000 (default, exact integer equality).
func test_spec39_ready_sets_limit_left_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_int_eq(node.limit_left, -10000000,
		"spec39 — after _ready(), limit_left is -10000000 (default)")
	node.free()


# AC-39.10: After _ready(), limit_right == 10000000 (default, exact integer equality).
func test_spec39_ready_sets_limit_right_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_int_eq(node.limit_right, 10000000,
		"spec39 — after _ready(), limit_right is 10000000 (default)")
	node.free()


# AC-39.11: After _ready(), limit_top == -10000000 (default, exact integer equality).
func test_spec39_ready_sets_limit_top_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_int_eq(node.limit_top, -10000000,
		"spec39 — after _ready(), limit_top is -10000000 (default)")
	node.free()


# AC-39.12: After _ready(), limit_bottom == 10000000 (default, exact integer equality).
func test_spec39_ready_sets_limit_bottom_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_int_eq(node.limit_bottom, 10000000,
		"spec39 — after _ready(), limit_bottom is 10000000 (default)")
	node.free()


# AC-39.13: _ready() applies a non-default smoothing_enabled = false.
# Set the export var to false before calling _ready(); verify position_smoothing_enabled
# is false afterward.
func test_spec39_ready_applies_nondefa_smoothing_enabled_false() -> void:
	var node: CameraFollow = CameraFollow.new()
	node.smoothing_enabled = false
	node._ready()
	_assert_false(node.position_smoothing_enabled,
		"spec39 — after setting smoothing_enabled=false and calling _ready(), position_smoothing_enabled is false")
	node.free()


# ===========================================================================
# SPEC-40 — Smoothing behavior (headless-verifiable ACs only)
# ===========================================================================
# AC-40.1 through AC-40.4 are manual (MAN-01, MAN-02, MAN-05) and not tested here.

# AC-40.5: After _ready() with defaults, position_smoothing_enabled == true.
# This confirms smoothing is configured on by default.
func test_spec40_smoothing_enabled_after_ready_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_true(node.position_smoothing_enabled == true,
		"spec40/AC-40.5 — position_smoothing_enabled is true after _ready() with defaults")
	node.free()


# AC-40.6: After setting smoothing_speed = 12.5 and calling _ready(),
# position_smoothing_speed == 12.5 (tolerance EPSILON).
func test_spec40_nondefa_smoothing_speed_applied_by_ready() -> void:
	var node: CameraFollow = CameraFollow.new()
	node.smoothing_speed = 12.5
	node._ready()
	_assert_approx(node.position_smoothing_speed, 12.5,
		"spec40/AC-40.6 — position_smoothing_speed is 12.5 after smoothing_speed=12.5 and _ready()")
	node.free()


# ===========================================================================
# SPEC-41 — Dead zone / drag margin behavior (headless-verifiable ACs only)
# ===========================================================================
# AC-41.8 and AC-41.9 are manual (MAN-03) and not tested here.

# AC-41.1: After _ready() with defaults, drag_horizontal_enabled == true.
func test_spec41_drag_horizontal_enabled_after_ready_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_true(node.drag_horizontal_enabled == true,
		"spec41/AC-41.1 — drag_horizontal_enabled is true after _ready() with defaults")
	node.free()


# AC-41.2: After _ready() with defaults, drag_vertical_enabled == false.
func test_spec41_drag_vertical_enabled_after_ready_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_false(node.drag_vertical_enabled,
		"spec41/AC-41.2 — drag_vertical_enabled is false after _ready() with defaults")
	node.free()


# AC-41.3: After _ready() with defaults, drag_left_margin == 0.2 (tolerance EPSILON).
func test_spec41_drag_left_margin_after_ready_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_approx(node.drag_left_margin, 0.2,
		"spec41/AC-41.3 — drag_left_margin is 0.2 after _ready() with defaults")
	node.free()


# AC-41.4: After _ready() with defaults, drag_right_margin == 0.2 (tolerance EPSILON).
func test_spec41_drag_right_margin_after_ready_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_approx(node.drag_right_margin, 0.2,
		"spec41/AC-41.4 — drag_right_margin is 0.2 after _ready() with defaults")
	node.free()


# AC-41.5: After _ready() with defaults, drag_top_margin == 0.2 (tolerance EPSILON).
func test_spec41_drag_top_margin_after_ready_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_approx(node.drag_top_margin, 0.2,
		"spec41/AC-41.5 — drag_top_margin is 0.2 after _ready() with defaults")
	node.free()


# AC-41.6: After _ready() with defaults, drag_bottom_margin == 0.2 (tolerance EPSILON).
func test_spec41_drag_bottom_margin_after_ready_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_approx(node.drag_bottom_margin, 0.2,
		"spec41/AC-41.6 — drag_bottom_margin is 0.2 after _ready() with defaults")
	node.free()


# AC-41.7: Setting drag_left_margin = 0.4 before _ready(); confirms _ready() applies
# the current export value rather than a hardcoded 0.2.
func test_spec41_nondefa_drag_left_margin_applied_by_ready() -> void:
	var node: CameraFollow = CameraFollow.new()
	node.follow_drag_left_margin = 0.4
	node._ready()
	_assert_approx(node.drag_left_margin, 0.4,
		"spec41/AC-41.7 — drag_left_margin is 0.4 after follow_drag_left_margin=0.4 and _ready()")
	node.free()


# ===========================================================================
# SPEC-42 — Level bounds limiting (headless-verifiable ACs only)
# ===========================================================================
# AC-42.7 is manual (MAN-04) and not tested here.

# AC-42.1: After _ready() with defaults, limit_left == -10000000.
func test_spec42_limit_left_after_ready_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_int_eq(node.limit_left, -10000000,
		"spec42/AC-42.1 — limit_left is -10000000 after _ready() with defaults")
	node.free()


# AC-42.2: After _ready() with defaults, limit_right == 10000000.
func test_spec42_limit_right_after_ready_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_int_eq(node.limit_right, 10000000,
		"spec42/AC-42.2 — limit_right is 10000000 after _ready() with defaults")
	node.free()


# AC-42.3: After _ready() with defaults, limit_top == -10000000.
func test_spec42_limit_top_after_ready_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_int_eq(node.limit_top, -10000000,
		"spec42/AC-42.3 — limit_top is -10000000 after _ready() with defaults")
	node.free()


# AC-42.4: After _ready() with defaults, limit_bottom == 10000000.
func test_spec42_limit_bottom_after_ready_default() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	_assert_int_eq(node.limit_bottom, 10000000,
		"spec42/AC-42.4 — limit_bottom is 10000000 after _ready() with defaults")
	node.free()


# AC-42.5: Set limit_right = 800 before _ready(); confirms the current export value
# is applied rather than the hardcoded default.
func test_spec42_nondefa_limit_right_applied_by_ready() -> void:
	var node: CameraFollow = CameraFollow.new()
	node.follow_limit_right = 800
	node._ready()
	_assert_int_eq(node.limit_right, 800,
		"spec42/AC-42.5 — limit_right is 800 after follow_limit_right=800 and _ready()")
	node.free()


# AC-42.6: Set all four limits to non-default values before _ready(); all four
# Camera2D limit properties match the assigned values after _ready().
func test_spec42_all_four_limits_applied_by_ready() -> void:
	var node: CameraFollow = CameraFollow.new()
	node.follow_limit_left = 0
	node.follow_limit_right = 2000
	node.follow_limit_top = -600
	node.follow_limit_bottom = 400
	node._ready()
	_assert_int_eq(node.limit_left, 0,
		"spec42/AC-42.6 — limit_left is 0 after assignment and _ready()")
	_assert_int_eq(node.limit_right, 2000,
		"spec42/AC-42.6 — limit_right is 2000 after assignment and _ready()")
	_assert_int_eq(node.limit_top, -600,
		"spec42/AC-42.6 — limit_top is -600 after assignment and _ready()")
	_assert_int_eq(node.limit_bottom, 400,
		"spec42/AC-42.6 — limit_bottom is 400 after assignment and _ready()")
	node.free()


# ===========================================================================
# SPEC-45 — Non-functional: typeof() runtime type checks
# ===========================================================================
# These tests verify the runtime Variant type of each @export variable's value,
# catching wrong-type-default bugs (e.g., int literal 5 instead of float 5.0).
# Static annotation completeness (NF-01) is owned by Static QA; these are
# behavioral proxies accessible at runtime (AC-45.1/NF-01 partial proxy).
# NF-03 is deferred to Static QA entirely (see header comment).

# smoothing_enabled must be TYPE_BOOL.
func test_spec45_type_smoothing_enabled_is_bool() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_type_eq(node.smoothing_enabled, TYPE_BOOL,
		"spec45 — smoothing_enabled value has Variant type TYPE_BOOL")
	node.free()


# smoothing_speed must be TYPE_FLOAT.
func test_spec45_type_smoothing_speed_is_float() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_type_eq(node.smoothing_speed, TYPE_FLOAT,
		"spec45 — smoothing_speed value has Variant type TYPE_FLOAT")
	node.free()


# drag_horizontal must be TYPE_BOOL.
func test_spec45_type_drag_horizontal_is_bool() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_type_eq(node.drag_horizontal, TYPE_BOOL,
		"spec45 — drag_horizontal value has Variant type TYPE_BOOL")
	node.free()


# drag_vertical must be TYPE_BOOL.
func test_spec45_type_drag_vertical_is_bool() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_type_eq(node.drag_vertical, TYPE_BOOL,
		"spec45 — drag_vertical value has Variant type TYPE_BOOL")
	node.free()


# drag_left_margin must be TYPE_FLOAT.
func test_spec45_type_drag_left_margin_is_float() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_type_eq(node.follow_drag_left_margin, TYPE_FLOAT,
		"spec45 — follow_drag_left_margin value has Variant type TYPE_FLOAT")
	node.free()


# follow_drag_right_margin must be TYPE_FLOAT.
func test_spec45_type_drag_right_margin_is_float() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_type_eq(node.follow_drag_right_margin, TYPE_FLOAT,
		"spec45 — follow_drag_right_margin value has Variant type TYPE_FLOAT")
	node.free()


# follow_drag_top_margin must be TYPE_FLOAT.
func test_spec45_type_drag_top_margin_is_float() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_type_eq(node.follow_drag_top_margin, TYPE_FLOAT,
		"spec45 — follow_drag_top_margin value has Variant type TYPE_FLOAT")
	node.free()


# follow_drag_bottom_margin must be TYPE_FLOAT.
func test_spec45_type_drag_bottom_margin_is_float() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_type_eq(node.follow_drag_bottom_margin, TYPE_FLOAT,
		"spec45 — follow_drag_bottom_margin value has Variant type TYPE_FLOAT")
	node.free()


# follow_limit_left must be TYPE_INT (not float).
func test_spec45_type_limit_left_is_int() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_type_eq(node.follow_limit_left, TYPE_INT,
		"spec45 — follow_limit_left value has Variant type TYPE_INT (not float)")
	node.free()


# follow_limit_right must be TYPE_INT.
func test_spec45_type_limit_right_is_int() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_type_eq(node.follow_limit_right, TYPE_INT,
		"spec45 — follow_limit_right value has Variant type TYPE_INT (not float)")
	node.free()


# follow_limit_top must be TYPE_INT.
func test_spec45_type_limit_top_is_int() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_type_eq(node.follow_limit_top, TYPE_INT,
		"spec45 — follow_limit_top value has Variant type TYPE_INT (not float)")
	node.free()


# follow_limit_bottom must be TYPE_INT.
func test_spec45_type_limit_bottom_is_int() -> void:
	var node: CameraFollow = CameraFollow.new()
	_assert_type_eq(node.follow_limit_bottom, TYPE_INT,
		"spec45 — follow_limit_bottom value has Variant type TYPE_INT (not float)")
	node.free()


# ===========================================================================
# Determinism
# ===========================================================================

# Two identical CameraFollow instances constructed and run through _ready() with
# the same export values must produce identical Camera2D property values.
# This confirms _ready() is a pure property-assignment function with no
# hidden state or side-effects.
func test_determinism_two_instances_same_defaults_produce_same_properties() -> void:
	var node_a: CameraFollow = CameraFollow.new()
	var node_b: CameraFollow = CameraFollow.new()
	node_a._ready()
	node_b._ready()

	_assert_true(node_a.position_smoothing_enabled == node_b.position_smoothing_enabled,
		"determinism — position_smoothing_enabled identical across two instances with same defaults")
	_assert_approx(node_a.position_smoothing_speed, node_b.position_smoothing_speed,
		"determinism — position_smoothing_speed identical across two instances with same defaults")
	_assert_true(node_a.drag_horizontal_enabled == node_b.drag_horizontal_enabled,
		"determinism — drag_horizontal_enabled identical across two instances with same defaults")
	_assert_true(node_a.drag_vertical_enabled == node_b.drag_vertical_enabled,
		"determinism — drag_vertical_enabled identical across two instances with same defaults")
	_assert_int_eq(node_a.limit_left, node_b.limit_left,
		"determinism — limit_left identical across two instances with same defaults")
	_assert_int_eq(node_a.limit_right, node_b.limit_right,
		"determinism — limit_right identical across two instances with same defaults")

	node_a.free()
	node_b.free()


# Calling _ready() twice on the same instance produces the same property values.
# _ready() has no initialization state that would change on repeated calls.
func test_determinism_calling_ready_twice_is_idempotent() -> void:
	var node: CameraFollow = CameraFollow.new()
	node._ready()
	var speed_after_first: float = node.position_smoothing_speed
	node._ready()
	_assert_approx(node.position_smoothing_speed, speed_after_first,
		"determinism — calling _ready() twice: position_smoothing_speed unchanged on second call")
	node.free()


# ===========================================================================
# Public entry point
# ===========================================================================

func run_all() -> int:
	print("--- test_camera_follow.gd ---")
	_pass_count = 0
	_fail_count = 0

	# SPEC-37: Class structure and headless instantiability
	test_spec37_camera_follow_class_is_resolvable()
	test_spec37_camera_follow_is_camera2d_subclass()
	test_spec37_camera_follow_is_node2d()
	test_spec37_ready_method_is_callable()

	# SPEC-38: Exported configuration parameter defaults (pre-_ready())
	test_spec38_default_smoothing_enabled()
	test_spec38_default_smoothing_speed()
	test_spec38_default_drag_horizontal()
	test_spec38_default_drag_vertical()
	test_spec38_default_drag_left_margin()
	test_spec38_default_drag_right_margin()
	test_spec38_default_drag_top_margin()
	test_spec38_default_drag_bottom_margin()
	test_spec38_default_limit_left()
	test_spec38_default_limit_right()
	test_spec38_default_limit_top()
	test_spec38_default_limit_bottom()
	test_spec38_smoothing_enabled_is_mutable()
	test_spec38_smoothing_speed_is_mutable()
	test_spec38_limit_right_is_mutable()

	# SPEC-39: _ready() initialization (post-_ready() Camera2D property values)
	test_spec39_ready_sets_position_smoothing_enabled_default()
	test_spec39_ready_sets_position_smoothing_speed_default()
	test_spec39_ready_sets_drag_horizontal_enabled_default()
	test_spec39_ready_sets_drag_vertical_enabled_default()
	test_spec39_ready_sets_drag_left_margin_default()
	test_spec39_ready_sets_drag_right_margin_default()
	test_spec39_ready_sets_drag_top_margin_default()
	test_spec39_ready_sets_drag_bottom_margin_default()
	test_spec39_ready_sets_limit_left_default()
	test_spec39_ready_sets_limit_right_default()
	test_spec39_ready_sets_limit_top_default()
	test_spec39_ready_sets_limit_bottom_default()
	test_spec39_ready_applies_nondefa_smoothing_enabled_false()

	# SPEC-40: Smoothing behavior (headless-verifiable ACs only)
	test_spec40_smoothing_enabled_after_ready_default()
	test_spec40_nondefa_smoothing_speed_applied_by_ready()

	# SPEC-41: Drag margin behavior (headless-verifiable ACs only)
	test_spec41_drag_horizontal_enabled_after_ready_default()
	test_spec41_drag_vertical_enabled_after_ready_default()
	test_spec41_drag_left_margin_after_ready_default()
	test_spec41_drag_right_margin_after_ready_default()
	test_spec41_drag_top_margin_after_ready_default()
	test_spec41_drag_bottom_margin_after_ready_default()
	test_spec41_nondefa_drag_left_margin_applied_by_ready()

	# SPEC-42: Level bounds limiting (headless-verifiable ACs only)
	test_spec42_limit_left_after_ready_default()
	test_spec42_limit_right_after_ready_default()
	test_spec42_limit_top_after_ready_default()
	test_spec42_limit_bottom_after_ready_default()
	test_spec42_nondefa_limit_right_applied_by_ready()
	test_spec42_all_four_limits_applied_by_ready()

	# SPEC-45: typeof() runtime type checks for all @export vars
	test_spec45_type_smoothing_enabled_is_bool()
	test_spec45_type_smoothing_speed_is_float()
	test_spec45_type_drag_horizontal_is_bool()
	test_spec45_type_drag_vertical_is_bool()
	test_spec45_type_drag_left_margin_is_float()
	test_spec45_type_drag_right_margin_is_float()
	test_spec45_type_drag_top_margin_is_float()
	test_spec45_type_drag_bottom_margin_is_float()
	test_spec45_type_limit_left_is_int()
	test_spec45_type_limit_right_is_int()
	test_spec45_type_limit_top_is_int()
	test_spec45_type_limit_bottom_is_int()

	# Determinism
	test_determinism_two_instances_same_defaults_produce_same_properties()
	test_determinism_calling_ready_twice_is_idempotent()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
