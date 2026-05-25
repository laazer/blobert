#
# test_verify_damage_knockback_adversarial_b.gd
#
# Adversarial edge-case tests (part B): executor parent/scene edge cases,
# mutation testing, combinatorial/stress tests, and determinism checks.
# Split from test_verify_damage_knockback_adversarial.gd for the 900-line limit.
#
# Spec: project_board/specs/verify_damage_knockback_spec.md (VDK-1..VDK-5, EC-1..EC-8)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/13_verify_damage_knockback.md
#

class_name VerifyDamageKnockbackAdversarialTestsB
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Mock inner classes
# ---------------------------------------------------------------------------

class MockEnemy extends Node3D:
	var damage_taken: Array = []
	var poison_calls: Array = []
	var acid_calls: Array = []
	var slow_calls: Array = []

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

	func apply_poison(duration: float, dps: float) -> void:
		poison_calls.append({"duration": duration, "dps": dps})

	func apply_acid(duration: float, dps: float) -> void:
		acid_calls.append({"duration": duration, "dps": dps})

	func apply_slowness(multiplier: float, duration: float) -> void:
		slow_calls.append({"multiplier": multiplier, "duration": duration})


class BareTarget extends Node3D:
	pass


class MockParent extends Node3D:
	var _facing: float = 1.0

	func get_facing_sign() -> float:
		return _facing


class ParentNoFacing extends Node3D:
	pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_resource(overrides: Dictionary = {}) -> AttackResource:
	var r := AttackResource.new()
	r.startup_frames = 0
	for key in overrides:
		r.set(key, overrides[key])
	return r


func _build_scene(
	test_label: String,
	enemies: Array = [],
	parent_pos: Vector3 = Vector3.ZERO,
	facing: float = 1.0
) -> Dictionary:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test(test_label, "executor not loadable")
		return {}

	var scene_root := Node3D.new()
	var parent := MockParent.new()
	parent._facing = facing
	scene_root.add_child(parent)
	parent.add_child(executor)
	parent.global_position = parent_pos

	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)

	for e in enemies:
		scene_root.add_child(e)
		if e.is_inside_tree():
			e.add_to_group("enemies")

	return {"root": scene_root, "parent": parent, "executor": executor}


func _build_scene_no_facing(test_label: String) -> Dictionary:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test(test_label, "executor not loadable")
		return {}
	var scene_root := Node3D.new()
	var parent := ParentNoFacing.new()
	scene_root.add_child(parent)
	parent.add_child(executor)
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)
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
	executor.connect("projectile_fired", func(p, r): _signals_log.append({"name": "projectile_fired", "projectile": p, "resource": r}))
	executor.connect("melee_vfx_requested", func(pos, col, sc): _signals_log.append({"name": "melee_vfx_requested", "position": pos, "color": col, "scale": sc}))


func _count_signal(signal_name: String) -> int:
	var count := 0
	for entry in _signals_log:
		if entry["name"] == signal_name:
			count += 1
	return count


func _make_projectile_root(proj: Node) -> Node3D:
	var root := Node3D.new()
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(root)
	root.add_child(proj)
	return root


func _free_root(root: Node) -> void:
	if root != null and is_instance_valid(root):
		root.free()


# ---------------------------------------------------------------------------
# ADV-EX: Executor Parent/Scene Edge Cases
# ---------------------------------------------------------------------------

func test_adv_ex01_parent_no_facing_method() -> void:
	var scene := _build_scene_no_facing("ADV-EX01")
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	var root = scene["root"]
	root.add_child(enemy)
	if enemy.is_inside_tree():
		enemy.add_to_group("enemies")
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 8.0,
		"knockback_magnitude": 5.0, "knockback_direction": "away"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "ADV-EX01_hit")
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.x > 0.0, "ADV-EX01_default_facing_right")
	_teardown(scene)


func test_adv_ex02_projectile_spit_no_grandparent() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV-EX02", "executor not loadable")
		return
	var parent := MockParent.new()
	parent.add_child(executor)
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(parent)
	_signals_log = []
	executor.connect("projectile_fired", func(p, r): _signals_log.append({"name": "projectile_fired", "projectile": p, "resource": r}))
	var res := _make_resource({
		"effect_type": "PROJECTILE_SPIT", "damage": 1.0,
		"projectile_speed": 100.0
	})
	executor.execute_attack(res)
	_assert_eq_int(1, _count_signal("projectile_fired"), "ADV-EX02_signal_still_emitted")
	_assert_false(executor.is_active(), "ADV-EX02_inactive_after")
	parent.free()


# ---------------------------------------------------------------------------
# ADV-MT: Mutation Testing — Flipped Conditions / Removed Guards
# ---------------------------------------------------------------------------

func test_adv_mt01_zero_damage_still_calls_take_damage() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(2.0, 0.0, 0.0)
	var scene := _build_scene("ADV-MT01", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 0.0, "attack_range": 8.0,
		"knockback_magnitude": 5.0, "knockback_direction": "away"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "ADV-MT01_take_damage_called_with_zero")
	if enemy.damage_taken.size() > 0:
		_assert_eq_float(0.0, enemy.damage_taken[0]["damage"], "ADV-MT01_zero_damage_value")
	_teardown(scene)


func test_adv_mt02_negative_damage_delivered() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = -5.0
	proj.knockback_magnitude = 0.0
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(2.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.damage_taken.size(), "ADV-MT02_hit")
	if enemy.damage_taken.size() > 0:
		_assert_eq_float(-5.0, enemy.damage_taken[0]["damage"], "ADV-MT02_negative_damage_delivered")
	_free_root(root)


func test_adv_mt03_zero_magnitude_away_gives_zero() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(3.0, 0.0, 0.0)
	var scene := _build_scene("ADV-MT03", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 8.0,
		"knockback_magnitude": 0.0, "knockback_direction": "away"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "ADV-MT03_hit")
	if enemy.damage_taken.size() > 0:
		_assert_vec3_near(enemy.damage_taken[0]["knockback"], Vector3.ZERO, 0.001, "ADV-MT03_zero_mag_zero_kb")
	_teardown(scene)


func test_adv_mt04_nonzero_magnitude_none_direction_gives_zero() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(3.0, 0.0, 0.0)
	var scene := _build_scene("ADV-MT04", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 8.0,
		"knockback_magnitude": 999.0, "knockback_direction": "none"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "ADV-MT04_hit")
	if enemy.damage_taken.size() > 0:
		_assert_vec3_near(enemy.damage_taken[0]["knockback"], Vector3.ZERO, 0.001, "ADV-MT04_none_dir_zero_kb")
	_teardown(scene)


func test_adv_mt05_melee_bare_target_no_crash() -> void:
	var bare := BareTarget.new()
	bare.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("ADV-MT05", [bare], Vector3.ZERO, 1.0)
	if scene.is_empty():
		bare.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 10.0, "attack_range": 8.0,
	})
	executor.execute_attack(res)
	_assert_false(executor.is_active(), "ADV-MT05_inactive")
	_assert_eq_int(1, _count_signal("melee_vfx_requested"), "ADV-MT05_vfx_still_emitted")
	_pass_test("ADV-MT05_no_crash_on_bare_target")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-CM: Combinatorial / Stress Tests
# ---------------------------------------------------------------------------

func test_adv_cm01_all_modifiers_all_defaults() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"poison": true, "acid_on_hit": true, "slow": 0.4}
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.poison_calls.size(), "ADV-CM01_poison")
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV-CM01_acid")
	_assert_eq_int(1, enemy.slow_calls.size(), "ADV-CM01_slow")
	if enemy.poison_calls.size() > 0:
		_assert_eq_float(2.0, enemy.poison_calls[0]["duration"], "ADV-CM01_poison_default_dur")
		_assert_eq_float(0.3, enemy.poison_calls[0]["dps"], "ADV-CM01_poison_default_dps")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(2.0, enemy.acid_calls[0]["duration"], "ADV-CM01_acid_default_dur")
		_assert_eq_float(0.2, enemy.acid_calls[0]["dps"], "ADV-CM01_acid_default_dps")
	if enemy.slow_calls.size() > 0:
		_assert_eq_float(0.4, enemy.slow_calls[0]["multiplier"], "ADV-CM01_slow_explicit")
		_assert_eq_float(1.5, enemy.slow_calls[0]["duration"], "ADV-CM01_slow_default_dur")
	_free_root(root)


func test_adv_cm02_many_enemies_in_range() -> void:
	var enemies: Array = []
	for i in range(10):
		var e := MockEnemy.new()
		e.global_position = Vector3(float(i) * 0.3 + 0.5, 0.0, 0.0)
		enemies.append(e)
	var scene := _build_scene("ADV-CM02", enemies, Vector3.ZERO, 1.0)
	if scene.is_empty():
		for e in enemies:
			e.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 20.0,
		"knockback_magnitude": 5.0, "knockback_direction": "away"
	})
	executor.execute_attack(res)
	var hit_count := 0
	for e in enemies:
		if e.damage_taken.size() > 0:
			hit_count += 1
	_assert_eq_int(10, hit_count, "ADV-CM02_all_10_hit")
	_teardown(scene)


func test_adv_cm03_sequential_executions() -> void:
	var e1 := MockEnemy.new()
	e1.global_position = Vector3(2.0, 0.0, 0.0)
	var scene := _build_scene("ADV-CM03", [e1], Vector3.ZERO, 1.0)
	if scene.is_empty():
		e1.free()
		return
	var executor = scene["executor"]
	var res1 := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 8.0,
		"knockback_magnitude": 5.0, "knockback_direction": "away"
	})
	var res2 := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 2.0, "attack_range": 8.0,
		"knockback_magnitude": 10.0, "knockback_direction": "toward"
	})
	executor.execute_attack(res1)
	_assert_eq_int(1, e1.damage_taken.size(), "ADV-CM03_first_hit")
	executor.execute_attack(res2)
	_assert_eq_int(2, e1.damage_taken.size(), "ADV-CM03_second_hit")
	if e1.damage_taken.size() >= 2:
		_assert_eq_float(1.0, e1.damage_taken[0]["damage"], "ADV-CM03_first_damage")
		_assert_eq_float(2.0, e1.damage_taken[1]["damage"], "ADV-CM03_second_damage")
		_assert_true(e1.damage_taken[0]["knockback"].x > 0.0, "ADV-CM03_first_away")
		_assert_true(e1.damage_taken[1]["knockback"].x < 0.0, "ADV-CM03_second_toward")
	_teardown(scene)


func test_adv_cm04_modifiers_irrelevant_keys_only() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"unrelated_key": true, "random_value": 42}
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.damage_taken.size(), "ADV-CM04_damage_applied")
	_assert_eq_int(0, enemy.poison_calls.size(), "ADV-CM04_no_poison")
	_assert_eq_int(0, enemy.acid_calls.size(), "ADV-CM04_no_acid")
	_assert_eq_int(0, enemy.slow_calls.size(), "ADV-CM04_no_slow")
	_free_root(root)


func test_adv_cm05_resource_modifier_deep_copy() -> void:
	var original_dict := {"poison": true, "poison_dps": 1.0}
	var res := AttackResource.new()
	res.modifiers = original_dict
	original_dict["poison_dps"] = 999.0
	_assert_eq_float(1.0, res.modifiers.get("poison_dps", 0.0), "ADV-CM05_deep_copy_isolation")


func test_adv_cm06_consumed_blocks_second_valid_target() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 10.0
	proj.knockback_magnitude = 5.0
	proj.knockback_direction = "away"
	proj.modifiers = {"poison": true, "poison_duration": 1.0, "poison_dps": 0.5}
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3.ZERO
	var e1 := MockEnemy.new()
	var e2 := MockEnemy.new()
	root.add_child(e1)
	root.add_child(e2)
	e1.global_position = Vector3(2.0, 0.0, 0.0)
	e2.global_position = Vector3(3.0, 0.0, 0.0)
	proj._on_body_entered(e1)
	proj._on_body_entered(e2)
	_assert_eq_int(1, e1.damage_taken.size(), "ADV-CM06_e1_hit")
	_assert_eq_int(0, e2.damage_taken.size(), "ADV-CM06_e2_blocked")
	_assert_eq_int(1, e1.poison_calls.size(), "ADV-CM06_e1_poison")
	_assert_eq_int(0, e2.poison_calls.size(), "ADV-CM06_e2_no_poison")
	_free_root(root)


# ---------------------------------------------------------------------------
# ADV-DT: Determinism Tests
# ---------------------------------------------------------------------------

func test_adv_dt01_knockback_deterministic() -> void:
	var results: Array = []
	for _i in range(2):
		var enemy := MockEnemy.new()
		enemy.global_position = Vector3(4.0, 1.0, 0.0)
		var scene := _build_scene("ADV-DT01", [enemy], Vector3(1.0, 0.0, 0.0), 1.0)
		if scene.is_empty():
			enemy.free()
			return
		var executor = scene["executor"]
		var res := _make_resource({
			"effect_type": "MELEE_SWIPE", "damage": 3.0, "attack_range": 10.0,
			"knockback_magnitude": 7.5, "knockback_direction": "away"
		})
		executor.execute_attack(res)
		if enemy.damage_taken.size() > 0:
			results.append(enemy.damage_taken[0]["knockback"])
		_teardown(scene)
	_assert_eq_int(2, results.size(), "ADV-DT01_both_hit")
	if results.size() == 2:
		_assert_vec3_near(results[0], results[1], 0.0001, "ADV-DT01_deterministic")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== VerifyDamageKnockbackAdversarialTestsB ===")

	# Executor parent/scene edge cases
	test_adv_ex01_parent_no_facing_method()
	test_adv_ex02_projectile_spit_no_grandparent()

	# Mutation testing
	test_adv_mt01_zero_damage_still_calls_take_damage()
	test_adv_mt02_negative_damage_delivered()
	test_adv_mt03_zero_magnitude_away_gives_zero()
	test_adv_mt04_nonzero_magnitude_none_direction_gives_zero()
	test_adv_mt05_melee_bare_target_no_crash()

	# Combinatorial / stress
	test_adv_cm01_all_modifiers_all_defaults()
	test_adv_cm02_many_enemies_in_range()
	test_adv_cm03_sequential_executions()
	test_adv_cm04_modifiers_irrelevant_keys_only()
	test_adv_cm05_resource_modifier_deep_copy()
	test_adv_cm06_consumed_blocks_second_valid_target()

	# Determinism
	test_adv_dt01_knockback_deterministic()

	print("VerifyDamageKnockbackAdversarialTestsB: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
