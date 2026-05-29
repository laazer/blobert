#
# test_fused_attack_resources.gd
#
# Behavioral tests for the 6 canonical fused AttackResource registrations in
# AttackDatabaseNode._register_defaults().
#
# Spec: project_board/specs/fused_attack_resources_spec.md
# Ticket: project_board/12_milestone_12_fused_mutation_attacks/backlog/02_fused_attack_resources.md
# Traceability: FAR-3, FAR-5, FAR-6
#
# Coverage (this file — 20 test functions):
#   Registration completeness (FAR-5): 4 tests
#   Bidirectional lookup / non-null (FAR-6): 12 tests
#   Attack IDs uniqueness and mapping (FAR-3): 8 tests (IDs 101-106 + uniqueness + base range)
#
# Companion file: test_fused_attack_stats.gd (FAR-4, FAR-7, FAR-EC-1, FAR-EC-2, FAR-NF)
#
# Design notes:
#   - Uses a fresh AttackDatabaseNode per test via add_child() to trigger _ready().
#   - Does NOT use the autoload singleton to avoid cross-test contamination.
#   - Tests are RED on clean checkout: fused attacks are not yet registered in
#     _register_defaults(). All get_fused_attack() calls return null until
#     implementation adds the 6 registration blocks.
#

class_name FusedAttackResourcesTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

const _DB_SCRIPT_PATH := "res://scripts/attacks/attack_database.gd"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_db(test_label: String) -> Node:
	var script = load(_DB_SCRIPT_PATH) as GDScript
	if script == null:
		_fail_test(test_label, _DB_SCRIPT_PATH + " not loadable (not yet implemented)")
		return null
	var inst = script.new()
	if inst == null:
		_fail_test(test_label, "instantiation returned null")
		return null
	# add_child triggers _ready() -> _register_defaults()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(inst)
	else:
		_fail_test(test_label, "SceneTree not available; cannot add_child")
		inst.free()
		return null
	return inst


func _free_db(db: Node) -> void:
	if db != null and is_instance_valid(db):
		db.free()


# ---------------------------------------------------------------------------
# FAR-5: Registration completeness
# ---------------------------------------------------------------------------

func test_far5a_fused_attack_count_is_6() -> void:
	# FAR-5a: After _ready(), get_fused_attack_count() == 6.
	var label := "FAR-5a_fused_attack_count_is_6"
	var db = _make_db(label)
	if db == null:
		return
	_assert_eq_int(6, db.get_fused_attack_count(), label)
	_free_db(db)


func test_far5b_fused_count_zero_after_clear() -> void:
	# FAR-5b: After clear(), get_fused_attack_count() == 0.
	var label := "FAR-5b_fused_count_zero_after_clear"
	var db = _make_db(label)
	if db == null:
		return
	db.clear()
	_assert_eq_int(0, db.get_fused_attack_count(), label)
	_free_db(db)


func test_far5c_base_attack_count_unchanged() -> void:
	# FAR-5c: Adding fused attacks does not change get_base_attack_count() == 4.
	var label := "FAR-5c_base_attack_count_unchanged"
	var db = _make_db(label)
	if db == null:
		return
	_assert_eq_int(4, db.get_base_attack_count(), label)
	_free_db(db)


func test_far5d_double_register_defaults_no_duplication() -> void:
	# FAR-5d: Calling _register_defaults() a second time yields count 6, not 12
	# (last-write-wins; sorted keys are distinct so no self-overwrite doubles any key).
	var label := "FAR-5d_double_register_defaults_no_duplication"
	var db = _make_db(label)
	if db == null:
		return
	db.call("_register_defaults")
	_assert_eq_int(6, db.get_fused_attack_count(), label)
	_free_db(db)


# ---------------------------------------------------------------------------
# FAR-6: Bidirectional lookup — all 6 combos return non-null in both orderings
# ---------------------------------------------------------------------------

func test_far6a_acid_claw_forward_non_null() -> void:
	# FAR-6a forward: get_fused_attack("acid", "claw") != null
	var label := "FAR-6a_acid_claw_forward_non_null"
	var db = _make_db(label)
	if db == null:
		return
	_assert_true(db.get_fused_attack("acid", "claw") != null, label)
	_free_db(db)


func test_far6a_acid_claw_reverse_same_resource() -> void:
	# FAR-6a reverse: get_fused_attack("claw", "acid") != null and same resource
	var label := "FAR-6a_acid_claw_reverse_same_resource"
	var db = _make_db(label)
	if db == null:
		return
	var fwd = db.get_fused_attack("acid", "claw")
	var rev = db.get_fused_attack("claw", "acid")
	_assert_true(rev != null, label + "_non_null")
	_assert_true(fwd == rev, label + "_same_resource")
	_free_db(db)


func test_far6b_adhesion_claw_forward_non_null() -> void:
	# FAR-6b forward: get_fused_attack("adhesion", "claw") != null
	var label := "FAR-6b_adhesion_claw_forward_non_null"
	var db = _make_db(label)
	if db == null:
		return
	_assert_true(db.get_fused_attack("adhesion", "claw") != null, label)
	_free_db(db)


func test_far6b_adhesion_claw_reverse_same_resource() -> void:
	# FAR-6b reverse: get_fused_attack("claw", "adhesion") != null and same resource
	var label := "FAR-6b_adhesion_claw_reverse_same_resource"
	var db = _make_db(label)
	if db == null:
		return
	var fwd = db.get_fused_attack("adhesion", "claw")
	var rev = db.get_fused_attack("claw", "adhesion")
	_assert_true(rev != null, label + "_non_null")
	_assert_true(fwd == rev, label + "_same_resource")
	_free_db(db)


func test_far6c_carapace_claw_forward_non_null() -> void:
	# FAR-6c forward: get_fused_attack("carapace", "claw") != null
	var label := "FAR-6c_carapace_claw_forward_non_null"
	var db = _make_db(label)
	if db == null:
		return
	_assert_true(db.get_fused_attack("carapace", "claw") != null, label)
	_free_db(db)


func test_far6c_carapace_claw_reverse_same_resource() -> void:
	# FAR-6c reverse: get_fused_attack("claw", "carapace") != null and same resource
	var label := "FAR-6c_carapace_claw_reverse_same_resource"
	var db = _make_db(label)
	if db == null:
		return
	var fwd = db.get_fused_attack("carapace", "claw")
	var rev = db.get_fused_attack("claw", "carapace")
	_assert_true(rev != null, label + "_non_null")
	_assert_true(fwd == rev, label + "_same_resource")
	_free_db(db)


func test_far6d_acid_adhesion_forward_non_null() -> void:
	# FAR-6d forward: get_fused_attack("acid", "adhesion") != null
	var label := "FAR-6d_acid_adhesion_forward_non_null"
	var db = _make_db(label)
	if db == null:
		return
	_assert_true(db.get_fused_attack("acid", "adhesion") != null, label)
	_free_db(db)


func test_far6d_acid_adhesion_reverse_same_resource() -> void:
	# FAR-6d reverse: get_fused_attack("adhesion", "acid") != null and same resource
	var label := "FAR-6d_acid_adhesion_reverse_same_resource"
	var db = _make_db(label)
	if db == null:
		return
	var fwd = db.get_fused_attack("acid", "adhesion")
	var rev = db.get_fused_attack("adhesion", "acid")
	_assert_true(rev != null, label + "_non_null")
	_assert_true(fwd == rev, label + "_same_resource")
	_free_db(db)


func test_far6e_acid_carapace_forward_non_null() -> void:
	# FAR-6e forward: get_fused_attack("acid", "carapace") != null
	var label := "FAR-6e_acid_carapace_forward_non_null"
	var db = _make_db(label)
	if db == null:
		return
	_assert_true(db.get_fused_attack("acid", "carapace") != null, label)
	_free_db(db)


func test_far6e_acid_carapace_reverse_same_resource() -> void:
	# FAR-6e reverse: get_fused_attack("carapace", "acid") != null and same resource
	var label := "FAR-6e_acid_carapace_reverse_same_resource"
	var db = _make_db(label)
	if db == null:
		return
	var fwd = db.get_fused_attack("acid", "carapace")
	var rev = db.get_fused_attack("carapace", "acid")
	_assert_true(rev != null, label + "_non_null")
	_assert_true(fwd == rev, label + "_same_resource")
	_free_db(db)


func test_far6f_adhesion_carapace_forward_non_null() -> void:
	# FAR-6f forward: get_fused_attack("adhesion", "carapace") != null
	var label := "FAR-6f_adhesion_carapace_forward_non_null"
	var db = _make_db(label)
	if db == null:
		return
	_assert_true(db.get_fused_attack("adhesion", "carapace") != null, label)
	_free_db(db)


func test_far6f_adhesion_carapace_reverse_same_resource() -> void:
	# FAR-6f reverse: get_fused_attack("carapace", "adhesion") != null and same resource
	var label := "FAR-6f_adhesion_carapace_reverse_same_resource"
	var db = _make_db(label)
	if db == null:
		return
	var fwd = db.get_fused_attack("adhesion", "carapace")
	var rev = db.get_fused_attack("carapace", "adhesion")
	_assert_true(rev != null, label + "_non_null")
	_assert_true(fwd == rev, label + "_same_resource")
	_free_db(db)


# ---------------------------------------------------------------------------
# FAR-3: Attack IDs — uniqueness and per-combo mapping (IDs 101-106)
# ---------------------------------------------------------------------------

func test_far3a_acid_claw_attack_id_101() -> void:
	# FAR-3a: acid_claw attack_id == 101
	var label := "FAR-3a_acid_claw_attack_id_101"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test(label, "acid_claw returned null (not yet registered)")
		_free_db(db)
		return
	_assert_eq_int(101, res.attack_id, label)
	_free_db(db)


func test_far3b_adhesion_claw_attack_id_102() -> void:
	# FAR-3b: adhesion_claw attack_id == 102
	var label := "FAR-3b_adhesion_claw_attack_id_102"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("adhesion", "claw")
	if res == null:
		_fail_test(label, "adhesion_claw returned null (not yet registered)")
		_free_db(db)
		return
	_assert_eq_int(102, res.attack_id, label)
	_free_db(db)


func test_far3c_carapace_claw_attack_id_103() -> void:
	# FAR-3c: carapace_claw attack_id == 103
	var label := "FAR-3c_carapace_claw_attack_id_103"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("carapace", "claw")
	if res == null:
		_fail_test(label, "carapace_claw returned null (not yet registered)")
		_free_db(db)
		return
	_assert_eq_int(103, res.attack_id, label)
	_free_db(db)


func test_far3d_acid_adhesion_attack_id_104() -> void:
	# FAR-3d: acid_adhesion attack_id == 104
	var label := "FAR-3d_acid_adhesion_attack_id_104"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "adhesion")
	if res == null:
		_fail_test(label, "acid_adhesion returned null (not yet registered)")
		_free_db(db)
		return
	_assert_eq_int(104, res.attack_id, label)
	_free_db(db)


func test_far3e_acid_carapace_attack_id_105() -> void:
	# FAR-3e: acid_carapace attack_id == 105
	var label := "FAR-3e_acid_carapace_attack_id_105"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "carapace")
	if res == null:
		_fail_test(label, "acid_carapace returned null (not yet registered)")
		_free_db(db)
		return
	_assert_eq_int(105, res.attack_id, label)
	_free_db(db)


func test_far3f_adhesion_carapace_attack_id_106() -> void:
	# FAR-3f: adhesion_carapace attack_id == 106
	var label := "FAR-3f_adhesion_carapace_attack_id_106"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("adhesion", "carapace")
	if res == null:
		_fail_test(label, "adhesion_carapace returned null (not yet registered)")
		_free_db(db)
		return
	_assert_eq_int(106, res.attack_id, label)
	_free_db(db)


func test_far3g_all_fused_attack_ids_unique() -> void:
	# FAR-3g: No two fused attacks share an attack_id (uniqueness across all 6).
	var label := "FAR-3g_all_fused_attack_ids_unique"
	var db = _make_db(label)
	if db == null:
		return
	var combos: Array = [
		["acid", "claw"],
		["adhesion", "claw"],
		["carapace", "claw"],
		["acid", "adhesion"],
		["acid", "carapace"],
		["adhesion", "carapace"],
	]
	var ids: Array = []
	for pair in combos:
		var res = db.get_fused_attack(pair[0], pair[1])
		if res == null:
			_fail_test(label, "get_fused_attack('%s', '%s') returned null" % [pair[0], pair[1]])
			_free_db(db)
			return
		ids.append(res.attack_id)
	var unique_ids: Array = []
	for id in ids:
		if id not in unique_ids:
			unique_ids.append(id)
	_assert_eq_int(6, unique_ids.size(), label + "_six_distinct_ids")
	_free_db(db)


func test_far3h_base_attacks_not_in_fused_id_range() -> void:
	# FAR-3h: No base attack has an attack_id in range 101-106.
	var label := "FAR-3h_base_attacks_not_in_fused_id_range"
	var db = _make_db(label)
	if db == null:
		return
	var bases := ["claw", "acid", "carapace", "adhesion"]
	for mutation_id in bases:
		var res = db.get_base_attack(mutation_id)
		if res == null:
			_fail_test(label, "base attack '%s' returned null" % mutation_id)
			_free_db(db)
			return
		var ok: bool = res.attack_id < 101 or res.attack_id > 106
		_assert_true(ok, label + "_" + mutation_id + "_not_in_101_106")
	_free_db(db)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== FusedAttackResourcesTests ===")

	# FAR-5: Registration completeness
	test_far5a_fused_attack_count_is_6()
	test_far5b_fused_count_zero_after_clear()
	test_far5c_base_attack_count_unchanged()
	test_far5d_double_register_defaults_no_duplication()

	# FAR-6: Bidirectional lookup — all 6 combos, both orderings
	test_far6a_acid_claw_forward_non_null()
	test_far6a_acid_claw_reverse_same_resource()
	test_far6b_adhesion_claw_forward_non_null()
	test_far6b_adhesion_claw_reverse_same_resource()
	test_far6c_carapace_claw_forward_non_null()
	test_far6c_carapace_claw_reverse_same_resource()
	test_far6d_acid_adhesion_forward_non_null()
	test_far6d_acid_adhesion_reverse_same_resource()
	test_far6e_acid_carapace_forward_non_null()
	test_far6e_acid_carapace_reverse_same_resource()
	test_far6f_adhesion_carapace_forward_non_null()
	test_far6f_adhesion_carapace_reverse_same_resource()

	# FAR-3: Attack IDs — per-combo mapping and uniqueness
	test_far3a_acid_claw_attack_id_101()
	test_far3b_adhesion_claw_attack_id_102()
	test_far3c_carapace_claw_attack_id_103()
	test_far3d_acid_adhesion_attack_id_104()
	test_far3e_acid_carapace_attack_id_105()
	test_far3f_adhesion_carapace_attack_id_106()
	test_far3g_all_fused_attack_ids_unique()
	test_far3h_base_attacks_not_in_fused_id_range()

	print(
		"FusedAttackResourcesTests: "
		+ str(_pass_count) + " passed, "
		+ str(_fail_count) + " failed"
	)
	return _fail_count
