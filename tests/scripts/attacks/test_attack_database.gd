#
# test_attack_database.gd
#
# Behavioral tests for AttackDatabase registration and lookup.
# Spec: project_board/specs/attack_database_integration_spec.md (ADB-1 through ADB-6)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/06_attack_database_integration.md
#

class_name AttackDatabaseTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

const _DB_SCRIPT_PATH := "res://scripts/attacks/attack_database.gd"


func _load_db_script() -> GDScript:
	return load(_DB_SCRIPT_PATH) as GDScript


func _make_db(test_label: String) -> Node:
	var script = _load_db_script()
	if script == null:
		_fail_test(test_label, _DB_SCRIPT_PATH + " not loadable (not yet implemented)")
		return null
	var inst = script.new()
	if inst == null:
		_fail_test(test_label, "instantiation returned null")
		return null
	return inst


func _make_resource(overrides: Dictionary = {}) -> Resource:
	var r = AttackResource.new()
	r.startup_frames = 0
	for key in overrides:
		r.set(key, overrides[key])
	return r


# ---------------------------------------------------------------------------
# ADB-1: Class Declaration (AC-1a..AC-1d)
# ---------------------------------------------------------------------------

func test_adb01_script_loads() -> void:
	var script = _load_db_script()
	_assert_true(script != null, "ADB-01_script_loads")


func test_adb01_is_node() -> void:
	var db = _make_db("ADB-01_is_node")
	if db == null:
		return
	_assert_true(db is Node, "ADB-01_is_node")
	_assert_false(db is Resource, "ADB-01_not_resource")
	db.free()


func test_adb01_not_character_body() -> void:
	var db = _make_db("ADB-01_not_charbody")
	if db == null:
		return
	_assert_false(db is CharacterBody3D, "ADB-01_not_character_body")
	db.free()


# ---------------------------------------------------------------------------
# ADB-2: Internal Storage (AC-2a, AC-2b)
# ---------------------------------------------------------------------------

func test_adb02_base_attacks_empty() -> void:
	var db = _make_db("ADB-02_base_empty")
	if db == null:
		return
	var result = db.get_base_attack("nonexistent")
	_assert_true(result == null, "ADB-02_base_attacks_initially_empty")
	db.free()


func test_adb02_fused_attacks_empty() -> void:
	var db = _make_db("ADB-02_fused_empty")
	if db == null:
		return
	var result = db.get_fused_attack("a", "b")
	_assert_true(result == null, "ADB-02_fused_attacks_initially_empty")
	db.free()


# ---------------------------------------------------------------------------
# ADB-3: Base Attack Registration (AC-3a..AC-3e)
# ---------------------------------------------------------------------------

func test_adb03_register_and_get() -> void:
	var db = _make_db("ADB-03_register_get")
	if db == null:
		return
	var res = _make_resource({"attack_id": 1, "attack_name": "Claw"})
	db.register_base_attack("claw", res)
	var retrieved = db.get_base_attack("claw")
	_assert_true(retrieved != null, "ADB-03_returns_resource")
	_assert_true(retrieved == res, "ADB-03_same_reference")
	db.free()


func test_adb03_overwrite() -> void:
	var db = _make_db("ADB-03_overwrite")
	if db == null:
		return
	var r1 = _make_resource({"attack_id": 1, "attack_name": "Old"})
	var r2 = _make_resource({"attack_id": 2, "attack_name": "New"})
	db.register_base_attack("claw", r1)
	db.register_base_attack("claw", r2)
	var retrieved = db.get_base_attack("claw")
	_assert_true(retrieved == r2, "ADB-03_overwrite_last_write_wins")
	db.free()


func test_adb03_empty_mutation_id_rejected() -> void:
	var db = _make_db("ADB-03_empty_id")
	if db == null:
		return
	var res = _make_resource({"attack_id": 1})
	db.register_base_attack("", res)
	var retrieved = db.get_base_attack("")
	_assert_true(retrieved == null, "ADB-03_empty_id_not_stored")
	db.free()


func test_adb03_null_resource_rejected() -> void:
	var db = _make_db("ADB-03_null_res")
	if db == null:
		return
	db.register_base_attack("claw", null)
	var retrieved = db.get_base_attack("claw")
	_assert_true(retrieved == null, "ADB-03_null_resource_not_stored")
	db.free()


func test_adb03_multiple_mutations() -> void:
	var db = _make_db("ADB-03_multiple")
	if db == null:
		return
	var r1 = _make_resource({"attack_id": 1, "attack_name": "Claw"})
	var r2 = _make_resource({"attack_id": 2, "attack_name": "Acid"})
	var r3 = _make_resource({"attack_id": 3, "attack_name": "Spike"})
	db.register_base_attack("claw", r1)
	db.register_base_attack("acid", r2)
	db.register_base_attack("spike", r3)
	_assert_true(db.get_base_attack("claw") == r1, "ADB-03_multi_claw")
	_assert_true(db.get_base_attack("acid") == r2, "ADB-03_multi_acid")
	_assert_true(db.get_base_attack("spike") == r3, "ADB-03_multi_spike")
	db.free()


# ---------------------------------------------------------------------------
# ADB-4: Base Attack Lookup (AC-4a..AC-4e)
# ---------------------------------------------------------------------------

func test_adb04_returns_registered() -> void:
	var db = _make_db("ADB-04_found")
	if db == null:
		return
	var res = _make_resource({"attack_id": 10})
	db.register_base_attack("acid", res)
	var result = db.get_base_attack("acid")
	_assert_true(result == res, "ADB-04_returns_registered_resource")
	db.free()


func test_adb04_missing_returns_null() -> void:
	var db = _make_db("ADB-04_missing")
	if db == null:
		return
	var result = db.get_base_attack("nonexistent")
	_assert_true(result == null, "ADB-04_missing_returns_null")
	db.free()


func test_adb04_empty_string_returns_null() -> void:
	var db = _make_db("ADB-04_empty")
	if db == null:
		return
	var result = db.get_base_attack("")
	_assert_true(result == null, "ADB-04_empty_string_returns_null")
	db.free()


# ---------------------------------------------------------------------------
# ADB-5: Fused Attack Registration (AC-5a..AC-5f)
# ---------------------------------------------------------------------------

func test_adb05_register_and_get() -> void:
	var db = _make_db("ADB-05_register_get")
	if db == null:
		return
	var res = _make_resource({"attack_id": 50, "attack_name": "Acid+Claw"})
	db.register_fused_attack("claw", "acid", res)
	var result = db.get_fused_attack("claw", "acid")
	_assert_true(result == res, "ADB-05_fused_register_returns_resource")
	db.free()


func test_adb05_order_independent() -> void:
	var db = _make_db("ADB-05_order")
	if db == null:
		return
	var res = _make_resource({"attack_id": 51})
	db.register_fused_attack("claw", "acid", res)
	var result_ab = db.get_fused_attack("claw", "acid")
	var result_ba = db.get_fused_attack("acid", "claw")
	_assert_true(result_ab == res, "ADB-05_order_a_b")
	_assert_true(result_ba == res, "ADB-05_order_b_a")
	db.free()


func test_adb05_self_fusion_rejected() -> void:
	var db = _make_db("ADB-05_self_fusion")
	if db == null:
		return
	var res = _make_resource({"attack_id": 52})
	db.register_fused_attack("claw", "claw", res)
	var result = db.get_fused_attack("claw", "claw")
	_assert_true(result == null, "ADB-05_self_fusion_not_stored")
	db.free()


func test_adb05_empty_slot_a_rejected() -> void:
	var db = _make_db("ADB-05_empty_a")
	if db == null:
		return
	var res = _make_resource({"attack_id": 53})
	db.register_fused_attack("", "acid", res)
	var result = db.get_fused_attack("", "acid")
	_assert_true(result == null, "ADB-05_empty_slot_a_not_stored")
	db.free()


func test_adb05_empty_slot_b_rejected() -> void:
	var db = _make_db("ADB-05_empty_b")
	if db == null:
		return
	var res = _make_resource({"attack_id": 54})
	db.register_fused_attack("claw", "", res)
	var result = db.get_fused_attack("claw", "")
	_assert_true(result == null, "ADB-05_empty_slot_b_not_stored")
	db.free()


func test_adb05_null_resource_rejected() -> void:
	var db = _make_db("ADB-05_null_res")
	if db == null:
		return
	db.register_fused_attack("claw", "acid", null)
	var result = db.get_fused_attack("claw", "acid")
	_assert_true(result == null, "ADB-05_null_fused_resource_not_stored")
	db.free()


func test_adb05_overwrite_fused() -> void:
	var db = _make_db("ADB-05_overwrite")
	if db == null:
		return
	var r1 = _make_resource({"attack_id": 55, "attack_name": "Old Fusion"})
	var r2 = _make_resource({"attack_id": 56, "attack_name": "New Fusion"})
	db.register_fused_attack("claw", "acid", r1)
	db.register_fused_attack("acid", "claw", r2)
	var result = db.get_fused_attack("claw", "acid")
	_assert_true(result == r2, "ADB-05_fused_overwrite_last_write_wins")
	db.free()


# ---------------------------------------------------------------------------
# ADB-6: Fused Attack Lookup (AC-6a..AC-6d)
# ---------------------------------------------------------------------------

func test_adb06_found() -> void:
	var db = _make_db("ADB-06_found")
	if db == null:
		return
	var res = _make_resource({"attack_id": 60})
	db.register_fused_attack("spike", "acid", res)
	var result = db.get_fused_attack("spike", "acid")
	_assert_true(result == res, "ADB-06_fused_found")
	db.free()


func test_adb06_order_independent() -> void:
	var db = _make_db("ADB-06_order")
	if db == null:
		return
	var res = _make_resource({"attack_id": 61})
	db.register_fused_attack("spike", "acid", res)
	var result_forward = db.get_fused_attack("spike", "acid")
	var result_reverse = db.get_fused_attack("acid", "spike")
	_assert_true(result_forward == res, "ADB-06_order_forward")
	_assert_true(result_reverse == res, "ADB-06_order_reverse")
	db.free()


func test_adb06_missing_returns_null() -> void:
	var db = _make_db("ADB-06_missing")
	if db == null:
		return
	var result = db.get_fused_attack("unknown_a", "unknown_b")
	_assert_true(result == null, "ADB-06_missing_fused_returns_null")
	db.free()


func test_adb06_empty_slot_returns_null() -> void:
	var db = _make_db("ADB-06_empty")
	if db == null:
		return
	var result = db.get_fused_attack("", "acid")
	_assert_true(result == null, "ADB-06_empty_slot_returns_null")
	db.free()


# ---------------------------------------------------------------------------
# Edge Cases (EC-5, EC-7 from spec)
# ---------------------------------------------------------------------------

func test_ec05_overwrite_preserves_other() -> void:
	var db = _make_db("EC-05_multi_overwrite")
	if db == null:
		return
	var r1 = _make_resource({"attack_id": 1})
	var r2 = _make_resource({"attack_id": 2})
	var r3 = _make_resource({"attack_id": 3})
	db.register_base_attack("claw", r1)
	db.register_base_attack("acid", r2)
	db.register_base_attack("claw", r3)
	_assert_true(db.get_base_attack("claw") == r3, "EC-05_claw_overwritten")
	_assert_true(db.get_base_attack("acid") == r2, "EC-05_acid_unaffected")
	db.free()


func test_ec07_multiple_fused_symmetry() -> void:
	var db = _make_db("EC-07_symmetry")
	if db == null:
		return
	var r1 = _make_resource({"attack_id": 70})
	var r2 = _make_resource({"attack_id": 71})
	db.register_fused_attack("alpha", "beta", r1)
	db.register_fused_attack("gamma", "delta", r2)
	_assert_true(db.get_fused_attack("beta", "alpha") == r1, "EC-07_sym_ab")
	_assert_true(db.get_fused_attack("delta", "gamma") == r2, "EC-07_sym_cd")
	_assert_true(db.get_fused_attack("alpha", "gamma") == null, "EC-07_cross_miss")
	db.free()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AttackDatabaseTests ===")

	test_adb01_script_loads()
	test_adb01_is_node()
	test_adb01_not_character_body()

	test_adb02_base_attacks_empty()
	test_adb02_fused_attacks_empty()

	test_adb03_register_and_get()
	test_adb03_overwrite()
	test_adb03_empty_mutation_id_rejected()
	test_adb03_null_resource_rejected()
	test_adb03_multiple_mutations()

	test_adb04_returns_registered()
	test_adb04_missing_returns_null()
	test_adb04_empty_string_returns_null()

	test_adb05_register_and_get()
	test_adb05_order_independent()
	test_adb05_self_fusion_rejected()
	test_adb05_empty_slot_a_rejected()
	test_adb05_empty_slot_b_rejected()
	test_adb05_null_resource_rejected()
	test_adb05_overwrite_fused()

	test_adb06_found()
	test_adb06_order_independent()
	test_adb06_missing_returns_null()
	test_adb06_empty_slot_returns_null()

	test_ec05_overwrite_preserves_other()
	test_ec07_multiple_fused_symmetry()

	print("AttackDatabaseTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
