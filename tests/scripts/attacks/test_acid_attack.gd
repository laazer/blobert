#
# test_acid_attack.gd
#
# Behavioral tests for the acid mutation attack: AttackResource registration,
# WEAKENED duration doubling, DoT parameters, non-stacking, visual distinction,
# and PROJECTILE_SPIT pipeline integration.
#
# Spec: project_board/specs/acid_player_attack_spec.md (APA-1..APA-7)
# Ticket: M11-09
#

class_name AcidAttackTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Mock inner classes
# ---------------------------------------------------------------------------

class MockEnemy extends Node3D:
	var damage_taken: Array = []
	var acid_calls: Array = []
	var poison_calls: Array = []
	var current_state: int = 0
	var is_dead_flag: bool = false

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

	func apply_acid(duration: float, dps: float) -> void:
		acid_calls.append({"duration": duration, "dps": dps})

	func apply_poison(duration: float, dps: float) -> void:
		poison_calls.append({"duration": duration, "dps": dps})

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag


class AcidWeakeningEnemy extends Node3D:
	var damage_taken: Array = []
	var acid_calls: Array = []
	var current_state: int = 0
	var is_dead_flag: bool = false
	var max_hp: float = 4.0
	var current_hp: float = 2.5

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})
		current_hp = maxf(0.0, current_hp - damage)
		if current_state == 0 and current_hp <= max_hp * 0.5:
			current_state = 1

	func apply_acid(duration: float, dps: float) -> void:
		acid_calls.append({"duration": duration, "dps": dps})

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag


class NoAcidTarget extends Node3D:
	var damage_taken: Array = []

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

	func get_base_state() -> int:
		return 0


class NoStateTarget extends Node3D:
	var acid_calls: Array = []
	var damage_taken: Array = []

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

	func apply_acid(duration: float, dps: float) -> void:
		acid_calls.append({"duration": duration, "dps": dps})


class MockParent extends Node3D:
	var _facing: float = 1.0
	func get_facing_sign() -> float:
		return _facing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_acid_resource() -> AttackResource:
	var r = AttackResource.new()
	r.attack_id = 2
	r.attack_name = "Acid Spit"
	r.description = "Ranged acid projectile. Applies damage over time. WEAKENED enemies suffer double duration."
	r.effect_type = "PROJECTILE_SPIT"
	r.damage = 1.0
	r.cooldown = 2.0
	r.attack_range = 0.0
	r.startup_frames = 0
	r.knockback_magnitude = 0.0
	r.knockback_direction = "none"
	r.projectile_speed = 8.0
	r.projectile_lifetime = 2.0
	r.color = Color.CHARTREUSE
	r.vfx_scale = 1.0
	r.modifiers = {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	return r


func _make_resource(overrides: Dictionary = {}) -> AttackResource:
	var r = AttackResource.new()
	r.startup_frames = 0
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


var _projectile_log: Array = []

func _reset_projectile_log() -> void:
	_projectile_log = []

func _connect_projectile_signal(executor: Node) -> void:
	_reset_projectile_log()
	executor.connect("projectile_fired", func(p, r): _projectile_log.append({"projectile": p, "resource": r}))


func _make_projectile_in_tree(mods: Dictionary = {}, dmg: float = 1.0) -> Dictionary:
	var root = Node3D.new()
	var proj = PlayerProjectile3D.new()
	proj.damage = dmg
	proj.speed = 8.0
	proj.knockback_magnitude = 0.0
	proj.knockback_direction = "none"
	proj.modifiers = mods
	proj.direction_x = 1.0
	root.add_child(proj)
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(root)
	return {"root": root, "projectile": proj}


# ---------------------------------------------------------------------------
# APA-1: Acid AttackResource Definition
# ---------------------------------------------------------------------------

func test_apa1_acid_resource_properties() -> void:
	var acid = _make_acid_resource()
	_assert_eq_int(2, acid.attack_id, "APA-1j_attack_id")
	_assert_eq_string("Acid Spit", acid.attack_name, "APA-1_name")
	_assert_eq_string("PROJECTILE_SPIT", acid.effect_type, "APA-1a_effect_type")
	_assert_eq_float(1.0, acid.damage, "APA-1b_damage")
	_assert_eq_float(2.0, acid.cooldown, "APA-1c_cooldown")
	_assert_eq_float(8.0, acid.projectile_speed, "APA-1d_speed")
	_assert_eq_float(0.0, acid.knockback_magnitude, "APA-1e_no_knockback")
	_assert_true(acid.modifiers.get("acid_on_hit", false) == true, "APA-1f_acid_on_hit")
	_assert_eq_float(3.0, acid.modifiers.get("acid_duration", 0.0), "APA-1g_acid_duration")
	_assert_eq_float(1.0, acid.modifiers.get("acid_dps", 0.0), "APA-1h_acid_dps")
	_assert_true(acid.color == Color.CHARTREUSE, "APA-1i_color")
	_assert_eq_float(0.0, acid.attack_range, "APA-1_range_zero")
	_assert_eq_int(0, acid.startup_frames, "APA-1_startup_zero")
	_assert_eq_string("none", acid.knockback_direction, "APA-1_kb_direction_none")


# ---------------------------------------------------------------------------
# APA-2: AttackDatabase Registration
# ---------------------------------------------------------------------------

func test_apa2a_register_defaults_creates_acid() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	_assert_true(db.has_base_attack("acid"), "APA-2a_acid_registered")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_apa2b_at_least_two_base_attacks() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	_assert_true(db.get_base_attack_count() >= 2, "APA-2b_at_least_two")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_apa2c_acid_distinct_from_claw() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var acid = db.get_base_attack("acid")
	var claw = db.get_base_attack("claw")
	if acid == null or claw == null:
		_fail_test("APA-2c", "acid or claw not registered")
		if tree: db.queue_free()
		else: db.free()
		return
	_assert_true(acid != claw, "APA-2c_distinct_instances")
	_assert_true(acid.effect_type != claw.effect_type, "APA-2c_distinct_types")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_apa2d_acid_defaults_properties() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var acid = db.get_base_attack("acid")
	if acid == null:
		_fail_test("APA-2d", "acid not registered by _register_defaults()")
		if tree: db.queue_free()
		else: db.free()
		return
	_assert_eq_string("PROJECTILE_SPIT", acid.effect_type, "APA-2d_type")
	_assert_eq_float(1.0, acid.damage, "APA-2d_damage")
	_assert_eq_float(2.0, acid.cooldown, "APA-2d_cooldown")
	_assert_eq_float(8.0, acid.projectile_speed, "APA-2d_speed")
	_assert_eq_float(0.0, acid.knockback_magnitude, "APA-2d_kb")
	_assert_true(acid.modifiers.get("acid_on_hit", false) == true, "APA-2d_mod")
	_assert_eq_float(3.0, acid.modifiers.get("acid_duration", 0.0), "APA-2d_dur")
	_assert_eq_float(1.0, acid.modifiers.get("acid_dps", 0.0), "APA-2d_dps")
	_assert_true(acid.color == Color.CHARTREUSE, "APA-2d_color")
	_assert_eq_int(2, acid.attack_id, "APA-2d_id")
	if tree:
		db.queue_free()
	else:
		db.free()


# ---------------------------------------------------------------------------
# APA-3: WEAKENED Doubles Duration — Executor Path
# Uses post-damage state (target.get_base_state()), not pre_damage_state arg.
# ---------------------------------------------------------------------------

func test_apa3a_executor_normal_base_duration() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("APA-3a", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 0
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(enemy, mods)
	_assert_eq_int(1, enemy.acid_calls.size(), "APA-3a_applied")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(3.0, enemy.acid_calls[0]["duration"], "APA-3a_dur_3")
		_assert_eq_float(1.0, enemy.acid_calls[0]["dps"], "APA-3a_dps_1")
	enemy.free()
	executor.free()

func test_apa3b_executor_weakened_doubled() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("APA-3b", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(enemy, mods)
	_assert_eq_int(1, enemy.acid_calls.size(), "APA-3b_applied")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(6.0, enemy.acid_calls[0]["duration"], "APA-3b_dur_6")
	enemy.free()
	executor.free()

func test_apa3c_executor_infected_base_duration() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("APA-3c", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 2
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(enemy, mods)
	_assert_eq_int(1, enemy.acid_calls.size(), "APA-3c_applied")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(3.0, enemy.acid_calls[0]["duration"], "APA-3c_dur_3")
	enemy.free()
	executor.free()

func test_apa3d_executor_no_state_method_fallback() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("APA-3d", "executor not loadable")
		return
	var target = NoStateTarget.new()
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(target, mods)
	_assert_eq_int(1, target.acid_calls.size(), "APA-3d_applied")
	if target.acid_calls.size() > 0:
		_assert_eq_float(3.0, target.acid_calls[0]["duration"], "APA-3d_dur_3")
	target.free()
	executor.free()

func test_apa3e_executor_dps_unchanged_when_weakened() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("APA-3e", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(enemy, mods)
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(1.0, enemy.acid_calls[0]["dps"], "APA-3h_dps_not_doubled")
	else:
		_fail_test("APA-3e", "acid not applied")
	enemy.free()
	executor.free()


# ---------------------------------------------------------------------------
# APA-3: WEAKENED Doubles Duration — Projectile Path
# ---------------------------------------------------------------------------

func test_apa3f_projectile_normal_base_duration() -> void:
	var acid_mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	var ps = _make_projectile_in_tree(acid_mods)
	var enemy = MockEnemy.new()
	enemy.current_state = 0
	ps["projectile"]._apply_modifiers(enemy)
	_assert_eq_int(1, enemy.acid_calls.size(), "APA-3f_applied")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(3.0, enemy.acid_calls[0]["duration"], "APA-3f_dur_3")
	enemy.free()
	(ps["root"] as Node).free()

func test_apa3g_projectile_weakened_doubled() -> void:
	var acid_mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	var ps = _make_projectile_in_tree(acid_mods)
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	ps["projectile"]._apply_modifiers(enemy)
	_assert_eq_int(1, enemy.acid_calls.size(), "APA-3g_applied")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(6.0, enemy.acid_calls[0]["duration"], "APA-3g_dur_6")
	enemy.free()
	(ps["root"] as Node).free()

func test_apa3h_projectile_infected_base_duration() -> void:
	var acid_mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	var ps = _make_projectile_in_tree(acid_mods)
	var enemy = MockEnemy.new()
	enemy.current_state = 2
	ps["projectile"]._apply_modifiers(enemy)
	_assert_eq_int(1, enemy.acid_calls.size(), "APA-3h_applied")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(3.0, enemy.acid_calls[0]["duration"], "APA-3h_dur_3")
	enemy.free()
	(ps["root"] as Node).free()

func test_apa3i_projectile_hit_weakens_acid_doubled() -> void:
	var acid_mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	var ps = _make_projectile_in_tree(acid_mods)
	var enemy = AcidWeakeningEnemy.new()
	ps["projectile"]._on_body_entered(enemy)
	_assert_eq_int(1, enemy.current_state, "APA-3i_weakened_from_hit")
	_assert_eq_int(1, enemy.acid_calls.size(), "APA-3i_acid_applied")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(6.0, enemy.acid_calls[0]["duration"], "APA-3i_dur_doubled")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_apa3j_both_paths_identical_output() -> void:
	var acid_mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("APA-3g_both", "executor not loadable")
		return
	var e1 = MockEnemy.new()
	e1.current_state = 1
	executor._apply_modifiers(e1, acid_mods)

	var ps = _make_projectile_in_tree(acid_mods)
	var e2 = MockEnemy.new()
	e2.current_state = 1
	ps["projectile"]._apply_modifiers(e2)

	if e1.acid_calls.size() > 0 and e2.acid_calls.size() > 0:
		_assert_eq_float(e1.acid_calls[0]["duration"], e2.acid_calls[0]["duration"], "APA-3g_both_same_dur")
		_assert_eq_float(e1.acid_calls[0]["dps"], e2.acid_calls[0]["dps"], "APA-3g_both_same_dps")
	else:
		_fail_test("APA-3j_both", "acid not applied on one or both paths")

	e1.free()
	e2.free()
	executor.free()
	(ps["root"] as Node).free()


# ---------------------------------------------------------------------------
# APA-4: DoT Parameters (contract verification of existing system)
# ---------------------------------------------------------------------------

func test_apa4a_dot_tick_interval_constant() -> void:
	_assert_eq_float(0.5, EnemyEffectTracker.DOT_TICK_INTERVAL, "APA-4a_tick_interval")

func test_apa4b_zero_duration_rejected() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", 0.0, 1.0)
	_assert_false(tracker.has_active_dot("acid"), "APA-4b_no_dot_at_zero")
	tracker.free()


# ---------------------------------------------------------------------------
# APA-5: Non-Stacking — Same-Source Refresh
# ---------------------------------------------------------------------------

func test_apa5a_refresh_not_stack() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", 3.0, 1.0)
	_assert_true(tracker.has_active_dot("acid"), "APA-5a_first")
	tracker._active_dots["acid"]["remaining_duration"] = 1.5
	tracker._active_dots["acid"]["elapsed_since_tick"] = 0.3
	tracker.add_dot("acid", 3.0, 1.0)
	_assert_true(tracker.has_active_dot("acid"), "APA-5a_still_active")
	_assert_eq_float(3.0, tracker._active_dots["acid"]["remaining_duration"], "APA-5a_refreshed")
	_assert_eq_float(0.0, tracker._active_dots["acid"]["elapsed_since_tick"], "APA-5d_tick_reset")
	tracker.free()

func test_apa5b_acid_poison_coexist() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", 3.0, 1.0)
	tracker.add_dot("poison", 5.0, 0.3)
	_assert_true(tracker.has_active_dot("acid"), "APA-5c_acid_active")
	_assert_true(tracker.has_active_dot("poison"), "APA-5c_poison_active")
	tracker.free()

func test_apa5c_dps_updates_on_refresh() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", 3.0, 1.0)
	tracker.add_dot("acid", 3.0, 2.0)
	_assert_eq_float(2.0, tracker._active_dots["acid"]["dps"], "APA-5e_dps_updated")
	tracker.free()


# ---------------------------------------------------------------------------
# APA-6: Visual Distinction — Acid Projectile Color
# ---------------------------------------------------------------------------

func test_apa6a_projectile_color_property_exists() -> void:
	var proj = PlayerProjectile3D.new()
	var color_val = proj.get("color")
	_assert_true(color_val != null, "APA-6a_has_color")
	proj.free()

func test_apa6b_executor_sets_projectile_color() -> void:
	var scene = _build_scene("APA-6b", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	_connect_projectile_signal(scene["executor"])
	scene["executor"].execute_attack(_make_acid_resource())
	_assert_eq_int(1, _projectile_log.size(), "APA-6b_projectile_spawned")
	if _projectile_log.size() > 0:
		var proj = _projectile_log[0]["projectile"]
		var proj_color = proj.get("color")
		if proj_color != null:
			_assert_true(proj_color == Color.CHARTREUSE, "APA-6b_color_chartreuse")
		else:
			_fail_test("APA-6b", "projectile has no color property")
	_teardown(scene)

func test_apa6c_acid_color_in_resource() -> void:
	var acid = _make_acid_resource()
	_assert_true(acid.color == Color.CHARTREUSE, "APA-6c_resource_chartreuse")
	_assert_true(acid.color != Color.ORANGE_RED, "APA-6d_distinct_from_claw")

func test_apa6d_default_color_white() -> void:
	var proj = PlayerProjectile3D.new()
	var color_val = proj.get("color")
	if color_val != null:
		_assert_true(color_val == Color.WHITE, "APA-6e_default_white")
	else:
		_fail_test("APA-6d", "color property missing")
	proj.free()


# ---------------------------------------------------------------------------
# APA-7: Pipeline Integration
# ---------------------------------------------------------------------------

func test_apa7a_acid_dispatches_to_projectile_spit() -> void:
	var scene = _build_scene("APA-7a", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	_connect_projectile_signal(scene["executor"])
	scene["executor"].execute_attack(_make_acid_resource())
	_assert_eq_int(1, _projectile_log.size(), "APA-7a_projectile_fired")
	_teardown(scene)

func test_apa7b_projectile_spawned_with_properties() -> void:
	var scene = _build_scene("APA-7b", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	_connect_projectile_signal(scene["executor"])
	scene["executor"].execute_attack(_make_acid_resource())
	if _projectile_log.size() == 0:
		_fail_test("APA-7b", "no projectile spawned")
		_teardown(scene)
		return
	var proj = _projectile_log[0]["projectile"]
	_assert_eq_float(1.0, proj.damage, "APA-7b_damage")
	_assert_eq_float(8.0, proj.speed, "APA-7b_speed")
	_assert_eq_float(2.0, proj.lifetime, "APA-7b_lifetime")
	_assert_eq_float(0.0, proj.knockback_magnitude, "APA-7b_kb_zero")
	_assert_true(proj.modifiers.get("acid_on_hit", false) == true, "APA-7b_acid_mod")
	_assert_eq_float(3.0, proj.modifiers.get("acid_duration", 0.0), "APA-7b_acid_dur")
	_assert_eq_float(1.0, proj.modifiers.get("acid_dps", 0.0), "APA-7b_acid_dps")
	_assert_eq_float(1.0, proj.direction_x, "APA-7b_direction")
	_teardown(scene)

func test_apa7c_cooldown_value_2s() -> void:
	var acid = _make_acid_resource()
	_assert_eq_float(2.0, acid.cooldown, "APA-7c_cooldown")

func test_apa7d_projectile_consumed_on_hit() -> void:
	var acid_mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	var ps = _make_projectile_in_tree(acid_mods)
	var proj = ps["projectile"]
	var enemy = MockEnemy.new()
	proj._on_body_entered(enemy)
	_assert_true(proj._consumed, "APA-7e_consumed")
	_assert_eq_int(1, enemy.damage_taken.size(), "APA-7e_damage_dealt")
	if enemy.damage_taken.size() > 0:
		_assert_eq_float(1.0, enemy.damage_taken[0]["damage"], "APA-7e_dmg_1")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()


# ---------------------------------------------------------------------------
# Edge Cases (spec EC table)
# ---------------------------------------------------------------------------

func test_ec6_no_apply_acid_skipped() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("EC-6", "executor not loadable")
		return
	var target = NoAcidTarget.new()
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(target, mods)
	_pass_test("EC-6_no_crash")
	target.free()
	executor.free()

func test_ec9_refresh_resets_tick_timer() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", 3.0, 1.0)
	tracker._active_dots["acid"]["elapsed_since_tick"] = 0.3
	tracker._active_dots["acid"]["remaining_duration"] = 1.5
	tracker.add_dot("acid", 3.0, 1.0)
	_assert_eq_float(0.0, tracker._active_dots["acid"]["elapsed_since_tick"], "EC-9_tick_reset")
	_assert_eq_float(3.0, tracker._active_dots["acid"]["remaining_duration"], "EC-9_dur_refreshed")
	tracker.free()

func test_ec12_projectile_no_take_damage_despawns_on_wall() -> void:
	var ps = _make_projectile_in_tree({})
	var bare = Node3D.new()
	ps["projectile"]._on_body_entered(bare)
	_assert_true(ps["projectile"]._consumed, "EC-12_consumed_on_wall")
	bare.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()

func test_ec14_zero_dps_no_crash() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", 3.0, 0.0)
	_assert_true(tracker.has_active_dot("acid"), "EC-14_applied_with_zero_dps")
	tracker.free()

func test_ec15_negative_duration_no_dot() -> void:
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", -1.0, 1.0)
	_assert_false(tracker.has_active_dot("acid"), "EC-15_rejected_negative")
	tracker.free()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AcidAttackTests ===")

	test_apa1_acid_resource_properties()

	test_apa2a_register_defaults_creates_acid()
	test_apa2b_at_least_two_base_attacks()
	test_apa2c_acid_distinct_from_claw()
	test_apa2d_acid_defaults_properties()

	test_apa3a_executor_normal_base_duration()
	test_apa3b_executor_weakened_doubled()
	test_apa3c_executor_infected_base_duration()
	test_apa3d_executor_no_state_method_fallback()
	test_apa3e_executor_dps_unchanged_when_weakened()

	test_apa3f_projectile_normal_base_duration()
	test_apa3g_projectile_weakened_doubled()
	test_apa3h_projectile_infected_base_duration()
	test_apa3i_projectile_hit_weakens_acid_doubled()
	test_apa3j_both_paths_identical_output()

	test_apa4a_dot_tick_interval_constant()
	test_apa4b_zero_duration_rejected()

	test_apa5a_refresh_not_stack()
	test_apa5b_acid_poison_coexist()
	test_apa5c_dps_updates_on_refresh()

	test_apa6a_projectile_color_property_exists()
	test_apa6b_executor_sets_projectile_color()
	test_apa6c_acid_color_in_resource()
	test_apa6d_default_color_white()

	test_apa7a_acid_dispatches_to_projectile_spit()
	test_apa7b_projectile_spawned_with_properties()
	test_apa7c_cooldown_value_2s()
	test_apa7d_projectile_consumed_on_hit()

	test_ec6_no_apply_acid_skipped()
	test_ec9_refresh_resets_tick_timer()
	test_ec12_projectile_no_take_damage_despawns_on_wall()
	test_ec14_zero_dps_no_crash()
	test_ec15_negative_duration_no_dot()

	print("AcidAttackTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
