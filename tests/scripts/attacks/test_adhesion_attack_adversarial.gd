#
# test_adhesion_attack_adversarial.gd
#
# Adversarial edge-case and boundary tests for the adhesion mutation attack.
# Targets runtime seams in EnemyEffectTracker._tick_slowness(), PlayerProjectile3D
# _on_body_entered()/_physics_process(), AttackExecutor._apply_modifiers(), and
# AttackDatabaseNode.register_base_attack().
#
# Spec: project_board/specs/adhesion_player_attack_spec.md (ADHA-1..ADHA-8)
# Ticket: M11-11
# Primary suite: tests/scripts/attacks/test_adhesion_attack.gd
#

class_name AdhesionAttackAdversarialTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Mock inner classes
# ---------------------------------------------------------------------------

class MockEnemy extends Node3D:
	var damage_taken: Array = []
	var slowness_applications: Array = []
	var current_state: int = 0
	var is_dead_flag: bool = false

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

	func apply_slowness(multiplier: float, duration: float) -> void:
		slowness_applications.append({"multiplier": multiplier, "duration": duration})

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag


class DeadEnemy extends Node3D:
	var damage_taken: Array = []
	var slowness_applications: Array = []
	var current_state: int = 0

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

	func apply_slowness(multiplier: float, duration: float) -> void:
		slowness_applications.append({"multiplier": multiplier, "duration": duration})

	func get_base_state() -> int:
		return current_state

	func is_dead() -> bool:
		return true


class MockWall extends Node3D:
	pass


class MockParent extends Node3D:
	var _facing: float = 1.0
	func get_facing_sign() -> float:
		return _facing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_adhesion_resource() -> AttackResource:
	var r = AttackResource.new()
	r.attack_id = 4
	r.attack_name = "Sticky Spit"
	r.description = "Sticky projectile that roots the first enemy hit, stopping all movement for 1.0s."
	r.effect_type = "PROJECTILE_SPIT"
	r.damage = 1.0
	r.cooldown = 2.5
	r.attack_range = 0.0
	r.startup_frames = 0
	r.knockback_magnitude = 0.0
	r.knockback_direction = "none"
	r.projectile_speed = 8.0
	r.projectile_lifetime = 1.25
	r.color = Color.DARK_GOLDENROD
	r.vfx_scale = 1.0
	r.modifiers = {"slow": 0.0, "slow_duration": 1.0}
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


func _make_projectile_in_tree(mods: Dictionary = {}, dmg: float = 1.0, spd: float = 8.0, lt: float = 1.25) -> Dictionary:
	var root = Node3D.new()
	var proj = PlayerProjectile3D.new()
	proj.damage = dmg
	proj.speed = spd
	proj.knockback_magnitude = 0.0
	proj.knockback_direction = "none"
	proj.modifiers = mods
	proj.direction_x = 1.0
	proj.lifetime = lt
	root.add_child(proj)
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(root)
	return {"root": root, "projectile": proj}


# ---------------------------------------------------------------------------
# 1. Root duration boundary — exactly 1.0s, slightly under/over
#    Targets: EnemyEffectTracker._tick_slowness() boundary condition
# ---------------------------------------------------------------------------

func test_root_duration_exactly_at_boundary() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, 1.0)
	tracker._tick_slowness(1.0)
	_assert_eq_float(1.0, tracker.get_speed_multiplier(), "root_expires_at_exact_1s")
	tracker.free()

func test_root_duration_one_frame_under() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, 1.0)
	tracker._tick_slowness(0.9999)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "root_active_just_under_1s")
	tracker.free()

func test_root_duration_one_frame_over() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, 1.0)
	tracker._tick_slowness(1.0001)
	_assert_eq_float(1.0, tracker.get_speed_multiplier(), "root_expired_just_over_1s")
	tracker.free()

func test_root_duration_epsilon_under() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, 1.0)
	tracker._tick_slowness(1.0 - 1e-7)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "root_active_epsilon_under")
	tracker.free()

func test_root_duration_multi_tick_accumulates_correctly() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, 1.0)
	for i in range(59):
		tracker._tick_slowness(1.0 / 60.0)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "root_still_active_59_frames")
	tracker._tick_slowness(1.0 / 60.0)
	_assert_eq_float(1.0, tracker.get_speed_multiplier(), "root_expires_60th_frame")
	tracker.free()

func test_root_duration_zero_duration_rejected() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, 0.0)
	_assert_eq_float(1.0, tracker.get_speed_multiplier(), "zero_duration_no_effect")
	tracker.free()

func test_root_negative_duration_rejected() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, -1.0)
	_assert_eq_float(1.0, tracker.get_speed_multiplier(), "negative_duration_no_effect")
	tracker.free()


# ---------------------------------------------------------------------------
# 2. Double-root stacking — should refresh, not stack durations
#    Targets: EnemyEffectTracker.set_slowness() overwrite semantics
# ---------------------------------------------------------------------------

func test_double_root_does_not_stack_duration() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, 1.0)
	tracker._tick_slowness(0.5)
	tracker.set_slowness(0.0, 1.0)
	tracker._tick_slowness(1.0)
	_assert_eq_float(1.0, tracker.get_speed_multiplier(), "double_root_refreshed_not_stacked")
	tracker.free()

func test_double_root_stacking_hypothetical_failure() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, 1.0)
	tracker._tick_slowness(0.99)
	tracker.set_slowness(0.0, 1.0)
	tracker._tick_slowness(0.5)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "reroot_mid_expiry_still_active")
	tracker._tick_slowness(0.51)
	_assert_eq_float(1.0, tracker.get_speed_multiplier(), "reroot_expired_after_full_new_duration")
	tracker.free()

func test_triple_root_refresh() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, 1.0)
	tracker._tick_slowness(0.9)
	tracker.set_slowness(0.0, 1.0)
	tracker._tick_slowness(0.9)
	tracker.set_slowness(0.0, 1.0)
	tracker._tick_slowness(0.9)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "triple_refresh_still_active")
	tracker._tick_slowness(0.11)
	_assert_eq_float(1.0, tracker.get_speed_multiplier(), "triple_refresh_eventually_expires")
	tracker.free()

func test_weaker_slow_overwrites_root() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, 1.0)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "initial_root")
	tracker.set_slowness(0.7, 2.0)
	_assert_eq_float(0.7, tracker.get_speed_multiplier(), "root_overwritten_by_weaker_slow")
	tracker.free()


# ---------------------------------------------------------------------------
# 3. Dead enemy hit by projectile
#    Targets: PlayerProjectile3D._on_body_entered() — dead targets
# ---------------------------------------------------------------------------

func test_dead_enemy_still_receives_body_entered() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var enemy = DeadEnemy.new()
	ps["projectile"]._on_body_entered(enemy)
	_assert_true(ps["projectile"]._consumed, "dead_enemy_consumes_projectile")
	_assert_eq_int(1, enemy.damage_taken.size(), "dead_enemy_take_damage_called")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_dead_enemy_slow_still_dispatched() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var enemy = DeadEnemy.new()
	ps["projectile"]._on_body_entered(enemy)
	_assert_eq_int(1, enemy.slowness_applications.size(), "dead_enemy_apply_slowness_called")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_executor_infect_weakened_guards_dead() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("executor_dead_guard", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	enemy.is_dead_flag = true
	var mods := {"infect_weakened": true}
	executor._apply_modifiers(enemy, mods, 1)
	_assert_eq_int(1, enemy.current_state, "dead_weakened_not_infected")
	enemy.free()
	executor.free()


# ---------------------------------------------------------------------------
# 4. Projectile wall collision at exact enemy position
#    Targets: _consumed flag race in _on_body_entered()
# ---------------------------------------------------------------------------

func test_wall_then_enemy_same_position() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var wall = MockWall.new()
	var enemy = MockEnemy.new()
	ps["projectile"]._on_body_entered(wall)
	ps["projectile"]._on_body_entered(enemy)
	_assert_true(ps["projectile"]._consumed, "wall_consumes_first")
	_assert_eq_int(0, enemy.damage_taken.size(), "enemy_not_hit_after_wall")
	_assert_eq_int(0, enemy.slowness_applications.size(), "enemy_no_slow_after_wall")
	wall.free()
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_enemy_then_wall_same_position() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var wall = MockWall.new()
	var enemy = MockEnemy.new()
	ps["projectile"]._on_body_entered(enemy)
	ps["projectile"]._on_body_entered(wall)
	_assert_true(ps["projectile"]._consumed, "enemy_consumes_first")
	_assert_eq_int(1, enemy.damage_taken.size(), "enemy_takes_damage")
	_assert_eq_int(1, enemy.slowness_applications.size(), "enemy_gets_slowed")
	wall.free()
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_two_walls_sequential() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var wall1 = MockWall.new()
	var wall2 = MockWall.new()
	ps["projectile"]._on_body_entered(wall1)
	ps["projectile"]._on_body_entered(wall2)
	_assert_true(ps["projectile"]._consumed, "first_wall_consumes")
	wall1.free()
	wall2.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_consumed_projectile_ignores_all_subsequent() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var e1 = MockEnemy.new()
	var e2 = MockEnemy.new()
	var wall = MockWall.new()
	ps["projectile"]._on_body_entered(e1)
	ps["projectile"]._on_body_entered(e2)
	ps["projectile"]._on_body_entered(wall)
	_assert_eq_int(1, e1.damage_taken.size(), "only_first_enemy_hit")
	_assert_eq_int(0, e2.damage_taken.size(), "second_enemy_safe")
	e1.free()
	e2.free()
	wall.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()


# ---------------------------------------------------------------------------
# 5. Zero-speed projectile (degenerate config)
#    Targets: PlayerProjectile3D._physics_process() with speed = 0
# ---------------------------------------------------------------------------

func test_zero_speed_projectile_stays_in_place() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0}, 1.0, 0.0, 1.25)
	var proj = ps["projectile"]
	var start_pos = proj.global_position
	proj._physics_process(0.5)
	_assert_eq_float(start_pos.x, proj.global_position.x, "zero_speed_no_movement")
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_zero_speed_projectile_still_despawns_on_lifetime() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0}, 1.0, 0.0, 1.25)
	var proj = ps["projectile"]
	proj._physics_process(1.26)
	_assert_true(proj._consumed, "zero_speed_despawns_on_lifetime")
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_zero_speed_projectile_can_still_hit_overlapping_enemy() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0}, 1.0, 0.0, 1.25)
	var enemy = MockEnemy.new()
	ps["projectile"]._on_body_entered(enemy)
	_assert_eq_int(1, enemy.damage_taken.size(), "zero_speed_still_damages")
	_assert_eq_int(1, enemy.slowness_applications.size(), "zero_speed_still_roots")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_negative_speed_projectile_moves_backward() -> void:
	var ps = _make_projectile_in_tree({}, 1.0, -8.0, 1.25)
	var proj = ps["projectile"]
	var start_x = proj.global_position.x
	proj._physics_process(0.1)
	_assert_true(proj.global_position.x < start_x, "negative_speed_moves_left")
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()


# ---------------------------------------------------------------------------
# 6. Multiple projectiles in flight simultaneously
#    Targets: scene tree isolation between projectile instances
# ---------------------------------------------------------------------------

func test_two_projectiles_independent_consumed_state() -> void:
	var ps1 = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var ps2 = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var wall = MockWall.new()
	ps1["projectile"]._on_body_entered(wall)
	_assert_true(ps1["projectile"]._consumed, "proj1_consumed")
	_assert_false(ps2["projectile"]._consumed, "proj2_still_active")
	wall.free()
	(ps1["root"] as Node).free()
	(ps2["root"] as Node).free()

func test_two_projectiles_independent_damage() -> void:
	var ps1 = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var ps2 = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var e1 = MockEnemy.new()
	var e2 = MockEnemy.new()
	ps1["projectile"]._on_body_entered(e1)
	ps2["projectile"]._on_body_entered(e2)
	_assert_eq_int(1, e1.damage_taken.size(), "proj1_hits_e1")
	_assert_eq_int(1, e2.damage_taken.size(), "proj2_hits_e2")
	_assert_eq_int(1, e1.slowness_applications.size(), "e1_rooted")
	_assert_eq_int(1, e2.slowness_applications.size(), "e2_rooted")
	e1.free()
	e2.free()
	(ps1["root"] as Node).free()
	(ps2["root"] as Node).free()

func test_two_projectiles_same_enemy() -> void:
	var ps1 = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var ps2 = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var enemy = MockEnemy.new()
	ps1["projectile"]._on_body_entered(enemy)
	ps2["projectile"]._on_body_entered(enemy)
	_assert_eq_int(2, enemy.damage_taken.size(), "both_projectiles_damage")
	_assert_eq_int(2, enemy.slowness_applications.size(), "both_apply_slow")
	enemy.free()
	(ps1["root"] as Node).free()
	(ps2["root"] as Node).free()

func test_projectile_age_independent_across_instances() -> void:
	var ps1 = _make_projectile_in_tree({}, 1.0, 8.0, 1.25)
	var ps2 = _make_projectile_in_tree({}, 1.0, 8.0, 1.25)
	ps1["projectile"]._physics_process(1.0)
	_assert_false(ps1["projectile"]._consumed, "proj1_not_expired_at_1s")
	_assert_false(ps2["projectile"]._consumed, "proj2_not_expired_untouched")
	ps1["projectile"]._physics_process(0.26)
	_assert_true(ps1["projectile"]._consumed, "proj1_expired")
	_assert_false(ps2["projectile"]._consumed, "proj2_still_fresh")
	(ps1["root"] as Node).free()
	(ps2["root"] as Node).free()


# ---------------------------------------------------------------------------
# 7. Root on WEAKENED enemy (infection interaction edge)
#    Targets: state remains WEAKENED, not promoted to INFECTED by root
# ---------------------------------------------------------------------------

func test_root_on_weakened_does_not_infect() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	ps["projectile"]._on_body_entered(enemy)
	_assert_eq_int(1, enemy.current_state, "weakened_stays_weakened_after_root")
	_assert_eq_int(1, enemy.slowness_applications.size(), "root_applied_to_weakened")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_root_on_infected_does_not_change_state() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var enemy = MockEnemy.new()
	enemy.current_state = 2
	ps["projectile"]._on_body_entered(enemy)
	_assert_eq_int(2, enemy.current_state, "infected_stays_infected_after_root")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_adhesion_then_claw_on_normal_does_not_infect() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("adhesion_claw_normal", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 0
	var adhesion_mods := {"slow": 0.0, "slow_duration": 1.0}
	executor._apply_modifiers(enemy, adhesion_mods)
	var claw_mods := {"infect_weakened": true}
	executor._apply_modifiers(enemy, claw_mods, 0)
	_assert_eq_int(0, enemy.current_state, "normal_not_infected_even_with_claw")
	enemy.free()
	executor.free()


# ---------------------------------------------------------------------------
# 8. apply_slowness(0.0, ...) vs apply_slowness(small_value, ...)
#    Targets: falsy-zero fix boundary — values near zero
# ---------------------------------------------------------------------------

func test_slow_exactly_zero_applies_root() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("slow_exactly_zero", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	executor._apply_modifiers(enemy, {"slow": 0.0, "slow_duration": 1.0})
	_assert_eq_int(1, enemy.slowness_applications.size(), "zero_applies")
	if enemy.slowness_applications.size() > 0:
		_assert_eq_float(0.0, enemy.slowness_applications[0]["multiplier"], "zero_multiplier")
	enemy.free()
	executor.free()

func test_slow_tiny_positive_applies() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("slow_tiny_positive", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	executor._apply_modifiers(enemy, {"slow": 0.001, "slow_duration": 1.0})
	_assert_eq_int(1, enemy.slowness_applications.size(), "tiny_positive_applies")
	if enemy.slowness_applications.size() > 0:
		_assert_eq_float(0.001, enemy.slowness_applications[0]["multiplier"], "tiny_value_passed")
	enemy.free()
	executor.free()

func test_slow_one_full_speed_applies() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("slow_one", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	executor._apply_modifiers(enemy, {"slow": 1.0, "slow_duration": 2.0})
	_assert_eq_int(1, enemy.slowness_applications.size(), "one_applies")
	if enemy.slowness_applications.size() > 0:
		_assert_eq_float(1.0, enemy.slowness_applications[0]["multiplier"], "one_multiplier")
	enemy.free()
	executor.free()

func test_slow_negative_value_passes_through() -> void:
	# CHECKPOINT: negative multiplier is not guarded by spec; tests conservative expectation
	# that any non-null value gets passed to apply_slowness (EnemyEffectTracker clamps via maxf)
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("slow_negative", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	executor._apply_modifiers(enemy, {"slow": -0.5, "slow_duration": 1.0})
	_assert_eq_int(1, enemy.slowness_applications.size(), "negative_dispatched")
	enemy.free()
	executor.free()

func test_effect_tracker_clamps_negative_multiplier() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(-0.5, 1.0)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "negative_clamped_to_zero")
	tracker.free()

func test_projectile_path_slow_exactly_zero() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0})
	var enemy = MockEnemy.new()
	ps["projectile"]._apply_modifiers(enemy)
	_assert_eq_int(1, enemy.slowness_applications.size(), "proj_zero_applies")
	if enemy.slowness_applications.size() > 0:
		_assert_eq_float(0.0, enemy.slowness_applications[0]["multiplier"], "proj_zero_mult")
	enemy.free()
	(ps["root"] as Node).free()

func test_projectile_path_slow_tiny_positive() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.01, "slow_duration": 1.5})
	var enemy = MockEnemy.new()
	ps["projectile"]._apply_modifiers(enemy)
	_assert_eq_int(1, enemy.slowness_applications.size(), "proj_tiny_applies")
	if enemy.slowness_applications.size() > 0:
		_assert_eq_float(0.01, enemy.slowness_applications[0]["multiplier"], "proj_tiny_mult")
		_assert_eq_float(1.5, enemy.slowness_applications[0]["duration"], "proj_tiny_dur")
	enemy.free()
	(ps["root"] as Node).free()


# ---------------------------------------------------------------------------
# 9. AttackDatabase duplicate registration
#    Targets: register_base_attack() overwrite behavior for same key
# ---------------------------------------------------------------------------

func test_duplicate_registration_overwrites() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var original = db.get_base_attack("claw")
	var imposter = AttackResource.new()
	imposter.attack_id = 99
	imposter.damage = 999.0
	imposter.effect_type = "MELEE_SWIPE"
	db.register_base_attack("claw", imposter)
	var retrieved = db.get_base_attack("claw")
	_assert_eq_int(99, retrieved.attack_id, "overwrite_replaces_attack_id")
	_assert_eq_float(999.0, retrieved.damage, "overwrite_replaces_damage")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_duplicate_registration_does_not_increase_count() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var initial_count = db.get_base_attack_count()
	var dup = AttackResource.new()
	dup.effect_type = "PROJECTILE_SPIT"
	db.register_base_attack("claw", dup)
	_assert_eq_int(initial_count, db.get_base_attack_count(), "count_unchanged_on_overwrite")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_empty_mutation_id_rejected() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var initial_count = db.get_base_attack_count()
	var res = AttackResource.new()
	res.effect_type = "MELEE_SWIPE"
	db.register_base_attack("", res)
	_assert_eq_int(initial_count, db.get_base_attack_count(), "empty_id_rejected")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_null_resource_rejected() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var initial_count = db.get_base_attack_count()
	db.register_base_attack("test_null", null)
	_assert_eq_int(initial_count, db.get_base_attack_count(), "null_resource_rejected")
	_assert_false(db.has_base_attack("test_null"), "null_not_registered")
	if tree:
		db.queue_free()
	else:
		db.free()


# ---------------------------------------------------------------------------
# 10. Cooldown boundary precision (exactly 2.5s)
#     Targets: AttackResource.cooldown value fidelity
# ---------------------------------------------------------------------------

func test_cooldown_value_exact() -> void:
	var res = _make_adhesion_resource()
	_assert_true(absf(res.cooldown - 2.5) < 1e-10, "cooldown_exact_2_5")

func test_cooldown_distinguishable_from_acid() -> void:
	var adhesion = _make_adhesion_resource()
	_assert_true(adhesion.cooldown != 2.0, "cooldown_not_acid_2_0")

func test_cooldown_distinguishable_from_carapace() -> void:
	var adhesion = _make_adhesion_resource()
	_assert_true(adhesion.cooldown != 3.5, "cooldown_not_carapace_3_5")

func test_lifetime_shorter_than_cooldown() -> void:
	var res = _make_adhesion_resource()
	_assert_true(res.projectile_lifetime < res.cooldown, "lifetime_lt_cooldown")

func test_effective_range_is_10_units() -> void:
	var res = _make_adhesion_resource()
	var effective_range = res.projectile_speed * res.projectile_lifetime
	_assert_eq_float(10.0, effective_range, "effective_range_10")


# ---------------------------------------------------------------------------
# Combinatorial: root + lifetime expiry interaction
# ---------------------------------------------------------------------------

func test_projectile_expires_mid_flight_no_root_applied() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": 1.0}, 1.0, 8.0, 1.25)
	var proj = ps["projectile"]
	proj._physics_process(1.3)
	_assert_true(proj._consumed, "expired_mid_flight")
	var enemy = MockEnemy.new()
	proj._on_body_entered(enemy)
	_assert_eq_int(0, enemy.damage_taken.size(), "expired_proj_no_damage")
	_assert_eq_int(0, enemy.slowness_applications.size(), "expired_proj_no_root")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()


# ---------------------------------------------------------------------------
# Combinatorial: modifier dict mutation safety
# ---------------------------------------------------------------------------

func test_modifiers_dict_is_duplicated_not_shared() -> void:
	var scene = _build_scene("mod_dup", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var res = _make_adhesion_resource()
	var original_mods = res.modifiers.duplicate()
	var log: Array = []
	scene["executor"].connect("projectile_fired", func(p, r): log.append(p))
	scene["executor"].execute_attack(res)
	if log.size() > 0:
		log[0].modifiers["injected_key"] = true
		_assert_false(res.modifiers.has("injected_key"), "proj_mods_isolated_from_resource")
	else:
		_fail_test("mod_dup", "no projectile spawned")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Stress: rapid successive calls to set_slowness
# ---------------------------------------------------------------------------

func test_rapid_set_slowness_100_times() -> void:
	var tracker = EnemyEffectTracker.new()
	for i in range(100):
		tracker.set_slowness(0.0, 1.0)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "100_roots_still_zero")
	tracker._tick_slowness(1.01)
	_assert_eq_float(1.0, tracker.get_speed_multiplier(), "100_roots_single_expiry")
	tracker.free()


# ---------------------------------------------------------------------------
# Assumption check: DEFAULT_SLOW_DURATION fallback
# ---------------------------------------------------------------------------

func test_missing_slow_duration_uses_default() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("default_dur", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	executor._apply_modifiers(enemy, {"slow": 0.3})
	_assert_eq_int(1, enemy.slowness_applications.size(), "fallback_applied")
	if enemy.slowness_applications.size() > 0:
		_assert_eq_float(1.5, enemy.slowness_applications[0]["duration"], "default_1_5s")
	enemy.free()
	executor.free()


# ---------------------------------------------------------------------------
# Determinism: same scenario twice yields identical results
# ---------------------------------------------------------------------------

func test_deterministic_root_tick_sequence() -> void:
	var results_a: Array = []
	var results_b: Array = []
	for run in range(2):
		var tracker = EnemyEffectTracker.new()
		tracker.set_slowness(0.0, 1.0)
		var seq: Array = []
		for i in range(10):
			tracker._tick_slowness(0.1)
			seq.append(tracker.get_speed_multiplier())
		if run == 0:
			results_a = seq
		else:
			results_b = seq
		tracker.free()
	var all_match := true
	for i in range(results_a.size()):
		if absf(results_a[i] - results_b[i]) > 1e-10:
			all_match = false
			break
	_assert_true(all_match, "deterministic_tick_sequence")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AdhesionAttackAdversarialTests ===")

	# 1. Root duration boundary
	test_root_duration_exactly_at_boundary()
	test_root_duration_one_frame_under()
	test_root_duration_one_frame_over()
	test_root_duration_epsilon_under()
	test_root_duration_multi_tick_accumulates_correctly()
	test_root_duration_zero_duration_rejected()
	test_root_negative_duration_rejected()

	# 2. Double-root stacking
	test_double_root_does_not_stack_duration()
	test_double_root_stacking_hypothetical_failure()
	test_triple_root_refresh()
	test_weaker_slow_overwrites_root()

	# 3. Dead enemy hit
	test_dead_enemy_still_receives_body_entered()
	test_dead_enemy_slow_still_dispatched()
	test_executor_infect_weakened_guards_dead()

	# 4. Wall collision at exact enemy position
	test_wall_then_enemy_same_position()
	test_enemy_then_wall_same_position()
	test_two_walls_sequential()
	test_consumed_projectile_ignores_all_subsequent()

	# 5. Zero-speed projectile
	test_zero_speed_projectile_stays_in_place()
	test_zero_speed_projectile_still_despawns_on_lifetime()
	test_zero_speed_projectile_can_still_hit_overlapping_enemy()
	test_negative_speed_projectile_moves_backward()

	# 6. Multiple projectiles in flight
	test_two_projectiles_independent_consumed_state()
	test_two_projectiles_independent_damage()
	test_two_projectiles_same_enemy()
	test_projectile_age_independent_across_instances()

	# 7. Root on WEAKENED enemy
	test_root_on_weakened_does_not_infect()
	test_root_on_infected_does_not_change_state()
	test_adhesion_then_claw_on_normal_does_not_infect()

	# 8. apply_slowness(0.0) vs small values
	test_slow_exactly_zero_applies_root()
	test_slow_tiny_positive_applies()
	test_slow_one_full_speed_applies()
	test_slow_negative_value_passes_through()
	test_effect_tracker_clamps_negative_multiplier()
	test_projectile_path_slow_exactly_zero()
	test_projectile_path_slow_tiny_positive()

	# 9. AttackDatabase duplicate registration
	test_duplicate_registration_overwrites()
	test_duplicate_registration_does_not_increase_count()
	test_empty_mutation_id_rejected()
	test_null_resource_rejected()

	# 10. Cooldown boundary precision
	test_cooldown_value_exact()
	test_cooldown_distinguishable_from_acid()
	test_cooldown_distinguishable_from_carapace()
	test_lifetime_shorter_than_cooldown()
	test_effective_range_is_10_units()

	# Combinatorial
	test_projectile_expires_mid_flight_no_root_applied()
	test_modifiers_dict_is_duplicated_not_shared()

	# Stress
	test_rapid_set_slowness_100_times()

	# Assumption check
	test_missing_slow_duration_uses_default()

	# Determinism
	test_deterministic_root_tick_sequence()

	print("AdhesionAttackAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
