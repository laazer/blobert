#
# test_cooldown_cross_state_adversarial.gd
#
# Adversarial edge-case tests for cooldown cross-state behavior.
# Targets runtime seams in _tick_controller_timers(), _try_attack(), reset_hp().
# Spec: project_board/specs/cooldown_cross_state_behavior_spec.md (CDB-1..CDB-5)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/12_verify_cooldown_behavior.md
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

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
	test_label: String, state: int,
	slot_a_id: String, slot_b_id: String, cooldowns: Dictionary,
) -> Dictionary:
	var scene = _build_controller_scene(test_label)
	if scene.is_empty():
		return {}
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	if psm == null:
		_fail_test(test_label, "_player_state_machine not found")
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
		_fail_test(test_label, "_mutation_cooldowns not found")
		_teardown(scene)
		return {}
	for key in cooldowns:
		cd_dict[key] = cooldowns[key]
	scene["executor"] = controller.get("_attack_executor")
	scene["slot_manager"] = msm
	return scene


# ---------------------------------------------------------------------------
# ADV-1: Negative delta must not increase cooldown
# maxf(0.0, val - (-delta)) = maxf(0.0, val + |delta|) → INCREASES cooldown.
# This exposes a missing guard: engine shouldn't pass negative delta, but no
# defensive clamp exists. # CHECKPOINT
# ---------------------------------------------------------------------------

func test_adv1_negative_delta_does_not_increase_cooldown() -> void:
	var scene = _build_controller_scene("ADV-1_neg_delta")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV-1_neg_delta", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["neg_test"] = 0.5
	controller.call("_tick_controller_timers", -0.1, false)
	var result: float = cd.get("neg_test", -1.0)
	_assert_true(
		result <= 0.5,
		"ADV-1_neg_delta_should_not_increase",
		"cooldown grew from 0.5 to " + str(result) + " with negative delta"
	)
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-2: Zero delta produces no change (paused physics)
# ---------------------------------------------------------------------------

func test_adv2_zero_delta_no_change() -> void:
	var scene = _build_controller_scene("ADV-2_zero_delta")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV-2_zero_delta", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["zero_test"] = 0.75
	controller.call("_tick_controller_timers", 0.0, false)
	_assert_eq_float(0.75, cd.get("zero_test", -1.0), "ADV-2_zero_delta_unchanged")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-3: Very large / max-float delta floors cooldown at 0.0
# ---------------------------------------------------------------------------

func test_adv3_large_delta_floors_at_zero() -> void:
	var scene = _build_controller_scene("ADV-3_large_delta")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV-3_large_delta", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["large_test"] = 1.0
	controller.call("_tick_controller_timers", 9999.0, false)
	_assert_eq_float(0.0, cd.get("large_test", -1.0), "ADV-3_large_delta_floors_zero")
	cd["large_test"] = 5.0
	controller.call("_tick_controller_timers", 1.79769e308, false)
	var result: float = cd.get("large_test", -1.0)
	_assert_true(result >= 0.0, "ADV-3_max_float_no_negative", "got " + str(result))
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-4: Empty cooldowns dictionary — tick is a safe no-op
# ---------------------------------------------------------------------------

func test_adv4_empty_dict_tick_no_crash() -> void:
	var scene = _build_controller_scene("ADV-4_empty_dict")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV-4_empty_dict", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd.clear()
	controller.call("_tick_controller_timers", 0.5, false)
	_assert_eq_int(0, cd.size(), "ADV-4_empty_dict_still_empty")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-5: Absent cooldown key — .get(key, 0.0) returns 0.0, attack fires
# ---------------------------------------------------------------------------

func test_adv5_absent_key_allows_attack() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV-5_absent_key", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
	db.register_base_attack("adv5_mut", res)
	var scene = _setup_attack_pipeline(
		"ADV-5_absent_key", PlayerStateMachine.PlayerState.IDLE, "adv5_mut", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV-5_absent_key", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_true(fired[0], "ADV-5_absent_key_attack_fires")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-6: Exact 0.0 boundary allows attack (check is > 0.0, not >= 0.0)
# ---------------------------------------------------------------------------

func test_adv6_exact_zero_boundary_allows_attack() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV-6_zero_boundary", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
	db.register_base_attack("adv6_mut", res)
	var scene = _setup_attack_pipeline(
		"ADV-6_zero_boundary", PlayerStateMachine.PlayerState.IDLE,
		"adv6_mut", "", {"adv6_mut": 0.0},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV-6_zero_boundary", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_true(fired[0], "ADV-6_zero_boundary_attack_fires")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-7: Float accumulation precision — 100 ticks of 0.01 from 1.0
# ---------------------------------------------------------------------------

func test_adv7_float_accumulation_precision() -> void:
	var scene = _build_controller_scene("ADV-7_float_accum")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV-7_float_accum", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["accum_test"] = 1.0
	for i in range(100):
		controller.call("_tick_controller_timers", 0.01, false)
	var result: float = cd.get("accum_test", -1.0)
	_assert_true(
		result >= 0.0 and result < 0.001,
		"ADV-7_float_accum_reaches_zero",
		"expected ~0.0, got " + str(result)
	)
	# Extended: 200 ticks past zero must stay at 0.0
	cd["neg_guard"] = 0.05
	for i in range(200):
		controller.call("_tick_controller_timers", 0.01, false)
	_assert_eq_float(0.0, cd.get("neg_guard", -1.0), "ADV-7_never_goes_negative")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-8: Stress — 50 simultaneous cooldown keys all decrement correctly
# ---------------------------------------------------------------------------

func test_adv8_stress_many_cooldown_keys() -> void:
	var scene = _build_controller_scene("ADV-8_stress")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV-8_stress", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	var key_count: int = 50
	for i in range(key_count):
		cd["stress_" + str(i)] = float(i) * 0.1
	controller.call("_tick_controller_timers", 0.05, false)
	var all_ok: bool = true
	for i in range(key_count):
		var expected: float = maxf(0.0, float(i) * 0.1 - 0.05)
		var actual: float = cd.get("stress_" + str(i), -1.0)
		if absf(actual - expected) > 0.0001:
			all_ok = false
			_fail_test("ADV-8_stress_key_" + str(i), "expected " + str(expected) + ", got " + str(actual))
			break
	if all_ok:
		_pass_test("ADV-8_stress_all_50_keys_decremented_correctly")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-9: Rapid state oscillation — tick once despite many state flips
# ---------------------------------------------------------------------------

func test_adv9_state_oscillation_single_tick() -> void:
	var scene = _build_controller_scene("ADV-9_oscillation")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("ADV-9_oscillation", "missing psm or cooldowns")
		_teardown(scene)
		return
	cd["osc_test"] = 1.0
	for i in range(20):
		psm._state = PlayerStateMachine.PlayerState.IDLE if i % 2 == 0 else PlayerStateMachine.PlayerState.WALK
	controller.call("_tick_controller_timers", 0.1, false)
	_assert_eq_float(0.9, cd.get("osc_test", -1.0), "ADV-9_single_tick_despite_oscillation")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-10: Fused key sorting — sorted pair produces deterministic key
# ---------------------------------------------------------------------------

func test_adv10_fused_key_sorted_determinism() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV-10_fused_sort", "AttackDatabase autoload not available")
		return
	var fused_res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 3.0})
	if not db.has_method("register_fused_attack"):
		_fail_test("ADV-10_fused_sort", "register_fused_attack not available")
		return
	db.register_fused_attack("acid", "claw", fused_res)
	var scene = _setup_attack_pipeline(
		"ADV-10_fused_sort", PlayerStateMachine.PlayerState.IDLE, "acid", "claw", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV-10_fused_sort", "_try_attack not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	_assert_true(cd.has("acid_claw"), "ADV-10_fused_key_is_acid_claw_sorted")
	_teardown(scene)


func test_adv10b_fused_key_reverse_slot_order() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV-10b", "AttackDatabase autoload not available")
		return
	if not db.has_method("register_fused_attack"):
		_fail_test("ADV-10b", "register_fused_attack not available")
		return
	var fused_res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 2.5})
	db.register_fused_attack("beta", "alpha", fused_res)
	var scene = _setup_attack_pipeline(
		"ADV-10b", PlayerStateMachine.PlayerState.IDLE, "beta", "alpha", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV-10b", "_try_attack not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	_assert_true(
		cd.has("alpha_beta"), "ADV-10b_reverse_slots_produce_sorted_key",
		"expected 'alpha_beta', found: " + str(cd.keys())
	)
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-11: Attack resource with cooldown=0.0 — documents spam potential
# # CHECKPOINT: Zero cooldown is a design decision; test documents behavior.
# ---------------------------------------------------------------------------

func test_adv11_zero_cooldown_resource() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV-11_zero_cd", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 0.0})
	db.register_base_attack("adv11_zero_cd", res)
	var scene = _setup_attack_pipeline(
		"ADV-11_zero_cd", PlayerStateMachine.PlayerState.IDLE, "adv11_zero_cd", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV-11_zero_cd", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var attack_count = [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): attack_count[0] += 1)
	controller.call("_try_attack")
	_assert_true(attack_count[0] >= 1, "ADV-11_zero_cd_first_fires", "count=" + str(attack_count[0]))
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-12/13: Null guards — _try_attack with null policy/slot
# ---------------------------------------------------------------------------

func test_adv12_null_input_policy_no_crash() -> void:
	var scene = _build_controller_scene("ADV-12")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	controller.set("_input_policy", null)
	if not controller.has_method("_try_attack"):
		_fail_test("ADV-12", "_try_attack not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	_pass_test("ADV-12_null_policy_no_crash")
	_teardown(scene)


func test_adv13_null_mutation_slot_no_crash() -> void:
	var scene = _build_controller_scene("ADV-13")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	controller.set("_mutation_slot", null)
	if not controller.has_method("_try_attack"):
		_fail_test("ADV-13", "_try_attack not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	_pass_test("ADV-13_null_slot_no_crash")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-14: Empty mutation slots — attack rejected
# ---------------------------------------------------------------------------

func test_adv14_empty_mutation_slots_rejected() -> void:
	var scene = _build_controller_scene("ADV-14")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	if psm == null:
		_fail_test("ADV-14", "_player_state_machine not found")
		_teardown(scene)
		return
	psm._state = PlayerStateMachine.PlayerState.IDLE
	controller.set("_mutation_slot", MutationSlotManager.new())
	if not controller.has_method("_try_attack"):
		_fail_test("ADV-14", "_try_attack not found")
		_teardown(scene)
		return
	var executor = controller.get("_attack_executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], "ADV-14_empty_slots_no_attack")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-15: reset_hp then tick — no ghost residual entries
# ---------------------------------------------------------------------------

func test_adv15_reset_then_tick_no_ghost_residual() -> void:
	var scene = _build_controller_scene("ADV-15")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null or not controller.has_method("reset_hp"):
		_fail_test("ADV-15", "missing cooldowns or reset_hp")
		_teardown(scene)
		return
	cd["ghost_a"] = 1.0
	cd["ghost_b"] = 2.0
	controller.call("reset_hp")
	controller.call("_tick_controller_timers", 0.5, false)
	_assert_eq_int(0, cd.size(), "ADV-15_no_ghost_after_reset_and_tick")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-16: DEAD state with active cooldown — tick doesn't crash
# ---------------------------------------------------------------------------

func test_adv16_dead_state_tick_continues() -> void:
	var scene = _build_controller_scene("ADV-16")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	var cd = controller.get("_mutation_cooldowns")
	if psm == null or cd == null:
		_fail_test("ADV-16", "missing psm or cooldowns")
		_teardown(scene)
		return
	psm._state = PlayerStateMachine.PlayerState.DEAD
	cd["dead_cd"] = 0.8
	controller.call("_tick_controller_timers", 0.3, false)
	_assert_eq_float(0.5, cd.get("dead_cd", -1.0), "ADV-16_dead_state_still_decrements")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-17: DEAD/ABSORB/MUTATE states block attack even at cd=0.0
# Per permit matrix, these states have no ACTION_ATTACK entry.
# ---------------------------------------------------------------------------

func test_adv17_locked_states_block_attack() -> void:
	var locked_states: Array[int] = [
		PlayerStateMachine.PlayerState.DEAD,
		PlayerStateMachine.PlayerState.ABSORB,
		PlayerStateMachine.PlayerState.MUTATE,
		PlayerStateMachine.PlayerState.HURT,
	]
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV-17_locked", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
	db.register_base_attack("adv17_mut", res)

	for state in locked_states:
		var scene = _setup_attack_pipeline(
			"ADV-17_state_" + str(state), state, "adv17_mut", "", {"adv17_mut": 0.0},
		)
		if scene.is_empty():
			continue
		var controller = scene["controller"]
		if not controller.has_method("_try_attack"):
			_fail_test("ADV-17_state_" + str(state), "_try_attack not found")
			_teardown(scene)
			continue
		var executor = scene.get("executor")
		var fired = [false]
		if executor != null and executor.has_signal("attack_started"):
			executor.connect("attack_started", func(_r): fired[0] = true)
		controller.call("_try_attack")
		_assert_false(fired[0], "ADV-17_state_" + str(state) + "_blocks_attack")
		_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-19: Epsilon cooldown (1e-10) still blocks attack
# ---------------------------------------------------------------------------

func test_adv19_epsilon_cooldown_still_blocks() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV-19_epsilon", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.0})
	db.register_base_attack("adv19_mut", res)
	var scene = _setup_attack_pipeline(
		"ADV-19_epsilon", PlayerStateMachine.PlayerState.IDLE,
		"adv19_mut", "", {"adv19_mut": 1e-10},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV-19_epsilon", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], "ADV-19_epsilon_above_zero_still_blocks")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-20: Cooldown set to exact resource.cooldown value after attack
# ---------------------------------------------------------------------------

func test_adv20_cooldown_set_to_exact_resource_value() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV-20", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 1.337})
	db.register_base_attack("adv20_mut", res)
	var scene = _setup_attack_pipeline(
		"ADV-20", PlayerStateMachine.PlayerState.IDLE, "adv20_mut", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV-20", "_try_attack not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	_assert_eq_float(1.337, cd.get("adv20_mut", -1.0), "ADV-20_exact_resource_cooldown")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-21: Multiple resets do not corrupt dictionary
# ---------------------------------------------------------------------------

func test_adv21_multiple_resets_stable() -> void:
	var scene = _build_controller_scene("ADV-21")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null or not controller.has_method("reset_hp"):
		_fail_test("ADV-21", "missing cooldowns or reset_hp")
		_teardown(scene)
		return
	cd["r1"] = 1.0
	controller.call("reset_hp")
	_assert_eq_int(0, cd.size(), "ADV-21_first_reset")
	cd["r2"] = 2.0
	cd["r3"] = 3.0
	controller.call("reset_hp")
	_assert_eq_int(0, cd.size(), "ADV-21_second_reset")
	controller.call("reset_hp")
	_assert_eq_int(0, cd.size(), "ADV-21_third_reset_on_empty")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-22: Fused attack fallback to base when fused not registered
# ---------------------------------------------------------------------------

func test_adv22_fused_fallback_to_base() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV-22", "AttackDatabase autoload not available")
		return
	var base_res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 0.9})
	db.register_base_attack("adv22_slota", base_res)
	var scene = _setup_attack_pipeline(
		"ADV-22", PlayerStateMachine.PlayerState.IDLE,
		"adv22_slota", "adv22_no_fused", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV-22", "_try_attack not found")
		_teardown(scene)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	_assert_true(cd.has("adv22_slota"), "ADV-22_fallback_uses_slot_a_key", "keys: " + str(cd.keys()))
	_assert_eq_float(0.9, cd.get("adv22_slota", -1.0), "ADV-22_fallback_cooldown_correct")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-23: Full lifecycle: attack → tick → state_change → refire
# ---------------------------------------------------------------------------

func test_adv23_attack_tick_state_reattack_cycle() -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test("ADV-23", "AttackDatabase autoload not available")
		return
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "cooldown": 0.3})
	db.register_base_attack("adv23_mut", res)
	var scene = _setup_attack_pipeline(
		"ADV-23", PlayerStateMachine.PlayerState.IDLE, "adv23_mut", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var psm = controller.get("_player_state_machine")
	if psm == null or not controller.has_method("_try_attack"):
		_fail_test("ADV-23", "missing psm or _try_attack")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var attack_count = [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): attack_count[0] += 1)
	controller.call("_try_attack")
	_assert_eq_int(1, attack_count[0], "ADV-23_first_attack")
	controller.call("_tick_controller_timers", 0.2, false)
	psm._state = PlayerStateMachine.PlayerState.JUMP
	controller.call("_try_attack")
	_assert_eq_int(1, attack_count[0], "ADV-23_mid_cooldown_rejected")
	controller.call("_tick_controller_timers", 0.15, false)
	psm._state = PlayerStateMachine.PlayerState.FALL
	controller.call("_try_attack")
	_assert_eq_int(2, attack_count[0], "ADV-23_post_cooldown_refire")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-24: Determinism — 3 trials produce identical results
# ---------------------------------------------------------------------------

func test_adv24_deterministic_results() -> void:
	var results: Array[float] = []
	for trial in range(3):
		var scene = _build_controller_scene("ADV-24_" + str(trial))
		if scene.is_empty():
			_fail_test("ADV-24", "scene creation failed trial " + str(trial))
			return
		var controller = scene["controller"]
		var cd = controller.get("_mutation_cooldowns")
		if cd == null:
			_fail_test("ADV-24", "cooldowns null trial " + str(trial))
			_teardown(scene)
			return
		cd["det_key"] = 1.0
		var psm = controller.get("_player_state_machine")
		if psm != null:
			psm._state = PlayerStateMachine.PlayerState.IDLE
		controller.call("_tick_controller_timers", 0.1, false)
		if psm != null:
			psm._state = PlayerStateMachine.PlayerState.WALK
		controller.call("_tick_controller_timers", 0.2, false)
		if psm != null:
			psm._state = PlayerStateMachine.PlayerState.JUMP
		controller.call("_tick_controller_timers", 0.15, false)
		results.append(cd.get("det_key", -1.0))
		_teardown(scene)
	_assert_true(
		absf(results[0] - results[1]) < 0.0001 and absf(results[1] - results[2]) < 0.0001,
		"ADV-24_three_trials_identical", "results: " + str(results)
	)
	_assert_eq_float(1.0 - 0.45, results[0], "ADV-24_value_correct")


# ---------------------------------------------------------------------------
# ADV-25: Null attack resource (unregistered mutation) — no crash
# ---------------------------------------------------------------------------

func test_adv25_null_attack_resource_no_crash() -> void:
	var scene = _setup_attack_pipeline(
		"ADV-25", PlayerStateMachine.PlayerState.IDLE, "adv25_unregistered", "", {},
	)
	if scene.is_empty():
		return
	var controller = scene["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test("ADV-25", "_try_attack not found")
		_teardown(scene)
		return
	var executor = scene.get("executor")
	var fired = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], "ADV-25_null_resource_no_crash")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-26: External cooldown overwrite mid-lifecycle
# ---------------------------------------------------------------------------

func test_adv26_overwrite_cooldown_mid_lifecycle() -> void:
	var scene = _build_controller_scene("ADV-26")
	if scene.is_empty():
		return
	var controller = scene["controller"]
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test("ADV-26", "_mutation_cooldowns not found")
		_teardown(scene)
		return
	cd["ow_key"] = 1.0
	controller.call("_tick_controller_timers", 0.3, false)
	cd["ow_key"] = 5.0
	controller.call("_tick_controller_timers", 0.2, false)
	_assert_eq_float(4.8, cd.get("ow_key", -1.0), "ADV-26_overwrite_respected")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== CooldownCrossStateAdversarialTests ===")

	test_adv1_negative_delta_does_not_increase_cooldown()
	test_adv2_zero_delta_no_change()
	test_adv3_large_delta_floors_at_zero()
	test_adv4_empty_dict_tick_no_crash()
	test_adv5_absent_key_allows_attack()
	test_adv6_exact_zero_boundary_allows_attack()
	test_adv7_float_accumulation_precision()
	test_adv8_stress_many_cooldown_keys()
	test_adv9_state_oscillation_single_tick()
	test_adv10_fused_key_sorted_determinism()
	test_adv10b_fused_key_reverse_slot_order()
	test_adv11_zero_cooldown_resource()
	test_adv12_null_input_policy_no_crash()
	test_adv13_null_mutation_slot_no_crash()
	test_adv14_empty_mutation_slots_rejected()
	test_adv15_reset_then_tick_no_ghost_residual()
	test_adv16_dead_state_tick_continues()
	test_adv17_locked_states_block_attack()
	test_adv19_epsilon_cooldown_still_blocks()
	test_adv20_cooldown_set_to_exact_resource_value()
	test_adv21_multiple_resets_stable()
	test_adv22_fused_fallback_to_base()
	test_adv23_attack_tick_state_reattack_cycle()
	test_adv24_deterministic_results()
	test_adv25_null_attack_resource_no_crash()
	test_adv26_overwrite_cooldown_mid_lifecycle()

	print("CooldownCrossStateAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
