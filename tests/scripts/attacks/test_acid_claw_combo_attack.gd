#
# test_acid_claw_combo_attack.gd
#
# Behavioral tests for the Acid + Claw fusion attack (Venomous Shred).
# Covers AttackResource schema extension (AC-1), MELEE_SWIPE_COMBO handler
# dispatch (AC-2), modifier dispatch for combo path (AC-4), AttackDatabase
# registration (AC-5), integration behavior (AC-6), and MELEE_SWIPE non-regression.
#
# Spec: project_board/specs/acid_claw_fusion_attack_spec.md
# Ticket: project_board/12_milestone_12_fused_mutation_attacks/in_progress/04_acid_claw_fusion_attack.md
# Traceability: AC-1 through AC-6, AC-NF-1, AC-NF-4, AC-NF-5
#
# NOTE: Tests will be RED until implementation:
#   - AttackResource.combo_hits field (AC-1/AC-DD-5)
#   - AttackExecutor MELEE_SWIPE_COMBO case (AC-2/AC-DD-2)
#   - AttackExecutor._apply_combo_modifiers() (AC-4)
#   - AttackDatabase acid_claw registration update (AC-5/AC-DD-1)
#   - EnemyBase.apply_acid_stack() / get_acid_stack_count() (AC-3/AC-DD-3)
#   - EnemyEffectTracker.add_acid_stack() / get_acid_stack_count() (AC-3/AC-DD-4)
#

class_name AcidClawComboAttackTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

# ---------------------------------------------------------------------------
# Mock inner classes
# ---------------------------------------------------------------------------

class MockEnemy extends Node3D:
	var damage_taken: Array = []
	var acid_stack_calls: Array = []
	var acid_calls: Array = []
	var current_state: int = 0
	var is_dead_flag: bool = false
	var _acid_stack_count: int = 0

	func take_damage(damage: float, knockback: Vector3) -> void:
		if is_dead_flag:
			return
		damage_taken.append({"damage": damage, "knockback": knockback})

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag

	func apply_acid(duration: float, dps: float) -> void:
		acid_calls.append({"duration": duration, "dps": dps})

	func apply_acid_stack(duration: float, dps: float) -> void:
		if is_dead_flag:
			return
		_acid_stack_count += 1
		acid_stack_calls.append({"duration": duration, "dps": dps})

	func get_acid_stack_count() -> int:
		return _acid_stack_count


class WeakenedEnemy extends Node3D:
	var damage_taken: Array = []
	var acid_stack_calls: Array = []
	var current_state: int = 1  # WEAKENED
	var is_dead_flag: bool = false
	var _acid_stack_count: int = 0

	func take_damage(damage: float, knockback: Vector3) -> void:
		if is_dead_flag:
			return
		damage_taken.append({"damage": damage, "knockback": knockback})

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag

	func apply_acid_stack(duration: float, dps: float) -> void:
		if is_dead_flag:
			return
		_acid_stack_count += 1
		acid_stack_calls.append({"duration": duration, "dps": dps})

	func get_acid_stack_count() -> int:
		return _acid_stack_count


class NoAcidStackEnemy extends Node3D:
	# Enemy WITHOUT apply_acid_stack — tests has_method guard
	var damage_taken: Array = []
	var current_state: int = 0

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

	func get_base_state() -> int:
		return current_state

	func is_dead() -> bool:
		return false


class PoisonSlowEnemy extends Node3D:
	# Enemy with poison and slowness methods but NOT apply_acid_stack
	# Used by test_ac4e to verify non-acid modifiers route correctly in combo path
	var poison_calls: Array = []
	var slow_calls: Array = []
	var current_state: int = 0

	func apply_poison(duration: float, dps: float) -> void:
		poison_calls.append({"duration": duration, "dps": dps})

	func apply_slowness(multiplier: float, duration: float) -> void:
		slow_calls.append({"multiplier": multiplier, "duration": duration})

	func get_base_state() -> int:
		return current_state

	func is_dead() -> bool:
		return false


class MockParent extends Node3D:
	var _facing: float = 1.0
	func get_facing_sign() -> float:
		return _facing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_combo_resource(combo_hits: int = 3) -> AttackResource:
	var r = AttackResource.new()
	r.attack_id = 101
	r.attack_name = "Venomous Shred"
	r.description = "3-hit melee combo — each hit applies a separate acid stack"
	r.effect_type = "MELEE_SWIPE_COMBO"
	r.damage = 1.8
	r.cooldown = 2.0
	r.attack_range = 1.2
	r.startup_frames = 0
	r.knockback_magnitude = 80.0
	r.knockback_direction = "away"
	r.modifiers = {
		"acid_on_hit": true,
		"acid_duration": 2.5,
		"acid_dps": 0.4,
		"combo_frame_interval": 6
	}
	r.set("combo_hits", combo_hits)
	return r


func _make_resource(overrides: Dictionary = {}) -> AttackResource:
	var r = AttackResource.new()
	r.startup_frames = 0
	for key in overrides:
		r.set(key, overrides[key])
	return r


func _make_melee_swipe_resource() -> AttackResource:
	var r = AttackResource.new()
	r.attack_id = 1
	r.attack_name = "Claw Swipe"
	r.effect_type = "MELEE_SWIPE"
	r.damage = 3.0
	r.cooldown = 0.8
	r.attack_range = 1.5
	r.startup_frames = 0
	r.knockback_magnitude = 2.0
	r.knockback_direction = "away"
	r.modifiers = {}
	return r


func _build_scene(label: String, enemies: Array = [], pos: Vector3 = Vector3.ZERO, facing: float = 1.0) -> Dictionary:
	var parent = MockParent.new()
	parent._facing = facing
	var result = AttackExecutorHarness.build_scene(parent, enemies, pos)
	if result.is_empty():
		_fail_test(label, "executor not loadable")
	return result


func _teardown(scene: Dictionary) -> void:
	AttackExecutorHarness.teardown_scene(scene)


var _signals_log: Array = []

func _reset_signals() -> void:
	_signals_log = []

func _connect_all_signals(executor: Node) -> void:
	_reset_signals()
	executor.connect("attack_started", func(r): _signals_log.append({"name": "attack_started", "resource": r}))
	executor.connect("attack_hit", func(t, r): _signals_log.append({"name": "attack_hit", "target": t, "resource": r}))
	executor.connect("melee_vfx_requested", func(pos, col, sc): _signals_log.append({"name": "melee_vfx_requested", "position": pos, "color": col, "scale": sc}))


func _count_signal(signal_name: String) -> int:
	var count := 0
	for entry in _signals_log:
		if entry["name"] == signal_name:
			count += 1
	return count


# ---------------------------------------------------------------------------
# AC-1: AttackResource Schema Extension — combo_hits field
# ---------------------------------------------------------------------------

func test_ac1a_default_combo_hits_is_one() -> void:
	# AC-1a: AttackResource.new() produces combo_hits == 1
	var r = AttackResource.new()
	var combo_hits = r.get("combo_hits")
	_assert_true(combo_hits != null, "AC-1a_combo_hits_field_exists")
	if combo_hits != null:
		_assert_eq_int(1, combo_hits, "AC-1a_default_is_1")
	r.free()


func test_ac1b_assign_combo_hits_3_roundtrip() -> void:
	# AC-1b: Assigning combo_hits = 3 and reading back returns 3
	var r = AttackResource.new()
	r.set("combo_hits", 3)
	_assert_eq_int(3, r.get("combo_hits"), "AC-1b_combo_hits_3")
	r.free()


func test_ac1c_assign_combo_hits_0_stores_0() -> void:
	# AC-1c: Assigning combo_hits = 0 stores 0 (no clamping by field)
	var r = AttackResource.new()
	r.set("combo_hits", 0)
	_assert_eq_int(0, r.get("combo_hits"), "AC-1c_combo_hits_0")
	r.free()


func test_ac1d_assign_combo_hits_negative_stores_negative() -> void:
	# AC-1d: Assigning combo_hits = -1 stores -1 (no clamping by field)
	var r = AttackResource.new()
	r.set("combo_hits", -1)
	_assert_eq_int(-1, r.get("combo_hits"), "AC-1d_combo_hits_neg1")
	r.free()


func test_ac1e_other_fields_unset_combo_hits_defaults_to_1() -> void:
	# AC-1e: A resource created with other fields set but combo_hits unset returns 1
	var r = _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 5.0,
		"attack_range": 2.0
	})
	var combo_hits = r.get("combo_hits")
	_assert_true(combo_hits != null, "AC-1e_field_exists")
	if combo_hits != null:
		_assert_eq_int(1, combo_hits, "AC-1e_default_1_when_unset")
	r.free()


func test_ac1f_combo_hits_is_int_float_coerces() -> void:
	# AC-1f: combo_hits is int — assigning 2.9 coerces to 2
	var r = AttackResource.new()
	r.set("combo_hits", 2.9)
	var val = r.get("combo_hits")
	_assert_true(val != null, "AC-1f_field_exists")
	if val != null:
		_assert_true(typeof(val) == TYPE_INT or (typeof(val) == TYPE_FLOAT and int(val) == 2),
			"AC-1f_int_or_coerced_to_2")
	r.free()


# ---------------------------------------------------------------------------
# AC-2: MELEE_SWIPE_COMBO handler dispatch
# ---------------------------------------------------------------------------

func test_ac2a_combo_hits_3_produces_3_attack_hit_signals() -> void:
	# AC-2a: combo_hits==3 results in exactly 3 attack_hit emissions
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-2a", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	_connect_all_signals(scene["executor"])
	scene["executor"].execute_attack(_make_combo_resource(3))
	_assert_eq_int(3, _count_signal("attack_hit"), "AC-2a_3_hit_signals")
	_teardown(scene)


func test_ac2g_attack_started_emitted_once_not_per_hit() -> void:
	# AC-2g: attack_started emitted exactly once at combo start
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-2g", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	_connect_all_signals(scene["executor"])
	scene["executor"].execute_attack(_make_combo_resource(3))
	_assert_eq_int(1, _count_signal("attack_started"), "AC-2g_started_once_not_per_hit")
	_teardown(scene)


func test_ac2f_melee_vfx_emitted_once_per_hit() -> void:
	# AC-2f: melee_vfx_requested emitted 3 times for combo_hits==3
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-2f", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	_connect_all_signals(scene["executor"])
	scene["executor"].execute_attack(_make_combo_resource(3))
	_assert_eq_int(3, _count_signal("melee_vfx_requested"), "AC-2f_3_vfx_emissions")
	_teardown(scene)


func test_ac2h_combo_hits_0_fires_no_attack_hit() -> void:
	# AC-2h: combo_hits==0 → no attack_hit signal, _is_active returns false
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-2h", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.execute_attack(_make_combo_resource(0))
	_assert_eq_int(0, _count_signal("attack_hit"), "AC-2h_no_hits_for_0")
	_assert_false(executor.is_active(), "AC-2h_is_active_false")
	_teardown(scene)


func test_ac2i_combo_hits_1_fires_exactly_one_hit() -> void:
	# AC-2i: combo_hits==1 → exactly one hit fires
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-2i", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	_connect_all_signals(scene["executor"])
	scene["executor"].execute_attack(_make_combo_resource(1))
	_assert_eq_int(1, _count_signal("attack_hit"), "AC-2i_1_hit_for_combo_hits_1")
	_teardown(scene)


func test_ac2l_is_active_false_after_combo_completes() -> void:
	# AC-2l: _is_active == false after the synchronous portion completes
	# (applies to combo_hits > 0 with no async delays, verified via direct call)
	var scene = _build_scene("AC-2l", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	# For combo_hits = 0, the handler completes synchronously
	executor.execute_attack(_make_combo_resource(0))
	_assert_false(executor.is_active(), "AC-2l_is_active_false_after_0_hit_combo")
	_teardown(scene)


func test_ac2k_second_execute_while_active_blocked() -> void:
	# AC-2k: A second execute_attack while _is_active == true is silently ignored
	# We simulate this by calling twice in rapid succession; the first call that
	# sets _is_active=true should block the second.
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-2k", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	# Manually set _is_active = true then try to fire
	executor._is_active = true
	executor.execute_attack(_make_combo_resource(3))
	_assert_eq_int(0, _count_signal("attack_hit"), "AC-2k_blocked_while_active")
	_teardown(scene)


# ---------------------------------------------------------------------------
# AC-2d: apply_acid_stack called per hit (not apply_acid)
# ---------------------------------------------------------------------------

func test_ac2d_each_hit_calls_apply_acid_stack_not_apply_acid() -> void:
	# AC-2d: each hit calls apply_acid_stack on the enemy, NOT apply_acid
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-2d", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_combo_resource(3))
	_assert_eq_int(3, enemy.acid_stack_calls.size(), "AC-2d_3_acid_stack_calls")
	_assert_eq_int(0, enemy.acid_calls.size(), "AC-2d_no_apply_acid")
	_teardown(scene)


func test_ac2e_knockback_applied_per_hit() -> void:
	# AC-2e: each hit applies knockback independently
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-2e", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_combo_resource(3))
	_assert_eq_int(3, enemy.damage_taken.size(), "AC-2e_3_damage_calls")
	for i in range(enemy.damage_taken.size()):
		var kb: Vector3 = enemy.damage_taken[i]["knockback"]
		_assert_true(kb.length() > 0.0, "AC-2e_kb_nonzero_hit_" + str(i))
	_teardown(scene)


func test_ac2_damage_per_hit_is_1_8() -> void:
	# Normative damage from AC-DD-1: damage per hit = 1.8
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC_damage_1_8", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_combo_resource(3))
	if enemy.damage_taken.size() >= 3:
		_assert_eq_float(1.8, enemy.damage_taken[0]["damage"], "AC_damage_hit0_1_8")
		_assert_eq_float(1.8, enemy.damage_taken[1]["damage"], "AC_damage_hit1_1_8")
		_assert_eq_float(1.8, enemy.damage_taken[2]["damage"], "AC_damage_hit2_1_8")
	else:
		_fail_test("AC_damage_1_8", "expected 3 hits, got " + str(enemy.damage_taken.size()))
	_teardown(scene)


# ---------------------------------------------------------------------------
# AC-4: Modifier dispatch for MELEE_SWIPE_COMBO path
# ---------------------------------------------------------------------------

func test_ac4a_normal_enemy_acid_stack_gets_correct_params() -> void:
	# AC-4a: _apply_combo_modifiers with NORMAL enemy → apply_acid_stack(2.5, 0.4)
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("AC-4a", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 0
	var mods := {"acid_on_hit": true, "acid_duration": 2.5, "acid_dps": 0.4}
	if executor.has_method("_apply_combo_modifiers"):
		executor._apply_combo_modifiers(enemy, mods)
		_assert_eq_int(1, enemy.acid_stack_calls.size(), "AC-4a_stack_applied")
		if enemy.acid_stack_calls.size() > 0:
			_assert_eq_float(2.5, enemy.acid_stack_calls[0]["duration"], "AC-4a_duration_2_5")
			_assert_eq_float(0.4, enemy.acid_stack_calls[0]["dps"], "AC-4a_dps_0_4")
		_assert_eq_int(0, enemy.acid_calls.size(), "AC-4a_no_apply_acid_called")
	else:
		_fail_test("AC-4a", "_apply_combo_modifiers not yet implemented")
	enemy.free()
	executor.free()


func test_ac4b_weakened_enemy_doubles_acid_duration() -> void:
	# AC-4b: WEAKENED state doubles acid_duration (2.5 * 2.0 = 5.0)
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("AC-4b", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 1  # WEAKENED
	var mods := {"acid_on_hit": true, "acid_duration": 2.5, "acid_dps": 0.4}
	if executor.has_method("_apply_combo_modifiers"):
		executor._apply_combo_modifiers(enemy, mods)
		if enemy.acid_stack_calls.size() > 0:
			_assert_eq_float(5.0, enemy.acid_stack_calls[0]["duration"], "AC-4b_doubled_to_5_0")
			_assert_eq_float(0.4, enemy.acid_stack_calls[0]["dps"], "AC-4b_dps_unchanged")
		else:
			_fail_test("AC-4b", "acid stack not applied on weakened enemy")
	else:
		_fail_test("AC-4b", "_apply_combo_modifiers not yet implemented")
	enemy.free()
	executor.free()


func test_ac4c_apply_acid_not_called_in_combo_modifier() -> void:
	# AC-4c: apply_acid is NOT called via _apply_combo_modifiers
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("AC-4c", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 0
	var mods := {"acid_on_hit": true, "acid_duration": 2.5, "acid_dps": 0.4}
	if executor.has_method("_apply_combo_modifiers"):
		executor._apply_combo_modifiers(enemy, mods)
		_assert_eq_int(0, enemy.acid_calls.size(), "AC-4c_apply_acid_not_called")
	else:
		_fail_test("AC-4c", "_apply_combo_modifiers not yet implemented")
	enemy.free()
	executor.free()


func test_ac4d_missing_apply_acid_stack_method_no_crash() -> void:
	# AC-4d: target without apply_acid_stack method → no crash
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("AC-4d", "executor not loadable")
		return
	var enemy = NoAcidStackEnemy.new()
	var mods := {"acid_on_hit": true, "acid_duration": 2.5, "acid_dps": 0.4}
	if executor.has_method("_apply_combo_modifiers"):
		executor._apply_combo_modifiers(enemy, mods)
		_pass_test("AC-4d_no_crash_without_apply_acid_stack")
	else:
		_fail_test("AC-4d", "_apply_combo_modifiers not yet implemented")
	enemy.free()
	executor.free()


func test_ac4e_non_acid_modifiers_work_in_combo_path() -> void:
	# AC-4e: non-acid modifiers (poison, slow) in _apply_combo_modifiers behave same as _apply_modifiers
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("AC-4e", "executor not loadable")
		return
	var enemy = PoisonSlowEnemy.new()
	var mods := {
		"acid_on_hit": false,
		"poison": true, "poison_duration": 2.0, "poison_dps": 0.3,
		"slow": 0.5, "slow_duration": 1.5
	}
	if executor.has_method("_apply_combo_modifiers"):
		executor._apply_combo_modifiers(enemy, mods)
		_assert_eq_int(1, enemy.poison_calls.size(), "AC-4e_poison_applied")
		_assert_eq_int(1, enemy.slow_calls.size(), "AC-4e_slow_applied")
	else:
		_fail_test("AC-4e", "_apply_combo_modifiers not yet implemented")
	enemy.free()
	executor.free()


# AC-5 database registration tests have been split to:
# tests/scripts/attacks/test_acid_claw_database_registration.gd
# (keeps this file under the 900-line limit per project organization rules)

# ---------------------------------------------------------------------------
# AC-6: Integration — full combo behavior
# ---------------------------------------------------------------------------

func test_ac6a_full_combo_3_stacks_on_single_enemy() -> void:
	# AC-6a: After 3-hit combo, enemy.get_acid_stack_count() == 3
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-6a", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_combo_resource(3))
	_assert_eq_int(3, enemy.get_acid_stack_count(), "AC-6a_3_stacks_after_combo")
	_teardown(scene)


func test_ac6b_full_combo_5_4_direct_damage() -> void:
	# AC-6b: 3 hits × 1.8 damage = 5.4 total direct damage
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-6b", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_combo_resource(3))
	var total_damage := 0.0
	for hit in enemy.damage_taken:
		total_damage += hit["damage"]
	_assert_eq_float(5.4, total_damage, "AC-6b_5_4_total_direct_damage")
	_teardown(scene)


func test_ac6c_each_stack_initialized_to_2_5s() -> void:
	# AC-6c: each acid stack has duration 2.5s at application
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-6c", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_combo_resource(3))
	for i in range(enemy.acid_stack_calls.size()):
		_assert_eq_float(2.5, enemy.acid_stack_calls[i]["duration"], "AC-6c_duration_2_5_hit_" + str(i))
	_teardown(scene)


# ---------------------------------------------------------------------------
# AC-NF-1: Backward compatibility — MELEE_SWIPE path not regressed
# ---------------------------------------------------------------------------

func test_acnf1_melee_swipe_combo_hits_defaults_to_1_no_regression() -> void:
	# AC-NF-1: existing MELEE_SWIPE resource has combo_hits=1 (default) and is unaffected
	var r = _make_melee_swipe_resource()
	var combo_hits = r.get("combo_hits")
	if combo_hits != null:
		_assert_eq_int(1, combo_hits, "AC-NF1_melee_swipe_default_combo_hits_1")
	else:
		# Field doesn't exist yet — expected to be RED
		_fail_test("AC-NF1_combo_hits_field_missing", "combo_hits field not yet on AttackResource")
	r.free()


func test_acnf1_melee_swipe_still_fires_single_hit() -> void:
	# AC-NF-1: MELEE_SWIPE dispatch still produces exactly 1 attack_hit
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-NF1_melee_swipe", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	_connect_all_signals(scene["executor"])
	scene["executor"].execute_attack(_make_melee_swipe_resource())
	_assert_eq_int(1, _count_signal("attack_hit"), "AC-NF1_single_hit_for_melee_swipe")
	_assert_eq_int(1, _count_signal("melee_vfx_requested"), "AC-NF1_single_vfx_for_melee_swipe")
	_teardown(scene)


func test_acnf1_melee_swipe_uses_apply_acid_not_stack() -> void:
	# AC-NF-1: MELEE_SWIPE with acid_on_hit uses apply_acid (not apply_acid_stack)
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-NF1_apply_acid", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 3.0,
		"attack_range": 1.5,
		"modifiers": {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	})
	scene["executor"].execute_attack(res)
	_assert_eq_int(1, enemy.acid_calls.size(), "AC-NF1_apply_acid_called_for_melee_swipe")
	_assert_eq_int(0, enemy.acid_stack_calls.size(), "AC-NF1_no_acid_stack_for_melee_swipe")
	_teardown(scene)


# ---------------------------------------------------------------------------
# AC-NF-4: Unknown effect_type fallback still fires (not broken by new case)
# ---------------------------------------------------------------------------

func test_acnf4_unknown_effect_type_still_handled() -> void:
	# AC-NF-4: Adding MELEE_SWIPE_COMBO does not break the fallback for unknown types
	var scene = _build_scene("AC-NF4", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var res = _make_resource({"effect_type": "UNKNOWN_TYPE_XYZ", "damage": 1.0})
	scene["executor"].execute_attack(res)
	_pass_test("AC-NF4_unknown_type_no_crash")
	_assert_false(scene["executor"].is_active(), "AC-NF4_is_active_false_after_unknown")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AcidClawComboAttackTests ===")

	# AC-1: combo_hits field
	test_ac1a_default_combo_hits_is_one()
	test_ac1b_assign_combo_hits_3_roundtrip()
	test_ac1c_assign_combo_hits_0_stores_0()
	test_ac1d_assign_combo_hits_negative_stores_negative()
	test_ac1e_other_fields_unset_combo_hits_defaults_to_1()
	test_ac1f_combo_hits_is_int_float_coerces()

	# AC-2: MELEE_SWIPE_COMBO handler dispatch
	test_ac2a_combo_hits_3_produces_3_attack_hit_signals()
	test_ac2g_attack_started_emitted_once_not_per_hit()
	test_ac2f_melee_vfx_emitted_once_per_hit()
	test_ac2h_combo_hits_0_fires_no_attack_hit()
	test_ac2i_combo_hits_1_fires_exactly_one_hit()
	test_ac2l_is_active_false_after_combo_completes()
	test_ac2k_second_execute_while_active_blocked()
	test_ac2d_each_hit_calls_apply_acid_stack_not_apply_acid()
	test_ac2e_knockback_applied_per_hit()
	test_ac2_damage_per_hit_is_1_8()

	# AC-4: modifier dispatch
	test_ac4a_normal_enemy_acid_stack_gets_correct_params()
	test_ac4b_weakened_enemy_doubles_acid_duration()
	test_ac4c_apply_acid_not_called_in_combo_modifier()
	test_ac4d_missing_apply_acid_stack_method_no_crash()
	test_ac4e_non_acid_modifiers_work_in_combo_path()

	# AC-5: AttackDatabase registration — see test_acid_claw_database_registration.gd

	# AC-6: integration
	test_ac6a_full_combo_3_stacks_on_single_enemy()
	test_ac6b_full_combo_5_4_direct_damage()
	test_ac6c_each_stack_initialized_to_2_5s()

	# Non-regression
	test_acnf1_melee_swipe_combo_hits_defaults_to_1_no_regression()
	test_acnf1_melee_swipe_still_fires_single_hit()
	test_acnf1_melee_swipe_uses_apply_acid_not_stack()
	test_acnf4_unknown_effect_type_still_handled()

	print("AcidClawComboAttackTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
