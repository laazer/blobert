#
# test_claw_enemy_attack.gd
#
# M8 claw 2-hit combo — exports and HADS defaults (CLA).
#

class_name ClawEnemyAttackTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


func test_cla_script_exists() -> void:
	var script: GDScript = load("res://scripts/enemy/claw_crawler_attack.gd") as GDScript
	if script == null:
		_fail_test("CLA-01", "claw_crawler_attack.gd missing")
		return
	var n: Object = script.new()
	_assert_true(n != null, "CLA-01_instantiate")
	n.free()


func test_cla_export_defaults() -> void:
	var script: GDScript = load("res://scripts/enemy/claw_crawler_attack.gd") as GDScript
	if script == null:
		_fail_test("CLA-02", "claw_crawler_attack.gd missing")
		return
	var n: Object = script.new()
	_assert_true(is_equal_approx(n.attack_range, 2.0), "CLA-02_attack_range")
	_assert_true(is_equal_approx(n.cooldown_seconds, 1.2), "CLA-02_cooldown")
	_assert_true(is_equal_approx(n.damage_per_hit, 7.0), "CLA-02_damage_per_hit")
	_assert_true(is_equal_approx(n.knockback_per_hit, 4.0), "CLA-02_knockback_per_hit")
	_assert_true(is_equal_approx(n.combo_pause_seconds, 0.12), "CLA-02_combo_pause")
	n.free()


func test_cla_damage_below_carapace_single_hit() -> void:
	var claw_s: GDScript = load("res://scripts/enemy/claw_crawler_attack.gd") as GDScript
	var cap_s: GDScript = load("res://scripts/enemy/carapace_husk_attack.gd") as GDScript
	if claw_s == null or cap_s == null:
		_fail_test("CLA-03", "script load failed")
		return
	var claw: Object = claw_s.new()
	var cap: Object = cap_s.new()
	_assert_true(claw.damage_per_hit < cap.damage_amount, "CLA-03_claw_lt_carapace_damage")
	claw.free()
	cap.free()


func run_all() -> int:
	print("=== ClawEnemyAttackTests ===")
	test_cla_script_exists()
	test_cla_export_defaults()
	test_cla_damage_below_carapace_single_hit()
	print("ClawEnemyAttackTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
