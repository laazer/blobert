#
# test_slot_consumption_rules.gd
#
# Primary behavioral tests for the slot consumption rules.
# Scope:
#   - SCR-1 — consume_fusion_slots() function contract: method existence,
#             void return, headless instantiation, equivalence to clear_all(),
#             idempotency.
#   - SCR-2 — All-or-nothing clear rule: both slots cleared atomically,
#             both-filled case, one-filled cases, no partial clear.
#   - SCR-3 — Re-infection allowed post-fusion: no lock-out flag,
#             fill order resumes normally, multi-cycle state isolation.
#   - SCR-4 — Ghost and duplicate prevention: get_active_mutation_id() == ""
#             and is_filled() == false simultaneously after call,
#             no stale IDs across cycles.
#   - SCR-5 — Edge cases with fewer than two slots filled: one slot filled
#             (either slot), both slots empty, double-call safety.
#
# Ticket: slot_consumption_rules.md
# Spec:   slot_consumption_rules_spec.md (SCR-1 through SCR-5)
#
# Tests that call consume_fusion_slots() are expected to FAIL until
# implementation adds the method to MutationSlotManager (TDD red phase).
# Tests that only inspect existing API surface will pass immediately.
#

class_name SlotConsumptionRulesTests
extends "res://tests/utils/test_utils.gd"


var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _load_manager_script() -> GDScript:
	return load("res://scripts/mutation/mutation_slot_manager.gd") as GDScript


func _make_manager() -> Object:
	var script: GDScript = _load_manager_script()
	if script == null:
		return null
	return script.new()


# Guard helper: fails descriptively when the method under test does not exist yet.
# Returns true when the guard fires (caller should return early).
func _require_consume_method(manager: Object, test_name: String) -> bool:
	if not manager.has_method("consume_fusion_slots"):
		_fail(
			test_name,
			"consume_fusion_slots() not found on MutationSlotManager — implement per SCR-1"
		)
		return true
	return false


# ---------------------------------------------------------------------------
# SCR-1-AC-1  consume_fusion_slots method exists on a freshly instantiated manager
# ---------------------------------------------------------------------------

func test_scr1_ac1_method_exists() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail(
			"scr1_ac1_method_exists",
			"MutationSlotManager instance missing; cannot verify method existence"
		)
		return

	_assert_true(
		manager.has_method("consume_fusion_slots"),
		"scr1_ac1_method_exists — MutationSlotManager must have consume_fusion_slots() per SCR-1"
	)


# ---------------------------------------------------------------------------
# SCR-1-AC-2  consume_fusion_slots() can be called without capturing a return value
# ---------------------------------------------------------------------------

func test_scr1_ac2_callable_void_no_crash() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr1_ac2_callable_void", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr1_ac2_callable_void"):
		return

	# Calling with return value ignored must not crash.
	manager.consume_fusion_slots()
	_pass("scr1_ac2_callable_void — consume_fusion_slots() called with return value ignored; no crash")


# ---------------------------------------------------------------------------
# SCR-1-AC-3  consume_fusion_slots() callable with no scene tree (headless)
# ---------------------------------------------------------------------------

func test_scr1_ac3_headless_instantiation_no_crash() -> void:
	# This entire suite runs headless. Reaching here proves the manager loaded
	# without a scene tree. We instantiate a fresh one and call the method.
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr1_ac3_headless", "MutationSlotManager could not be instantiated headlessly")
		return

	if _require_consume_method(manager, "scr1_ac3_headless"):
		return

	manager.consume_fusion_slots()
	_pass("scr1_ac3_headless — consume_fusion_slots() ran in headless process without crash or scene tree")


# ---------------------------------------------------------------------------
# SCR-1-AC-4  consume_fusion_slots() produces same post-call state as clear_all()
# ---------------------------------------------------------------------------

func test_scr1_ac4_equivalent_to_clear_all() -> void:
	var ref_manager: Object = _make_manager()
	var test_manager: Object = _make_manager()

	if ref_manager == null or test_manager == null:
		_fail("scr1_ac4_equiv_clear_all", "MutationSlotManager instances missing; skipping")
		return

	if _require_consume_method(test_manager, "scr1_ac4_equiv_clear_all"):
		return

	# Pre-fill both managers identically.
	ref_manager.fill_next_available("mutation_a")
	ref_manager.fill_next_available("mutation_b")
	test_manager.fill_next_available("mutation_a")
	test_manager.fill_next_available("mutation_b")

	# Apply each clearing method.
	ref_manager.clear_all()
	test_manager.consume_fusion_slots()

	# Both managers must have identical observable post-call state.
	_assert_false(
		ref_manager.any_filled(),
		"scr1_ac4_ref_any_filled_false — reference (clear_all) any_filled() must be false"
	)
	_assert_false(
		test_manager.any_filled(),
		"scr1_ac4_test_any_filled_false — consume_fusion_slots() any_filled() must equal clear_all() result (false)"
	)
	_assert_eq_string(
		ref_manager.get_slot(0).get_active_mutation_id(),
		test_manager.get_slot(0).get_active_mutation_id(),
		"scr1_ac4_slot_a_id_matches — slot A active ID must match clear_all() reference"
	)
	_assert_eq_string(
		ref_manager.get_slot(1).get_active_mutation_id(),
		test_manager.get_slot(1).get_active_mutation_id(),
		"scr1_ac4_slot_b_id_matches — slot B active ID must match clear_all() reference"
	)
	_assert_false(
		test_manager.get_slot(0).is_filled(),
		"scr1_ac4_slot_a_not_filled — slot A is_filled() must be false after consume_fusion_slots()"
	)
	_assert_false(
		test_manager.get_slot(1).is_filled(),
		"scr1_ac4_slot_b_not_filled — slot B is_filled() must be false after consume_fusion_slots()"
	)


# ---------------------------------------------------------------------------
# SCR-1-AC-5  Calling consume_fusion_slots() twice in succession is safe
# ---------------------------------------------------------------------------

func test_scr1_ac5_double_call_idempotent() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr1_ac5_double_call", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr1_ac5_double_call"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")

	# First call
	manager.consume_fusion_slots()
	# Second call must not crash and must leave state unchanged (both empty)
	manager.consume_fusion_slots()

	_assert_false(
		manager.get_slot(0).is_filled(),
		"scr1_ac5_slot_a_empty_after_double_call — slot A must be empty after two successive consume_fusion_slots() calls"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"scr1_ac5_slot_b_empty_after_double_call — slot B must be empty after two successive consume_fusion_slots() calls"
	)
	_assert_false(
		manager.any_filled(),
		"scr1_ac5_any_filled_false_after_double_call — any_filled() must be false after two successive consume_fusion_slots() calls"
	)


# ---------------------------------------------------------------------------
# SCR-2-AC-1  Both slots cleared when both were filled
# ---------------------------------------------------------------------------

func test_scr2_ac1_both_slots_cleared_when_both_filled() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr2_ac1_both_cleared", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr2_ac1_both_cleared"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")

	manager.consume_fusion_slots()

	_assert_false(
		manager.get_slot(0).is_filled(),
		"scr2_ac1_slot_a_cleared — get_slot(0).is_filled() must be false after consume_fusion_slots() on both-filled manager"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"scr2_ac1_slot_b_cleared — get_slot(1).is_filled() must be false after consume_fusion_slots() on both-filled manager"
	)


# ---------------------------------------------------------------------------
# SCR-2-AC-2  any_filled() false after both-filled consume
# ---------------------------------------------------------------------------

func test_scr2_ac2_any_filled_false_after_both_filled_consume() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr2_ac2_any_filled_false", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr2_ac2_any_filled_false"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")

	manager.consume_fusion_slots()

	_assert_false(
		manager.any_filled(),
		"scr2_ac2_any_filled_false — any_filled() must return false after consume_fusion_slots() on both-filled manager"
	)


# ---------------------------------------------------------------------------
# SCR-2-AC-3  One-filled case: slot A filled, slot B empty — both cleared
# ---------------------------------------------------------------------------

func test_scr2_ac3_slot_a_only_filled_both_cleared() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr2_ac3_slot_a_only", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr2_ac3_slot_a_only"):
		return

	manager.fill_next_available("mutation_a")
	# slot B is intentionally left empty

	manager.consume_fusion_slots()

	_assert_false(
		manager.get_slot(0).is_filled(),
		"scr2_ac3_slot_a_cleared — slot A must be empty after consume_fusion_slots() (was filled)"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"scr2_ac3_slot_b_still_empty — slot B must be empty after consume_fusion_slots() (was already empty)"
	)


# ---------------------------------------------------------------------------
# SCR-2-AC-4  One-filled case: slot A empty, slot B filled — both cleared
# ---------------------------------------------------------------------------

func test_scr2_ac4_slot_b_only_filled_both_cleared() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr2_ac4_slot_b_only", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr2_ac4_slot_b_only"):
		return

	# Directly set slot B to simulate out-of-normal-fill-order state
	# (e.g., slot A was manually cleared after both were filled).
	manager.get_slot(1).set_active_mutation_id("mutation_b")
	# slot A is intentionally left empty

	manager.consume_fusion_slots()

	_assert_false(
		manager.get_slot(0).is_filled(),
		"scr2_ac4_slot_a_still_empty — slot A must be empty after consume_fusion_slots() (was already empty)"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"scr2_ac4_slot_b_cleared — slot B must be empty after consume_fusion_slots() (was filled)"
	)


# ---------------------------------------------------------------------------
# SCR-2-AC-5  No partial clear: after consume, neither slot is half-cleared
# Asserts that when both slots were filled, the result is neither
# (filled, empty) nor (empty, filled) — only (empty, empty) is valid.
# ---------------------------------------------------------------------------

func test_scr2_ac5_no_partial_clear_from_both_filled() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr2_ac5_no_partial_clear", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr2_ac5_no_partial_clear"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")

	manager.consume_fusion_slots()

	var slot_a_filled: bool = manager.get_slot(0).is_filled()
	var slot_b_filled: bool = manager.get_slot(1).is_filled()

	# Partial clear would be: one true, one false.
	var partial_clear: bool = (slot_a_filled and not slot_b_filled) or (not slot_a_filled and slot_b_filled)

	_assert_false(
		partial_clear,
		"scr2_ac5_no_partial_clear — no code path may leave one slot filled and one empty after consume_fusion_slots() on both-filled manager"
	)
	_assert_false(
		slot_a_filled,
		"scr2_ac5_slot_a_must_be_empty — slot A must be empty (not partially cleared)"
	)
	_assert_false(
		slot_b_filled,
		"scr2_ac5_slot_b_must_be_empty — slot B must be empty (not partially cleared)"
	)


# ---------------------------------------------------------------------------
# SCR-3-AC-1  After consume, fill_next_available fills slot A first
# ---------------------------------------------------------------------------

func test_scr3_ac1_first_fill_after_consume_goes_to_slot_a() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr3_ac1_fill_after_consume", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr3_ac1_fill_after_consume"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.consume_fusion_slots()

	manager.fill_next_available("mutation_x")

	_assert_eq_string(
		"mutation_x",
		manager.get_slot(0).get_active_mutation_id(),
		"scr3_ac1_slot_a_gets_mutation_x — first fill after consume must go to slot A"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"scr3_ac1_slot_b_still_empty — slot B must remain empty after one post-consume fill"
	)


# ---------------------------------------------------------------------------
# SCR-3-AC-2  After consume, two fills fill A then B in normal order
# ---------------------------------------------------------------------------

func test_scr3_ac2_two_fills_after_consume_respect_fill_order() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr3_ac2_two_fills_after_consume", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr3_ac2_two_fills_after_consume"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.consume_fusion_slots()

	manager.fill_next_available("mutation_x")
	manager.fill_next_available("mutation_y")

	_assert_eq_string(
		"mutation_x",
		manager.get_slot(0).get_active_mutation_id(),
		"scr3_ac2_slot_a_holds_x — slot A must hold 'mutation_x' after two post-consume fills"
	)
	_assert_eq_string(
		"mutation_y",
		manager.get_slot(1).get_active_mutation_id(),
		"scr3_ac2_slot_b_holds_y — slot B must hold 'mutation_y' after two post-consume fills"
	)


# ---------------------------------------------------------------------------
# SCR-3-AC-3  Full fill-consume-fill cycle: second fill IDs replace first
# ---------------------------------------------------------------------------

func test_scr3_ac3_full_cycle_new_ids_replace_old() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr3_ac3_full_cycle", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr3_ac3_full_cycle"):
		return

	# Cycle 1
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.consume_fusion_slots()

	# Cycle 2 fills
	manager.fill_next_available("mutation_c")
	manager.fill_next_available("mutation_d")

	_assert_eq_string(
		"mutation_c",
		manager.get_slot(0).get_active_mutation_id(),
		"scr3_ac3_slot_a_holds_c — slot A must hold 'mutation_c' (not pre-fusion value 'mutation_a')"
	)
	_assert_eq_string(
		"mutation_d",
		manager.get_slot(1).get_active_mutation_id(),
		"scr3_ac3_slot_b_holds_d — slot B must hold 'mutation_d' (not pre-fusion value 'mutation_b')"
	)


# ---------------------------------------------------------------------------
# SCR-3-AC-4  Multiple cycles do not accumulate state
# ---------------------------------------------------------------------------

func test_scr3_ac4_multiple_cycles_no_state_accumulation() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr3_ac4_multi_cycle", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr3_ac4_multi_cycle"):
		return

	# Cycle 1
	manager.fill_next_available("x1")
	manager.fill_next_available("x2")
	manager.consume_fusion_slots()

	# Cycle 2
	manager.fill_next_available("x3")
	manager.fill_next_available("x4")
	manager.consume_fusion_slots()

	# Cycle 3 — partial fill
	manager.fill_next_available("x5")

	# Only x5 should be present; x1–x4 must not appear anywhere.
	_assert_eq_string(
		"x5",
		manager.get_slot(0).get_active_mutation_id(),
		"scr3_ac4_slot_a_holds_x5 — slot A must hold only the most-recent fill 'x5'"
	)
	_assert_eq_string(
		"",
		manager.get_slot(1).get_active_mutation_id(),
		"scr3_ac4_slot_b_empty — slot B must be empty; no prior-cycle ID should persist"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"scr3_ac4_slot_b_not_filled — slot B must not be filled after 3 cycles with only one post-consume fill"
	)


# ---------------------------------------------------------------------------
# SCR-3-AC-5  No _post_fusion or _locked field introduced by consume_fusion_slots
# Verify by checking has_method for known-forbidden names and that is_filled
# behavior remains unchanged (the only behavioral proxy for lockout state).
# ---------------------------------------------------------------------------

func test_scr3_ac5_no_lockout_field_introduced() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr3_ac5_no_lockout", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr3_ac5_no_lockout"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.consume_fusion_slots()

	# If a lockout field existed, fill_next_available would fail to fill slot A.
	# The behavioral proxy: slot A must accept a new fill immediately.
	manager.fill_next_available("probe_id")

	_assert_eq_string(
		"probe_id",
		manager.get_slot(0).get_active_mutation_id(),
		"scr3_ac5_fill_accepted_after_consume — fill_next_available must work immediately after consume_fusion_slots() with no lockout"
	)


# ---------------------------------------------------------------------------
# SCR-4-AC-1  get_slot(0).get_active_mutation_id() == "" after both-filled consume
# ---------------------------------------------------------------------------

func test_scr4_ac1_slot_a_id_empty_after_consume() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr4_ac1_slot_a_id_empty", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr4_ac1_slot_a_id_empty"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.consume_fusion_slots()

	_assert_eq_string(
		"",
		manager.get_slot(0).get_active_mutation_id(),
		"scr4_ac1_slot_a_id_is_empty_string — get_slot(0).get_active_mutation_id() must be exactly '' (not null) after consume_fusion_slots()"
	)


# ---------------------------------------------------------------------------
# SCR-4-AC-2  get_slot(1).get_active_mutation_id() == "" after both-filled consume
# ---------------------------------------------------------------------------

func test_scr4_ac2_slot_b_id_empty_after_consume() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr4_ac2_slot_b_id_empty", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr4_ac2_slot_b_id_empty"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.consume_fusion_slots()

	_assert_eq_string(
		"",
		manager.get_slot(1).get_active_mutation_id(),
		"scr4_ac2_slot_b_id_is_empty_string — get_slot(1).get_active_mutation_id() must be exactly '' (not null) after consume_fusion_slots()"
	)


# ---------------------------------------------------------------------------
# SCR-4-AC-3  get_slot(0).is_filled() == false after both-filled consume
# ---------------------------------------------------------------------------

func test_scr4_ac3_slot_a_is_filled_false_after_consume() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr4_ac3_slot_a_is_filled", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr4_ac3_slot_a_is_filled"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.consume_fusion_slots()

	_assert_false(
		manager.get_slot(0).is_filled(),
		"scr4_ac3_slot_a_is_filled_false — get_slot(0).is_filled() must be false after consume_fusion_slots()"
	)


# ---------------------------------------------------------------------------
# SCR-4-AC-4  get_slot(1).is_filled() == false after both-filled consume
# ---------------------------------------------------------------------------

func test_scr4_ac4_slot_b_is_filled_false_after_consume() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr4_ac4_slot_b_is_filled", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr4_ac4_slot_b_is_filled"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.consume_fusion_slots()

	_assert_false(
		manager.get_slot(1).is_filled(),
		"scr4_ac4_slot_b_is_filled_false — get_slot(1).is_filled() must be false after consume_fusion_slots()"
	)


# ---------------------------------------------------------------------------
# SCR-4-AC-5  No ghost ID inversion on slot A: is_filled and ID are consistent
# ---------------------------------------------------------------------------

func test_scr4_ac5_no_ghost_id_on_slot_a() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr4_ac5_no_ghost_a", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr4_ac5_no_ghost_a"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.consume_fusion_slots()

	var slot_a: Object = manager.get_slot(0)
	var a_filled: bool = slot_a.is_filled()
	var a_id: String = slot_a.get_active_mutation_id()

	# Ghost ID: is_filled() false but ID is non-empty, or is_filled() true but ID is empty.
	var ghost_id_inversion: bool = (not a_filled and a_id != "") or (a_filled and a_id == "")

	_assert_false(
		ghost_id_inversion,
		"scr4_ac5_no_ghost_id_slot_a — slot A must have consistent is_filled() and get_active_mutation_id() after consume_fusion_slots() (no ghost ID inversion)"
	)
	_assert_false(
		a_filled,
		"scr4_ac5_slot_a_not_filled — slot A is_filled() must be false"
	)
	_assert_eq_string(
		"",
		a_id,
		"scr4_ac5_slot_a_id_empty — slot A ID must be empty string"
	)


# ---------------------------------------------------------------------------
# SCR-4-AC-6  No ghost ID inversion on slot B: is_filled and ID are consistent
# ---------------------------------------------------------------------------

func test_scr4_ac6_no_ghost_id_on_slot_b() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr4_ac6_no_ghost_b", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr4_ac6_no_ghost_b"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.consume_fusion_slots()

	var slot_b: Object = manager.get_slot(1)
	var b_filled: bool = slot_b.is_filled()
	var b_id: String = slot_b.get_active_mutation_id()

	var ghost_id_inversion: bool = (not b_filled and b_id != "") or (b_filled and b_id == "")

	_assert_false(
		ghost_id_inversion,
		"scr4_ac6_no_ghost_id_slot_b — slot B must have consistent is_filled() and get_active_mutation_id() after consume_fusion_slots() (no ghost ID inversion)"
	)
	_assert_false(
		b_filled,
		"scr4_ac6_slot_b_not_filled — slot B is_filled() must be false"
	)
	_assert_eq_string(
		"",
		b_id,
		"scr4_ac6_slot_b_id_empty — slot B ID must be empty string"
	)


# ---------------------------------------------------------------------------
# SCR-4-AC-7  No pre-fusion ID appears after consume and one re-fill
# ---------------------------------------------------------------------------

func test_scr4_ac7_no_pre_fusion_id_after_consume_and_one_fill() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr4_ac7_no_prefusion_id", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr4_ac7_no_prefusion_id"):
		return

	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.consume_fusion_slots()

	manager.fill_next_available("mutation_new")

	_assert_eq_string(
		"mutation_new",
		manager.get_slot(0).get_active_mutation_id(),
		"scr4_ac7_slot_a_holds_new — slot A must hold 'mutation_new', not the pre-fusion ID"
	)
	_assert_eq_string(
		"",
		manager.get_slot(1).get_active_mutation_id(),
		"scr4_ac7_slot_b_id_empty — slot B ID must be empty string; pre-fusion 'mutation_b' must not appear"
	)


# ---------------------------------------------------------------------------
# SCR-4-AC-8  No ID from any prior cycle appears after multi-cycle consume
# ---------------------------------------------------------------------------

func test_scr4_ac8_no_prior_cycle_id_after_multi_cycle_consume() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr4_ac8_no_prior_cycle_id", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr4_ac8_no_prior_cycle_id"):
		return

	# Cycle 1
	manager.fill_next_available("x1")
	manager.fill_next_available("x2")
	manager.consume_fusion_slots()

	# Cycle 2
	manager.fill_next_available("x3")
	manager.fill_next_available("x4")
	manager.consume_fusion_slots()

	# After cycle 2's consume, neither slot may hold x1, x2, x3, or x4.
	var slot_a_id: String = manager.get_slot(0).get_active_mutation_id()
	var slot_b_id: String = manager.get_slot(1).get_active_mutation_id()
	var stale_ids: Array = ["x1", "x2", "x3", "x4"]

	_assert_false(
		stale_ids.has(slot_a_id),
		"scr4_ac8_slot_a_no_stale_id — slot A must not hold any ID from prior cycles after consume_fusion_slots(); got: '" + slot_a_id + "'"
	)
	_assert_false(
		stale_ids.has(slot_b_id),
		"scr4_ac8_slot_b_no_stale_id — slot B must not hold any ID from prior cycles after consume_fusion_slots(); got: '" + slot_b_id + "'"
	)
	_assert_eq_string(
		"",
		slot_a_id,
		"scr4_ac8_slot_a_id_empty — slot A ID must be exactly '' after final consume_fusion_slots()"
	)
	_assert_eq_string(
		"",
		slot_b_id,
		"scr4_ac8_slot_b_id_empty — slot B ID must be exactly '' after final consume_fusion_slots()"
	)


# ---------------------------------------------------------------------------
# SCR-5-AC-1  One slot filled (slot A): no crash, normal return
# ---------------------------------------------------------------------------

func test_scr5_ac1_one_slot_a_filled_no_crash() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr5_ac1_slot_a_only_no_crash", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr5_ac1_slot_a_only_no_crash"):
		return

	manager.fill_next_available("mutation_a")
	# slot B intentionally left empty

	# Must not crash.
	manager.consume_fusion_slots()
	_pass("scr5_ac1_slot_a_only_no_crash — consume_fusion_slots() with only slot A filled did not crash")


# ---------------------------------------------------------------------------
# SCR-5-AC-2  After one-slot-A-filled consume: slot A cleared with empty ID
# ---------------------------------------------------------------------------

func test_scr5_ac2_slot_a_cleared_after_one_slot_a_filled_consume() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr5_ac2_slot_a_cleared", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr5_ac2_slot_a_cleared"):
		return

	manager.fill_next_available("mutation_a")
	manager.consume_fusion_slots()

	_assert_false(
		manager.get_slot(0).is_filled(),
		"scr5_ac2_slot_a_is_filled_false — slot A must be empty after consume with only slot A pre-filled"
	)
	_assert_eq_string(
		"",
		manager.get_slot(0).get_active_mutation_id(),
		"scr5_ac2_slot_a_id_empty — slot A ID must be '' after consume with only slot A pre-filled"
	)


# ---------------------------------------------------------------------------
# SCR-5-AC-3  After one-slot-A-filled consume: slot B remains empty and unmodified
# ---------------------------------------------------------------------------

func test_scr5_ac3_slot_b_unmodified_after_one_slot_a_filled_consume() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr5_ac3_slot_b_unmodified", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr5_ac3_slot_b_unmodified"):
		return

	manager.fill_next_available("mutation_a")
	# slot B is empty throughout

	manager.consume_fusion_slots()

	_assert_false(
		manager.get_slot(1).is_filled(),
		"scr5_ac3_slot_b_still_empty — slot B must be empty after consume (was already empty before)"
	)
	_assert_eq_string(
		"",
		manager.get_slot(1).get_active_mutation_id(),
		"scr5_ac3_slot_b_id_empty — slot B ID must be '' (not erroneously set to non-empty) after one-slot-A consume"
	)


# ---------------------------------------------------------------------------
# SCR-5-AC-4  One slot filled (slot B only): no crash, normal return
# ---------------------------------------------------------------------------

func test_scr5_ac4_one_slot_b_filled_no_crash() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr5_ac4_slot_b_only_no_crash", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr5_ac4_slot_b_only_no_crash"):
		return

	# Directly set slot B to simulate state where slot A was manually cleared.
	manager.get_slot(1).set_active_mutation_id("mutation_b")
	# slot A intentionally left empty

	manager.consume_fusion_slots()
	_pass("scr5_ac4_slot_b_only_no_crash — consume_fusion_slots() with only slot B filled did not crash")


# ---------------------------------------------------------------------------
# SCR-5-AC-5  After one-slot-B-filled consume: both slots empty
# ---------------------------------------------------------------------------

func test_scr5_ac5_both_empty_after_one_slot_b_filled_consume() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr5_ac5_both_empty_after_b_only", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr5_ac5_both_empty_after_b_only"):
		return

	manager.get_slot(1).set_active_mutation_id("mutation_b")
	manager.consume_fusion_slots()

	_assert_false(
		manager.get_slot(0).is_filled(),
		"scr5_ac5_slot_a_empty — slot A must be empty after consume with only slot B pre-filled"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"scr5_ac5_slot_b_cleared — slot B must be empty after consume with only slot B pre-filled"
	)


# ---------------------------------------------------------------------------
# SCR-5-AC-6  Both slots empty on construction: consume does not crash
# ---------------------------------------------------------------------------

func test_scr5_ac6_both_empty_on_construction_no_crash() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr5_ac6_empty_no_crash", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr5_ac6_empty_no_crash"):
		return

	# Fresh manager: both slots already empty. Must not crash or push_error.
	manager.consume_fusion_slots()
	_pass("scr5_ac6_empty_no_crash — consume_fusion_slots() on freshly constructed (both-empty) manager did not crash")


# ---------------------------------------------------------------------------
# SCR-5-AC-7  After empty-manager consume: both slots remain empty
# ---------------------------------------------------------------------------

func test_scr5_ac7_both_slots_remain_empty_after_empty_consume() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr5_ac7_empty_state_unchanged", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr5_ac7_empty_state_unchanged"):
		return

	manager.consume_fusion_slots()

	_assert_false(
		manager.get_slot(0).is_filled(),
		"scr5_ac7_slot_a_remains_empty — slot A must still be empty after consume on empty manager"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"scr5_ac7_slot_b_remains_empty — slot B must still be empty after consume on empty manager"
	)


# ---------------------------------------------------------------------------
# SCR-5-AC-8  Double call on any state: no crash; both slots empty after second call
# ---------------------------------------------------------------------------

func test_scr5_ac8_double_call_any_state_no_crash_both_empty() -> void:
	var manager: Object = _make_manager()
	if manager == null:
		_fail("scr5_ac8_double_call", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager, "scr5_ac8_double_call"):
		return

	# Test with both-filled state.
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.consume_fusion_slots()
	manager.consume_fusion_slots()

	_assert_false(
		manager.get_slot(0).is_filled(),
		"scr5_ac8_slot_a_empty_after_double_call_from_both_filled — slot A must be empty after two calls from both-filled state"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"scr5_ac8_slot_b_empty_after_double_call_from_both_filled — slot B must be empty after two calls from both-filled state"
	)

	# Test with one-filled state.
	var manager2: Object = _make_manager()
	if manager2 == null:
		_fail("scr5_ac8_double_call_one_filled", "Second MutationSlotManager instance missing; skipping")
		return

	manager2.fill_next_available("mutation_a")
	manager2.consume_fusion_slots()
	manager2.consume_fusion_slots()

	_assert_false(
		manager2.get_slot(0).is_filled(),
		"scr5_ac8_slot_a_empty_after_double_call_from_one_filled — slot A must be empty after two calls from one-filled state"
	)
	_assert_false(
		manager2.get_slot(1).is_filled(),
		"scr5_ac8_slot_b_empty_after_double_call_from_one_filled — slot B must be empty after two calls from one-filled state"
	)

	# Test with both-empty state.
	var manager3: Object = _make_manager()
	if manager3 == null:
		_fail("scr5_ac8_double_call_both_empty", "Third MutationSlotManager instance missing; skipping")
		return

	manager3.consume_fusion_slots()
	manager3.consume_fusion_slots()

	_assert_false(
		manager3.get_slot(0).is_filled(),
		"scr5_ac8_slot_a_empty_after_double_call_from_both_empty — slot A must be empty after two calls from both-empty state"
	)
	_assert_false(
		manager3.get_slot(1).is_filled(),
		"scr5_ac8_slot_b_empty_after_double_call_from_both_empty — slot B must be empty after two calls from both-empty state"
	)


# ---------------------------------------------------------------------------
# SCR-5-AC-9  any_filled() false after consume regardless of pre-call state
# ---------------------------------------------------------------------------

func test_scr5_ac9_any_filled_false_regardless_of_precall_state() -> void:
	# Both-filled case
	var manager_both: Object = _make_manager()
	if manager_both == null:
		_fail("scr5_ac9_any_filled_both_filled", "MutationSlotManager instance missing; skipping")
		return

	if _require_consume_method(manager_both, "scr5_ac9_any_filled_both_filled"):
		return

	manager_both.fill_next_available("mutation_a")
	manager_both.fill_next_available("mutation_b")
	manager_both.consume_fusion_slots()

	_assert_false(
		manager_both.any_filled(),
		"scr5_ac9_any_filled_false_from_both_filled — any_filled() must be false after consume when both slots were filled"
	)

	# One-filled case
	var manager_one: Object = _make_manager()
	if manager_one == null:
		_fail("scr5_ac9_any_filled_one_filled", "MutationSlotManager instance missing; skipping")
		return

	manager_one.fill_next_available("mutation_a")
	manager_one.consume_fusion_slots()

	_assert_false(
		manager_one.any_filled(),
		"scr5_ac9_any_filled_false_from_one_filled — any_filled() must be false after consume when only one slot was filled"
	)

	# Both-empty case
	var manager_none: Object = _make_manager()
	if manager_none == null:
		_fail("scr5_ac9_any_filled_none_filled", "MutationSlotManager instance missing; skipping")
		return

	manager_none.consume_fusion_slots()

	_assert_false(
		manager_none.any_filled(),
		"scr5_ac9_any_filled_false_from_both_empty — any_filled() must be false after consume when both slots were already empty"
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_slot_consumption_rules.gd ---")
	_pass_count = 0
	_fail_count = 0

	# SCR-1 — consume_fusion_slots() function contract
	test_scr1_ac1_method_exists()
	test_scr1_ac2_callable_void_no_crash()
	test_scr1_ac3_headless_instantiation_no_crash()
	test_scr1_ac4_equivalent_to_clear_all()
	test_scr1_ac5_double_call_idempotent()

	# SCR-2 — All-or-nothing clear rule
	test_scr2_ac1_both_slots_cleared_when_both_filled()
	test_scr2_ac2_any_filled_false_after_both_filled_consume()
	test_scr2_ac3_slot_a_only_filled_both_cleared()
	test_scr2_ac4_slot_b_only_filled_both_cleared()
	test_scr2_ac5_no_partial_clear_from_both_filled()

	# SCR-3 — Re-infection allowed post-fusion
	test_scr3_ac1_first_fill_after_consume_goes_to_slot_a()
	test_scr3_ac2_two_fills_after_consume_respect_fill_order()
	test_scr3_ac3_full_cycle_new_ids_replace_old()
	test_scr3_ac4_multiple_cycles_no_state_accumulation()
	test_scr3_ac5_no_lockout_field_introduced()

	# SCR-4 — Ghost and duplicate prevention
	test_scr4_ac1_slot_a_id_empty_after_consume()
	test_scr4_ac2_slot_b_id_empty_after_consume()
	test_scr4_ac3_slot_a_is_filled_false_after_consume()
	test_scr4_ac4_slot_b_is_filled_false_after_consume()
	test_scr4_ac5_no_ghost_id_on_slot_a()
	test_scr4_ac6_no_ghost_id_on_slot_b()
	test_scr4_ac7_no_pre_fusion_id_after_consume_and_one_fill()
	test_scr4_ac8_no_prior_cycle_id_after_multi_cycle_consume()

	# SCR-5 — Edge cases with fewer than two slots filled
	test_scr5_ac1_one_slot_a_filled_no_crash()
	test_scr5_ac2_slot_a_cleared_after_one_slot_a_filled_consume()
	test_scr5_ac3_slot_b_unmodified_after_one_slot_a_filled_consume()
	test_scr5_ac4_one_slot_b_filled_no_crash()
	test_scr5_ac5_both_empty_after_one_slot_b_filled_consume()
	test_scr5_ac6_both_empty_on_construction_no_crash()
	test_scr5_ac7_both_slots_remain_empty_after_empty_consume()
	test_scr5_ac8_double_call_any_state_no_crash_both_empty()
	test_scr5_ac9_any_filled_false_regardless_of_precall_state()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
