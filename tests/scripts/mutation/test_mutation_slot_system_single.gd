#
# test_mutation_slot_system_single.gd
#
# Primary behavioral tests for the single-slot mutation system.
# Scope:
#   - SLOT-1 — pure-logic MutationSlot data model (empty vs filled).
#   - SLOT-2 — invariants between MutationSlot and MutationInventory under
#              simple grant sequences (last-wins, no orphaned slot IDs).
#   - SLOT-5 — deterministic, side-effect free behavior for the slot model.
#
# Ticket: mutation_slot_system_single.md
# Spec:  mutation_slot_system_single_spec.md (SLOT-1, SLOT-2, SLOT-5)
#

class_name MutationSlotSystemSingleTests
extends "res://tests/utils/test_utils.gd"


const DEFAULT_MUTATION_ID: String = "infection_mutation_01"


var _pass_count: int = 0
var _fail_count: int = 0


func _load_mutation_slot_script() -> GDScript:
	return load("res://scripts/mutation/mutation_slot.gd") as GDScript


func _make_mutation_slot_instance() -> Object:
	var script: GDScript = _load_mutation_slot_script()
	if script == null:
		return null
	return script.new()


func _make_inventory_instance() -> Object:
	var script: GDScript = load("res://scripts/mutation/mutation_inventory.gd") as GDScript
	if script == null:
		return null
	return script.new()


# ---------------------------------------------------------------------------
# SLOT-1 — Single active mutation slot data model
# ---------------------------------------------------------------------------

func test_mutation_slot_script_exists_and_is_pure_logic() -> void:
	var script: GDScript = _load_mutation_slot_script()
	if script == null:
		_fail(
			"slot_1_script_exists",
			"res://scripts/mutation/mutation_slot.gd not found; implement MutationSlot per SLOT-1 spec"
		)
		return

	var instance: Object = script.new()
	if instance == null:
		_fail(
			"slot_1_instantiates",
			"MutationSlot script did not instantiate; expected pure-logic RefCounted/Object"
		)
		return

	# Spec requires a pure-logic object, not a Node/scene.
	_assert_false(instance is Node, "slot_1_not_node — MutationSlot must not extend Node")


func test_mutation_slot_default_state_is_empty() -> void:
	var slot: Object = _make_mutation_slot_instance()
	if slot == null:
		_fail(
			"slot_1_default_state",
			"MutationSlot script missing or failed to instantiate; cannot verify default state"
		)
		return

	if not slot.has_method("is_filled") or not slot.has_method("get_active_mutation_id"):
		_fail(
			"slot_1_api_missing",
			"MutationSlot must implement is_filled() and get_active_mutation_id() per SLOT-1 spec"
		)
		return

	var filled: bool = slot.is_filled()
	var active_id: String = slot.get_active_mutation_id()

	_assert_false(
		filled,
		"slot_1_default_not_filled — is_filled() is false immediately after construction"
	)
	_assert_eq_string(
		"",
		active_id,
		"slot_1_default_empty_id — get_active_mutation_id() returns empty string when slot is empty"
	)


func test_mutation_slot_set_and_clear_round_trip() -> void:
	var slot: Object = _make_mutation_slot_instance()
	if slot == null:
		_fail("slot_1_set_clear_round_trip", "MutationSlot instance missing; skipping")
		return

	if not slot.has_method("set_active_mutation_id") or not slot.has_method("clear"):
		_fail(
			"slot_1_set_clear_api_missing",
			"MutationSlot must implement set_active_mutation_id(id: String) and clear() per SLOT-1"
		)
		return

	slot.clear()
	slot.set_active_mutation_id(DEFAULT_MUTATION_ID)

	_assert_true(
		slot.is_filled(),
		"slot_1_after_set_filled — is_filled() true after set_active_mutation_id(id)"
	)
	_assert_eq_string(
		DEFAULT_MUTATION_ID,
		slot.get_active_mutation_id(),
		"slot_1_after_set_id_matches — get_active_mutation_id() returns the last set ID"
	)

	slot.clear()

	_assert_false(
		slot.is_filled(),
		"slot_1_after_clear_not_filled — is_filled() false after clear()"
	)
	_assert_eq_string(
		"",
		slot.get_active_mutation_id(),
		"slot_1_after_clear_empty_id — get_active_mutation_id() returns empty string after clear()"
	)

	# Idempotent clear: calling clear() again must leave state unchanged.
	slot.clear()
	_assert_false(
		slot.is_filled(),
		"slot_1_clear_idempotent_filled — repeated clear() keeps slot empty"
	)
	_assert_eq_string(
		"",
		slot.get_active_mutation_id(),
		"slot_1_clear_idempotent_id — repeated clear() keeps active ID at empty string"
	)


func test_mutation_slot_last_wins_for_multiple_ids() -> void:
	var slot: Object = _make_mutation_slot_instance()
	if slot == null:
		_fail("slot_1_last_wins", "MutationSlot instance missing; skipping")
		return

	if not slot.has_method("set_active_mutation_id"):
		_fail(
			"slot_1_last_wins_api_missing",
			"MutationSlot must implement set_active_mutation_id(id: String) per SLOT-1"
		)
		return

	slot.clear()
	slot.set_active_mutation_id("mutation_a")
	slot.set_active_mutation_id("mutation_b")

	_assert_true(
		slot.is_filled(),
		"slot_1_last_wins_filled — slot remains filled after multiple set_active_mutation_id calls"
	)
	_assert_eq_string(
		"mutation_b",
		slot.get_active_mutation_id(),
		"slot_1_last_wins_id — last set mutation ID wins"
	)


func test_mutation_slot_idempotent_for_same_id() -> void:
	var slot: Object = _make_mutation_slot_instance()
	if slot == null:
		_fail("slot_1_idempotent_same_id", "MutationSlot instance missing; skipping")
		return

	if not slot.has_method("set_active_mutation_id"):
		_fail(
			"slot_1_idempotent_same_id_api_missing",
			"MutationSlot must implement set_active_mutation_id(id: String) per SLOT-1"
		)
		return

	slot.clear()
	slot.set_active_mutation_id(DEFAULT_MUTATION_ID)
	slot.set_active_mutation_id(DEFAULT_MUTATION_ID)

	_assert_true(
		slot.is_filled(),
		"slot_1_idempotent_same_id_filled — slot stays filled after repeated set with same ID"
	)
	_assert_eq_string(
		DEFAULT_MUTATION_ID,
		slot.get_active_mutation_id(),
		"slot_1_idempotent_same_id_id — active ID unchanged when set to same value twice"
	)


# ---------------------------------------------------------------------------
# SLOT-2 — Integration invariants with MutationInventory
# ---------------------------------------------------------------------------

func test_slot_and_inventory_start_empty_together() -> void:
	var inv: Object = _make_inventory_instance()
	var slot: Object = _make_mutation_slot_instance()
	if inv == null or slot == null:
		_fail(
			"slot_2_start_empty_together",
			"MutationInventory or MutationSlot missing; cannot verify starting invariants"
		)
		return

	if not inv.has_method("get_granted_count") or not inv.has_method("has"):
		_fail(
			"slot_2_inventory_api_missing",
			"MutationInventory must implement get_granted_count() and has(id)"
		)
		return

	var count: int = inv.get_granted_count()
	_assert_eq_int(
		0,
		count,
		"slot_2_inventory_initial_zero — inventory granted-count is 0 at start"
	)

	_assert_false(
		slot.is_filled(),
		"slot_2_slot_initial_empty — slot is empty at start"
	)
	_assert_eq_string(
		"",
		slot.get_active_mutation_id(),
		"slot_2_slot_initial_empty_id — active ID is empty string at start"
	)


func test_single_grant_updates_inventory_and_slot_consistently() -> void:
	var inv: Object = _make_inventory_instance()
	var slot: Object = _make_mutation_slot_instance()
	if inv == null or slot == null:
		_fail(
			"slot_2_single_grant",
			"MutationInventory or MutationSlot missing; cannot verify single-grant invariant"
		)
		return

	if not inv.has_method("grant") or not inv.has_method("get_granted_count") or not inv.has_method("has"):
		_fail(
			"slot_2_single_grant_inventory_api_missing",
			"MutationInventory must implement grant(id), has(id), get_granted_count()"
		)
		return

	if not slot.has_method("set_active_mutation_id"):
		_fail(
			"slot_2_single_grant_slot_api_missing",
			"MutationSlot must implement set_active_mutation_id(id: String) per SLOT-2"
		)
		return

	var count_before: int = inv.get_granted_count()

	# Drive both systems as production code is expected to: grant into inventory
	# and update the slot with the granted ID.
	inv.grant(DEFAULT_MUTATION_ID)
	slot.set_active_mutation_id(DEFAULT_MUTATION_ID)

	var count_after: int = inv.get_granted_count()
	_assert_eq_int(
		count_before + 1,
		count_after,
		"slot_2_single_grant_inventory_count — one new mutation granted to inventory"
	)
	_assert_true(
		inv.has(DEFAULT_MUTATION_ID),
		"slot_2_single_grant_inventory_has_id — inventory has the granted mutation ID"
	)
	_assert_true(
		slot.is_filled(),
		"slot_2_single_grant_filled — slot is filled after first grant"
	)
	_assert_eq_string(
		DEFAULT_MUTATION_ID,
		slot.get_active_mutation_id(),
		"slot_2_single_grant_slot_id_matches — slot active ID equals granted mutation"
	)
	_assert_true(
		inv.has(slot.get_active_mutation_id()),
		"slot_2_single_grant_slot_id_in_inventory — inventory.has(slot.get_active_mutation_id()) is true when slot is filled"
	)


func test_repeated_grants_same_id_do_not_change_slot_active_id() -> void:
	var inv: Object = _make_inventory_instance()
	var slot: Object = _make_mutation_slot_instance()
	if inv == null or slot == null:
		_fail(
			"slot_2_repeated_same_id",
			"MutationInventory or MutationSlot missing; cannot verify repeated-grant invariant"
		)
		return

	if not inv.has_method("grant") or not inv.has_method("get_granted_count") or not inv.has_method("has"):
		_fail(
			"slot_2_repeated_same_id_inventory_api_missing",
			"MutationInventory must implement grant(id), has(id), get_granted_count()"
		)
		return

	if not slot.has_method("set_active_mutation_id"):
		_fail(
			"slot_2_repeated_same_id_slot_api_missing",
			"MutationSlot must implement set_active_mutation_id(id: String) per SLOT-2"
		)
		return

	slot.clear()

	inv.grant(DEFAULT_MUTATION_ID)
	slot.set_active_mutation_id(DEFAULT_MUTATION_ID)

	var count_after_first: int = inv.get_granted_count()

	inv.grant(DEFAULT_MUTATION_ID)
	slot.set_active_mutation_id(DEFAULT_MUTATION_ID)

	var count_after_second: int = inv.get_granted_count()

	_assert_true(
		slot.is_filled(),
		"slot_2_repeated_same_id_filled — slot remains filled after repeated grants of same ID"
	)
	_assert_eq_string(
		DEFAULT_MUTATION_ID,
		slot.get_active_mutation_id(),
		"slot_2_repeated_same_id_slot_id_unchanged — active ID unchanged for repeated same-ID grants"
	)
	_assert_true(
		inv.has(DEFAULT_MUTATION_ID),
		"slot_2_repeated_same_id_inventory_has_id — inventory still has the mutation ID"
	)
	_assert_true(
		count_after_second == count_after_first + 1,
		"slot_2_repeated_same_id_inventory_count_increments — inventory count still increases per grant"
	)


func test_grants_of_different_ids_follow_last_wins_rule() -> void:
	var inv: Object = _make_inventory_instance()
	var slot: Object = _make_mutation_slot_instance()
	if inv == null or slot == null:
		_fail(
			"slot_2_last_wins_different_ids",
			"MutationInventory or MutationSlot missing; cannot verify last-wins invariant"
		)
		return

	if not inv.has_method("grant") or not inv.has_method("get_granted_count") or not inv.has_method("has"):
		_fail(
			"slot_2_last_wins_different_ids_inventory_api_missing",
			"MutationInventory must implement grant(id), has(id), get_granted_count()"
		)
		return

	if not slot.has_method("set_active_mutation_id"):
		_fail(
			"slot_2_last_wins_different_ids_slot_api_missing",
			"MutationSlot must implement set_active_mutation_id(id: String) per SLOT-2"
		)
		return

	slot.clear()

	var first_id: String = "mutation_a"
	var second_id: String = "mutation_b"

	inv.grant(first_id)
	slot.set_active_mutation_id(first_id)

	inv.grant(second_id)
	slot.set_active_mutation_id(second_id)

	_assert_true(
		slot.is_filled(),
		"slot_2_last_wins_different_ids_filled — slot filled after multiple different-ID grants"
	)
	_assert_eq_string(
		second_id,
		slot.get_active_mutation_id(),
		"slot_2_last_wins_different_ids_slot_id — last granted ID becomes active"
	)
	_assert_true(
		inv.has(slot.get_active_mutation_id()),
		"slot_2_last_wins_different_ids_slot_id_in_inventory — slot ID always present in inventory"
	)


func test_clearing_slot_does_not_change_inventory_but_breaks_link() -> void:
	var inv: Object = _make_inventory_instance()
	var slot: Object = _make_mutation_slot_instance()
	if inv == null or slot == null:
		_fail(
			"slot_2_clear_breaks_link",
			"MutationInventory or MutationSlot missing; cannot verify clear invariant"
		)
		return

	if not inv.has_method("grant") or not inv.has_method("get_granted_count") or not inv.has_method("has"):
		_fail(
			"slot_2_clear_breaks_link_inventory_api_missing",
			"MutationInventory must implement grant(id), has(id), get_granted_count()"
		)
		return

	if not slot.has_method("set_active_mutation_id") or not slot.has_method("clear"):
		_fail(
			"slot_2_clear_breaks_link_slot_api_missing",
			"MutationSlot must implement set_active_mutation_id(id: String) and clear() per SLOT-1/2"
		)
		return

	inv.grant(DEFAULT_MUTATION_ID)
	slot.set_active_mutation_id(DEFAULT_MUTATION_ID)

	var count_before_clear: int = inv.get_granted_count()

	slot.clear()

	var count_after_clear: int = inv.get_granted_count()

	_assert_eq_int(
		count_before_clear,
		count_after_clear,
		"slot_2_clear_does_not_mutate_inventory — clearing slot does not change inventory count"
	)
	_assert_true(
		inv.has(DEFAULT_MUTATION_ID),
		"slot_2_clear_inventory_still_has_id — inventory still reports granted mutation after slot clear()"
	)
	_assert_false(
		slot.is_filled(),
		"slot_2_clear_slot_empty — slot is empty after clear() even though inventory has grants"
	)
	_assert_eq_string(
		"",
		slot.get_active_mutation_id(),
		"slot_2_clear_slot_id_empty — active mutation ID is empty after clear()"
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_mutation_slot_system_single.gd ---")
	_pass_count = 0
	_fail_count = 0

	# SLOT-1 — pure-logic MutationSlot data model
	test_mutation_slot_script_exists_and_is_pure_logic()
	test_mutation_slot_default_state_is_empty()
	test_mutation_slot_set_and_clear_round_trip()
	test_mutation_slot_last_wins_for_multiple_ids()
	test_mutation_slot_idempotent_for_same_id()

	# SLOT-2 — integration invariants with MutationInventory
	test_slot_and_inventory_start_empty_together()
	test_single_grant_updates_inventory_and_slot_consistently()
	test_repeated_grants_same_id_do_not_change_slot_active_id()
	test_grants_of_different_ids_follow_last_wins_rule()
	test_clearing_slot_does_not_change_inventory_but_breaks_link()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

