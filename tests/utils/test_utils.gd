#
# test_utils.gd
#
# Shared test utility base for all test files in tests/.
#
# Spec:   project_board/maintenance/in_progress/test_utility_consolidation.md
#         Requirements MAINT-TUC-1, MAINT-TUC-2, MAINT-TUC-3
#
# Usage:
#   Replace `extends Object` with `extends "res://tests/utils/test_utils.gd"` in
#   any test file. The test file must still declare its own:
#     var _pass_count: int = 0
#     var _fail_count: int = 0
#
# This file is discovered by run_tests.gd (begins with "test_"). It satisfies
# the runner via run_all() -> int: return 0 (no-op, zero failures).
#
# IMPORTANT: Do NOT add a class_name declaration to this file.
#
# Implementation note: _pass_count and _fail_count are NOT declared here (AC-3.1).
# Each subclass declares them. The base class methods access them via _get()/_set()
# virtual method dispatch: when a subclass instance calls _pass(), self._get() finds
# the subclass-declared _pass_count directly (the declared property takes precedence
# over _get()). When the smoke/adversarial tests inject counters via inst.set() on a
# bare base instance, _set()/_get() route through _dyn to the backing Dictionary.
# This satisfies AC-3.1 while allowing the tests to instrument base instances.
#

extends Object

# Backing store for dynamically-set properties on bare base instances.
# Used by _get()/_set() so tests can inject _pass_count/_fail_count via
# inst.set("_pass_count", 0) without requiring them to be declared in the base.
# Subclass-declared _pass_count/_fail_count take precedence and are not routed here.
var _dyn: Dictionary = {}


func _get(property: StringName) -> Variant:
	if _dyn.has(property):
		return _dyn[property]
	return null


func _set(property: StringName, value: Variant) -> bool:
	_dyn[property] = value
	return true


# ---------------------------------------------------------------------------
# Group A — Core pass/fail reporters
# ---------------------------------------------------------------------------

func _pass(test_name: String) -> void:
	set("_pass_count", get("_pass_count") + 1)
	print("  PASS: " + test_name)


func _pass_test(test_name: String) -> void:
	set("_pass_count", get("_pass_count") + 1)
	print("  PASS: " + test_name)


func _fail(test_name: String, message: String) -> void:
	set("_fail_count", get("_fail_count") + 1)
	print("  FAIL: " + test_name + " — " + message)


func _fail_test(test_name: String, message: String) -> void:
	set("_fail_count", get("_fail_count") + 1)
	print("  FAIL: " + test_name + " — " + message)


# ---------------------------------------------------------------------------
# Group B — Boolean assertion helpers
# ---------------------------------------------------------------------------

func _assert_true(condition: bool, test_name: String, fail_msg: String = "expected true, got false") -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, fail_msg)


func _assert_false(condition: bool, test_name: String, fail_msg: String = "expected false, got true") -> void:
	if not condition:
		_pass(test_name)
	else:
		_fail(test_name, fail_msg)


# ---------------------------------------------------------------------------
# Group C — Typed equality helpers
# ---------------------------------------------------------------------------

func _assert_eq_int(expected: int, actual: int, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected " + str(expected) + ", got " + str(actual))


func _assert_eq_string(expected: String, actual: String, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected '" + expected + "', got '" + actual + "'")


func _assert_eq_float(expected: float, actual: float, test_name: String) -> void:
	if absf(actual - expected) < 0.0001:
		_pass(test_name)
	else:
		_fail(test_name, "expected " + str(expected) + ", got " + str(actual))


func _assert_eq(expected: Variant, actual: Variant, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected " + str(expected) + ", got " + str(actual))


func _assert_eq_str(actual: String, expected: String, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected \"" + expected + "\", got \"" + actual + "\"")


# ---------------------------------------------------------------------------
# Group D — Float and vector approximate equality
# ---------------------------------------------------------------------------

func _approx_eq(a: float, b: float) -> bool:
	return abs(a - b) < 1e-4


func _assert_approx(a: float, b: float, test_name: String) -> void:
	if _approx_eq(a, b):
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b) + " (delta " + str(abs(a - b)) + ")")


func _assert_vec2_approx(a: Vector2, b: Vector2, test_name: String) -> void:
	if _approx_eq(a.x, b.x) and _approx_eq(a.y, b.y):
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b))


# ---------------------------------------------------------------------------
# Group E — Vector3 approximate equality
# ---------------------------------------------------------------------------

func _near(a: float, b: float, tol: float) -> bool:
	return absf(a - b) <= tol


func _assert_vec3_near(actual: Vector3, expected: Vector3, tol: float, test_name: String) -> void:
	var ok: bool = _near(actual.x, expected.x, tol) \
		and _near(actual.y, expected.y, tol) \
		and _near(actual.z, expected.z, tol)
	if ok:
		_pass(test_name)
	else:
		_fail(test_name, "expected ~" + str(expected) + " (tol " + str(tol) + "), got " + str(actual))


# ---------------------------------------------------------------------------
# Group F — Shared test helpers (DRY pattern for common test utilities)
# ---------------------------------------------------------------------------

# Create a mock enemy with health component for testing.
# Used by health bar tests and related enemy behavior tests.
func test_create_mock_enemy(hp: float = 100.0, max_hp: float = 100.0) -> CharacterBody3D:
	var body := CharacterBody3D.new()
	body.set_script(load("res://scripts/enemies/enemy_base.gd"))
	body.set_meta("current_hp", hp)
	body.set_meta("max_hp", max_hp)
	return body


# Load and instantiate a scene at the given path.
# Returns the instantiated node or null if loading fails.
func test_load_and_instantiate_scene(scene_path: String) -> Variant:
	var scene = load(scene_path)
	if scene == null:
		return null
	return scene.instantiate() as Node


# Find a ProgressBar node anywhere in the given tree.
# Performs depth-first search; returns null if not found.
func test_find_progress_bar(root: Node) -> Variant:
	var stack: Array[Node] = [root]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is ProgressBar:
			return node
		for child in node.get_children():
			stack.append(child)
	return null


# ---------------------------------------------------------------------------
# Group G — No-op runner compatibility (AC-1.4, AC-2.19)
# ---------------------------------------------------------------------------

func run_all() -> int:
	return 0
