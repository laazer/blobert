#
# test_attack_executor.gd
#
# Behavioral tests for AttackExecutor dispatch and handlers.
# Spec: project_board/specs/attack_executor_spec.md (AEX-1 through AEX-8)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/05_attack_executor_handlers.md
#

class_name AttackExecutorTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

const _EXECUTOR_PATH := "res://scripts/attacks/attack_executor.gd"


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


class BareEnemy extends Node3D:
	pass


class MockParent extends Node3D:
	var _facing: float = 1.0

	func get_facing_sign() -> float:
		return _facing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _load_executor_script() -> GDScript:
	return load(_EXECUTOR_PATH) as GDScript


func _make_executor(test_label: String) -> Node:
	var script := _load_executor_script()
	if script == null:
		_fail_test(test_label, _EXECUTOR_PATH + " not loadable")
		return null
	var inst = script.new()
	if inst == null:
		_fail_test(test_label, "instantiation returned null")
		return null
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
# AEX-1: Class Declaration (AC-1a..AC-1f)
# ---------------------------------------------------------------------------

func test_aex01_script_loads() -> void:
	var script := _load_executor_script()
	_assert_true(script != null, "AEX-01_script_loads")


func test_aex01_class_identity() -> void:
	var inst := _make_executor("AEX-01_identity")
	if inst == null:
		return
	_assert_true(inst is Node, "AEX-01_is_node")
	_assert_false(is_instance_of(inst, Resource), "AEX-01_not_resource")
	_assert_false(inst is CharacterBody3D, "AEX-01_not_character_body")
	inst.free()


# ---------------------------------------------------------------------------
# AEX-2: Dispatch Function (AC-2a..AC-2g)
# ---------------------------------------------------------------------------

func test_aex02_melee_dispatch() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("AEX-02_melee_dispatch", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 4.0})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "AEX-02_melee_routed")
	_teardown(scene)


func test_aex02_projectile_dispatch() -> void:
	var scene := _build_scene("AEX-02_proj_dispatch", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	var children_before: int = scene_root.get_child_count()
	var res := _make_resource({"effect_type": "PROJECTILE_SPIT", "damage": 3.0, "projectile_speed": 100.0})
	executor.execute_attack(res)
	_assert_true(scene_root.get_child_count() > children_before, "AEX-02_projectile_routed")
	_teardown(scene)


func test_aex02_active_guard() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("AEX-02_active_guard", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	executor.set("_is_active", true)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 4.0})
	executor.execute_attack(res)
	_assert_eq_int(0, enemy.damage_taken.size(), "AEX-02_overlap_blocked")
	_teardown(scene)


func test_aex02_active_resets_after_handler() -> void:
	var scene := _build_scene("AEX-02_active_reset", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 1.0})
	executor.execute_attack(res)
	_assert_false(executor.is_active(), "AEX-02_active_false_after")
	_teardown(scene)


# ---------------------------------------------------------------------------
# AEX-3: MELEE_SWIPE Handler (AC-3a..AC-3i)
# ---------------------------------------------------------------------------

func test_aex03_melee_hits_in_range() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.5, 0.0, 0.0)
	var scene := _build_scene("AEX-03_in_range", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 10.0, "attack_range": 4.0})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "AEX-03_enemy_hit")
	_teardown(scene)


func test_aex03_melee_misses_out_of_range() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(50.0, 0.0, 0.0)
	var scene := _build_scene("AEX-03_out_of_range", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 10.0, "attack_range": 2.0})
	executor.execute_attack(res)
	_assert_eq_int(0, enemy.damage_taken.size(), "AEX-03_enemy_not_hit")
	_teardown(scene)


func test_aex03_melee_damage_and_knockback() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("AEX-03_dmg_kb", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 7.5,
		"attack_range": 4.0,
		"knockback_magnitude": 10.0,
		"knockback_direction": "away"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "AEX-03_damage_called")
	if enemy.damage_taken.size() >= 1:
		_assert_eq_float(7.5, enemy.damage_taken[0]["damage"], "AEX-03_damage_value")
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.x > 0.0, "AEX-03_knockback_positive_x")
		_assert_eq_float(0.0, kb.z, "AEX-03_knockback_z_zero")
	_teardown(scene)


func test_aex03_melee_no_enemies() -> void:
	var scene := _build_scene("AEX-03_no_enemies", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 4.0})
	executor.execute_attack(res)
	_assert_false(executor.is_active(), "AEX-03_no_crash_no_enemies")
	_teardown(scene)


func test_aex03_melee_multiple_enemies() -> void:
	var e1 := MockEnemy.new()
	var e2 := MockEnemy.new()
	var e3 := MockEnemy.new()
	e1.global_position = Vector3(1.0, 0.0, 0.0)
	e2.global_position = Vector3(1.5, 0.0, 0.0)
	e3.global_position = Vector3(100.0, 0.0, 0.0)
	var scene := _build_scene("AEX-03_multi", [e1, e2, e3], Vector3.ZERO, 1.0)
	if scene.is_empty():
		e1.free()
		e2.free()
		e3.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 3.0, "attack_range": 4.0})
	executor.execute_attack(res)
	_assert_true(e1.damage_taken.size() >= 1, "AEX-03_multi_e1_hit")
	_assert_true(e2.damage_taken.size() >= 1, "AEX-03_multi_e2_hit")
	_assert_eq_int(0, e3.damage_taken.size(), "AEX-03_multi_e3_miss")
	_teardown(scene)


# ---------------------------------------------------------------------------
# AEX-4: PROJECTILE_SPIT Handler (AC-4a..AC-4g)
# ---------------------------------------------------------------------------

func test_aex04_projectile_created() -> void:
	var scene := _build_scene("AEX-04_create", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	var children_before: int = scene_root.get_child_count()
	var res := _make_resource({
		"effect_type": "PROJECTILE_SPIT",
		"damage": 5.0,
		"projectile_speed": 200.0,
		"projectile_lifetime": 3.0
	})
	executor.execute_attack(res)
	_assert_true(scene_root.get_child_count() > children_before, "AEX-04_projectile_added")
	_teardown(scene)


func test_aex04_projectile_properties() -> void:
	var scene := _build_scene("AEX-04_props", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	var children_before: int = scene_root.get_child_count()
	var mods := {"poison": true, "poison_duration": 3.0, "poison_dps": 0.5}
	var res := _make_resource({
		"effect_type": "PROJECTILE_SPIT",
		"damage": 8.0,
		"projectile_speed": 150.0,
		"projectile_lifetime": 4.0,
		"knockback_magnitude": 5.0,
		"knockback_direction": "away",
		"modifiers": mods
	})
	executor.execute_attack(res)
	if scene_root.get_child_count() <= children_before:
		_fail_test("AEX-04_props", "no projectile child added")
		_teardown(scene)
		return
	var proj = scene_root.get_child(scene_root.get_child_count() - 1)
	_assert_eq_float(8.0, proj.damage, "AEX-04_proj_damage")
	_assert_eq_float(150.0, proj.speed, "AEX-04_proj_speed")
	_assert_eq_float(4.0, proj.lifetime, "AEX-04_proj_lifetime")
	_assert_eq_float(5.0, proj.knockback_magnitude, "AEX-04_proj_kb_mag")
	_assert_eq_string("away", proj.knockback_direction, "AEX-04_proj_kb_dir")
	_assert_true(proj.modifiers.get("poison", false) == true, "AEX-04_proj_mod_poison")
	_teardown(scene)


func test_aex04_projectile_direction() -> void:
	var scene := _build_scene("AEX-04_dir", [], Vector3.ZERO, -1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	var children_before: int = scene_root.get_child_count()
	var res := _make_resource({"effect_type": "PROJECTILE_SPIT", "damage": 1.0, "projectile_speed": 100.0})
	executor.execute_attack(res)
	if scene_root.get_child_count() <= children_before:
		_fail_test("AEX-04_dir", "no projectile child added")
		_teardown(scene)
		return
	var proj = scene_root.get_child(scene_root.get_child_count() - 1)
	_assert_eq_float(-1.0, proj.direction_x, "AEX-04_facing_left")
	_teardown(scene)


func test_aex04_zero_speed() -> void:
	var scene := _build_scene("AEX-04_zero_spd", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	var children_before: int = scene_root.get_child_count()
	var res := _make_resource({"effect_type": "PROJECTILE_SPIT", "damage": 1.0, "projectile_speed": 0.0})
	executor.execute_attack(res)
	_assert_true(scene_root.get_child_count() > children_before, "AEX-04_zero_speed_still_created")
	_teardown(scene)


# ---------------------------------------------------------------------------
# AEX-5: Knockback Direction Calculation (AC-5a..AC-5g)
# ---------------------------------------------------------------------------

func test_aex05_knockback_away() -> void:
	var executor := _make_executor("AEX-05_away")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(5.0, 0.0, 0.0), Vector3.ZERO, 10.0, "away"
	)
	_assert_vec3_near(result, Vector3(10.0, 0.0, 0.0), 0.01, "AEX-05_away_direction")
	executor.free()


func test_aex05_knockback_toward() -> void:
	var executor := _make_executor("AEX-05_toward")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(5.0, 0.0, 0.0), Vector3.ZERO, 10.0, "toward"
	)
	_assert_vec3_near(result, Vector3(-10.0, 0.0, 0.0), 0.01, "AEX-05_toward_direction")
	executor.free()


func test_aex05_knockback_none() -> void:
	var executor := _make_executor("AEX-05_none")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(5.0, 0.0, 0.0), Vector3.ZERO, 10.0, "none"
	)
	_assert_vec3_near(result, Vector3.ZERO, 0.001, "AEX-05_none_zero")
	executor.free()


func test_aex05_knockback_zero_magnitude() -> void:
	var executor := _make_executor("AEX-05_zero_mag")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(5.0, 0.0, 0.0), Vector3.ZERO, 0.0, "away"
	)
	_assert_vec3_near(result, Vector3.ZERO, 0.001, "AEX-05_zero_mag_returns_zero")
	executor.free()


func test_aex05_knockback_degenerate() -> void:
	var executor := _make_executor("AEX-05_degen")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3.ZERO, Vector3.ZERO, 10.0, "away"
	)
	_assert_vec3_near(result, Vector3(10.0, 0.0, 0.0), 0.01, "AEX-05_degenerate_defaults_right")
	executor.free()


func test_aex05_knockback_z_zeroed() -> void:
	var executor := _make_executor("AEX-05_z_zero")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(3.0, 2.0, 999.0), Vector3.ZERO, 10.0, "away"
	)
	_assert_eq_float(0.0, result.z, "AEX-05_z_component_zero")
	executor.free()


func test_aex05_knockback_unknown_direction() -> void:
	var executor := _make_executor("AEX-05_unknown")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(5.0, 0.0, 0.0), Vector3.ZERO, 10.0, "diagonal"
	)
	_assert_vec3_near(result, Vector3.ZERO, 0.001, "AEX-05_unknown_dir_zero")
	executor.free()


# ---------------------------------------------------------------------------
# AEX-6: Modifier Application (AC-6a..AC-6h)
# ---------------------------------------------------------------------------

func test_aex06_poison() -> void:
	var executor := _make_executor("AEX-06_poison")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {"poison": true, "poison_duration": 3.0, "poison_dps": 0.5})
	_assert_eq_int(1, enemy.poison_calls.size(), "AEX-06_poison_called")
	if enemy.poison_calls.size() >= 1:
		_assert_eq_float(3.0, enemy.poison_calls[0]["duration"], "AEX-06_poison_dur")
		_assert_eq_float(0.5, enemy.poison_calls[0]["dps"], "AEX-06_poison_dps")
	enemy.free()
	executor.free()


func test_aex06_acid() -> void:
	var executor := _make_executor("AEX-06_acid")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {"acid_on_hit": true, "acid_duration": 4.0, "acid_dps": 0.8})
	_assert_eq_int(1, enemy.acid_calls.size(), "AEX-06_acid_called")
	if enemy.acid_calls.size() >= 1:
		_assert_eq_float(4.0, enemy.acid_calls[0]["duration"], "AEX-06_acid_dur")
		_assert_eq_float(0.8, enemy.acid_calls[0]["dps"], "AEX-06_acid_dps")
	enemy.free()
	executor.free()


func test_aex06_slow() -> void:
	var executor := _make_executor("AEX-06_slow")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {"slow": 0.5, "slow_duration": 2.0})
	_assert_eq_int(1, enemy.slow_calls.size(), "AEX-06_slow_called")
	if enemy.slow_calls.size() >= 1:
		_assert_eq_float(0.5, enemy.slow_calls[0]["multiplier"], "AEX-06_slow_mult")
		_assert_eq_float(2.0, enemy.slow_calls[0]["duration"], "AEX-06_slow_dur")
	enemy.free()
	executor.free()


func test_aex06_guard_no_crash() -> void:
	var executor := _make_executor("AEX-06_guard")
	if executor == null:
		return
	var bare := BareEnemy.new()
	executor._apply_modifiers(bare, {"poison": true, "acid_on_hit": true, "slow": 0.5})
	_pass_test("AEX-06_guard_no_crash")
	bare.free()
	executor.free()


func test_aex06_empty_modifiers() -> void:
	var executor := _make_executor("AEX-06_empty")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {})
	_assert_eq_int(0, enemy.poison_calls.size(), "AEX-06_empty_no_poison")
	_assert_eq_int(0, enemy.acid_calls.size(), "AEX-06_empty_no_acid")
	_assert_eq_int(0, enemy.slow_calls.size(), "AEX-06_empty_no_slow")
	enemy.free()
	executor.free()


func test_aex06_multiple_concurrent() -> void:
	var executor := _make_executor("AEX-06_multi")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {
		"poison": true, "poison_duration": 2.0, "poison_dps": 0.3,
		"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.2,
		"slow": 0.7, "slow_duration": 1.5
	})
	_assert_eq_int(1, enemy.poison_calls.size(), "AEX-06_multi_poison")
	_assert_eq_int(1, enemy.acid_calls.size(), "AEX-06_multi_acid")
	_assert_eq_int(1, enemy.slow_calls.size(), "AEX-06_multi_slow")
	enemy.free()
	executor.free()


func test_aex06_default_values() -> void:
	var executor := _make_executor("AEX-06_defaults")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {"poison": true})
	_assert_eq_int(1, enemy.poison_calls.size(), "AEX-06_defaults_called")
	if enemy.poison_calls.size() >= 1:
		_assert_eq_float(2.0, enemy.poison_calls[0]["duration"], "AEX-06_default_poison_dur")
		_assert_eq_float(0.3, enemy.poison_calls[0]["dps"], "AEX-06_default_poison_dps")
	enemy.free()
	executor.free()


# ---------------------------------------------------------------------------
# AEX-7: Signal Emission (AC-7a..AC-7f)
# ---------------------------------------------------------------------------

func test_aex07_attack_started() -> void:
	var scene := _build_scene("AEX-07_started", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 1.0})
	executor.execute_attack(res)
	_assert_eq_int(1, _count_signal("attack_started"), "AEX-07_started_emitted_once")
	_teardown(scene)


func test_aex07_attack_hit_per_enemy() -> void:
	var e1 := MockEnemy.new()
	var e2 := MockEnemy.new()
	e1.global_position = Vector3(1.0, 0.0, 0.0)
	e2.global_position = Vector3(1.5, 0.0, 0.0)
	var scene := _build_scene("AEX-07_hit_per", [e1, e2], Vector3.ZERO, 1.0)
	if scene.is_empty():
		e1.free()
		e2.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 4.0})
	executor.execute_attack(res)
	_assert_eq_int(2, _count_signal("attack_hit"), "AEX-07_two_hit_signals")
	_teardown(scene)


func test_aex07_projectile_fired() -> void:
	var scene := _build_scene("AEX-07_proj_sig", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "PROJECTILE_SPIT", "damage": 1.0, "projectile_speed": 100.0})
	executor.execute_attack(res)
	_assert_eq_int(1, _count_signal("projectile_fired"), "AEX-07_proj_fired_once")
	_teardown(scene)


func test_aex07_melee_vfx_on_miss() -> void:
	var scene := _build_scene("AEX-07_vfx_miss", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 1.0})
	executor.execute_attack(res)
	_assert_eq_int(1, _count_signal("melee_vfx_requested"), "AEX-07_vfx_on_whiff")
	_assert_eq_int(0, _count_signal("attack_hit"), "AEX-07_zero_hits_on_whiff")
	_teardown(scene)


func test_aex07_no_signals_on_unknown() -> void:
	var scene := _build_scene("AEX-07_unknown_sigs", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "TOTALLY_UNKNOWN"})
	executor.execute_attack(res)
	_assert_eq_int(1, _count_signal("attack_started"), "AEX-07_unknown_started_yes")
	_assert_eq_int(0, _count_signal("attack_hit"), "AEX-07_unknown_no_hit")
	_assert_eq_int(0, _count_signal("projectile_fired"), "AEX-07_unknown_no_proj")
	_assert_eq_int(0, _count_signal("melee_vfx_requested"), "AEX-07_unknown_no_vfx")
	_teardown(scene)


# ---------------------------------------------------------------------------
# AEX-8: Unknown effect_type (AC-8a..AC-8f)
# ---------------------------------------------------------------------------

func test_aex08_unknown_no_crash() -> void:
	var scene := _build_scene("AEX-08_no_crash", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "INVALID_TYPE"})
	executor.execute_attack(res)
	_pass_test("AEX-08_no_crash")
	_teardown(scene)


func test_aex08_empty_effect_type() -> void:
	var scene := _build_scene("AEX-08_empty", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": ""})
	executor.execute_attack(res)
	_pass_test("AEX-08_empty_treated_as_unknown")
	_teardown(scene)


func test_aex08_active_resets() -> void:
	var scene := _build_scene("AEX-08_active_reset", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "UNKNOWN_HANDLER"})
	executor.execute_attack(res)
	_assert_false(executor.is_active(), "AEX-08_active_false_after_unknown")
	_teardown(scene)


func test_aex08_no_damage_no_projectile() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("AEX-08_no_side_fx", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	var children_before: int = scene_root.get_child_count()
	var res := _make_resource({"effect_type": "FUTURE_UNKNOWN", "damage": 99.0, "attack_range": 100.0})
	executor.execute_attack(res)
	_assert_eq_int(0, enemy.damage_taken.size(), "AEX-08_no_damage")
	_assert_eq_int(children_before, scene_root.get_child_count(), "AEX-08_no_projectile_created")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AttackExecutorTests ===")

	# AEX-1: Class Declaration
	test_aex01_script_loads()
	test_aex01_class_identity()

	# AEX-2: Dispatch Function
	test_aex02_melee_dispatch()
	test_aex02_projectile_dispatch()
	test_aex02_active_guard()
	test_aex02_active_resets_after_handler()

	# AEX-3: MELEE_SWIPE Handler
	test_aex03_melee_hits_in_range()
	test_aex03_melee_misses_out_of_range()
	test_aex03_melee_damage_and_knockback()
	test_aex03_melee_no_enemies()
	test_aex03_melee_multiple_enemies()

	# AEX-4: PROJECTILE_SPIT Handler
	test_aex04_projectile_created()
	test_aex04_projectile_properties()
	test_aex04_projectile_direction()
	test_aex04_zero_speed()

	# AEX-5: Knockback Direction Calculation
	test_aex05_knockback_away()
	test_aex05_knockback_toward()
	test_aex05_knockback_none()
	test_aex05_knockback_zero_magnitude()
	test_aex05_knockback_degenerate()
	test_aex05_knockback_z_zeroed()
	test_aex05_knockback_unknown_direction()

	# AEX-6: Modifier Application
	test_aex06_poison()
	test_aex06_acid()
	test_aex06_slow()
	test_aex06_guard_no_crash()
	test_aex06_empty_modifiers()
	test_aex06_multiple_concurrent()
	test_aex06_default_values()

	# AEX-7: Signal Emission
	test_aex07_attack_started()
	test_aex07_attack_hit_per_enemy()
	test_aex07_projectile_fired()
	test_aex07_melee_vfx_on_miss()
	test_aex07_no_signals_on_unknown()

	# AEX-8: Unknown effect_type
	test_aex08_unknown_no_crash()
	test_aex08_empty_effect_type()
	test_aex08_active_resets()
	test_aex08_no_damage_no_projectile()

	print("AttackExecutorTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
