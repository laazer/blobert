#
# test_verify_damage_knockback.gd
#
# Behavioral verification tests for damage/knockback delivery across the
# attack system: AttackDatabaseNode → AttackExecutor → PlayerProjectile3D.
# Spec: project_board/specs/verify_damage_knockback_spec.md (VDK-1..VDK-5)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/13_verify_damage_knockback.md
#

class_name VerifyDamageKnockbackTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Mock inner classes (same contract as existing attack tests)
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


func _get_signal_data(signal_name: String, index: int = 0) -> Dictionary:
	var count := 0
	for entry in _signals_log:
		if entry["name"] == signal_name:
			if count == index:
				return entry
			count += 1
	return {}


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
# VDK-1: Cross-Mutation Integration — DB → Executor Pipeline (AC-1a..AC-1e)
# ---------------------------------------------------------------------------

func test_vdk1a_claw_melee_pipeline() -> void:
	var db := AttackDatabaseNode.new()
	var res := _make_resource({
		"attack_id": 101, "attack_name": "Claw Swipe",
		"effect_type": "MELEE_SWIPE", "damage": 2.0,
		"knockback_magnitude": 100.0, "knockback_direction": "away",
		"attack_range": 8.0
	})
	db.register_base_attack("claw", res)
	var retrieved = db.get_base_attack("claw")
	_assert_true(retrieved != null, "VDK-1a_retrieved")
	if retrieved == null:
		db.free()
		return

	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(3.0, 0.0, 0.0)
	var scene := _build_scene("VDK-1a", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		db.free()
		return
	var executor = scene["executor"]
	executor.execute_attack(retrieved)
	_assert_true(enemy.damage_taken.size() > 0, "VDK-1a_damage_called")
	if enemy.damage_taken.size() > 0:
		_assert_eq_float(2.0, enemy.damage_taken[0]["damage"], "VDK-1a_damage_value")
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.x > 0.0, "VDK-1a_knockback_away_positive_x")
	_teardown(scene)
	db.free()


func test_vdk1b_acid_projectile_pipeline() -> void:
	var db := AttackDatabaseNode.new()
	var mods := {"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.3}
	var res := _make_resource({
		"attack_id": 102, "attack_name": "Acid Spit",
		"effect_type": "PROJECTILE_SPIT", "damage": 1.5,
		"projectile_speed": 250.0, "modifiers": mods
	})
	db.register_base_attack("acid", res)
	var retrieved = db.get_base_attack("acid")
	_assert_true(retrieved != null, "VDK-1b_retrieved")
	if retrieved == null:
		db.free()
		return

	var scene := _build_scene("VDK-1b", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		db.free()
		return
	var executor = scene["executor"]
	var scene_root = scene["root"]
	var children_before: int = scene_root.get_child_count()
	executor.execute_attack(retrieved)
	_assert_true(scene_root.get_child_count() > children_before, "VDK-1b_projectile_created")
	if scene_root.get_child_count() > children_before:
		var proj = scene_root.get_child(scene_root.get_child_count() - 1)
		_assert_eq_float(1.5, proj.damage, "VDK-1b_proj_damage")
		_assert_eq_float(250.0, proj.speed, "VDK-1b_proj_speed")
		_assert_true(proj.modifiers.get("acid_on_hit", false) == true, "VDK-1b_proj_acid_mod")
	_teardown(scene)
	db.free()


func test_vdk1c_carapace_unknown_handler() -> void:
	var db := AttackDatabaseNode.new()
	var res := _make_resource({
		"attack_id": 103, "attack_name": "Carapace Slam",
		"effect_type": "SLAM_AOE", "damage": 3.0
	})
	db.register_base_attack("carapace", res)
	var retrieved = db.get_base_attack("carapace")

	var scene := _build_scene("VDK-1c", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		db.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.execute_attack(retrieved)
	_assert_false(executor.is_active(), "VDK-1c_active_reset")
	_assert_eq_int(1, _count_signal("attack_started"), "VDK-1c_started_emitted")
	_assert_eq_int(0, _count_signal("attack_hit"), "VDK-1c_no_hit")
	_teardown(scene)
	db.free()


func test_vdk1d_adhesion_unknown_handler() -> void:
	var db := AttackDatabaseNode.new()
	var res := _make_resource({
		"attack_id": 104, "attack_name": "Adhesion Lunge",
		"effect_type": "LUNGE", "modifiers": {"root_duration": 0.5}
	})
	db.register_base_attack("adhesion", res)
	var retrieved = db.get_base_attack("adhesion")

	var scene := _build_scene("VDK-1d", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		db.free()
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.execute_attack(retrieved)
	_assert_false(executor.is_active(), "VDK-1d_active_reset")
	_assert_eq_int(1, _count_signal("attack_started"), "VDK-1d_started_emitted")
	_assert_eq_int(0, _count_signal("attack_hit"), "VDK-1d_no_hit")
	_assert_eq_float(0.5, retrieved.modifiers.get("root_duration", 0.0), "VDK-1d_modifiers_preserved")
	_teardown(scene)
	db.free()


func test_vdk1e_property_preservation() -> void:
	var db := AttackDatabaseNode.new()
	var configs: Array = [
		{"mid": "claw", "attack_name": "Claw Swipe", "damage": 2.0, "cooldown": 0.8,
		 "attack_range": 8.0, "knockback_magnitude": 100.0, "knockback_direction": "away",
		 "modifiers": {}},
		{"mid": "acid", "attack_name": "Acid Spit", "damage": 1.5, "cooldown": 1.2,
		 "attack_range": 12.0, "knockback_magnitude": 50.0, "knockback_direction": "away",
		 "modifiers": {"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.3}},
		{"mid": "carapace", "attack_name": "Carapace Slam", "damage": 3.0, "cooldown": 1.5,
		 "attack_range": 3.0, "knockback_magnitude": 80.0, "knockback_direction": "away",
		 "modifiers": {}},
		{"mid": "adhesion", "attack_name": "Adhesion Lunge", "damage": 1.0, "cooldown": 2.0,
		 "attack_range": 6.0, "knockback_magnitude": 60.0, "knockback_direction": "toward",
		 "modifiers": {"root_duration": 0.5}},
	]
	for cfg in configs:
		var r := _make_resource({
			"attack_name": cfg["attack_name"], "damage": cfg["damage"],
			"cooldown": cfg["cooldown"], "attack_range": cfg["attack_range"],
			"knockback_magnitude": cfg["knockback_magnitude"],
			"knockback_direction": cfg["knockback_direction"],
			"modifiers": cfg["modifiers"],
		})
		db.register_base_attack(cfg["mid"], r)
	for cfg in configs:
		var mid: String = cfg["mid"]
		var r = db.get_base_attack(mid)
		var label := "VDK-1e_" + mid
		_assert_true(r != null, label + "_not_null")
		if r == null:
			continue
		_assert_eq_string(cfg["attack_name"], r.attack_name, label + "_name")
		_assert_eq_float(cfg["damage"], r.damage, label + "_damage")
		_assert_eq_float(cfg["cooldown"], r.cooldown, label + "_cooldown")
		_assert_eq_float(cfg["attack_range"], r.attack_range, label + "_range")
		_assert_eq_float(cfg["knockback_magnitude"], r.knockback_magnitude, label + "_kb_mag")
		_assert_eq_string(cfg["knockback_direction"], r.knockback_direction, label + "_kb_dir")
	var acid_r = db.get_base_attack("acid")
	if acid_r:
		_assert_true(acid_r.modifiers.get("acid_on_hit", false) == true, "VDK-1e_acid_mod_aoh")
		_assert_eq_float(2.0, acid_r.modifiers.get("acid_duration", 0.0), "VDK-1e_acid_mod_dur")
	var adh_r = db.get_base_attack("adhesion")
	if adh_r:
		_assert_eq_float(0.5, adh_r.modifiers.get("root_duration", 0.0), "VDK-1e_adh_mod_root")
	db.free()


# ---------------------------------------------------------------------------
# VDK-2: VFX Spawn Position Correctness (AC-2a..AC-2d)
# ---------------------------------------------------------------------------

func test_vdk2a_vfx_facing_right() -> void:
	var scene := _build_scene("VDK-2a", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "attack_range": 4.0})
	executor.execute_attack(res)
	var vfx := _get_signal_data("melee_vfx_requested")
	_assert_true(vfx.size() > 0, "VDK-2a_vfx_emitted")
	if vfx.size() > 0:
		var pos: Vector3 = vfx["position"]
		_assert_vec3_near(pos, Vector3(2.0, 0.0, 0.0), 0.01, "VDK-2a_position")
	_teardown(scene)


func test_vdk2b_vfx_facing_left() -> void:
	var scene := _build_scene("VDK-2b", [], Vector3(10.0, 0.0, 0.0), -1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "attack_range": 6.0})
	executor.execute_attack(res)
	var vfx := _get_signal_data("melee_vfx_requested")
	_assert_true(vfx.size() > 0, "VDK-2b_vfx_emitted")
	if vfx.size() > 0:
		var pos: Vector3 = vfx["position"]
		_assert_vec3_near(pos, Vector3(7.0, 0.0, 0.0), 0.01, "VDK-2b_position")
	_teardown(scene)


func test_vdk2c_vfx_nonzero_y() -> void:
	var scene := _build_scene("VDK-2c", [], Vector3(5.0, 3.0, 0.0), 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "attack_range": 2.0})
	executor.execute_attack(res)
	var vfx := _get_signal_data("melee_vfx_requested")
	_assert_true(vfx.size() > 0, "VDK-2c_vfx_emitted")
	if vfx.size() > 0:
		var pos: Vector3 = vfx["position"]
		_assert_vec3_near(pos, Vector3(6.0, 3.0, 0.0), 0.01, "VDK-2c_position")
	_teardown(scene)


func test_vdk2d_vfx_zero_range() -> void:
	var scene := _build_scene("VDK-2d", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "attack_range": 0.0})
	executor.execute_attack(res)
	var vfx := _get_signal_data("melee_vfx_requested")
	_assert_true(vfx.size() > 0, "VDK-2d_vfx_emitted")
	if vfx.size() > 0:
		var pos: Vector3 = vfx["position"]
		_assert_vec3_near(pos, Vector3.ZERO, 0.01, "VDK-2d_position")
	_teardown(scene)


# ---------------------------------------------------------------------------
# VDK-3: PlayerProjectile3D On-Hit Behavior (AC-3a..AC-3j)
# ---------------------------------------------------------------------------

func test_vdk3a_damage_on_hit_away() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 5.0
	proj.knockback_magnitude = 10.0
	proj.knockback_direction = "away"
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(8.0, 0.0, 0.0)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(10.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.damage_taken.size(), "VDK-3a_damage_called")
	if enemy.damage_taken.size() > 0:
		_assert_eq_float(5.0, enemy.damage_taken[0]["damage"], "VDK-3a_damage_value")
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.x > 0.0, "VDK-3a_knockback_away_positive_x")
	_free_root(root)


func test_vdk3b_knockback_toward() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 3.0
	proj.knockback_magnitude = 8.0
	proj.knockback_direction = "toward"
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(8.0, 0.0, 0.0)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(10.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.damage_taken.size(), "VDK-3b_damage_called")
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.x < 0.0, "VDK-3b_knockback_toward_negative_x")
	_free_root(root)


func test_vdk3c_zero_knockback() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 2.0
	proj.knockback_magnitude = 0.0
	proj.knockback_direction = "away"
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(5.0, 0.0, 0.0)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(8.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.damage_taken.size(), "VDK-3c_damage_called")
	if enemy.damage_taken.size() > 0:
		_assert_vec3_near(enemy.damage_taken[0]["knockback"], Vector3.ZERO, 0.001, "VDK-3c_zero_kb")
	_free_root(root)


func test_vdk3d_poison_modifier() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"poison": true, "poison_duration": 3.0, "poison_dps": 0.5}
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(2.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.poison_calls.size(), "VDK-3d_poison_called")
	if enemy.poison_calls.size() > 0:
		_assert_eq_float(3.0, enemy.poison_calls[0]["duration"], "VDK-3d_poison_dur")
		_assert_eq_float(0.5, enemy.poison_calls[0]["dps"], "VDK-3d_poison_dps")
	_free_root(root)


func test_vdk3e_acid_modifier() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.2}
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(2.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.acid_calls.size(), "VDK-3e_acid_called")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(2.0, enemy.acid_calls[0]["duration"], "VDK-3e_acid_dur")
		_assert_eq_float(0.2, enemy.acid_calls[0]["dps"], "VDK-3e_acid_dps")
	_free_root(root)


func test_vdk3f_slow_modifier() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"slow": 0.5, "slow_duration": 1.5}
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(2.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.slow_calls.size(), "VDK-3f_slow_called")
	if enemy.slow_calls.size() > 0:
		_assert_eq_float(0.5, enemy.slow_calls[0]["multiplier"], "VDK-3f_slow_mult")
		_assert_eq_float(1.5, enemy.slow_calls[0]["duration"], "VDK-3f_slow_dur")
	_free_root(root)


func test_vdk3g_multiple_modifiers() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {
		"poison": true, "poison_duration": 3.0, "poison_dps": 0.5,
		"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.2,
		"slow": 0.5, "slow_duration": 1.5,
	}
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(2.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.poison_calls.size(), "VDK-3g_poison")
	_assert_eq_int(1, enemy.acid_calls.size(), "VDK-3g_acid")
	_assert_eq_int(1, enemy.slow_calls.size(), "VDK-3g_slow")
	_free_root(root)


func test_vdk3h_consumed_prevents_double_hit() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 5.0
	proj.knockback_magnitude = 10.0
	proj.knockback_direction = "away"
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(0.0, 0.0, 0.0)
	var enemy1 := MockEnemy.new()
	var enemy2 := MockEnemy.new()
	root.add_child(enemy1)
	root.add_child(enemy2)
	enemy1.global_position = Vector3(2.0, 0.0, 0.0)
	enemy2.global_position = Vector3(3.0, 0.0, 0.0)
	proj._on_body_entered(enemy1)
	_assert_true(proj._consumed, "VDK-3h_consumed_after_first")
	proj._on_body_entered(enemy2)
	_assert_eq_int(1, enemy1.damage_taken.size(), "VDK-3h_first_hit")
	_assert_eq_int(0, enemy2.damage_taken.size(), "VDK-3h_second_blocked")
	_free_root(root)


func test_vdk3i_bare_target_no_crash() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 5.0
	proj.knockback_magnitude = 10.0
	var root := _make_projectile_root(proj)
	var bare := BareTarget.new()
	root.add_child(bare)
	bare.global_position = Vector3(2.0, 0.0, 0.0)
	proj._on_body_entered(bare)
	_assert_false(proj._consumed, "VDK-3i_consumed_stays_false")
	_pass_test("VDK-3i_no_crash")
	_free_root(root)


func test_vdk3j_queue_free_on_hit() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(2.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_true(proj.is_queued_for_deletion(), "VDK-3j_queue_free_called")
	_free_root(root)


# ---------------------------------------------------------------------------
# VDK-4: End-to-End Knockback Direction in Melee (AC-4a..AC-4e)
# ---------------------------------------------------------------------------

func test_vdk4a_melee_away_e2e() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(3.0, 0.0, 0.0)
	var scene := _build_scene("VDK-4a", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 8.0,
		"knockback_magnitude": 10.0, "knockback_direction": "away"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "VDK-4a_hit")
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.x > 0.0, "VDK-4a_away_positive_x")
		_assert_eq_float(0.0, kb.z, "VDK-4a_z_zero")
	_teardown(scene)


func test_vdk4b_melee_toward_e2e() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(3.0, 0.0, 0.0)
	var scene := _build_scene("VDK-4b", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 8.0,
		"knockback_magnitude": 10.0, "knockback_direction": "toward"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "VDK-4b_hit")
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.x < 0.0, "VDK-4b_toward_negative_x")
		_assert_eq_float(0.0, kb.z, "VDK-4b_z_zero")
	_teardown(scene)


func test_vdk4c_melee_none_e2e() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(3.0, 0.0, 0.0)
	var scene := _build_scene("VDK-4c", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 8.0,
		"knockback_magnitude": 10.0, "knockback_direction": "none"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "VDK-4c_hit")
	if enemy.damage_taken.size() > 0:
		_assert_vec3_near(enemy.damage_taken[0]["knockback"], Vector3.ZERO, 0.001, "VDK-4c_none_zero")
	_teardown(scene)


func test_vdk4d_enemy_left_of_player() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(3.0, 0.0, 0.0)
	var scene := _build_scene("VDK-4d", [enemy], Vector3(5.0, 0.0, 0.0), -1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 6.0,
		"knockback_magnitude": 8.0, "knockback_direction": "away"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "VDK-4d_hit")
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.x < 0.0, "VDK-4d_away_pushed_left")
	_teardown(scene)


func test_vdk4e_multiple_enemies_away() -> void:
	var e1 := MockEnemy.new()
	var e2 := MockEnemy.new()
	e1.global_position = Vector3(2.0, 0.0, 0.0)
	e2.global_position = Vector3(1.0, 0.0, 0.0)
	var scene := _build_scene("VDK-4e", [e1, e2], Vector3.ZERO, 1.0)
	if scene.is_empty():
		e1.free()
		e2.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 8.0,
		"knockback_magnitude": 10.0, "knockback_direction": "away"
	})
	executor.execute_attack(res)
	_assert_true(e1.damage_taken.size() > 0, "VDK-4e_e1_hit")
	_assert_true(e2.damage_taken.size() > 0, "VDK-4e_e2_hit")
	if e1.damage_taken.size() > 0:
		_assert_true(e1.damage_taken[0]["knockback"].x > 0.0, "VDK-4e_e1_away_positive")
	if e2.damage_taken.size() > 0:
		_assert_true(e2.damage_taken[0]["knockback"].x > 0.0, "VDK-4e_e2_away_positive")
	_teardown(scene)


# ---------------------------------------------------------------------------
# VDK-5: Projectile Velocity Correctness (AC-5a..AC-5g)
# ---------------------------------------------------------------------------

func test_vdk5a_rightward_movement() -> void:
	var proj := PlayerProjectile3D.new()
	proj.direction_x = 1.0
	proj.speed = 100.0
	proj.lifetime = 5.0
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(0.0, 0.0, 0.0)
	proj._physics_process(0.1)
	_assert_approx(proj.global_position.x, 10.0, "VDK-5a_rightward_x")
	_free_root(root)


func test_vdk5b_leftward_movement() -> void:
	var proj := PlayerProjectile3D.new()
	proj.direction_x = -1.0
	proj.speed = 200.0
	proj.lifetime = 5.0
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(50.0, 0.0, 0.0)
	proj._physics_process(0.05)
	_assert_approx(proj.global_position.x, 40.0, "VDK-5b_leftward_x")
	_free_root(root)


func test_vdk5c_zero_speed() -> void:
	var proj := PlayerProjectile3D.new()
	proj.direction_x = 1.0
	proj.speed = 0.0
	proj.lifetime = 5.0
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(10.0, 0.0, 0.0)
	proj._physics_process(1.0)
	_assert_approx(proj.global_position.x, 10.0, "VDK-5c_zero_speed_no_move")
	_free_root(root)


func test_vdk5d_y_z_unchanged() -> void:
	var proj := PlayerProjectile3D.new()
	proj.direction_x = 1.0
	proj.speed = 100.0
	proj.lifetime = 5.0
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(0.0, 5.0, 3.0)
	proj._physics_process(0.1)
	_assert_approx(proj.global_position.y, 5.0, "VDK-5d_y_unchanged")
	_assert_approx(proj.global_position.z, 3.0, "VDK-5d_z_unchanged")
	_free_root(root)


func test_vdk5e_no_movement_when_consumed() -> void:
	var proj := PlayerProjectile3D.new()
	proj.direction_x = 1.0
	proj.speed = 100.0
	proj.lifetime = 5.0
	proj._consumed = true
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(10.0, 0.0, 0.0)
	proj._physics_process(0.1)
	_assert_approx(proj.global_position.x, 10.0, "VDK-5e_consumed_no_move")
	_free_root(root)


func test_vdk5f_lifetime_expiration() -> void:
	var proj := PlayerProjectile3D.new()
	proj.direction_x = 1.0
	proj.speed = 100.0
	proj.lifetime = 1.0
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(0.0, 0.0, 0.0)
	proj._physics_process(0.5)
	_assert_false(proj._consumed, "VDK-5f_not_consumed_at_half")
	proj._physics_process(0.6)
	_assert_true(proj._consumed, "VDK-5f_consumed_after_expiry")
	_assert_true(proj.is_queued_for_deletion(), "VDK-5f_queue_free_pending")
	_free_root(root)


func test_vdk5g_cumulative_movement() -> void:
	var proj := PlayerProjectile3D.new()
	proj.direction_x = 1.0
	proj.speed = 50.0
	proj.lifetime = 5.0
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(0.0, 0.0, 0.0)
	proj._physics_process(0.1)
	proj._physics_process(0.2)
	proj._physics_process(0.05)
	_assert_approx(proj.global_position.x, 17.5, "VDK-5g_cumulative")
	_free_root(root)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== VerifyDamageKnockbackTests ===")

	# VDK-1: Cross-Mutation Integration
	test_vdk1a_claw_melee_pipeline()
	test_vdk1b_acid_projectile_pipeline()
	test_vdk1c_carapace_unknown_handler()
	test_vdk1d_adhesion_unknown_handler()
	test_vdk1e_property_preservation()

	# VDK-2: VFX Spawn Position Correctness
	test_vdk2a_vfx_facing_right()
	test_vdk2b_vfx_facing_left()
	test_vdk2c_vfx_nonzero_y()
	test_vdk2d_vfx_zero_range()

	# VDK-3: PlayerProjectile3D On-Hit Behavior
	test_vdk3a_damage_on_hit_away()
	test_vdk3b_knockback_toward()
	test_vdk3c_zero_knockback()
	test_vdk3d_poison_modifier()
	test_vdk3e_acid_modifier()
	test_vdk3f_slow_modifier()
	test_vdk3g_multiple_modifiers()
	test_vdk3h_consumed_prevents_double_hit()
	test_vdk3i_bare_target_no_crash()
	test_vdk3j_queue_free_on_hit()

	# VDK-4: E2E Knockback Direction in Melee
	test_vdk4a_melee_away_e2e()
	test_vdk4b_melee_toward_e2e()
	test_vdk4c_melee_none_e2e()
	test_vdk4d_enemy_left_of_player()
	test_vdk4e_multiple_enemies_away()

	# VDK-5: Projectile Velocity Correctness
	test_vdk5a_rightward_movement()
	test_vdk5b_leftward_movement()
	test_vdk5c_zero_speed()
	test_vdk5d_y_z_unchanged()
	test_vdk5e_no_movement_when_consumed()
	test_vdk5f_lifetime_expiration()
	test_vdk5g_cumulative_movement()

	print("VerifyDamageKnockbackTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
