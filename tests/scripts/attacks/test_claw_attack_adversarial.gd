#
# test_claw_attack_adversarial.gd
#
# Adversarial edge-case, boundary, and mutation tests for the claw attack.
# Extends the primary test_claw_attack.gd suite with weaknesses, blind spots,
# and gaps the primary coverage misses.
#
# Spec: project_board/specs/claw_player_attack_spec.md (CPA-1..CPA-7, EC-1..EC-18)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/08_claw_player_attack.md
#
# Tests marked EXPECTED FAIL will fail until claw implementation is complete.
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Mock inner classes
# ---------------------------------------------------------------------------

class MockEnemy extends Node3D:
	var damage_taken: Array = []
	var current_state: int = 0
	var is_dead_flag: bool = false
	var slow_calls: Array = []

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag

	func apply_slowness(multiplier: float, duration: float) -> void:
		slow_calls.append({"multiplier": multiplier, "duration": duration})


class DyingEnemy extends Node3D:
	## Faithfully models a WEAKENED enemy with low HP that dies from claw damage.
	## Exposes the gap where _apply_modifiers may infect a just-killed enemy.
	var damage_taken: Array = []
	var current_state: int = 1
	var is_dead_flag: bool = false
	var current_hp: float = 2.0

	func take_damage(damage: float, knockback: Vector3) -> void:
		if is_dead_flag:
			return
		damage_taken.append({"damage": damage, "knockback": knockback})
		current_hp = maxf(0.0, current_hp - damage)
		if current_hp <= 0.0:
			is_dead_flag = true

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag


class WeakeningEnemy extends Node3D:
	var damage_taken: Array = []
	var current_state: int = 0
	var is_dead_flag: bool = false
	var max_hp: float = 10.0
	var current_hp: float = 10.0

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})
		current_hp = maxf(0.0, current_hp - damage)
		if current_state == 0 and current_hp <= max_hp * 0.5:
			current_state = 1

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag


class BareTarget extends Node3D:
	pass


class SilentParent extends Node3D:
	## Parent without get_facing_sign — tests fallback to facing=1.0.
	pass


class MockParent extends Node3D:
	var _facing: float = 1.0
	func get_facing_sign() -> float:
		return _facing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_claw_resource() -> AttackResource:
	var r = AttackResource.new()
	r.attack_id = 1
	r.attack_name = "Claw Swipe"
	r.description = "Fast melee swipe with short cooldown. Infects weakened enemies."
	r.effect_type = "MELEE_SWIPE"
	r.damage = 3.0
	r.cooldown = 0.8
	r.attack_range = 1.5
	r.startup_frames = 0
	r.knockback_magnitude = 2.0
	r.knockback_direction = "away"
	r.projectile_speed = 0.0
	r.projectile_lifetime = 2.0
	r.color = Color.ORANGE_RED
	r.vfx_scale = 1.2
	r.modifiers = {"infect_weakened": true}
	return r


func _make_resource(overrides: Dictionary = {}) -> AttackResource:
	var r = AttackResource.new()
	r.startup_frames = 0
	for key in overrides:
		r.set(key, overrides[key])
	return r


func _build_scene(label: String, enemies: Array = [], pos: Vector3 = Vector3.ZERO, facing: float = 1.0) -> Dictionary:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test(label, "executor not loadable")
		return {}
	var scene_root = Node3D.new()
	var parent = MockParent.new()
	parent._facing = facing
	scene_root.add_child(parent)
	parent.add_child(executor)
	parent.global_position = pos
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)
	for e in enemies:
		scene_root.add_child(e)
		if e.is_inside_tree():
			e.add_to_group("enemies")
	return {"root": scene_root, "parent": parent, "executor": executor}


func _build_scene_silent_parent(label: String, enemies: Array = []) -> Dictionary:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test(label, "executor not loadable")
		return {}
	var scene_root = Node3D.new()
	var parent = SilentParent.new()
	scene_root.add_child(parent)
	parent.add_child(executor)
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)
	for e in enemies:
		scene_root.add_child(e)
		if e.is_inside_tree():
			e.add_to_group("enemies")
	return {"root": scene_root, "parent": parent, "executor": executor}


func _teardown(scene: Dictionary) -> void:
	var root = scene.get("root")
	if root != null and is_instance_valid(root):
		(root as Node).free()


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
# Boundary: Range (hitbox center=0.75, radius=0.75 for claw at origin facing right)
# ---------------------------------------------------------------------------

func test_adv_range_exact_boundary_hit() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.5, 0.0, 0.0)
	var scene = _build_scene("ADV_range_exact", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, enemy.damage_taken.size(), "ADV_range_exact_hit")
	_teardown(scene)


func test_adv_range_just_outside_miss() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.501, 0.0, 0.0)
	var scene = _build_scene("ADV_range_outside", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(0, enemy.damage_taken.size(), "ADV_range_outside_miss")
	_teardown(scene)


func test_adv_range_just_inside_hit() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.499, 0.0, 0.0)
	var scene = _build_scene("ADV_range_inside", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, enemy.damage_taken.size(), "ADV_range_inside_hit")
	_teardown(scene)


func test_adv_zero_range_no_hit() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.01, 0.0, 0.0)
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "damage": 3.0, "attack_range": 0.0})
	var scene = _build_scene("ADV_zero_range", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(res)
	_assert_eq_int(0, enemy.damage_taken.size(), "ADV_zero_range_miss")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Boundary: Damage
# ---------------------------------------------------------------------------

func test_adv_damage_zero_no_weaken() -> void:
	var enemy = WeakeningEnemy.new()
	enemy.max_hp = 10.0
	enemy.current_hp = 6.0
	enemy.current_state = 0
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "damage": 0.0, "attack_range": 1.5})
	var scene = _build_scene("ADV_zero_dmg", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(res)
	_assert_eq_int(0, enemy.current_state, "ADV_zero_dmg_still_normal")
	_assert_eq_int(1, enemy.damage_taken.size(), "ADV_zero_dmg_called")
	_teardown(scene)


func test_adv_zero_damage_weakened_still_infects() -> void:
	## EXPECTED FAIL until infect_weakened modifier is implemented.
	## Damage and modifiers are independent: 0 damage on a WEAKENED enemy
	## should still trigger the infect_weakened modifier.
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var res = _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 0.0, "attack_range": 1.5,
		"modifiers": {"infect_weakened": true}
	})
	var scene = _build_scene("ADV_zero_dmg_infect", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(res)
	_assert_eq_int(2, enemy.current_state, "ADV_zero_dmg_infected")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Null & Empty: Registration edge cases
# ---------------------------------------------------------------------------

func test_adv_infect_weakened_false_explicit() -> void:
	## Explicit false must NOT trigger infection, even though the key exists.
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var res = _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 3.0, "attack_range": 1.5,
		"modifiers": {"infect_weakened": false}
	})
	var scene = _build_scene("ADV_false_key", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(res)
	_assert_eq_int(1, enemy.current_state, "ADV_false_key_no_infect")
	_teardown(scene)


func test_adv_empty_mutation_id_rejected() -> void:
	var db = AttackDatabaseNode.new()
	var r = _make_claw_resource()
	db.register_base_attack("", r)
	_assert_false(db.has_base_attack(""), "ADV_empty_id_rejected")
	_assert_eq_int(0, db.get_base_attack_count(), "ADV_empty_id_count_zero")
	db.free()


func test_adv_null_resource_registration_rejected() -> void:
	var db = AttackDatabaseNode.new()
	db.register_base_attack("claw", null)
	_assert_false(db.has_base_attack("claw"), "ADV_null_res_rejected")
	db.free()


# ---------------------------------------------------------------------------
# State machine edge cases
# ---------------------------------------------------------------------------

func test_adv_state_beyond_enum_no_crash() -> void:
	## Enemy with state value outside the State enum (e.g. 99).
	## Modifier must not crash; should not transition.
	## EXPECTED FAIL until infect_weakened modifier is implemented (partial).
	var enemy = MockEnemy.new()
	enemy.current_state = 99
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("ADV_state_99", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(99, enemy.current_state, "ADV_state_99_unchanged")
	_pass_test("ADV_state_99_no_crash")
	_teardown(scene)


func test_adv_weakened_killed_by_damage_no_infect() -> void:
	# CHECKPOINT: Spec CPA-3d says dead enemy → no transition.
	# Gap: if claw damage kills a WEAKENED enemy, the infect_weakened modifier
	# runs after _apply_damage. The spec handler doesn't check is_dead(), so
	# the dead enemy may get infected. This test asserts correct behavior:
	# dead enemies must NOT transition to INFECTED.
	# EXPECTED FAIL until implementation guards is_dead() in infect_weakened.
	var enemy = DyingEnemy.new()
	enemy.current_state = 1
	enemy.current_hp = 2.0
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("ADV_kill_infect", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_true(enemy.is_dead_flag, "ADV_kill_confirmed_dead")
	_assert_true(enemy.current_state != 2, "ADV_kill_not_infected")
	_teardown(scene)


func test_adv_normal_killed_by_damage_not_infected() -> void:
	var enemy = DyingEnemy.new()
	enemy.current_state = 0
	enemy.current_hp = 1.0
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("ADV_kill_normal", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_true(enemy.is_dead_flag, "ADV_kill_normal_dead")
	_assert_true(enemy.current_state != 2, "ADV_kill_normal_not_infected")
	_teardown(scene)


func test_adv_weakened_threshold_exact_50_pct() -> void:
	var enemy = WeakeningEnemy.new()
	enemy.max_hp = 10.0
	enemy.current_hp = 8.0
	enemy.current_state = 0
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("ADV_threshold", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, enemy.current_state, "ADV_threshold_exactly_50pct_weakened")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Knockback direction edge cases
# ---------------------------------------------------------------------------

func test_adv_knockback_facing_left() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(-0.5, 0.0, 0.0)
	var scene = _build_scene("ADV_kb_left", [enemy], Vector3.ZERO, -1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.x < 0.0, "ADV_kb_left_negative_x")
	else:
		_fail_test("ADV_kb_left", "no damage recorded")
	_teardown(scene)


func test_adv_knockback_degenerate_same_pos() -> void:
	## Enemy at exact same position as player → degenerate distance fallback
	## should use default direction Vector3(1,0,0) per DEGENERATE_DISTANCE_SQ.
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3.ZERO
	var scene = _build_scene("ADV_kb_degen", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.length() > 0.0, "ADV_kb_degen_nonzero")
		_assert_true(kb.x > 0.0, "ADV_kb_degen_default_positive_x")
	else:
		_fail_test("ADV_kb_degen", "no damage — enemy may be at range boundary")
	_teardown(scene)


func test_adv_knockback_none_direction() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var res = _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 3.0, "attack_range": 1.5,
		"knockback_magnitude": 5.0, "knockback_direction": "none"
	})
	var scene = _build_scene("ADV_kb_none", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(res)
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb == Vector3.ZERO, "ADV_kb_none_zero")
	else:
		_fail_test("ADV_kb_none", "no damage recorded")
	_teardown(scene)


func test_adv_knockback_zero_magnitude() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var res = _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 3.0, "attack_range": 1.5,
		"knockback_magnitude": 0.0, "knockback_direction": "away"
	})
	var scene = _build_scene("ADV_kb_zero_mag", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(res)
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb == Vector3.ZERO, "ADV_kb_zero_mag_zero")
	else:
		_fail_test("ADV_kb_zero_mag", "no damage recorded")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Concurrency / Order
# ---------------------------------------------------------------------------

func test_adv_active_flag_blocks_second() -> void:
	## Manually set _is_active to true, then verify execute_attack is a no-op.
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("ADV_active_block", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	executor.set("_is_active", true)
	_connect_all_signals(executor)
	executor.execute_attack(_make_claw_resource())
	_assert_eq_int(0, enemy.damage_taken.size(), "ADV_active_no_damage")
	_assert_eq_int(0, _count_signal("attack_started"), "ADV_active_no_signal")
	executor.set("_is_active", false)
	_teardown(scene)


func test_adv_rapid_three_sequential() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("ADV_rapid_3", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var claw = _make_claw_resource()
	executor.execute_attack(claw)
	executor.execute_attack(claw)
	executor.execute_attack(claw)
	_assert_eq_int(3, enemy.damage_taken.size(), "ADV_rapid_3_all_hit")
	_assert_false(executor.is_active(), "ADV_rapid_3_not_active")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Multi-enemy
# ---------------------------------------------------------------------------

func test_adv_five_weakened_all_infect() -> void:
	## EXPECTED FAIL until infect_weakened modifier is implemented.
	## All 5 WEAKENED enemies in range must transition to INFECTED.
	var enemies: Array = []
	for i in range(5):
		var e = MockEnemy.new()
		e.current_state = 1
		e.global_position = Vector3(0.2 + i * 0.2, 0.0, 0.0)
		enemies.append(e)
	var scene = _build_scene("ADV_5_weak", enemies, Vector3.ZERO, 1.0)
	if scene.is_empty():
		for e in enemies:
			e.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	for i in range(5):
		_assert_eq_int(2, enemies[i].current_state, "ADV_5_weak_" + str(i) + "_infected")
	_teardown(scene)


func test_adv_mixed_range_partial_hit() -> void:
	var e_in1 = MockEnemy.new()
	e_in1.global_position = Vector3(0.5, 0.0, 0.0)
	var e_in2 = MockEnemy.new()
	e_in2.global_position = Vector3(1.0, 0.0, 0.0)
	var e_out1 = MockEnemy.new()
	e_out1.global_position = Vector3(5.0, 0.0, 0.0)
	var e_out2 = MockEnemy.new()
	e_out2.global_position = Vector3(-3.0, 0.0, 0.0)
	var scene = _build_scene("ADV_mixed", [e_in1, e_in2, e_out1, e_out2], Vector3.ZERO, 1.0)
	if scene.is_empty():
		for e in [e_in1, e_in2, e_out1, e_out2]:
			e.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, e_in1.damage_taken.size(), "ADV_mixed_in1_hit")
	_assert_eq_int(1, e_in2.damage_taken.size(), "ADV_mixed_in2_hit")
	_assert_eq_int(0, e_out1.damage_taken.size(), "ADV_mixed_out1_miss")
	_assert_eq_int(0, e_out2.damage_taken.size(), "ADV_mixed_out2_miss")
	_teardown(scene)


func test_adv_enemy_behind_player_miss() -> void:
	## Enemy at negative X when player faces right. Hitbox center is at +0.75
	## with radius 0.75, so enemies at X < 0 are >0.75 from center → miss.
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(-1.0, 0.0, 0.0)
	var scene = _build_scene("ADV_behind", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(0, enemy.damage_taken.size(), "ADV_behind_miss")
	_teardown(scene)


func test_adv_attack_hit_signal_count_matches() -> void:
	var e1 = MockEnemy.new()
	e1.global_position = Vector3(0.3, 0.0, 0.0)
	var e2 = MockEnemy.new()
	e2.global_position = Vector3(0.6, 0.0, 0.0)
	var e3 = MockEnemy.new()
	e3.global_position = Vector3(0.9, 0.0, 0.0)
	var scene = _build_scene("ADV_hit_count", [e1, e2, e3], Vector3.ZERO, 1.0)
	if scene.is_empty():
		for e in [e1, e2, e3]:
			e.free()
		return
	_connect_all_signals(scene["executor"])
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(3, _count_signal("attack_hit"), "ADV_hit_count_3")
	_assert_eq_int(1, _count_signal("attack_started"), "ADV_started_once")
	_teardown(scene)


func test_adv_vfx_emitted_once_multi_enemies() -> void:
	var enemies: Array = []
	for i in range(4):
		var e = MockEnemy.new()
		e.global_position = Vector3(0.2 + i * 0.2, 0.0, 0.0)
		enemies.append(e)
	var scene = _build_scene("ADV_vfx_multi", enemies, Vector3.ZERO, 1.0)
	if scene.is_empty():
		for e in enemies:
			e.free()
		return
	_connect_all_signals(scene["executor"])
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, _count_signal("melee_vfx_requested"), "ADV_vfx_once")
	_assert_eq_int(4, _count_signal("attack_hit"), "ADV_vfx_4_hits")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Isolation / Cross-cutting
# ---------------------------------------------------------------------------

func test_adv_modifier_slow_and_infect_coexist() -> void:
	## EXPECTED FAIL until infect_weakened modifier is implemented.
	## Both slow and infect_weakened must fire independently.
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var res = _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 3.0, "attack_range": 1.5,
		"modifiers": {"infect_weakened": true, "slow": 0.5, "slow_duration": 2.0}
	})
	var scene = _build_scene("ADV_slow_infect", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(res)
	_assert_eq_int(2, enemy.current_state, "ADV_slow_infect_infected")
	_assert_eq_int(1, enemy.slow_calls.size(), "ADV_slow_infect_slowed")
	_teardown(scene)


func test_adv_silent_parent_facing_fallback() -> void:
	## Executor parent without get_facing_sign falls back to facing=1.0.
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene_silent_parent("ADV_silent", [enemy])
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, enemy.damage_taken.size(), "ADV_silent_still_hits")
	_teardown(scene)


func test_adv_double_registration_last_wins() -> void:
	var db = AttackDatabaseNode.new()
	var r1 = _make_resource({"damage": 5.0})
	var r2 = _make_resource({"damage": 99.0})
	db.register_base_attack("claw", r1)
	db.register_base_attack("claw", r2)
	_assert_eq_float(99.0, db.get_base_attack("claw").damage, "ADV_double_reg_last_wins")
	_assert_eq_int(1, db.get_base_attack_count(), "ADV_double_reg_count_1")
	db.free()


func test_adv_cooldown_value_matches_spec() -> void:
	var claw = _make_claw_resource()
	_assert_eq_float(0.8, claw.cooldown, "ADV_cd_0_8")
	_assert_true(claw.cooldown < 1.0, "ADV_cd_shortest")


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

func test_adv_repeated_identical_result() -> void:
	for trial in range(3):
		var enemy = MockEnemy.new()
		enemy.current_state = 1
		enemy.global_position = Vector3(0.5, 0.0, 0.0)
		var scene = _build_scene("ADV_determ_" + str(trial), [enemy], Vector3.ZERO, 1.0)
		if scene.is_empty():
			enemy.free()
			continue
		scene["executor"].execute_attack(_make_claw_resource())
		_assert_eq_int(1, enemy.damage_taken.size(), "ADV_determ_dmg_" + str(trial))
		_assert_eq_float(3.0, enemy.damage_taken[0]["damage"], "ADV_determ_val_" + str(trial))
		_teardown(scene)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== ClawAttackAdversarialTests ===")

	test_adv_range_exact_boundary_hit()
	test_adv_range_just_outside_miss()
	test_adv_range_just_inside_hit()
	test_adv_zero_range_no_hit()

	test_adv_damage_zero_no_weaken()
	test_adv_zero_damage_weakened_still_infects()

	test_adv_infect_weakened_false_explicit()
	test_adv_empty_mutation_id_rejected()
	test_adv_null_resource_registration_rejected()

	test_adv_state_beyond_enum_no_crash()
	test_adv_weakened_killed_by_damage_no_infect()
	test_adv_normal_killed_by_damage_not_infected()
	test_adv_weakened_threshold_exact_50_pct()

	test_adv_knockback_facing_left()
	test_adv_knockback_degenerate_same_pos()
	test_adv_knockback_none_direction()
	test_adv_knockback_zero_magnitude()

	test_adv_active_flag_blocks_second()
	test_adv_rapid_three_sequential()

	test_adv_five_weakened_all_infect()
	test_adv_mixed_range_partial_hit()
	test_adv_enemy_behind_player_miss()
	test_adv_attack_hit_signal_count_matches()
	test_adv_vfx_emitted_once_multi_enemies()

	test_adv_modifier_slow_and_infect_coexist()
	test_adv_silent_parent_facing_fallback()
	test_adv_double_registration_last_wins()
	test_adv_cooldown_value_matches_spec()

	test_adv_repeated_identical_result()

	print("ClawAttackAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
