#
# test_carapace_enemy_attack.gd
#
# M8 carapace charge — exports, API, HADS defaults (CEA).
#

class_name CarapaceEnemyAttackTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


func test_cea_script_and_velocity_gate_api() -> void:
	var script: GDScript = load("res://scripts/enemy/carapace_husk_attack.gd") as GDScript
	if script == null:
		_fail_test("CEA-01", "carapace_husk_attack.gd missing")
		return
	var n: Object = script.new()
	_assert_true(n.has_method("enemy_writes_velocity_x_this_frame"), "CEA-01_velocity_gate_api")
	n.free()


func test_cea_export_defaults() -> void:
	var script: GDScript = load("res://scripts/enemy/carapace_husk_attack.gd") as GDScript
	if script == null:
		_fail_test("CEA-02", "carapace_husk_attack.gd missing")
		return
	var n: Object = script.new()
	_assert_true(is_equal_approx(n.attack_range, 6.0), "CEA-02_attack_range")
	_assert_true(is_equal_approx(n.cooldown_seconds, 4.0), "CEA-02_cooldown")
	_assert_true(is_equal_approx(n.max_charge_range, 6.0), "CEA-02_max_charge_range")
	_assert_true(is_equal_approx(n.damage_amount, 35.0), "CEA-02_damage")
	_assert_true(is_equal_approx(n.knockback_strength, 22.0), "CEA-02_knockback")
	n.free()


func test_cea_controller_accepts_min_hold_param() -> void:
	var ctrl_script: GDScript = load("res://scripts/enemies/enemy_animation_controller.gd") as GDScript
	if ctrl_script == null:
		_fail_test("CEA-03", "enemy_animation_controller.gd missing")
		return
	var src: String = ctrl_script.source_code
	_assert_true(src.contains("begin_ranged_attack_telegraph(min_hold_seconds"), "CEA-03_min_hold_signature")


func run_all() -> int:
	print("=== CarapaceEnemyAttackTests ===")
	test_cea_script_and_velocity_gate_api()
	test_cea_export_defaults()
	test_cea_controller_accepts_min_hold_param()
	print("CarapaceEnemyAttackTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
