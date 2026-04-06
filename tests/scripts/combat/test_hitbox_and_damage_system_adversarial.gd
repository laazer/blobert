#
# test_hitbox_and_damage_system_adversarial.gd
#
# Adversarial cases for enemy attack hitbox + take_damage (HADS spec).
#

class_name HitboxAndDamageSystemAdversarialTests
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


func test_adv_hads_coincident_positions_knockback_fallback_plus_x() -> void:
	# CHECKPOINT: zero separation → spec fallback +X knockback
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("ADV-HADS-01", "no player")
		return
	player._ready()
	player.global_position = Vector3(1.0, 1.0, 0.0)
	player.velocity = Vector3.ZERO
	var hb := _make_hitbox()
	hb.global_position = Vector3(1.0, 1.0, 0.0)
	hb.damage_amount = 0.0
	hb.knockback_strength = 6.0
	hb._ready()
	hb.set_hitbox_active(true)
	hb.call("_apply_hit", player)
	var v: Vector3 = player.velocity as Vector3
	_assert_true(is_equal_approx(v.x, 6.0) and is_equal_approx(v.y, 0.0), "ADV-HADS-01_fallback_knockback")
	player.free()
	hb.free()


func test_adv_hads_apply_hit_without_arm_is_noop() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("ADV-HADS-02", "no player")
		return
	player._ready()
	player.global_position = Vector3(3.0, 0.0, 0.0)
	var before: float = player.call("get_current_hp") as float
	var hb := _make_hitbox()
	hb.damage_amount = 50.0
	hb.global_position = Vector3.ZERO
	hb._ready()
	hb.call("_apply_hit", player)
	var after: float = player.call("get_current_hp") as float
	_assert_true(is_equal_approx(before, after), "ADV-HADS-02_no_damage_when_inactive")
	player.free()
	hb.free()


func test_adv_hads_set_active_false_disarms_without_hit() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("ADV-HADS-03", "no player")
		return
	player._ready()
	var hb := _make_hitbox()
	hb._ready()
	hb.set_hitbox_active(true)
	hb.set_hitbox_active(false)
	_assert_true(not hb.monitoring, "ADV-HADS-03_monitoring_off")
	player.global_position = Vector3(2.0, 0.0, 0.0)
	hb.global_position = Vector3.ZERO
	var before: float = player.call("get_current_hp") as float
	hb.call("_apply_hit", player)
	var after: float = player.call("get_current_hp") as float
	_assert_true(is_equal_approx(before, after), "ADV-HADS-03_disarmed_no_hit")
	player.free()
	hb.free()


func test_adv_hads_hp_clamps_at_min() -> void:
	var player: Node = _load_player_from_scene()
	if player == null:
		_fail_test("ADV-HADS-04", "no player")
		return
	player._ready()
	player.call("take_damage", 1.0e9, Vector3.ZERO)
	var hp: float = player.call("get_current_hp") as float
	_assert_true(hp >= 0.0, "ADV-HADS-04_non_negative_hp")
	player.free()


func _assert_true(condition: bool, test_name: String, fail_msg: String = "expected true") -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, fail_msg)


func run_all() -> int:
	print("=== HitboxAndDamageSystemAdversarialTests ===")
	test_adv_hads_coincident_positions_knockback_fallback_plus_x()
	test_adv_hads_apply_hit_without_arm_is_noop()
	test_adv_hads_set_active_false_disarms_without_hit()
	test_adv_hads_hp_clamps_at_min()
	print(
		"HitboxAndDamageSystemAdversarialTests: "
		+ str(_pass_count)
		+ " passed, "
		+ str(_fail_count)
		+ " failed"
	)
	return _fail_count
