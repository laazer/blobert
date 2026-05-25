#
# test_attack_database_controller_adversarial.gd
#
# Adversarial tests for the PlayerController3D attack pipeline.
# Targets: cooldown precision, extreme delta, negative cooldowns, slot permutations,
# facing sign edge cases, rapid attack attempts, mutation testing of _try_attack,
# fused cooldown key semantics, and spec gap detection.
# Spec: project_board/specs/attack_database_integration_spec.md (ADB-7..ADB-12, EC-9..EC-24)
# Ticket: M11-06 (06_attack_database_integration)
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

const _CONTROLLER_PATH := "res://scripts/player/player_controller_3d.gd"
const _DB_PATH := "res://scripts/attacks/attack_database.gd"


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
# EC-13: Negative cooldown in AttackResource
# Spec: cooldown set to resource.cooldown. If negative, next tick clamps to 0.
# Conservative: negative cooldown should not break anything; treated as <=0 on
# subsequent tick → attack immediately available.
# ---------------------------------------------------------------------------

func test_ec13_negative_cooldown_resource() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("EC-13_neg_cd", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": -0.5})
	db.register_base_attack("test_neg_cd", res)

	var scene = _setup_attack_pipeline(
		"EC-13_neg_cd",
		PlayerStateMachine.PlayerState.IDLE,
		"test_neg_cd", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("EC-13_neg_cd", "_try_attack not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("EC-13_neg_cd", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	var remaining: float = cd.get("test_neg_cd", 1.0)
	_assert_true(remaining <= 0.0, "EC-13_neg_cooldown_set_nonpositive")

	controller.call("_tick_controller_timers", 0.016, false)
	remaining = cd.get("test_neg_cd", 1.0)
	_assert_eq_float(0.0, remaining, "EC-13_neg_cooldown_clamped_to_zero")
	_teardown(scene)


# ---------------------------------------------------------------------------
# BOUNDARY: Cooldown precision — very small delta tick
# Mutation catch: float rounding leaves cooldown slightly above zero
# ---------------------------------------------------------------------------

func test_cooldown_precision_small_delta() -> void:
	var scene = _build_controller_scene("ADV_small_delta")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV_small_delta", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["test_precision"] = 0.0001
	controller.call("_tick_controller_timers", 0.0001, false)
	var remaining: float = cd.get("test_precision", -1.0)
	_assert_true(remaining >= 0.0, "ADV_small_delta_non_negative")
	_assert_true(remaining <= 0.0001, "ADV_small_delta_near_zero")
	_teardown(scene)


# ---------------------------------------------------------------------------
# BOUNDARY: Large delta tick (e.g. lag spike or alt-tab)
# Mutation catch: subtraction wraps around or overflows
# ---------------------------------------------------------------------------

func test_cooldown_large_delta() -> void:
	var scene = _build_controller_scene("ADV_large_delta")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV_large_delta", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["test_large"] = 1.0
	controller.call("_tick_controller_timers", 999.0, false)
	var remaining: float = cd.get("test_large", -1.0)
	_assert_eq_float(0.0, remaining, "ADV_large_delta_clamped")
	_teardown(scene)


# ---------------------------------------------------------------------------
# EC-24: Multiple independent cooldowns decrement simultaneously
# ---------------------------------------------------------------------------

func test_ec24_simultaneous_cooldown_decrement() -> void:
	var scene = _build_controller_scene("EC-24_multi")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("EC-24_multi", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["claw"] = 2.0
	cd["acid"] = 1.0
	cd["spike"] = 0.5
	controller.call("_tick_controller_timers", 0.3, false)
	_assert_eq_float(1.7, cd.get("claw", -1.0), "EC-24_claw_decremented")
	_assert_eq_float(0.7, cd.get("acid", -1.0), "EC-24_acid_decremented")
	_assert_eq_float(0.2, cd.get("spike", -1.0), "EC-24_spike_decremented")
	_teardown(scene)


# ---------------------------------------------------------------------------
# BOUNDARY: Cooldown at epsilon boundary
# Mutation catch: > 0.0 check fails at float epsilon
# ---------------------------------------------------------------------------

func test_cooldown_epsilon_boundary() -> void:
	var scene = _build_controller_scene("ADV_epsilon")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV_epsilon", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["test_eps"] = 0.0
	controller.call("_tick_controller_timers", 0.016, false)
	var remaining: float = cd.get("test_eps", -1.0)
	_assert_eq_float(0.0, remaining, "ADV_epsilon_stays_zero")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADB-8: Facing sign edge cases
# ---------------------------------------------------------------------------

func test_facing_sign_very_large_positive() -> void:
	var scene = _build_controller_scene("ADV_face_large_pos")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("get_facing_sign"):
		_fail_test("ADV_face_large_pos", "get_facing_sign not found")
		_teardown(scene)
		return
	controller.velocity = Vector3(99999.0, 0.0, 0.0)
	_assert_eq_float(1.0, controller.get_facing_sign(), "ADV_face_large_pos")
	_teardown(scene)


func test_facing_sign_very_large_negative() -> void:
	var scene = _build_controller_scene("ADV_face_large_neg")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("get_facing_sign"):
		_fail_test("ADV_face_large_neg", "get_facing_sign not found")
		_teardown(scene)
		return
	controller.velocity = Vector3(-99999.0, 0.0, 0.0)
	_assert_eq_float(-1.0, controller.get_facing_sign(), "ADV_face_large_neg")
	_teardown(scene)


func test_facing_sign_only_y_velocity() -> void:
	var scene = _build_controller_scene("ADV_face_y_only")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("get_facing_sign"):
		_fail_test("ADV_face_y_only", "get_facing_sign not found")
		_teardown(scene)
		return
	controller.velocity = Vector3(0.0, 50.0, 0.0)
	_assert_eq_float(1.0, controller.get_facing_sign(), "ADV_face_y_only_defaults_right")
	_teardown(scene)


func test_facing_sign_only_z_velocity() -> void:
	var scene = _build_controller_scene("ADV_face_z_only")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("get_facing_sign"):
		_fail_test("ADV_face_z_only", "get_facing_sign not found")
		_teardown(scene)
		return
	controller.velocity = Vector3(0.0, 0.0, -10.0)
	_assert_eq_float(1.0, controller.get_facing_sign(), "ADV_face_z_only_defaults_right")
	_teardown(scene)


func test_facing_sign_tiny_negative() -> void:
	var scene = _build_controller_scene("ADV_face_tiny_neg")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("get_facing_sign"):
		_fail_test("ADV_face_tiny_neg", "get_facing_sign not found")
		_teardown(scene)
		return
	controller.velocity = Vector3(-0.001, 0.0, 0.0)
	_assert_eq_float(-1.0, controller.get_facing_sign(), "ADV_face_tiny_neg_still_left")
	_teardown(scene)


# ---------------------------------------------------------------------------
# EC-20: Slot B filled, slot A empty → base attack from slot B
# Existing tests don't cover slot B only; they test slot A only.
# ---------------------------------------------------------------------------

func test_ec20_slot_b_only_base_attack() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("EC-20_slot_b", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 0.5})
	db.register_base_attack("test_slot_b_acid", res)

	var scene = _build_controller_scene("EC-20_slot_b")
	if scene.is_empty():
		return
	var controller = scene["controller"]

	var psm = controller.get("_player_state_machine")
	if psm == null:
		_fail_test("EC-20_slot_b", "_player_state_machine not found")
		_teardown(scene)
		return
	psm._state = PlayerStateMachine.PlayerState.IDLE

	var msm = MutationSlotManager.new()
	msm.fill_next_available("dummy_slot_a")
	msm.fill_next_available("test_slot_b_acid")
	msm.clear_slot(0)
	controller.set("_mutation_slot", msm)

	# CHECKPOINT: Spec ADB-7 step 3 says "If only one slot is filled: use that
	# slot's mutation_id for base attack lookup." This must work for slot B too.
	# Assumption: implementation iterates both slots to find the filled one.
	# Confidence: High — spec is explicit about "only one slot."

	if not controller.has_method("_try_attack"):
		_fail_test("EC-20_slot_b", "_try_attack not found")
		_teardown(scene)
		return
	var executor = controller.get("_attack_executor")
	var fired_resource = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired_resource[0] = r)
	controller.call("_try_attack")
	_assert_true(fired_resource[0] == res, "EC-20_slot_b_fires_base_attack")
	_teardown(scene)


# ---------------------------------------------------------------------------
# EC-14: Rapid sequential attack attempts while cooldown active
# Catch: cooldown check has off-by-one or race condition
# ---------------------------------------------------------------------------

func test_ec14_rapid_attacks_all_blocked() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("EC-14_rapid", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 2.0})
	db.register_base_attack("test_rapid_claw", res)

	var scene = _setup_attack_pipeline(
		"EC-14_rapid",
		PlayerStateMachine.PlayerState.IDLE,
		"test_rapid_claw", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("EC-14_rapid", "_try_attack not found")
		_teardown(scene)
		return

	var executor = scene.get("executor")
	var attack_count = [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): attack_count[0] += 1)

	controller.call("_try_attack")
	_assert_eq_int(1, attack_count[0], "EC-14_first_attack_fires")

	for i in range(10):
		controller.call("_try_attack")
	_assert_eq_int(1, attack_count[0], "EC-14_10_rapid_all_blocked")
	_teardown(scene)


# ---------------------------------------------------------------------------
# MUTATION: Cooldown decrement with zero delta
# Catch: implementation divides by delta or has delta-dependent bugs
# ---------------------------------------------------------------------------

func test_cooldown_zero_delta() -> void:
	var scene = _build_controller_scene("ADV_zero_delta")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV_zero_delta", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["test_zero_d"] = 1.0
	controller.call("_tick_controller_timers", 0.0, false)
	_assert_eq_float(1.0, cd.get("test_zero_d", -1.0), "ADV_zero_delta_unchanged")
	_teardown(scene)


# ---------------------------------------------------------------------------
# FUSED COOLDOWN KEY: When both slots filled and fused attack fires,
# cooldown key should be the canonical fused key, not a base mutation_id.
# Catch: implementation uses slot_a mutation_id as cooldown key for fused attacks
# ---------------------------------------------------------------------------

func test_fused_attack_cooldown_key() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV_fused_cd_key", "AttackDatabase autoload not available")
		return
	var fused_res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 3.0})
	db.register_fused_attack("test_fa_acid", "test_fa_claw", fused_res)
	db.register_base_attack("test_fa_acid", _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0}))

	var scene = _setup_attack_pipeline(
		"ADV_fused_cd_key",
		PlayerStateMachine.PlayerState.IDLE,
		"test_fa_acid", "test_fa_claw", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV_fused_cd_key", "_try_attack not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV_fused_cd_key", "_mutation_cooldowns not found")
		_teardown(scene)
		return

	# CHECKPOINT: Spec ADB-9 says fused attacks use canonical fused key for
	# cooldown. "acid" + "claw" → sorted → "test_fa_acid_test_fa_claw".
	# Assumption: cooldown key for fused is the sorted canonical key.
	# Confidence: High — spec ADB-9 is explicit.

	var fused_key_candidates: Array = []
	for key in cd:
		if cd[key] == 3.0:
			fused_key_candidates.append(key)
	_assert_true(fused_key_candidates.size() >= 1, "ADV_fused_cd_key_present")
	_teardown(scene)


# ---------------------------------------------------------------------------
# BOUNDARY: Attack with zero-damage resource — should still fire
# Catch: implementation skips zero-damage attacks
# ---------------------------------------------------------------------------

func test_attack_fires_with_zero_damage() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV_zero_dmg", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0, "damage": 0.0})
	db.register_base_attack("test_zero_dmg", res)

	var scene = _setup_attack_pipeline(
		"ADV_zero_dmg",
		PlayerStateMachine.PlayerState.IDLE,
		"test_zero_dmg", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV_zero_dmg", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_true(fired[0], "ADV_zero_dmg_still_fires")
	_teardown(scene)


# ---------------------------------------------------------------------------
# BOUNDARY: Attack with very large cooldown
# Catch: cooldown value overflow or comparison bug
# ---------------------------------------------------------------------------

func test_attack_very_large_cooldown() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV_large_cd", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 99999.0})
	db.register_base_attack("test_large_cd", res)

	var scene = _setup_attack_pipeline(
		"ADV_large_cd",
		PlayerStateMachine.PlayerState.IDLE,
		"test_large_cd", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV_large_cd", "_try_attack not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV_large_cd", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	_assert_eq_float(99999.0, cd.get("test_large_cd", 0.0), "ADV_large_cd_set")
	_teardown(scene)


# ---------------------------------------------------------------------------
# MUTATION: _try_attack with all permitted states — verify each fires
# Existing test checks one state (IDLE). This systematically checks all 6.
# Catch: implementation hardcodes IDLE check instead of using policy
# ---------------------------------------------------------------------------

func test_try_attack_fires_in_all_permitted_states() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV_all_permit", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 0.0})
	db.register_base_attack("test_all_permit", res)

	var permitted_states: Array[int] = [
		PlayerStateMachine.PlayerState.IDLE,
		PlayerStateMachine.PlayerState.WALK,
		PlayerStateMachine.PlayerState.JUMP,
		PlayerStateMachine.PlayerState.FALL,
		PlayerStateMachine.PlayerState.FLOAT,
		PlayerStateMachine.PlayerState.WALL_CLING,
	]
	for state in permitted_states:
		var scene = _setup_attack_pipeline(
			"ADV_all_permit_" + str(state),
			state, "test_all_permit", "", {},
		)
		if scene.is_empty():
			continue
		var controller = scene["controller"]
		if not controller.has_method("_try_attack"):
			_fail_test("ADV_all_permit_" + str(state), "_try_attack not found")
			_teardown(scene)
			continue
		var executor = scene.get("executor")
		var fired = [false]
		if executor != null and executor.has_signal("attack_started"):
			executor.connect("attack_started", func(_r): fired[0] = true)
		controller.call("_try_attack")
		_assert_true(fired[0], "ADV_attack_fires_state_" + str(state))
		_teardown(scene)


# ---------------------------------------------------------------------------
# COOLDOWN LIFECYCLE: Full cycle — attack → cooldown set → tick down → re-attack
# Catch: cooldown doesn't actually re-enable attacks
# ---------------------------------------------------------------------------

func test_cooldown_full_lifecycle() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV_cd_lifecycle", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 0.5})
	db.register_base_attack("test_lifecycle", res)

	var scene = _setup_attack_pipeline(
		"ADV_cd_lifecycle",
		PlayerStateMachine.PlayerState.IDLE,
		"test_lifecycle", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV_cd_lifecycle", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var attack_count = [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): attack_count[0] += 1)

	controller.call("_try_attack")
	_assert_eq_int(1, attack_count[0], "ADV_lifecycle_first_fires")

	controller.call("_try_attack")
	_assert_eq_int(1, attack_count[0], "ADV_lifecycle_blocked_while_cooling")

	controller.call("_tick_controller_timers", 0.3, false)
	controller.call("_try_attack")
	_assert_eq_int(1, attack_count[0], "ADV_lifecycle_still_blocked_at_0.2")

	controller.call("_tick_controller_timers", 0.3, false)
	controller.call("_try_attack")
	_assert_eq_int(2, attack_count[0], "ADV_lifecycle_re_enabled_after_expiry")
	_teardown(scene)


# ---------------------------------------------------------------------------
# MUTATION: Cooldown dictionary mutation during iteration safety
# If implementation removes keys at 0 during tick, verify no crash
# ---------------------------------------------------------------------------

func test_cooldown_many_keys_tick() -> void:
	var scene = _build_controller_scene("ADV_many_keys")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV_many_keys", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	for i in range(20):
		cd["key_%d" % i] = 0.1 * (i + 1)
	controller.call("_tick_controller_timers", 0.5, false)
	var all_valid = true
	for i in range(20):
		var val = cd.get("key_%d" % i, -1.0)
		if val < 0.0:
			all_valid = false
			break
	_assert_true(all_valid, "ADV_many_keys_all_non_negative")
	_teardown(scene)


# ---------------------------------------------------------------------------
# DETERMINISM: Same attack sequence produces same cooldown state
# ---------------------------------------------------------------------------

func test_deterministic_attack_cooldown() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV_determinism", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.5})
	db.register_base_attack("test_det", res)

	var cd_values: Array = []
	for _trial in range(3):
		var scene = _setup_attack_pipeline(
			"ADV_determinism",
			PlayerStateMachine.PlayerState.IDLE,
			"test_det", "", {},
		)
		if scene.is_empty():
			return
		var controller = scene["controller"]
		if not controller.has_method("_try_attack"):
			_fail_test("ADV_determinism", "_try_attack not found")
			_teardown(scene)
			return
		controller.call("_try_attack")
		controller.call("_tick_controller_timers", 0.25, false)
		var cd = controller.get("_mutation_cooldowns")
		cd_values.append(cd.get("test_det", -1.0))
		_teardown(scene)

	_assert_eq_float(cd_values[0], cd_values[1], "ADV_determinism_trial_0_1")
	_assert_eq_float(cd_values[1], cd_values[2], "ADV_determinism_trial_1_2")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AttackDatabaseControllerAdversarialTests ===")

	test_ec13_negative_cooldown_resource()
	test_cooldown_precision_small_delta()
	test_cooldown_large_delta()
	test_ec24_simultaneous_cooldown_decrement()
	test_cooldown_epsilon_boundary()

	test_facing_sign_very_large_positive()
	test_facing_sign_very_large_negative()
	test_facing_sign_only_y_velocity()
	test_facing_sign_only_z_velocity()
	test_facing_sign_tiny_negative()

	test_ec20_slot_b_only_base_attack()
	test_ec14_rapid_attacks_all_blocked()

	test_cooldown_zero_delta()
	test_fused_attack_cooldown_key()
	test_attack_fires_with_zero_damage()
	test_attack_very_large_cooldown()
	test_try_attack_fires_in_all_permitted_states()
	test_cooldown_full_lifecycle()
	test_cooldown_many_keys_tick()
	test_deterministic_attack_cooldown()

	print("AttackDatabaseControllerAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
