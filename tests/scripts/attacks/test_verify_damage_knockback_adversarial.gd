#
# test_verify_damage_knockback_adversarial.gd
#
# Adversarial edge-case tests for VDK damage/knockback verification.
# Spec: project_board/specs/verify_damage_knockback_spec.md (VDK-1..VDK-5, EC-1..EC-8)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/13_verify_damage_knockback.md
#

class_name VerifyDamageKnockbackAdversarialTests
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


# --- ADV-NE: Null & Empty Input Boundary ---
# Executor null-resource guard — primary suite never passes null.
func test_adv_ne01_execute_null_resource() -> void:
	var scene := _build_scene("ADV-NE01")
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor.execute_attack(null)
	_assert_false(executor.is_active(), "ADV-NE01_inactive_after_null")
	_assert_eq_int(0, _count_signal("attack_started"), "ADV-NE01_no_started_signal")
	_teardown(scene)


# Re-entrancy guard — no primary test calls execute_attack while _is_active.
func test_adv_ne02_reentrant_execute_blocked() -> void:
	var scene := _build_scene("ADV-NE02")
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	executor._is_active = true
	var res := _make_resource({"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 8.0})
	executor.execute_attack(res)
	_assert_eq_int(0, _count_signal("attack_started"), "ADV-NE02_blocked_no_started")
	_assert_eq_int(0, _count_signal("attack_hit"), "ADV-NE02_blocked_no_hit")
	executor._is_active = false
	_teardown(scene)


# Empty effect_type → unknown handler path (primary tests SLAM_AOE/LUNGE only).
func test_adv_ne03_empty_effect_type() -> void:
	var scene := _build_scene("ADV-NE03")
	if scene.is_empty():
		return
	var executor = scene["executor"]
	_connect_all_signals(executor)
	var res := _make_resource({"effect_type": "", "damage": 1.0})
	executor.execute_attack(res)
	_assert_false(executor.is_active(), "ADV-NE03_inactive")
	_assert_eq_int(1, _count_signal("attack_started"), "ADV-NE03_started_emitted")
	_assert_eq_int(0, _count_signal("attack_hit"), "ADV-NE03_no_hit")
	_teardown(scene)


# --- ADV-DB: AttackDatabase Boundary ---
# Empty mutation_id registration guard — primary VDK-1e tests only valid IDs.
func test_adv_db01_register_empty_mutation_id() -> void:
	var db := AttackDatabaseNode.new()
	var res := _make_resource({"attack_name": "Test"})
	db.register_base_attack("", res)
	_assert_false(db.has_base_attack(""), "ADV-DB01_empty_id_rejected")
	_assert_eq_int(0, db.get_base_attack_count(), "ADV-DB01_count_zero")
	db.free()


# Null resource registration guard.
func test_adv_db02_register_null_resource() -> void:
	var db := AttackDatabaseNode.new()
	db.register_base_attack("test_null", null)
	_assert_false(db.has_base_attack("test_null"), "ADV-DB02_null_rejected")
	_assert_eq_int(0, db.get_base_attack_count(), "ADV-DB02_count_zero")
	db.free()


# Unregistered key lookup — primary suite never queries a truly missing key.
func test_adv_db03_get_unregistered_returns_null() -> void:
	var db := AttackDatabaseNode.new()
	var result = db.get_base_attack("nonexistent_key")
	_assert_true(result == null, "ADV-DB03_null_for_missing_key")
	db.free()


# Overwrite semantics — no primary test re-registers the same key.
func test_adv_db04_overwrite_existing_registration() -> void:
	var db := AttackDatabaseNode.new()
	var r1 := _make_resource({"attack_name": "Version1", "damage": 1.0})
	var r2 := _make_resource({"attack_name": "Version2", "damage": 99.0})
	db.register_base_attack("overwrite_test", r1)
	db.register_base_attack("overwrite_test", r2)
	var retrieved = db.get_base_attack("overwrite_test")
	_assert_true(retrieved != null, "ADV-DB04_exists")
	if retrieved:
		_assert_eq_float(99.0, retrieved.damage, "ADV-DB04_latest_wins")
		_assert_eq_string("Version2", retrieved.attack_name, "ADV-DB04_name_updated")
	_assert_eq_int(1, db.get_base_attack_count(), "ADV-DB04_count_still_one")
	db.free()


# EC-6: DB stores direct reference — mutations visible via get_base_attack.
func test_adv_db05_reference_sharing_ec6() -> void:
	var db := AttackDatabaseNode.new()
	var res := _make_resource({"attack_name": "Original", "damage": 5.0})
	db.register_base_attack("ref_test", res)
	res.damage = 999.0
	var retrieved = db.get_base_attack("ref_test")
	_assert_true(retrieved != null, "ADV-DB05_exists")
	if retrieved:
		_assert_eq_float(999.0, retrieved.damage, "ADV-DB05_mutation_visible")
	db.free()


# --- ADV-DG: Degenerate Knockback Geometry ---
# DEGENERATE_DISTANCE_SQ fallback — enemy and player at same position.
func test_adv_dg01_melee_degenerate_same_position() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3.ZERO
	var scene := _build_scene("ADV-DG01", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 5.0, "attack_range": 8.0,
		"knockback_magnitude": 10.0, "knockback_direction": "away"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "ADV-DG01_hit")
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_eq_float(10.0, kb.x, "ADV-DG01_degenerate_fallback_x")
		_assert_eq_float(0.0, kb.y, "ADV-DG01_degenerate_y_zero")
		_assert_eq_float(0.0, kb.z, "ADV-DG01_degenerate_z_zero")
	_teardown(scene)


# Projectile degenerate: target at same position as projectile.
func test_adv_dg02_projectile_degenerate_same_position() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 3.0
	proj.knockback_magnitude = 7.0
	proj.knockback_direction = "away"
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(5.0, 0.0, 0.0)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(5.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.damage_taken.size(), "ADV-DG02_hit")
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_eq_float(7.0, kb.x, "ADV-DG02_degenerate_fallback_x")
		_assert_eq_float(0.0, kb.z, "ADV-DG02_z_zero")
	_free_root(root)


# EC-8: knockback Y component preserved (Z zeroed). Primary uses Y=0 only.
func test_adv_dg03_knockback_nonzero_y_component() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(8.0, 3.0, 0.0)
	var scene := _build_scene("ADV-DG03", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 20.0,
		"knockback_magnitude": 10.0, "knockback_direction": "away"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "ADV-DG03_hit")
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.y > 0.0, "ADV-DG03_y_positive_away")
		_assert_eq_float(0.0, kb.z, "ADV-DG03_z_always_zero")
	_teardown(scene)


# Unknown knockback_direction string → match `_:` returns ZERO.
func test_adv_dg04_unknown_knockback_direction_string() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3(3.0, 0.0, 0.0)
	var scene := _build_scene("ADV-DG04", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 8.0,
		"knockback_magnitude": 50.0, "knockback_direction": "GARBAGE_STRING"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "ADV-DG04_hit")
	if enemy.damage_taken.size() > 0:
		_assert_vec3_near(enemy.damage_taken[0]["knockback"], Vector3.ZERO, 0.001, "ADV-DG04_unknown_dir_zero")
	_teardown(scene)


# "toward" at degenerate position → fallback (1,0,0) negated to (-10,0,0).
func test_adv_dg05_toward_degenerate_same_position() -> void:
	var enemy := MockEnemy.new()
	enemy.global_position = Vector3.ZERO
	var scene := _build_scene("ADV-DG05", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 8.0,
		"knockback_magnitude": 10.0, "knockback_direction": "toward"
	})
	executor.execute_attack(res)
	_assert_true(enemy.damage_taken.size() > 0, "ADV-DG05_hit")
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_eq_float(-10.0, kb.x, "ADV-DG05_toward_degenerate_negative_x")
	_teardown(scene)


# --- ADV-PB: Projectile Boundary ---
# EC-3: zero lifetime → immediate expiry (_age=0.0 >= lifetime=0.0).
func test_adv_pb01_zero_lifetime_immediate_expiry() -> void:
	var proj := PlayerProjectile3D.new()
	proj.direction_x = 1.0
	proj.speed = 100.0
	proj.lifetime = 0.0
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3.ZERO
	proj._physics_process(0.016)
	_assert_true(proj._consumed, "ADV-PB01_consumed_immediately")
	_assert_true(proj.is_queued_for_deletion(), "ADV-PB01_queue_free_called")
	_free_root(root)


# Negative lifetime → _age=0.0 >= -1.0 is true, immediate consume.
func test_adv_pb02_negative_lifetime() -> void:
	var proj := PlayerProjectile3D.new()
	proj.direction_x = 1.0
	proj.speed = 50.0
	proj.lifetime = -1.0
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(10.0, 0.0, 0.0)
	proj._physics_process(0.016)
	_assert_true(proj._consumed, "ADV-PB02_consumed_on_negative_lifetime")
	_free_root(root)


# direction_x=0 → no X movement but lifetime still ticks.
func test_adv_pb03_direction_zero_no_movement() -> void:
	var proj := PlayerProjectile3D.new()
	proj.direction_x = 0.0
	proj.speed = 100.0
	proj.lifetime = 5.0
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(7.0, 2.0, 1.0)
	proj._physics_process(0.5)
	_assert_approx(proj.global_position.x, 7.0, "ADV-PB03_no_x_movement")
	_assert_approx(proj.global_position.y, 2.0, "ADV-PB03_y_unchanged")
	_assert_false(proj._consumed, "ADV-PB03_not_consumed_yet")
	_free_root(root)


# Negative speed reverses movement direction.
func test_adv_pb04_negative_speed() -> void:
	var proj := PlayerProjectile3D.new()
	proj.direction_x = 1.0
	proj.speed = -50.0
	proj.lifetime = 5.0
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3(10.0, 0.0, 0.0)
	proj._physics_process(0.1)
	_assert_true(proj.global_position.x < 10.0, "ADV-PB04_negative_speed_reverses")
	_assert_approx(proj.global_position.x, 5.0, "ADV-PB04_exact_position")
	_free_root(root)


# Extreme speed*delta → large displacement (no clamping).
func test_adv_pb05_extreme_displacement() -> void:
	var proj := PlayerProjectile3D.new()
	proj.direction_x = 1.0
	proj.speed = 100000.0
	proj.lifetime = 999.0
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3.ZERO
	proj._physics_process(1.0)
	_assert_approx(proj.global_position.x, 100000.0, "ADV-PB05_large_displacement")
	_free_root(root)


# _physics_process after body-consumed → no further movement.
func test_adv_pb06_physics_after_body_consumed() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.direction_x = 1.0
	proj.speed = 100.0
	proj.lifetime = 5.0
	var root := _make_projectile_root(proj)
	proj.global_position = Vector3.ZERO
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(2.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_true(proj._consumed, "ADV-PB06_consumed_after_hit")
	var pos_after_hit := proj.global_position.x
	proj._physics_process(1.0)
	_assert_approx(proj.global_position.x, pos_after_hit, "ADV-PB06_no_movement_after_consumed")
	_free_root(root)


# --- ADV-MF: Modifier Default Fallbacks ---
# DEFAULT_POISON_DPS (0.3) when poison_dps key absent.
func test_adv_mf01_poison_default_dps() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"poison": true, "poison_duration": 4.0}
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.poison_calls.size(), "ADV-MF01_poison_called")
	if enemy.poison_calls.size() > 0:
		_assert_eq_float(4.0, enemy.poison_calls[0]["duration"], "ADV-MF01_explicit_duration")
		_assert_eq_float(0.3, enemy.poison_calls[0]["dps"], "ADV-MF01_default_dps_0.3")
	_free_root(root)


# Default poison_duration (2.0) when key missing.
func test_adv_mf02_poison_default_duration() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"poison": true, "poison_dps": 0.8}
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.poison_calls.size(), "ADV-MF02_poison_called")
	if enemy.poison_calls.size() > 0:
		_assert_eq_float(2.0, enemy.poison_calls[0]["duration"], "ADV-MF02_default_duration_2.0")
		_assert_eq_float(0.8, enemy.poison_calls[0]["dps"], "ADV-MF02_explicit_dps")
	_free_root(root)


# DEFAULT_ACID_DPS (0.2) when acid_dps key absent.
func test_adv_mf03_acid_default_dps() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"acid_on_hit": true, "acid_duration": 3.0}
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV-MF03_acid_called")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(3.0, enemy.acid_calls[0]["duration"], "ADV-MF03_explicit_duration")
		_assert_eq_float(0.2, enemy.acid_calls[0]["dps"], "ADV-MF03_default_dps_0.2")
	_free_root(root)


# DEFAULT_SLOW_DURATION (1.5) when slow_duration key absent.
func test_adv_mf04_slow_default_duration() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"slow": 0.6}
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.slow_calls.size(), "ADV-MF04_slow_called")
	if enemy.slow_calls.size() > 0:
		_assert_eq_float(0.6, enemy.slow_calls[0]["multiplier"], "ADV-MF04_explicit_mult")
		_assert_eq_float(1.5, enemy.slow_calls[0]["duration"], "ADV-MF04_default_duration_1.5")
	_free_root(root)


# slow=0.0 must NOT trigger apply_slowness (0.0 is falsy in guard).
func test_adv_mf05_slow_zero_not_applied() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"slow": 0.0, "slow_duration": 2.0}
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.slow_calls.size(), "ADV-MF05_zero_slow_applied")
	_free_root(root)


# Empty modifiers dictionary → no modifier methods called.
func test_adv_mf06_empty_modifiers_no_calls() -> void:
	var proj := PlayerProjectile3D.new()
	proj.damage = 2.0
	proj.modifiers = {}
	var root := _make_projectile_root(proj)
	var enemy := MockEnemy.new()
	root.add_child(enemy)
	enemy.global_position = Vector3(1.0, 0.0, 0.0)
	proj._on_body_entered(enemy)
	_assert_eq_int(1, enemy.damage_taken.size(), "ADV-MF06_damage_called")
	_assert_eq_int(0, enemy.poison_calls.size(), "ADV-MF06_no_poison")
	_assert_eq_int(0, enemy.acid_calls.size(), "ADV-MF06_no_acid")
	_assert_eq_int(0, enemy.slow_calls.size(), "ADV-MF06_no_slow")
	_free_root(root)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("=== VerifyDamageKnockbackAdversarialTests ===")

	# Null & Empty
	test_adv_ne01_execute_null_resource()
	test_adv_ne02_reentrant_execute_blocked()
	test_adv_ne03_empty_effect_type()

	# AttackDatabase boundary
	test_adv_db01_register_empty_mutation_id()
	test_adv_db02_register_null_resource()
	test_adv_db03_get_unregistered_returns_null()
	test_adv_db04_overwrite_existing_registration()
	test_adv_db05_reference_sharing_ec6()

	# Degenerate knockback geometry
	test_adv_dg01_melee_degenerate_same_position()
	test_adv_dg02_projectile_degenerate_same_position()
	test_adv_dg03_knockback_nonzero_y_component()
	test_adv_dg04_unknown_knockback_direction_string()
	test_adv_dg05_toward_degenerate_same_position()

	# Projectile boundary
	test_adv_pb01_zero_lifetime_immediate_expiry()
	test_adv_pb02_negative_lifetime()
	test_adv_pb03_direction_zero_no_movement()
	test_adv_pb04_negative_speed()
	test_adv_pb05_extreme_displacement()
	test_adv_pb06_physics_after_body_consumed()

	# Modifier default fallbacks
	test_adv_mf01_poison_default_dps()
	test_adv_mf02_poison_default_duration()
	test_adv_mf03_acid_default_dps()
	test_adv_mf04_slow_default_duration()
	test_adv_mf05_slow_zero_not_applied()
	test_adv_mf06_empty_modifiers_no_calls()

	print("VerifyDamageKnockbackAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
