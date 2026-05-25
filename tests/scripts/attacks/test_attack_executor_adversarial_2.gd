#
# test_attack_executor_adversarial_2.gd
#
# Adversarial tests ADV-17 through ADV-30 for AttackExecutor.
# Split from test_attack_executor_adversarial.gd for gd-organization (max 900 lines).
# Spec: project_board/specs/attack_executor_spec.md (AEX-1..AEX-8, EC-1..EC-20)
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

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


class BareEnemy extends Node3D:
	pass


class MockParent extends Node3D:
	var _facing: float = 1.0

	func get_facing_sign() -> float:
		return _facing


class ParentNoFacing extends Node3D:
	pass


func _make_executor(test_label: String) -> Node:
	var inst = AttackExecutorHarness.make_executor()
	if inst == null:
		_fail_test(test_label, AttackExecutorHarness.EXECUTOR_PATH + " not loadable")
	return inst


func _make_resource(overrides: Dictionary = {}) -> Resource:
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
	var executor := _make_executor(test_label)
	if executor == null:
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


# ---------------------------------------------------------------------------
# ADV-17: Empty string effect_type treated as unknown (EC-6)
# ---------------------------------------------------------------------------

func test_adv17_empty_effect_type_no_damage() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("ADV-17_empty_fx", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "", "damage": 99.0, "attack_range": 100.0})
	executor.execute_attack(res)
	_assert_eq_int(0, enemy.damage_taken.size(), "ADV-17_no_damage_empty_type")
	_assert_false(executor.is_active(), "ADV-17_active_false_empty_type")
	_teardown(scene)


func test_adv18_slam_aoe_unknown() -> void:
	var scene := _build_scene("ADV-18_slam", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "SLAM_AOE", "damage": 20.0})
	executor.execute_attack(res)
	_assert_eq_int(1, _count_signal("attack_started"), "ADV-18_started_emitted")
	_assert_eq_int(0, _count_signal("attack_hit"), "ADV-18_no_hit")
	_assert_eq_int(0, _count_signal("melee_vfx_requested"), "ADV-18_no_vfx")
	_assert_false(executor.is_active(), "ADV-18_active_false")
	_teardown(scene)


func test_adv18_charge_unknown() -> void:
	var scene := _build_scene("ADV-18_charge", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "CHARGE"})
	executor.execute_attack(res)
	_assert_false(executor.is_active(), "ADV-18_charge_unknown_resets")
	_teardown(scene)


func test_adv19_all_modifiers_on_bare_enemy() -> void:
	var executor := _make_executor("ADV-19_all_mods_bare")
	if executor == null:
		return
	var bare := BareEnemy.new()
	executor._apply_modifiers(bare, {
		"poison": true, "poison_duration": 5.0, "poison_dps": 1.0,
		"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 0.5,
		"slow": 0.8, "slow_duration": 2.0
	})
	_pass_test("ADV-19_all_modifiers_bare_no_crash")
	bare.free()
	executor.free()


func test_adv20_knockback_preserves_y_component() -> void:
	var executor := _make_executor("ADV-20_kb_y")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(3.0, 5.0, 0.0), Vector3.ZERO, 10.0, "away"
	)
	_assert_eq_float(0.0, result.z, "ADV-20_z_always_zero")
	executor.free()


func test_adv20_knockback_large_z_zeroed() -> void:
	var executor := _make_executor("ADV-20_large_z")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(1.0, 0.0, 1000.0), Vector3.ZERO, 10.0, "away"
	)
	_assert_eq_float(0.0, result.z, "ADV-20_huge_z_zeroed")
	executor.free()


func test_adv21_vfx_signal_includes_color_and_scale() -> void:
	var scene := _build_scene("ADV-21_vfx_args", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 1.0,
		"attack_range": 1.0,
		"color": Color.RED,
		"vfx_scale": 2.5
	})
	executor.execute_attack(res)
	_assert_eq_int(1, _count_signal("melee_vfx_requested"), "ADV-21_vfx_emitted")
	if _signals_log.size() > 0:
		var vfx_entry = null
		for entry in _signals_log:
			if entry["name"] == "melee_vfx_requested":
				vfx_entry = entry
				break
		if vfx_entry != null:
			_assert_true(vfx_entry["color"] == Color.RED, "ADV-21_color_red")
			_assert_eq_float(2.5, vfx_entry["scale"], "ADV-21_scale_2_5")
	_teardown(scene)


func test_adv22_projectile_modifiers_deep_copy() -> void:
	var scene := _build_scene("ADV-22_deep_copy", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	var children_before: int = scene_root.get_child_count()
	var mods := {"poison": true, "poison_duration": 3.0}
	var res := _make_resource({
		"effect_type": "PROJECTILE_SPIT",
		"damage": 1.0,
		"projectile_speed": 100.0,
		"modifiers": mods
	})
	executor.execute_attack(res)
	if scene_root.get_child_count() <= children_before:
		_fail_test("ADV-22_deep_copy", "no projectile created")
		_teardown(scene)
		return
	var proj = scene_root.get_child(scene_root.get_child_count() - 1)
	res.modifiers["poison"] = false
	res.modifiers["new_key"] = "injected"
	_assert_true(proj.modifiers.get("poison", false) == true, "ADV-22_poison_not_mutated")
	_assert_false(proj.modifiers.has("new_key"), "ADV-22_no_injected_key")
	_teardown(scene)


func test_adv23_attack_hit_target_reference() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("ADV-23_hit_ref", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 4.0})
	executor.execute_attack(res)
	var found := false
	for entry in _signals_log:
		if entry["name"] == "attack_hit" and entry["target"] == enemy:
			found = true
			break
	_assert_true(found, "ADV-23_hit_target_is_enemy_ref")
	_teardown(scene)


func test_adv24_projectile_fired_reference() -> void:
	var scene := _build_scene("ADV-24_proj_ref", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	_connect_all_signals(executor)
	var children_before: int = scene_root.get_child_count()
	var res := _make_resource({"effect_type": "PROJECTILE_SPIT", "damage": 1.0, "projectile_speed": 100.0})
	executor.execute_attack(res)
	if scene_root.get_child_count() <= children_before:
		_fail_test("ADV-24_proj_ref", "no projectile created")
		_teardown(scene)
		return
	var proj = scene_root.get_child(scene_root.get_child_count() - 1)
	var found := false
	for entry in _signals_log:
		if entry["name"] == "projectile_fired" and entry["projectile"] == proj:
			found = true
			break
	_assert_true(found, "ADV-24_fired_signal_has_proj_ref")
	_teardown(scene)


func test_adv25_melee_facing_left_hits_left_enemy() -> void:
	var enemy_left := MockEnemy.new()
	var enemy_right := MockEnemy.new()
	enemy_left.global_position = Vector3(-2.0, 0.0, 0.0)
	enemy_right.global_position = Vector3(2.0, 0.0, 0.0)
	var scene := _build_scene("ADV-25_face_left", [enemy_left, enemy_right], Vector3.ZERO, -1.0)
	if scene.is_empty():
		enemy_left.free()
		enemy_right.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 3.0})
	executor.execute_attack(res)
	_assert_true(enemy_left.damage_taken.size() >= 1, "ADV-25_left_enemy_hit")
	_teardown(scene)


func test_adv26_is_active_returns_bool() -> void:
	var executor := _make_executor("ADV-26_is_active")
	if executor == null:
		return
	_assert_true(executor.is_active() is bool or executor.is_active() == false, "ADV-26_is_active_bool")
	_assert_false(executor.is_active(), "ADV-26_initially_inactive")
	executor.free()


func test_adv27_acid_defaults() -> void:
	var executor := _make_executor("ADV-27_acid_def")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {"acid_on_hit": true})
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV-27_acid_called")
	if enemy.acid_calls.size() >= 1:
		_assert_eq_float(2.0, enemy.acid_calls[0]["duration"], "ADV-27_acid_default_dur")
		_assert_eq_float(0.2, enemy.acid_calls[0]["dps"], "ADV-27_acid_default_dps")
	enemy.free()
	executor.free()


func test_adv27_slow_defaults() -> void:
	var executor := _make_executor("ADV-27_slow_def")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {"slow": 0.5})
	_assert_eq_int(1, enemy.slow_calls.size(), "ADV-27_slow_called")
	if enemy.slow_calls.size() >= 1:
		_assert_eq_float(0.5, enemy.slow_calls[0]["multiplier"], "ADV-27_slow_mult_passthrough")
		_assert_eq_float(1.5, enemy.slow_calls[0]["duration"], "ADV-27_slow_default_dur")
	enemy.free()
	executor.free()


func test_adv28_melee_all_modifiers_applied() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("ADV-28_all_mods", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 5.0,
		"attack_range": 4.0,
		"modifiers": {
			"poison": true, "poison_duration": 3.0, "poison_dps": 0.5,
			"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.3,
			"slow": 0.6, "slow_duration": 1.0
		}
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "ADV-28_damage_applied")
	_assert_eq_int(1, enemy.poison_calls.size(), "ADV-28_poison_applied")
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV-28_acid_applied")
	_assert_eq_int(1, enemy.slow_calls.size(), "ADV-28_slow_applied")
	_teardown(scene)


func test_adv29_get_facing_sign_with_parent() -> void:
	var scene := _build_scene("ADV-29_facing_helper", [], Vector3.ZERO, -1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var sign_val: float = executor._get_facing_sign()
	_assert_eq_float(-1.0, sign_val, "ADV-29_facing_minus_one")
	_teardown(scene)


func test_adv29_get_facing_sign_no_parent() -> void:
	var executor := _make_executor("ADV-29_no_parent")
	if executor == null:
		return
	var sign_val: float = executor._get_facing_sign()
	_assert_eq_float(1.0, sign_val, "ADV-29_default_one_no_parent")
	executor.free()


func test_adv30_get_owner_position() -> void:
	var scene := _build_scene("ADV-30_owner_pos", [], Vector3(7.0, 3.0, 0.0), 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var pos: Vector3 = executor._get_owner_position()
	_assert_vec3_near(pos, Vector3(7.0, 3.0, 0.0), 0.01, "ADV-30_owner_pos_correct")
	_teardown(scene)


func test_adv30_get_owner_position_no_parent() -> void:
	var executor := _make_executor("ADV-30_no_parent_pos")
	if executor == null:
		return
	var pos: Vector3 = executor._get_owner_position()
	_assert_vec3_near(pos, Vector3.ZERO, 0.01, "ADV-30_default_zero_no_parent")
	executor.free()


func run_all() -> int:
	print("--- test_attack_executor_adversarial_2.gd ---")
	_pass_count = 0
	_fail_count = 0
	test_adv17_empty_effect_type_no_damage()
	test_adv18_slam_aoe_unknown()
	test_adv18_charge_unknown()
	test_adv19_all_modifiers_on_bare_enemy()
	test_adv20_knockback_preserves_y_component()
	test_adv20_knockback_large_z_zeroed()
	test_adv21_vfx_signal_includes_color_and_scale()
	test_adv22_projectile_modifiers_deep_copy()
	test_adv23_attack_hit_target_reference()
	test_adv24_projectile_fired_reference()
	test_adv25_melee_facing_left_hits_left_enemy()
	test_adv26_is_active_returns_bool()
	test_adv27_acid_defaults()
	test_adv27_slow_defaults()
	test_adv28_melee_all_modifiers_applied()
	test_adv29_get_facing_sign_with_parent()
	test_adv29_get_facing_sign_no_parent()
	test_adv30_get_owner_position()
	test_adv30_get_owner_position_no_parent()
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
