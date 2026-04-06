#
# test_adhesion_enemy_attack.gd
#
# M8 adhesion lunge — player movement root timer (engine integration contract).
#
# Ticket: project_board/8_milestone_8_enemy_attacks/backlog/adhesion_enemy_attack.md
#

class_name AdhesionEnemyAttackTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


func _load_player_from_scene() -> Node:
	var packed: PackedScene = load("res://scenes/player/player_3d.tscn") as PackedScene
	if packed == null:
		return null
	return packed.instantiate()


func test_aela_root_timer_starts_at_duration() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("AELA-01", "could not load player_3d.tscn")
		return
	player._ready()
	player.call("apply_enemy_movement_root", 0.5)
	var rem: float = player.call("get_enemy_movement_root_remaining") as float
	_assert_true(rem >= 0.499, "AELA-01_root_timer_set")
	player.free()


func test_aela_root_expires_after_simulated_time() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("AELA-02", "could not load player_3d.tscn")
		return
	player._ready()
	player.call("apply_enemy_movement_root", 0.5)
	for _i in 6:
		if player.has_method("_physics_process"):
			player._physics_process(0.1)
	var rem: float = player.call("get_enemy_movement_root_remaining") as float
	_assert_true(rem <= 0.001, "AELA-02_root_cleared_after_0p6s")
	player.free()


func test_aela_root_refresh_uses_max_not_sum() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("AELA-03", "could not load player_3d.tscn")
		return
	player._ready()
	player.call("apply_enemy_movement_root", 0.2)
	player.call("apply_enemy_movement_root", 0.5)
	var rem: float = player.call("get_enemy_movement_root_remaining") as float
	_assert_true(rem >= 0.499 and rem <= 0.501, "AELA-03_max_refresh")
	player.free()


# CHECKPOINT: adversarial — root must not accumulate unbounded on repeated shorter applies after decay
func test_aela_checkpoint_reapply_after_decay() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("AELA-CHK", "could not load player_3d.tscn")
		return
	player._ready()
	player.call("apply_enemy_movement_root", 0.5)
	for _i in 6:
		if player.has_method("_physics_process"):
			player._physics_process(0.1)
	player.call("apply_enemy_movement_root", 0.3)
	var rem: float = player.call("get_enemy_movement_root_remaining") as float
	_assert_true(rem >= 0.29 and rem <= 0.31, "AELA-CHK_fresh_apply_after_clear")
	player.free()


func test_aela_enemy_velocity_gate_method_exists() -> void:
	var script: GDScript = load("res://scripts/enemy/adhesion_bug_lunge_attack.gd") as GDScript
	if script == null:
		_fail_test("AELA-10", "adhesion_bug_lunge_attack.gd missing")
		return
	var n: Object = script.new()
	_assert_true(n.has_method("enemy_writes_velocity_x_this_frame"), "AELA-10_velocity_gate_api")
	n.free()


func run_all() -> int:
	print("=== AdhesionEnemyAttackTests ===")
	test_aela_root_timer_starts_at_duration()
	test_aela_root_expires_after_simulated_time()
	test_aela_root_refresh_uses_max_not_sum()
	test_aela_checkpoint_reapply_after_decay()
	test_aela_enemy_velocity_gate_method_exists()
	print("AdhesionEnemyAttackTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
