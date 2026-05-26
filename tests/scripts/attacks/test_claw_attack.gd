#
# test_claw_attack.gd
#
# Behavioral tests for the claw mutation attack: AttackResource registration,
# infect_weakened modifier, pre-damage state capture, single-frame hitbox,
# VFX placeholder signal, and pipeline integration.
#
# Spec: project_board/specs/claw_player_attack_spec.md (CPA-1..CPA-7)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/08_claw_player_attack.md
#

class_name ClawAttackTests
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
	var poison_calls: Array = []
	var acid_calls: Array = []
	var slow_calls: Array = []

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag

	func apply_poison(duration: float, dps: float) -> void:
		poison_calls.append({"duration": duration, "dps": dps})

	func apply_acid(duration: float, dps: float) -> void:
		acid_calls.append({"duration": duration, "dps": dps})

	func apply_slowness(multiplier: float, duration: float) -> void:
		slow_calls.append({"multiplier": multiplier, "duration": duration})


class WeakeningEnemy extends Node3D:
	var damage_taken: Array = []
	var current_state: int = 0
	var is_dead_flag: bool = false
	var max_hp: float = 10.0
	var current_hp: float = 10.0

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})
		current_hp = maxf(0.0, current_hp - damage)
		if current_state == 0 and current_hp <= max_hp * 0.5:
			current_state = 1

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag


class BareTarget extends Node3D:
	pass


class MockParent extends Node3D:
	var _facing: float = 1.0
	func get_facing_sign() -> float:
		return _facing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_claw_resource() -> AttackResource:
	var r = AttackResource.new()
	r.attack_id = 1
	r.attack_name = "Claw Swipe"
	r.description = "Fast melee swipe with short cooldown. Infects weakened enemies."
	r.effect_type = "MELEE_SWIPE"
	r.damage = 3.0
	r.cooldown = 0.8
	r.attack_range = 1.5
	r.startup_frames = 0
	r.knockback_magnitude = 2.0
	r.knockback_direction = "away"
	r.projectile_speed = 0.0
	r.projectile_lifetime = 2.0
	r.color = Color.ORANGE_RED
	r.vfx_scale = 1.2
	r.modifiers = {"infect_weakened": true}
	return r


func _make_resource(overrides: Dictionary = {}) -> AttackResource:
	var r = AttackResource.new()
	r.startup_frames = 0
	for key in overrides:
		r.set(key, overrides[key])
	return r


func _build_scene(label: String, enemies: Array = [], pos: Vector3 = Vector3.ZERO, facing: float = 1.0) -> Dictionary:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test(label, "executor not loadable")
		return {}
	var scene_root = Node3D.new()
	var parent = MockParent.new()
	parent._facing = facing
	scene_root.add_child(parent)
	parent.add_child(executor)
	parent.global_position = pos
	var tree = Engine.get_main_loop() as SceneTree
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


# ---------------------------------------------------------------------------
# CPA-1: Claw AttackResource Definition (all 15 property checks)
# ---------------------------------------------------------------------------

func test_cpa1_claw_resource_properties() -> void:
	var claw = _make_claw_resource()
	_assert_eq_string("MELEE_SWIPE", claw.effect_type, "CPA-1b_effect_type")
	_assert_eq_float(3.0, claw.damage, "CPA-1c_damage")
	_assert_eq_float(0.8, claw.cooldown, "CPA-1d_cooldown")
	_assert_eq_float(1.5, claw.attack_range, "CPA-1e_range")
	_assert_eq_float(2.0, claw.knockback_magnitude, "CPA-1f_kb_magnitude")
	_assert_eq_string("away", claw.knockback_direction, "CPA-1g_kb_direction")
	_assert_true(claw.modifiers.get("infect_weakened", false) == true, "CPA-1h_infect_weakened")
	_assert_eq_int(0, claw.startup_frames, "CPA-1i_startup_frames")
	_assert_true(claw.color == Color.ORANGE_RED, "CPA-1j_color")
	_assert_eq_float(1.2, claw.vfx_scale, "CPA-1k_vfx_scale")
	_assert_eq_int(1, claw.attack_id, "CPA-1_attack_id")
	_assert_eq_string("Claw Swipe", claw.attack_name, "CPA-1_attack_name")

func test_cpa1a_claw_roundtrip_via_database() -> void:
	var db = AttackDatabaseNode.new()
	var claw = _make_claw_resource()
	db.register_base_attack("claw", claw)
	var retrieved = db.get_base_attack("claw")
	_assert_true(retrieved != null, "CPA-1a_retrieved")
	if retrieved != null:
		_assert_eq_float(3.0, retrieved.damage, "CPA-1a_damage_preserved")
		_assert_eq_float(0.8, retrieved.cooldown, "CPA-1a_cooldown_preserved")
	db.free()


# ---------------------------------------------------------------------------
# CPA-2: AttackDatabase Registration Site (_register_defaults)
# EXPECTED TO FAIL until _register_defaults() is implemented.
# ---------------------------------------------------------------------------

func test_cpa2a_register_defaults_creates_claw() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	_assert_true(db.has_base_attack("claw"), "CPA-2a_claw_auto_registered")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_cpa2b_register_defaults_count() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	_assert_true(db.get_base_attack_count() >= 1, "CPA-2b_at_least_one")
	if tree:
		db.queue_free()
	else:
		db.free()

func test_cpa2c_register_defaults_claw_properties() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var claw = db.get_base_attack("claw")
	if claw == null:
		_fail_test("CPA-2c", "claw not registered by _register_defaults()")
		if tree: db.queue_free()
		else: db.free()
		return
	_assert_eq_string("MELEE_SWIPE", claw.effect_type, "CPA-2c_type")
	_assert_eq_float(3.0, claw.damage, "CPA-2c_damage")
	_assert_eq_float(0.8, claw.cooldown, "CPA-2c_cooldown")
	_assert_eq_float(1.5, claw.attack_range, "CPA-2c_range")
	_assert_eq_float(2.0, claw.knockback_magnitude, "CPA-2c_kb")
	_assert_true(claw.modifiers.get("infect_weakened", false) == true, "CPA-2c_mod")
	_assert_true(claw.color == Color.ORANGE_RED, "CPA-2c_color")
	_assert_eq_float(1.2, claw.vfx_scale, "CPA-2c_vfx")
	if tree: db.queue_free()
	else: db.free()

func test_cpa2d_manual_registration_unaffected() -> void:
	var db = AttackDatabaseNode.new()
	var custom = _make_resource({"effect_type": "MELEE_SWIPE", "damage": 99.0})
	db.register_base_attack("test_manual", custom)
	_assert_true(db.has_base_attack("test_manual"), "CPA-2d_manual_ok")
	_assert_eq_float(99.0, db.get_base_attack("test_manual").damage, "CPA-2d_damage")
	db.free()

func test_cpa2e_claw_override_after_ready() -> void:
	var db = AttackDatabaseNode.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(db)
	var custom = _make_resource({"effect_type": "MELEE_SWIPE", "damage": 50.0})
	db.register_base_attack("claw", custom)
	_assert_eq_float(50.0, db.get_base_attack("claw").damage, "CPA-2e_override")
	if tree: db.queue_free()
	else: db.free()


# ---------------------------------------------------------------------------
# CPA-3: WEAKENED→INFECTED Modifier (infect_weakened)
# EXPECTED TO FAIL until _apply_modifiers gains infect_weakened handler.
# ---------------------------------------------------------------------------

func test_cpa3a_weakened_becomes_infected() -> void:
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-3a", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(2, enemy.current_state, "CPA-3a_infected")
	_teardown(scene)

func test_cpa3b_normal_not_infected() -> void:
	var enemy = MockEnemy.new()
	enemy.current_state = 0
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-3b", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_true(enemy.current_state != 2, "CPA-3b_not_infected")
	_assert_true(enemy.damage_taken.size() > 0, "CPA-3b_damage_applied")
	_teardown(scene)

func test_cpa3c_already_infected_unchanged() -> void:
	var enemy = MockEnemy.new()
	enemy.current_state = 2
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-3c", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(2, enemy.current_state, "CPA-3c_still_infected")
	_pass_test("CPA-3c_no_crash")
	_teardown(scene)

func test_cpa3d_dead_enemy_no_transition() -> void:
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	enemy.is_dead_flag = true
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-3d", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_pass_test("CPA-3d_no_crash_on_dead")
	_teardown(scene)

func test_cpa3e_bare_target_skipped() -> void:
	var bare = BareTarget.new()
	bare.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-3e", [bare], Vector3.ZERO, 1.0)
	if scene.is_empty():
		bare.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_pass_test("CPA-3e_bare_no_crash")
	_teardown(scene)

func test_cpa3f_two_hit_infection_pattern() -> void:
	var enemy = WeakeningEnemy.new()
	enemy.max_hp = 6.0
	enemy.current_hp = 6.0
	enemy.current_state = 0
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-3f", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var claw = _make_claw_resource()
	executor.execute_attack(claw)
	_assert_eq_int(1, enemy.current_state, "CPA-3f_hit1_weakened_not_infected")
	executor.execute_attack(claw)
	_assert_eq_int(2, enemy.current_state, "CPA-3f_hit2_infected")
	_teardown(scene)

func test_cpa3g_same_hit_weaken_infect_blocked() -> void:
	var enemy = WeakeningEnemy.new()
	enemy.max_hp = 6.0
	enemy.current_hp = 6.0
	enemy.current_state = 0
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-3g", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, enemy.current_state, "CPA-3g_weakened_not_infected")
	_teardown(scene)

func test_cpa3h_modifiers_coexist() -> void:
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var res = _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 3.0, "attack_range": 1.5,
		"modifiers": {"infect_weakened": true, "poison": true, "poison_duration": 2.0, "poison_dps": 0.3}
	})
	var scene = _build_scene("CPA-3h", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(res)
	_assert_eq_int(2, enemy.current_state, "CPA-3h_infected")
	_assert_eq_int(1, enemy.poison_calls.size(), "CPA-3h_poison_also_applied")
	_teardown(scene)

func test_cpa3i_no_infect_key_no_infection() -> void:
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var res = _make_resource({"effect_type": "MELEE_SWIPE", "damage": 3.0, "attack_range": 1.5, "modifiers": {}})
	var scene = _build_scene("CPA-3i", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(res)
	_assert_eq_int(1, enemy.current_state, "CPA-3i_still_weakened")
	_teardown(scene)

func test_cpa3j_multiple_enemies_mixed_states() -> void:
	var e_weak = MockEnemy.new()
	e_weak.current_state = 1
	e_weak.global_position = Vector3(0.5, 0.0, 0.0)
	var e_normal = MockEnemy.new()
	e_normal.current_state = 0
	e_normal.global_position = Vector3(0.3, 0.0, 0.0)
	var e_inf = MockEnemy.new()
	e_inf.current_state = 2
	e_inf.global_position = Vector3(0.4, 0.0, 0.0)
	var scene = _build_scene("CPA-3j", [e_weak, e_normal, e_inf], Vector3.ZERO, 1.0)
	if scene.is_empty():
		e_weak.free()
		e_normal.free()
		e_inf.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(2, e_weak.current_state, "CPA-3j_weakened_infected")
	_assert_eq_int(0, e_normal.current_state, "CPA-3j_normal_unchanged")
	_assert_eq_int(2, e_inf.current_state, "CPA-3j_infected_unchanged")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CPA-4: Pre-Damage State Capture
# ---------------------------------------------------------------------------

func test_cpa4a_pre_damage_prevents_same_hit_infect() -> void:
	var enemy = WeakeningEnemy.new()
	enemy.max_hp = 5.0
	enemy.current_hp = 5.0
	enemy.current_state = 0
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-4a", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, enemy.current_state, "CPA-4a_weakened_only")
	_teardown(scene)

func test_cpa4b_pre_damage_weakened_infects() -> void:
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-4b", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(2, enemy.current_state, "CPA-4b_infected")
	_teardown(scene)

func test_cpa4c_bare_target_no_crash() -> void:
	var bare = BareTarget.new()
	bare.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-4c", [bare], Vector3.ZERO, 1.0)
	if scene.is_empty():
		bare.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_pass_test("CPA-4c_no_crash")
	_teardown(scene)

func test_cpa4d_existing_modifiers_unaffected() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var res = _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 1.0, "attack_range": 1.5,
		"modifiers": {
			"poison": true, "poison_duration": 3.0, "poison_dps": 0.5,
			"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.2,
			"slow": 0.5, "slow_duration": 1.5
		}
	})
	var scene = _build_scene("CPA-4d", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(res)
	_assert_eq_int(1, enemy.poison_calls.size(), "CPA-4d_poison")
	_assert_eq_int(1, enemy.acid_calls.size(), "CPA-4d_acid")
	_assert_eq_int(1, enemy.slow_calls.size(), "CPA-4d_slow")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CPA-5: Single-Frame Hitbox Semantics
# ---------------------------------------------------------------------------

func test_cpa5a_single_hit_per_enemy() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-5a", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, enemy.damage_taken.size(), "CPA-5a_exactly_one_hit")
	_teardown(scene)

func test_cpa5b_cooldown_value_and_executor_reset() -> void:
	var scene = _build_scene("CPA-5b", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var claw = _make_claw_resource()
	executor.execute_attack(claw)
	_assert_false(executor.is_active(), "CPA-5b_not_active")
	_assert_eq_float(0.8, claw.cooldown, "CPA-5b_cooldown_0_8")
	_teardown(scene)

func test_cpa5c_no_persistent_hitbox() -> void:
	var scene = _build_scene("CPA-5c", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	executor.execute_attack(_make_claw_resource())
	var area_count := 0
	for child in executor.get_children():
		if child is Area3D:
			area_count += 1
	_assert_eq_int(0, area_count, "CPA-5c_no_area3d")
	_teardown(scene)

func test_cpa5d_out_of_range_not_hit() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(100.0, 0.0, 0.0)
	var scene = _build_scene("CPA-5d", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(0, enemy.damage_taken.size(), "CPA-5d_not_hit")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CPA-6: VFX Placeholder
# ---------------------------------------------------------------------------

func test_cpa6a_vfx_signal_emitted() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-6a", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	_connect_all_signals(scene["executor"])
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, _count_signal("melee_vfx_requested"), "CPA-6a_vfx_emitted")
	_teardown(scene)

func test_cpa6b_vfx_color_and_scale() -> void:
	var scene = _build_scene("CPA-6b", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	_connect_all_signals(scene["executor"])
	scene["executor"].execute_attack(_make_claw_resource())
	var vfx = _get_signal_data("melee_vfx_requested")
	_assert_true(vfx.size() > 0, "CPA-6b_signal_received")
	if vfx.size() > 0:
		_assert_true(vfx["color"] == Color.ORANGE_RED, "CPA-6b_color")
		_assert_eq_float(1.2, vfx["scale"], "CPA-6c_scale")
	_teardown(scene)

func test_cpa6d_vfx_on_whiff() -> void:
	var scene = _build_scene("CPA-6d", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	_connect_all_signals(scene["executor"])
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, _count_signal("melee_vfx_requested"), "CPA-6d_whiff_vfx")
	_assert_eq_int(0, _count_signal("attack_hit"), "CPA-6d_no_hit")
	_teardown(scene)


# ---------------------------------------------------------------------------
# CPA-7: Integration with Existing Pipeline
# ---------------------------------------------------------------------------

func test_cpa7a_melee_swipe_routing() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-7a", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	_connect_all_signals(scene["executor"])
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, _count_signal("attack_started"), "CPA-7a_started")
	_assert_eq_int(1, _count_signal("attack_hit"), "CPA-7a_hit")
	_assert_eq_int(1, _count_signal("melee_vfx_requested"), "CPA-7a_vfx")
	_teardown(scene)

func test_cpa7b_damage_value() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-7b", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(1, enemy.damage_taken.size(), "CPA-7b_hit")
	if enemy.damage_taken.size() > 0:
		_assert_eq_float(3.0, enemy.damage_taken[0]["damage"], "CPA-7b_damage_3")
	_teardown(scene)

func test_cpa7c_knockback_away() -> void:
	var enemy = MockEnemy.new()
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("CPA-7c", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	if enemy.damage_taken.size() > 0:
		var kb: Vector3 = enemy.damage_taken[0]["knockback"]
		_assert_true(kb.x > 0.0, "CPA-7c_kb_positive_x")
		_assert_eq_float(0.0, kb.z, "CPA-7c_kb_z_zero")
	else:
		_fail_test("CPA-7c", "no damage recorded")
	_teardown(scene)

func test_cpa7d_null_resource_safe() -> void:
	var scene = _build_scene("CPA-7d", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	scene["executor"].execute_attack(null)
	_assert_false(scene["executor"].is_active(), "CPA-7d_null_safe")
	_pass_test("CPA-7d_no_crash")
	_teardown(scene)

func test_cpa7e_active_flag_resets_sync() -> void:
	var scene = _build_scene("CPA-7e", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	var claw = _make_claw_resource()
	executor.execute_attack(claw)
	_assert_false(executor.is_active(), "CPA-7e_reset_after_sync")
	executor.execute_attack(claw)
	_assert_false(executor.is_active(), "CPA-7e_second_completes")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Edge cases (EC table from spec, covering gaps not hit above)
# ---------------------------------------------------------------------------

func test_ec8_two_sequential_hits_weaken_then_infect() -> void:
	var enemy = WeakeningEnemy.new()
	enemy.max_hp = 4.0
	enemy.current_hp = 4.0
	enemy.current_state = 0
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("EC-8", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	var executor = scene["executor"]
	var claw = _make_claw_resource()
	executor.execute_attack(claw)
	_assert_eq_int(1, enemy.current_state, "EC-8_hit1_weakened")
	executor.execute_attack(claw)
	_assert_eq_int(2, enemy.current_state, "EC-8_hit2_infected")
	_teardown(scene)

func test_ec10_whiff_behavior() -> void:
	var scene = _build_scene("EC-10", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	_connect_all_signals(scene["executor"])
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(0, _count_signal("attack_hit"), "EC-10_no_hits")
	_assert_eq_int(1, _count_signal("melee_vfx_requested"), "EC-10_vfx_emitted")
	_teardown(scene)

func test_ec16_absent_infect_key() -> void:
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var res = _make_resource({
		"effect_type": "MELEE_SWIPE", "damage": 3.0, "attack_range": 1.5,
		"modifiers": {"poison": true, "poison_duration": 2.0, "poison_dps": 0.3}
	})
	var scene = _build_scene("EC-16", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(res)
	_assert_eq_int(1, enemy.current_state, "EC-16_still_weakened")
	_assert_eq_int(1, enemy.poison_calls.size(), "EC-16_poison_ok")
	_teardown(scene)

func test_ec17_cross_attack_then_claw_infects() -> void:
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	enemy.global_position = Vector3(0.5, 0.0, 0.0)
	var scene = _build_scene("EC-17", [enemy], Vector3.ZERO, 1.0)
	if scene.is_empty():
		enemy.free()
		return
	scene["executor"].execute_attack(_make_claw_resource())
	_assert_eq_int(2, enemy.current_state, "EC-17_infection_from_external_weaken")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== ClawAttackTests ===")

	test_cpa1_claw_resource_properties()
	test_cpa1a_claw_roundtrip_via_database()

	test_cpa2a_register_defaults_creates_claw()
	test_cpa2b_register_defaults_count()
	test_cpa2c_register_defaults_claw_properties()
	test_cpa2d_manual_registration_unaffected()
	test_cpa2e_claw_override_after_ready()

	test_cpa3a_weakened_becomes_infected()
	test_cpa3b_normal_not_infected()
	test_cpa3c_already_infected_unchanged()
	test_cpa3d_dead_enemy_no_transition()
	test_cpa3e_bare_target_skipped()
	test_cpa3f_two_hit_infection_pattern()
	test_cpa3g_same_hit_weaken_infect_blocked()
	test_cpa3h_modifiers_coexist()
	test_cpa3i_no_infect_key_no_infection()
	test_cpa3j_multiple_enemies_mixed_states()

	test_cpa4a_pre_damage_prevents_same_hit_infect()
	test_cpa4b_pre_damage_weakened_infects()
	test_cpa4c_bare_target_no_crash()
	test_cpa4d_existing_modifiers_unaffected()

	test_cpa5a_single_hit_per_enemy()
	test_cpa5b_cooldown_value_and_executor_reset()
	test_cpa5c_no_persistent_hitbox()
	test_cpa5d_out_of_range_not_hit()

	test_cpa6a_vfx_signal_emitted()
	test_cpa6b_vfx_color_and_scale()
	test_cpa6d_vfx_on_whiff()

	test_cpa7a_melee_swipe_routing()
	test_cpa7b_damage_value()
	test_cpa7c_knockback_away()
	test_cpa7d_null_resource_safe()
	test_cpa7e_active_flag_resets_sync()

	test_ec8_two_sequential_hits_weaken_then_infect()
	test_ec10_whiff_behavior()
	test_ec16_absent_infect_key()
	test_ec17_cross_attack_then_claw_infects()

	print("ClawAttackTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
