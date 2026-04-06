#
# test_hitbox_and_damage_system.gd
#
# Behavioral tests for M8 enemy attack hitbox + PlayerController3D.take_damage.
# Spec: project_board/specs/hitbox_and_damage_system_spec.md (HADS-1..HADS-8)
#

class_name HitboxAndDamageSystemTests
extends "res://tests/utils/test_utils.gd"

const _HITBOX_SCRIPT: GDScript = preload("res://scripts/enemies/enemy_attack_hitbox.gd")

var _pass_count: int = 0
var _fail_count: int = 0


func _load_player_from_scene() -> Node:
	var packed: PackedScene = load("res://scenes/player/player_3d.tscn") as PackedScene
	if packed == null:
		return null
	return packed.instantiate()


func _make_hitbox() -> Area3D:
	var hb: Area3D = _HITBOX_SCRIPT.new() as Area3D
	var shape := CollisionShape3D.new()
	shape.shape = SphereShape3D.new()
	hb.add_child(shape)
	return hb


func test_hads_take_damage_reduces_hp() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("HADS-01", "could not load player_3d.tscn")
		return
	player._ready()
	var before: float = player.call("get_current_hp") as float
	player.call("take_damage", 12.0, Vector3.ZERO)
	var after: float = player.call("get_current_hp") as float
	_assert_true(is_equal_approx(before - after, 12.0), "HADS-01_hp_delta")
	player.free()


func test_hads_take_damage_applies_knockback_xy() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("HADS-02", "could not load player_3d.tscn")
		return
	player._ready()
	player.velocity = Vector3.ZERO
	player.call("take_damage", 0.0, Vector3(3.0, -2.0, 99.0))
	var v: Vector3 = player.velocity as Vector3
	_assert_true(is_equal_approx(v.x, 3.0) and is_equal_approx(v.y, -2.0) and is_equal_approx(v.z, 0.0), "HADS-02_velocity")
	player.free()


func test_hads_hitbox_default_inactive() -> void:
	var hb := _make_hitbox()
	hb._ready()
	_assert_true(not hb.monitoring, "HADS-03_default_monitoring_off")
	hb.free()


func test_hads_hitbox_one_hit_per_activation() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("HADS-04", "could not load player_3d.tscn")
		return
	player._ready()
	player.global_position = Vector3(5.0, 0.0, 0.0)
	var hb := _make_hitbox()
	hb.damage_amount = 7.0
	hb.knockback_strength = 4.0
	hb.global_position = Vector3.ZERO
	hb._ready()
	hb.set_hitbox_active(true)
	hb.call("_apply_hit", player)
	var hp1: float = player.call("get_current_hp") as float
	hb.call("_apply_hit", player)
	var hp2: float = player.call("get_current_hp") as float
	_assert_true(is_equal_approx(hp1, hp2), "HADS-04_second_hit_ignored")
	_assert_true(not hb.monitoring, "HADS-04_auto_off")
	player.free()
	hb.free()


func test_hads_hitbox_rearm_allows_second_hit() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("HADS-05", "could not load player_3d.tscn")
		return
	player._ready()
	player.global_position = Vector3(2.0, 0.0, 0.0)
	var hb := _make_hitbox()
	hb.damage_amount = 5.0
	hb.knockback_strength = 1.0
	hb.global_position = Vector3.ZERO
	hb._ready()
	hb.set_hitbox_active(true)
	hb.call("_apply_hit", player)
	var hp1: float = player.call("get_current_hp") as float
	hb.set_hitbox_active(true)
	hb.call("_apply_hit", player)
	var hp2: float = player.call("get_current_hp") as float
	_assert_true(hp2 < hp1, "HADS-05_second_cycle_damages")
	player.free()
	hb.free()


func test_hads_knockback_direction_away_from_hitbox() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("HADS-06", "could not load player_3d.tscn")
		return
	player._ready()
	player.global_position = Vector3(10.0, 2.0, 0.0)
	player.velocity = Vector3.ZERO
	var hb := _make_hitbox()
	hb.damage_amount = 1.0
	hb.knockback_strength = 10.0
	hb.global_position = Vector3(8.0, 2.0, 0.0)
	hb._ready()
	hb.set_hitbox_active(true)
	hb.call("_apply_hit", player)
	var v: Vector3 = player.velocity as Vector3
	_assert_true(v.x > 0.0 and is_equal_approx(v.y, 0.0), "HADS-06_push_along_x")
	player.free()
	hb.free()


func _assert_true(condition: bool, test_name: String, fail_msg: String = "expected true") -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, fail_msg)


func run_all() -> int:
	print("=== HitboxAndDamageSystemTests ===")
	test_hads_take_damage_reduces_hp()
	test_hads_take_damage_applies_knockback_xy()
	test_hads_hitbox_default_inactive()
	test_hads_hitbox_one_hit_per_activation()
	test_hads_hitbox_rearm_allows_second_hit()
	test_hads_knockback_direction_away_from_hitbox()
	print("HitboxAndDamageSystemTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
