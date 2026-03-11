#
# test_mutation_slot_system_dual.gd
#
# Primary behavioral tests for the dual-slot mutation system.
# Scope:
#   - DSM-1 — MutationSlotManager pure-logic class: instantiation, API surface,
#             slot independence, out-of-range safety.
#   - DSM-2 — Fill-order rule: first-available fill (slot A then B),
#             last-absorb-wins for slot B when both full, empty-string guard.
#   - DSM-3 — Speed-buff effect rule: any_filled() invariants.
#             NOTE: PlayerController3D wiring (scene-dependent) is intentionally
#             out of scope here; see checkpoint [two_mutation_slots] Test Designer
#             — DSM-3 speed-buff scene wiring in CHECKPOINTS.md. These tests
#             validate the any_filled() API contract that the controller depends on.
#
# Ticket: two_mutation_slots.md
# Spec:   two_mutation_slots_spec.md (DSM-1, DSM-2, DSM-3)
#
# All tests in this suite are expected to FAIL before MutationSlotManager is
# implemented (red phase of red-green-refactor).
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


func _assert_null(value: Object, test_name: String) -> void:
	if value == null:
		_pass(test_name)
	else:
		_fail(test_name, "expected null, got non-null object")


func _assert_not_null(value: Object, test_name: String) -> void:
	if value != null:
		_pass(test_name)
	else:
		_fail(test_name, "expected non-null object, got null")


func _load_manager_script() -> GDScript:
	return load("res://scripts/mutation_slot_manager.gd") as GDScript


func _make_manager() -> Object:
	var script: GDScript = _load_manager_script()
	if script == null:
		return null
	return script.new()


# ---------------------------------------------------------------------------
# DSM-1-AC-1  Script exists and is instantiable headlessly
# ---------------------------------------------------------------------------

func test_dsm1_script_exists_and_instantiates() -> void:
	var script: GDScript = _load_manager_script()
	if script == null:
		_fail(
			"dsm1_script_exists",
			"res://scripts/mutation_slot_manager.gd not found; implement MutationSlotManager per DSM-1"
		)
		return

	var instance: Object = script.new()
	if instance == null:
		_fail(
			"dsm1_instantiates",
			"MutationSlotManager script did not instantiate; expected pure-logic RefCounted"
		)
		return

	_pass("dsm1_script_exists_and_instantiates")


# ---------------------------------------------------------------------------
# DSM-1-AC-8  Manager is not a Node
# ---------------------------------------------------------------------------

func test_dsm1_manager_is_not_node() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail(
			"dsm1_not_node",
			"MutationSlotManager script missing or failed to instantiate; cannot verify not-Node"
		)
		return

	_assert_false(
		manager is Node,
		"dsm1_not_node — MutationSlotManager must not extend Node (must be RefCounted)"
	)


# ---------------------------------------------------------------------------
# DSM-1-AC-2  get_slot_count() returns 2
# ---------------------------------------------------------------------------

func test_dsm1_get_slot_count_returns_two() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_get_slot_count", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("get_slot_count"):
		_fail(
			"dsm1_get_slot_count_api_missing",
			"MutationSlotManager must implement get_slot_count() per DSM-1"
		)
		return

	_assert_eq_int(
		2,
		manager.get_slot_count(),
		"dsm1_get_slot_count_returns_two — get_slot_count() must return exactly 2"
	)


# ---------------------------------------------------------------------------
# DSM-1-AC-3  get_slot(0) returns valid slot object with required API
# ---------------------------------------------------------------------------

func test_dsm1_get_slot_0_returns_valid_object() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_get_slot_0", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("get_slot"):
		_fail("dsm1_get_slot_api_missing", "MutationSlotManager must implement get_slot(index) per DSM-1")
		return

	var slot: Object = manager.get_slot(0)

	if slot == null:
		_fail("dsm1_get_slot_0_not_null", "get_slot(0) returned null; expected a MutationSlot instance")
		return

	_assert_true(
		slot.has_method("is_filled"),
		"dsm1_get_slot_0_has_is_filled — slot 0 must have is_filled()"
	)
	_assert_true(
		slot.has_method("get_active_mutation_id"),
		"dsm1_get_slot_0_has_get_active_mutation_id — slot 0 must have get_active_mutation_id()"
	)
	_assert_true(
		slot.has_method("set_active_mutation_id"),
		"dsm1_get_slot_0_has_set_active_mutation_id — slot 0 must have set_active_mutation_id(id)"
	)
	_assert_true(
		slot.has_method("clear"),
		"dsm1_get_slot_0_has_clear — slot 0 must have clear()"
	)


# ---------------------------------------------------------------------------
# DSM-1-AC-4  get_slot(1) returns valid slot object with required API
# ---------------------------------------------------------------------------

func test_dsm1_get_slot_1_returns_valid_object() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_get_slot_1", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("get_slot"):
		_fail("dsm1_get_slot_api_missing", "MutationSlotManager must implement get_slot(index) per DSM-1")
		return

	var slot: Object = manager.get_slot(1)

	if slot == null:
		_fail("dsm1_get_slot_1_not_null", "get_slot(1) returned null; expected a MutationSlot instance")
		return

	_assert_true(
		slot.has_method("is_filled"),
		"dsm1_get_slot_1_has_is_filled — slot 1 must have is_filled()"
	)
	_assert_true(
		slot.has_method("get_active_mutation_id"),
		"dsm1_get_slot_1_has_get_active_mutation_id — slot 1 must have get_active_mutation_id()"
	)
	_assert_true(
		slot.has_method("set_active_mutation_id"),
		"dsm1_get_slot_1_has_set_active_mutation_id — slot 1 must have set_active_mutation_id(id)"
	)
	_assert_true(
		slot.has_method("clear"),
		"dsm1_get_slot_1_has_clear — slot 1 must have clear()"
	)


# ---------------------------------------------------------------------------
# DSM-1-AC-5  get_slot(0) and get_slot(1) are different object references
# ---------------------------------------------------------------------------

func test_dsm1_slots_are_independent_references() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_independent_refs", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("get_slot"):
		_fail("dsm1_independent_refs_api_missing", "MutationSlotManager must implement get_slot(index)")
		return

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("dsm1_independent_refs_slots_null", "get_slot(0) or get_slot(1) returned null; cannot verify independence")
		return

	_assert_true(
		slot_a != slot_b,
		"dsm1_slots_are_different_references — get_slot(0) and get_slot(1) must be different object instances"
	)


# ---------------------------------------------------------------------------
# DSM-1-AC-6  Out-of-range get_slot returns null without crashing
# ---------------------------------------------------------------------------

func test_dsm1_get_slot_out_of_range_returns_null() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_get_slot_oob", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("get_slot"):
		_fail("dsm1_get_slot_oob_api_missing", "MutationSlotManager must implement get_slot(index)")
		return

	# Negative index
	var slot_neg: Object = manager.get_slot(-1)
	_assert_null(
		slot_neg,
		"dsm1_get_slot_neg1_returns_null — get_slot(-1) must return null"
	)

	# Index 2 (one past the end)
	var slot_2: Object = manager.get_slot(2)
	_assert_null(
		slot_2,
		"dsm1_get_slot_2_returns_null — get_slot(2) must return null"
	)

	# Large out-of-range index
	var slot_99: Object = manager.get_slot(99)
	_assert_null(
		slot_99,
		"dsm1_get_slot_99_returns_null — get_slot(99) must return null"
	)


# ---------------------------------------------------------------------------
# DSM-1-AC-7  clear_slot with out-of-range index is a no-op (no crash)
# ---------------------------------------------------------------------------

func test_dsm1_clear_slot_out_of_range_is_no_op() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_clear_slot_oob", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("clear_slot"):
		_fail("dsm1_clear_slot_oob_api_missing", "MutationSlotManager must implement clear_slot(index) per DSM-1")
		return

	# These must not crash. If we reach the assertions after calling them, the test passes.
	manager.clear_slot(-1)
	manager.clear_slot(2)

	_pass("dsm1_clear_slot_oob_no_crash — clear_slot(-1) and clear_slot(2) did not crash")


# ---------------------------------------------------------------------------
# DSM-1-AC-9  Two manager instances do not share slot state
# ---------------------------------------------------------------------------

func test_dsm1_two_manager_instances_are_isolated() -> void:
	var manager_a: Object = _make_manager()
	var manager_b: Object = _make_manager()

	if manager_a == null or manager_b == null:
		_fail("dsm1_instance_isolation", "MutationSlotManager instances missing; skipping")
		return

	if not manager_a.has_method("fill_next_available") or not manager_b.has_method("any_filled"):
		_fail("dsm1_instance_isolation_api_missing", "MutationSlotManager must implement fill_next_available and any_filled")
		return

	# Fill one manager; the other must remain empty.
	manager_a.fill_next_available(DEFAULT_MUTATION_ID)

	_assert_true(
		manager_a.any_filled(),
		"dsm1_instance_isolation_a_filled — manager_a.any_filled() must be true after fill"
	)
	_assert_false(
		manager_b.any_filled(),
		"dsm1_instance_isolation_b_unaffected — filling manager_a must not affect manager_b"
	)


# ---------------------------------------------------------------------------
# DSM-1  Fresh manager: all slots are empty on construction
# ---------------------------------------------------------------------------

func test_dsm1_fresh_manager_slots_are_empty() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_fresh_slots_empty", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("get_slot"):
		_fail("dsm1_fresh_slots_empty_api_missing", "MutationSlotManager must implement get_slot(index)")
		return

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("dsm1_fresh_slots_null", "get_slot(0) or get_slot(1) returned null; cannot verify empty state")
		return

	_assert_false(
		slot_a.is_filled(),
		"dsm1_fresh_slot_a_not_filled — slot A must be empty on fresh manager"
	)
	_assert_false(
		slot_b.is_filled(),
		"dsm1_fresh_slot_b_not_filled — slot B must be empty on fresh manager"
	)
	_assert_eq_string(
		"",
		slot_a.get_active_mutation_id(),
		"dsm1_fresh_slot_a_empty_id — slot A active ID must be empty string on fresh manager"
	)
	_assert_eq_string(
		"",
		slot_b.get_active_mutation_id(),
		"dsm1_fresh_slot_b_empty_id — slot B active ID must be empty string on fresh manager"
	)


# ---------------------------------------------------------------------------
# DSM-2-AC-1  First fill goes to slot A; slot B remains empty
# ---------------------------------------------------------------------------

func test_dsm2_first_fill_goes_to_slot_a() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm2_first_fill_slot_a", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot"):
		_fail("dsm2_first_fill_slot_a_api_missing", "MutationSlotManager must implement fill_next_available and get_slot")
		return

	manager.fill_next_available("mutation_a")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("dsm2_first_fill_slots_null", "get_slot returned null; cannot verify fill result")
		return

	_assert_eq_string(
		"mutation_a",
		slot_a.get_active_mutation_id(),
		"dsm2_first_fill_slot_a_id — after first fill, slot A must hold 'mutation_a'"
	)
	_assert_false(
		slot_b.is_filled(),
		"dsm2_first_fill_slot_b_empty — after first fill, slot B must remain empty"
	)


# ---------------------------------------------------------------------------
# DSM-2-AC-2  Second fill goes to slot B; slot A is unchanged
# ---------------------------------------------------------------------------

func test_dsm2_second_fill_goes_to_slot_b() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm2_second_fill_slot_b", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot"):
		_fail("dsm2_second_fill_slot_b_api_missing", "MutationSlotManager must implement fill_next_available and get_slot")
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("dsm2_second_fill_slots_null", "get_slot returned null; cannot verify fill result")
		return

	_assert_eq_string(
		"mutation_a",
		slot_a.get_active_mutation_id(),
		"dsm2_second_fill_slot_a_unchanged — slot A must still hold 'mutation_a' after second fill"
	)
	_assert_eq_string(
		"mutation_b",
		slot_b.get_active_mutation_id(),
		"dsm2_second_fill_slot_b_id — slot B must hold 'mutation_b' after second fill"
	)


# ---------------------------------------------------------------------------
# DSM-2-AC-3  Third fill (both full) overwrites slot B; slot A unchanged
# ---------------------------------------------------------------------------

func test_dsm2_third_fill_overwrites_slot_b_not_slot_a() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm2_third_fill_overwrite_b", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot"):
		_fail("dsm2_third_fill_overwrite_b_api_missing", "MutationSlotManager must implement fill_next_available and get_slot")
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.fill_next_available("mutation_c")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("dsm2_third_fill_slots_null", "get_slot returned null; cannot verify overwrite result")
		return

	_assert_eq_string(
		"mutation_a",
		slot_a.get_active_mutation_id(),
		"dsm2_third_fill_slot_a_unchanged — slot A must remain 'mutation_a' when both slots were full (slot A is never overwritten by fill_next_available)"
	)
	_assert_eq_string(
		"mutation_c",
		slot_b.get_active_mutation_id(),
		"dsm2_third_fill_slot_b_overwritten — slot B must be overwritten with 'mutation_c' (last-absorb-wins)"
	)


# ---------------------------------------------------------------------------
# DSM-2-AC-4  Empty-string fill is rejected; both slots remain empty
# ---------------------------------------------------------------------------

func test_dsm2_empty_string_fill_is_rejected() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm2_empty_string_rejected", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("any_filled"):
		_fail("dsm2_empty_string_rejected_api_missing", "MutationSlotManager must implement fill_next_available and any_filled")
		return

	# fill_next_available("") must call push_error and return without modifying any slot.
	# We cannot directly assert that push_error was called (no mock), but we verify
	# that no slot state changed and no crash occurred.
	manager.fill_next_available("")

	_assert_false(
		manager.any_filled(),
		"dsm2_empty_string_rejected_no_fill — fill_next_available('') must not fill any slot"
	)

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("dsm2_empty_string_slots_null", "get_slot returned null; cannot verify state")
		return

	_assert_false(
		slot_a.is_filled(),
		"dsm2_empty_string_slot_a_still_empty — slot A must remain empty after empty-string fill"
	)
	_assert_false(
		slot_b.is_filled(),
		"dsm2_empty_string_slot_b_still_empty — slot B must remain empty after empty-string fill"
	)


# ---------------------------------------------------------------------------
# DSM-2-AC-5  fill_next_available after clear_slot(0) fills slot A again
# ---------------------------------------------------------------------------

func test_dsm2_fill_after_clear_slot_a_fills_slot_a() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm2_fill_after_clear_a", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot") or not manager.has_method("clear_slot"):
		_fail("dsm2_fill_after_clear_a_api_missing", "MutationSlotManager must implement fill_next_available, get_slot, clear_slot")
		return

	# Fill both slots first
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")

	# Clear slot A
	manager.clear_slot(0)

	# Now fill again: slot A is empty so it should be filled (not slot B)
	manager.fill_next_available("mutation_x")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("dsm2_fill_after_clear_a_slots_null", "get_slot returned null; cannot verify state")
		return

	_assert_eq_string(
		"mutation_x",
		slot_a.get_active_mutation_id(),
		"dsm2_fill_after_clear_a_slot_a_gets_new_id — after clearing slot A and filling again, slot A gets the new ID"
	)
	_assert_eq_string(
		"mutation_b",
		slot_b.get_active_mutation_id(),
		"dsm2_fill_after_clear_a_slot_b_unchanged — slot B must remain 'mutation_b' unchanged"
	)


# ---------------------------------------------------------------------------
# DSM-3-AC-6  any_filled() returns false on fresh manager
# ---------------------------------------------------------------------------

func test_dsm3_any_filled_false_on_fresh_manager() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm3_any_filled_fresh", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("any_filled"):
		_fail("dsm3_any_filled_api_missing", "MutationSlotManager must implement any_filled() per DSM-3")
		return

	_assert_false(
		manager.any_filled(),
		"dsm3_any_filled_false_on_fresh_manager — any_filled() must return false when both slots are empty"
	)


# ---------------------------------------------------------------------------
# DSM-3-AC-2  any_filled() true when only slot A is filled
# ---------------------------------------------------------------------------

func test_dsm3_any_filled_true_when_only_slot_a_filled() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm3_any_filled_slot_a_only", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("any_filled"):
		_fail("dsm3_any_filled_slot_a_only_api_missing", "MutationSlotManager must implement fill_next_available and any_filled")
		return

	manager.fill_next_available(DEFAULT_MUTATION_ID)

	_assert_true(
		manager.any_filled(),
		"dsm3_any_filled_true_slot_a_only — any_filled() must return true when slot A is filled and slot B is empty"
	)


# ---------------------------------------------------------------------------
# DSM-3-AC-3  any_filled() true when only slot B is filled
# ---------------------------------------------------------------------------

func test_dsm3_any_filled_true_when_only_slot_b_filled() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm3_any_filled_slot_b_only", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("get_slot") or not manager.has_method("any_filled"):
		_fail("dsm3_any_filled_slot_b_only_api_missing", "MutationSlotManager must implement get_slot and any_filled")
		return

	# Directly fill slot B via the underlying slot object so we can test the
	# case where only slot B is filled (fill_next_available fills A first).
	var slot_b: Object = manager.get_slot(1)
	if slot_b == null:
		_fail("dsm3_any_filled_slot_b_only_slot_null", "get_slot(1) returned null; cannot test slot B only case")
		return

	slot_b.set_active_mutation_id(DEFAULT_MUTATION_ID)

	_assert_true(
		manager.any_filled(),
		"dsm3_any_filled_true_slot_b_only — any_filled() must return true when only slot B is filled"
	)


# ---------------------------------------------------------------------------
# DSM-3-AC-4  any_filled() true when both slots are filled (no stacking)
# ---------------------------------------------------------------------------

func test_dsm3_any_filled_true_when_both_slots_filled() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm3_any_filled_both_filled", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("any_filled"):
		_fail("dsm3_any_filled_both_filled_api_missing", "MutationSlotManager must implement fill_next_available and any_filled")
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")

	_assert_true(
		manager.any_filled(),
		"dsm3_any_filled_true_both_filled — any_filled() must return true when both slots are filled"
	)


# ---------------------------------------------------------------------------
# DSM-3-AC-5  any_filled() returns false after clear_all()
# ---------------------------------------------------------------------------

func test_dsm3_any_filled_false_after_clear_all() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm3_any_filled_after_clear_all", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_all") or not manager.has_method("any_filled"):
		_fail("dsm3_any_filled_after_clear_all_api_missing", "MutationSlotManager must implement fill_next_available, clear_all, and any_filled")
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")

	_assert_true(
		manager.any_filled(),
		"dsm3_any_filled_true_before_clear — any_filled() must be true before clear_all()"
	)

	manager.clear_all()

	_assert_false(
		manager.any_filled(),
		"dsm3_any_filled_false_after_clear_all — any_filled() must return false after clear_all()"
	)


# ---------------------------------------------------------------------------
# DSM-1  clear_all() clears both slots
# ---------------------------------------------------------------------------

func test_dsm1_clear_all_clears_both_slots() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_clear_all_both_slots", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_all") or not manager.has_method("get_slot"):
		_fail("dsm1_clear_all_both_slots_api_missing", "MutationSlotManager must implement fill_next_available, clear_all, and get_slot")
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")

	manager.clear_all()

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("dsm1_clear_all_slots_null", "get_slot returned null; cannot verify clear state")
		return

	_assert_false(
		slot_a.is_filled(),
		"dsm1_clear_all_slot_a_empty — slot A must be empty after clear_all()"
	)
	_assert_false(
		slot_b.is_filled(),
		"dsm1_clear_all_slot_b_empty — slot B must be empty after clear_all()"
	)
	_assert_eq_string(
		"",
		slot_a.get_active_mutation_id(),
		"dsm1_clear_all_slot_a_id_empty — slot A active ID must be empty string after clear_all()"
	)
	_assert_eq_string(
		"",
		slot_b.get_active_mutation_id(),
		"dsm1_clear_all_slot_b_id_empty — slot B active ID must be empty string after clear_all()"
	)


# ---------------------------------------------------------------------------
# DSM-1  clear_slot(0) clears only slot A; slot B unaffected
# ---------------------------------------------------------------------------

func test_dsm1_clear_slot_0_only_clears_slot_a() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_clear_slot_0_only_a", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_slot") or not manager.has_method("get_slot"):
		_fail("dsm1_clear_slot_0_only_a_api_missing", "MutationSlotManager must implement fill_next_available, clear_slot, and get_slot")
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")

	manager.clear_slot(0)

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("dsm1_clear_slot_0_slots_null", "get_slot returned null; cannot verify state")
		return

	_assert_false(
		slot_a.is_filled(),
		"dsm1_clear_slot_0_slot_a_empty — slot A must be empty after clear_slot(0)"
	)
	_assert_true(
		slot_b.is_filled(),
		"dsm1_clear_slot_0_slot_b_unaffected — slot B must remain filled after clear_slot(0)"
	)
	_assert_eq_string(
		"mutation_b",
		slot_b.get_active_mutation_id(),
		"dsm1_clear_slot_0_slot_b_id_unchanged — slot B ID must remain 'mutation_b' after clear_slot(0)"
	)


# ---------------------------------------------------------------------------
# DSM-1  clear_slot(1) clears only slot B; slot A unaffected
# ---------------------------------------------------------------------------

func test_dsm1_clear_slot_1_only_clears_slot_b() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_clear_slot_1_only_b", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_slot") or not manager.has_method("get_slot"):
		_fail("dsm1_clear_slot_1_only_b_api_missing", "MutationSlotManager must implement fill_next_available, clear_slot, and get_slot")
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")

	manager.clear_slot(1)

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("dsm1_clear_slot_1_slots_null", "get_slot returned null; cannot verify state")
		return

	_assert_true(
		slot_a.is_filled(),
		"dsm1_clear_slot_1_slot_a_unaffected — slot A must remain filled after clear_slot(1)"
	)
	_assert_eq_string(
		"mutation_a",
		slot_a.get_active_mutation_id(),
		"dsm1_clear_slot_1_slot_a_id_unchanged — slot A ID must remain 'mutation_a' after clear_slot(1)"
	)
	_assert_false(
		slot_b.is_filled(),
		"dsm1_clear_slot_1_slot_b_empty — slot B must be empty after clear_slot(1)"
	)


# ---------------------------------------------------------------------------
# DSM-2  fill A, clear A, fill again goes back to slot A (not slot B)
# Round-trip: slot A recovers to be first-available after clear
# ---------------------------------------------------------------------------

func test_dsm2_fill_clear_a_fill_cycle() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm2_fill_clear_a_cycle", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_slot") or not manager.has_method("get_slot"):
		_fail("dsm2_fill_clear_a_cycle_api_missing", "MutationSlotManager must implement fill_next_available, clear_slot, and get_slot")
		return

	# Fill only slot A
	manager.fill_next_available("mutation_a")

	# Clear it
	manager.clear_slot(0)

	# Fill again: since A is empty, it must go to A again
	manager.fill_next_available("mutation_new")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("dsm2_fill_clear_a_cycle_slots_null", "get_slot returned null; cannot verify cycle state")
		return

	_assert_eq_string(
		"mutation_new",
		slot_a.get_active_mutation_id(),
		"dsm2_fill_clear_a_cycle_slot_a_refilled — slot A must receive 'mutation_new' after clear and refill"
	)
	_assert_false(
		slot_b.is_filled(),
		"dsm2_fill_clear_a_cycle_slot_b_empty — slot B must remain empty throughout single-fill cycle"
	)


# ---------------------------------------------------------------------------
# DSM-3  any_filled() returns false after clearing the only filled slot
# ---------------------------------------------------------------------------

func test_dsm3_any_filled_false_after_clearing_only_filled_slot() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm3_any_filled_after_clear_only", "MutationSlotManager instance missing; skipping")
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_slot") or not manager.has_method("any_filled"):
		_fail("dsm3_any_filled_after_clear_only_api_missing", "MutationSlotManager must implement fill_next_available, clear_slot, and any_filled")
		return

	manager.fill_next_available(DEFAULT_MUTATION_ID)

	_assert_true(
		manager.any_filled(),
		"dsm3_any_filled_true_before_single_clear — any_filled() true after one fill"
	)

	manager.clear_slot(0)

	_assert_false(
		manager.any_filled(),
		"dsm3_any_filled_false_after_single_slot_clear — any_filled() must return false after clearing the only filled slot"
	)


# ---------------------------------------------------------------------------
# DSM-1  Required public API methods exist on manager
# ---------------------------------------------------------------------------

func test_dsm1_manager_exposes_full_api() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("dsm1_full_api", "MutationSlotManager instance missing; skipping")
		return

	_assert_true(
		manager.has_method("get_slot"),
		"dsm1_api_get_slot — MutationSlotManager must expose get_slot(index)"
	)
	_assert_true(
		manager.has_method("fill_next_available"),
		"dsm1_api_fill_next_available — MutationSlotManager must expose fill_next_available(id)"
	)
	_assert_true(
		manager.has_method("get_slot_count"),
		"dsm1_api_get_slot_count — MutationSlotManager must expose get_slot_count()"
	)
	_assert_true(
		manager.has_method("any_filled"),
		"dsm1_api_any_filled — MutationSlotManager must expose any_filled()"
	)
	_assert_true(
		manager.has_method("clear_all"),
		"dsm1_api_clear_all — MutationSlotManager must expose clear_all()"
	)
	_assert_true(
		manager.has_method("clear_slot"),
		"dsm1_api_clear_slot — MutationSlotManager must expose clear_slot(index)"
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_mutation_slot_system_dual.gd ---")
	_pass_count = 0
	_fail_count = 0

	# DSM-1 — MutationSlotManager pure-logic class
	test_dsm1_script_exists_and_instantiates()
	test_dsm1_manager_is_not_node()
	test_dsm1_get_slot_count_returns_two()
	test_dsm1_get_slot_0_returns_valid_object()
	test_dsm1_get_slot_1_returns_valid_object()
	test_dsm1_slots_are_independent_references()
	test_dsm1_get_slot_out_of_range_returns_null()
	test_dsm1_clear_slot_out_of_range_is_no_op()
	test_dsm1_two_manager_instances_are_isolated()
	test_dsm1_fresh_manager_slots_are_empty()
	test_dsm1_clear_all_clears_both_slots()
	test_dsm1_clear_slot_0_only_clears_slot_a()
	test_dsm1_clear_slot_1_only_clears_slot_b()
	test_dsm1_manager_exposes_full_api()

	# DSM-2 — Fill-order rule
	test_dsm2_first_fill_goes_to_slot_a()
	test_dsm2_second_fill_goes_to_slot_b()
	test_dsm2_third_fill_overwrites_slot_b_not_slot_a()
	test_dsm2_empty_string_fill_is_rejected()
	test_dsm2_fill_after_clear_slot_a_fills_slot_a()
	test_dsm2_fill_clear_a_fill_cycle()

	# DSM-3 — Speed-buff any_filled() invariants
	test_dsm3_any_filled_false_on_fresh_manager()
	test_dsm3_any_filled_true_when_only_slot_a_filled()
	test_dsm3_any_filled_true_when_only_slot_b_filled()
	test_dsm3_any_filled_true_when_both_slots_filled()
	test_dsm3_any_filled_false_after_clear_all()
	test_dsm3_any_filled_false_after_clearing_only_filled_slot()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
