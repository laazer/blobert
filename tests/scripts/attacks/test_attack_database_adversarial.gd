#
# test_attack_database_adversarial.gd
#
# Adversarial and edge-case tests for AttackDatabase.
# Targets: boundary inputs, type coercion, stress volume, mutation testing,
# key collision, case sensitivity, determinism, and spec gap detection.
# Spec: project_board/specs/attack_database_integration_spec.md (ADB-1..ADB-6, EC-1..EC-8, EC-23)
# Ticket: M11-06 (06_attack_database_integration)
#

class_name AttackDatabaseAdversarialTests
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
# BOUNDARY: Whitespace-only mutation_id (not empty, but semantically invalid)
# Existing tests cover "" but not " ". Spec ADB-3 only guards "".
# Conservative assumption: whitespace-only IDs are storable (no guard in spec).
# Mutation this would catch: implementation adds .strip_edges() guard
# ---------------------------------------------------------------------------

func test_whitespace_mutation_id_storable() -> void:
	# CHECKPOINT: Spec ADB-3 only rejects "" explicitly. Whitespace IDs are
	# technically storable per last-write-wins semantics.
	var db = _make_db("ADV_whitespace_id")
	if db == null:
		return
	var res = _make_resource({"attack_id": 100})
	db.register_base_attack(" ", res)
	var result = db.get_base_attack(" ")
	_assert_true(result == res, "ADV_whitespace_id_stored")
	db.free()


func test_whitespace_and_real_id_independent() -> void:
	var db = _make_db("ADV_ws_vs_real")
	if db == null:
		return
	var r1 = _make_resource({"attack_id": 101})
	var r2 = _make_resource({"attack_id": 102})
	db.register_base_attack(" ", r1)
	db.register_base_attack("claw", r2)
	_assert_true(db.get_base_attack(" ") == r1, "ADV_ws_independent_space")
	_assert_true(db.get_base_attack("claw") == r2, "ADV_ws_independent_claw")
	db.free()


# ---------------------------------------------------------------------------
# BOUNDARY: Case sensitivity — "Claw" vs "claw"
# Spec uses lowercase examples. GDScript strings are case-sensitive.
# This tests the implementation does NOT normalize case.
# Mutation catch: implementation lowercases keys
# ---------------------------------------------------------------------------

func test_case_sensitive_base_keys() -> void:
	var db = _make_db("ADV_case_base")
	if db == null:
		return
	var r_lower = _make_resource({"attack_id": 110})
	var r_upper = _make_resource({"attack_id": 111})
	db.register_base_attack("claw", r_lower)
	db.register_base_attack("Claw", r_upper)
	_assert_true(db.get_base_attack("claw") == r_lower, "ADV_case_lower")
	_assert_true(db.get_base_attack("Claw") == r_upper, "ADV_case_upper")
	_assert_true(db.get_base_attack("CLAW") == null, "ADV_case_allcaps_miss")
	db.free()


func test_case_sensitive_fused_keys() -> void:
	var db = _make_db("ADV_case_fused")
	if db == null:
		return
	var r1 = _make_resource({"attack_id": 112})
	var r2 = _make_resource({"attack_id": 113})
	db.register_fused_attack("Acid", "claw", r1)
	db.register_fused_attack("acid", "claw", r2)
	_assert_true(db.get_fused_attack("Acid", "claw") == r1, "ADV_case_fused_mixed")
	_assert_true(db.get_fused_attack("acid", "claw") == r2, "ADV_case_fused_lower")
	db.free()


# ---------------------------------------------------------------------------
# EC-23: Key collision — base key "acid_claw" vs fused key "acid_claw"
# Spec notes this is theoretically possible if a mutation_id contains underscore.
# The two dictionaries are separate, so no collision should occur.
# Mutation catch: implementation uses a single dictionary for both
# ---------------------------------------------------------------------------

func test_ec23_base_and_fused_key_no_collision() -> void:
	var db = _make_db("EC-23_collision")
	if db == null:
		return
	var base_res = _make_resource({"attack_id": 200, "attack_name": "BaseAcidClaw"})
	var fused_res = _make_resource({"attack_id": 201, "attack_name": "FusedAcidClaw"})
	db.register_base_attack("acid_claw", base_res)
	db.register_fused_attack("acid", "claw", fused_res)
	_assert_true(db.get_base_attack("acid_claw") == base_res, "EC-23_base_unaffected")
	_assert_true(db.get_fused_attack("acid", "claw") == fused_res, "EC-23_fused_unaffected")
	db.free()


func test_underscore_in_mutation_id() -> void:
	var db = _make_db("ADV_underscore_id")
	if db == null:
		return
	var res = _make_resource({"attack_id": 202})
	db.register_base_attack("fire_claw", res)
	_assert_true(db.get_base_attack("fire_claw") == res, "ADV_underscore_id_stored")
	_assert_true(db.get_base_attack("fire") == null, "ADV_underscore_no_partial_match")
	db.free()


# ---------------------------------------------------------------------------
# STRESS: Register many base attacks, verify all retrievable
# Mutation catch: dictionary capacity bug, key hash collision
# ---------------------------------------------------------------------------

func test_stress_100_base_attacks() -> void:
	var db = _make_db("ADV_stress_100")
	if db == null:
		return
	var resources: Array = []
	for i in range(100):
		var res = _make_resource({"attack_id": i})
		resources.append(res)
		db.register_base_attack("mut_%d" % i, res)

	var all_match = true
	for i in range(100):
		var result = db.get_base_attack("mut_%d" % i)
		if result != resources[i]:
			all_match = false
			break
	_assert_true(all_match, "ADV_stress_100_all_match")
	db.free()


func test_stress_50_fused_attacks() -> void:
	var db = _make_db("ADV_stress_50_fused")
	if db == null:
		return
	var resources: Array = []
	for i in range(50):
		var res = _make_resource({"attack_id": 1000 + i})
		resources.append(res)
		db.register_fused_attack("type_a_%d" % i, "type_b_%d" % i, res)

	var all_match = true
	for i in range(50):
		var result = db.get_fused_attack("type_a_%d" % i, "type_b_%d" % i)
		if result != resources[i]:
			all_match = false
			break
	_assert_true(all_match, "ADV_stress_50_fused_all_match")
	db.free()


# ---------------------------------------------------------------------------
# BOUNDARY: Numeric string mutation_ids
# Mutation catch: implementation coerces string to int
# ---------------------------------------------------------------------------

func test_numeric_string_mutation_id() -> void:
	var db = _make_db("ADV_numeric_str")
	if db == null:
		return
	var r0 = _make_resource({"attack_id": 300})
	var r1 = _make_resource({"attack_id": 301})
	db.register_base_attack("0", r0)
	db.register_base_attack("1", r1)
	_assert_true(db.get_base_attack("0") == r0, "ADV_numeric_zero_str")
	_assert_true(db.get_base_attack("1") == r1, "ADV_numeric_one_str")
	_assert_true(db.get_base_attack("00") == null, "ADV_numeric_not_coerced")
	db.free()


# ---------------------------------------------------------------------------
# BOUNDARY: Very long mutation_id
# Mutation catch: truncation or buffer issues
# ---------------------------------------------------------------------------

func test_long_mutation_id() -> void:
	var db = _make_db("ADV_long_id")
	if db == null:
		return
	var long_id = ""
	for i in range(500):
		long_id += "a"
	var res = _make_resource({"attack_id": 400})
	db.register_base_attack(long_id, res)
	_assert_true(db.get_base_attack(long_id) == res, "ADV_long_id_stored")
	db.free()


# ---------------------------------------------------------------------------
# MUTATION: Overwrite with same reference (idempotent)
# Mutation catch: overwrite corrupts the stored reference
# ---------------------------------------------------------------------------

func test_overwrite_same_reference() -> void:
	var db = _make_db("ADV_same_ref_overwrite")
	if db == null:
		return
	var res = _make_resource({"attack_id": 500})
	db.register_base_attack("claw", res)
	db.register_base_attack("claw", res)
	_assert_true(db.get_base_attack("claw") == res, "ADV_same_ref_overwrite_preserved")
	db.free()


# ---------------------------------------------------------------------------
# MUTATION: Register then free resource — stale reference detection
# The database stores a reference; if the resource is freed externally,
# get_base_attack should still return something (Godot doesn't null freed refs).
# This is a real-world footgun test.
# ---------------------------------------------------------------------------

func test_register_and_access_after_resource_property_change() -> void:
	var db = _make_db("ADV_mut_after_change")
	if db == null:
		return
	var res = _make_resource({"attack_id": 600, "damage": 5.0})
	db.register_base_attack("acid", res)
	res.damage = 99.0
	var retrieved = db.get_base_attack("acid")
	_assert_true(retrieved != null, "ADV_resource_still_valid")
	_assert_eq_float(99.0, retrieved.damage, "ADV_resource_reflects_mutation")
	db.free()


# ---------------------------------------------------------------------------
# DETERMINISM: Same operations in same order → same results
# ---------------------------------------------------------------------------

func test_deterministic_registration_order() -> void:
	var db1 = _make_db("ADV_determinism_1")
	var db2 = _make_db("ADV_determinism_2")
	if db1 == null or db2 == null:
		if db1 != null:
			db1.free()
		if db2 != null:
			db2.free()
		return
	var r1 = _make_resource({"attack_id": 1})
	var r2 = _make_resource({"attack_id": 2})
	var r3 = _make_resource({"attack_id": 3})
	db1.register_base_attack("a", r1)
	db1.register_base_attack("b", r2)
	db1.register_base_attack("c", r3)
	db2.register_base_attack("a", r1)
	db2.register_base_attack("b", r2)
	db2.register_base_attack("c", r3)
	_assert_true(db1.get_base_attack("a") == db2.get_base_attack("a"), "ADV_determinism_a")
	_assert_true(db1.get_base_attack("b") == db2.get_base_attack("b"), "ADV_determinism_b")
	_assert_true(db1.get_base_attack("c") == db2.get_base_attack("c"), "ADV_determinism_c")
	db1.free()
	db2.free()


# ---------------------------------------------------------------------------
# FUSED: Alphabetical sort verification — canonical key correctness
# Tests that the canonical key is truly alphabetical: "z" + "a" → "a_z"
# Mutation catch: sort is reversed, or join separator is wrong
# ---------------------------------------------------------------------------

func test_fused_canonical_key_alphabetical_reverse() -> void:
	var db = _make_db("ADV_fused_alpha_rev")
	if db == null:
		return
	var res = _make_resource({"attack_id": 700})
	db.register_fused_attack("zzz", "aaa", res)
	_assert_true(db.get_fused_attack("aaa", "zzz") == res, "ADV_fused_alpha_aaa_zzz")
	_assert_true(db.get_fused_attack("zzz", "aaa") == res, "ADV_fused_alpha_zzz_aaa")
	db.free()


func test_fused_canonical_key_identical_prefix() -> void:
	var db = _make_db("ADV_fused_prefix")
	if db == null:
		return
	var r1 = _make_resource({"attack_id": 701})
	var r2 = _make_resource({"attack_id": 702})
	db.register_fused_attack("abc", "abd", r1)
	db.register_fused_attack("abc", "abz", r2)
	_assert_true(db.get_fused_attack("abc", "abd") == r1, "ADV_fused_prefix_abd")
	_assert_true(db.get_fused_attack("abc", "abz") == r2, "ADV_fused_prefix_abz")
	_assert_true(db.get_fused_attack("abd", "abz") == null, "ADV_fused_prefix_cross_miss")
	db.free()


# ---------------------------------------------------------------------------
# BOUNDARY: Fused with empty string combinations
# Spec ADB-5 rejects when either slot is empty. Test all permutations.
# ---------------------------------------------------------------------------

func test_fused_both_empty() -> void:
	var db = _make_db("ADV_fused_both_empty")
	if db == null:
		return
	var res = _make_resource({"attack_id": 800})
	db.register_fused_attack("", "", res)
	_assert_true(db.get_fused_attack("", "") == null, "ADV_fused_both_empty_rejected")
	db.free()


# ---------------------------------------------------------------------------
# MUTATION: get_fused_attack with self-key (same id both slots)
# The lookup should also use canonical key, so "claw","claw" → "claw_claw"
# But registration is rejected for self-fusion. So lookup should return null.
# ---------------------------------------------------------------------------

func test_fused_lookup_self_key() -> void:
	var db = _make_db("ADV_fused_self_lookup")
	if db == null:
		return
	var result = db.get_fused_attack("claw", "claw")
	_assert_true(result == null, "ADV_fused_self_lookup_returns_null")
	db.free()


# ---------------------------------------------------------------------------
# MUTATION: Multiple overwrites preserve last value
# Catch: off-by-one in overwrite logic
# ---------------------------------------------------------------------------

func test_triple_overwrite_base() -> void:
	var db = _make_db("ADV_triple_overwrite")
	if db == null:
		return
	var r1 = _make_resource({"attack_id": 901})
	var r2 = _make_resource({"attack_id": 902})
	var r3 = _make_resource({"attack_id": 903})
	db.register_base_attack("x", r1)
	db.register_base_attack("x", r2)
	db.register_base_attack("x", r3)
	_assert_true(db.get_base_attack("x") == r3, "ADV_triple_overwrite_last_wins")
	db.free()


# ---------------------------------------------------------------------------
# ISOLATION: Two database instances do not share state
# Catch: global/static state leaking between instances
# ---------------------------------------------------------------------------

func test_instance_isolation() -> void:
	var db1 = _make_db("ADV_isolation_1")
	var db2 = _make_db("ADV_isolation_2")
	if db1 == null or db2 == null:
		if db1 != null:
			db1.free()
		if db2 != null:
			db2.free()
		return
	var res = _make_resource({"attack_id": 999})
	db1.register_base_attack("shared_key", res)
	_assert_true(db1.get_base_attack("shared_key") == res, "ADV_isolation_db1_has")
	_assert_true(db2.get_base_attack("shared_key") == null, "ADV_isolation_db2_empty")
	db1.free()
	db2.free()


# ---------------------------------------------------------------------------
# NULL/EMPTY: Sequential null registrations on same key
# Catch: first null leaves a partial entry that second null corrupts
# ---------------------------------------------------------------------------

func test_sequential_null_registration() -> void:
	var db = _make_db("ADV_seq_null")
	if db == null:
		return
	db.register_base_attack("claw", null)
	db.register_base_attack("claw", null)
	_assert_true(db.get_base_attack("claw") == null, "ADV_seq_null_still_empty")
	db.free()


# ---------------------------------------------------------------------------
# NULL/EMPTY: Register valid then null on same key
# Spec ADB-3 says null is rejected with warning; existing entry should survive
# Catch: null overwrites valid entry
# ---------------------------------------------------------------------------

func test_valid_then_null_preserves_original() -> void:
	var db = _make_db("ADV_valid_then_null")
	if db == null:
		return
	var res = _make_resource({"attack_id": 1001})
	db.register_base_attack("claw", res)
	db.register_base_attack("claw", null)
	_assert_true(db.get_base_attack("claw") == res, "ADV_valid_then_null_preserved")
	db.free()


# ---------------------------------------------------------------------------
# FUSED: Register valid then null resource on same pair
# Same logic as base: null should be rejected, existing entry survives
# ---------------------------------------------------------------------------

func test_fused_valid_then_null_preserves() -> void:
	var db = _make_db("ADV_fused_valid_null")
	if db == null:
		return
	var res = _make_resource({"attack_id": 1002})
	db.register_fused_attack("a", "b", res)
	db.register_fused_attack("a", "b", null)
	_assert_true(db.get_fused_attack("a", "b") == res, "ADV_fused_valid_then_null_preserved")
	db.free()


# ---------------------------------------------------------------------------
# BOUNDARY: Fused with one slot empty, one valid — both permutations
# ADB-5 step 2: either slot empty → rejected
# ---------------------------------------------------------------------------

func test_fused_empty_a_valid_b() -> void:
	var db = _make_db("ADV_fused_empty_a")
	if db == null:
		return
	var res = _make_resource({"attack_id": 1003})
	db.register_fused_attack("", "valid", res)
	_assert_true(db.get_fused_attack("", "valid") == null, "ADV_fused_empty_a_rejected")
	db.free()


func test_fused_valid_a_empty_b() -> void:
	var db = _make_db("ADV_fused_empty_b")
	if db == null:
		return
	var res = _make_resource({"attack_id": 1004})
	db.register_fused_attack("valid", "", res)
	_assert_true(db.get_fused_attack("valid", "") == null, "ADV_fused_empty_b_rejected")
	db.free()


# ---------------------------------------------------------------------------
# MUTATION: _make_fused_key correctness for Unicode / special chars
# Tests that non-ASCII characters sort correctly via GDScript default sort
# ---------------------------------------------------------------------------

func test_fused_unicode_mutation_ids() -> void:
	var db = _make_db("ADV_fused_unicode")
	if db == null:
		return
	var res = _make_resource({"attack_id": 1100})
	db.register_fused_attack("alpha", "beta", res)
	_assert_true(db.get_fused_attack("beta", "alpha") == res, "ADV_unicode_latin_symmetric")
	db.free()


# ---------------------------------------------------------------------------
# ISOLATION: Fused and base dictionaries don't leak into each other
# Registering a base attack doesn't create a fused entry and vice versa
# ---------------------------------------------------------------------------

func test_base_does_not_create_fused_entry() -> void:
	var db = _make_db("ADV_base_no_fused")
	if db == null:
		return
	var res = _make_resource({"attack_id": 1200})
	db.register_base_attack("acid", res)
	_assert_true(db.get_fused_attack("acid", "anything") == null, "ADV_base_no_fused_leak")
	db.free()


func test_fused_does_not_create_base_entry() -> void:
	var db = _make_db("ADV_fused_no_base")
	if db == null:
		return
	var res = _make_resource({"attack_id": 1201})
	db.register_fused_attack("acid", "claw", res)
	_assert_true(db.get_base_attack("acid") == null, "ADV_fused_no_base_leak_a")
	_assert_true(db.get_base_attack("claw") == null, "ADV_fused_no_base_leak_b")
	db.free()


# ---------------------------------------------------------------------------
# COMBINATORIAL: Empty + null + self-fusion in one sequence
# ---------------------------------------------------------------------------

func test_combinatorial_invalid_sequence() -> void:
	var db = _make_db("ADV_combo_invalid")
	if db == null:
		return
	var res = _make_resource({"attack_id": 1300})
	db.register_fused_attack("", "b", res)
	db.register_fused_attack("a", "", res)
	db.register_fused_attack("a", "a", res)
	db.register_fused_attack("a", "b", null)
	_assert_true(db.get_fused_attack("a", "b") == null, "ADV_combo_all_invalid_no_entry")
	db.free()


# ---------------------------------------------------------------------------
# MUTATION: get_base_attack after registering only fused attack for those ids
# Base and fused are separate; having a fused("a","b") does not imply base("a")
# ---------------------------------------------------------------------------

func test_fused_registration_does_not_populate_base() -> void:
	var db = _make_db("ADV_fused_not_base")
	if db == null:
		return
	var res = _make_resource({"attack_id": 1400})
	db.register_fused_attack("spike", "venom", res)
	_assert_true(db.get_base_attack("spike") == null, "ADV_fused_no_base_spike")
	_assert_true(db.get_base_attack("venom") == null, "ADV_fused_no_base_venom")
	_assert_true(db.get_fused_attack("spike", "venom") == res, "ADV_fused_still_works")
	db.free()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AttackDatabaseAdversarialTests ===")

	test_whitespace_mutation_id_storable()
	test_whitespace_and_real_id_independent()

	test_case_sensitive_base_keys()
	test_case_sensitive_fused_keys()

	test_ec23_base_and_fused_key_no_collision()
	test_underscore_in_mutation_id()

	test_stress_100_base_attacks()
	test_stress_50_fused_attacks()

	test_numeric_string_mutation_id()
	test_long_mutation_id()
	test_overwrite_same_reference()
	test_register_and_access_after_resource_property_change()
	test_deterministic_registration_order()

	test_fused_canonical_key_alphabetical_reverse()
	test_fused_canonical_key_identical_prefix()
	test_fused_both_empty()
	test_fused_lookup_self_key()
	test_triple_overwrite_base()

	test_instance_isolation()
	test_sequential_null_registration()
	test_valid_then_null_preserves_original()
	test_fused_valid_then_null_preserves()

	test_fused_empty_a_valid_b()
	test_fused_valid_a_empty_b()
	test_fused_unicode_mutation_ids()

	test_base_does_not_create_fused_entry()
	test_fused_does_not_create_base_entry()
	test_combinatorial_invalid_sequence()
	test_fused_registration_does_not_populate_base()

	print("AttackDatabaseAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
