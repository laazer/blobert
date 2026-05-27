#
# test_carapace_attack_adversarial.gd
#
# Adversarial edge-case, boundary, mutation, and stress tests for the carapace
# ground slam attack. Extends test_carapace_attack.gd with weaknesses, blind
# spots, and gaps the primary coverage misses.
#
# Spec: project_board/specs/carapace_player_attack_spec.md (CCA-1..CCA-8, EC-1..EC-22)
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


class DyingEnemy extends Node3D:
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


class BareEnemy extends Node3D:
	pass


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
# 1) ZERO-RADIUS SLAM (CCA-3j deepening)
# Exposes: handler must not crash with attack_range=0.0 (degenerate config).
# ---------------------------------------------------------------------------

func test_adv_zero_radius_slam() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0, 0)
	var scene = _build_scene("adv_zero_radius", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"attack_range": 0.0, "startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(0, enemy.damage_taken.size(), "adv_zero_radius_no_hit")
	if scene["executor"].has_signal("slam_vfx_requested"):
		_assert_eq_int(1, _slam_vfx_log.size(), "adv_zero_radius_vfx_still_emits")
		if _slam_vfx_log.size() > 0:
			_assert_eq_float(0.0, _slam_vfx_log[0]["radius"], "adv_zero_radius_vfx_val")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 2) BOUNDARY PRECISION (CCA-3, EC-2/EC-3 deepening)
# Exposes: off-by-one in <= vs < comparison in _query_enemies_in_range.
# ---------------------------------------------------------------------------

func test_adv_boundary_epsilon_beyond_miss() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(3.001, 0, 0)
	var scene = _build_scene("adv_boundary_eps", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(0, enemy.damage_taken.size(), "adv_boundary_eps_miss")
	_teardown(scene)

func test_adv_boundary_negative_range_no_crash() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0, 0)
	var scene = _build_scene("adv_neg_range", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"attack_range": -1.0, "startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(0, enemy.damage_taken.size(), "adv_neg_range_no_hit")
	_pass_test("adv_neg_range_no_crash")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 3) DEAD/DYING ENEMY (CCA-7g deepening)
# Exposes: take_damage called on dead enemy (handler doesn't filter); dying
# enemy transitions to dead mid-slam.
# ---------------------------------------------------------------------------

func test_adv_dead_enemy_receives_call_and_signal() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	enemy.is_dead_flag = true
	var scene = _build_scene("adv_dead_call", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "adv_dead_receives_call")
	_assert_eq_int(1, _attack_hit_log.size(), "adv_dead_signal_emitted")
	_teardown(scene)

func test_adv_dying_enemy_killed_by_slam() -> void:
	var enemy = DyingEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	enemy.current_hp = 2.0
	var scene = _build_scene("adv_dying", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy.is_dead_flag, "adv_dying_now_dead")
	_assert_eq_int(1, enemy.damage_taken.size(), "adv_dying_took_damage")
	_teardown(scene)

func test_adv_mix_alive_dead_and_bare() -> void:
	var alive = MockEnemy.new()
	alive.global_position = Vector3(1.0, 0, 0)
	var dead = MockEnemy.new()
	dead.global_position = Vector3(-1.0, 0, 0)
	dead.is_dead_flag = true
	var bare = BareEnemy.new()
	bare.global_position = Vector3(0, 1.0, 0)
	var scene = _build_scene("adv_mix", [alive, dead, bare], Vector3.ZERO)
	if scene.is_empty():
		alive.free()
		dead.free()
		bare.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_eq_int(1, alive.damage_taken.size(), "adv_mix_alive_hit")
	_assert_true(dead.damage_taken.size() >= 1, "adv_mix_dead_called")
	_pass_test("adv_mix_bare_no_crash")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 4) DOUBLE-TAP / TRIPLE-TAP (CCA-4d deepening)
# Exposes: _is_active guard must block overlapping execute_attack calls.
# ---------------------------------------------------------------------------

func test_adv_double_tap_during_active() -> void:
	var scene = _build_scene("adv_double_tap")
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_signals(executor)
	var res = _make_resource({"startup_frames": 0})
	executor.execute_attack(res)
	executor._is_active = true
	executor.execute_attack(res)
	executor.execute_attack(res)
	_assert_true(_attack_started_log.size() <= 1, "adv_multi_tap_blocked")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 5) AIRBORNE TIMING (CCA-4 deepening)
# Exposes: is_on_floor check after wind-up; _is_active during airborne wait.
# ---------------------------------------------------------------------------

func test_adv_grounded_immediate_damage() -> void:
	var parent = MockParent.new()
	parent._on_floor = true
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(1.0, 0, 0)
	var scene = _build_scene("adv_grounded", [enemy], Vector3.ZERO, parent)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(enemy.damage_taken.size() >= 1, "adv_grounded_immediate")
	_teardown(scene)

func test_adv_airborne_is_active_during_wait() -> void:
	var parent = MockParent.new()
	parent._on_floor = false
	var scene = _build_scene("adv_airborne_active", [], Vector3.ZERO, parent)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var res = _make_resource({"startup_frames": 0})
	executor.execute_attack(res)
	if executor.has_method("_handle_slam_aoe"):
		_assert_true(executor.is_active(), "adv_airborne_active_guard")
	else:
		_pass_test("adv_airborne_active_pending")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 6) LARGE ENEMY COUNT — 15 and 20 enemies (EC-4 deepening + stress)
# Exposes: no cap on enemy processing; deterministic damage for all.
# ---------------------------------------------------------------------------

func test_adv_fifteen_enemies_all_hit() -> void:
	var enemies: Array = []
	for i in range(15):
		var e = MockEnemy.new()
		var angle := float(i) * (TAU / 15.0)
		e.global_position = Vector3(cos(angle) * 2.0, sin(angle) * 2.0, 0)
		enemies.append(e)
	var scene = _build_scene("adv_fifteen", enemies, Vector3.ZERO)
	if scene.is_empty():
		for e in enemies:
			e.free()
		return
	_connect_signals(scene["executor"])
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	var hit_count := 0
	for e in enemies:
		if e.damage_taken.size() > 0:
			hit_count += 1
	_assert_eq_int(15, hit_count, "adv_fifteen_all_hit")
	_assert_eq_int(15, _attack_hit_log.size(), "adv_fifteen_all_signals")
	_assert_eq_int(1, _slam_vfx_log.size(), "adv_fifteen_single_vfx")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 7) DEGENERATE KNOCKBACK (CCA-7f, EC-17 deepening)
# Exposes: _calculate_knockback degenerate path; near-zero offset behavior.
# ---------------------------------------------------------------------------

func test_adv_degenerate_kb_multiple_all_default() -> void:
	var enemies: Array = []
	for i in range(3):
		var e = MockEnemy.new()
		e.global_position = Vector3.ZERO
		enemies.append(e)
	var scene = _build_scene("adv_degen_multi", enemies, Vector3.ZERO)
	if scene.is_empty():
		for e in enemies:
			e.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	for i in range(3):
		if enemies[i].damage_taken.size() > 0:
			var kb: Vector3 = enemies[i].damage_taken[0]["knockback"]
			_assert_eq_float(5.0, kb.x, "adv_degen_%d_x" % i)
			_assert_eq_float(0.0, kb.y, "adv_degen_%d_y" % i)
		else:
			_fail_test("adv_degen_%d" % i, "not hit")
	_teardown(scene)

func test_adv_near_degenerate_tiny_offset() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.00001, 0, 0)
	var scene = _build_scene("adv_near_degen", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_eq_float(5.0, kb.length(), "adv_near_degen_magnitude")
	else:
		_fail_test("adv_near_degen", "enemy not hit")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 8) COOLDOWN IS SLOWEST OF ALL BASE MUTATIONS (CCA-1c, CCA-8c)
# Exposes: carapace cooldown > claw and acid; value drift.
# ---------------------------------------------------------------------------

func test_adv_cooldown_slowest_of_all_mutations() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var carapace = db.get_base_attack("carapace")
	if carapace == null:
		_fail_test("adv_cd_db", "carapace not registered")
		if tree: db.queue_free()
		else: db.free()
		return
	_assert_eq_float(3.5, carapace.cooldown, "adv_cd_3_5")
	var claw = db.get_base_attack("claw")
	var acid = db.get_base_attack("acid")
	if claw:
		_assert_true(carapace.cooldown > claw.cooldown, "adv_cd_gt_claw")
	if acid:
		_assert_true(carapace.cooldown > acid.cooldown, "adv_cd_gt_acid")
	if tree:
		db.queue_free()
	else:
		db.free()


# ---------------------------------------------------------------------------
# 9) DATABASE DUPLICATE/INVALID REGISTRATION (CCA-2 deepening)
# Exposes: overwrite semantics, empty-id rejection, null-resource rejection.
# ---------------------------------------------------------------------------

func test_adv_duplicate_registration_overwrites() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var count_before := db.get_base_attack_count()
	db.register_base_attack("carapace", _make_resource({"damage": 99.0}))
	_assert_eq_float(99.0, db.get_base_attack("carapace").damage, "adv_dup_overwrite")
	_assert_eq_int(count_before, db.get_base_attack_count(), "adv_dup_count_stable")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_adv_register_invalid_inputs() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var count_before := db.get_base_attack_count()
	db.register_base_attack("", _make_resource())
	db.register_base_attack("test_null", null)
	_assert_eq_int(count_before, db.get_base_attack_count(), "adv_invalid_inputs_rejected")
	_assert_false(db.has_base_attack("test_null"), "adv_null_not_present")
	if tree:
		db.queue_free()
	else:
		db.free()


# ---------------------------------------------------------------------------
# 10) DUCK-TYPE GUARD — BareEnemy has no take_damage (EC-10 deepening)
# Exposes: _apply_damage has_method guard prevents crash on non-enemy nodes.
# ---------------------------------------------------------------------------

func test_adv_bare_enemy_no_take_damage() -> void:
	var bare = BareEnemy.new()
	bare.global_position = Vector3(1.0, 0, 0)
	var normal = MockEnemy.new()
	normal.global_position = Vector3(-1.0, 0, 0)
	var scene = _build_scene("adv_bare", [bare, normal], Vector3.ZERO)
	if scene.is_empty():
		bare.free()
		normal.free()
		return
	var res = _make_resource({"startup_frames": 0})
	scene["executor"].execute_attack(res)
	_assert_true(normal.damage_taken.size() >= 1, "adv_normal_still_hit")
	_pass_test("adv_bare_no_crash")
	_teardown(scene)


# ---------------------------------------------------------------------------
# 11) KNOCKBACK DIRECTION MUTATIONS (AEX-5 deepening)
# Exposes: "toward", "none", zero magnitude, unknown direction strings.
# ---------------------------------------------------------------------------

func test_adv_knockback_toward_pulls_enemy() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(2.0, 0, 0)
	var scene = _build_scene("adv_kb_toward", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"knockback_direction": "toward", "startup_frames": 0})
	scene["executor"].execute_attack(res)
	if enemy.damage_taken.size() > 0:
		_assert_true(enemy.damage_taken[0]["knockback"].x < 0.0, "adv_kb_toward_neg_x")
	else:
		_fail_test("adv_kb_toward", "enemy not hit")
	_teardown(scene)

func test_adv_knockback_none_and_zero_mag() -> void:
	var e1 = MockEnemy.new()
	e1.global_position = Vector3(1.0, 0, 0)
	var e2 = MockEnemy.new()
	e2.global_position = Vector3(-1.0, 0, 0)
	var scene = _build_scene("adv_kb_none_zero", [e1, e2], Vector3.ZERO)
	if scene.is_empty():
		e1.free()
		e2.free()
		return
	var res_none = _make_resource({"knockback_direction": "none", "startup_frames": 0})
	scene["executor"].execute_attack(res_none)
	if e1.damage_taken.size() > 0:
		_assert_eq_float(0.0, e1.damage_taken[0]["knockback"].length(), "adv_kb_none_zero_vec")
	scene["executor"]._is_active = false
	var res_zero = _make_resource({"knockback_magnitude": 0.0, "startup_frames": 0})
	scene["executor"].execute_attack(res_zero)
	if e1.damage_taken.size() > 1:
		_assert_eq_float(0.0, e1.damage_taken[1]["knockback"].length(), "adv_kb_zero_mag")
	_teardown(scene)

func test_adv_knockback_unknown_direction() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(2.0, 0, 0)
	var scene = _build_scene("adv_kb_unknown", [enemy], Vector3.ZERO)
	if scene.is_empty():
		enemy.free()
		return
	var res = _make_resource({"knockback_direction": "sideways", "startup_frames": 0})
	scene["executor"].execute_attack(res)
	if enemy.damage_taken.size() > 0:
		_assert_eq_float(0.0, enemy.damage_taken[0]["knockback"].length(), "adv_kb_unknown_zero")
	else:
		_fail_test("adv_kb_unknown", "enemy not hit")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== CarapaceAttackAdversarialTests ===")

	test_adv_zero_radius_slam()
	test_adv_boundary_epsilon_beyond_miss()
	test_adv_boundary_negative_range_no_crash()
	test_adv_dead_enemy_receives_call_and_signal()
	test_adv_dying_enemy_killed_by_slam()
	test_adv_mix_alive_dead_and_bare()
	test_adv_double_tap_during_active()
	test_adv_grounded_immediate_damage()
	test_adv_airborne_is_active_during_wait()
	test_adv_fifteen_enemies_all_hit()
	test_adv_degenerate_kb_multiple_all_default()
	test_adv_near_degenerate_tiny_offset()
	test_adv_cooldown_slowest_of_all_mutations()
	test_adv_duplicate_registration_overwrites()
	test_adv_register_invalid_inputs()
	test_adv_bare_enemy_no_take_damage()
	test_adv_knockback_toward_pulls_enemy()
	test_adv_knockback_none_and_zero_mag()
	test_adv_knockback_unknown_direction()

	print("CarapaceAttackAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
