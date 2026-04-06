#
# test_acid_enemy_attack.gd
#
# Behavioral tests for M8 acid enemy projectile + player acid DoT stacking.
#
# Ticket: project_board/8_milestone_8_enemy_attacks/backlog/acid_enemy_attack.md
#

class_name AcidEnemyAttackTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


func _load_player_from_scene() -> Node:
	var packed: PackedScene = load("res://scenes/player/player_3d.tscn") as PackedScene
	if packed == null:
		return null
	return packed.instantiate()


func test_aeaa_player_acid_impact_reduces_hp() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("AEAA-01", "could not load player_3d.tscn")
		return
	player._ready()
	var hp_before: float = player.call("get_current_hp") as float
	player.call("apply_enemy_acid_damage", 10.0, 1.0, 3.0, 0.5)
	var hp_after: float = player.call("get_current_hp") as float
	_assert_true(hp_before - hp_after >= 9.99, "AEAA-01_impact_damage")
	_assert_eq(player.call("get_enemy_acid_dot_instance_count") as int, 1, "AEAA-01_one_dot_stack")
	player.free()


func test_aeaa_dot_ticks_six_times_over_three_seconds() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("AEAA-02", "could not load player_3d.tscn")
		return
	player._ready()
	player.call("apply_enemy_acid_damage", 0.0, 5.0, 3.0, 0.5)
	var hp0: float = player.call("get_current_hp") as float
	for _i in 6:
		if player.has_method("_physics_process"):
			player._physics_process(0.5)
	var hp1: float = player.call("get_current_hp") as float
	_assert_true(is_equal_approx(hp0 - hp1, 30.0), "AEAA-02_six_dot_ticks")
	_assert_eq(player.call("get_enemy_acid_dot_instance_count") as int, 0, "AEAA-02_dot_expired")
	player.free()


func test_aeaa_dot_stacks_independent_instances() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("AEAA-03", "could not load player_3d.tscn")
		return
	player._ready()
	player.call("apply_enemy_acid_damage", 0.0, 2.0, 3.0, 0.5)
	player.call("apply_enemy_acid_damage", 0.0, 2.0, 3.0, 0.5)
	_assert_eq(player.call("get_enemy_acid_dot_instance_count") as int, 2, "AEAA-03_two_stacks")
	if player.has_method("_physics_process"):
		player._physics_process(0.5)
	var hp: float = player.call("get_current_hp") as float
	var max_hp: float = 100.0
	_assert_true(is_equal_approx(max_hp - hp, 4.0), "AEAA-03_two_instances_one_tick_each")
	player.free()


func test_aeaa_projectile_moves_along_x() -> void:
	var packed: PackedScene = load("res://scenes/combat/acid_projectile_3d.tscn") as PackedScene
	if packed == null:
		_fail_test("AEAA-10", "acid_projectile scene missing")
		return
	var proj: Node = packed.instantiate()
	if proj == null:
		_fail_test("AEAA-10", "instantiate failed")
		return
	proj._ready()
	if proj.has_method("setup"):
		proj.call("setup", -1.0, 10.0)
	var n3: Node3D = proj as Node3D
	var x0: float = n3.position.x
	if proj.has_method("_physics_process"):
		proj._physics_process(0.1)
	var x1: float = n3.position.x
	_assert_true(x1 < x0 - 0.05, "AEAA-10_moves_negative_x_when_dir_negative")
	proj.free()


func test_aeaa_projectile_despawns_on_static_body() -> void:
	var packed: PackedScene = load("res://scenes/combat/acid_projectile_3d.tscn") as PackedScene
	if packed == null:
		_fail_test("AEAA-11", "acid_projectile scene missing")
		return
	var proj: Node = packed.instantiate()
	var wall := StaticBody3D.new()
	proj._ready()
	if proj.has_method("_on_body_entered"):
		proj._on_body_entered(wall)
	_assert_true(proj.is_queued_for_deletion(), "AEAA-11_queues_free_on_static")
	proj.free()
	wall.free()


# CHECKPOINT: adversarial — three rapid applications must yield three concurrent DoT instances
# before any expires (same parameters, 0s simulated time).
func test_aeaa_checkpoint_triple_stack_three_instances() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("AEAA-CHK", "could not load player_3d.tscn")
		return
	player._ready()
	player.call("apply_enemy_acid_damage", 0.0, 1.0, 3.0, 0.5)
	player.call("apply_enemy_acid_damage", 0.0, 1.0, 3.0, 0.5)
	player.call("apply_enemy_acid_damage", 0.0, 1.0, 3.0, 0.5)
	_assert_eq(player.call("get_enemy_acid_dot_instance_count") as int, 3, "AEAA-CHK_triple_stack")
	player.free()


func _assert_eq(a: Variant, b: Variant, test_name: String) -> void:
	if a == b:
		_pass(test_name)
	else:
		_fail(test_name, "expected " + str(b) + ", got " + str(a))


func run_all() -> int:
	print("=== AcidEnemyAttackTests ===")
	test_aeaa_player_acid_impact_reduces_hp()
	test_aeaa_dot_ticks_six_times_over_three_seconds()
	test_aeaa_dot_stacks_independent_instances()
	test_aeaa_projectile_moves_along_x()
	test_aeaa_projectile_despawns_on_static_body()
	test_aeaa_checkpoint_triple_stack_three_instances()
	print("AcidEnemyAttackTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
