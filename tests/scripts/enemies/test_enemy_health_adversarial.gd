# test_enemy_health_adversarial.gd
#
# Adversarial edge-case tests for the EnemyBase health system,
# EnemyEffectTracker, knockback, and death interactions.
#
# Spec: project_board/specs/enemy_health_damage_reception_spec.md
# Requirements: EHD-1 through EHD-9 (adversarial coverage)
# Ticket: M11-14 (enemy_health_and_damage_reception)
#
# These tests target runtime seams the primary suite does not cover:
# killing-blow knockback gating, signal ordering on death, concurrent
# DoT + direct damage races, floating-point HP accumulation, rapid
# damage bursts through death, tracker isolation under stress, and
# boundary precision for WEAKENED threshold and slowness expiry.
#
# Every test is deterministic (no randomness, no real-time waits).
# All tests will FAIL until the implementation is complete.

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
# ADV: Killing-blow knockback gating (spec EHD-2 step 6)
# Primary suite never tests that the KILLING blow skips knockback.
# ---------------------------------------------------------------------------

func test_adv_killing_blow_does_not_apply_knockback() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(10.0, Vector3(99.0, 0.0, 0.0))
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3.ZERO, 0.001,
		"ADV — killing blow knockback NOT applied (spec step 6 gate)"
	)
	enemy.free()


func test_adv_near_lethal_blow_does_apply_knockback() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(9.99, Vector3(5.0, 0.0, 0.0))
	_assert_false(enemy.is_dead(), "ADV — 9.99 damage does not kill (HP=0.01)")
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3(5.0, 0.0, 0.0), 0.01,
		"ADV — non-lethal 9.99 hit applies knockback normally"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Signal ordering on killing blow (damaged BEFORE died)
# ---------------------------------------------------------------------------

func test_adv_damaged_signal_fires_on_killing_blow() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	var sig_received = [false]
	var sig_hp = [0.0]
	enemy.damaged.connect(func(dmg: float, hp: float):
		sig_received[0] = true
		sig_hp[0] = hp
	)
	enemy.take_damage(10.0, Vector3.ZERO)
	_assert_true(sig_received[0], "ADV — damaged signal fires on the killing blow")
	_assert_eq_float(0.0, sig_hp[0], "ADV — damaged signal reports current_hp=0.0 on kill")
	enemy.free()


func test_adv_signal_order_damaged_before_died() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	var order = []
	enemy.damaged.connect(func(_d: float, _h: float): order.append("damaged"))
	enemy.died.connect(func(): order.append("died"))
	enemy.take_damage(10.0, Vector3.ZERO)
	_assert_eq_int(2, order.size(), "ADV — exactly 2 signals on killing blow")
	if order.size() >= 2:
		_assert_eq_string("damaged", order[0], "ADV — damaged fires before died")
		_assert_eq_string("died", order[1], "ADV — died fires after damaged")
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Double-lethal blow — only first kills; second is noop
# ---------------------------------------------------------------------------

func test_adv_double_lethal_blow() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	var died_count = [0]
	var damaged_count = [0]
	enemy.died.connect(func(): died_count[0] += 1)
	enemy.damaged.connect(func(_d: float, _h: float): damaged_count[0] += 1)
	enemy.take_damage(15.0, Vector3(1.0, 0.0, 0.0))
	enemy.take_damage(15.0, Vector3(2.0, 0.0, 0.0))
	_assert_eq_int(1, died_count[0], "ADV — died emitted only once from double lethal")
	_assert_eq_int(1, damaged_count[0], "ADV — damaged emitted only once from double lethal")
	_assert_eq_float(0.0, enemy.current_hp, "ADV — HP clamped at 0.0 after double lethal")
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Rapid burst — death triggers mid-sequence (hit 4 of 5 kills)
# ---------------------------------------------------------------------------

func test_adv_rapid_damage_burst_death_midsequence() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	var damaged_count = [0]
	var died_count = [0]
	enemy.damaged.connect(func(_d: float, _h: float): damaged_count[0] += 1)
	enemy.died.connect(func(): died_count[0] += 1)
	for i in range(5):
		enemy.take_damage(3.0, Vector3.ZERO)
	_assert_eq_float(0.0, enemy.current_hp, "ADV — HP=0 after burst")
	_assert_eq_int(1, died_count[0], "ADV — died once during burst")
	_assert_eq_int(4, damaged_count[0], "ADV — damaged 4 times (hits 1-4), hit 5 is noop")
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Concurrent DoT + direct damage on same frame
# ---------------------------------------------------------------------------

func test_adv_dot_tick_then_direct_damage_same_frame() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(5.0, 4.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(8.0, enemy.current_hp, "ADV — poison tick: HP 10→8 (4.0 dps * 0.5)")
	enemy.take_damage(3.0, Vector3.ZERO)
	_assert_eq_float(5.0, enemy.current_hp, "ADV — direct damage after tick: HP 8→5")
	enemy.free()


func test_adv_direct_damage_then_dot_tick_kills() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(8.0, Vector3.ZERO)
	var died_count = [0]
	enemy.died.connect(func(): died_count[0] += 1)
	enemy.apply_poison(5.0, 8.0)
	enemy._effect_tracker._process(0.5)
	_assert_true(enemy.is_dead(), "ADV — DoT tick kills after direct damage")
	_assert_eq_int(1, died_count[0], "ADV — died once from DoT after direct damage")
	_assert_eq_float(0.0, enemy.current_hp, "ADV — HP clamped to 0")
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Two DoTs race — first kills, second is noop
# ---------------------------------------------------------------------------

func test_adv_two_dots_race_on_killing_tick() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(7.0, Vector3.ZERO)
	var died_count = [0]
	enemy.died.connect(func(): died_count[0] += 1)
	enemy.apply_poison(5.0, 10.0)
	enemy.apply_acid(5.0, 10.0)
	enemy._effect_tracker._process(0.5)
	_assert_true(enemy.is_dead(), "ADV — dead after dual-DoT tick")
	_assert_eq_int(1, died_count[0], "ADV — died exactly once despite two DoTs ticking")
	_assert_eq_float(0.0, enemy.current_hp, "ADV — HP clamped to 0")
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: DoT reapply after DoT kills — noop
# ---------------------------------------------------------------------------

func test_adv_dot_reapply_after_dot_kills() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(9.0, Vector3.ZERO)
	enemy.apply_poison(5.0, 4.0)
	enemy._effect_tracker._process(0.5)
	_assert_true(enemy.is_dead(), "ADV — enemy killed by DoT tick (HP 1 - 2 = -1 → 0)")
	enemy.apply_poison(5.0, 10.0)
	_assert_false(
		enemy._effect_tracker.has_active_dot("poison"),
		"ADV — poison reapply after death is noop; no active DoT"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Apply effects on a dead enemy are all noop
# ---------------------------------------------------------------------------

func test_adv_all_effects_noop_after_death() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(10.0, Vector3.ZERO)
	_assert_true(enemy.is_dead(), "ADV — enemy is dead")
	enemy.apply_poison(5.0, 2.0)
	enemy.apply_acid(5.0, 2.0)
	enemy.apply_slowness(0.5, 5.0)
	_assert_false(
		enemy._effect_tracker.has_active_dot("poison"),
		"ADV — apply_poison noop after death"
	)
	_assert_false(
		enemy._effect_tracker.has_active_dot("acid"),
		"ADV — apply_acid noop after death"
	)
	_assert_eq_float(
		1.0, enemy.get_speed_multiplier(),
		"ADV — apply_slowness noop after death"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: WEAKENED threshold with non-default max_hp values
# Primary suite only tests with max_hp=10. Adversarial: odd values, floats.
# ---------------------------------------------------------------------------

func test_adv_weakened_threshold_custom_max_hp_20() -> void:
	var enemy = _make_enemy()
	enemy.max_hp = 20.0
	enemy._ready()
	enemy.take_damage(10.0, Vector3.ZERO)
	_assert_eq_int(
		enemy.State.WEAKENED, enemy.current_state,
		"ADV — exactly 50% of max_hp=20 triggers WEAKENED"
	)
	enemy.free()


func test_adv_weakened_threshold_custom_max_hp_7() -> void:
	var enemy = _make_enemy()
	enemy.max_hp = 7.0
	enemy._ready()
	enemy.take_damage(3.5, Vector3.ZERO)
	_assert_eq_int(
		enemy.State.WEAKENED, enemy.current_state,
		"ADV — exactly 50% of max_hp=7 (3.5 HP) triggers WEAKENED"
	)
	enemy.free()


func test_adv_weakened_threshold_just_above() -> void:
	var enemy = _make_enemy()
	enemy.max_hp = 100.0
	enemy._ready()
	enemy.take_damage(49.99, Vector3.ZERO)
	_assert_eq_int(
		enemy.State.NORMAL, enemy.current_state,
		"ADV — HP 50.01 (>50%) stays NORMAL"
	)
	enemy.free()


func test_adv_weakened_threshold_just_below() -> void:
	var enemy = _make_enemy()
	enemy.max_hp = 100.0
	enemy._ready()
	enemy.take_damage(50.01, Vector3.ZERO)
	_assert_eq_int(
		enemy.State.WEAKENED, enemy.current_state,
		"ADV — HP 49.99 (<50%) triggers WEAKENED"
	)
	enemy.free()


func test_adv_weakened_constant_value() -> void:
	var enemy = _make_enemy()
	_assert_eq_float(
		0.5, enemy.WEAKENED_HP_THRESHOLD,
		"ADV — WEAKENED_HP_THRESHOLD constant is 0.5"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Zero max_hp edge cases
# ---------------------------------------------------------------------------

func test_adv_zero_max_hp_weakened_never_triggers() -> void:
	var enemy = _make_enemy()
	enemy.max_hp = 0.0
	enemy._ready()
	_assert_eq_float(0.0, enemy.current_hp, "ADV — current_hp=0 with max_hp=0")
	enemy.take_damage(0.0, Vector3.ZERO)
	_assert_true(
		enemy.is_dead() or enemy.current_state != enemy.State.WEAKENED,
		"ADV — max_hp=0: death or never-WEAKENED (threshold=0, HP=0 → dead)",
		"state=" + str(enemy.current_state) + " is_dead=" + str(enemy.is_dead())
	)
	enemy.free()


func test_adv_tiny_max_hp() -> void:
	var enemy = _make_enemy()
	enemy.max_hp = 0.001
	enemy._ready()
	_assert_eq_float(0.001, enemy.current_hp, "ADV — tiny max_hp initializes")
	enemy.take_damage(0.001, Vector3.ZERO)
	_assert_true(enemy.is_dead(), "ADV — tiny max_hp killed by matching damage")
	_assert_eq_float(0.0, enemy.current_hp, "ADV — HP clamped to 0")
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Floating-point HP accumulation
# Repeated small damages should not cause negative HP or drift.
# ---------------------------------------------------------------------------

func test_adv_floating_point_many_small_damages() -> void:
	var enemy = _make_enemy()
	enemy.max_hp = 1.0
	enemy._ready()
	for i in range(100):
		enemy.take_damage(0.01, Vector3.ZERO)
	_assert_true(
		enemy.current_hp >= 0.0,
		"ADV — HP never negative after 100 * 0.01 damage on 1.0 HP",
		"current_hp=" + str(enemy.current_hp)
	)
	enemy.free()


func test_adv_floating_point_dot_accumulation() -> void:
	var enemy = _make_enemy()
	enemy.max_hp = 5.0
	enemy._ready()
	enemy.apply_poison(10.0, 0.1)
	for i in range(20):
		enemy._effect_tracker._process(0.5)
	_assert_true(
		enemy.current_hp >= 0.0,
		"ADV — HP never negative after 20 DoT ticks of 0.05",
		"current_hp=" + str(enemy.current_hp)
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Knockback decay over many frames
# Verify convergence to zero; no floating-point divergence or NaN.
# ---------------------------------------------------------------------------

func test_adv_knockback_decay_converges_to_zero() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(1.0, Vector3(100.0, 50.0, 100.0))
	for i in range(200):
		enemy._physics_process(1.0 / 60.0)
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3.ZERO, 0.001,
		"ADV — knockback converges to zero after 200 frames"
	)
	enemy.free()


func test_adv_knockback_no_nan_after_extreme_values() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(1.0, Vector3(9999.0, 9999.0, 9999.0))
	for i in range(500):
		enemy._physics_process(1.0 / 60.0)
	var kb = enemy._knockback_velocity
	_assert_false(
		is_nan(kb.x) or is_nan(kb.y) or is_nan(kb.z),
		"ADV — no NaN in knockback after extreme impulse + 500 frames"
	)
	_assert_vec3_near(
		kb, Vector3.ZERO, 0.01,
		"ADV — extreme knockback decays to zero"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: DoT lag spike — large delta causes multiple ticks in one frame
# Spec says: "Multiple ticks can fire in a single frame if delta is large"
# ---------------------------------------------------------------------------

func test_adv_dot_lag_spike_multiple_ticks() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(5.0, 2.0)
	enemy._effect_tracker._process(1.5)
	var ticks_fired = 3
	var expected_hp = 10.0 - (ticks_fired * 2.0 * 0.5)
	_assert_eq_float(
		expected_hp, enemy.current_hp,
		"ADV — 1.5s delta fires 3 ticks (floor(1.5/0.5)=3); HP 10→7"
	)
	enemy.free()


func test_adv_dot_lag_spike_kills_midway() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(7.0, Vector3.ZERO)
	enemy.apply_poison(5.0, 10.0)
	enemy._effect_tracker._process(1.5)
	_assert_true(enemy.is_dead(), "ADV — DoT lag spike kills during multi-tick burst")
	_assert_eq_float(0.0, enemy.current_hp, "ADV — HP clamped at 0 after lag spike kill")
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: DoT with negative/invalid parameters
# ---------------------------------------------------------------------------

func test_adv_dot_negative_duration() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(-1.0, 5.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(
		10.0, enemy.current_hp,
		"ADV — negative duration: no ticks fire; HP unchanged"
	)
	enemy.free()


func test_adv_dot_negative_dps() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_poison(2.0, -5.0)
	enemy._effect_tracker._process(0.5)
	_assert_true(
		enemy.current_hp >= 10.0,
		"ADV — negative DPS does not heal enemy (HP stays >= 10.0)",
		"current_hp=" + str(enemy.current_hp)
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Slowness expiry boundary precision
# ---------------------------------------------------------------------------

func test_adv_slowness_expires_exactly_on_boundary() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(0.5, 1.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(
		0.5, enemy.get_speed_multiplier(),
		"ADV — slowness still active at 0.5s (half of 1.0s duration)"
	)
	enemy._effect_tracker._process(0.5)
	_assert_eq_float(
		1.0, enemy.get_speed_multiplier(),
		"ADV — slowness expired exactly at 1.0s boundary"
	)
	enemy.free()


func test_adv_slowness_many_small_deltas() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(0.3, 1.0)
	for i in range(100):
		enemy._effect_tracker._process(0.01)
	_assert_eq_float(
		1.0, enemy.get_speed_multiplier(),
		"ADV — slowness expires after 100 * 0.01 = 1.0s via small deltas"
	)
	enemy.free()


func test_adv_slowness_greater_than_one_speed_boost() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.apply_slowness(1.5, 2.0)
	_assert_eq_float(
		1.5, enemy.get_speed_multiplier(),
		"ADV — multiplier > 1.0 is valid (speed boost); no clamping"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Zero-knockback does not overwrite residual (EHD-3i)
# ---------------------------------------------------------------------------

func test_adv_zero_knockback_preserves_residual() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(1.0, Vector3(10.0, 0.0, 0.0))
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3(10.0, 0.0, 0.0), 0.001,
		"ADV — first hit sets knockback"
	)
	enemy.take_damage(1.0, Vector3.ZERO)
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3(10.0, 0.0, 0.0), 0.001,
		"ADV — zero knockback does NOT overwrite existing residual (EHD-3i)"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: EnemyEffectTracker isolation — stress and edge cases
# ---------------------------------------------------------------------------

func test_adv_tracker_add_many_dot_types() -> void:
	var tracker = _make_tracker()
	tracker.add_dot("poison", 5.0, 1.0)
	tracker.add_dot("acid", 5.0, 1.0)
	tracker.add_dot("fire", 5.0, 1.0)
	tracker.add_dot("ice", 5.0, 1.0)
	_assert_true(tracker.has_active_dot("poison"), "ADV — poison active in multi-type")
	_assert_true(tracker.has_active_dot("acid"), "ADV — acid active in multi-type")
	_assert_true(tracker.has_active_dot("fire"), "ADV — fire active in multi-type")
	_assert_true(tracker.has_active_dot("ice"), "ADV — ice active in multi-type")
	tracker.free()


func test_adv_tracker_stop_then_readd() -> void:
	var tracker = _make_tracker()
	tracker.add_dot("poison", 5.0, 2.0)
	tracker.stop_all_effects()
	_assert_false(tracker.has_active_dot("poison"), "ADV — poison cleared after stop")
	tracker.add_dot("poison", 3.0, 1.0)
	_assert_true(tracker.has_active_dot("poison"), "ADV — poison re-added after stop")
	tracker.free()


func test_adv_tracker_two_instances_isolated() -> void:
	var t1 = _make_tracker()
	var t2 = _make_tracker()
	t1.add_dot("poison", 5.0, 2.0)
	t2.set_slowness(0.3, 5.0)
	_assert_true(t1.has_active_dot("poison"), "ADV — tracker1 has poison")
	_assert_false(t2.has_active_dot("poison"), "ADV — tracker2 does NOT have poison")
	_assert_eq_float(1.0, t1.get_speed_multiplier(), "ADV — tracker1 no slowness")
	_assert_eq_float(0.3, t2.get_speed_multiplier(), "ADV — tracker2 has slowness")
	t1.free()
	t2.free()


func test_adv_tracker_stop_all_is_idempotent() -> void:
	var tracker = _make_tracker()
	tracker.stop_all_effects()
	tracker.stop_all_effects()
	_assert_eq_float(
		1.0, tracker.get_speed_multiplier(),
		"ADV — double stop_all_effects is safe"
	)
	_assert_false(
		tracker.has_active_dot("poison"),
		"ADV — no poison after double stop"
	)
	tracker.free()


# ---------------------------------------------------------------------------
# ADV: Signal isolation — DoT tick vs direct damage
# ---------------------------------------------------------------------------

func test_adv_dot_tick_and_direct_damage_signal_isolation() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	var damaged_count = [0]
	var dot_tick_count = [0]
	enemy.damaged.connect(func(_d: float, _h: float): damaged_count[0] += 1)
	enemy.dot_tick.connect(func(_n: String, _d: float, _h: float): dot_tick_count[0] += 1)
	enemy.apply_poison(5.0, 2.0)
	enemy._effect_tracker._process(0.5)
	enemy.take_damage(1.0, Vector3.ZERO)
	_assert_eq_int(1, damaged_count[0], "ADV — damaged signal count is 1 (only from take_damage)")
	_assert_eq_int(1, dot_tick_count[0], "ADV — DoT tick emits exactly 1 dot_tick signal")
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: dot_tick signal not emitted after death
# ---------------------------------------------------------------------------

func test_adv_dot_tick_signal_stops_after_death() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(9.0, Vector3.ZERO)
	var tick_count = [0]
	enemy.dot_tick.connect(func(_n: String, _d: float, _h: float): tick_count[0] += 1)
	enemy.apply_poison(5.0, 4.0)
	enemy._effect_tracker._process(0.5)
	_assert_true(enemy.is_dead(), "ADV — enemy killed by first DoT tick")
	var count_at_death = tick_count[0]
	enemy._effect_tracker._process(0.5)
	enemy._effect_tracker._process(0.5)
	_assert_eq_int(
		count_at_death, tick_count[0],
		"ADV — no dot_tick signals after death"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Damage of exactly current_hp (precision kill)
# ---------------------------------------------------------------------------

func test_adv_exact_hp_damage_kills() -> void:
	var enemy = _make_enemy()
	enemy.max_hp = 3.7
	enemy._ready()
	enemy.take_damage(3.7, Vector3.ZERO)
	_assert_true(enemy.is_dead(), "ADV — exact current_hp damage kills (3.7)")
	_assert_eq_float(0.0, enemy.current_hp, "ADV — HP exactly 0.0 after precision kill")
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Knockback applied and then physics process on dead enemy
# Dead enemies should not process knockback (no velocity changes).
# ---------------------------------------------------------------------------

func test_adv_physics_process_noop_after_death() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(5.0, Vector3(10.0, 0.0, 0.0))
	enemy.take_damage(5.0, Vector3.ZERO)
	_assert_true(enemy.is_dead(), "ADV — enemy is dead after two hits totaling 10")
	var kb_before = enemy._knockback_velocity
	enemy._physics_process(1.0 / 60.0)
	_assert_vec3_near(
		enemy._knockback_velocity, kb_before, 0.001,
		"ADV — _physics_process does not mutate knockback on dead enemy"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: WEAKENED state transition via DoT with custom max_hp
# ---------------------------------------------------------------------------

func test_adv_weakened_via_dot_custom_max_hp() -> void:
	var enemy = _make_enemy()
	enemy.max_hp = 20.0
	enemy._ready()
	enemy.apply_poison(10.0, 20.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_int(
		enemy.State.WEAKENED, enemy.current_state,
		"ADV — DoT tick triggers WEAKENED on custom max_hp=20 (10.0 dps * 0.5 = 5.0 → HP 15 not yet); two ticks needed"
	)
	_assert_eq_float(
		10.0, enemy.current_hp,
		"ADV — HP after 1 tick: 20 - 10 = 10 (50% of 20)"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: INFECTED + active DoT — WEAKENED threshold skipped (EHD-5f)
# ---------------------------------------------------------------------------

func test_adv_infected_during_dot_no_weakened_trigger() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.set_base_state(enemy.State.INFECTED)
	enemy.apply_poison(5.0, 10.0)
	enemy._effect_tracker._process(0.5)
	_assert_eq_int(
		enemy.State.INFECTED, enemy.current_state,
		"ADV — INFECTED state unchanged despite DoT reducing HP below 50%"
	)
	_assert_eq_float(5.0, enemy.current_hp, "ADV — DoT still deals damage in INFECTED state")
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Negative damage + knockback — knockback still applies
# ---------------------------------------------------------------------------

func test_adv_negative_damage_with_knockback() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(-10.0, Vector3(5.0, 0.0, 0.0))
	_assert_eq_float(10.0, enemy.current_hp, "ADV — negative damage treated as 0")
	_assert_vec3_near(
		enemy._knockback_velocity, Vector3(5.0, 0.0, 0.0), 0.001,
		"ADV — knockback still applied with negative damage"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Zero-damage take_damage on already-dead enemy
# ---------------------------------------------------------------------------

func test_adv_zero_damage_on_dead_enemy() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(10.0, Vector3.ZERO)
	var damaged_after = [0]
	enemy.damaged.connect(func(_d: float, _h: float): damaged_after[0] += 1)
	enemy.take_damage(0.0, Vector3.ZERO)
	_assert_eq_int(0, damaged_after[0], "ADV — zero damage on dead enemy emits nothing")
	enemy.free()


# ---------------------------------------------------------------------------
# ADV: Knockback multi-axis decay is uniform
# ---------------------------------------------------------------------------

func test_adv_knockback_3axis_decay_uniform() -> void:
	var enemy = _make_enemy()
	enemy._ready()
	enemy.take_damage(1.0, Vector3(10.0, 5.0, 8.0))
	enemy._physics_process(1.0 / 60.0)
	var rate = enemy.KNOCKBACK_DECAY_RATE
	var expected = Vector3(10.0 * rate, 5.0 * rate, 8.0 * rate)
	_assert_vec3_near(
		enemy._knockback_velocity, expected, 0.01,
		"ADV — all 3 axes decay at the same rate"
	)
	enemy.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_health_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Killing-blow knockback gating
	test_adv_killing_blow_does_not_apply_knockback()
	test_adv_near_lethal_blow_does_apply_knockback()

	# Signal ordering on killing blow
	test_adv_damaged_signal_fires_on_killing_blow()
	test_adv_signal_order_damaged_before_died()

	# Double-lethal and rapid burst
	test_adv_double_lethal_blow()
	test_adv_rapid_damage_burst_death_midsequence()

	# Concurrent DoT + direct damage
	test_adv_dot_tick_then_direct_damage_same_frame()
	test_adv_direct_damage_then_dot_tick_kills()

	# Two DoTs race on killing tick
	test_adv_two_dots_race_on_killing_tick()

	# DoT reapply after death
	test_adv_dot_reapply_after_dot_kills()
	test_adv_all_effects_noop_after_death()

	# WEAKENED threshold with custom max_hp
	test_adv_weakened_threshold_custom_max_hp_20()
	test_adv_weakened_threshold_custom_max_hp_7()
	test_adv_weakened_threshold_just_above()
	test_adv_weakened_threshold_just_below()
	test_adv_weakened_constant_value()

	# Zero and tiny max_hp
	test_adv_zero_max_hp_weakened_never_triggers()
	test_adv_tiny_max_hp()

	# Floating-point accumulation
	test_adv_floating_point_many_small_damages()
	test_adv_floating_point_dot_accumulation()

	# Knockback decay convergence
	test_adv_knockback_decay_converges_to_zero()
	test_adv_knockback_no_nan_after_extreme_values()

	# DoT lag spike multi-tick
	test_adv_dot_lag_spike_multiple_ticks()
	test_adv_dot_lag_spike_kills_midway()

	# Invalid DoT parameters
	test_adv_dot_negative_duration()
	test_adv_dot_negative_dps()

	# Slowness precision and edge values
	test_adv_slowness_expires_exactly_on_boundary()
	test_adv_slowness_many_small_deltas()
	test_adv_slowness_greater_than_one_speed_boost()

	# Zero-knockback residual preservation
	test_adv_zero_knockback_preserves_residual()

	# Tracker isolation and stress
	test_adv_tracker_add_many_dot_types()
	test_adv_tracker_stop_then_readd()
	test_adv_tracker_two_instances_isolated()
	test_adv_tracker_stop_all_is_idempotent()

	# Signal isolation: DoT vs direct
	test_adv_dot_tick_and_direct_damage_signal_isolation()
	test_adv_dot_tick_signal_stops_after_death()

	# Precision kill
	test_adv_exact_hp_damage_kills()

	# Physics process on dead enemy
	test_adv_physics_process_noop_after_death()

	# WEAKENED via DoT with custom max_hp
	test_adv_weakened_via_dot_custom_max_hp()

	# INFECTED + DoT interaction
	test_adv_infected_during_dot_no_weakened_trigger()

	# Negative damage + knockback
	test_adv_negative_damage_with_knockback()

	# Zero damage on dead
	test_adv_zero_damage_on_dead_enemy()

	# Multi-axis knockback decay
	test_adv_knockback_3axis_decay_uniform()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
