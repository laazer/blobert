#
# test_carapace_enemy_attack_adversarial.gd
#
# ADV-CEA — conservative bounds on carapace charge attack.
#

class_name CarapaceEnemyAttackAdversarialTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# CHECKPOINT: telegraph floor for carapace must remain >= 0.6 s wall-clock (CEA-3)
func test_adv_cea_checkpoint_min_telegraph_constant() -> void:
	var script: GDScript = load("res://scripts/enemy/carapace_husk_attack.gd") as GDScript
	if script == null:
		_fail_test("ADV-CEA-CHK", "carapace_husk_attack.gd missing")
		return
	var src: String = script.source_code
	_assert_true(src.contains("begin_ranged_attack_telegraph(_MIN_TELEGRAPH_WALL_SEC)"), "ADV-CEA-CHK_telegraph_call")
	_assert_true(src.contains("0.6"), "ADV-CEA-CHK_min_constant")


func test_adv_cea_decel_factor_sane() -> void:
	var script: GDScript = load("res://scripts/enemy/carapace_husk_attack.gd") as GDScript
	if script == null:
		_fail_test("ADV-CEA-01", "carapace_husk_attack.gd missing")
		return
	var n: Object = script.new()
	_assert_true(n.decel_factor > 0.0 and n.decel_factor < 1.0, "ADV-CEA-01_decel_between_0_1")
	n.free()


func run_all() -> int:
	print("=== CarapaceEnemyAttackAdversarialTests ===")
	test_adv_cea_checkpoint_min_telegraph_constant()
	test_adv_cea_decel_factor_sane()
	print("CarapaceEnemyAttackAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
