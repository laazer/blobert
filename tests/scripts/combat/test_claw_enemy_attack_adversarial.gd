#
# test_claw_enemy_attack_adversarial.gd
#
# ADV-CLA — claw combo contract markers.
#

class_name ClawEnemyAttackAdversarialTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# CHECKPOINT: combo must remain 2 swipes with pause + second telegraph path
func test_adv_cla_checkpoint_two_swipe_flow() -> void:
	var script: GDScript = load("res://scripts/enemy/claw_crawler_attack.gd") as GDScript
	if script == null:
		_fail_test("ADV-CLA-CHK", "claw_crawler_attack.gd missing")
		return
	var src: String = script.source_code
	_assert_true(src.contains("_open_swipe_window(1)"), "ADV-CLA-CHK_swipe1")
	_assert_true(src.contains("_open_swipe_window(2)"), "ADV-CLA-CHK_swipe2")
	_assert_true(src.contains("_begin_second_telegraph"), "ADV-CLA-CHK_second_telegraph")


func test_adv_cla_swipe_window_positive() -> void:
	var script: GDScript = load("res://scripts/enemy/claw_crawler_attack.gd") as GDScript
	if script == null:
		_fail_test("ADV-CLA-01", "claw_crawler_attack.gd missing")
		return
	var n: Object = script.new()
	_assert_true(n.swipe_hit_window_seconds > 0.0, "ADV-CLA-01_window_positive")
	n.free()


func run_all() -> int:
	print("=== ClawEnemyAttackAdversarialTests ===")
	test_adv_cla_checkpoint_two_swipe_flow()
	test_adv_cla_swipe_window_positive()
	print("ClawEnemyAttackAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
