#
# test_mutation_slot_system_dual.gd
#
# Primary behavioral tests for the dual-slot MutationSlotManager.
# Spec: two_mutation_slots_spec.md
#
# Covers DSM-1 (MutationSlotManager API), DSM-2 (fill-order rule),
# DSM-3 (any_filled / speed-buff rule), DSM-5 (backward-compat alias),
# and DSM-6 (InfectionAbsorbResolver dispatch).
#
# Red-green pattern: tests are written before implementation.
# All tests should FAIL before MutationSlotManager exists.
#

class_name MutationSlotSystemDualTests
extends Object


const DEFAULT_MUTATION_ID: String = "infection_mutation_01"


var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)


func _assert_true(condition: bool, test_name: String) -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected true, got false")


func _assert_false(condition: bool, test_name: String) -> void:
	if not condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected false, got true")


func _assert_eq_string(expected: String, actual: String, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected '" + expected + "', got '" + actual + "'")


func _assert_eq_int(expected: int, actual: int, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected " + str(expected) + ", got " + str(actual))


func _make_manager() -> Object:
	var script: GDScript = load("res://scripts/mutation/mutation_slot_manager.gd") as GDScript
	if script == null:
		return null
	return script.new()


func _make_esm() -> Object:
	var script: GDScript = load("res://scripts/enemy/enemy_state_machine.gd") as GDScript
	if script == null:
		return null
	return script.new()


func _make_inventory() -> Object:
	var script: GDScript = load("res://scripts/mutation/mutation_inventory.gd") as GDScript
	if script == null:
		return null
	return script.new()


func _make_resolver() -> Object:
	var script: GDScript = load("res://scripts/infection/infection_absorb_resolver.gd") as GDScript
	if script == null:
		return null
	return script.new()


# ---------------------------------------------------------------------------
# DSM-1 — MutationSlotManager pure-logic class
# ---------------------------------------------------------------------------

func test_manager_script_loads_and_instantiates() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail(
			"dsm1_loads",
			"res://scripts/mutation/mutation_slot_manager.gd not found; implement MutationSlotManager per DSM-1"
		)
		return
	_pass("dsm1_loads")
	_assert_false(manager is Node, "dsm1_not_node — MutationSlotManager must not extend Node")


func test_manager_slot_count_is_two() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_slot_count", "manager missing; skipping")
		return
	if not manager.has_method("get_slot_count"):
		_fail("dsm1_slot_count", "get_slot_count() not found")
		return
	_assert_eq_int(2, manager.get_slot_count(), "dsm1_slot_count — get_slot_count() returns 2")


func test_manager_get_slot_0_and_1_non_null() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_get_slot_non_null", "manager missing; skipping")
		return
	if not manager.has_method("get_slot"):
		_fail("dsm1_get_slot_non_null", "get_slot() not found")
		return
	var s0: Object = manager.get_slot(0)
	var s1: Object = manager.get_slot(1)
	_assert_true(s0 != null, "dsm1_slot0_non_null — get_slot(0) returns non-null")
	_assert_true(s1 != null, "dsm1_slot1_non_null — get_slot(1) returns non-null")


func test_manager_slots_have_required_api() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_slot_api", "manager missing; skipping")
		return
	var s0: Object = manager.get_slot(0)
	var s1: Object = manager.get_slot(1)
	if s0 == null or s1 == null:
		_fail("dsm1_slot_api", "get_slot returned null; skipping")
		return
	_assert_true(
		s0.has_method("is_filled") and s0.has_method("get_active_mutation_id")
		and s0.has_method("set_active_mutation_id") and s0.has_method("clear"),
		"dsm1_slot0_api — slot A has all required MutationSlot methods"
	)
	_assert_true(
		s1.has_method("is_filled") and s1.has_method("get_active_mutation_id")
		and s1.has_method("set_active_mutation_id") and s1.has_method("clear"),
		"dsm1_slot1_api — slot B has all required MutationSlot methods"
	)


func test_manager_slots_are_independent_instances() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_slots_independent", "manager missing; skipping")
		return
	var s0: Object = manager.get_slot(0)
	var s1: Object = manager.get_slot(1)
	if s0 == null or s1 == null:
		_fail("dsm1_slots_independent", "get_slot returned null; skipping")
		return
	_assert_true(s0 != s1, "dsm1_slots_independent — slot A and slot B are different object references")


func test_manager_get_slot_out_of_range_returns_null() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_oob_null", "manager missing; skipping")
		return
	var neg: Object = manager.get_slot(-1)
	var two: Object = manager.get_slot(2)
	var big: Object = manager.get_slot(99)
	_assert_true(neg == null, "dsm1_slot_neg1_null — get_slot(-1) returns null")
	_assert_true(two == null, "dsm1_slot_2_null — get_slot(2) returns null")
	_assert_true(big == null, "dsm1_slot_99_null — get_slot(99) returns null")


func test_manager_clear_slot_oob_does_not_crash() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_clear_slot_oob", "manager missing; skipping")
		return
	if not manager.has_method("clear_slot"):
		_fail("dsm1_clear_slot_oob", "clear_slot() not found")
		return
	manager.clear_slot(-1)
	manager.clear_slot(2)
	_pass("dsm1_clear_slot_oob — clear_slot with out-of-range index does not crash")


# ---------------------------------------------------------------------------
# DSM-2 — Fill-order rule
# ---------------------------------------------------------------------------

func test_fill_first_goes_to_slot_a() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("fill_next_available"):
		_fail("dsm2_fill_first_slot_a", "manager or fill_next_available missing; skipping")
		return
	manager.fill_next_available("mutation_a")
	var s0: Object = manager.get_slot(0)
	var s1: Object = manager.get_slot(1)
	_assert_eq_string("mutation_a", s0.get_active_mutation_id(),
		"dsm2_fill_first_slot_a — first fill goes to slot A")
	_assert_false(s1.is_filled(),
		"dsm2_fill_first_slot_b_empty — slot B remains empty after first fill")


func test_fill_second_goes_to_slot_b() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("fill_next_available"):
		_fail("dsm2_fill_second_slot_b", "manager or fill_next_available missing; skipping")
		return
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	var s0: Object = manager.get_slot(0)
	var s1: Object = manager.get_slot(1)
	_assert_eq_string("mutation_a", s0.get_active_mutation_id(),
		"dsm2_fill_second_slot_a_unchanged — slot A keeps mutation_a")
	_assert_eq_string("mutation_b", s1.get_active_mutation_id(),
		"dsm2_fill_second_slot_b_filled — slot B gets mutation_b")


func test_fill_both_full_overwrites_slot_b() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("fill_next_available"):
		_fail("dsm2_fill_overwrite_b", "manager or fill_next_available missing; skipping")
		return
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.fill_next_available("mutation_c")
	var s0: Object = manager.get_slot(0)
	var s1: Object = manager.get_slot(1)
	_assert_eq_string("mutation_a", s0.get_active_mutation_id(),
		"dsm2_overwrite_slot_a_unchanged — slot A is never overwritten by fill_next_available when full")
	_assert_eq_string("mutation_c", s1.get_active_mutation_id(),
		"dsm2_overwrite_slot_b — slot B is overwritten when both slots are full")


func test_fill_after_clear_slot_a_refills_slot_a() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("fill_next_available") or not manager.has_method("clear_slot"):
		_fail("dsm2_refill_slot_a", "manager API missing; skipping")
		return
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.clear_slot(0)
	manager.fill_next_available("mutation_new")
	var s0: Object = manager.get_slot(0)
	var s1: Object = manager.get_slot(1)
	_assert_eq_string("mutation_new", s0.get_active_mutation_id(),
		"dsm2_refill_slot_a — fill after clear_slot(0) fills slot A again (first-available)")
	_assert_eq_string("mutation_b", s1.get_active_mutation_id(),
		"dsm2_refill_slot_b_unchanged — slot B unchanged when slot A was refilled")


# ---------------------------------------------------------------------------
# DSM-3 — any_filled / speed-buff rule
# ---------------------------------------------------------------------------

func test_any_filled_false_when_empty() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("any_filled"):
		_fail("dsm3_any_filled_empty", "manager or any_filled missing; skipping")
		return
	_assert_false(manager.any_filled(), "dsm3_any_filled_false_empty — any_filled() is false on fresh manager")


func test_any_filled_true_when_slot_a_filled() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("any_filled") or not manager.has_method("fill_next_available"):
		_fail("dsm3_any_filled_slot_a", "manager API missing; skipping")
		return
	manager.fill_next_available("mutation_a")
	_assert_true(manager.any_filled(), "dsm3_any_filled_true_slot_a — any_filled() true when slot A filled")


func test_any_filled_true_when_slot_b_only_filled() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("any_filled") or not manager.has_method("fill_next_available") or not manager.has_method("clear_slot"):
		_fail("dsm3_any_filled_slot_b_only", "manager API missing; skipping")
		return
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.clear_slot(0)
	_assert_true(manager.any_filled(), "dsm3_any_filled_true_slot_b_only — any_filled() true when only slot B filled")


func test_any_filled_true_when_both_filled() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("any_filled") or not manager.has_method("fill_next_available"):
		_fail("dsm3_any_filled_both", "manager API missing; skipping")
		return
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	_assert_true(manager.any_filled(), "dsm3_any_filled_true_both — any_filled() true when both slots filled")


func test_any_filled_false_after_clear_all() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("any_filled") or not manager.has_method("fill_next_available") or not manager.has_method("clear_all"):
		_fail("dsm3_any_filled_after_clear_all", "manager API missing; skipping")
		return
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.clear_all()
	_assert_false(manager.any_filled(), "dsm3_any_filled_false_after_clear_all — any_filled() false after clear_all()")


func test_clear_all_empties_both_slots() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("fill_next_available") or not manager.has_method("clear_all"):
		_fail("dsm3_clear_all_empties", "manager API missing; skipping")
		return
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.clear_all()
	var s0: Object = manager.get_slot(0)
	var s1: Object = manager.get_slot(1)
	_assert_false(s0.is_filled(), "dsm3_clear_all_slot_a_empty — slot A empty after clear_all()")
	_assert_false(s1.is_filled(), "dsm3_clear_all_slot_b_empty — slot B empty after clear_all()")


# ---------------------------------------------------------------------------
# DSM-6 — InfectionAbsorbResolver dual-slot dispatch
# ---------------------------------------------------------------------------

func _make_infected_esm() -> Object:
	var esm: Object = _make_esm()
	if esm == null:
		return null
	esm.apply_weaken_event()
	esm.apply_infection_event()
	return esm


func test_resolver_with_manager_fills_next_available_slot() -> void:
	var resolver: Object = _make_resolver()
	var inv: Object = _make_inventory()
	var manager: Object = _make_manager()
	var esm: Object = _make_infected_esm()
	if resolver == null or inv == null or manager == null or esm == null:
		_fail("dsm6_resolver_manager", "dependencies missing; skipping")
		return
	resolver.resolve_absorb(esm, inv, manager)
	_assert_true(manager.any_filled(), "dsm6_resolver_fills_manager — resolve_absorb fills next slot in manager")
	_assert_eq_string(DEFAULT_MUTATION_ID, manager.get_slot(0).get_active_mutation_id(),
		"dsm6_resolver_fills_slot_a — first absorb goes to slot A via manager")


func test_resolver_second_absorb_fills_slot_b() -> void:
	var resolver: Object = _make_resolver()
	var inv: Object = _make_inventory()
	var manager: Object = _make_manager()
	if resolver == null or inv == null or manager == null:
		_fail("dsm6_resolver_fills_slot_b", "dependencies missing; skipping")
		return
	var esm1: Object = _make_infected_esm()
	var esm2: Object = _make_infected_esm()
	if esm1 == null or esm2 == null:
		_fail("dsm6_resolver_fills_slot_b", "esm missing; skipping")
		return
	resolver.resolve_absorb(esm1, inv, manager)
	resolver.resolve_absorb(esm2, inv, manager)
	_assert_eq_string(DEFAULT_MUTATION_ID, manager.get_slot(0).get_active_mutation_id(),
		"dsm6_second_absorb_slot_a_unchanged — slot A holds first absorb")
	_assert_eq_string(DEFAULT_MUTATION_ID, manager.get_slot(1).get_active_mutation_id(),
		"dsm6_second_absorb_slot_b_filled — slot B holds second absorb")


func test_resolver_null_slot_arg_still_kills_esm() -> void:
	var resolver: Object = _make_resolver()
	var inv: Object = _make_inventory()
	var esm: Object = _make_infected_esm()
	if resolver == null or inv == null or esm == null:
		_fail("dsm6_null_slot", "dependencies missing; skipping")
		return
	resolver.resolve_absorb(esm, inv, null)
	_assert_eq_string("dead", esm.get_state(), "dsm6_null_slot_kills_esm — ESM reaches dead state even with null slot arg")


func test_resolver_single_slot_arg_still_works() -> void:
	var resolver: Object = _make_resolver()
	var inv: Object = _make_inventory()
	var slot_script: GDScript = load("res://scripts/mutation/mutation_slot.gd") as GDScript
	var esm: Object = _make_infected_esm()
	if resolver == null or inv == null or slot_script == null or esm == null:
		_fail("dsm6_single_slot_backward_compat", "dependencies missing; skipping")
		return
	var single_slot: Object = slot_script.new()
	resolver.resolve_absorb(esm, inv, single_slot)
	_assert_true(single_slot.is_filled(), "dsm6_single_slot_filled — single-slot backward-compat: slot is filled after resolve_absorb")
	_assert_eq_string(DEFAULT_MUTATION_ID, single_slot.get_active_mutation_id(),
		"dsm6_single_slot_id — single-slot backward-compat: slot ID matches DEFAULT_MUTATION_ID")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_mutation_slot_system_dual.gd ---")
	_pass_count = 0
	_fail_count = 0

	# DSM-1 — MutationSlotManager API
	test_manager_script_loads_and_instantiates()
	test_manager_slot_count_is_two()
	test_manager_get_slot_0_and_1_non_null()
	test_manager_slots_have_required_api()
	test_manager_slots_are_independent_instances()
	test_manager_get_slot_out_of_range_returns_null()
	test_manager_clear_slot_oob_does_not_crash()

	# DSM-2 — Fill-order rule
	test_fill_first_goes_to_slot_a()
	test_fill_second_goes_to_slot_b()
	test_fill_both_full_overwrites_slot_b()
	test_fill_after_clear_slot_a_refills_slot_a()

	# DSM-3 — any_filled / speed-buff rule
	test_any_filled_false_when_empty()
	test_any_filled_true_when_slot_a_filled()
	test_any_filled_true_when_slot_b_only_filled()
	test_any_filled_true_when_both_filled()
	test_any_filled_false_after_clear_all()
	test_clear_all_empties_both_slots()

	# DSM-6 — InfectionAbsorbResolver dispatch
	test_resolver_with_manager_fills_next_available_slot()
	test_resolver_second_absorb_fills_slot_b()
	test_resolver_null_slot_arg_still_kills_esm()
	test_resolver_single_slot_arg_still_works()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
