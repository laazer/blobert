#
# test_scene_state_integration_3d.gd
#
# Minimal headless integration tests that validate the 3D main scene
# (`test_movement_3d.tscn`) can instantiate a SceneVariantController node,
# own a SceneStateMachine instance, and switch between canonical scene
# variants via the controller API without duplicating the scene.
#
# Ticket: scene_state_machine.md
#

extends Object


var _pass_count: int = 0
var _fail_count: int = 0


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


func _load_3d_scene() -> Node:
	var packed: PackedScene = load("res://scenes/levels/sandbox/test_movement_3d.tscn") as PackedScene
	if packed == null:
		_fail(
			"scene_state_3d_load",
			"could not load res://scenes/levels/sandbox/test_movement_3d.tscn for scene state integration"
		)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail(
			"scene_state_3d_instantiate",
			"instantiate() returned null for test_movement_3d.tscn"
		)
		return null
	return inst


func _find_variant_controller(root: Node) -> Node:
	if root == null:
		return null
	return root.get_node_or_null("SceneVariantController")


func test_scene_has_scene_variant_controller_with_state_machine() -> void:
	var root: Node = _load_3d_scene()
	if root == null:
		return

	var controller: Node = _find_variant_controller(root)
	_assert_true(controller != null, "scene_state_3d_has_variant_controller")
	if controller == null:
		root.free()
		return

	_assert_true(
		controller.has_method("get_state_machine"),
		"scene_state_3d_controller_has_get_state_machine"
	)

	if controller.has_method("get_state_machine"):
		var machine = controller.call("get_state_machine")
		_assert_true(
			machine != null,
			"scene_state_3d_controller_returns_state_machine"
		)
		if machine != null:
			var state_id: String = machine.get_state_id()
			_assert_true(
				state_id == "BASELINE",
				"scene_state_3d_initial_state_baseline"
			)
	root.free()


func test_controller_can_switch_between_baseline_and_infection_demo() -> void:
	var root: Node = _load_3d_scene()
	if root == null:
		return

	var controller: Node = _find_variant_controller(root)
	if controller == null:
		_fail(
			"scene_state_3d_switch_variants_controller_missing",
			"SceneVariantController node not found in 3D scene"
		)
		root.free()
		return

	if not controller.has_method("get_state_machine"):
		_fail(
			"scene_state_3d_switch_variants_no_get_state_machine",
			"SceneVariantController missing get_state_machine()"
		)
		root.free()
		return

	var machine = controller.call("get_state_machine")
	if machine == null:
		_fail(
			"scene_state_3d_switch_variants_no_machine",
			"SceneVariantController.get_state_machine() returned null"
		)
		root.free()
		return

	# Start from baseline.
	_assert_true(
		machine.get_state_id() == "BASELINE",
		"scene_state_3d_switch_variants_starts_baseline"
	)

	# Switch to infection demo and verify state reflects the change.
	if controller.has_method("select_infection_demo"):
		controller.call("select_infection_demo")
		_assert_true(
			machine.get_state_id() == "INFECTION_DEMO",
			"scene_state_3d_switch_variants_infection_demo"
		)
	else:
		_fail(
			"scene_state_3d_switch_variants_missing_select_infection_demo",
			"SceneVariantController missing select_infection_demo()"
		)

	# Switch back to baseline and verify.
	if controller.has_method("select_baseline"):
		controller.call("select_baseline")
		_assert_true(
			machine.get_state_id() == "BASELINE",
			"scene_state_3d_switch_variants_back_to_baseline"
		)
	else:
		_fail(
			"scene_state_3d_switch_variants_missing_select_baseline",
			"SceneVariantController missing select_baseline()"
		)

	root.free()


func test_controller_feature_gates_reflect_state() -> void:
	# Validates AC-4: feature systems are gated on scene state via the
	# is_infection_enabled(), is_enemies_enabled(), and
	# is_prototype_hud_enabled() helpers on SceneVariantController3D.
	# All assertions are pure method calls — no Node visibility or physics
	# wiring is required for headless execution.
	var root: Node = _load_3d_scene()
	if root == null:
		return

	var controller: Node = _find_variant_controller(root)
	if controller == null:
		_fail(
			"scene_state_3d_gates_controller_missing",
			"SceneVariantController node not found in 3D scene"
		)
		root.free()
		return

	# Verify the three gate helpers exist on the controller.
	_assert_true(
		controller.has_method("is_infection_enabled"),
		"scene_state_3d_controller_has_is_infection_enabled"
	)
	_assert_true(
		controller.has_method("is_enemies_enabled"),
		"scene_state_3d_controller_has_is_enemies_enabled"
	)
	_assert_true(
		controller.has_method("is_prototype_hud_enabled"),
		"scene_state_3d_controller_has_is_prototype_hud_enabled"
	)

	if not (controller.has_method("is_infection_enabled") and
			controller.has_method("is_enemies_enabled") and
			controller.has_method("is_prototype_hud_enabled") and
			controller.has_method("select_baseline") and
			controller.has_method("select_infection_demo") and
			controller.has_method("select_enemy_playtest")):
		root.free()
		return

	# --- BASELINE state ---
	controller.call("select_baseline")
	_assert_true(
		controller.call("is_infection_enabled") == false,
		"scene_state_3d_baseline_infection_disabled"
	)
	_assert_true(
		controller.call("is_enemies_enabled") == false,
		"scene_state_3d_baseline_enemies_disabled"
	)
	_assert_true(
		controller.call("is_prototype_hud_enabled") == true,
		"scene_state_3d_baseline_hud_enabled"
	)

	# --- INFECTION_DEMO state ---
	controller.call("select_infection_demo")
	_assert_true(
		controller.call("is_infection_enabled") == true,
		"scene_state_3d_infection_demo_infection_enabled"
	)
	_assert_true(
		controller.call("is_enemies_enabled") == false,
		"scene_state_3d_infection_demo_enemies_disabled"
	)
	_assert_true(
		controller.call("is_prototype_hud_enabled") == true,
		"scene_state_3d_infection_demo_hud_enabled"
	)

	# --- ENEMY_PLAYTEST state ---
	controller.call("select_enemy_playtest")
	_assert_true(
		controller.call("is_infection_enabled") == false,
		"scene_state_3d_enemy_playtest_infection_disabled"
	)
	_assert_true(
		controller.call("is_enemies_enabled") == true,
		"scene_state_3d_enemy_playtest_enemies_enabled"
	)
	_assert_true(
		controller.call("is_prototype_hud_enabled") == true,
		"scene_state_3d_enemy_playtest_hud_enabled"
	)

	root.free()


func run_all() -> int:
	print("--- test_scene_state_integration_3d.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_scene_has_scene_variant_controller_with_state_machine()
	test_controller_can_switch_between_baseline_and_infection_demo()
	test_controller_feature_gates_reflect_state()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

