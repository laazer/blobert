#
# run_debug_toggle_tests.gd
#
# Isolated test runner for debugging the enemy health bar debug toggle tests.
# This runs ONLY test_enemy_health_bar_3d_debug_toggle.gd to avoid crashes in other test files.
#

extends SceneTree

func _initialize() -> void:
	print("=== Debug Toggle Test Runner ===")
	print("")

	var path := "res://tests/ui/test_enemy_health_bar_3d_debug_toggle.gd"
	var script: GDScript = load(path)

	if script == null or not script.can_instantiate():
		push_error("RUNNER ERROR: could not load " + path)
		quit(1)
		return

	var failures: int = script.new().run_all()

	print("")
	if failures == 0:
		print("=== ALL DEBUG TOGGLE TESTS PASSED ===")
	else:
		print("=== FAILURES: " + str(failures) + " test(s) failed ===")

	quit(1 if failures > 0 else 0)
