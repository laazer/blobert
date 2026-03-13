#
# test_mutation_slot_system_dual_adversarial.gd
#
# Adversarial test suite for the dual-slot mutation system (MutationSlotManager).
# Ticket: two_mutation_slots.md
# Spec:   two_mutation_slots_spec.md (DSM-1, DSM-2, DSM-3)
#
# Purpose: Expose coverage gaps, assumption blind spots, and edge-case failures
# that the primary behavioral suite (test_mutation_slot_system_dual.gd) does not
# cover. Every test here targets a concrete vulnerability category (see matrix).
#
# Vulnerability categories addressed:
#   - Null/empty/whitespace IDs passed to fill_next_available
#   - Simultaneous fill of both slots with identical mutation IDs
#   - Repeated overwrite of slot B (both-full path, many iterations)
#   - clear_all then immediate refill (ghost state)
#   - clear_slot with extreme/invalid indices (no crash, no-op)
#   - Two independent manager instances sharing no state (deep isolation)
#   - Rapid alternating fill/clear sequences
#   - any_filled(), get_slot(), get_slot_count() on freshly cleared manager
#   - get_slot identity stability (same object reference across repeated calls)
#   - get_slot_count invariance (always 2 regardless of fill/clear state)
#   - Clearing an already-empty slot (double-clear safety)
#   - Mutation IDs with special characters and very long strings
#   - Direct slot manipulation bypass (writing via get_slot() result)
#   - Mutation: flip fill-order assumption (slot A is never overwritten by
#     fill_next_available while both slots are full)
#   - CHECKPOINT decisions encoded as tests (see inline comments)
#
# All tests in this suite are expected to FAIL before MutationSlotManager is
# implemented (red phase of red-green-refactor).
#

class_name MutationSlotSystemDualAdversarialTests
extends Object


const DEFAULT_MUTATION_ID: String = "infection_mutation_01"

# A string that is not the empty string but contains only whitespace.
# The spec guards against id == "" but is silent on whitespace-only IDs.
# CHECKPOINT: whitespace IDs — see test_adv_whitespace_id_fill_rejected below.
const WHITESPACE_ID: String = "   "
const TAB_ID: String = "\t"
const NEWLINE_ID: String = "\n"

# Extreme index values for out-of-range testing.
const EXTREME_NEG_INDEX: int = -9999
const EXTREME_POS_INDEX: int = 9999

# A mutation ID with special characters to test ID pass-through integrity.
const SPECIAL_CHAR_ID: String = "infection:mutation/01?x=2&y=3"

# A very long mutation ID (300 characters) for boundary testing.
const LONG_ID: String = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


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


func _make_manager() -> Object:
	var script: GDScript = load("res://scripts/mutation/mutation_slot_manager.gd") as GDScript
	if script == null:
		return null
	return script.new()


func _skip_if_missing(manager: Object, test_name: String) -> bool:
	if manager == null:
		_fail(test_name, "MutationSlotManager script missing or failed to instantiate; skipping")
		return true
	return false


# ---------------------------------------------------------------------------
# NULL/EMPTY/WHITESPACE IDs — Vulnerability: invalid-input mutation
# ---------------------------------------------------------------------------

# Primary suite covers fill_next_available(""). These tests go further:
# null (if GDScript allows), whitespace, tab, newline.

# CHECKPOINT: The spec (DSM-2) only guards against id == "". Whitespace IDs
# (e.g. "   ", "\t", "\n") are not explicitly guarded. Conservative assumption:
# whitespace IDs are accepted as valid non-empty strings and ARE allowed to fill
# a slot, because the spec's only rejection criterion is the empty string "".
# The spec states push_error and return for id == "" specifically.
# This test encodes that assumption: whitespace IDs succeed in filling a slot.
# If the implementation rejects them, this test will catch the discrepancy.
# CHECKPOINT

func test_adv_whitespace_id_fills_slot_because_not_empty_string() -> void:
	# CHECKPOINT: whitespace ID — see class header for assumption detail
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_whitespace_id_behavior"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot"):
		_fail("adv_whitespace_id_behavior_api_missing", "MutationSlotManager must implement fill_next_available and get_slot")
		return

	# Whitespace is NOT the empty string; spec only rejects "".
	# Conservative assumption: whitespace IDs are accepted.
	manager.fill_next_available(WHITESPACE_ID)

	var slot_a: Object = manager.get_slot(0)
	if slot_a == null:
		_fail("adv_whitespace_id_slot_a_null", "get_slot(0) returned null; cannot verify fill result")
		return

	# Slot A should be filled (whitespace is a non-empty string)
	_assert_true(
		slot_a.is_filled(),
		"adv_whitespace_id_fills_slot_a — whitespace-only ID is not '' so must fill slot A per spec guard"
	)
	_assert_eq_string(
		WHITESPACE_ID,
		slot_a.get_active_mutation_id(),
		"adv_whitespace_id_stored_verbatim — whitespace ID must be stored as-is if accepted"
	)


func test_adv_tab_id_fills_slot() -> void:
	# CHECKPOINT: tab character ID — same conservative assumption as whitespace
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_tab_id_fills_slot"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("any_filled"):
		_fail("adv_tab_id_api_missing", "MutationSlotManager must implement fill_next_available and any_filled")
		return

	manager.fill_next_available(TAB_ID)

	# Tab is not ""; conservative assumption: fills slot A.
	_assert_true(
		manager.any_filled(),
		"adv_tab_id_fills_slot — tab ID is not '' so it should fill slot per spec guard logic"
	)


func test_adv_newline_id_fills_slot() -> void:
	# CHECKPOINT: newline character ID — same conservative assumption
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_newline_id_fills_slot"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("any_filled"):
		_fail("adv_newline_id_api_missing", "MutationSlotManager must implement fill_next_available and any_filled")
		return

	manager.fill_next_available(NEWLINE_ID)

	_assert_true(
		manager.any_filled(),
		"adv_newline_id_fills_slot — newline ID is not '' so it should fill slot per spec guard logic"
	)


func test_adv_empty_string_fill_on_full_manager_changes_nothing() -> void:
	# Both slots full, then empty-string fill — slot B must NOT be overwritten.
	# This is the intersection of the empty-string guard and the both-full path.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_empty_str_on_full_manager"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot"):
		_fail("adv_empty_str_on_full_api_missing", "MutationSlotManager must implement fill_next_available and get_slot")
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	# Both slots full. Now attempt empty-string fill.
	manager.fill_next_available("")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_empty_str_on_full_slots_null", "get_slot returned null")
		return

	_assert_eq_string(
		"mutation_a",
		slot_a.get_active_mutation_id(),
		"adv_empty_str_on_full_slot_a_unchanged — slot A must remain 'mutation_a' after empty-string fill on full manager"
	)
	_assert_eq_string(
		"mutation_b",
		slot_b.get_active_mutation_id(),
		"adv_empty_str_on_full_slot_b_unchanged — slot B must remain 'mutation_b' after empty-string fill on full manager"
	)


# ---------------------------------------------------------------------------
# SIMULTANEOUS FILL WITH IDENTICAL IDs — Vulnerability: aliasing/shared state
# ---------------------------------------------------------------------------

func test_adv_both_slots_filled_with_same_id_are_independent() -> void:
	# Fill both slots with the identical string. The slots must remain independent
	# objects; clearing one must not clear the other.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_identical_ids_independence"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot") or not manager.has_method("clear_slot"):
		_fail("adv_identical_ids_api_missing", "MutationSlotManager must implement fill_next_available, get_slot, clear_slot")
		return

	manager.fill_next_available(DEFAULT_MUTATION_ID)
	manager.fill_next_available(DEFAULT_MUTATION_ID)

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_identical_ids_slots_null", "get_slot returned null")
		return

	# Both slots must be filled with the same ID but be independent references.
	_assert_true(slot_a.is_filled(), "adv_identical_ids_slot_a_filled — slot A must be filled")
	_assert_true(slot_b.is_filled(), "adv_identical_ids_slot_b_filled — slot B must be filled")
	_assert_eq_string(DEFAULT_MUTATION_ID, slot_a.get_active_mutation_id(), "adv_identical_ids_slot_a_id — slot A holds correct ID")
	_assert_eq_string(DEFAULT_MUTATION_ID, slot_b.get_active_mutation_id(), "adv_identical_ids_slot_b_id — slot B holds correct ID")

	# Now clear slot A. Slot B must NOT be affected, even though they hold the same ID.
	manager.clear_slot(0)

	_assert_false(
		slot_a.is_filled(),
		"adv_identical_ids_clear_a_only_clears_a — clearing slot A must not affect slot B even when both hold same ID"
	)
	_assert_true(
		slot_b.is_filled(),
		"adv_identical_ids_slot_b_still_filled_after_a_clear — slot B must remain filled after clear_slot(0)"
	)


func test_adv_get_slot_0_and_1_return_distinct_objects_with_same_id() -> void:
	# Verify get_slot(0) != get_slot(1) as object references even when both hold
	# identical ID strings — ensures no aliasing was introduced during fill.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_same_id_distinct_refs"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot"):
		_fail("adv_same_id_distinct_refs_api_missing", "MutationSlotManager must implement fill_next_available and get_slot")
		return

	manager.fill_next_available("dup_id")
	manager.fill_next_available("dup_id")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_same_id_distinct_refs_slots_null", "get_slot returned null")
		return

	_assert_true(
		slot_a != slot_b,
		"adv_same_id_distinct_refs — even with identical IDs, get_slot(0) and get_slot(1) must be different object instances"
	)


# ---------------------------------------------------------------------------
# REPEATED FILL OF SLOT B (both-full overwrite-B many times)
# Vulnerability: mutation — confirm slot A is NEVER overwritten
# ---------------------------------------------------------------------------

func test_adv_repeated_overwrite_slot_b_slot_a_never_changes() -> void:
	# Fill slot A once, then overwrite slot B ten times (both-full path).
	# Slot A must hold the original ID throughout all ten overwrites.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_repeated_overwrite_slot_b"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot"):
		_fail("adv_repeated_overwrite_slot_b_api_missing", "MutationSlotManager must implement fill_next_available and get_slot")
		return

	manager.fill_next_available("slot_a_original")
	manager.fill_next_available("slot_b_first")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_repeated_overwrite_slots_null", "get_slot returned null")
		return

	# Overwrite slot B ten times; slot A must remain "slot_a_original" every iteration.
	var i: int = 0
	while i < 10:
		var overwrite_id: String = "overwrite_" + str(i)
		manager.fill_next_available(overwrite_id)
		if slot_a.get_active_mutation_id() != "slot_a_original":
			_fail(
				"adv_repeated_overwrite_slot_b_slot_a_mutated_at_iter_" + str(i),
				"slot A changed to '" + slot_a.get_active_mutation_id() + "' during overwrite iteration " + str(i) + "; slot A must never be overwritten by fill_next_available when full"
			)
			return
		i += 1

	_pass("adv_repeated_overwrite_slot_b_slot_a_never_changes — slot A held 'slot_a_original' across 10 slot-B overwrites")

	# Verify final slot B holds the last overwrite ID.
	_assert_eq_string(
		"overwrite_9",
		slot_b.get_active_mutation_id(),
		"adv_repeated_overwrite_slot_b_final_id — slot B must hold the last overwrite ID 'overwrite_9'"
	)


func test_adv_overwrite_slot_b_any_filled_remains_true() -> void:
	# After every overwrite of slot B while both slots are full, any_filled() must
	# remain true (no implementation bug that transiently clears during overwrite).
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_overwrite_slot_b_any_filled_stable"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("any_filled"):
		_fail("adv_overwrite_slot_b_any_filled_stable_api_missing", "MutationSlotManager must implement fill_next_available and any_filled")
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")

	var j: int = 0
	while j < 5:
		manager.fill_next_available("overwrite_" + str(j))
		if not manager.any_filled():
			_fail(
				"adv_overwrite_slot_b_any_filled_false_at_iter_" + str(j),
				"any_filled() returned false after overwrite at iteration " + str(j) + "; must remain true while slots are occupied"
			)
			return
		j += 1

	_pass("adv_overwrite_slot_b_any_filled_stable — any_filled() remained true across 5 slot-B overwrites")


# ---------------------------------------------------------------------------
# clear_all THEN IMMEDIATE REFILL — Vulnerability: ghost state
# ---------------------------------------------------------------------------

func test_adv_clear_all_then_refill_no_ghost_state() -> void:
	# Fill both slots, clear_all, then refill. The IDs from the first fill must
	# not resurface — only the new IDs should be present.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_clear_all_refill_no_ghost"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_all") or not manager.has_method("get_slot"):
		_fail("adv_clear_all_refill_no_ghost_api_missing", "MutationSlotManager must implement fill_next_available, clear_all, get_slot")
		return

	manager.fill_next_available("ghost_a")
	manager.fill_next_available("ghost_b")
	manager.clear_all()

	# Immediately refill with different IDs.
	manager.fill_next_available("fresh_a")
	manager.fill_next_available("fresh_b")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_clear_all_refill_slots_null", "get_slot returned null")
		return

	_assert_eq_string(
		"fresh_a",
		slot_a.get_active_mutation_id(),
		"adv_clear_all_refill_slot_a_no_ghost — slot A must hold 'fresh_a', not ghost ID 'ghost_a'"
	)
	_assert_eq_string(
		"fresh_b",
		slot_b.get_active_mutation_id(),
		"adv_clear_all_refill_slot_b_no_ghost — slot B must hold 'fresh_b', not ghost ID 'ghost_b'"
	)


func test_adv_clear_all_refill_cycle_repeated() -> void:
	# Repeat clear_all + refill 5 times. No ghost state, no ID accumulation.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_clear_all_refill_cycle_repeated"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_all") or not manager.has_method("get_slot") or not manager.has_method("any_filled"):
		_fail("adv_clear_all_refill_cycle_api_missing", "MutationSlotManager must implement fill_next_available, clear_all, get_slot, any_filled")
		return

	var cycle: int = 0
	while cycle < 5:
		manager.fill_next_available("cycle_a_" + str(cycle))
		manager.fill_next_available("cycle_b_" + str(cycle))
		manager.clear_all()

		if manager.any_filled():
			_fail(
				"adv_clear_all_cycle_" + str(cycle) + "_any_filled_not_false",
				"any_filled() was true immediately after clear_all() at cycle " + str(cycle)
			)
			return

		var slot_a: Object = manager.get_slot(0)
		var slot_b: Object = manager.get_slot(1)

		if slot_a == null or slot_b == null:
			_fail("adv_clear_all_cycle_" + str(cycle) + "_slots_null", "get_slot returned null at cycle " + str(cycle))
			return

		if slot_a.get_active_mutation_id() != "" or slot_b.get_active_mutation_id() != "":
			_fail(
				"adv_clear_all_cycle_" + str(cycle) + "_ghost_id",
				"ghost ID found after clear_all at cycle " + str(cycle) + ": A='" + slot_a.get_active_mutation_id() + "' B='" + slot_b.get_active_mutation_id() + "'"
			)
			return

		cycle += 1

	_pass("adv_clear_all_refill_cycle_repeated — 5 fill+clear_all cycles produced no ghost state")


func test_adv_clear_all_then_single_fill_goes_to_slot_a() -> void:
	# After clear_all on a full manager, the very first refill must go to slot A
	# (first-available rule resets correctly after clear).
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_clear_all_single_refill_to_a"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_all") or not manager.has_method("get_slot"):
		_fail("adv_clear_all_single_refill_to_a_api_missing", "MutationSlotManager must implement fill_next_available, clear_all, get_slot")
		return

	manager.fill_next_available("old_a")
	manager.fill_next_available("old_b")
	manager.clear_all()
	manager.fill_next_available("new_a")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_clear_all_single_refill_slots_null", "get_slot returned null")
		return

	_assert_eq_string(
		"new_a",
		slot_a.get_active_mutation_id(),
		"adv_clear_all_single_refill_to_slot_a — first fill after clear_all goes to slot A"
	)
	_assert_false(
		slot_b.is_filled(),
		"adv_clear_all_single_refill_slot_b_empty — slot B must remain empty after single fill post-clear_all"
	)


# ---------------------------------------------------------------------------
# clear_slot WITH INVALID INDICES — Vulnerability: crash, no-op guarantee
# ---------------------------------------------------------------------------

func test_adv_clear_slot_extreme_negative_index() -> void:
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_clear_slot_extreme_neg"):
		return

	if not manager.has_method("clear_slot"):
		_fail("adv_clear_slot_extreme_neg_api_missing", "MutationSlotManager must implement clear_slot")
		return

	# Must not crash.
	manager.clear_slot(EXTREME_NEG_INDEX)
	_pass("adv_clear_slot_extreme_neg_no_crash — clear_slot(" + str(EXTREME_NEG_INDEX) + ") did not crash")


func test_adv_clear_slot_extreme_positive_index() -> void:
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_clear_slot_extreme_pos"):
		return

	if not manager.has_method("clear_slot"):
		_fail("adv_clear_slot_extreme_pos_api_missing", "MutationSlotManager must implement clear_slot")
		return

	# Must not crash.
	manager.clear_slot(EXTREME_POS_INDEX)
	_pass("adv_clear_slot_extreme_pos_no_crash — clear_slot(" + str(EXTREME_POS_INDEX) + ") did not crash")


func test_adv_clear_slot_invalid_leaves_valid_slots_intact() -> void:
	# Invalid index clear must not corrupt the valid slots.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_clear_slot_invalid_leaves_valid_intact"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_slot") or not manager.has_method("get_slot"):
		_fail("adv_clear_slot_invalid_intact_api_missing", "MutationSlotManager must implement fill_next_available, clear_slot, get_slot")
		return

	manager.fill_next_available("safe_a")
	manager.fill_next_available("safe_b")

	# Attempt invalid clear operations.
	manager.clear_slot(EXTREME_NEG_INDEX)
	manager.clear_slot(EXTREME_POS_INDEX)
	manager.clear_slot(2)
	manager.clear_slot(-1)

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_clear_slot_invalid_intact_slots_null", "get_slot returned null")
		return

	_assert_eq_string(
		"safe_a",
		slot_a.get_active_mutation_id(),
		"adv_clear_slot_invalid_slot_a_intact — slot A must survive invalid clear_slot calls"
	)
	_assert_eq_string(
		"safe_b",
		slot_b.get_active_mutation_id(),
		"adv_clear_slot_invalid_slot_b_intact — slot B must survive invalid clear_slot calls"
	)


func test_adv_clear_slot_on_empty_slot_is_safe() -> void:
	# clear_slot(0) on an already-empty slot must be idempotent and crash-free.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_clear_slot_empty_is_safe"):
		return

	if not manager.has_method("clear_slot") or not manager.has_method("get_slot"):
		_fail("adv_clear_slot_empty_safe_api_missing", "MutationSlotManager must implement clear_slot and get_slot")
		return

	# Double-clear slot A (fresh manager, slot A starts empty).
	manager.clear_slot(0)
	manager.clear_slot(0)
	manager.clear_slot(1)
	manager.clear_slot(1)

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_clear_slot_empty_slots_null", "get_slot returned null after double-clear")
		return

	_assert_false(slot_a.is_filled(), "adv_double_clear_slot_a_empty — slot A remains empty after double-clear")
	_assert_false(slot_b.is_filled(), "adv_double_clear_slot_b_empty — slot B remains empty after double-clear")


func test_adv_clear_all_on_empty_manager_is_safe() -> void:
	# clear_all() on an already-empty manager must not crash.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_clear_all_empty_safe"):
		return

	if not manager.has_method("clear_all") or not manager.has_method("any_filled"):
		_fail("adv_clear_all_empty_safe_api_missing", "MutationSlotManager must implement clear_all and any_filled")
		return

	manager.clear_all()
	manager.clear_all()  # Second call: idempotent, must not crash.

	_assert_false(manager.any_filled(), "adv_clear_all_empty_safe — any_filled() false after clear_all on empty manager")
	_pass("adv_clear_all_empty_safe_no_crash — two clear_all() calls on empty manager did not crash")


# ---------------------------------------------------------------------------
# TWO INDEPENDENT MANAGER INSTANCES — Vulnerability: shared/static state
# ---------------------------------------------------------------------------

func test_adv_two_instances_deep_isolation_fill_and_clear() -> void:
	# Manager A fills both slots with unique IDs; manager B must remain fully empty.
	# Then manager B fills its slots; manager A's slots must be unaffected.
	var manager_a: Object = _make_manager()
	var manager_b: Object = _make_manager()

	if manager_a == null or manager_b == null:
		_fail("adv_deep_isolation_fill_clear", "MutationSlotManager instances missing; skipping")
		return

	if not manager_a.has_method("fill_next_available") or not manager_a.has_method("get_slot") or not manager_a.has_method("any_filled"):
		_fail("adv_deep_isolation_fill_clear_api_missing", "MutationSlotManager must implement fill_next_available, get_slot, any_filled")
		return

	# Fill manager A completely.
	manager_a.fill_next_available("a_slot0")
	manager_a.fill_next_available("a_slot1")

	# Manager B must remain empty.
	_assert_false(
		manager_b.any_filled(),
		"adv_deep_isolation_b_empty_after_a_fill — filling manager_a must not affect manager_b"
	)

	var b_slot_a: Object = manager_b.get_slot(0)
	var b_slot_b: Object = manager_b.get_slot(1)

	if b_slot_a == null or b_slot_b == null:
		_fail("adv_deep_isolation_b_slots_null", "manager_b get_slot returned null")
		return

	_assert_eq_string("", b_slot_a.get_active_mutation_id(), "adv_deep_isolation_b_slot0_empty — manager_b slot 0 must be empty")
	_assert_eq_string("", b_slot_b.get_active_mutation_id(), "adv_deep_isolation_b_slot1_empty — manager_b slot 1 must be empty")

	# Now fill manager B.
	manager_b.fill_next_available("b_slot0")
	manager_b.fill_next_available("b_slot1")

	# Manager A's slots must be unaffected.
	var a_slot_a: Object = manager_a.get_slot(0)
	var a_slot_b: Object = manager_a.get_slot(1)

	if a_slot_a == null or a_slot_b == null:
		_fail("adv_deep_isolation_a_slots_null", "manager_a get_slot returned null")
		return

	_assert_eq_string(
		"a_slot0",
		a_slot_a.get_active_mutation_id(),
		"adv_deep_isolation_a_slot0_unchanged_after_b_fill — manager_a slot 0 must remain 'a_slot0'"
	)
	_assert_eq_string(
		"a_slot1",
		a_slot_b.get_active_mutation_id(),
		"adv_deep_isolation_a_slot1_unchanged_after_b_fill — manager_a slot 1 must remain 'a_slot1'"
	)


func test_adv_two_instances_clear_all_does_not_affect_other() -> void:
	# clear_all() on manager A must not clear manager B's slots.
	var manager_a: Object = _make_manager()
	var manager_b: Object = _make_manager()

	if manager_a == null or manager_b == null:
		_fail("adv_clear_all_isolation", "MutationSlotManager instances missing; skipping")
		return

	if not manager_a.has_method("fill_next_available") or not manager_a.has_method("clear_all") or not manager_b.has_method("any_filled"):
		_fail("adv_clear_all_isolation_api_missing", "MutationSlotManager must implement fill_next_available, clear_all, any_filled")
		return

	manager_a.fill_next_available("shared_id")
	manager_b.fill_next_available("shared_id")

	manager_a.clear_all()

	_assert_false(
		manager_a.any_filled(),
		"adv_clear_all_isolation_a_cleared — manager_a must be empty after clear_all"
	)
	_assert_true(
		manager_b.any_filled(),
		"adv_clear_all_isolation_b_unaffected — manager_b must remain filled after manager_a.clear_all()"
	)


# ---------------------------------------------------------------------------
# RAPID ALTERNATING FILL/CLEAR SEQUENCES — Vulnerability: order dependency
# ---------------------------------------------------------------------------

func test_adv_rapid_alternating_fill_clear_slot_a() -> void:
	# Fill slot A, clear slot A, fill slot A — repeat 10 times.
	# Final state: slot A filled with last ID, slot B empty throughout.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_rapid_fill_clear_slot_a"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_slot") or not manager.has_method("get_slot"):
		_fail("adv_rapid_fill_clear_slot_a_api_missing", "MutationSlotManager must implement fill_next_available, clear_slot, get_slot")
		return

	var k: int = 0
	while k < 10:
		manager.fill_next_available("id_" + str(k))
		manager.clear_slot(0)
		k += 1

	# After all cycles: fill one more time to leave a known final state.
	manager.fill_next_available("final_id")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_rapid_fill_clear_slots_null", "get_slot returned null")
		return

	_assert_eq_string(
		"final_id",
		slot_a.get_active_mutation_id(),
		"adv_rapid_fill_clear_slot_a_final_id — slot A must hold 'final_id' after 10 fill/clear cycles"
	)
	_assert_false(
		slot_b.is_filled(),
		"adv_rapid_fill_clear_slot_b_always_empty — slot B must remain empty throughout rapid fill/clear of slot A"
	)


func test_adv_rapid_fill_clear_both_slots() -> void:
	# Fill both slots, clear both individually, repeat 5 times.
	# After each clear-both cycle, any_filled() must be false.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_rapid_fill_clear_both"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_slot") or not manager.has_method("any_filled"):
		_fail("adv_rapid_fill_clear_both_api_missing", "MutationSlotManager must implement fill_next_available, clear_slot, any_filled")
		return

	var m: int = 0
	while m < 5:
		manager.fill_next_available("id_a_" + str(m))
		manager.fill_next_available("id_b_" + str(m))
		manager.clear_slot(0)
		manager.clear_slot(1)

		if manager.any_filled():
			_fail(
				"adv_rapid_fill_clear_both_cycle_" + str(m),
				"any_filled() true after clearing both slots at cycle " + str(m)
			)
			return
		m += 1

	_pass("adv_rapid_fill_clear_both — any_filled() was false after each of 5 fill+clear-both cycles")


func test_adv_fill_a_clear_all_fill_next_goes_to_a_not_b() -> void:
	# fill slot A, clear_all, fill again: must go to slot A (not skip to B).
	# Distinct from the primary suite's test_dsm2_fill_clear_a_fill_cycle which uses
	# clear_slot(0); this uses clear_all to ensure clear_all truly resets both slots.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_fill_clear_all_next_to_a"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_all") or not manager.has_method("get_slot"):
		_fail("adv_fill_clear_all_next_to_a_api_missing", "MutationSlotManager must implement fill_next_available, clear_all, get_slot")
		return

	manager.fill_next_available("original_a")
	manager.clear_all()
	manager.fill_next_available("refilled")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_fill_clear_all_next_slots_null", "get_slot returned null")
		return

	_assert_eq_string(
		"refilled",
		slot_a.get_active_mutation_id(),
		"adv_fill_clear_all_next_to_slot_a — first fill after clear_all goes to slot A"
	)
	_assert_false(
		slot_b.is_filled(),
		"adv_fill_clear_all_slot_b_empty — slot B stays empty when only one fill after clear_all"
	)


# ---------------------------------------------------------------------------
# QUERYING ON FRESHLY CLEARED MANAGER — any_filled, get_slot, get_slot_count
# ---------------------------------------------------------------------------

func test_adv_any_filled_false_after_clear_slot_0_of_only_filled_slot() -> void:
	# Fill only slot B directly, then clear slot B via clear_slot(1).
	# any_filled() must then return false.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_any_filled_after_clear_only_b"):
		return

	if not manager.has_method("get_slot") or not manager.has_method("clear_slot") or not manager.has_method("any_filled"):
		_fail("adv_any_filled_after_clear_only_b_api_missing", "MutationSlotManager must implement get_slot, clear_slot, any_filled")
		return

	# Fill slot B directly (bypassing fill_next_available to isolate slot B only).
	var slot_b: Object = manager.get_slot(1)
	if slot_b == null:
		_fail("adv_any_filled_after_clear_only_b_slot_null", "get_slot(1) returned null")
		return

	slot_b.set_active_mutation_id(DEFAULT_MUTATION_ID)

	_assert_true(
		manager.any_filled(),
		"adv_any_filled_true_only_b_directly_filled — any_filled() must be true when slot B is filled directly"
	)

	manager.clear_slot(1)

	_assert_false(
		manager.any_filled(),
		"adv_any_filled_false_after_clear_only_b — any_filled() must be false after clearing the only filled slot (B)"
	)


func test_adv_get_slot_count_invariant_across_fill_and_clear() -> void:
	# get_slot_count() must always return 2 regardless of fill/clear state.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_get_slot_count_invariant"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_all") or not manager.has_method("get_slot_count"):
		_fail("adv_get_slot_count_invariant_api_missing", "MutationSlotManager must implement fill_next_available, clear_all, get_slot_count")
		return

	# Fresh manager.
	_assert_eq_int(2, manager.get_slot_count(), "adv_slot_count_fresh — get_slot_count() returns 2 on fresh manager")

	# After filling slot A.
	manager.fill_next_available("a")
	_assert_eq_int(2, manager.get_slot_count(), "adv_slot_count_after_fill_a — get_slot_count() returns 2 after filling slot A")

	# After filling slot B.
	manager.fill_next_available("b")
	_assert_eq_int(2, manager.get_slot_count(), "adv_slot_count_after_fill_b — get_slot_count() returns 2 after filling slot B")

	# After clear_all.
	manager.clear_all()
	_assert_eq_int(2, manager.get_slot_count(), "adv_slot_count_after_clear_all — get_slot_count() returns 2 after clear_all")


func test_adv_get_slot_returns_same_object_on_repeated_calls() -> void:
	# get_slot(0) called twice must return the same object reference (identity
	# stability). A new instance must not be created on every call.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_get_slot_identity_stable"):
		return

	if not manager.has_method("get_slot"):
		_fail("adv_get_slot_identity_stable_api_missing", "MutationSlotManager must implement get_slot")
		return

	var slot_a_first: Object = manager.get_slot(0)
	var slot_a_second: Object = manager.get_slot(0)
	var slot_b_first: Object = manager.get_slot(1)
	var slot_b_second: Object = manager.get_slot(1)

	if slot_a_first == null or slot_a_second == null or slot_b_first == null or slot_b_second == null:
		_fail("adv_get_slot_identity_stable_slots_null", "get_slot returned null; cannot verify identity")
		return

	_assert_true(
		slot_a_first == slot_a_second,
		"adv_get_slot_0_identity_stable — get_slot(0) must return the same object reference on each call"
	)
	_assert_true(
		slot_b_first == slot_b_second,
		"adv_get_slot_1_identity_stable — get_slot(1) must return the same object reference on each call"
	)


func test_adv_get_slot_out_of_range_exhaustive() -> void:
	# Exhaustively test all commonly dangerous out-of-range index values beyond
	# what the primary suite covers (primary covers -1, 2, 99).
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_get_slot_oob_exhaustive"):
		return

	if not manager.has_method("get_slot"):
		_fail("adv_get_slot_oob_exhaustive_api_missing", "MutationSlotManager must implement get_slot")
		return

	var dangerous_indices: Array = [-9999, -2, -1, 2, 3, 100, 9999]
	for idx in dangerous_indices:
		var result: Object = manager.get_slot(idx)
		if result != null:
			_fail(
				"adv_get_slot_oob_" + str(idx) + "_not_null",
				"get_slot(" + str(idx) + ") returned non-null; must return null for out-of-range indices"
			)
			return

	_pass("adv_get_slot_oob_exhaustive — all dangerous indices returned null without crashing")


# ---------------------------------------------------------------------------
# SPECIAL CHARACTER AND LONG ID STRINGS — Vulnerability: string boundary
# ---------------------------------------------------------------------------

func test_adv_special_character_id_stored_verbatim() -> void:
	# IDs with special characters must be stored and retrieved exactly.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_special_char_id"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot"):
		_fail("adv_special_char_id_api_missing", "MutationSlotManager must implement fill_next_available and get_slot")
		return

	manager.fill_next_available(SPECIAL_CHAR_ID)

	var slot_a: Object = manager.get_slot(0)
	if slot_a == null:
		_fail("adv_special_char_id_slot_null", "get_slot(0) returned null")
		return

	_assert_eq_string(
		SPECIAL_CHAR_ID,
		slot_a.get_active_mutation_id(),
		"adv_special_char_id_stored_verbatim — special character ID must be stored and retrieved without modification"
	)


func test_adv_very_long_id_stored_verbatim() -> void:
	# Very long ID strings must be stored and retrieved exactly.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_long_id"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot"):
		_fail("adv_long_id_api_missing", "MutationSlotManager must implement fill_next_available and get_slot")
		return

	manager.fill_next_available(LONG_ID)

	var slot_a: Object = manager.get_slot(0)
	if slot_a == null:
		_fail("adv_long_id_slot_null", "get_slot(0) returned null")
		return

	_assert_eq_string(
		LONG_ID,
		slot_a.get_active_mutation_id(),
		"adv_long_id_stored_verbatim — very long ID (300 chars) must be stored and retrieved without truncation"
	)


# ---------------------------------------------------------------------------
# DIRECT SLOT MANIPULATION BYPASS — fill via get_slot() result directly
# Vulnerability: assumption that any_filled() reads live slot state
# ---------------------------------------------------------------------------

func test_adv_any_filled_reflects_direct_set_on_slot_a() -> void:
	# Set slot A's ID directly (bypassing fill_next_available); any_filled() must
	# reflect the live state of both slots, not a cached value.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_any_filled_live_state"):
		return

	if not manager.has_method("get_slot") or not manager.has_method("any_filled"):
		_fail("adv_any_filled_live_state_api_missing", "MutationSlotManager must implement get_slot and any_filled")
		return

	var slot_a: Object = manager.get_slot(0)
	if slot_a == null:
		_fail("adv_any_filled_live_state_slot_null", "get_slot(0) returned null")
		return

	_assert_false(manager.any_filled(), "adv_any_filled_false_before_direct_set — any_filled() false before direct set")

	# Write directly to the slot object.
	slot_a.set_active_mutation_id("directly_set")

	_assert_true(
		manager.any_filled(),
		"adv_any_filled_true_after_direct_set — any_filled() must reflect direct set_active_mutation_id on slot A"
	)

	# Now clear directly on the slot.
	slot_a.clear()

	_assert_false(
		manager.any_filled(),
		"adv_any_filled_false_after_direct_clear — any_filled() must reflect direct clear() on slot A"
	)


func test_adv_any_filled_reflects_direct_set_on_slot_b() -> void:
	# Same as above but for slot B — ensures any_filled() polls both slots.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_any_filled_live_state_slot_b"):
		return

	if not manager.has_method("get_slot") or not manager.has_method("any_filled"):
		_fail("adv_any_filled_live_state_slot_b_api_missing", "MutationSlotManager must implement get_slot and any_filled")
		return

	var slot_b: Object = manager.get_slot(1)
	if slot_b == null:
		_fail("adv_any_filled_live_state_slot_b_null", "get_slot(1) returned null")
		return

	slot_b.set_active_mutation_id("directly_set_b")

	_assert_true(
		manager.any_filled(),
		"adv_any_filled_true_after_direct_set_b — any_filled() must reflect direct set_active_mutation_id on slot B"
	)


# ---------------------------------------------------------------------------
# MUTATION TEST: fill_next_available fill-order rule robustness
# Verify spec invariant: slot A is NEVER targeted when slot B is empty+A is full
# ---------------------------------------------------------------------------

func test_adv_fill_order_slot_a_full_slot_b_empty_goes_to_b_not_a() -> void:
	# This tests a subtle mutation: an implementation might incorrectly target slot A
	# again (e.g. off-by-one, wrong condition) when slot A is filled and slot B is empty.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_fill_order_a_full_b_empty"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot"):
		_fail("adv_fill_order_a_full_b_empty_api_missing", "MutationSlotManager must implement fill_next_available and get_slot")
		return

	manager.fill_next_available("first_fill")
	# Slot A now filled. Slot B empty. Second fill must go to B.
	manager.fill_next_available("second_fill")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_fill_order_a_full_b_empty_slots_null", "get_slot returned null")
		return

	_assert_eq_string(
		"first_fill",
		slot_a.get_active_mutation_id(),
		"adv_fill_order_slot_a_not_overwritten — slot A must not be overwritten when slot B is empty"
	)
	_assert_eq_string(
		"second_fill",
		slot_b.get_active_mutation_id(),
		"adv_fill_order_slot_b_receives_second_fill — slot B must receive the second fill when slot A is full and slot B is empty"
	)


func test_adv_fill_order_clear_b_then_fill_goes_to_b_not_overwrite_a() -> void:
	# Fill both slots, clear slot B, fill again. Must go to B (empty) not overwrite A.
	# This is the symmetric counterpart to test_dsm2_fill_after_clear_slot_a_fills_slot_a
	# in the primary suite.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_fill_order_clear_b_refill_to_b"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_slot") or not manager.has_method("get_slot"):
		_fail("adv_fill_order_clear_b_refill_api_missing", "MutationSlotManager must implement fill_next_available, clear_slot, get_slot")
		return

	manager.fill_next_available("orig_a")
	manager.fill_next_available("orig_b")
	manager.clear_slot(1)  # Clear slot B, leaving slot A filled.
	manager.fill_next_available("new_fill")  # Slot A full, slot B empty: new_fill goes to B.

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_fill_order_clear_b_refill_slots_null", "get_slot returned null")
		return

	_assert_eq_string(
		"orig_a",
		slot_a.get_active_mutation_id(),
		"adv_fill_order_clear_b_slot_a_unchanged — slot A must remain 'orig_a' after clearing slot B and refilling"
	)
	_assert_eq_string(
		"new_fill",
		slot_b.get_active_mutation_id(),
		"adv_fill_order_clear_b_slot_b_gets_new_fill — slot B must receive 'new_fill' because it was empty"
	)


# ---------------------------------------------------------------------------
# COMBINATORIAL: empty ID + both-full state
# Already covered above in test_adv_empty_string_fill_on_full_manager_changes_nothing.
# Additional: empty ID after clear_all must still leave manager empty.
# ---------------------------------------------------------------------------

func test_adv_empty_string_fill_after_clear_all_leaves_empty() -> void:
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_empty_str_after_clear_all"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("clear_all") or not manager.has_method("any_filled"):
		_fail("adv_empty_str_after_clear_all_api_missing", "MutationSlotManager must implement fill_next_available, clear_all, any_filled")
		return

	manager.fill_next_available("temp")
	manager.clear_all()
	manager.fill_next_available("")  # Must be rejected.

	_assert_false(
		manager.any_filled(),
		"adv_empty_str_after_clear_all_still_empty — fill_next_available('') after clear_all must not fill any slot"
	)


# ---------------------------------------------------------------------------
# STRESS: large number of fill_next_available calls on a full manager
# ---------------------------------------------------------------------------

func test_adv_stress_100_overwrites_slot_b_slot_a_unmodified() -> void:
	# 100 calls to fill_next_available while both slots are full.
	# Slot A must never change; slot B must hold the last written ID.
	var manager: Object = _make_manager()
	if _skip_if_missing(manager, "adv_stress_100_overwrites"):
		return

	if not manager.has_method("fill_next_available") or not manager.has_method("get_slot"):
		_fail("adv_stress_100_overwrites_api_missing", "MutationSlotManager must implement fill_next_available and get_slot")
		return

	manager.fill_next_available("anchor_a")
	manager.fill_next_available("first_b")

	var slot_a: Object = manager.get_slot(0)
	var slot_b: Object = manager.get_slot(1)

	if slot_a == null or slot_b == null:
		_fail("adv_stress_100_slots_null", "get_slot returned null")
		return

	var n: int = 0
	while n < 100:
		manager.fill_next_available("stress_" + str(n))
		n += 1

	_assert_eq_string(
		"anchor_a",
		slot_a.get_active_mutation_id(),
		"adv_stress_100_slot_a_unchanged — slot A must remain 'anchor_a' after 100 overwrites of slot B"
	)
	_assert_eq_string(
		"stress_99",
		slot_b.get_active_mutation_id(),
		"adv_stress_100_slot_b_last_id — slot B must hold the last ID 'stress_99' after 100 overwrites"
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_mutation_slot_system_dual_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Null/empty/whitespace IDs
	test_adv_whitespace_id_fills_slot_because_not_empty_string()
	test_adv_tab_id_fills_slot()
	test_adv_newline_id_fills_slot()
	test_adv_empty_string_fill_on_full_manager_changes_nothing()

	# Simultaneous fill with identical IDs
	test_adv_both_slots_filled_with_same_id_are_independent()
	test_adv_get_slot_0_and_1_return_distinct_objects_with_same_id()

	# Repeated overwrite of slot B (both-full path)
	test_adv_repeated_overwrite_slot_b_slot_a_never_changes()
	test_adv_overwrite_slot_b_any_filled_remains_true()

	# clear_all then immediate refill (ghost state)
	test_adv_clear_all_then_refill_no_ghost_state()
	test_adv_clear_all_refill_cycle_repeated()
	test_adv_clear_all_then_single_fill_goes_to_slot_a()

	# clear_slot with invalid/extreme indices
	test_adv_clear_slot_extreme_negative_index()
	test_adv_clear_slot_extreme_positive_index()
	test_adv_clear_slot_invalid_leaves_valid_slots_intact()
	test_adv_clear_slot_on_empty_slot_is_safe()
	test_adv_clear_all_on_empty_manager_is_safe()

	# Two independent manager instances — deep isolation
	test_adv_two_instances_deep_isolation_fill_and_clear()
	test_adv_two_instances_clear_all_does_not_affect_other()

	# Rapid alternating fill/clear sequences
	test_adv_rapid_alternating_fill_clear_slot_a()
	test_adv_rapid_fill_clear_both_slots()
	test_adv_fill_a_clear_all_fill_next_goes_to_a_not_b()

	# any_filled(), get_slot(), get_slot_count() on freshly cleared manager
	test_adv_any_filled_false_after_clear_slot_0_of_only_filled_slot()
	test_adv_get_slot_count_invariant_across_fill_and_clear()
	test_adv_get_slot_returns_same_object_on_repeated_calls()
	test_adv_get_slot_out_of_range_exhaustive()

	# Special characters and long IDs
	test_adv_special_character_id_stored_verbatim()
	test_adv_very_long_id_stored_verbatim()

	# Direct slot manipulation bypass
	test_adv_any_filled_reflects_direct_set_on_slot_a()
	test_adv_any_filled_reflects_direct_set_on_slot_b()

	# Fill-order rule robustness (mutation testing)
	test_adv_fill_order_slot_a_full_slot_b_empty_goes_to_b_not_a()
	test_adv_fill_order_clear_b_then_fill_goes_to_b_not_overwrite_a()

	# Combinatorial: empty ID + various states
	test_adv_empty_string_fill_after_clear_all_leaves_empty()

	# Stress / load
	test_adv_stress_100_overwrites_slot_b_slot_a_unmodified()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
