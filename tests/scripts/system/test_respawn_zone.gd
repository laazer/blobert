#
# respawn_zone.gd should fully recover player runtime state on enter.

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


class _FakeExecutor:
	extends RefCounted
	var _is_active: bool = true


class _FakePlayer:
	extends Node3D
	var reset_position_called: bool = false
	var reset_hp_called: bool = false
	var reset_chunks_called: bool = false
	var last_reset_position: Vector3 = Vector3.ZERO
	var _executor: _FakeExecutor = _FakeExecutor.new()

	func _init() -> void:
		add_to_group("player")

	func reset_position(target: Vector3) -> void:
		reset_position_called = true
		last_reset_position = target

	func reset_hp() -> void:
		reset_hp_called = true

	func reset_chunks() -> void:
		reset_chunks_called = true

	func get_attack_executor() -> Variant:
		return _executor


func test_respawn_zone_recovers_player_runtime_state() -> void:
	var zone_script: GDScript = load("res://scripts/world/respawn_zone.gd") as GDScript
	if zone_script == null:
		_fail("respawn_zone_load", "could not load respawn_zone.gd")
		return
	var zone: Area3D = zone_script.new() as Area3D
	if zone == null:
		_fail("respawn_zone_new", "could not instantiate respawn_zone.gd")
		return
	var root: Node3D = Node3D.new()
	var spawn: Marker3D = Marker3D.new()
	spawn.name = "Spawn"
	spawn.global_position = Vector3(3.0, 1.0, 0.0)
	root.add_child(spawn)
	root.add_child(zone)
	zone.spawn_point = NodePath("../Spawn")
	var player: _FakePlayer = _FakePlayer.new()
	root.add_child(player)
	zone.call("_on_body_entered", player)
	_assert_true(player.reset_position_called, "respawn_calls_reset_position")
	_assert_true(
		player.last_reset_position.is_equal_approx(spawn.global_position),
		"respawn_uses_spawn_point",
	)
	_assert_true(player.reset_hp_called, "respawn_calls_reset_hp")
	_assert_true(player.reset_chunks_called, "respawn_calls_reset_chunks")
	_assert_false(player.get_attack_executor()._is_active, "respawn_clears_executor_active")
	root.free()


func run_all() -> int:
	_pass_count = 0
	_fail_count = 0
	test_respawn_zone_recovers_player_runtime_state()
	return _fail_count
