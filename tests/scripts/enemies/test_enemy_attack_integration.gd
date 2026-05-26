#
# test_enemy_attack_integration.gd
#
# Integration tests verifying the full attack pipeline connects to a real
# EnemyBase instance. Bridges AttackExecutor and PlayerProjectile3D with
# EnemyBase (not mocks) to satisfy AC-11 of ticket M11-14.
#
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/14_enemy_health_and_damage_reception.md
#

class_name EnemyAttackIntegrationTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class MockParent extends Node3D:
	var _facing: float = 1.0

	func get_facing_sign() -> float:
		return _facing


func _make_enemy(pos: Vector3 = Vector3.ZERO, hp: float = 10.0) -> EnemyBase:
	var enemy := EnemyBase.new()
	enemy.max_hp = hp
	return enemy


func _make_resource(overrides: Dictionary = {}) -> AttackResource:
	var r := AttackResource.new()
	r.startup_frames = 0
	for key in overrides:
		r.set(key, overrides[key])
	return r


func _build_integration_scene(
	enemies: Array,
	parent_pos: Vector3 = Vector3.ZERO,
	facing: float = 1.0
) -> Dictionary:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		return {}

	var scene_root := Node3D.new()
	var parent := MockParent.new()
	parent._facing = facing
	scene_root.add_child(parent)
	parent.add_child(executor)

	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)

	parent.global_position = parent_pos

	for e in enemies:
		scene_root.add_child(e)
		if e.is_inside_tree():
			e.add_to_group("enemies")

	return {"root": scene_root, "parent": parent, "executor": executor}


func _teardown(scene: Dictionary) -> void:
	var root = scene.get("root")
	if root != null and is_instance_valid(root):
		(root as Node).free()


# ---------------------------------------------------------------------------
# INTEGRATION-1: AttackExecutor MELEE_SWIPE → real EnemyBase
# ---------------------------------------------------------------------------

func test_int1a_melee_reduces_hp() -> void:
	var enemy := _make_enemy(Vector3(3.0, 0.0, 0.0))
	var scene := _build_integration_scene([enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return

	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 4.0,
		"attack_range": 8.0,
		"knockback_magnitude": 5.0,
		"knockback_direction": "away",
	})

	var executor = scene["executor"]
	executor.execute_attack(res)

	_assert_eq_float(6.0, enemy.current_hp, "INT-1a_hp_reduced_to_6")
	_teardown(scene)


func test_int1b_melee_emits_damaged_signal() -> void:
	var enemy := _make_enemy(Vector3(3.0, 0.0, 0.0))
	var scene := _build_integration_scene([enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return

	var signal_received: Array = []
	enemy.damaged.connect(func(dmg, hp): signal_received.append({"damage": dmg, "hp": hp}))

	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 3.0,
		"attack_range": 8.0,
		"knockback_magnitude": 10.0,
		"knockback_direction": "away",
	})

	var executor = scene["executor"]
	executor.execute_attack(res)

	_assert_eq_int(1, signal_received.size(), "INT-1b_damaged_signal_emitted")
	if signal_received.size() > 0:
		_assert_eq_float(3.0, signal_received[0]["damage"], "INT-1b_signal_damage_value")
		_assert_eq_float(7.0, signal_received[0]["hp"], "INT-1b_signal_hp_value")
	_teardown(scene)


func test_int1c_melee_applies_knockback() -> void:
	var enemy := _make_enemy(Vector3(3.0, 0.0, 0.0))
	var scene := _build_integration_scene([enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return

	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 2.0,
		"attack_range": 8.0,
		"knockback_magnitude": 15.0,
		"knockback_direction": "away",
	})

	var executor = scene["executor"]
	executor.execute_attack(res)

	_assert_true(enemy._knockback_velocity.length() > 0.0, "INT-1c_knockback_applied")
	_assert_true(enemy._knockback_velocity.x > 0.0, "INT-1c_knockback_pushes_away")
	_teardown(scene)


func test_int1d_melee_multiple_enemies() -> void:
	var e1 := _make_enemy(Vector3(2.0, 0.0, 0.0))
	var e2 := _make_enemy(Vector3(3.0, 0.0, 0.0))
	var scene := _build_integration_scene([e1, e2], Vector3.ZERO, 1.0)
	if scene.is_empty():
		e1.free()
		e2.free()
		return

	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 5.0,
		"attack_range": 10.0,
		"knockback_magnitude": 8.0,
		"knockback_direction": "away",
	})

	var executor = scene["executor"]
	executor.execute_attack(res)

	_assert_eq_float(5.0, e1.current_hp, "INT-1d_enemy1_hp")
	_assert_eq_float(5.0, e2.current_hp, "INT-1d_enemy2_hp")
	_teardown(scene)


# ---------------------------------------------------------------------------
# INTEGRATION-2: PlayerProjectile3D → real EnemyBase
# ---------------------------------------------------------------------------

func test_int2a_projectile_reduces_hp() -> void:
	var enemy := _make_enemy(Vector3(5.0, 0.0, 0.0))
	var root := Node3D.new()
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(root)
	root.add_child(enemy)

	var proj := PlayerProjectile3D.new()
	proj.damage = 3.0
	proj.knockback_magnitude = 5.0
	proj.knockback_direction = "away"
	root.add_child(proj)
	proj.global_position = Vector3(4.0, 0.0, 0.0)

	proj._on_body_entered(enemy)

	_assert_eq_float(7.0, enemy.current_hp, "INT-2a_hp_reduced_to_7")
	_assert_true(proj._consumed, "INT-2a_projectile_consumed")
	root.free()


func test_int2b_projectile_poison_modifier() -> void:
	var enemy := _make_enemy(Vector3(5.0, 0.0, 0.0))
	var root := Node3D.new()
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(root)
	root.add_child(enemy)

	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"poison": true, "poison_duration": 3.0, "poison_dps": 0.5}
	root.add_child(proj)

	proj._on_body_entered(enemy)

	var tracker: EnemyEffectTracker = enemy.get_node("EnemyEffectTracker")
	_assert_true(tracker != null, "INT-2b_tracker_exists")
	if tracker:
		_assert_true(tracker.has_active_dot("poison"), "INT-2b_poison_active")
	root.free()


func test_int2c_projectile_acid_modifier() -> void:
	var enemy := _make_enemy(Vector3(5.0, 0.0, 0.0))
	var root := Node3D.new()
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(root)
	root.add_child(enemy)

	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.3}
	root.add_child(proj)

	proj._on_body_entered(enemy)

	var tracker: EnemyEffectTracker = enemy.get_node("EnemyEffectTracker")
	_assert_true(tracker != null, "INT-2c_tracker_exists")
	if tracker:
		_assert_true(tracker.has_active_dot("acid"), "INT-2c_acid_active")
	root.free()


func test_int2d_projectile_slowness_modifier() -> void:
	var enemy := _make_enemy(Vector3(5.0, 0.0, 0.0))
	var root := Node3D.new()
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(root)
	root.add_child(enemy)

	var proj := PlayerProjectile3D.new()
	proj.damage = 1.0
	proj.modifiers = {"slow": 0.5, "slow_duration": 2.0}
	root.add_child(proj)

	proj._on_body_entered(enemy)

	_assert_eq_float(0.5, enemy.get_speed_multiplier(), "INT-2d_slowness_applied")
	root.free()


func test_int2e_projectile_all_modifiers() -> void:
	var enemy := _make_enemy(Vector3(5.0, 0.0, 0.0))
	var root := Node3D.new()
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(root)
	root.add_child(enemy)

	var proj := PlayerProjectile3D.new()
	proj.damage = 2.0
	proj.knockback_magnitude = 7.0
	proj.knockback_direction = "away"
	proj.modifiers = {
		"poison": true, "poison_duration": 3.0, "poison_dps": 0.5,
		"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.2,
		"slow": 0.4, "slow_duration": 1.5,
	}
	root.add_child(proj)
	proj.global_position = Vector3(3.0, 0.0, 0.0)

	proj._on_body_entered(enemy)

	_assert_eq_float(8.0, enemy.current_hp, "INT-2e_hp_reduced")
	var tracker: EnemyEffectTracker = enemy.get_node("EnemyEffectTracker")
	if tracker:
		_assert_true(tracker.has_active_dot("poison"), "INT-2e_poison_active")
		_assert_true(tracker.has_active_dot("acid"), "INT-2e_acid_active")
	_assert_eq_float(0.4, enemy.get_speed_multiplier(), "INT-2e_slow_applied")
	_assert_true(enemy._knockback_velocity.length() > 0.0, "INT-2e_knockback_applied")
	root.free()


# ---------------------------------------------------------------------------
# INTEGRATION-3: WEAKENED state via attack pipeline
# ---------------------------------------------------------------------------

func test_int3a_melee_triggers_weakened() -> void:
	var enemy := _make_enemy(Vector3(3.0, 0.0, 0.0))
	var scene := _build_integration_scene([enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return

	_assert_eq_int(EnemyBase.State.NORMAL, enemy.current_state, "INT-3a_starts_normal")

	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 6.0,
		"attack_range": 8.0,
		"knockback_magnitude": 5.0,
		"knockback_direction": "away",
	})

	var executor = scene["executor"]
	executor.execute_attack(res)

	_assert_eq_float(4.0, enemy.current_hp, "INT-3a_hp_is_4")
	_assert_eq_int(EnemyBase.State.WEAKENED, enemy.current_state, "INT-3a_weakened_at_40pct")
	_teardown(scene)


func test_int3b_projectile_triggers_weakened() -> void:
	var enemy := _make_enemy(Vector3(5.0, 0.0, 0.0))
	var root := Node3D.new()
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(root)
	root.add_child(enemy)

	_assert_eq_int(EnemyBase.State.NORMAL, enemy.current_state, "INT-3b_starts_normal")

	var proj := PlayerProjectile3D.new()
	proj.damage = 7.0
	proj.knockback_magnitude = 3.0
	proj.knockback_direction = "away"
	root.add_child(proj)
	proj.global_position = Vector3(3.0, 0.0, 0.0)

	proj._on_body_entered(enemy)

	_assert_eq_float(3.0, enemy.current_hp, "INT-3b_hp_is_3")
	_assert_eq_int(EnemyBase.State.WEAKENED, enemy.current_state, "INT-3b_weakened_at_30pct")
	root.free()


func test_int3c_melee_death_via_pipeline() -> void:
	var enemy := _make_enemy(Vector3(3.0, 0.0, 0.0))
	var scene := _build_integration_scene([enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return

	var died_emitted: Array = []
	enemy.died.connect(func(): died_emitted.append(true))

	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 15.0,
		"attack_range": 8.0,
		"knockback_magnitude": 0.0,
		"knockback_direction": "none",
	})

	var executor = scene["executor"]
	executor.execute_attack(res)

	_assert_eq_float(0.0, enemy.current_hp, "INT-3c_hp_zero")
	_assert_true(enemy.is_dead(), "INT-3c_is_dead")
	_assert_eq_int(1, died_emitted.size(), "INT-3c_died_emitted")
	_teardown(scene)


func test_int3d_weakened_threshold_boundary() -> void:
	var enemy := _make_enemy(Vector3(3.0, 0.0, 0.0))
	var scene := _build_integration_scene([enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return

	# Deal exactly 5.0 damage → HP becomes 5.0 = 50% of max_hp (10.0)
	# WEAKENED threshold is <= 50%, so 5.0 should trigger WEAKENED
	var res := _make_resource({
		"effect_type": "MELEE_SWIPE",
		"damage": 5.0,
		"attack_range": 8.0,
		"knockback_magnitude": 3.0,
		"knockback_direction": "away",
	})

	var executor = scene["executor"]
	executor.execute_attack(res)

	_assert_eq_float(5.0, enemy.current_hp, "INT-3d_hp_at_threshold")
	_assert_eq_int(EnemyBase.State.WEAKENED, enemy.current_state, "INT-3d_weakened_at_exact_50pct")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== EnemyAttackIntegrationTests ===")

	# INTEGRATION-1: AttackExecutor MELEE_SWIPE → real EnemyBase
	test_int1a_melee_reduces_hp()
	test_int1b_melee_emits_damaged_signal()
	test_int1c_melee_applies_knockback()
	test_int1d_melee_multiple_enemies()

	# INTEGRATION-2: PlayerProjectile3D → real EnemyBase
	test_int2a_projectile_reduces_hp()
	test_int2b_projectile_poison_modifier()
	test_int2c_projectile_acid_modifier()
	test_int2d_projectile_slowness_modifier()
	test_int2e_projectile_all_modifiers()

	# INTEGRATION-3: WEAKENED state transition via attack pipeline
	test_int3a_melee_triggers_weakened()
	test_int3b_projectile_triggers_weakened()
	test_int3c_melee_death_via_pipeline()
	test_int3d_weakened_threshold_boundary()

	print("EnemyAttackIntegrationTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
