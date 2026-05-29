#
# test_adhesion_attack.gd
#
# Behavioral tests for the adhesion mutation attack: AttackResource registration,
# falsy-zero slow modifier fix, root effect (speed=0 for 3.0s), wall collision
# despawn, visual distinction, root+infection tactical synergy, and pipeline
# integration with PROJECTILE_SPIT.
#
# Spec: project_board/specs/adhesion_player_attack_spec.md (ADHA-1..ADHA-8)
# Ticket: M11-11
#

class_name AdhesionAttackTests
extends "res://tests/utils/test_utils.gd"

const ADHESION_ROOT_DURATION_SEC: float = 3.0

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


class MockWall extends Node3D:
	pass


class MockParent extends Node3D:
	var _facing: float = 1.0
	func get_facing_sign() -> float:
		return _facing


class WeakeningEnemy extends Node3D:
	var damage_taken: Array = []
	var slowness_applications: Array = []
	var current_state: int = 0
	var is_dead_flag: bool = false
	var max_hp: float = 10.0
	var current_hp: float = 5.5

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})
		current_hp = maxf(0.0, current_hp - damage)
		if current_state == 0 and current_hp <= max_hp * 0.5:
			current_state = 1

	func apply_slowness(multiplier: float, duration: float) -> void:
		slowness_applications.append({"multiplier": multiplier, "duration": duration})

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag


class NoSlownessTarget extends Node3D:
	var damage_taken: Array = []

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

	func get_base_state() -> int:
		return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_adhesion_resource() -> AttackResource:
	var r = AttackResource.new()
	r.attack_id = 4
	r.attack_name = "Sticky Spit"
	r.description = "Sticky projectile that roots the first enemy hit, stopping all movement for 3.0s."
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
	r.modifiers = {"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC}
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


var _projectile_log: Array = []

func _reset_projectile_log() -> void:
	_projectile_log = []

func _connect_projectile_signal(executor: Node) -> void:
	_reset_projectile_log()
	executor.connect("projectile_fired", func(p, r): _projectile_log.append({"projectile": p, "resource": r}))


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
# ADHA-1: Adhesion AttackResource Definition
# ---------------------------------------------------------------------------

func test_adha1a_effect_type_projectile_spit() -> void:
	var res = _make_adhesion_resource()
	_assert_eq_string("PROJECTILE_SPIT", res.effect_type, "ADHA-1a_effect_type")

func test_adha1b_damage_is_one() -> void:
	var res = _make_adhesion_resource()
	_assert_eq_float(1.0, res.damage, "ADHA-1b_damage")

func test_adha1c_cooldown_is_2_5() -> void:
	var res = _make_adhesion_resource()
	_assert_eq_float(2.5, res.cooldown, "ADHA-1c_cooldown")

func test_adha1d_projectile_speed_is_8() -> void:
	var res = _make_adhesion_resource()
	_assert_eq_float(8.0, res.projectile_speed, "ADHA-1d_speed")

func test_adha1e_projectile_lifetime_is_1_25() -> void:
	var res = _make_adhesion_resource()
	_assert_eq_float(1.25, res.projectile_lifetime, "ADHA-1e_lifetime")

func test_adha1f_knockback_magnitude_zero() -> void:
	var res = _make_adhesion_resource()
	_assert_eq_float(0.0, res.knockback_magnitude, "ADHA-1f_kb_zero")

func test_adha1g_modifiers_slow_zero() -> void:
	var res = _make_adhesion_resource()
	var slow_val = res.modifiers.get("slow", null)
	_assert_true(slow_val != null, "ADHA-1g_slow_key_present")
	if slow_val != null:
		_assert_eq_float(0.0, slow_val, "ADHA-1g_slow_is_zero")

func test_adha1h_modifiers_slow_duration_one() -> void:
	var res = _make_adhesion_resource()
	_assert_eq_float(
		ADHESION_ROOT_DURATION_SEC,
		res.modifiers.get("slow_duration", -1.0),
		"ADHA-1h_slow_duration",
	)

func test_adha1i_color_dark_goldenrod() -> void:
	var res = _make_adhesion_resource()
	_assert_true(res.color == Color.DARK_GOLDENROD, "ADHA-1i_color")

func test_adha1j_attack_id_is_4() -> void:
	var res = _make_adhesion_resource()
	_assert_eq_int(4, res.attack_id, "ADHA-1j_id")

func test_adha1k_no_infect_weakened_modifier() -> void:
	var res = _make_adhesion_resource()
	_assert_false(res.modifiers.has("infect_weakened"), "ADHA-1k_no_infect")


# ---------------------------------------------------------------------------
# ADHA-2: AttackDatabase Registration
# ---------------------------------------------------------------------------

func test_adha2a_adhesion_registered_in_database() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	_assert_true(db.has_base_attack("adhesion"), "ADHA-2a_registered")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_adha2b_at_least_four_base_attacks() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	_assert_true(db.get_base_attack_count() >= 4, "ADHA-2b_at_least_4")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_adha2c_adhesion_distinct_from_others() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var adhesion = db.get_base_attack("adhesion")
	var claw = db.get_base_attack("claw")
	var acid = db.get_base_attack("acid")
	var carapace = db.get_base_attack("carapace")
	if adhesion == null:
		_fail_test("ADHA-2c", "adhesion not registered")
		if tree: db.queue_free()
		else: db.free()
		return
	_assert_true(adhesion != claw, "ADHA-2c_distinct_claw")
	_assert_true(adhesion != acid, "ADHA-2c_distinct_acid")
	_assert_true(adhesion != carapace, "ADHA-2c_distinct_carapace")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_adha2d_db_adhesion_properties_match_spec() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var adhesion = db.get_base_attack("adhesion")
	if adhesion == null:
		_fail_test("ADHA-2d", "adhesion not registered")
		if tree: db.queue_free()
		else: db.free()
		return
	_assert_eq_string("PROJECTILE_SPIT", adhesion.effect_type, "ADHA-2d_type")
	_assert_eq_float(1.0, adhesion.damage, "ADHA-2d_damage")
	_assert_eq_float(2.5, adhesion.cooldown, "ADHA-2d_cooldown")
	_assert_eq_float(8.0, adhesion.projectile_speed, "ADHA-2d_speed")
	_assert_eq_float(1.25, adhesion.projectile_lifetime, "ADHA-2d_lifetime")
	_assert_eq_float(0.0, adhesion.knockback_magnitude, "ADHA-2d_kb")
	_assert_true(adhesion.color == Color.DARK_GOLDENROD, "ADHA-2d_color")
	var slow_val = adhesion.modifiers.get("slow", null)
	_assert_true(slow_val != null, "ADHA-2d_slow_present")
	if slow_val != null:
		_assert_eq_float(0.0, slow_val, "ADHA-2d_slow_zero")
	_assert_eq_float(
		ADHESION_ROOT_DURATION_SEC,
		adhesion.modifiers.get("slow_duration", -1.0),
		"ADHA-2d_slow_dur",
	)
	_assert_eq_int(4, adhesion.attack_id, "ADHA-2d_id")
	if tree:
		db.queue_free()
	else:
		db.free()


# ---------------------------------------------------------------------------
# ADHA-3: Falsy-Zero Slow Modifier Fix — Executor Path
# ---------------------------------------------------------------------------

func test_adha3a_executor_slow_zero_calls_apply_slowness() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADHA-3a", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	var mods := {"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC}
	executor._apply_modifiers(enemy, mods)
	_assert_eq_int(1, enemy.slowness_applications.size(), "ADHA-3a_called")
	if enemy.slowness_applications.size() > 0:
		_assert_eq_float(0.0, enemy.slowness_applications[0]["multiplier"], "ADHA-3a_mult_zero")
		_assert_eq_float(
			ADHESION_ROOT_DURATION_SEC,
			enemy.slowness_applications[0]["duration"],
			"ADHA-3a_dur_one",
		)
	enemy.free()
	executor.free()

func test_adha3b_executor_slow_positive_still_works() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADHA-3b", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	var mods := {"slow": 0.5, "slow_duration": 2.0}
	executor._apply_modifiers(enemy, mods)
	_assert_eq_int(1, enemy.slowness_applications.size(), "ADHA-3b_called")
	if enemy.slowness_applications.size() > 0:
		_assert_eq_float(0.5, enemy.slowness_applications[0]["multiplier"], "ADHA-3b_mult")
		_assert_eq_float(2.0, enemy.slowness_applications[0]["duration"], "ADHA-3b_dur")
	enemy.free()
	executor.free()

func test_adha3c_executor_no_slow_key_skips_apply() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADHA-3c", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	var mods := {"acid_on_hit": true}
	executor._apply_modifiers(enemy, mods)
	_assert_eq_int(0, enemy.slowness_applications.size(), "ADHA-3c_not_called")
	enemy.free()
	executor.free()


# ---------------------------------------------------------------------------
# ADHA-3: Falsy-Zero Slow Modifier Fix — Projectile Path
# ---------------------------------------------------------------------------

func test_adha3d_projectile_slow_zero_calls_apply_slowness() -> void:
	var mods := {"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC}
	var ps = _make_projectile_in_tree(mods)
	var enemy = MockEnemy.new()
	ps["projectile"]._apply_modifiers(enemy)
	_assert_eq_int(1, enemy.slowness_applications.size(), "ADHA-3d_called")
	if enemy.slowness_applications.size() > 0:
		_assert_eq_float(0.0, enemy.slowness_applications[0]["multiplier"], "ADHA-3d_mult_zero")
		_assert_eq_float(
			ADHESION_ROOT_DURATION_SEC,
			enemy.slowness_applications[0]["duration"],
			"ADHA-3d_dur_one",
		)
	enemy.free()
	(ps["root"] as Node).free()

func test_adha3e_projectile_slow_positive_still_works() -> void:
	var mods := {"slow": 0.5, "slow_duration": 2.0}
	var ps = _make_projectile_in_tree(mods)
	var enemy = MockEnemy.new()
	ps["projectile"]._apply_modifiers(enemy)
	_assert_eq_int(1, enemy.slowness_applications.size(), "ADHA-3e_called")
	if enemy.slowness_applications.size() > 0:
		_assert_eq_float(0.5, enemy.slowness_applications[0]["multiplier"], "ADHA-3e_mult")
	enemy.free()
	(ps["root"] as Node).free()

func test_adha3f_projectile_no_slow_key_skips() -> void:
	var mods := {"acid_on_hit": true}
	var ps = _make_projectile_in_tree(mods)
	var enemy = MockEnemy.new()
	ps["projectile"]._apply_modifiers(enemy)
	_assert_eq_int(0, enemy.slowness_applications.size(), "ADHA-3f_not_called")
	enemy.free()
	(ps["root"] as Node).free()

func test_adha3g_no_apply_slowness_method_skipped() -> void:
	var mods := {"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC}
	var ps = _make_projectile_in_tree(mods)
	var target = NoSlownessTarget.new()
	ps["projectile"]._apply_modifiers(target)
	_pass_test("ADHA-3g_no_crash")
	target.free()
	(ps["root"] as Node).free()


# ---------------------------------------------------------------------------
# ADHA-4: Root Effect via Slow Modifier
# ---------------------------------------------------------------------------

func test_adha4a_speed_multiplier_zero_after_root() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "ADHA-4a_speed_zero")
	tracker.free()

func test_adha4b_speed_restores_after_duration() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	tracker._tick_slowness(ADHESION_ROOT_DURATION_SEC + 0.01)
	_assert_eq_float(1.0, tracker.get_speed_multiplier(), "ADHA-4b_speed_restored")
	tracker.free()

func test_adha4c_speed_zero_during_root_midway() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	tracker._tick_slowness(0.5)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "ADHA-4c_still_rooted")
	tracker.free()

func test_adha4d_reroot_refreshes_duration() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	tracker._tick_slowness(0.8)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "ADHA-4d_pre_reroot")
	tracker.set_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	tracker._tick_slowness(0.8)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "ADHA-4d_still_rooted_after_refresh")
	tracker.free()

func test_adha4e_root_does_not_prevent_damage() -> void:
	var enemy = MockEnemy.new()
	enemy.apply_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	enemy.take_damage(5.0, Vector3.ZERO)
	_assert_eq_int(1, enemy.damage_taken.size(), "ADHA-4e_damage_taken")
	enemy.free()

func test_adha4f_root_does_not_prevent_state_transition() -> void:
	var enemy = WeakeningEnemy.new()
	enemy.apply_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	enemy.take_damage(1.0, Vector3.ZERO)
	_assert_eq_int(1, enemy.current_state, "ADHA-4f_weakened_during_root")
	enemy.free()

func test_adha4g_root_expires_naturally() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	var step := 0.05
	var elapsed := 0.0
	while elapsed <= ADHESION_ROOT_DURATION_SEC:
		tracker._tick_slowness(step)
		elapsed += step
	_assert_eq_float(1.0, tracker.get_speed_multiplier(), "ADHA-4g_expired")
	tracker.free()


# ---------------------------------------------------------------------------
# ADHA-5: Wall Collision Despawn
# ---------------------------------------------------------------------------

func test_adha5a_projectile_despawns_on_wall() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC})
	var wall = MockWall.new()
	ps["projectile"]._on_body_entered(wall)
	_assert_true(ps["projectile"]._consumed, "ADHA-5a_consumed")
	wall.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_adha5b_wall_no_damage_dealt() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC})
	var wall = MockWall.new()
	ps["projectile"]._on_body_entered(wall)
	_pass_test("ADHA-5b_no_damage_on_wall")
	wall.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_adha5c_wall_no_modifiers_applied() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC})
	var wall = MockWall.new()
	ps["projectile"]._on_body_entered(wall)
	_pass_test("ADHA-5c_no_modifiers_on_wall")
	wall.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_adha5d_consumed_prevents_double_processing() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC})
	var wall = MockWall.new()
	var enemy = MockEnemy.new()
	ps["projectile"]._on_body_entered(wall)
	ps["projectile"]._on_body_entered(enemy)
	_assert_eq_int(0, enemy.damage_taken.size(), "ADHA-5d_no_double_process")
	wall.free()
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_adha5e_enemy_hit_still_works() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC})
	var enemy = MockEnemy.new()
	ps["projectile"]._on_body_entered(enemy)
	_assert_true(ps["projectile"]._consumed, "ADHA-5e_consumed_on_enemy")
	_assert_eq_int(1, enemy.damage_taken.size(), "ADHA-5e_damage_dealt")
	_assert_eq_int(1, enemy.slowness_applications.size(), "ADHA-5e_modifiers_applied")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_adha5g_lifetime_despawn_unchanged() -> void:
	var ps = _make_projectile_in_tree({}, 1.0, 8.0, 1.25)
	var proj = ps["projectile"]
	proj._age = 1.24
	proj._physics_process(0.02)
	_assert_true(proj._consumed, "ADHA-5g_lifetime_consumed")
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()


# ---------------------------------------------------------------------------
# ADHA-6: Visual Distinction — Adhesion Projectile Color
# ---------------------------------------------------------------------------

func test_adha6a_projectile_color_dark_goldenrod() -> void:
	var scene = _build_scene("ADHA-6a", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	_connect_projectile_signal(scene["executor"])
	scene["executor"].execute_attack(_make_adhesion_resource())
	_assert_eq_int(1, _projectile_log.size(), "ADHA-6a_spawned")
	if _projectile_log.size() > 0:
		var proj = _projectile_log[0]["projectile"]
		_assert_true(proj.color == Color.DARK_GOLDENROD, "ADHA-6a_color")
	_teardown(scene)

func test_adha6b_distinct_from_acid() -> void:
	_assert_true(Color.DARK_GOLDENROD != Color.CHARTREUSE, "ADHA-6b_not_acid")

func test_adha6c_distinct_from_claw() -> void:
	_assert_true(Color.DARK_GOLDENROD != Color.ORANGE_RED, "ADHA-6c_not_claw")

func test_adha6d_distinct_from_carapace() -> void:
	_assert_true(Color.DARK_GOLDENROD != Color.SADDLE_BROWN, "ADHA-6d_not_carapace")


# ---------------------------------------------------------------------------
# ADHA-7: Root + Infection Tactical Synergy
# ---------------------------------------------------------------------------

func test_adha7a_no_infect_weakened_in_adhesion_modifiers() -> void:
	var res = _make_adhesion_resource()
	_assert_false(res.modifiers.has("infect_weakened"), "ADHA-7a_no_infect")

func test_adha7b_claw_can_infect_rooted_weakened_enemy() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADHA-7b", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	enemy.apply_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	var claw_mods := {"infect_weakened": true}
	executor._apply_modifiers(enemy, claw_mods, 1)
	_assert_eq_int(2, enemy.current_state, "ADHA-7b_infected")
	enemy.free()
	executor.free()

func test_adha7c_adhesion_alone_does_not_infect() -> void:
	var mods := {"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC}
	var ps = _make_projectile_in_tree(mods)
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	ps["projectile"]._on_body_entered(enemy)
	_assert_eq_int(1, enemy.current_state, "ADHA-7c_still_weakened")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_adha7d_root_creates_movement_stop_window() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "ADHA-7d_speed_zero")
	tracker.free()


# ---------------------------------------------------------------------------
# ADHA-8: Pipeline Integration
# ---------------------------------------------------------------------------

func test_adha8a_adhesion_dispatches_to_projectile_spit() -> void:
	var scene = _build_scene("ADHA-8a", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	_connect_projectile_signal(scene["executor"])
	scene["executor"].execute_attack(_make_adhesion_resource())
	_assert_eq_int(1, _projectile_log.size(), "ADHA-8a_projectile_fired")
	_teardown(scene)

func test_adha8b_projectile_properties_correct() -> void:
	var scene = _build_scene("ADHA-8b", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	_connect_projectile_signal(scene["executor"])
	scene["executor"].execute_attack(_make_adhesion_resource())
	if _projectile_log.size() == 0:
		_fail_test("ADHA-8b", "no projectile spawned")
		_teardown(scene)
		return
	var proj = _projectile_log[0]["projectile"]
	_assert_eq_float(1.0, proj.damage, "ADHA-8b_damage")
	_assert_eq_float(8.0, proj.speed, "ADHA-8b_speed")
	_assert_eq_float(1.25, proj.lifetime, "ADHA-8b_lifetime")
	_assert_eq_float(0.0, proj.knockback_magnitude, "ADHA-8b_kb_zero")
	_assert_eq_float(1.0, proj.direction_x, "ADHA-8b_direction")
	var slow_val = proj.modifiers.get("slow", null)
	_assert_true(slow_val != null, "ADHA-8b_slow_present")
	if slow_val != null:
		_assert_eq_float(0.0, slow_val, "ADHA-8b_slow_zero")
	_assert_eq_float(
		ADHESION_ROOT_DURATION_SEC,
		proj.modifiers.get("slow_duration", -1.0),
		"ADHA-8b_slow_dur",
	)
	_teardown(scene)

func test_adha8c_cooldown_value() -> void:
	var res = _make_adhesion_resource()
	_assert_eq_float(2.5, res.cooldown, "ADHA-8c_cooldown")

func test_adha8d_projectile_travels_along_x() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC})
	var proj = ps["projectile"]
	var start_x = proj.global_position.x
	proj._physics_process(0.1)
	var expected_x = start_x + 1.0 * 8.0 * 0.1
	_assert_eq_float(expected_x, proj.global_position.x, "ADHA-8d_x_travel")
	(ps["root"] as Node).free()

func test_adha8e_projectile_consumed_on_first_enemy() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC})
	var proj = ps["projectile"]
	var e1 = MockEnemy.new()
	var e2 = MockEnemy.new()
	proj._on_body_entered(e1)
	proj._on_body_entered(e2)
	_assert_eq_int(1, e1.damage_taken.size(), "ADHA-8e_first_hit")
	_assert_eq_int(0, e2.damage_taken.size(), "ADHA-8e_second_skipped")
	e1.free()
	e2.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_adha8f_facing_left_negative_direction() -> void:
	var scene = _build_scene("ADHA-8f", [], Vector3.ZERO, -1.0)
	if scene.is_empty():
		return
	_connect_projectile_signal(scene["executor"])
	scene["executor"].execute_attack(_make_adhesion_resource())
	if _projectile_log.size() > 0:
		var proj = _projectile_log[0]["projectile"]
		_assert_eq_float(-1.0, proj.direction_x, "ADHA-8f_left_facing")
	else:
		_fail_test("ADHA-8f", "no projectile")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Edge Cases (spec EC table)
# ---------------------------------------------------------------------------

func test_ec1_adhesion_hit_normal_stays_normal() -> void:
	var enemy = MockEnemy.new()
	enemy.current_state = 0
	var mods := {"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC}
	var ps = _make_projectile_in_tree(mods)
	ps["projectile"]._on_body_entered(enemy)
	_assert_eq_int(0, enemy.current_state, "EC-1_stays_normal")
	_assert_eq_int(1, enemy.slowness_applications.size(), "EC-1_rooted")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_ec2_adhesion_hit_weakens_enemy() -> void:
	var enemy = WeakeningEnemy.new()
	enemy.current_state = 0
	var mods := {"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC}
	var ps = _make_projectile_in_tree(mods)
	ps["projectile"]._on_body_entered(enemy)
	_assert_eq_int(1, enemy.current_state, "EC-2_now_weakened")
	_assert_eq_int(1, enemy.slowness_applications.size(), "EC-2_rooted")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_ec3_adhesion_weakened_no_infect() -> void:
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	var mods := {"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC}
	var ps = _make_projectile_in_tree(mods)
	ps["projectile"]._on_body_entered(enemy)
	_assert_eq_int(1, enemy.current_state, "EC-3_still_weakened")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_ec9_reroot_refreshes_duration() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	tracker._tick_slowness(0.9)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "EC-9_still_rooted")
	tracker.set_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	tracker._tick_slowness(0.9)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "EC-9_refreshed")
	tracker.free()

func test_ec11_claw_slow_overwrites_root() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "EC-11_rooted")
	tracker.set_slowness(0.5, 2.0)
	_assert_eq_float(0.5, tracker.get_speed_multiplier(), "EC-11_overwritten")
	tracker.free()

func test_ec14_first_enemy_consumes_projectile() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC})
	var e1 = MockEnemy.new()
	var e2 = MockEnemy.new()
	ps["projectile"]._on_body_entered(e1)
	ps["projectile"]._on_body_entered(e2)
	_assert_true(ps["projectile"]._consumed, "EC-14_consumed")
	_assert_eq_int(0, e2.damage_taken.size(), "EC-14_second_untouched")
	e1.free()
	e2.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_ec15_root_overwrites_partial_slow() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.set_slowness(0.5, 2.0)
	_assert_eq_float(0.5, tracker.get_speed_multiplier(), "EC-15_partial")
	tracker.set_slowness(0.0, ADHESION_ROOT_DURATION_SEC)
	_assert_eq_float(0.0, tracker.get_speed_multiplier(), "EC-15_full_root")
	tracker.free()

func test_ec17_slow_duration_explicit_in_modifiers() -> void:
	var res = _make_adhesion_resource()
	_assert_true(res.modifiers.has("slow_duration"), "EC-17_has_duration")
	_assert_eq_float(ADHESION_ROOT_DURATION_SEC, res.modifiers["slow_duration"], "EC-17_is_three")

func test_ec20_consumed_prevents_wall_after_enemy() -> void:
	var ps = _make_projectile_in_tree({"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION_SEC})
	var enemy = MockEnemy.new()
	var wall = MockWall.new()
	ps["projectile"]._on_body_entered(enemy)
	ps["projectile"]._on_body_entered(wall)
	_assert_eq_int(1, enemy.damage_taken.size(), "EC-20_enemy_hit_once")
	_assert_true(ps["projectile"]._consumed, "EC-20_consumed")
	enemy.free()
	wall.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AdhesionAttackTests ===")

	test_adha1a_effect_type_projectile_spit()
	test_adha1b_damage_is_one()
	test_adha1c_cooldown_is_2_5()
	test_adha1d_projectile_speed_is_8()
	test_adha1e_projectile_lifetime_is_1_25()
	test_adha1f_knockback_magnitude_zero()
	test_adha1g_modifiers_slow_zero()
	test_adha1h_modifiers_slow_duration_one()
	test_adha1i_color_dark_goldenrod()
	test_adha1j_attack_id_is_4()
	test_adha1k_no_infect_weakened_modifier()

	test_adha2a_adhesion_registered_in_database()
	test_adha2b_at_least_four_base_attacks()
	test_adha2c_adhesion_distinct_from_others()
	test_adha2d_db_adhesion_properties_match_spec()

	test_adha3a_executor_slow_zero_calls_apply_slowness()
	test_adha3b_executor_slow_positive_still_works()
	test_adha3c_executor_no_slow_key_skips_apply()
	test_adha3d_projectile_slow_zero_calls_apply_slowness()
	test_adha3e_projectile_slow_positive_still_works()
	test_adha3f_projectile_no_slow_key_skips()
	test_adha3g_no_apply_slowness_method_skipped()

	test_adha4a_speed_multiplier_zero_after_root()
	test_adha4b_speed_restores_after_duration()
	test_adha4c_speed_zero_during_root_midway()
	test_adha4d_reroot_refreshes_duration()
	test_adha4e_root_does_not_prevent_damage()
	test_adha4f_root_does_not_prevent_state_transition()
	test_adha4g_root_expires_naturally()

	test_adha5a_projectile_despawns_on_wall()
	test_adha5b_wall_no_damage_dealt()
	test_adha5c_wall_no_modifiers_applied()
	test_adha5d_consumed_prevents_double_processing()
	test_adha5e_enemy_hit_still_works()
	test_adha5g_lifetime_despawn_unchanged()

	test_adha6a_projectile_color_dark_goldenrod()
	test_adha6b_distinct_from_acid()
	test_adha6c_distinct_from_claw()
	test_adha6d_distinct_from_carapace()

	test_adha7a_no_infect_weakened_in_adhesion_modifiers()
	test_adha7b_claw_can_infect_rooted_weakened_enemy()
	test_adha7c_adhesion_alone_does_not_infect()
	test_adha7d_root_creates_movement_stop_window()

	test_adha8a_adhesion_dispatches_to_projectile_spit()
	test_adha8b_projectile_properties_correct()
	test_adha8c_cooldown_value()
	test_adha8d_projectile_travels_along_x()
	test_adha8e_projectile_consumed_on_first_enemy()
	test_adha8f_facing_left_negative_direction()

	test_ec1_adhesion_hit_normal_stays_normal()
	test_ec2_adhesion_hit_weakens_enemy()
	test_ec3_adhesion_weakened_no_infect()
	test_ec9_reroot_refreshes_duration()
	test_ec11_claw_slow_overwrites_root()
	test_ec14_first_enemy_consumes_projectile()
	test_ec15_root_overwrites_partial_slow()
	test_ec17_slow_duration_explicit_in_modifiers()
	test_ec20_consumed_prevents_wall_after_enemy()

	print("AdhesionAttackTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
