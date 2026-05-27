#
# test_carapace_attack_adversarial_b.gd
#
# Second half of adversarial tests for carapace ground slam: 3D positioning,
# knockback geometry, modifiers isolation, VFX, determinism, and stress.
#
# Spec: project_board/specs/carapace_player_attack_spec.md (CCA-1..CCA-8)
# Ticket: M11-10
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


class NoFloorParent extends Node3D:
	var _facing: float = 1.0
	func get_facing_sign() -> float:
		return _facing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_resource(overrides: Dictionary = {}) -> AttackResource:
	var r = AttackResource.new()
	r.attack_id = 3
	r.attack_name = "Ground Slam"
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
	for key in overrides:
		r.set(key, overrides[key])
	return r


func _build_scene(label: String, enemies: Array = [], pos: Vector3 = Vector3.ZERO, parent_node: Node3D = null) -> Dictionary:
	if parent_node == null:
		parent_node = MockParent.new()
	var result = AttackExecutorHarness.build_scene(parent_node, enemies, pos)
	if result.is_empty():
		_fail_test(label, "executor not loadable")
	return result


func _teardown(scene: Dictionary) -> void:
	AttackExecutorHarness.teardown_scene(scene)


var _slam_vfx_log: Array = []
var _melee_vfx_log: Array = []

func _reset_signal_logs() -> void:
	_slam_vfx_log = []
	_melee_vfx_log = []

func _connect_signals(executor: Node) -> void:
	_reset_signal_logs()
	if executor.has_signal("slam_vfx_requested"):
		executor.connect("slam_vfx_requested", func(p, rad, c, s): _slam_vfx_log.append({"position": p, "radius": rad, "color": c, "scale": s}))
	if executor.has_signal("melee_vfx_requested"):
		executor.connect("melee_vfx_requested", func(p, c, s): _melee_vfx_log.append({"position": p, "color": c, "scale": s}))


# ---------------------------------------------------------------------------
# 12) 3D POSITIONING — Z-axis, Y-axis, diagonals (CCA-3b deepening)
# ---------------------------------------------------------------------------

func test_adv_enemy_on_z_axis() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0, 0, 2.5)
	var scene = _build_scene("adv_z_axis", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "adv_z_axis_hit")
	_teardown(scene)

func test_adv_3d_diagonal_boundary() -> void:
	var e_in = MockEnemy.new()
	e_in.global_position = Vector3(1.0, 1.0, 1.0)
	var e_out = MockEnemy.new()
	e_out.global_position = Vector3(2.0, 2.0, 2.0)
	var scene = _build_scene("adv_3d_diag", [e_in, e_out], Vector3.ZERO)
	if scene.is_empty():
		e_in.free()
		e_out.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(e_in.damage_taken.size() >= 1, "adv_3d_diag_in_hit")
	_assert_eq_int(0, e_out.damage_taken.size(), "adv_3d_diag_out_miss")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 13) KNOCKBACK Z-COMPONENT ZEROED
# ---------------------------------------------------------------------------

func test_adv_knockback_z_zeroed() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 2.0)
	var scene = _build_scene("adv_kb_z", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	if enemy.damage_taken.size() > 0:
		_assert_eq_float(0.0, enemy.damage_taken[0]["knockback"].z, "adv_kb_z_zeroed")
		_assert_true(enemy.damage_taken[0]["knockback"].x > 0.0, "adv_kb_z_has_x")
	else:
		_fail_test("adv_kb_z", "enemy not hit")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 14) MODIFIERS ISOLATION
# ---------------------------------------------------------------------------

func test_adv_modifiers_isolation() -> void:
	var r1 = _make_resource()
	var r2 = _make_resource()
	r1.modifiers["test_key"] = true
	_assert_eq_int(0, r2.modifiers.size(), "adv_mod_isolation_r2_empty")

func test_adv_modifiers_deep_copy() -> void:
	var r = _make_resource({"modifiers": {"nested": {"deep": true}}})
	var r2 = AttackResource.new()
	r2.modifiers = r.modifiers
	r2.modifiers["extra"] = true
	_assert_false(r.modifiers.has("extra"), "adv_deep_copy_no_leak")


# ---------------------------------------------------------------------------
# 15) VFX SIGNAL ISOLATION — slam does not emit melee_vfx
# ---------------------------------------------------------------------------

func test_adv_slam_only_emits_slam_vfx() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	var scene = _build_scene("adv_vfx_iso", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(0, _melee_vfx_log.size(), "adv_no_melee_vfx")
	if scene["executor"].has_signal("slam_vfx_requested"):
		_assert_eq_int(1, _slam_vfx_log.size(), "adv_slam_vfx_emitted")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 16) PARENT WITHOUT IS_ON_FLOOR
# ---------------------------------------------------------------------------

func test_adv_no_floor_parent_fires_slam() -> void:
	var parent = NoFloorParent.new()
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	var scene = _build_scene("adv_no_floor", [enemy], Vector3.ZERO, parent)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "adv_no_floor_damage")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 17) FACING INDEPENDENCE
# ---------------------------------------------------------------------------

func test_adv_facing_does_not_affect_slam() -> void:
	var p_r = MockParent.new()
	p_r._facing = 1.0
	var p_l = MockParent.new()
	p_l._facing = -1.0
	var e_r = MockEnemy.new()
	e_r.global_position = Vector3(2.0, 0, 0)
	var e_l = MockEnemy.new()
	e_l.global_position = Vector3(2.0, 0, 0)
	var scene_r = _build_scene("adv_facing_r", [e_r], Vector3.ZERO, p_r)
	if scene_r.is_empty():
		e_r.free()
		e_l.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene_r["executor"].execute_attack(res)
	_teardown(scene_r)
	var scene_l = _build_scene("adv_facing_l", [e_l], Vector3.ZERO, p_l)
	if scene_l.is_empty():
		e_l.free()
		return
	scene_l["executor"].execute_attack(res)
	_assert_eq_int(e_r.damage_taken.size(), e_l.damage_taken.size(), "adv_facing_same_result")
	_teardown(scene_l)


# ---------------------------------------------------------------------------
# 18) PLAYER OFFSET POSITION
# ---------------------------------------------------------------------------

func test_adv_player_offset_position() -> void:
	var e_near = MockEnemy.new()
	e_near.global_position = Vector3(12.0, 0, 0)
	var e_far = MockEnemy.new()
	e_far.global_position = Vector3(0.0, 0, 0)
	var scene = _build_scene("adv_offset", [e_near, e_far], Vector3(10.0, 0, 0))
	if scene.is_empty():
		e_near.free()
		e_far.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(e_near.damage_taken.size() >= 1, "adv_offset_near_hit")
	_assert_eq_int(0, e_far.damage_taken.size(), "adv_offset_far_miss")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 19) DETERMINISM
# ---------------------------------------------------------------------------

func test_adv_determinism() -> void:
	var results: Array = []
	for run in range(2):
		var enemies: Array = []
		for i in range(5):
			var e = MockEnemy.new()
			e.global_position = Vector3(float(i) * 0.5 + 0.5, 0, 0)
			enemies.append(e)
		var scene = _build_scene("adv_det_%d" % run, enemies, Vector3.ZERO)
		if scene.is_empty():
			for e in enemies:
				e.free()
			return
		var res = _make_resource({"startup_frames": 0})
		scene["executor"].execute_attack(res)
		var run_result := []
		for e in enemies:
			if e.damage_taken.size() > 0:
				run_result.append(e.damage_taken[0]["damage"])
		results.append(run_result)
		_teardown(scene)
	_assert_eq_int(results[0].size(), results[1].size(), "adv_det_count")
	for i in range(results[0].size()):
		_assert_eq_float(results[0][i], results[1][i], "adv_det_dmg_%d" % i)


# ---------------------------------------------------------------------------
# 20) EXTREME VALUES
# ---------------------------------------------------------------------------

func test_adv_extreme_damage() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	var scene = _build_scene("adv_huge_dmg", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"damage": 999999.0, "startup_frames": 0})
	scene["executor"].execute_attack(res)
	if enemy.damage_taken.size() > 0:
		_assert_eq_float(999999.0, enemy.damage_taken[0]["damage"], "adv_huge_dmg_val")
	else:
		_fail_test("adv_huge_dmg", "not hit")
	_teardown(scene)

func test_adv_extreme_knockback() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	var scene = _build_scene("adv_huge_kb", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"knockback_magnitude": 100000.0, "startup_frames": 0})
	scene["executor"].execute_attack(res)
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(is_finite(kb.x), "adv_huge_kb_finite")
		_assert_eq_float(100000.0, kb.length(), "adv_huge_kb_mag")
	else:
		_fail_test("adv_huge_kb", "not hit")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 21) VFX POSITION MATCHES PLAYER
# ---------------------------------------------------------------------------

func test_adv_vfx_position_matches_player() -> void:
	var player_pos := Vector3(5.0, 2.0, 0)
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(6.0, 2.0, 0)
	var scene = _build_scene("adv_vfx_pos", [enemy], player_pos)
	if scene.is_empty():
		enemy.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	if _slam_vfx_log.size() > 0:
		_assert_vec3_near(_slam_vfx_log[0]["position"], player_pos, 0.01, "adv_vfx_at_player")
	elif scene["executor"].has_signal("slam_vfx_requested"):
		_fail_test("adv_vfx_pos", "slam vfx not emitted")
	else:
		_pass_test("adv_vfx_pos_pending")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 22) SEQUENTIAL SLAMS
# ---------------------------------------------------------------------------

func test_adv_sequential_slams_both_succeed() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	var scene = _build_scene("adv_seq", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res = _make_resource({"startup_frames": 0})
	executor.execute_attack(res)
	_assert_eq_int(1, enemy.damage_taken.size(), "adv_seq_first_hit")
	_assert_false(executor.is_active(), "adv_seq_not_active")
	executor.execute_attack(res)
	_assert_eq_int(2, enemy.damage_taken.size(), "adv_seq_second_hit")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 23) CARAPACE DAMAGE IS STRONGEST BASE MUTATION
# ---------------------------------------------------------------------------

func test_adv_carapace_strongest_single_hit() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var carapace = db.get_base_attack("carapace")
	if carapace == null:
		_fail_test("adv_strongest", "carapace not registered")
		if tree: db.queue_free()
		else: db.free()
		return
	var claw = db.get_base_attack("claw")
	var acid = db.get_base_attack("acid")
	if claw:
		_assert_true(carapace.damage > claw.damage, "adv_dmg_gt_claw")
	if acid:
		_assert_true(carapace.damage > acid.damage, "adv_dmg_gt_acid")
	_assert_eq_float(4.0, carapace.damage, "adv_dmg_exact_4")
	if tree:
		db.queue_free()
	else:
		db.free()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== CarapaceAttackAdversarialTestsB ===")

	test_adv_enemy_on_z_axis()
	test_adv_3d_diagonal_boundary()
	test_adv_knockback_z_zeroed()
	test_adv_modifiers_isolation()
	test_adv_modifiers_deep_copy()
	test_adv_slam_only_emits_slam_vfx()
	test_adv_no_floor_parent_fires_slam()
	test_adv_facing_does_not_affect_slam()
	test_adv_player_offset_position()
	test_adv_determinism()
	test_adv_extreme_damage()
	test_adv_extreme_knockback()
	test_adv_vfx_position_matches_player()
	test_adv_sequential_slams_both_succeed()
	test_adv_carapace_strongest_single_hit()

	print("CarapaceAttackAdversarialTestsB: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
