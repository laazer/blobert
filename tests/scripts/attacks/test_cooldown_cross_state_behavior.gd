#
# test_cooldown_cross_state_behavior.gd
#
# Behavioral tests for cooldown behavior across player state transitions.
# Spec: project_board/specs/cooldown_cross_state_behavior_spec.md (CDB-1..CDB-5)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/12_verify_cooldown_behavior.md
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

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


func _build_controller_scene(_test_label: String) -> Dictionary:
	return AttackControllerHarness.build_controller_scene()


func _teardown(scene: Dictionary) -> void:
	AttackControllerHarness.teardown(scene)


func _get_autoload_db() -> Node:
	return AttackControllerHarness.get_autoload_db()


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
# CDB-1: State-independent cooldown decrement
# Verify cooldown decrements by delta in each PlayerState.
# ---------------------------------------------------------------------------

func test_cdb1_decrement_in_all_states() -> void:
	var all_states: Array[int] = [
		PlayerStateMachine.PlayerState.IDLE,
		PlayerStateMachine.PlayerState.WALK,
		PlayerStateMachine.PlayerState.JUMP,
		PlayerStateMachine.PlayerState.FALL,
		PlayerStateMachine.PlayerState.WALL_CLING,
		PlayerStateMachine.PlayerState.HURT,
		PlayerStateMachine.PlayerState.ABSORB,
		PlayerStateMachine.PlayerState.MUTATE,
		PlayerStateMachine.PlayerState.DEAD,
	]
	for state in all_states:
		var scene = _build_controller_scene("CDB-1_state_" + str(state))
		if scene.is_empty():
			continue
		var controller = scene["controller"]
		var psm = controller.get("_player_state_machine")
		if psm == null:
			_fail_test("CDB-1_state_" + str(state), "_player_state_machine not found")
			_teardown(scene)
			continue
		psm._state = state
		var cd = controller.get("_mutation_cooldowns")
		if cd == null:
			_fail_test("CDB-1_state_" + str(state), "_mutation_cooldowns not found")
			_teardown(scene)
			continue
		cd["cdb1_test"] = 1.0
		controller.call("_tick_controller_timers", 0.25, false)
		_assert_eq_float(
			0.75,
			cd.get("cdb1_test", -1.0),
			"CDB-1_decrement_in_state_" + str(state),
		)
		_teardown(scene)


# ---------------------------------------------------------------------------
# CDB-2: Cross-state transition cooldown continuity
# Cooldown value survives state transitions without reset or loss.
# ---------------------------------------------------------------------------

func test_cdb2a_idle_to_walk_continuity() -> void:
	var scene = _build_controller_scene("CDB-2a")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("CDB-2a", "missing psm or cooldowns")
		_teardown(scene)
		return
	psm._state = PlayerStateMachine.PlayerState.IDLE
	cd["cdb2a"] = 1.0
	controller.call("_tick_controller_timers", 0.1, false)
	_assert_eq_float(0.9, cd.get("cdb2a", -1.0), "CDB-2a_idle_tick")
	psm._state = PlayerStateMachine.PlayerState.WALK
	controller.call("_tick_controller_timers", 0.1, false)
	_assert_eq_float(0.8, cd.get("cdb2a", -1.0), "CDB-2a_walk_tick_after_idle")
	_teardown(scene)


func test_cdb2b_walk_to_jump_continuity() -> void:
	var scene = _build_controller_scene("CDB-2b")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("CDB-2b", "missing psm or cooldowns")
		_teardown(scene)
		return
	psm._state = PlayerStateMachine.PlayerState.WALK
	cd["cdb2b"] = 0.8
	controller.call("_tick_controller_timers", 0.1, false)
	_assert_eq_float(0.7, cd.get("cdb2b", -1.0), "CDB-2b_walk_tick")
	psm._state = PlayerStateMachine.PlayerState.JUMP
	controller.call("_tick_controller_timers", 0.1, false)
	_assert_eq_float(0.6, cd.get("cdb2b", -1.0), "CDB-2b_jump_tick_after_walk")
	_teardown(scene)


func test_cdb2c_jump_to_fall_continuity() -> void:
	var scene = _build_controller_scene("CDB-2c")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("CDB-2c", "missing psm or cooldowns")
		_teardown(scene)
		return
	psm._state = PlayerStateMachine.PlayerState.JUMP
	cd["cdb2c"] = 0.5
	controller.call("_tick_controller_timers", 0.1, false)
	_assert_eq_float(0.4, cd.get("cdb2c", -1.0), "CDB-2c_jump_tick")
	psm._state = PlayerStateMachine.PlayerState.FALL
	controller.call("_tick_controller_timers", 0.1, false)
	_assert_eq_float(0.3, cd.get("cdb2c", -1.0), "CDB-2c_fall_tick_after_jump")
	_teardown(scene)


func test_cdb2d_fall_to_idle_landing_continuity() -> void:
	var scene = _build_controller_scene("CDB-2d")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("CDB-2d", "missing psm or cooldowns")
		_teardown(scene)
		return
	psm._state = PlayerStateMachine.PlayerState.FALL
	cd["cdb2d"] = 0.6
	controller.call("_tick_controller_timers", 0.2, false)
	_assert_eq_float(0.4, cd.get("cdb2d", -1.0), "CDB-2d_fall_tick")
	psm._state = PlayerStateMachine.PlayerState.IDLE
	controller.call("_tick_controller_timers", 0.2, false)
	_assert_eq_float(0.2, cd.get("cdb2d", -1.0), "CDB-2d_idle_tick_after_fall")
	_teardown(scene)


func test_cdb2e_any_to_hurt_continuity() -> void:
	var scene = _build_controller_scene("CDB-2e")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("CDB-2e", "missing psm or cooldowns")
		_teardown(scene)
		return
	psm._state = PlayerStateMachine.PlayerState.IDLE
	cd["cdb2e"] = 0.5
	psm._state = PlayerStateMachine.PlayerState.HURT
	controller.call("_tick_controller_timers", 0.3, false)
	_assert_eq_float(0.2, cd.get("cdb2e", -1.0), "CDB-2e_hurt_tick_continues")
	_teardown(scene)


func test_cdb2f_hurt_to_idle_recovery_continuity() -> void:
	var scene = _build_controller_scene("CDB-2f")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("CDB-2f", "missing psm or cooldowns")
		_teardown(scene)
		return
	psm._state = PlayerStateMachine.PlayerState.HURT
	cd["cdb2f"] = 0.4
	psm._state = PlayerStateMachine.PlayerState.IDLE
	controller.call("_tick_controller_timers", 0.2, false)
	_assert_eq_float(0.2, cd.get("cdb2f", -1.0), "CDB-2f_idle_tick_after_hurt")
	_teardown(scene)


func test_cdb2g_idle_to_wall_cling_continuity() -> void:
	var scene = _build_controller_scene("CDB-2g")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("CDB-2g", "missing psm or cooldowns")
		_teardown(scene)
		return
	psm._state = PlayerStateMachine.PlayerState.IDLE
	cd["cdb2g"] = 0.7
	psm._state = PlayerStateMachine.PlayerState.WALL_CLING
	controller.call("_tick_controller_timers", 0.3, false)
	_assert_eq_float(0.4, cd.get("cdb2g", -1.0), "CDB-2g_wall_cling_tick")
	_teardown(scene)


func test_cdb2_multi_state_chain() -> void:
	var scene = _build_controller_scene("CDB-2_chain")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("CDB-2_chain", "missing psm or cooldowns")
		_teardown(scene)
		return
	cd["chain"] = 2.0
	var states: Array[int] = [
		PlayerStateMachine.PlayerState.IDLE,
		PlayerStateMachine.PlayerState.WALK,
		PlayerStateMachine.PlayerState.JUMP,
		PlayerStateMachine.PlayerState.FALL,
		PlayerStateMachine.PlayerState.IDLE,
	]
	var delta: float = 0.1
	for state in states:
		psm._state = state
		controller.call("_tick_controller_timers", delta, false)
	var expected: float = 2.0 - (delta * states.size())
	_assert_eq_float(
		expected,
		cd.get("chain", -1.0),
		"CDB-2_chain_total_decrement_across_5_states",
	)
	_teardown(scene)


# ---------------------------------------------------------------------------
# CDB-3: Death resets all cooldowns
# reset_hp() MUST clear _mutation_cooldowns.
# This is a REGRESSION test — currently fails until _mutation_cooldowns.clear()
# is added to reset_hp().
# ---------------------------------------------------------------------------

func test_cdb3a_reset_hp_clears_cooldowns() -> void:
	var scene = _build_controller_scene("CDB-3a")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("CDB-3a", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["mut_a"] = 0.5
	cd["mut_b"] = 1.0
	if not controller.has_method("reset_hp"):
		_fail_test("CDB-3a", "reset_hp method not found")
		_teardown(scene)
		return
	controller.call("reset_hp")
	_assert_eq_int(
		0,
		cd.size(),
		"CDB-3a_reset_hp_clears_all_cooldowns",
	)
	_teardown(scene)


func test_cdb3b_attack_available_after_respawn() -> void:
	var scene = _build_controller_scene("CDB-3b")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("CDB-3b", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["respawn_mut"] = 2.0
	if not controller.has_method("reset_hp"):
		_fail_test("CDB-3b", "reset_hp method not found")
		_teardown(scene)
		return
	controller.call("reset_hp")
	var remaining: float = cd.get("respawn_mut", 0.0)
	_assert_eq_float(
		0.0,
		remaining,
		"CDB-3b_cooldown_zero_after_respawn",
	)
	_teardown(scene)


func test_cdb3c_reset_applies_to_all_mutations() -> void:
	var scene = _build_controller_scene("CDB-3c")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("CDB-3c", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["claw"] = 0.3
	cd["acid"] = 1.5
	cd["spike"] = 0.7
	cd["venom"] = 2.0
	cd["fused_claw_acid"] = 3.0
	if not controller.has_method("reset_hp"):
		_fail_test("CDB-3c", "reset_hp method not found")
		_teardown(scene)
		return
	controller.call("reset_hp")
	_assert_eq_int(
		0,
		cd.size(),
		"CDB-3c_all_five_cooldowns_cleared",
	)
	_teardown(scene)


func test_cdb3_attack_fires_immediately_after_reset() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("CDB-3_fire_after_reset", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 2.0})
	db.register_base_attack("cdb3_fire_test", res)

	var scene = _setup_attack_pipeline(
		"CDB-3_fire_after_reset",
		PlayerStateMachine.PlayerState.IDLE,
		"cdb3_fire_test", "",
		{"cdb3_fire_test": 1.5},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("reset_hp") or not controller.has_method("_try_attack"):
		_fail_test("CDB-3_fire_after_reset", "missing reset_hp or _try_attack")
		_teardown(scene)
		return

	controller.call("reset_hp")

	var psm = controller.get("_player_state_machine")
	if psm != null:
		psm._state = PlayerStateMachine.PlayerState.IDLE

	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_true(fired[0], "CDB-3_attack_fires_immediately_post_reset")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CDB-4: Per-mutation independence across state changes
# Each mutation's cooldown tracks independently through state transitions.
# ---------------------------------------------------------------------------

func test_cdb4a_two_mutations_independent_across_transition() -> void:
	var scene = _build_controller_scene("CDB-4a")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("CDB-4a", "missing psm or cooldowns")
		_teardown(scene)
		return
	psm._state = PlayerStateMachine.PlayerState.IDLE
	cd["claw"] = 1.0
	cd["acid"] = 0.5
	psm._state = PlayerStateMachine.PlayerState.JUMP
	controller.call("_tick_controller_timers", 0.3, false)
	_assert_eq_float(0.7, cd.get("claw", -1.0), "CDB-4a_claw_after_transition")
	_assert_eq_float(0.2, cd.get("acid", -1.0), "CDB-4a_acid_after_transition")
	_teardown(scene)


func test_cdb4b_execute_one_does_not_affect_other() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("CDB-4b", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.5})
	db.register_base_attack("cdb4b_claw", res)

	var scene = _setup_attack_pipeline(
		"CDB-4b",
		PlayerStateMachine.PlayerState.IDLE,
		"cdb4b_claw", "",
		{"cdb4b_claw": 0.0, "cdb4b_acid": 0.5},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("CDB-4b", "_try_attack not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("CDB-4b", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	_assert_eq_float(1.5, cd.get("cdb4b_claw", -1.0), "CDB-4b_claw_cooldown_set")
	_assert_eq_float(0.5, cd.get("cdb4b_acid", -1.0), "CDB-4b_acid_unaffected")
	_teardown(scene)


func test_cdb4c_three_mutations_through_multi_state_path() -> void:
	var scene = _build_controller_scene("CDB-4c")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("CDB-4c", "missing psm or cooldowns")
		_teardown(scene)
		return
	cd["a"] = 1.0
	cd["b"] = 0.6
	cd["c"] = 0.2
	var delta: float = 0.05
	var states: Array[int] = [
		PlayerStateMachine.PlayerState.IDLE,
		PlayerStateMachine.PlayerState.WALK,
		PlayerStateMachine.PlayerState.JUMP,
	]
	for state in states:
		psm._state = state
		controller.call("_tick_controller_timers", delta, false)
	var total_elapsed: float = delta * states.size()
	_assert_eq_float(1.0 - total_elapsed, cd.get("a", -1.0), "CDB-4c_a_independent")
	_assert_eq_float(0.6 - total_elapsed, cd.get("b", -1.0), "CDB-4c_b_independent")
	_assert_eq_float(0.2 - total_elapsed, cd.get("c", -1.0), "CDB-4c_c_independent")
	_teardown(scene)


func test_cdb4_fused_key_independent_from_base_keys() -> void:
	var scene = _build_controller_scene("CDB-4_fused")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("CDB-4_fused", "missing psm or cooldowns")
		_teardown(scene)
		return
	cd["claw"] = 1.0
	cd["acid"] = 0.8
	cd["acid_claw"] = 2.0
	psm._state = PlayerStateMachine.PlayerState.IDLE
	controller.call("_tick_controller_timers", 0.5, false)
	psm._state = PlayerStateMachine.PlayerState.WALK
	controller.call("_tick_controller_timers", 0.3, false)
	_assert_eq_float(0.2, cd.get("claw", -1.0), "CDB-4_fused_claw_independent")
	_assert_eq_float(0.0, cd.get("acid", -1.0), "CDB-4_fused_acid_independent")
	_assert_eq_float(1.2, cd.get("acid_claw", -1.0), "CDB-4_fused_key_independent")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CDB-5: Rapid input rejection during cooldown across state boundaries
# Attacks must be rejected while cooldown > 0 regardless of state transitions.
# ---------------------------------------------------------------------------

func test_cdb5a_attack_rejected_idle_during_cooldown() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("CDB-5a", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
	db.register_base_attack("cdb5a_mut", res)

	var scene = _setup_attack_pipeline(
		"CDB-5a",
		PlayerStateMachine.PlayerState.IDLE,
		"cdb5a_mut", "",
		{"cdb5a_mut": 0.5},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("CDB-5a", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], "CDB-5a_rejected_idle_during_cooldown")
	_teardown(scene)


func test_cdb5b_attack_rejected_walk_during_cooldown() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("CDB-5b", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
	db.register_base_attack("cdb5b_mut", res)

	var scene = _setup_attack_pipeline(
		"CDB-5b",
		PlayerStateMachine.PlayerState.WALK,
		"cdb5b_mut", "",
		{"cdb5b_mut": 0.5},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("CDB-5b", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], "CDB-5b_rejected_walk_during_cooldown")
	_teardown(scene)


func test_cdb5c_rejected_after_multi_state_transition() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("CDB-5c", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 2.0})
	db.register_base_attack("cdb5c_mut", res)

	var scene = _setup_attack_pipeline(
		"CDB-5c",
		PlayerStateMachine.PlayerState.IDLE,
		"cdb5c_mut", "",
		{"cdb5c_mut": 1.0},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	if psm == null or not controller.has_method("_try_attack"):
		_fail_test("CDB-5c", "missing psm or _try_attack")
		_teardown(scene)
		return
	controller.call("_tick_controller_timers", 0.1, false)
	psm._state = PlayerStateMachine.PlayerState.JUMP
	controller.call("_tick_controller_timers", 0.1, false)
	psm._state = PlayerStateMachine.PlayerState.FALL
	controller.call("_tick_controller_timers", 0.1, false)
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], "CDB-5c_rejected_after_idle_jump_fall")
	_teardown(scene)


func test_cdb5d_succeeds_after_cooldown_expires_post_transition() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("CDB-5d", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
	db.register_base_attack("cdb5d_mut", res)

	var scene = _setup_attack_pipeline(
		"CDB-5d",
		PlayerStateMachine.PlayerState.IDLE,
		"cdb5d_mut", "",
		{"cdb5d_mut": 0.1},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	if psm == null or not controller.has_method("_try_attack"):
		_fail_test("CDB-5d", "missing psm or _try_attack")
		_teardown(scene)
		return
	controller.call("_tick_controller_timers", 0.2, false)
	psm._state = PlayerStateMachine.PlayerState.WALK
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_true(fired[0], "CDB-5d_attack_succeeds_after_expiry_in_walk")
	_teardown(scene)


func test_cdb5e_rapid_calls_do_not_bypass() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("CDB-5e", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 2.0})
	db.register_base_attack("cdb5e_mut", res)

	var scene = _setup_attack_pipeline(
		"CDB-5e",
		PlayerStateMachine.PlayerState.IDLE,
		"cdb5e_mut", "",
		{"cdb5e_mut": 1.0},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	if psm == null or not controller.has_method("_try_attack"):
		_fail_test("CDB-5e", "missing psm or _try_attack")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var attack_count = [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): attack_count[0] += 1)
	for i in range(5):
		controller.call("_try_attack")
	_assert_eq_int(0, attack_count[0], "CDB-5e_five_rapid_calls_all_rejected")
	psm._state = PlayerStateMachine.PlayerState.JUMP
	for i in range(5):
		controller.call("_try_attack")
	_assert_eq_int(0, attack_count[0], "CDB-5e_five_more_in_jump_all_rejected")
	_teardown(scene)


func test_cdb5f_state_gate_rejects_even_at_zero_cooldown() -> void:
	var scene = _setup_attack_pipeline(
		"CDB-5f",
		PlayerStateMachine.PlayerState.HURT,
		"cdb5f_mut", "",
		{"cdb5f_mut": 0.0},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("CDB-5f", "_try_attack not found")
		_teardown(scene)
		return

	var db = _get_autoload_db()
	if db != null:
		var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
		db.register_base_attack("cdb5f_mut", res)

	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], "CDB-5f_hurt_state_blocks_even_zero_cooldown")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CDB-2 + CDB-5 combined: Full cross-state lifecycle with attack
# Attack in state A, transition through B,C,D, attack succeeds after expiry in E
# ---------------------------------------------------------------------------

func test_cross_state_lifecycle_attack_refire() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("CDB_lifecycle", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 0.5})
	db.register_base_attack("cdb_lc_mut", res)

	var scene = _setup_attack_pipeline(
		"CDB_lifecycle",
		PlayerStateMachine.PlayerState.IDLE,
		"cdb_lc_mut", "",
		{},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	if psm == null or not controller.has_method("_try_attack"):
		_fail_test("CDB_lifecycle", "missing psm or _try_attack")
		_teardown(scene)
		return

	var executor = scene.get("executor")
	var attack_count = [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): attack_count[0] += 1)

	controller.call("_try_attack")
	_assert_eq_int(1, attack_count[0], "CDB_lc_initial_attack_fires")

	psm._state = PlayerStateMachine.PlayerState.WALK
	controller.call("_tick_controller_timers", 0.15, false)
	controller.call("_try_attack")
	_assert_eq_int(1, attack_count[0], "CDB_lc_blocked_in_walk")

	psm._state = PlayerStateMachine.PlayerState.JUMP
	controller.call("_tick_controller_timers", 0.15, false)
	controller.call("_try_attack")
	_assert_eq_int(1, attack_count[0], "CDB_lc_blocked_in_jump")

	psm._state = PlayerStateMachine.PlayerState.FALL
	controller.call("_tick_controller_timers", 0.25, false)
	controller.call("_try_attack")
	_assert_eq_int(2, attack_count[0], "CDB_lc_fires_after_expiry_in_fall")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== CooldownCrossStateBehaviorTests ===")

	test_cdb1_decrement_in_all_states()

	test_cdb2a_idle_to_walk_continuity()
	test_cdb2b_walk_to_jump_continuity()
	test_cdb2c_jump_to_fall_continuity()
	test_cdb2d_fall_to_idle_landing_continuity()
	test_cdb2e_any_to_hurt_continuity()
	test_cdb2f_hurt_to_idle_recovery_continuity()
	test_cdb2g_idle_to_wall_cling_continuity()
	test_cdb2_multi_state_chain()

	test_cdb3a_reset_hp_clears_cooldowns()
	test_cdb3b_attack_available_after_respawn()
	test_cdb3c_reset_applies_to_all_mutations()
	test_cdb3_attack_fires_immediately_after_reset()

	test_cdb4a_two_mutations_independent_across_transition()
	test_cdb4b_execute_one_does_not_affect_other()
	test_cdb4c_three_mutations_through_multi_state_path()
	test_cdb4_fused_key_independent_from_base_keys()

	test_cdb5a_attack_rejected_idle_during_cooldown()
	test_cdb5b_attack_rejected_walk_during_cooldown()
	test_cdb5c_rejected_after_multi_state_transition()
	test_cdb5d_succeeds_after_cooldown_expires_post_transition()
	test_cdb5e_rapid_calls_do_not_bypass()
	test_cdb5f_state_gate_rejects_even_at_zero_cooldown()

	test_cross_state_lifecycle_attack_refire()

	print("CooldownCrossStateBehaviorTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
