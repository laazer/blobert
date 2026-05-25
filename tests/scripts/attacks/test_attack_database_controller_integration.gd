#
# test_attack_database_controller_integration.gd
#
# Integration tests for the attack pipeline: _try_attack, cooldown tracking,
# state gating, executor wiring, facing sign, and input reading.
# Spec: project_board/specs/attack_database_integration_spec.md (ADB-7 through ADB-14)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/06_attack_database_integration.md
#

class_name AttackDatabaseIntegrationTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

const _CONTROLLER_PATH := "res://scripts/player/player_controller_3d.gd"
const _DB_PATH := "res://scripts/attacks/attack_database.gd"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_resource(overrides: Dictionary = {}) -> Resource:
	var r = AttackResource.new()
	r.startup_frames = 0
	for key in overrides:
		r.set(key, overrides[key])
	return r


func _load_controller_script() -> GDScript:
	return load(_CONTROLLER_PATH) as GDScript


func _load_db_script() -> GDScript:
	return load(_DB_PATH) as GDScript


func _make_db(test_label: String) -> Node:
	var script = _load_db_script()
	if script == null:
		_fail_test(test_label, _DB_PATH + " not loadable (not yet implemented)")
		return null
	return script.new()


func _build_controller_scene(test_label: String) -> Dictionary:
	var ctrl_script = _load_controller_script()
	if ctrl_script == null:
		_fail_test(test_label, _CONTROLLER_PATH + " not loadable")
		return {}

	var controller = ctrl_script.new()
	if controller == null:
		_fail_test(test_label, "controller instantiation returned null")
		return {}

	var scene_root = Node3D.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)
	scene_root.add_child(controller)

	return {"root": scene_root, "controller": controller}


func _teardown(scene: Dictionary) -> void:
	var root = scene.get("root")
	if root != null and is_instance_valid(root):
		(root as Node).free()


func _get_autoload_db() -> Node:
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		return null
	return tree.root.get_node_or_null("AttackDatabase")


func _setup_attack_pipeline(
	test_label: String,
	state: int,
	slot_a_id: String,
	slot_b_id: String,
	cooldowns: Dictionary,
) -> Dictionary:
	var scene = _build_controller_scene(test_label)
	if scene.is_empty():
		return {}

	var controller = scene["controller"]

	var psm = controller.get("_player_state_machine")
	if psm == null:
		_fail_test(test_label, "_player_state_machine not found on controller")
		_teardown(scene)
		return {}
	psm._state = state

	var msm = MutationSlotManager.new()
	if slot_a_id != "":
		msm.fill_next_available(slot_a_id)
	if slot_b_id != "":
		msm.fill_next_available(slot_b_id)
	controller.set("_mutation_slot", msm)

	var cd_dict = controller.get("_mutation_cooldowns")
	if cd_dict == null:
		_fail_test(test_label, "_mutation_cooldowns not found on controller")
		_teardown(scene)
		return {}
	for key in cooldowns:
		cd_dict[key] = cooldowns[key]

	var executor = controller.get("_attack_executor")
	scene["executor"] = executor
	scene["slot_manager"] = msm
	return scene


# ---------------------------------------------------------------------------
# ADB-14: State gating via PlayerInputActionPolicy
# ---------------------------------------------------------------------------

func test_adb14_attack_permitted_states() -> void:
	var policy = PlayerInputActionPolicy.new()
	var permitted: Array[int] = [
		PlayerStateMachine.PlayerState.IDLE,
		PlayerStateMachine.PlayerState.WALK,
		PlayerStateMachine.PlayerState.JUMP,
		PlayerStateMachine.PlayerState.FALL,
		PlayerStateMachine.PlayerState.FLOAT,
		PlayerStateMachine.PlayerState.WALL_CLING,
	]
	for state in permitted:
		var allowed: bool = policy.is_action_permitted(
			state as PlayerStateMachine.PlayerState,
			PlayerInputActionPolicy.ACTION_ATTACK,
		)
		_assert_true(
			allowed,
			"ADB-14_permit_state_" + str(state),
		)


func test_adb14_attack_denied_states() -> void:
	var policy = PlayerInputActionPolicy.new()
	var denied: Array[int] = [
		PlayerStateMachine.PlayerState.ABSORB,
		PlayerStateMachine.PlayerState.MUTATE,
		PlayerStateMachine.PlayerState.HURT,
		PlayerStateMachine.PlayerState.DEAD,
	]
	for state in denied:
		var allowed: bool = policy.is_action_permitted(
			state as PlayerStateMachine.PlayerState,
			PlayerInputActionPolicy.ACTION_ATTACK,
		)
		_assert_false(
			allowed,
			"ADB-14_deny_state_" + str(state),
		)


# ---------------------------------------------------------------------------
# ADB-8: get_facing_sign (AC-8a..AC-8c)
# ---------------------------------------------------------------------------

func test_adb08_facing_sign_positive() -> void:
	var scene = _build_controller_scene("ADB-08_positive")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("get_facing_sign"):
		_fail_test("ADB-08_positive", "get_facing_sign method not found on controller")
		_teardown(scene)
		return
	controller.velocity = Vector3(5.0, 0.0, 0.0)
	var sign_val: float = controller.get_facing_sign()
	_assert_eq_float(1.0, sign_val, "ADB-08_positive_velocity_returns_1")
	_teardown(scene)


func test_adb08_facing_sign_negative() -> void:
	var scene = _build_controller_scene("ADB-08_negative")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("get_facing_sign"):
		_fail_test("ADB-08_negative", "get_facing_sign method not found on controller")
		_teardown(scene)
		return
	controller.velocity = Vector3(-3.0, 0.0, 0.0)
	var sign_val: float = controller.get_facing_sign()
	_assert_eq_float(-1.0, sign_val, "ADB-08_negative_velocity_returns_neg1")
	_teardown(scene)


func test_adb08_facing_sign_zero() -> void:
	var scene = _build_controller_scene("ADB-08_zero")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("get_facing_sign"):
		_fail_test("ADB-08_zero", "get_facing_sign method not found on controller")
		_teardown(scene)
		return
	controller.velocity = Vector3(0.0, 0.0, 0.0)
	var sign_val: float = controller.get_facing_sign()
	_assert_eq_float(1.0, sign_val, "ADB-08_zero_velocity_defaults_right")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADB-12: AttackExecutor child node wiring (AC-12a..AC-12b)
# ---------------------------------------------------------------------------

func test_adb12_executor_is_child() -> void:
	var scene = _build_controller_scene("ADB-12_child")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var executor = controller.get("_attack_executor")
	if executor == null:
		_fail_test("ADB-12_child", "_attack_executor not found on controller")
		_teardown(scene)
		return
	_assert_true(is_instance_valid(executor), "ADB-12_executor_valid")
	_assert_true(executor.get_parent() == controller, "ADB-12_executor_parent_is_controller")
	_teardown(scene)


func test_adb12_executor_is_attack_executor() -> void:
	var scene = _build_controller_scene("ADB-12_type")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var executor = controller.get("_attack_executor")
	if executor == null:
		_fail_test("ADB-12_type", "_attack_executor not found on controller")
		_teardown(scene)
		return
	_assert_true(executor is AttackExecutor, "ADB-12_is_attack_executor")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADB-9: Cooldown tracking (AC-9a..AC-9g)
# ---------------------------------------------------------------------------

func test_adb09_cooldown_starts_empty() -> void:
	var scene = _build_controller_scene("ADB-09_empty")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADB-09_empty", "_mutation_cooldowns not found on controller")
		_teardown(scene)
		return
	_assert_eq_int(0, cd.size(), "ADB-09_cooldowns_start_empty")
	_teardown(scene)


func test_adb09_cooldown_blocks_attack() -> void:
	var scene = _setup_attack_pipeline(
		"ADB-09_blocks",
		PlayerStateMachine.PlayerState.IDLE,
		"test_claw_09a", "", {"test_claw_09a": 0.5},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADB-09_blocks", "_try_attack method not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], "ADB-09_cooldown_blocks_execution")
	_teardown(scene)


func test_adb09_cooldown_allows_at_zero() -> void:
	var db = _get_autoload_db()
	if db == null:
		var db_inst = _make_db("ADB-09_allows")
		if db_inst == null:
			return
		db_inst.free()
		_fail_test("ADB-09_allows", "AttackDatabase autoload not available")
		return

	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
	db.register_base_attack("test_claw_09b", res)

	var scene = _setup_attack_pipeline(
		"ADB-09_allows",
		PlayerStateMachine.PlayerState.IDLE,
		"test_claw_09b", "", {"test_claw_09b": 0.0},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADB-09_allows", "_try_attack method not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_true(fired[0], "ADB-09_zero_cooldown_allows_execution")
	_teardown(scene)


func test_adb09_cooldown_set_after_execution() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADB-09_set", "AttackDatabase autoload not available")
		return

	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 2.5})
	db.register_base_attack("test_claw_09c", res)

	var scene = _setup_attack_pipeline(
		"ADB-09_set",
		PlayerStateMachine.PlayerState.IDLE,
		"test_claw_09c", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADB-09_set", "_try_attack method not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADB-09_set", "_mutation_cooldowns not available")
		_teardown(scene)
		return
	_assert_eq_float(2.5, cd.get("test_claw_09c", 0.0), "ADB-09_cooldown_set_to_resource_value")
	_teardown(scene)


func test_adb09_cooldown_independent() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADB-09_indep", "AttackDatabase autoload not available")
		return

	var res_claw = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
	db.register_base_attack("test_claw_09d", res_claw)

	var scene = _setup_attack_pipeline(
		"ADB-09_indep",
		PlayerStateMachine.PlayerState.IDLE,
		"test_claw_09d", "",
		{"test_claw_09d": 0.0, "test_acid_09d": 0.5},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADB-09_indep", "_try_attack method not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADB-09_indep", "_mutation_cooldowns not available")
		_teardown(scene)
		return
	_assert_eq_float(1.0, cd.get("test_claw_09d", -1.0), "ADB-09_claw_cooldown_set")
	_assert_eq_float(0.5, cd.get("test_acid_09d", -1.0), "ADB-09_acid_cooldown_unaffected")
	_teardown(scene)


func test_adb09_cooldown_decrement() -> void:
	var scene = _build_controller_scene("ADB-09_decrement")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADB-09_decrement", "_mutation_cooldowns not found on controller")
		_teardown(scene)
		return
	cd["test_tick"] = 1.0
	controller.call("_tick_controller_timers", 0.25, false)
	_assert_eq_float(0.75, cd.get("test_tick", -1.0), "ADB-09_decremented_by_delta")
	_teardown(scene)


func test_adb09_cooldown_clamp_zero() -> void:
	var scene = _build_controller_scene("ADB-09_clamp")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADB-09_clamp", "_mutation_cooldowns not found on controller")
		_teardown(scene)
		return
	cd["test_clamp"] = 0.1
	controller.call("_tick_controller_timers", 0.5, false)
	var remaining: float = cd.get("test_clamp", -1.0)
	_assert_true(remaining >= 0.0, "ADB-09_clamp_never_negative")
	_assert_eq_float(0.0, remaining, "ADB-09_clamp_at_zero")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADB-7: _try_attack pipeline (AC-7a..AC-7j)
# ---------------------------------------------------------------------------

func test_adb07_succeeds_base_mutation() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADB-07_base", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 0.8, "damage": 5.0})
	db.register_base_attack("test_claw_07a", res)

	var scene = _setup_attack_pipeline(
		"ADB-07_base",
		PlayerStateMachine.PlayerState.IDLE,
		"test_claw_07a", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADB-07_base", "_try_attack method not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired_resource = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired_resource[0] = r)
	controller.call("_try_attack")
	_assert_true(fired_resource[0] != null, "ADB-07_base_executor_called")
	if fired_resource[0] != null:
		_assert_true(fired_resource[0] == res, "ADB-07_base_correct_resource")
	_teardown(scene)


func test_adb07_blocked_by_state() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADB-07_state_block", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
	db.register_base_attack("test_claw_07b", res)

	var denied_states: Array[int] = [
		PlayerStateMachine.PlayerState.ABSORB,
		PlayerStateMachine.PlayerState.MUTATE,
		PlayerStateMachine.PlayerState.HURT,
		PlayerStateMachine.PlayerState.DEAD,
	]
	for state in denied_states:
		var scene = _setup_attack_pipeline(
			"ADB-07_state_block_" + str(state),
			state, "test_claw_07b", "", {},
		)
		if scene.is_empty():
			continue
		var controller = scene["controller"]
		if not controller.has_method("_try_attack"):
			_fail_test("ADB-07_state_block_" + str(state), "_try_attack not found")
			_teardown(scene)
			continue
		var executor = scene.get("executor")
		var fired = [false]
		if executor != null and executor.has_signal("attack_started"):
			executor.connect("attack_started", func(_r): fired[0] = true)
		controller.call("_try_attack")
		_assert_false(fired[0], "ADB-07_blocked_state_" + str(state))
		_teardown(scene)


func test_adb07_blocked_no_mutation() -> void:
	var scene = _setup_attack_pipeline(
		"ADB-07_no_mut",
		PlayerStateMachine.PlayerState.IDLE,
		"", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADB-07_no_mut", "_try_attack method not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], "ADB-07_no_mutation_blocks_attack")
	_teardown(scene)


func test_adb07_blocked_by_cooldown() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADB-07_cd_block", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
	db.register_base_attack("test_claw_07d", res)

	var scene = _setup_attack_pipeline(
		"ADB-07_cd_block",
		PlayerStateMachine.PlayerState.IDLE,
		"test_claw_07d", "", {"test_claw_07d": 0.5},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADB-07_cd_block", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], "ADB-07_cooldown_blocks_attack")
	_teardown(scene)


func test_adb07_null_db_result_no_crash() -> void:
	var scene = _setup_attack_pipeline(
		"ADB-07_null_db",
		PlayerStateMachine.PlayerState.IDLE,
		"test_nonexistent_07e", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADB-07_null_db", "_try_attack not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	_pass_test("ADB-07_null_db_result_no_crash")
	_teardown(scene)


func test_adb07_fused_when_both_slots() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADB-07_fused", "AttackDatabase autoload not available")
		return
	var base_res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 0.8, "damage": 2.0})
	var fused_res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.5, "damage": 10.0})
	db.register_base_attack("test_claw_07f", base_res)
	db.register_fused_attack("test_claw_07f", "test_acid_07f", fused_res)

	var scene = _setup_attack_pipeline(
		"ADB-07_fused",
		PlayerStateMachine.PlayerState.IDLE,
		"test_claw_07f", "test_acid_07f", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADB-07_fused", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired_resource = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired_resource[0] = r)
	controller.call("_try_attack")
	_assert_true(fired_resource[0] == fused_res, "ADB-07_fused_attack_used")
	_teardown(scene)


func test_adb07_fused_fallback_to_base() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADB-07_fallback", "AttackDatabase autoload not available")
		return
	var base_res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 0.8, "damage": 3.0})
	db.register_base_attack("test_claw_07g", base_res)

	var scene = _setup_attack_pipeline(
		"ADB-07_fallback",
		PlayerStateMachine.PlayerState.IDLE,
		"test_claw_07g", "test_no_fused_07g", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADB-07_fallback", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired_resource = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired_resource[0] = r)
	controller.call("_try_attack")
	_assert_true(fired_resource[0] == base_res, "ADB-07_fused_fallback_uses_base")
	_teardown(scene)


func test_adb07_executor_reentrant_guard() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADB-07_reentrant", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
	db.register_base_attack("test_claw_07h", res)

	var scene = _setup_attack_pipeline(
		"ADB-07_reentrant",
		PlayerStateMachine.PlayerState.IDLE,
		"test_claw_07h", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADB-07_reentrant", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	if executor != null:
		executor.set("_is_active", true)
	var attack_count = [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): attack_count[0] += 1)
	controller.call("_try_attack")
	_assert_eq_int(0, attack_count[0], "ADB-07_executor_active_blocks")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADB-10: Attack input in _read_player_input (AC-10a..AC-10d)
# ---------------------------------------------------------------------------

func test_adb10_input_key_exists() -> void:
	var scene = _build_controller_scene("ADB-10_key")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_read_player_input"):
		_fail_test("ADB-10_key", "_read_player_input method not found")
		_teardown(scene)
		return
	var input_dict = controller.call("_read_player_input")
	if input_dict == null or not (input_dict is Dictionary):
		_fail_test("ADB-10_key", "_read_player_input did not return a Dictionary")
		_teardown(scene)
		return
	_assert_true(
		(input_dict as Dictionary).has("attack_just_pressed"),
		"ADB-10_attack_just_pressed_key_exists",
	)
	_teardown(scene)


# ---------------------------------------------------------------------------
# EC-12: Zero cooldown allows immediate re-attack
# ---------------------------------------------------------------------------

func test_ec12_zero_cooldown_immediate() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("EC-12_zero_cd", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 0.0})
	db.register_base_attack("test_claw_ec12", res)

	var scene = _setup_attack_pipeline(
		"EC-12_zero_cd",
		PlayerStateMachine.PlayerState.IDLE,
		"test_claw_ec12", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("EC-12_zero_cd", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var attack_count = [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): attack_count[0] += 1)
	controller.call("_try_attack")
	_assert_true(attack_count[0] >= 1, "EC-12_first_attack_fires")

	var cd = controller.get("_mutation_cooldowns")
	if cd != null:
		var remaining: float = cd.get("test_claw_ec12", -1.0)
		_assert_true(remaining <= 0.0, "EC-12_zero_cooldown_set")
	_teardown(scene)


# ---------------------------------------------------------------------------
# EC-9: _try_attack when _mutation_slot is null
# ---------------------------------------------------------------------------

func test_ec09_null_mutation_slot_no_crash() -> void:
	var scene = _build_controller_scene("EC-09_null_slot")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	controller.set("_mutation_slot", null)
	if not controller.has_method("_try_attack"):
		_fail_test("EC-09_null_slot", "_try_attack not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	_pass_test("EC-09_null_mutation_slot_no_crash")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AttackDatabaseIntegrationTests ===")

	test_adb14_attack_permitted_states()
	test_adb14_attack_denied_states()

	test_adb08_facing_sign_positive()
	test_adb08_facing_sign_negative()
	test_adb08_facing_sign_zero()

	test_adb12_executor_is_child()
	test_adb12_executor_is_attack_executor()

	test_adb09_cooldown_starts_empty()
	test_adb09_cooldown_blocks_attack()
	test_adb09_cooldown_allows_at_zero()
	test_adb09_cooldown_set_after_execution()
	test_adb09_cooldown_independent()
	test_adb09_cooldown_decrement()
	test_adb09_cooldown_clamp_zero()

	test_adb07_succeeds_base_mutation()
	test_adb07_blocked_by_state()
	test_adb07_blocked_no_mutation()
	test_adb07_blocked_by_cooldown()
	test_adb07_null_db_result_no_crash()
	test_adb07_fused_when_both_slots()
	test_adb07_fused_fallback_to_base()
	test_adb07_executor_reentrant_guard()

	test_adb10_input_key_exists()

	test_ec12_zero_cooldown_immediate()
	test_ec09_null_mutation_slot_no_crash()

	print("AttackDatabaseIntegrationTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
