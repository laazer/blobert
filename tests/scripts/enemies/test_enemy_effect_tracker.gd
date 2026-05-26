# test_enemy_effect_tracker.gd
#
# Behavioral tests for EnemyEffectTracker (DoT effects, slowness modifier)
# and the EnemyBase delegation methods (apply_poison, apply_acid, apply_slowness).
#
# Spec: project_board/specs/enemy_health_damage_reception_spec.md
# Requirements: EHD-4, EHD-7, EHD-8
# Ticket: M11-14 (enemy_health_and_damage_reception)
#
# These tests define the behavioral contract. They will FAIL until the
# implementation is complete.
#
# DoT timing is tested via direct _process(delta) calls on the tracker
# with controlled delta values — no reliance on real time.

extends "res://tests/utils/test_utils.gd"


var _pass_count: int = 0
var _fail_count: int = 0


func _make_enemy() -> CharacterBody3D:
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	var body = CharacterBody3D.new()
	body.set_script(script_res)
	return body


func _make_tracker() -> Node:
	var script_res: GDScript = load("res://scripts/enemies/enemy_effect_tracker.gd")
	var node = Node.new()
	node.set_script(script_res)
	return node


# ---------------------------------------------------------------------------
# EHD-8: EnemyEffectTracker Helper Node (isolation tests)
# ---------------------------------------------------------------------------

func test_ehd8a_tracker_extends_node() -> void:
	var tracker = _make_tracker()
	_assert_true(tracker is Node, "EHD-8a — EnemyEffectTracker extends Node")
	tracker.free()


func test_ehd8c_add_dot_method_exists() -> void:
	var tracker = _make_tracker()
	_assert_true(
		tracker.has_method("add_dot"),
		"EHD-8c — add_dot method exists on EnemyEffectTracker"
	)
	tracker.free()


func test_ehd8d_set_slowness_method_exists() -> void:
	var tracker = _make_tracker()
	_assert_true(
		tracker.has_method("set_slowness"),
		"EHD-8d — set_slowness method exists on EnemyEffectTracker"
	)
	tracker.free()


func test_ehd8e_get_speed_multiplier_default() -> void:
	var tracker = _make_tracker()
	_assert_eq_float(
		1.0, tracker.get_speed_multiplier(),
		"EHD-8e — get_speed_multiplier() returns 1.0 when no slowness active"
	)
	tracker.free()


func test_ehd8f_stop_all_effects_clears_everything() -> void:
	var tracker = _make_tracker()
	tracker.add_dot("poison", 5.0, 2.0)
	tracker.set_slowness(0.5, 5.0)
	tracker.stop_all_effects()
	_assert_false(
		tracker.has_active_dot("poison"),
		"EHD-8f — stop_all_effects clears DoT"
	)
	_assert_eq_float(
		1.0, tracker.get_speed_multiplier(),
		"EHD-8f — stop_all_effects clears slowness"
	)
	tracker.free()


func test_ehd8g_has_active_dot() -> void:
	var tracker = _make_tracker()
	_assert_false(tracker.has_active_dot("poison"), "EHD-8g — no poison before apply")
	tracker.add_dot("poison", 2.0, 1.0)
	_assert_true(tracker.has_active_dot("poison"), "EHD-8g — poison active after add_dot")
	tracker.free()


func test_ehd8h_dot_tick_requested_signal() -> void:
	var tracker = _make_tracker()
	var received = [false]
	var received_name = [""]
	var received_damage = [0.0]
	tracker.dot_tick_requested.connect(func(name: String, dmg: float):
		received[0] = true
		received_name[0] = name
		received_damage[0] = dmg
	)
	tracker.add_dot("poison", 2.0, 2.0)
	tracker._process(0.5)
	_assert_true(received[0], "EHD-8h — dot_tick_requested signal emitted after 0.5s")
	_assert_eq_string("poison", received_name[0], "EHD-8h — signal carries effect name")
	_assert_eq_float(1.0, received_damage[0], "EHD-8h — tick_damage == dps * 0.5 = 1.0")
	tracker.free()


func test_ehd4p_dot_tick_interval_constant() -> void:
	var tracker = _make_tracker()
	_assert_eq_float(0.5, tracker.DOT_TICK_INTERVAL, "EHD-4p — DOT_TICK_INTERVAL == 0.5")
	tracker.free()


# ---------------------------------------------------------------------------
# EHD-4: Damage-Over-Time (DoT) Effects — via EnemyBase delegation
# ---------------------------------------------------------------------------

func test_ehd4a_apply_poison_method_exists() -> void:
	var enemy = _make_enemy()
	_assert_true(
		enemy.has_method("apply_poison"),
		"EHD-4a — has_method('apply_poison') returns true"
	)
	enemy.free()


func test_ehd4b_apply_acid_method_exists() -> void:
	var enemy = _make_enemy()
	_assert_true(
		enemy.has_method("apply_acid"),
		"EHD-4b — has_method('apply_acid') returns true"
	)
	enemy.free()


func test_ehd4c_poison_ticks_damage() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(4.0, 2.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(9.0, enemy.current_hp, "EHD-4c — poison tick: 2.0dps * 0.5 = 1.0 dmg; HP 10->9")
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(8.0, enemy.current_hp, "EHD-4c — second tick: HP 9->8")
	enemy.free()


func test_ehd4d_acid_ticks_damage() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_acid(4.0, 2.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(9.0, enemy.current_hp, "EHD-4d — acid tick: 2.0dps * 0.5 = 1.0 dmg; HP 10->9")
	enemy.free()


func test_ehd4e_dot_expires_after_duration() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(1.0, 2.0)
	enemy._effect_tracker._process(0.5)
	enemy._effect_tracker._process(0.5)
	var hp_after_expiry = enemy.current_hp
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(
		hp_after_expiry, enemy.current_hp,
		"EHD-4e — no further damage after duration expires (2 ticks in 1.0s)"
	)
	enemy.free()


func test_ehd4f_reapply_refreshes_duration_no_stack() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(1.0, 2.0)
	enemy._effect_tracker._process(0.5)
	enemy.apply_poison(1.0, 2.0)
	enemy._effect_tracker._process(0.5)
	enemy._effect_tracker._process(0.5)
	var hp_before = enemy.current_hp
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(
		hp_before, enemy.current_hp,
		"EHD-4f — re-applied poison refreshes duration; expires after new duration"
	)
	enemy.free()


func test_ehd4g_reapply_updates_dps() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(3.0, 1.0)
	enemy._effect_tracker._process(0.5)
	var hp_after_first_tick = enemy.current_hp
	enemy.apply_poison(3.0, 4.0)
	enemy._effect_tracker._process(0.5)
	var expected_hp = hp_after_first_tick - (4.0 * 0.5)
	_assert_eq_float(
		expected_hp, enemy.current_hp,
		"EHD-4g — re-applied poison updates DPS; new tick uses 4.0 dps"
	)
	enemy.free()


func test_ehd4h_poison_and_acid_independent() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(2.0, 2.0)
	enemy.apply_acid(2.0, 2.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(
		8.0, enemy.current_hp,
		"EHD-4h — poison + acid both tick independently; HP 10 - 1.0 - 1.0 = 8.0"
	)
	enemy.free()


func test_ehd4i_dot_does_not_emit_damaged_signal() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	var damaged_count = [0]
	enemy.damaged.connect(func(_d: float, _h: float): damaged_count[0] += 1)
	enemy.apply_poison(2.0, 2.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_int(0, damaged_count[0], "EHD-4i — DoT does NOT emit damaged signal")
	enemy.free()


func test_ehd4j_dot_emits_dot_tick_signal() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	var tick_received = [false]
	var tick_name = [""]
	var tick_dmg = [0.0]
	var tick_hp = [0.0]
	enemy.dot_tick.connect(func(name: String, dmg: float, hp: float):
		tick_received[0] = true
		tick_name[0] = name
		tick_dmg[0] = dmg
		tick_hp[0] = hp
	)
	enemy.apply_poison(2.0, 2.0)
	enemy._effect_tracker._process(0.5)
	_assert_true(tick_received[0], "EHD-4j — dot_tick signal emitted on tick")
	_assert_eq_string("poison", tick_name[0], "EHD-4j — dot_tick signal effect_name == 'poison'")
	_assert_eq_float(1.0, tick_dmg[0], "EHD-4j — dot_tick signal tick_damage == 1.0")
	_assert_eq_float(9.0, tick_hp[0], "EHD-4j — dot_tick signal current_hp == 9.0")
	enemy.free()


func test_ehd4k_dot_triggers_weakened() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(10.0, 10.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_int(
		enemy.State.WEAKENED, enemy.current_state,
		"EHD-4k — DoT tick triggers WEAKENED at <=50% HP"
	)
	enemy.free()


func test_ehd4l_dot_triggers_death() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(9.0, Vector3.ZERO)
	var died_count = [0]
	enemy.died.connect(func(): died_count[0] += 1)
	enemy.apply_poison(2.0, 4.0)
	enemy._effect_tracker._process(0.5)
	_assert_true(enemy.is_dead(), "EHD-4l — DoT tick kills enemy at 1.0 HP")
	_assert_eq_int(1, died_count[0], "EHD-4l — died signal emitted from DoT kill")
	enemy.free()


func test_ehd4m_dot_stops_after_death() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(9.0, Vector3.ZERO)
	enemy.apply_poison(5.0, 4.0)
	enemy._effect_tracker._process(0.5)
	var hp_after_kill = enemy.current_hp
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(
		hp_after_kill, enemy.current_hp,
		"EHD-4m — no further DoT ticks after death"
	)
	enemy.free()


func test_ehd4n_zero_duration_noop() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(0.0, 5.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(10.0, enemy.current_hp, "EHD-4n — duration=0 is a no-op; no ticks fire")
	enemy.free()


func test_ehd4o_zero_dps_ticks_no_damage() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(2.0, 0.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(10.0, enemy.current_hp, "EHD-4o — DPS=0 ticks but deals 0 damage")
	enemy.free()


# ---------------------------------------------------------------------------
# EHD-7: Slowness Modifier
# ---------------------------------------------------------------------------

func test_ehd7a_apply_slowness_method_exists() -> void:
	var enemy = _make_enemy()
	_assert_true(
		enemy.has_method("apply_slowness"),
		"EHD-7a — has_method('apply_slowness') returns true"
	)
	enemy.free()


func test_ehd7b_get_speed_multiplier_default() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	_assert_eq_float(
		1.0, enemy.get_speed_multiplier(),
		"EHD-7b — get_speed_multiplier() == 1.0 when no slowness"
	)
	enemy.free()


func test_ehd7c_apply_slowness_changes_multiplier() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(0.5, 2.0)
	_assert_eq_float(
		0.5, enemy.get_speed_multiplier(),
		"EHD-7c — get_speed_multiplier() == 0.5 after apply_slowness(0.5, 2.0)"
	)
	enemy.free()


func test_ehd7d_slowness_expires_after_duration() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(0.5, 1.0)
	enemy._effect_tracker._process(0.5)
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(
		1.0, enemy.get_speed_multiplier(),
		"EHD-7d — slowness expires after duration; multiplier back to 1.0"
	)
	enemy.free()


func test_ehd7e_reapply_refreshes_duration() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(0.5, 1.0)
	enemy._effect_tracker._process(0.5)
	enemy.apply_slowness(0.5, 1.0)
	enemy._effect_tracker._process(0.75)
	_assert_eq_float(
		0.5, enemy.get_speed_multiplier(),
		"EHD-7e — re-applied slowness refreshes duration; still active"
	)
	enemy.free()


func test_ehd7f_reapply_updates_multiplier() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(0.5, 3.0)
	enemy.apply_slowness(0.3, 3.0)
	_assert_eq_float(
		0.3, enemy.get_speed_multiplier(),
		"EHD-7f — re-applied slowness updates multiplier to 0.3"
	)
	enemy.free()


func test_ehd7h_slowness_does_not_affect_knockback() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(0.1, 10.0)
	enemy.take_damage(1.0, Vector3(5.0, 0.0, 0.0))
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3(5.0, 0.0, 0.0), 0.001,
		"EHD-7h — slowness does NOT affect knockback magnitude"
	)
	enemy.free()


func test_ehd7i_slowness_stops_on_death() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(0.5, 10.0)
	enemy.take_damage(10.0, Vector3.ZERO)
	_assert_eq_float(
		1.0, enemy.get_speed_multiplier(),
		"EHD-7i — slowness cleared on death"
	)
	enemy.free()


func test_ehd7j_zero_duration_noop() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(0.5, 0.0)
	_assert_eq_float(
		1.0, enemy.get_speed_multiplier(),
		"EHD-7j — duration=0 is a no-op; multiplier stays 1.0"
	)
	enemy.free()


func test_ehd7k_negative_multiplier_treated_as_zero() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(-0.5, 2.0)
	_assert_eq_float(
		0.0, enemy.get_speed_multiplier(),
		"EHD-7k — negative multiplier clamped to 0.0"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# Edge Cases (EC)
# ---------------------------------------------------------------------------

func test_ec6_dot_duration_less_than_tick_interval() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(0.3, 10.0)
	enemy._effect_tracker._process(0.3)
	_assert_eq_float(
		10.0, enemy.current_hp,
		"EC-6 — duration < DOT_TICK_INTERVAL: zero ticks fire"
	)
	enemy.free()


func test_ec8_concurrent_poison_acid_slowness() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(3.0, 2.0)
	enemy.apply_acid(3.0, 2.0)
	enemy.apply_slowness(0.5, 3.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(8.0, enemy.current_hp, "EC-8 — poison + acid both tick; HP 10 - 1 - 1 = 8")
	_assert_eq_float(0.5, enemy.get_speed_multiplier(), "EC-8 — slowness active concurrently")
	enemy.free()


func test_ec10_dot_kills_cancels_remaining() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(8.0, Vector3.ZERO)
	enemy.apply_poison(5.0, 8.0)
	enemy._effect_tracker._process(0.5)
	_assert_true(enemy.is_dead(), "EC-10 — DoT kills enemy (HP 2 - 4 per tick)")
	_assert_false(
		enemy._effect_tracker.has_active_dot("poison"),
		"EC-10 — poison cleared after death"
	)
	enemy.free()


func test_ec15_slowness_zero_full_stop() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(0.0, 5.0)
	_assert_eq_float(
		0.0, enemy.get_speed_multiplier(),
		"EC-15 — multiplier=0.0 means full stop"
	)
	enemy.free()


func test_ec19_reapply_dot_different_dps() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(3.0, 1.0)
	enemy._effect_tracker._process(0.5)
	var hp_after_first = enemy.current_hp
	enemy.apply_poison(3.0, 6.0)
	enemy._effect_tracker._process(0.5)
	var expected = hp_after_first - (6.0 * 0.5)
	_assert_eq_float(
		expected, enemy.current_hp,
		"EC-19 — re-apply DoT with different DPS updates to new DPS"
	)
	enemy.free()


func test_ec20_slowness_reapply_longer_duration() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(0.5, 1.0)
	enemy.apply_slowness(0.5, 3.0)
	enemy._effect_tracker._process(1.0)
	_assert_eq_float(
		0.5, enemy.get_speed_multiplier(),
		"EC-20 — re-apply with longer duration refreshes; still active after 1.0s"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_effect_tracker.gd ---")
	_pass_count = 0
	_fail_count = 0

	# EHD-8: EnemyEffectTracker isolation
	test_ehd8a_tracker_extends_node()
	test_ehd8c_add_dot_method_exists()
	test_ehd8d_set_slowness_method_exists()
	test_ehd8e_get_speed_multiplier_default()
	test_ehd8f_stop_all_effects_clears_everything()
	test_ehd8g_has_active_dot()
	test_ehd8h_dot_tick_requested_signal()
	test_ehd4p_dot_tick_interval_constant()

	# EHD-4: DoT via EnemyBase
	test_ehd4a_apply_poison_method_exists()
	test_ehd4b_apply_acid_method_exists()
	test_ehd4c_poison_ticks_damage()
	test_ehd4d_acid_ticks_damage()
	test_ehd4e_dot_expires_after_duration()
	test_ehd4f_reapply_refreshes_duration_no_stack()
	test_ehd4g_reapply_updates_dps()
	test_ehd4h_poison_and_acid_independent()
	test_ehd4i_dot_does_not_emit_damaged_signal()
	test_ehd4j_dot_emits_dot_tick_signal()
	test_ehd4k_dot_triggers_weakened()
	test_ehd4l_dot_triggers_death()
	test_ehd4m_dot_stops_after_death()
	test_ehd4n_zero_duration_noop()
	test_ehd4o_zero_dps_ticks_no_damage()

	# EHD-7: Slowness
	test_ehd7a_apply_slowness_method_exists()
	test_ehd7b_get_speed_multiplier_default()
	test_ehd7c_apply_slowness_changes_multiplier()
	test_ehd7d_slowness_expires_after_duration()
	test_ehd7e_reapply_refreshes_duration()
	test_ehd7f_reapply_updates_multiplier()
	test_ehd7h_slowness_does_not_affect_knockback()
	test_ehd7i_slowness_stops_on_death()
	test_ehd7j_zero_duration_noop()
	test_ehd7k_negative_multiplier_treated_as_zero()

	# Edge Cases
	test_ec6_dot_duration_less_than_tick_interval()
	test_ec8_concurrent_poison_acid_slowness()
	test_ec10_dot_kills_cancels_remaining()
	test_ec15_slowness_zero_full_stop()
	test_ec19_reapply_dot_different_dps()
	test_ec20_slowness_reapply_longer_duration()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
