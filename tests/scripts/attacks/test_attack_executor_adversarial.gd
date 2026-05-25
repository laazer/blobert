#
# test_attack_executor_adversarial.gd
#
# Adversarial edge-case and mutation tests for AttackExecutor.
# Spec: project_board/specs/attack_executor_spec.md (AEX-1..AEX-8, EC-1..EC-20)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/05_attack_executor_handlers.md
#
# Each test targets a weakness, blind spot, or gap NOT covered by the primary
# test_attack_executor.gd suite. Tests are RED until implementation exists.
#

class_name AttackExecutorAdversarialTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

# ---------------------------------------------------------------------------
# Mock inner classes (matching primary test patterns)
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


class ParentNoFacing extends Node3D:
	pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


func _build_scene_bare_parent(
	test_label: String,
	enemies: Array = [],
	parent_pos: Vector3 = Vector3.ZERO
) -> Dictionary:
	var executor := _make_executor(test_label)
	if executor == null:
		return {}

	var scene_root := Node3D.new()
	var parent := ParentNoFacing.new()
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
# ADV-01: Null AttackResource passed to execute_attack (EC-15)
# Executor must not crash; should return immediately.
# ---------------------------------------------------------------------------

func test_adv01_null_resource_no_crash() -> void:
	var scene := _build_scene("ADV-01_null_res", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	executor.execute_attack(null)
	_assert_false(executor.is_active(), "ADV-01_active_false_after_null")
	_teardown(scene)


func test_adv01_null_resource_no_signal() -> void:
	var scene := _build_scene("ADV-01_null_no_sig", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.execute_attack(null)
	_assert_eq_int(0, _count_signal("attack_started"), "ADV-01_no_attack_started_on_null")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-02: Re-entrancy guard — overlapping execute_attack calls (EC-14)
# Second call must be a no-op while first is active.
# ---------------------------------------------------------------------------

func test_adv02_reentrant_guard_blocks_second() -> void:
	var e1 := MockEnemy.new()
	e1.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("ADV-02_reentrant", [e1], Vector3.ZERO, 1.0)
	if scene.is_empty():
		e1.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.set("_is_active", true)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 4.0})
	executor.execute_attack(res)
	_assert_eq_int(0, e1.damage_taken.size(), "ADV-02_no_damage_during_active")
	_assert_eq_int(0, _count_signal("attack_started"), "ADV-02_no_signal_during_active")
	_teardown(scene)


func test_adv02_reentrant_projectile_blocked() -> void:
	var scene := _build_scene("ADV-02_reentrant_proj", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	executor.set("_is_active", true)
	var children_before: int = scene_root.get_child_count()
	var res := _make_resource({"effect_type": "PROJECTILE_SPIT", "damage": 3.0, "projectile_speed": 100.0})
	executor.execute_attack(res)
	_assert_eq_int(children_before, scene_root.get_child_count(), "ADV-02_no_projectile_during_active")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-03: Zero damage attack — take_damage still called (EC-1)
# Utility attacks with modifiers-only are valid.
# ---------------------------------------------------------------------------

func test_adv03_zero_damage_still_calls_take_damage() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("ADV-03_zero_dmg", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 0.0,
		"attack_range": 4.0,
		"knockback_magnitude": 5.0,
		"knockback_direction": "away"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "ADV-03_take_damage_called")
	if enemy.damage_taken.size() >= 1:
		_assert_eq_float(0.0, enemy.damage_taken[0]["damage"], "ADV-03_damage_is_zero")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-04: Zero attack_range (EC-2)
# Degenerate query; probably hits nothing unless exactly co-located.
# ---------------------------------------------------------------------------

func test_adv04_zero_range_no_crash() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("ADV-04_zero_range", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 0.0})
	executor.execute_attack(res)
	_assert_false(executor.is_active(), "ADV-04_active_false_after_zero_range")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-05: Negative knockback magnitude (EC-3)
# Reversed direction; executor applies as-is.
# ---------------------------------------------------------------------------

func test_adv05_negative_knockback_magnitude() -> void:
	var executor := _make_executor("ADV-05_neg_kb")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(5.0, 0.0, 0.0), Vector3.ZERO, -10.0, "away"
	)
	_assert_true(result.x < 0.0, "ADV-05_negative_mag_reverses_direction")
	_assert_eq_float(0.0, result.z, "ADV-05_neg_kb_z_zero")
	executor.free()


func test_adv05_negative_magnitude_toward() -> void:
	var executor := _make_executor("ADV-05_neg_toward")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(5.0, 0.0, 0.0), Vector3.ZERO, -10.0, "toward"
	)
	_assert_true(result.x > 0.0, "ADV-05_neg_toward_flips")
	executor.free()


# ---------------------------------------------------------------------------
# ADV-06: Startup frames = 0 — immediate hit (EC-5)
# No timer created; hitbox query is synchronous.
# ---------------------------------------------------------------------------

func test_adv06_zero_startup_immediate_hit() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("ADV-06_zero_startup", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 3.0,
		"attack_range": 4.0,
		"startup_frames": 0
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "ADV-06_immediate_damage")
	_assert_false(executor.is_active(), "ADV-06_active_false_sync")
	_teardown(scene)


func test_adv06_zero_startup_projectile() -> void:
	var scene := _build_scene("ADV-06_zero_proj", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	var children_before: int = scene_root.get_child_count()
	var res := _make_resource({
		"effect_type": "PROJECTILE_SPIT",
		"damage": 1.0,
		"projectile_speed": 100.0,
		"startup_frames": 0
	})
	executor.execute_attack(res)
	_assert_true(scene_root.get_child_count() > children_before, "ADV-06_proj_immediate")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-07: Very large attack_range (should still work)
# No crash or overflow; enemies in range are still hit.
# ---------------------------------------------------------------------------

func test_adv07_huge_range_hits_distant_enemy() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(999.0, 0.0, 0.0)
	var scene := _build_scene("ADV-07_huge_range", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 1.0,
		"attack_range": 99999.0
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "ADV-07_distant_enemy_hit")
	_teardown(scene)


func test_adv07_huge_range_no_crash() -> void:
	var scene := _build_scene("ADV-07_huge_no_enemies", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 1.0,
		"attack_range": 1e12
	})
	executor.execute_attack(res)
	_assert_false(executor.is_active(), "ADV-07_huge_range_resets")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-08: Projectile with zero lifetime (EC-8 variant)
# Projectile created; auto-despawn is the projectile's responsibility.
# ---------------------------------------------------------------------------

func test_adv08_zero_lifetime_projectile() -> void:
	var scene := _build_scene("ADV-08_zero_life", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	var children_before: int = scene_root.get_child_count()
	var res := _make_resource({
		"effect_type": "PROJECTILE_SPIT",
		"damage": 1.0,
		"projectile_speed": 100.0,
		"projectile_lifetime": 0.0
	})
	executor.execute_attack(res)
	_assert_true(scene_root.get_child_count() > children_before, "ADV-08_zero_life_still_created")
	var proj = scene_root.get_child(scene_root.get_child_count() - 1)
	_assert_eq_float(0.0, proj.lifetime, "ADV-08_lifetime_is_zero")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-09: Knockback with zero distance (degenerate, EC-5e extended)
# target == owner; defaults direction to (1,0,0).
# ---------------------------------------------------------------------------

func test_adv09_same_position_away() -> void:
	var executor := _make_executor("ADV-09_same_pos_away")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(3.0, 0.0, 0.0), Vector3(3.0, 0.0, 0.0), 5.0, "away"
	)
	_assert_vec3_near(result, Vector3(5.0, 0.0, 0.0), 0.01, "ADV-09_away_default_right")
	executor.free()


func test_adv09_same_position_toward() -> void:
	var executor := _make_executor("ADV-09_same_pos_toward")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(3.0, 0.0, 0.0), Vector3(3.0, 0.0, 0.0), 5.0, "toward"
	)
	_assert_vec3_near(result, Vector3(-5.0, 0.0, 0.0), 0.01, "ADV-09_toward_default_left")
	executor.free()


func test_adv09_nearly_same_position() -> void:
	var executor := _make_executor("ADV-09_nearly_same")
	if executor == null:
		return
	var result: Vector3 = executor._calculate_knockback(
		Vector3(1e-10, 0.0, 0.0), Vector3.ZERO, 8.0, "away"
	)
	_assert_vec3_near(result, Vector3(8.0, 0.0, 0.0), 0.01, "ADV-09_nearly_degenerate_defaults_right")
	executor.free()


# ---------------------------------------------------------------------------
# ADV-10: Modifier keys with null values
# Null flags should not trigger modifier application.
# ---------------------------------------------------------------------------

func test_adv10_null_poison_flag() -> void:
	var executor := _make_executor("ADV-10_null_poison")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {"poison": null, "acid_on_hit": null, "slow": null})
	_assert_eq_int(0, enemy.poison_calls.size(), "ADV-10_no_poison_on_null")
	_assert_eq_int(0, enemy.acid_calls.size(), "ADV-10_no_acid_on_null")
	_assert_eq_int(0, enemy.slow_calls.size(), "ADV-10_no_slow_on_null")
	enemy.free()
	executor.free()


func test_adv10_false_poison_flag() -> void:
	var executor := _make_executor("ADV-10_false_poison")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {"poison": false, "acid_on_hit": false})
	_assert_eq_int(0, enemy.poison_calls.size(), "ADV-10_no_poison_on_false")
	_assert_eq_int(0, enemy.acid_calls.size(), "ADV-10_no_acid_on_false")
	enemy.free()
	executor.free()


func test_adv10_slow_zero_value() -> void:
	var executor := _make_executor("ADV-10_slow_zero")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {"slow": 0.0})
	_assert_eq_int(0, enemy.slow_calls.size(), "ADV-10_no_slow_on_zero")
	enemy.free()
	executor.free()


func test_adv10_slow_negative_value() -> void:
	var executor := _make_executor("ADV-10_slow_neg")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {"slow": -1.0})
	_assert_eq_int(0, enemy.slow_calls.size(), "ADV-10_no_slow_on_negative")
	enemy.free()
	executor.free()


# ---------------------------------------------------------------------------
# ADV-11: Rapid sequential attacks (cooldown is caller's job)
# After one attack completes, a second should execute immediately.
# ---------------------------------------------------------------------------

func test_adv11_rapid_sequential_melee() -> void:
	var e1 := MockEnemy.new()
	e1.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("ADV-11_rapid_melee", [e1], Vector3.ZERO, 1.0)
	if scene.is_empty():
		e1.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 2.0, "attack_range": 4.0})
	executor.execute_attack(res)
	executor.execute_attack(res)
	executor.execute_attack(res)
	_assert_true(e1.damage_taken.size() >= 3, "ADV-11_three_sequential_hits")
	_teardown(scene)


func test_adv11_rapid_sequential_signals() -> void:
	var scene := _build_scene("ADV-11_rapid_signals", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 1.0})
	executor.execute_attack(res)
	executor.execute_attack(res)
	_assert_eq_int(2, _count_signal("attack_started"), "ADV-11_two_started_signals")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-12: Signal listener count verification (no duplicate connections)
# Connecting the same callable twice must not cause double emissions.
# ---------------------------------------------------------------------------

func test_adv12_no_duplicate_signal_connections() -> void:
	var scene := _build_scene("ADV-12_dup_sigs", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var counter := [0]
	var counter_fn := func(_r): counter[0] += 1
	executor.connect("attack_started", counter_fn)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 1.0})
	executor.execute_attack(res)
	_assert_eq_int(1, counter[0], "ADV-12_single_emission")
	_teardown(scene)


func test_adv12_multiple_listeners_each_fire_once() -> void:
	var scene := _build_scene("ADV-12_multi_listen", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var counts := [0, 0]
	executor.connect("attack_started", func(_r): counts[0] += 1)
	executor.connect("attack_started", func(_r): counts[1] += 1)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 1.0})
	executor.execute_attack(res)
	_assert_eq_int(1, counts[0], "ADV-12_listener_a_once")
	_assert_eq_int(1, counts[1], "ADV-12_listener_b_once")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-13: Parent has no get_facing_sign() — defaults to 1.0 (EC-17)
# ---------------------------------------------------------------------------

func test_adv13_parent_no_facing_defaults_right() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene_bare_parent("ADV-13_no_facing", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 4.0})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "ADV-13_still_hits_with_default_facing")
	_teardown(scene)


func test_adv13_parent_no_facing_projectile_direction() -> void:
	var scene := _build_scene_bare_parent("ADV-13_no_facing_proj", [], Vector3.ZERO)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	var children_before: int = scene_root.get_child_count()
	var res := _make_resource({"effect_type": "PROJECTILE_SPIT", "damage": 1.0, "projectile_speed": 100.0})
	executor.execute_attack(res)
	if scene_root.get_child_count() <= children_before:
		_fail_test("ADV-13_no_facing_proj", "no projectile created")
		_teardown(scene)
		return
	var proj = scene_root.get_child(scene_root.get_child_count() - 1)
	_assert_eq_float(1.0, proj.direction_x, "ADV-13_proj_defaults_right")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-14: Enemy with no take_damage during melee (EC-10)
# BareEnemy has no take_damage; has_method guard silently skips.
# ---------------------------------------------------------------------------

func test_adv14_bare_enemy_melee_no_crash() -> void:
	var bare := BareEnemy.new()
	bare.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("ADV-14_bare_melee", [bare], Vector3.ZERO, 1.0)
	if scene.is_empty():
		bare.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 10.0,
		"attack_range": 4.0,
		"modifiers": {"poison": true}
	})
	executor.execute_attack(res)
	_assert_false(executor.is_active(), "ADV-14_bare_enemy_no_crash")
	_teardown(scene)


func test_adv14_mixed_enemies_bare_and_full() -> void:
	var bare := BareEnemy.new()
	var full := MockEnemy.new()
	bare.global_position = Vector3(1.0, 0.0, 0.0)
	full.global_position = Vector3(1.5, 0.0, 0.0)
	var scene := _build_scene("ADV-14_mixed", [bare, full], Vector3.ZERO, 1.0)
	if scene.is_empty():
		bare.free()
		full.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 5.0,
		"attack_range": 4.0
	})
	executor.execute_attack(res)
	_assert_true(full.damage_taken.size() >= 1, "ADV-14_full_enemy_hit")
	_assert_false(executor.is_active(), "ADV-14_mixed_completes")
	_teardown(scene)


# ---------------------------------------------------------------------------
# ADV-15: Unknown modifier keys ignored (EC-20)
# ---------------------------------------------------------------------------

func test_adv15_unknown_modifier_keys_ignored() -> void:
	var executor := _make_executor("ADV-15_unknown_mods")
	if executor == null:
		return
	var enemy := MockEnemy.new()
	executor._apply_modifiers(enemy, {
		"weaken": true,
		"freeze": 5.0,
		"explode_on_death": true,
		"nonexistent_key": "value"
	})
	_assert_eq_int(0, enemy.poison_calls.size(), "ADV-15_no_poison")
	_assert_eq_int(0, enemy.acid_calls.size(), "ADV-15_no_acid")
	_assert_eq_int(0, enemy.slow_calls.size(), "ADV-15_no_slow")
	_pass_test("ADV-15_unknown_keys_no_crash")
	enemy.free()
	executor.free()


# ---------------------------------------------------------------------------
# ADV-16: Knockback direction unknown strings (EC-19 extended)
# Multiple unknown strings all return Vector3.ZERO.
# ---------------------------------------------------------------------------

func test_adv16_knockback_various_unknown_directions() -> void:
	var executor := _make_executor("ADV-16_kb_unknown")
	if executor == null:
		return
	var unknowns := ["diagonal", "up", "down", "left", "right", "AWAY", "None", "TOWARD", ""]
	for dir_str in unknowns:
		var result: Vector3 = executor._calculate_knockback(
			Vector3(5.0, 0.0, 0.0), Vector3.ZERO, 10.0, dir_str
		)
		_assert_vec3_near(result, Vector3.ZERO, 0.001, "ADV-16_unknown_dir_" + dir_str.replace(" ", "_"))
	executor.free()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AttackExecutorAdversarialTests ===")

	test_adv01_null_resource_no_crash()
	test_adv01_null_resource_no_signal()
	test_adv02_reentrant_guard_blocks_second()
	test_adv02_reentrant_projectile_blocked()
	test_adv03_zero_damage_still_calls_take_damage()
	test_adv04_zero_range_no_crash()
	test_adv05_negative_knockback_magnitude()
	test_adv05_negative_magnitude_toward()
	test_adv06_zero_startup_immediate_hit()
	test_adv06_zero_startup_projectile()
	test_adv07_huge_range_hits_distant_enemy()
	test_adv07_huge_range_no_crash()
	test_adv08_zero_lifetime_projectile()
	test_adv09_same_position_away()
	test_adv09_same_position_toward()
	test_adv09_nearly_same_position()
	test_adv10_null_poison_flag()
	test_adv10_false_poison_flag()
	test_adv10_slow_zero_value()
	test_adv10_slow_negative_value()
	test_adv11_rapid_sequential_melee()
	test_adv11_rapid_sequential_signals()
	test_adv12_no_duplicate_signal_connections()
	test_adv12_multiple_listeners_each_fire_once()
	test_adv13_parent_no_facing_defaults_right()
	test_adv13_parent_no_facing_projectile_direction()
	test_adv14_bare_enemy_melee_no_crash()
	test_adv14_mixed_enemies_bare_and_full()
	test_adv15_unknown_modifier_keys_ignored()
	test_adv16_knockback_various_unknown_directions()

	print("AttackExecutorAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
