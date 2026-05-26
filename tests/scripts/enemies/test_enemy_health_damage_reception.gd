# test_enemy_health_damage_reception.gd
#
# Behavioral tests for EnemyBase health system, take_damage(), knockback
# impulse, WEAKENED threshold, death state, and backward compatibility.
#
# Spec: project_board/specs/enemy_health_damage_reception_spec.md
# Requirements: EHD-1, EHD-2, EHD-3, EHD-5, EHD-6, EHD-9
# Ticket: M11-14 (enemy_health_and_damage_reception)
#
# These tests define the behavioral contract. They will FAIL until the
# implementation is complete.

extends "res://tests/utils/test_utils.gd"


var _pass_count: int = 0
var _fail_count: int = 0


func _make_enemy() -> CharacterBody3D:
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	var body = CharacterBody3D.new()
	body.set_script(script_res)
	return body


# ---------------------------------------------------------------------------
# EHD-1: HP Core System
# ---------------------------------------------------------------------------

func test_ehd1a_max_hp_export_default() -> void:
	var enemy = _make_enemy()
	_assert_eq_float(10.0, enemy.max_hp, "EHD-1a — max_hp defaults to 10.0")
	enemy.free()


func test_ehd1b_current_hp_exists() -> void:
	var enemy = _make_enemy()
	var hp = enemy.get("current_hp")
	_assert_true(hp != null, "EHD-1b — current_hp property exists on EnemyBase")
	enemy.free()


func test_ehd1c_current_hp_initializes_to_max_hp() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	_assert_eq_float(10.0, enemy.current_hp, "EHD-1c — current_hp == max_hp after _ready()")
	enemy.free()


func test_ehd1d_current_hp_respects_max_hp_override() -> void:
	var enemy = _make_enemy()
	enemy.max_hp = 25.0
	enemy._ready()
	_assert_eq_float(25.0, enemy.current_hp, "EHD-1d — current_hp == 25.0 after max_hp override + _ready()")
	enemy.free()


func test_ehd1e_current_hp_never_negative() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(999.0, Vector3.ZERO)
	_assert_eq_float(0.0, enemy.current_hp, "EHD-1e — current_hp clamped to 0.0 after overkill damage")
	enemy.free()


func test_ehd1f_current_hp_never_exceeds_max() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.current_hp = enemy.max_hp + 10.0
	_assert_true(
		enemy.current_hp <= enemy.max_hp,
		"EHD-1f — current_hp clamped to max_hp when set above",
		"current_hp=" + str(enemy.current_hp) + " exceeds max_hp=" + str(enemy.max_hp)
	)
	enemy.free()


# ---------------------------------------------------------------------------
# EHD-2: take_damage() Method
# ---------------------------------------------------------------------------

func test_ehd2a_take_damage_method_exists() -> void:
	var enemy = _make_enemy()
	_assert_true(
		enemy.has_method("take_damage"),
		"EHD-2a — has_method('take_damage') returns true"
	)
	enemy.free()


func test_ehd2b_take_damage_reduces_hp() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(3.0, Vector3.ZERO)
	_assert_eq_float(7.0, enemy.current_hp, "EHD-2b — HP reduced from 10 to 7 after 3.0 damage")
	enemy.free()


func test_ehd2c_take_damage_clamps_to_zero() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(5.0, Vector3.ZERO)
	enemy.take_damage(8.0, Vector3.ZERO)
	_assert_eq_float(0.0, enemy.current_hp, "EHD-2c — HP clamped to 0.0 not negative")
	enemy.free()


func test_ehd2d_take_damage_emits_damaged_signal() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	var signal_received = [false]
	var signal_args = [0.0, 0.0]
	enemy.damaged.connect(func(dmg: float, hp: float):
		signal_received[0] = true
		signal_args[0] = dmg
		signal_args[1] = hp
	)
	enemy.take_damage(3.0, Vector3.ZERO)
	_assert_true(signal_received[0], "EHD-2d — damaged signal emitted")
	_assert_eq_float(3.0, signal_args[0], "EHD-2d — damaged signal arg[0] == damage dealt")
	_assert_eq_float(7.0, signal_args[1], "EHD-2d — damaged signal arg[1] == current_hp after")
	enemy.free()


func test_ehd2e_take_damage_applies_knockback() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(1.0, Vector3(5.0, 0.0, 0.0))
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3(5.0, 0.0, 0.0), 0.001,
		"EHD-2e — _knockback_velocity set to knockback arg"
	)
	enemy.free()


func test_ehd2f_zero_damage_valid() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	var signal_received = [false]
	enemy.damaged.connect(func(_dmg: float, _hp: float): signal_received[0] = true)
	enemy.take_damage(0.0, Vector3.ZERO)
	_assert_eq_float(10.0, enemy.current_hp, "EHD-2f — HP unchanged with 0 damage")
	_assert_true(signal_received[0], "EHD-2f — damaged signal still emits with 0 damage")
	enemy.free()


func test_ehd2g_negative_damage_treated_as_zero() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(-5.0, Vector3.ZERO)
	_assert_eq_float(10.0, enemy.current_hp, "EHD-2g — negative damage treated as 0; HP unchanged")
	enemy.free()


func test_ehd2h_noop_after_death() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(10.0, Vector3.ZERO)
	var signal_count = [0]
	enemy.damaged.connect(func(_d: float, _h: float): signal_count[0] += 1)
	enemy.take_damage(5.0, Vector3(1.0, 0.0, 0.0))
	_assert_eq_float(0.0, enemy.current_hp, "EHD-2h — HP stays 0 after death")
	_assert_eq_int(0, signal_count[0], "EHD-2h — no damaged signal after death")
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3.ZERO, 0.001,
		"EHD-2h — no knockback applied after death"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# EHD-3: Knockback Impulse System
# ---------------------------------------------------------------------------

func test_ehd3a_knockback_velocity_initialized_zero() -> void:
	var enemy = _make_enemy()
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3.ZERO, 0.001,
		"EHD-3a — _knockback_velocity initialized to Vector3.ZERO"
	)
	enemy.free()


func test_ehd3b_take_damage_sets_knockback() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(1.0, Vector3(10.0, 0.0, 0.0))
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3(10.0, 0.0, 0.0), 0.001,
		"EHD-3b — _knockback_velocity set by take_damage knockback arg"
	)
	enemy.free()


func test_ehd3d_knockback_decays_per_frame() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(1.0, Vector3(10.0, 0.0, 0.0))
	enemy._physics_process(1.0 / 60.0)
	var expected_x = 10.0 * enemy.KNOCKBACK_DECAY_RATE
	_assert_true(
		absf(enemy._knockback_velocity.x - expected_x) < 0.01,
		"EHD-3d — knockback decays by KNOCKBACK_DECAY_RATE per frame",
		"expected ~" + str(expected_x) + " got " + str(enemy._knockback_velocity.x)
	)
	enemy.free()


func test_ehd3e_knockback_zeroes_below_epsilon() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(1.0, Vector3(0.005, 0.0, 0.0))
	enemy._physics_process(1.0 / 60.0)
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3.ZERO, 0.001,
		"EHD-3e — knockback zeroed when below KNOCKBACK_EPSILON"
	)
	enemy.free()


func test_ehd3g_knockback_decay_rate_constant() -> void:
	var enemy = _make_enemy()
	_assert_eq_float(0.8, enemy.KNOCKBACK_DECAY_RATE, "EHD-3g — KNOCKBACK_DECAY_RATE == 0.8")
	enemy.free()


func test_ehd3h_knockback_epsilon_constant() -> void:
	var enemy = _make_enemy()
	_assert_eq_float(0.01, enemy.KNOCKBACK_EPSILON, "EHD-3h — KNOCKBACK_EPSILON == 0.01")
	enemy.free()


func test_ehd3i_zero_knockback_no_impulse() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(5.0, Vector3.ZERO)
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3.ZERO, 0.001,
		"EHD-3i — Vector3.ZERO knockback does not create impulse"
	)
	enemy.free()


func test_ehd3j_new_knockback_overwrites_residual() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(1.0, Vector3(10.0, 0.0, 0.0))
	enemy.take_damage(1.0, Vector3(0.0, 0.0, 5.0))
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3(0.0, 0.0, 5.0), 0.001,
		"EHD-3j — new knockback overwrites residual (not additive)"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# EHD-5: WEAKENED State Threshold
# ---------------------------------------------------------------------------

func test_ehd5a_hp_at_50_percent_triggers_weakened() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(5.0, Vector3.ZERO)
	_assert_eq_int(
		enemy.State.WEAKENED, enemy.current_state,
		"EHD-5a — HP at exactly 50% triggers WEAKENED"
	)
	enemy.free()


func test_ehd5b_hp_below_50_percent_triggers_weakened() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(6.0, Vector3.ZERO)
	_assert_eq_int(
		enemy.State.WEAKENED, enemy.current_state,
		"EHD-5b — HP below 50% triggers WEAKENED"
	)
	enemy.free()


func test_ehd5c_hp_above_50_percent_stays_normal() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(4.0, Vector3.ZERO)
	_assert_eq_int(
		enemy.State.NORMAL, enemy.current_state,
		"EHD-5c — HP at 60% (above 50%) stays NORMAL"
	)
	enemy.free()


func test_ehd5d_manual_set_base_state_weakened_works() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.set_base_state(enemy.State.WEAKENED)
	_assert_eq_int(
		enemy.State.WEAKENED, enemy.current_state,
		"EHD-5d — manual set_base_state(WEAKENED) still works at full HP"
	)
	enemy.free()


func test_ehd5e_no_retrigger_if_already_weakened() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.set_base_state(enemy.State.WEAKENED)
	enemy.take_damage(6.0, Vector3.ZERO)
	_assert_eq_int(
		enemy.State.WEAKENED, enemy.current_state,
		"EHD-5e — HP threshold does not re-trigger; state stays WEAKENED"
	)
	enemy.free()


func test_ehd5f_no_trigger_if_infected() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.set_base_state(enemy.State.INFECTED)
	enemy.take_damage(6.0, Vector3.ZERO)
	_assert_eq_int(
		enemy.State.INFECTED, enemy.current_state,
		"EHD-5f — HP threshold does not trigger if already INFECTED"
	)
	enemy.free()


func test_ehd5g_no_state_change_after_death() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(10.0, Vector3.ZERO)
	var state_after_death = enemy.current_state
	_assert_true(
		state_after_death == enemy.State.WEAKENED or enemy.is_dead(),
		"EHD-5g — after lethal damage, WEAKENED triggered before death (or dead)",
		"state=" + str(state_after_death) + " is_dead=" + str(enemy.is_dead())
	)
	enemy.free()


# ---------------------------------------------------------------------------
# EHD-6: Death State
# ---------------------------------------------------------------------------

func test_ehd6a_is_dead_false_by_default() -> void:
	var enemy = _make_enemy()
	_assert_false(enemy._is_dead, "EHD-6a — _is_dead is false by default")
	enemy.free()


func test_ehd6b_is_dead_true_at_zero_hp() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(10.0, Vector3.ZERO)
	_assert_true(enemy._is_dead, "EHD-6b — _is_dead becomes true when HP reaches 0")
	enemy.free()


func test_ehd6c_died_signal_emitted_once() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	var died_count = [0]
	enemy.died.connect(func(): died_count[0] += 1)
	enemy.take_damage(10.0, Vector3.ZERO)
	_assert_eq_int(1, died_count[0], "EHD-6c — died signal emitted exactly once")
	enemy.free()


func test_ehd6d_died_signal_not_emitted_on_subsequent_damage() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	var died_count = [0]
	enemy.died.connect(func(): died_count[0] += 1)
	enemy.take_damage(10.0, Vector3.ZERO)
	enemy.take_damage(5.0, Vector3.ZERO)
	_assert_eq_int(1, died_count[0], "EHD-6d — died signal NOT emitted on subsequent damage after death")
	enemy.free()


func test_ehd6e_take_damage_noop_after_death() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(10.0, Vector3.ZERO)
	var damaged_count = [0]
	enemy.damaged.connect(func(_d: float, _h: float): damaged_count[0] += 1)
	enemy.take_damage(5.0, Vector3(1.0, 0.0, 0.0))
	_assert_eq_float(0.0, enemy.current_hp, "EHD-6e — HP stays 0 after death")
	_assert_eq_int(0, damaged_count[0], "EHD-6e — no damaged signal after death")
	enemy.free()


func test_ehd6h_node_not_freed_after_death() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(10.0, Vector3.ZERO)
	_assert_true(
		is_instance_valid(enemy),
		"EHD-6h — enemy node is NOT queue_free'd after death"
	)
	enemy.free()


func test_ehd6i_is_dead_method() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	_assert_false(enemy.is_dead(), "EHD-6i — is_dead() returns false before death")
	enemy.take_damage(10.0, Vector3.ZERO)
	_assert_true(enemy.is_dead(), "EHD-6i — is_dead() returns true after death")
	enemy.free()


# ---------------------------------------------------------------------------
# EHD-9: Backward Compatibility
# ---------------------------------------------------------------------------

func test_ehd9a_state_enum_still_3_members() -> void:
	var enemy = _make_enemy()
	var key_count = enemy.State.keys().size()
	_assert_eq_int(3, key_count, "EHD-9a — State enum still has exactly 3 members")
	enemy.free()


func test_ehd9b_state_enum_values_unchanged() -> void:
	var enemy = _make_enemy()
	_assert_eq_int(0, enemy.State.NORMAL, "EHD-9b — State.NORMAL == 0")
	_assert_eq_int(1, enemy.State.WEAKENED, "EHD-9b — State.WEAKENED == 1")
	_assert_eq_int(2, enemy.State.INFECTED, "EHD-9b — State.INFECTED == 2")
	enemy.free()


func test_ehd9c_set_get_base_state_unchanged() -> void:
	var enemy = _make_enemy()
	enemy.set_base_state(enemy.State.WEAKENED)
	_assert_eq_int(
		enemy.State.WEAKENED, enemy.get_base_state(),
		"EHD-9c — set_base_state/get_base_state unchanged"
	)
	enemy.free()


func test_ehd9d_identity_exports_unchanged() -> void:
	var enemy = _make_enemy()
	_assert_eq_string("", enemy.enemy_id, "EHD-9d — enemy_id still defaults to ''")
	_assert_eq_string("", enemy.enemy_family, "EHD-9d — enemy_family still defaults to ''")
	_assert_eq_string("", enemy.mutation_drop, "EHD-9d — mutation_drop still defaults to ''")
	enemy.free()


func test_ehd9e_physics_process_now_exists() -> void:
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	var source: String = script_res.source_code
	_assert_true(
		source.contains("_physics_process"),
		"EHD-9e — enemy_base.gd now defines _physics_process (knockback system)"
	)


# ---------------------------------------------------------------------------
# Edge Cases (EC)
# ---------------------------------------------------------------------------

func test_ec3_max_hp_zero_instant_death() -> void:
	var enemy = _make_enemy()
	enemy.max_hp = 0.0
	enemy._ready()
	_assert_eq_float(0.0, enemy.current_hp, "EC-3 — max_hp=0 means current_hp=0")
	enemy.take_damage(1.0, Vector3.ZERO)
	_assert_true(enemy.is_dead(), "EC-3 — first damage on 0-HP enemy triggers death")
	enemy.free()


func test_ec14_two_enemies_independent_hp() -> void:
	var enemy_a = _make_enemy()
	var enemy_b = _make_enemy()
	enemy_a._ready()
	enemy_b._ready()
	enemy_a.take_damage(3.0, Vector3.ZERO)
	_assert_eq_float(7.0, enemy_a.current_hp, "EC-14 — enemy_a HP reduced")
	_assert_eq_float(10.0, enemy_b.current_hp, "EC-14 — enemy_b HP unaffected")
	enemy_a.free()
	enemy_b.free()


func test_ec17_multiple_take_damage_same_frame() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(3.0, Vector3.ZERO)
	enemy.take_damage(3.0, Vector3.ZERO)
	enemy.take_damage(3.0, Vector3.ZERO)
	_assert_eq_float(1.0, enemy.current_hp, "EC-17 — three 3.0 hits reduce HP to 1.0")
	enemy.free()


func test_ec18_large_knockback_no_cap() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(1.0, Vector3(100.0, 0.0, 0.0))
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3(100.0, 0.0, 0.0), 0.01,
		"EC-18 — large knockback applied without cap"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_health_damage_reception.gd ---")
	_pass_count = 0
	_fail_count = 0

	# EHD-1: HP Core
	test_ehd1a_max_hp_export_default()
	test_ehd1b_current_hp_exists()
	test_ehd1c_current_hp_initializes_to_max_hp()
	test_ehd1d_current_hp_respects_max_hp_override()
	test_ehd1e_current_hp_never_negative()
	test_ehd1f_current_hp_never_exceeds_max()

	# EHD-2: take_damage()
	test_ehd2a_take_damage_method_exists()
	test_ehd2b_take_damage_reduces_hp()
	test_ehd2c_take_damage_clamps_to_zero()
	test_ehd2d_take_damage_emits_damaged_signal()
	test_ehd2e_take_damage_applies_knockback()
	test_ehd2f_zero_damage_valid()
	test_ehd2g_negative_damage_treated_as_zero()
	test_ehd2h_noop_after_death()

	# EHD-3: Knockback Impulse
	test_ehd3a_knockback_velocity_initialized_zero()
	test_ehd3b_take_damage_sets_knockback()
	test_ehd3d_knockback_decays_per_frame()
	test_ehd3e_knockback_zeroes_below_epsilon()
	test_ehd3g_knockback_decay_rate_constant()
	test_ehd3h_knockback_epsilon_constant()
	test_ehd3i_zero_knockback_no_impulse()
	test_ehd3j_new_knockback_overwrites_residual()

	# EHD-5: WEAKENED Threshold
	test_ehd5a_hp_at_50_percent_triggers_weakened()
	test_ehd5b_hp_below_50_percent_triggers_weakened()
	test_ehd5c_hp_above_50_percent_stays_normal()
	test_ehd5d_manual_set_base_state_weakened_works()
	test_ehd5e_no_retrigger_if_already_weakened()
	test_ehd5f_no_trigger_if_infected()
	test_ehd5g_no_state_change_after_death()

	# EHD-6: Death State
	test_ehd6a_is_dead_false_by_default()
	test_ehd6b_is_dead_true_at_zero_hp()
	test_ehd6c_died_signal_emitted_once()
	test_ehd6d_died_signal_not_emitted_on_subsequent_damage()
	test_ehd6e_take_damage_noop_after_death()
	test_ehd6h_node_not_freed_after_death()
	test_ehd6i_is_dead_method()

	# EHD-9: Backward Compat
	test_ehd9a_state_enum_still_3_members()
	test_ehd9b_state_enum_values_unchanged()
	test_ehd9c_set_get_base_state_unchanged()
	test_ehd9d_identity_exports_unchanged()
	test_ehd9e_physics_process_now_exists()

	# Edge Cases
	test_ec3_max_hp_zero_instant_death()
	test_ec14_two_enemies_independent_hp()
	test_ec17_multiple_take_damage_same_frame()
	test_ec18_large_knockback_no_cap()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
