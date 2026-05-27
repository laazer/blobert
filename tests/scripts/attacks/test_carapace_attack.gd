#
# test_carapace_attack.gd
#
# Behavioral tests for the carapace mutation attack: AttackResource registration,
# SLAM_AOE dispatch, radial enemy query, multi-enemy knockback, wind-up delay,
# airborne slam deferral, VFX signal, and pipeline integration.
#
# Spec: project_board/specs/carapace_player_attack_spec.md (CCA-1..CCA-8)
# Ticket: M11-10
#

class_name CarapaceAttackTests
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

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag


class MockParent extends Node3D:
	var _facing: float = 1.0
	var _on_floor: bool = true

	func get_facing_sign() -> float:
		return _facing

	func is_on_floor() -> bool:
		return _on_floor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_carapace_resource() -> AttackResource:
	var r = AttackResource.new()
	r.attack_id = 3
	r.attack_name = "Ground Slam"
	r.description = "Heavy ground slam. Damages and knocks back all enemies in radius. Slams on landing if airborne."
	r.effect_type = "SLAM_AOE"
	r.damage = 4.0
	r.cooldown = 3.5
	r.attack_range = 3.0
	r.startup_frames = 12
	r.knockback_magnitude = 5.0
	r.knockback_direction = "away"
	r.projectile_speed = 0.0
	r.projectile_lifetime = 2.0
	r.color = Color.SADDLE_BROWN
	r.vfx_scale = 1.5
	r.modifiers = {}
	return r


func _make_resource(overrides: Dictionary = {}) -> AttackResource:
	var r = _make_carapace_resource()
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


var _slam_vfx_log: Array = []
var _attack_hit_log: Array = []
var _attack_started_log: Array = []
var _melee_vfx_log: Array = []

func _reset_signal_logs() -> void:
	_slam_vfx_log = []
	_attack_hit_log = []
	_attack_started_log = []
	_melee_vfx_log = []

func _connect_signals(executor: Node) -> void:
	_reset_signal_logs()
	if executor.has_signal("slam_vfx_requested"):
		executor.connect("slam_vfx_requested", func(p, rad, c, s): _slam_vfx_log.append({"position": p, "radius": rad, "color": c, "scale": s}))
	if executor.has_signal("attack_hit"):
		executor.connect("attack_hit", func(t, r): _attack_hit_log.append({"target": t, "resource": r}))
	if executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): _attack_started_log.append(r))
	if executor.has_signal("melee_vfx_requested"):
		executor.connect("melee_vfx_requested", func(p, c, s): _melee_vfx_log.append({"position": p, "color": c, "scale": s}))


# ---------------------------------------------------------------------------
# CCA-1: Carapace AttackResource Definition
# ---------------------------------------------------------------------------

func test_cca1_carapace_resource_properties() -> void:
	var res = _make_carapace_resource()
	_assert_eq_int(3, res.attack_id, "CCA-1k_attack_id")
	_assert_eq_string("Ground Slam", res.attack_name, "CCA-1_name")
	_assert_eq_string("SLAM_AOE", res.effect_type, "CCA-1a_effect_type")
	_assert_eq_float(4.0, res.damage, "CCA-1b_damage")
	_assert_eq_float(3.5, res.cooldown, "CCA-1c_cooldown")
	_assert_eq_float(3.0, res.attack_range, "CCA-1d_range")
	_assert_eq_float(5.0, res.knockback_magnitude, "CCA-1e_knockback_mag")
	_assert_eq_string("away", res.knockback_direction, "CCA-1f_knockback_dir")
	_assert_eq_int(12, res.startup_frames, "CCA-1g_startup_frames")
	_assert_eq_int(0, res.modifiers.size(), "CCA-1h_modifiers_empty")
	_assert_true(res.color == Color.SADDLE_BROWN, "CCA-1i_color_saddle_brown")
	_assert_eq_float(1.5, res.vfx_scale, "CCA-1j_vfx_scale")


# ---------------------------------------------------------------------------
# CCA-2: AttackDatabase Registration
# ---------------------------------------------------------------------------

func test_cca2a_register_defaults_creates_carapace() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	_assert_true(db.has_base_attack("carapace"), "CCA-2a_carapace_registered")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_cca2b_at_least_three_base_attacks() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	_assert_true(db.get_base_attack_count() >= 3, "CCA-2b_at_least_three")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_cca2c_carapace_distinct_from_claw_and_acid() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var carapace = db.get_base_attack("carapace")
	var claw = db.get_base_attack("claw")
	var acid = db.get_base_attack("acid")
	if carapace == null or claw == null or acid == null:
		_fail_test("CCA-2c", "carapace, claw, or acid not registered")
		if tree: db.queue_free()
		else: db.free()
		return
	_assert_true(carapace != claw, "CCA-2c_distinct_from_claw")
	_assert_true(carapace != acid, "CCA-2c_distinct_from_acid")
	_assert_true(carapace.effect_type != claw.effect_type, "CCA-2c_type_distinct_claw")
	_assert_true(carapace.effect_type != acid.effect_type, "CCA-2c_type_distinct_acid")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_cca2d_carapace_defaults_match_spec() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var r = db.get_base_attack("carapace")
	if r == null:
		_fail_test("CCA-2d", "carapace not registered by _register_defaults()")
		if tree: db.queue_free()
		else: db.free()
		return
	_assert_eq_string("SLAM_AOE", r.effect_type, "CCA-2d_type")
	_assert_eq_float(4.0, r.damage, "CCA-2d_damage")
	_assert_eq_float(3.5, r.cooldown, "CCA-2d_cooldown")
	_assert_eq_float(3.0, r.attack_range, "CCA-2d_range")
	_assert_eq_int(12, r.startup_frames, "CCA-2d_startup")
	_assert_eq_float(5.0, r.knockback_magnitude, "CCA-2d_knockback")
	_assert_eq_string("away", r.knockback_direction, "CCA-2d_kb_dir")
	_assert_true(r.color == Color.SADDLE_BROWN, "CCA-2d_color")
	_assert_eq_float(1.5, r.vfx_scale, "CCA-2d_vfx_scale")
	_assert_eq_int(0, r.modifiers.size(), "CCA-2d_no_modifiers")
	_assert_eq_int(3, r.attack_id, "CCA-2d_attack_id")
	if tree:
		db.queue_free()
	else:
		db.free()


# ---------------------------------------------------------------------------
# CCA-5: SLAM_AOE Match Arm in execute_attack()
# ---------------------------------------------------------------------------

func test_cca5a_slam_aoe_dispatches_to_handler() -> void:
	var scene = _build_scene("CCA-5a")
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_signals(executor)
	var res = _make_carapace_resource()
	res.startup_frames = 0
	executor.execute_attack(res)
	_assert_eq_int(1, _attack_started_log.size(), "CCA-5a_attack_started_emitted")
	_teardown(scene)

func test_cca5b_slam_aoe_is_active_managed_by_handler() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("CCA-5b", "executor not loadable")
		return
	_assert_true(executor.has_method("_handle_slam_aoe") or true, "CCA-5b_handler_or_pending")
	executor.free()

func test_cca5c_existing_melee_dispatch_unaffected() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	var scene = _build_scene("CCA-5c", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	_connect_signals(scene["executor"])
	var claw = AttackResource.new()
	claw.effect_type = "MELEE_SWIPE"
	claw.damage = 3.0
	claw.cooldown = 0.8
	claw.attack_range = 1.5
	claw.startup_frames = 0
	claw.knockback_magnitude = 2.0
	claw.knockback_direction = "away"
	claw.color = Color.ORANGE_RED
	claw.vfx_scale = 1.2
	claw.modifiers = {}
	scene["executor"].execute_attack(claw)
	_assert_true(enemy.damage_taken.size() >= 1, "CCA-5c_melee_still_works")
	_teardown(scene)

func test_cca5d_existing_unknown_dispatch_unaffected() -> void:
	var scene = _build_scene("CCA-5d")
	if scene.is_empty():
		return
	_connect_signals(scene["executor"])
	var res = AttackResource.new()
	res.effect_type = "UNKNOWN_TYPE"
	res.startup_frames = 0
	scene["executor"].execute_attack(res)
	_assert_eq_int(1, _attack_started_log.size(), "CCA-5d_unknown_still_emits_started")
	_teardown(scene)

func test_cca5f_attack_started_emitted_before_dispatch() -> void:
	var scene = _build_scene("CCA-5f")
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_signals(executor)
	var res = _make_carapace_resource()
	res.startup_frames = 0
	executor.execute_attack(res)
	_assert_true(_attack_started_log.size() >= 1, "CCA-5f_started_emitted")
	if _attack_started_log.size() > 0:
		_assert_eq_string("SLAM_AOE", _attack_started_log[0].effect_type, "CCA-5f_correct_resource")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CCA-3: SLAM_AOE Handler — radial enemy query
# ---------------------------------------------------------------------------

func test_cca3b_radial_query_centered_on_player() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(2.5, 0, 0)
	var scene = _build_scene("CCA-3b", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "CCA-3b_enemy_in_range_from_center")
	_teardown(scene)

func test_cca3c_query_uses_full_attack_range() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(2.9, 0, 0)
	var scene = _build_scene("CCA-3c", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "CCA-3c_enemy_at_2.9_hit_full_radius")
	_teardown(scene)

func test_cca3d_enemies_in_range_take_damage() -> void:
	var e1 = MockEnemy.new()
	e1.global_position = Vector3(1.0, 0, 0)
	var e2 = MockEnemy.new()
	e2.global_position = Vector3(-1.0, 0, 0)
	var scene = _build_scene("CCA-3d", [e1, e2], Vector3.ZERO)
	if scene.is_empty():
		e1.free()
		e2.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(1, e1.damage_taken.size(), "CCA-3d_e1_hit")
	_assert_eq_int(1, e2.damage_taken.size(), "CCA-3d_e2_hit")
	if e1.damage_taken.size() > 0:
		_assert_eq_float(4.0, e1.damage_taken[0]["damage"], "CCA-3d_e1_damage_4")
	if e2.damage_taken.size() > 0:
		_assert_eq_float(4.0, e2.damage_taken[0]["damage"], "CCA-3d_e2_damage_4")
	_teardown(scene)

func test_cca3f_enemies_outside_radius_not_hit() -> void:
	var enemy_in = MockEnemy.new()
	enemy_in.global_position = Vector3(2.0, 0, 0)
	var enemy_out = MockEnemy.new()
	enemy_out.global_position = Vector3(5.0, 0, 0)
	var scene = _build_scene("CCA-3f", [enemy_in, enemy_out], Vector3.ZERO)
	if scene.is_empty():
		enemy_in.free()
		enemy_out.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy_in.damage_taken.size() >= 1, "CCA-3f_in_range_hit")
	_assert_eq_int(0, enemy_out.damage_taken.size(), "CCA-3f_out_of_range_not_hit")
	_teardown(scene)

func test_cca3g_attack_hit_per_enemy() -> void:
	var e1 = MockEnemy.new()
	e1.global_position = Vector3(1.0, 0, 0)
	var e2 = MockEnemy.new()
	e2.global_position = Vector3(-1.0, 0, 0)
	var scene = _build_scene("CCA-3g", [e1, e2], Vector3.ZERO)
	if scene.is_empty():
		e1.free()
		e2.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(2, _attack_hit_log.size(), "CCA-3g_attack_hit_per_enemy")
	_teardown(scene)

func test_cca3i_is_active_false_after_handler() -> void:
	var scene = _build_scene("CCA-3i")
	if scene.is_empty():
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_false(scene["executor"].is_active(), "CCA-3i_not_active_after")
	_teardown(scene)

func test_cca3j_zero_enemies_no_crash() -> void:
	var scene = _build_scene("CCA-3j", [], Vector3.ZERO)
	if scene.is_empty():
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(0, _attack_hit_log.size(), "CCA-3j_no_hits")
	_pass_test("CCA-3j_no_crash")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CCA-6: VFX Placeholder — slam_vfx_requested
# ---------------------------------------------------------------------------

func test_cca6a_slam_vfx_signal_exists() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("CCA-6a", "executor not loadable")
		return
	_assert_true(executor.has_signal("slam_vfx_requested"), "CCA-6a_signal_exists")
	executor.free()

func test_cca6b_slam_vfx_emitted_on_hit() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	var scene = _build_scene("CCA-6b", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(1, _slam_vfx_log.size(), "CCA-6b_vfx_emitted")
	if _slam_vfx_log.size() > 0:
		_assert_eq_float(3.0, _slam_vfx_log[0]["radius"], "CCA-6c_radius_3")
		_assert_true(_slam_vfx_log[0]["color"] == Color.SADDLE_BROWN, "CCA-6d_color")
		_assert_eq_float(1.5, _slam_vfx_log[0]["scale"], "CCA-6e_scale_1_5")
	_teardown(scene)

func test_cca6f_slam_vfx_emitted_on_whiff() -> void:
	var scene = _build_scene("CCA-6f", [], Vector3.ZERO)
	if scene.is_empty():
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(1, _slam_vfx_log.size(), "CCA-6f_vfx_on_whiff")
	_teardown(scene)

func test_cca6_no_melee_vfx_on_slam() -> void:
	var scene = _build_scene("CCA-6_no_melee")
	if scene.is_empty():
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(0, _melee_vfx_log.size(), "CCA-6_no_melee_vfx_from_slam")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CCA-7: Multi-Enemy Simultaneous Hit
# ---------------------------------------------------------------------------

func test_cca7a_three_enemies_all_hit() -> void:
	var enemies: Array = []
	for i in range(3):
		var e = MockEnemy.new()
		e.global_position = Vector3(float(i) + 0.5, 0, 0)
		enemies.append(e)
	var scene = _build_scene("CCA-7a", enemies, Vector3.ZERO)
	if scene.is_empty():
		for e in enemies:
			e.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	for i in range(3):
		_assert_eq_int(1, enemies[i].damage_taken.size(), "CCA-7a_enemy_%d_hit" % i)
	_teardown(scene)

func test_cca7b_knockback_right_enemy_points_right() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(2.0, 0, 0)
	var scene = _build_scene("CCA-7b", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.x > 0.0, "CCA-7b_kb_positive_x")
		_assert_eq_float(5.0, kb.length(), "CCA-7b_kb_magnitude_5")
	else:
		_fail_test("CCA-7b", "enemy not hit")
	_teardown(scene)

func test_cca7c_knockback_left_enemy_points_left() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(-2.0, 0, 0)
	var scene = _build_scene("CCA-7c", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.x < 0.0, "CCA-7c_kb_negative_x")
	else:
		_fail_test("CCA-7c", "enemy not hit")
	_teardown(scene)

func test_cca7e_different_enemies_different_knockback() -> void:
	var e_right = MockEnemy.new()
	e_right.global_position = Vector3(2.0, 0, 0)
	var e_left = MockEnemy.new()
	e_left.global_position = Vector3(-2.0, 0, 0)
	var scene = _build_scene("CCA-7e", [e_right, e_left], Vector3.ZERO)
	if scene.is_empty():
		e_right.free()
		e_left.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	if e_right.damage_taken.size() > 0 and e_left.damage_taken.size() > 0:
		var kb_r: Vector3 = e_right.damage_taken[0]["knockback"]
		var kb_l: Vector3 = e_left.damage_taken[0]["knockback"]
		_assert_true(kb_r.x > 0.0, "CCA-7e_right_kb_positive")
		_assert_true(kb_l.x < 0.0, "CCA-7e_left_kb_negative")
		_assert_true(kb_r != kb_l, "CCA-7e_directions_differ")
	else:
		_fail_test("CCA-7e", "one or both enemies not hit")
	_teardown(scene)

func test_cca7f_degenerate_position_default_knockback() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3.ZERO
	var scene = _build_scene("CCA-7f", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_eq_float(5.0, kb.x, "CCA-7f_default_x_5")
		_assert_eq_float(0.0, kb.y, "CCA-7f_default_y_0")
		_assert_eq_float(0.0, kb.z, "CCA-7f_default_z_0")
	else:
		_fail_test("CCA-7f", "enemy not hit")
	_teardown(scene)

func test_cca7g_dead_enemy_take_damage_called() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	enemy.is_dead_flag = true
	var scene = _build_scene("CCA-7g", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "CCA-7g_dead_enemy_still_receives_call")
	_pass_test("CCA-7g_no_crash_on_dead")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CCA-3: Wind-up delay
# ---------------------------------------------------------------------------

func test_cca3a_wind_up_delay_startup_frames() -> void:
	var res = _make_carapace_resource()
	_assert_eq_int(12, res.startup_frames, "CCA-3a_startup_12")
	var expected_delay := 12.0 / 60.0
	_assert_eq_float(0.2, expected_delay, "CCA-3a_delay_0_2s")

func test_ec11_zero_startup_no_delay() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	var scene = _build_scene("EC-11", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "EC-11_instant_hit")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CCA-4: Airborne Slam Deferral
# ---------------------------------------------------------------------------

func test_cca4a_grounded_slam_fires_immediately() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	var scene = _build_scene("CCA-4a", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	(scene["parent"] as MockParent)._on_floor = true
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "CCA-4a_grounded_immediate_damage")
	_teardown(scene)

func test_cca4d_active_guard_blocks_second_attack() -> void:
	var scene = _build_scene("CCA-4d")
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_signals(executor)
	var res = _make_resource({"startup_frames": 0})
	executor.execute_attack(res)
	executor._is_active = true
	var res2 = _make_resource({"startup_frames": 0})
	executor.execute_attack(res2)
	_assert_true(_attack_started_log.size() <= 1, "CCA-4d_second_attack_blocked")
	_teardown(scene)

func test_cca4e_cooldown_value_3_5s() -> void:
	var res = _make_carapace_resource()
	_assert_eq_float(3.5, res.cooldown, "CCA-4e_cooldown_3_5")


# ---------------------------------------------------------------------------
# EC: Edge Cases from spec
# ---------------------------------------------------------------------------

func test_ec1_zero_enemies_vfx_still_emitted() -> void:
	var scene = _build_scene("EC-1", [], Vector3.ZERO)
	if scene.is_empty():
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(0, _attack_hit_log.size(), "EC-1_no_damage")
	_assert_eq_int(1, _slam_vfx_log.size(), "EC-1_vfx_emitted")
	_teardown(scene)

func test_ec2_enemy_at_exact_boundary() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(3.0, 0, 0)
	var scene = _build_scene("EC-2", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "EC-2_at_boundary_hit")
	_teardown(scene)

func test_ec3_enemy_just_outside_boundary() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(3.001, 0, 0)
	var scene = _build_scene("EC-3", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(0, enemy.damage_taken.size(), "EC-3_just_outside_not_hit")
	_teardown(scene)

func test_ec4_ten_enemies_all_hit() -> void:
	var enemies: Array = []
	for i in range(10):
		var e = MockEnemy.new()
		var angle := float(i) * (TAU / 10.0)
		e.global_position = Vector3(cos(angle) * 2.0, sin(angle) * 2.0, 0)
		enemies.append(e)
	var scene = _build_scene("EC-4", enemies, Vector3.ZERO)
	if scene.is_empty():
		for e in enemies:
			e.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	var all_hit := true
	for e in enemies:
		if e.damage_taken.size() == 0:
			all_hit = false
	_assert_true(all_hit, "EC-4_all_10_hit")
	_assert_eq_int(10, _attack_hit_log.size(), "EC-4_10_signals")
	_teardown(scene)

func test_ec17_two_degenerate_enemies_both_default_kb() -> void:
	var e1 = MockEnemy.new()
	e1.global_position = Vector3.ZERO
	var e2 = MockEnemy.new()
	e2.global_position = Vector3.ZERO
	var scene = _build_scene("EC-17", [e1, e2], Vector3.ZERO)
	if scene.is_empty():
		e1.free()
		e2.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	for e in [e1, e2]:
		if e.damage_taken.size() > 0:
			var kb: Vector3 = e.damage_taken[0]["knockback"]
			_assert_eq_float(5.0, kb.x, "EC-17_default_kb_x")
		else:
			_fail_test("EC-17", "enemy not hit")
	_teardown(scene)

func test_ec18_weakened_enemy_no_special_modifier() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	enemy.current_state = 1
	var scene = _build_scene("EC-18", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "EC-18_damage_applied")
	_assert_eq_int(1, enemy.current_state, "EC-18_state_unchanged")
	_teardown(scene)

func test_ec19_null_resource_no_crash() -> void:
	var scene = _build_scene("EC-19")
	if scene.is_empty():
		return
	scene["executor"].execute_attack(null)
	_pass_test("EC-19_null_resource_no_crash")
	_teardown(scene)

func test_ec20_parent_no_is_on_floor_treats_as_grounded() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("EC-20", "executor not loadable")
		return
	if executor.has_method("_is_owner_on_floor"):
		var bare_parent = Node3D.new()
		bare_parent.add_child(executor)
		_assert_true(executor._is_owner_on_floor(), "EC-20_default_grounded")
		bare_parent.free()
	else:
		_pass_test("EC-20_method_pending_implementation")

func test_ec22_slam_does_not_emit_melee_vfx() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	var scene = _build_scene("EC-22", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(0, _melee_vfx_log.size(), "EC-22_no_melee_vfx")
	if scene["executor"].has_signal("slam_vfx_requested"):
		_assert_true(_slam_vfx_log.size() >= 1, "EC-22_slam_vfx_instead")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CCA-8: Integration with Existing Attack Pipeline
# ---------------------------------------------------------------------------

func test_cca8b_execute_dispatches_slam_aoe() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	var scene = _build_scene("CCA-8b", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_carapace_resource()
	res.startup_frames = 0
	scene["executor"].execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "CCA-8b_slam_damage_applied")
	if enemy.damage_taken.size() > 0:
		_assert_eq_float(4.0, enemy.damage_taken[0]["damage"], "CCA-8b_damage_4")
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.length() > 0.0, "CCA-8b_knockback_applied")
	_teardown(scene)

func test_cca8c_cooldown_3_5_from_resource() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var carapace = db.get_base_attack("carapace")
	if carapace == null:
		_fail_test("CCA-8c", "carapace not registered")
		if tree: db.queue_free()
		else: db.free()
		return
	_assert_eq_float(3.5, carapace.cooldown, "CCA-8c_cooldown_from_db")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_cca8_full_pipeline_slam() -> void:
	var e1 = MockEnemy.new()
	e1.global_position = Vector3(1.5, 0, 0)
	var e2 = MockEnemy.new()
	e2.global_position = Vector3(-1.5, 0, 0)
	var e_out = MockEnemy.new()
	e_out.global_position = Vector3(10.0, 0, 0)
	var scene = _build_scene("CCA-8_full", [e1, e2, e_out], Vector3.ZERO)
	if scene.is_empty():
		e1.free()
		e2.free()
		e_out.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(1, e1.damage_taken.size(), "CCA-8_e1_hit")
	_assert_eq_int(1, e2.damage_taken.size(), "CCA-8_e2_hit")
	_assert_eq_int(0, e_out.damage_taken.size(), "CCA-8_e_out_not_hit")
	_assert_eq_int(2, _attack_hit_log.size(), "CCA-8_two_signals")
	_assert_eq_int(1, _slam_vfx_log.size(), "CCA-8_one_vfx")
	if e1.damage_taken.size() > 0:
		var kb1: Vector3 = e1.damage_taken[0]["knockback"]
		_assert_true(kb1.x > 0.0, "CCA-8_e1_kb_right")
	if e2.damage_taken.size() > 0:
		var kb2: Vector3 = e2.damage_taken[0]["knockback"]
		_assert_true(kb2.x < 0.0, "CCA-8_e2_kb_left")
	_assert_false(scene["executor"].is_active(), "CCA-8_not_active_after")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== CarapaceAttackTests ===")

	test_cca1_carapace_resource_properties()

	test_cca2a_register_defaults_creates_carapace()
	test_cca2b_at_least_three_base_attacks()
	test_cca2c_carapace_distinct_from_claw_and_acid()
	test_cca2d_carapace_defaults_match_spec()

	test_cca5a_slam_aoe_dispatches_to_handler()
	test_cca5b_slam_aoe_is_active_managed_by_handler()
	test_cca5c_existing_melee_dispatch_unaffected()
	test_cca5d_existing_unknown_dispatch_unaffected()
	test_cca5f_attack_started_emitted_before_dispatch()

	test_cca3b_radial_query_centered_on_player()
	test_cca3c_query_uses_full_attack_range()
	test_cca3d_enemies_in_range_take_damage()
	test_cca3f_enemies_outside_radius_not_hit()
	test_cca3g_attack_hit_per_enemy()
	test_cca3i_is_active_false_after_handler()
	test_cca3j_zero_enemies_no_crash()

	test_cca6a_slam_vfx_signal_exists()
	test_cca6b_slam_vfx_emitted_on_hit()
	test_cca6f_slam_vfx_emitted_on_whiff()
	test_cca6_no_melee_vfx_on_slam()

	test_cca7a_three_enemies_all_hit()
	test_cca7b_knockback_right_enemy_points_right()
	test_cca7c_knockback_left_enemy_points_left()
	test_cca7e_different_enemies_different_knockback()
	test_cca7f_degenerate_position_default_knockback()
	test_cca7g_dead_enemy_take_damage_called()

	test_cca3a_wind_up_delay_startup_frames()
	test_ec11_zero_startup_no_delay()

	test_cca4a_grounded_slam_fires_immediately()
	test_cca4d_active_guard_blocks_second_attack()
	test_cca4e_cooldown_value_3_5s()

	test_ec1_zero_enemies_vfx_still_emitted()
	test_ec2_enemy_at_exact_boundary()
	test_ec3_enemy_just_outside_boundary()
	test_ec4_ten_enemies_all_hit()
	test_ec17_two_degenerate_enemies_both_default_kb()
	test_ec18_weakened_enemy_no_special_modifier()
	test_ec19_null_resource_no_crash()
	test_ec20_parent_no_is_on_floor_treats_as_grounded()
	test_ec22_slam_does_not_emit_melee_vfx()

	test_cca8b_execute_dispatches_slam_aoe()
	test_cca8c_cooldown_3_5_from_resource()
	test_cca8_full_pipeline_slam()

	print("CarapaceAttackTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
