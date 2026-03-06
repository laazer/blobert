# test_base_physics_entity_3d.gd
#
# Simple tests for the BasePhysicsEntity3D gravity application.
#
# These tests run without nodes or scenes; they simply call the script method
# directly to ensure gravity modifies velocity as expected.

class_name BasePhysicsEntity3DTests
extends Object

var _pass_count: int = 0
var _fail_count: int = 0

func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)

func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)

func _assert_true(cond: bool, test_name: String) -> void:
	if cond:
		_pass(test_name)
	else:
		_fail(test_name, "expected true, got false")

func test_gravity_applied() -> void:
	var body = BasePhysicsEntity3D.new()
	body.velocity = Vector3(0, 0, 0)
	# simulate one second
	body._physics_process(1.0)
	# after one second, velocity.y should be negative roughly equal to gravity
	var applied = body.velocity.y
	_assert_true(applied < 0.0, "gravity_applied_is_negative")

func run_all() -> int:
	print("--- test_base_physics_entity_3d.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_gravity_applied()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count