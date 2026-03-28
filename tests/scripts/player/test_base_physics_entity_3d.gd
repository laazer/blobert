# test_base_physics_entity_3d.gd
#
# Simple tests for the BasePhysicsEntity3D gravity application.
#
# These tests run without nodes or scenes; they simply call the script method
# directly to ensure gravity modifies velocity as expected.

class_name BasePhysicsEntity3DTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

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