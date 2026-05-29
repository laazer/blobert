#
# test_acid_claw_combo_adversarial.gd
#
# Adversarial and edge-case tests for the Acid + Claw fusion attack.
# Covers failure modes, mid-combo edge cases, boundary conditions, and
# scenarios from AC-EC-1 through AC-EC-10.
#
# Spec: project_board/specs/acid_claw_fusion_attack_spec.md
# Ticket: project_board/12_milestone_12_fused_mutation_attacks/in_progress/04_acid_claw_fusion_attack.md
# Traceability: AC-EC-1 through AC-EC-10, Failure modes 1-4, AC-2h, AC-2j, AC-2k
#
# NOTE: These tests will be RED until implementation of:
#   - MELEE_SWIPE_COMBO case in AttackExecutor.execute_attack()
#   - _handle_melee_swipe_combo() with null-tree guard
#   - _apply_combo_modifiers() with has_method guard
#   - EnemyBase.apply_acid_stack() with _is_dead guard
#

class_name AcidClawComboAdversarialTests
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
	# Enemy WITHOUT apply_acid_stack — tests has_method guard (Failure 4)
	var damage_taken: Array = []
	var current_state: int = 0

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

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
# Failure 1: combo_hits <= 0 — no hits, no crash (AC-2h extended)
# ---------------------------------------------------------------------------

func test_fail1_combo_hits_zero_no_attack_hit_no_crash() -> void:
	# Failure 1: combo_hits=0 → silent no-op, no attack_hit, _is_active resets
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("FAIL1_zero", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.execute_attack(_make_combo_resource(0))
	_assert_eq_int(0, _count_signal("attack_hit"), "FAIL1_no_hit_for_0_combo")
	_assert_false(executor.is_active(), "FAIL1_is_active_false")
	_assert_eq_int(0, enemy.acid_stack_calls.size(), "FAIL1_no_acid_stack_applied")
	_teardown(scene)


func test_fail1_combo_hits_negative_no_hits() -> void:
	# AC-2h extended: combo_hits = -1 → no hits, no crash
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("FAIL1_neg", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.execute_attack(_make_combo_resource(-1))
	_assert_eq_int(0, _count_signal("attack_hit"), "FAIL1_no_hit_for_neg1_combo")
	_assert_false(executor.is_active(), "FAIL1_neg_is_active_false")
	_assert_eq_int(0, enemy.damage_taken.size(), "FAIL1_no_damage_for_neg1")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Failure 4: Missing apply_acid_stack — no crash, damage still applied
# ---------------------------------------------------------------------------

func test_fail4_no_apply_acid_stack_method_no_crash_damage_applies() -> void:
	# Failure 4: target without apply_acid_stack → no crash, damage and knockback still apply
	var enemy = NoAcidStackEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("FAIL4", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.execute_attack(_make_combo_resource(3))
	_pass_test("FAIL4_no_crash_without_apply_acid_stack")
	_assert_eq_int(3, enemy.damage_taken.size(), "FAIL4_damage_still_applied_3_times")
	_assert_false(executor.is_active(), "FAIL4_is_active_false_after_combo")
	_teardown(scene)


# ---------------------------------------------------------------------------
# AC-EC-2: Enemy killed by hit 1 — no post-death stacks or damage
# ---------------------------------------------------------------------------

func test_acec2_enemy_killed_by_hit1_no_further_stacks() -> void:
	# AC-EC-2: enemy dies at hit 1 → hits 2/3 skipped via _is_dead guard
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-EC-2", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	# Kill the enemy before the attack lands — simulates enemy already dead
	enemy.is_dead_flag = true
	scene["executor"].execute_attack(_make_combo_resource(3))
	_assert_eq_int(0, enemy.damage_taken.size(), "AC-EC-2_no_damage_on_dead")
	_assert_eq_int(0, enemy.acid_stack_calls.size(), "AC-EC-2_no_stacks_on_dead")
	_teardown(scene)


func test_acec2_acid_stack_not_applied_to_dead_enemy() -> void:
	# AC-6f / Failure 2: apply_acid_stack on dead enemy → no-op
	# (Executor-level test via combo path with pre-dead enemy)
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	enemy.is_dead_flag = true
	var scene = _build_scene("AC-6f_via_executor", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_combo_resource(3))
	_assert_eq_int(0, enemy.get_acid_stack_count(), "AC-6f_0_stacks_on_pre_dead")
	_teardown(scene)


# ---------------------------------------------------------------------------
# AC-EC-3: Non-stacking acid coexists with acid_stack_* entries
# ---------------------------------------------------------------------------

func test_acec3_base_acid_key_does_not_interfere_with_stack_count() -> void:
	# AC-EC-3: apply_acid() (base key "acid") does NOT affect get_acid_stack_count()
	# This is tested in isolation via EnemyEffectTracker in the stacking test file.
	# Here we verify the combo path does not call apply_acid on a combo resource.
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-EC-3", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_combo_resource(3))
	_assert_eq_int(0, enemy.acid_calls.size(), "AC-EC-3_no_base_apply_acid_from_combo")
	_assert_eq_int(3, enemy.acid_stack_calls.size(), "AC-EC-3_3_stack_calls")
	_teardown(scene)


# ---------------------------------------------------------------------------
# AC-EC-4: Three hits on WEAKENED enemy → each stack gets doubled duration
# ---------------------------------------------------------------------------

func test_acec4_weakened_check_per_hit_not_once_at_combo_start() -> void:
	# AC-EC-4: WEAKENED check per hit → 3 stacks each at 5.0s (not 2.5s)
	var enemy = WeakenedEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-EC-4", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_combo_resource(3))
	_assert_eq_int(3, enemy.acid_stack_calls.size(), "AC-EC-4_3_stacks_on_weakened")
	for i in range(enemy.acid_stack_calls.size()):
		_assert_eq_float(5.0, enemy.acid_stack_calls[i]["duration"],
			"AC-EC-4_duration_doubled_to_5_hit_" + str(i))
	_teardown(scene)


# ---------------------------------------------------------------------------
# AC-EC-5: combo_hits=1 (degenerate valid case)
# ---------------------------------------------------------------------------

func test_acec5_combo_hits_1_single_hit_acid_stack_path() -> void:
	# AC-EC-5: combo_hits=1 fires exactly 1 hit with stacking acid (not base acid)
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-EC-5", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.execute_attack(_make_combo_resource(1))
	_assert_eq_int(1, _count_signal("attack_hit"), "AC-EC-5_1_hit")
	_assert_eq_int(1, enemy.acid_stack_calls.size(), "AC-EC-5_1_stack_applied")
	_assert_eq_int(0, enemy.acid_calls.size(), "AC-EC-5_no_base_acid")
	_assert_eq_int(1, enemy.damage_taken.size(), "AC-EC-5_1_damage_hit")
	_teardown(scene)


# ---------------------------------------------------------------------------
# AC-EC-6: _is_active guard — rapid re-fire attempt mid-combo blocked
# ---------------------------------------------------------------------------

func test_acec6_rapid_refire_blocked_while_active() -> void:
	# AC-EC-6: A second execute_attack while _is_active == true is silently ignored
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("AC-EC-6", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	# Force active to simulate mid-combo state
	executor._is_active = true
	executor.execute_attack(_make_combo_resource(3))
	_assert_eq_int(0, _count_signal("attack_started"), "AC-EC-6_no_started_when_active")
	_assert_eq_int(0, _count_signal("attack_hit"), "AC-EC-6_no_hit_when_active")
	_teardown(scene)


# ---------------------------------------------------------------------------
# AC-EC-9: add_acid_stack with duration=0.0 — counter must NOT increment
# ---------------------------------------------------------------------------

func test_acec9_zero_duration_acid_stack_not_stored() -> void:
	# AC-EC-9: duration=0.0 → stack not stored, counter not incremented
	# Tested at the EnemyEffectTracker level directly
	var tracker_script: GDScript = load("res://scripts/enemies/enemy_effect_tracker.gd")
	if tracker_script == null:
		_fail_test("AC-EC-9", "enemy_effect_tracker.gd not loadable")
		return
	var tracker = tracker_script.new()
	if not tracker.has_method("add_acid_stack"):
		_fail_test("AC-EC-9", "add_acid_stack not yet implemented")
		tracker.free()
		return
	# Call add_acid_stack with zero duration
	tracker.add_acid_stack(0.0, 0.4)
	if not tracker.has_method("get_acid_stack_count"):
		_fail_test("AC-EC-9", "get_acid_stack_count not yet implemented")
		tracker.free()
		return
	_assert_eq_int(0, tracker.get_acid_stack_count(), "AC-EC-9_zero_dur_not_stored")
	# Verify counter did NOT increment — next valid add should use key "acid_stack_0"
	tracker.add_acid_stack(2.5, 0.4)
	_assert_eq_int(1, tracker.get_acid_stack_count(), "AC-EC-9_valid_add_after_zero_uses_stack_0")
	tracker.free()


# ---------------------------------------------------------------------------
# AC-EC-10: No enemies in range — whiff: no stacks, no damage, VFX still fires
# ---------------------------------------------------------------------------

func test_acec10_whiff_no_stacks_no_damage_vfx_fires() -> void:
	# AC-EC-10: 0 enemies in range → 3 empty hit loops, no stacks, no damage, 3 VFX
	var scene = _build_scene("AC-EC-10", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.execute_attack(_make_combo_resource(3))
	_assert_eq_int(0, _count_signal("attack_hit"), "AC-EC-10_no_hits_whiff")
	_assert_eq_int(3, _count_signal("melee_vfx_requested"), "AC-EC-10_3_vfx_on_whiff")
	_assert_eq_int(1, _count_signal("attack_started"), "AC-EC-10_started_emitted")
	_teardown(scene)


# ---------------------------------------------------------------------------
# MELEE_SWIPE path not confused with MELEE_SWIPE_COMBO (effect type separation)
# ---------------------------------------------------------------------------

func test_melee_swipe_routing_unaffected_by_new_case() -> void:
	# MELEE_SWIPE must continue to route to _handle_melee_swipe (not combo)
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("ROUTE_SEP", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 3.0,
		"attack_range": 1.5,
		"knockback_magnitude": 2.0,
		"knockback_direction": "away"
	})
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.execute_attack(res)
	# Single swipe: 1 attack_hit, 1 VFX, no stacks
	_assert_eq_int(1, _count_signal("attack_hit"), "ROUTE_SEP_1_hit_for_melee_swipe")
	_assert_eq_int(1, _count_signal("melee_vfx_requested"), "ROUTE_SEP_1_vfx_for_melee_swipe")
	_assert_eq_int(0, enemy.acid_stack_calls.size(), "ROUTE_SEP_no_acid_stack_for_melee_swipe")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Boundary: Large combo_hits value — no crash
# ---------------------------------------------------------------------------

func test_large_combo_hits_no_crash() -> void:
	# Boundary: combo_hits = 10 executes 10 loops without crash (no enemies in range)
	var scene = _build_scene("LARGE_COMBO", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.execute_attack(_make_combo_resource(10))
	_pass_test("LARGE_COMBO_no_crash")
	_assert_eq_int(10, _count_signal("melee_vfx_requested"), "LARGE_COMBO_10_vfx_for_10_hits")
	_assert_eq_int(0, _count_signal("attack_hit"), "LARGE_COMBO_no_hit_no_enemies")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Full combo with two enemies — both receive 3 stacks each
# ---------------------------------------------------------------------------

func test_two_enemies_each_get_3_stacks() -> void:
	# AC-EC-8: Multiple enemies in range each receive all combo hits
	var e1 = MockEnemy.new()
	e1.global_position = Vector3(0.4, 0.0, 0.0)
	var e2 = MockEnemy.new()
	e2.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("TWO_ENEMIES", [e1, e2], Vector3.ZERO, 1.0)
	if scene.is_empty():
		e1.free()
		e2.free()
		return
	scene["executor"].execute_attack(_make_combo_resource(3))
	_assert_eq_int(3, e1.get_acid_stack_count(), "TWO_ENEMIES_e1_3_stacks")
	_assert_eq_int(3, e2.get_acid_stack_count(), "TWO_ENEMIES_e2_3_stacks")
	_assert_eq_int(3, e1.damage_taken.size(), "TWO_ENEMIES_e1_3_hits")
	_assert_eq_int(3, e2.damage_taken.size(), "TWO_ENEMIES_e2_3_hits")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AcidClawComboAdversarialTests ===")

	# Failure modes
	test_fail1_combo_hits_zero_no_attack_hit_no_crash()
	test_fail1_combo_hits_negative_no_hits()
	test_fail4_no_apply_acid_stack_method_no_crash_damage_applies()

	# Edge cases
	test_acec2_enemy_killed_by_hit1_no_further_stacks()
	test_acec2_acid_stack_not_applied_to_dead_enemy()
	test_acec3_base_acid_key_does_not_interfere_with_stack_count()
	test_acec4_weakened_check_per_hit_not_once_at_combo_start()
	test_acec5_combo_hits_1_single_hit_acid_stack_path()
	test_acec6_rapid_refire_blocked_while_active()
	test_acec9_zero_duration_acid_stack_not_stored()
	test_acec10_whiff_no_stacks_no_damage_vfx_fires()

	# Routing separation
	test_melee_swipe_routing_unaffected_by_new_case()

	# Boundary
	test_large_combo_hits_no_crash()
	test_two_enemies_each_get_3_stacks()

	print("AcidClawComboAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
