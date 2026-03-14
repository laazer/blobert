# test_slot_consumption_rules_adversarial.gd
#
# Adversarial test suite for the slot consumption rules (consume_fusion_slots).
# Ticket: slot_consumption_rules.md
# Spec:   slot_consumption_rules_spec.md (SCR-1 through SCR-5)
#
# Purpose: Expose coverage gaps, blind spots, and edge-case failures that the
# primary behavioral suite (test_slot_consumption_rules.gd) does not cover.
# Every test here is mapped to a concrete vulnerability category and documents
# WHY the test can expose a real implementation bug.
#
# IMPORTANT — TDD STATE:
# consume_fusion_slots() does NOT exist yet. All invocations use has_method()
# and call() so that the suite parses and runs without crashing even when the
# method is absent. Absence of the method is itself a recorded failure.
#
# Adversarial coverage matrix:
#
# | ID     | Category             | Vulnerability probed                            |
# |--------|---------------------|-------------------------------------------------|
# | ADV-01 | Null/empty          | fill_next_available("") after consume — push_error, no crash, slots stay empty |
# | ADV-02 | Rapid repeat        | 10 successive consume calls — no crash, all slots empty each time               |
# | ADV-03 | Ghost ID            | get_active_mutation_id() == "" (not null, not stale) after consume              |
# | ADV-04 | Ghost ID inversion  | is_filled()==false AND id=="" must hold simultaneously per slot                 |
# | ADV-05 | Fill-after-clear    | New fill IDs after consume must not be contaminated by pre-consume IDs          |
# | ADV-06 | Instance isolation  | Consuming on manager A must not affect manager B                                |
# | ADV-07 | ID uniqueness cycle | Cycle N IDs must not appear in cycle N+1 after consume                         |
# | ADV-08 | Fill count invariant| 3+ fill→consume→fill cycles leave state clean each time                        |
# | ADV-09 | Slot B-only fill    | Abnormal state (slot A empty, slot B filled via clear_slot(0)) handled safely  |
# | ADV-10 | Object identity     | Slot instances are same objects before and after consume (in-place clear)       |
# | ADV-11 | any_filled post     | any_filled() is false after consume regardless of all pre-states               |
# | ADV-12 | Partial-clear mutant| Detect if consume only clears one slot (mutation: clears [0] but not [1])     |
# | ADV-13 | Whitespace ID       | fill_next_available(" ") after consume — must fill (whitespace is valid id)    |
# | ADV-14 | Determinism         | Same sequence produces identical state on two separate manager instances        |
# | ADV-15 | Empty-state consume | consume on fresh manager (both empty) — no error, state unchanged              |
# | ADV-16 | One-slot consume    | consume with only slot A filled — both cleared, no push_error                 |
# | ADV-17 | One-slot consume B  | consume with only slot B filled (via clear_slot(0)) — both cleared            |
# | ADV-18 | Slot count stable   | get_slot_count() is always 2 before, during, and after consume                 |
# | ADV-19 | No hidden fields    | Manager has no _post_fusion, _locked, or equivalent field after consume        |
# | ADV-20 | Large ID stress     | 100-char mutation IDs survive a full fill→consume→fill cycle cleanly           |
# | ADV-21 | Identical IDs cycle | Fill both slots with same ID, consume, verify both cleared to ""               |
# | ADV-22 | Slot access stable  | get_slot(0) and get_slot(1) return non-null after consume                      |
# | ADV-23 | Out-of-range safe   | get_slot(-1) and get_slot(2) return null after consume (no regression)         |
# | ADV-24 | 10-cycle endurance  | 10 full fill→consume cycles — no accumulation, each cycle ends clean          |

class_name SlotConsumptionRulesAdversarialTests
extends Object

const _MANAGER_PATH: String = "res://scripts/mutation/mutation_slot_manager.gd"

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


func _assert_eq(a: Variant, b: Variant, test_name: String) -> void:
	if a == b:
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b))


# Creates a fresh MutationSlotManager instance.
func _new_manager() -> RefCounted:
	var script: GDScript = load(_MANAGER_PATH)
	return script.new()


# Calls consume_fusion_slots() on manager if the method exists.
# Returns true if the call succeeded, false if method is absent.
func _consume(manager: RefCounted) -> bool:
	if not manager.has_method("consume_fusion_slots"):
		return false
	manager.call("consume_fusion_slots")
	return true


# Fills slot A then slot B using fill_next_available.
func _fill_both(manager: RefCounted, id_a: String, id_b: String) -> void:
	manager.fill_next_available(id_a)
	manager.fill_next_available(id_b)


# ---------------------------------------------------------------------------
# Gate: method exists (all downstream tests depend on this)
# ---------------------------------------------------------------------------

func test_adv_method_exists() -> void:
	var manager: RefCounted = _new_manager()
	_assert_true(
		manager.has_method("consume_fusion_slots"),
		"adv-gate — MutationSlotManager has consume_fusion_slots method"
	)


# ---------------------------------------------------------------------------
# ADV-01: fill_next_available("") after consume — must push_error, not crash,
# slots stay empty.
#
# Why this exposes a bug: an implementation that silently ignores empty-string
# fills after consume (rather than calling push_error) could pass the primary
# suite but violate the DSM-2 empty-id contract. A buggy impl that clears the
# push_error guard post-consume would leave both slots in an indeterminate state.
# ---------------------------------------------------------------------------

func test_adv_01_empty_string_fill_after_consume_no_crash_slots_empty() -> void:
	var manager: RefCounted = _new_manager()
	if not _consume(manager):
		_fail("adv-01/a", "consume_fusion_slots method absent — skipping body")
		return
	# Call fill_next_available with empty string — must not crash.
	# push_error is the expected side effect; we cannot intercept it headlessly,
	# but we verify that slots remain empty (the guard prevented the fill).
	manager.fill_next_available("")
	_assert_false(
		manager.get_slot(0).is_filled(),
		"adv-01/a — slot A still empty after fill_next_available('') post-consume"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"adv-01/b — slot B still empty after fill_next_available('') post-consume"
	)
	_assert_false(
		manager.any_filled(),
		"adv-01/c — any_filled() false after empty-string fill attempt post-consume"
	)


# ---------------------------------------------------------------------------
# ADV-02: 10 successive consume calls — no crash, all slots empty each time.
#
# Why this exposes a bug: a non-idempotent implementation that tracks call
# count or sets a flag on the first consume would misbehave on subsequent calls.
# A crash on double-consume would surface here.
# ---------------------------------------------------------------------------

func test_adv_02_rapid_repeated_consume_calls_no_crash() -> void:
	var manager: RefCounted = _new_manager()
	_fill_both(manager, "mut_rapid_a", "mut_rapid_b")
	if not manager.has_method("consume_fusion_slots"):
		_fail("adv-02/a", "consume_fusion_slots method absent")
		return
	for i: int in range(10):
		manager.call("consume_fusion_slots")
		_assert_false(
			manager.get_slot(0).is_filled(),
			"adv-02/slot-a-call-" + str(i + 1) + " — slot A empty after call " + str(i + 1)
		)
		_assert_false(
			manager.get_slot(1).is_filled(),
			"adv-02/slot-b-call-" + str(i + 1) + " — slot B empty after call " + str(i + 1)
		)


# ---------------------------------------------------------------------------
# ADV-03: get_active_mutation_id() returns "" (not null, not stale) after consume.
#
# Why this exposes a bug: MutationSlot.clear() sets _active_mutation_id = "".
# If a buggy implementation uses null or a sentinel like "NONE" for the empty
# state, the equality check == "" fails while is_filled() may still return false,
# creating a ghost-ID inversion. The spec requires strict "" equality (SCR-4).
# ---------------------------------------------------------------------------

func test_adv_03_ghost_id_active_mutation_id_is_empty_string_not_null() -> void:
	var manager: RefCounted = _new_manager()
	_fill_both(manager, "ghost_test_a", "ghost_test_b")
	if not _consume(manager):
		_fail("adv-03/a", "consume_fusion_slots method absent")
		return
	var id0: String = manager.get_slot(0).get_active_mutation_id()
	var id1: String = manager.get_slot(1).get_active_mutation_id()
	_assert_eq(id0, "", "adv-03/a — slot A get_active_mutation_id() == \"\" (not null, not stale)")
	_assert_eq(id1, "", "adv-03/b — slot B get_active_mutation_id() == \"\" (not null, not stale)")
	# Explicitly guard against null (GDScript Variant can sometimes coerce)
	_assert_true(
		typeof(id0) == TYPE_STRING,
		"adv-03/c — slot A get_active_mutation_id() is TYPE_STRING, not null/other"
	)
	_assert_true(
		typeof(id1) == TYPE_STRING,
		"adv-03/d — slot B get_active_mutation_id() is TYPE_STRING, not null/other"
	)


# ---------------------------------------------------------------------------
# ADV-04: Ghost ID inversion — is_filled()==false AND id=="" must hold
# simultaneously per slot after consume.
#
# Why this exposes a bug: a partial implementation could clear _active_mutation_id
# but forget to update is_filled()'s backing state if it were ever decoupled.
# (Currently is_filled() derives from _active_mutation_id, but if a caching
# field were introduced, they could diverge.) Both must be consistent at once.
# ---------------------------------------------------------------------------

func test_adv_04_ghost_id_inversion_both_invariants_simultaneous() -> void:
	var manager: RefCounted = _new_manager()
	_fill_both(manager, "inversion_a", "inversion_b")
	if not _consume(manager):
		_fail("adv-04/a", "consume_fusion_slots method absent")
		return
	var slot0: RefCounted = manager.get_slot(0)
	var slot1: RefCounted = manager.get_slot(1)
	# Slot A: both invariants must hold simultaneously
	var a_not_filled: bool = not slot0.is_filled()
	var a_id_empty: bool = slot0.get_active_mutation_id() == ""
	_assert_true(
		a_not_filled and a_id_empty,
		"adv-04/a — slot A: is_filled()==false AND get_active_mutation_id()==\"\" simultaneously"
	)
	# Slot B: both invariants must hold simultaneously
	var b_not_filled: bool = not slot1.is_filled()
	var b_id_empty: bool = slot1.get_active_mutation_id() == ""
	_assert_true(
		b_not_filled and b_id_empty,
		"adv-04/b — slot B: is_filled()==false AND get_active_mutation_id()==\"\" simultaneously"
	)


# ---------------------------------------------------------------------------
# ADV-05: Fill-after-clear ordering — pre-consume IDs must not contaminate
# new fills.
#
# Why this exposes a bug: if consume_fusion_slots() uses a shallow clear that
# leaves a reference to the old ID in a cache or history field, fill_next_available
# with a new ID might overwrite but the old ID could reappear via get_active_mutation_id.
# ---------------------------------------------------------------------------

func test_adv_05_fill_after_clear_no_id_contamination() -> void:
	var manager: RefCounted = _new_manager()
	_fill_both(manager, "old_a", "old_b")
	if not _consume(manager):
		_fail("adv-05/a", "consume_fusion_slots method absent")
		return
	# Re-fill with new IDs
	manager.fill_next_available("new_c")
	manager.fill_next_available("new_d")
	_assert_eq(
		manager.get_slot(0).get_active_mutation_id(), "new_c",
		"adv-05/a — slot A holds new ID 'new_c', not old 'old_a'"
	)
	_assert_eq(
		manager.get_slot(1).get_active_mutation_id(), "new_d",
		"adv-05/b — slot B holds new ID 'new_d', not old 'old_b'"
	)
	# Verify old IDs are completely gone
	_assert_true(
		manager.get_slot(0).get_active_mutation_id() != "old_a",
		"adv-05/c — slot A does not contain pre-consume ID 'old_a'"
	)
	_assert_true(
		manager.get_slot(1).get_active_mutation_id() != "old_b",
		"adv-05/d — slot B does not contain pre-consume ID 'old_b'"
	)


# ---------------------------------------------------------------------------
# ADV-06: Instance isolation — consuming on manager A must not affect manager B.
#
# Why this exposes a bug: if MutationSlotManager uses any class-level (static)
# state or if the _slots array is accidentally shared via a preloaded script
# instance rather than being freshly allocated per _init(), one instance's
# consume can corrupt another.
# ---------------------------------------------------------------------------

func test_adv_06_instance_isolation_consume_on_a_does_not_affect_b() -> void:
	var manager_a: RefCounted = _new_manager()
	var manager_b: RefCounted = _new_manager()
	_fill_both(manager_a, "iso_a1", "iso_a2")
	_fill_both(manager_b, "iso_b1", "iso_b2")
	if not _consume(manager_a):
		_fail("adv-06/a", "consume_fusion_slots method absent on manager_a")
		return
	# manager_a slots must be empty
	_assert_false(
		manager_a.get_slot(0).is_filled(),
		"adv-06/a — manager_a slot A empty after consume"
	)
	_assert_false(
		manager_a.get_slot(1).is_filled(),
		"adv-06/b — manager_a slot B empty after consume"
	)
	# manager_b slots must be completely unaffected
	_assert_true(
		manager_b.get_slot(0).is_filled(),
		"adv-06/c — manager_b slot A still filled after consuming manager_a"
	)
	_assert_true(
		manager_b.get_slot(1).is_filled(),
		"adv-06/d — manager_b slot B still filled after consuming manager_a"
	)
	_assert_eq(
		manager_b.get_slot(0).get_active_mutation_id(), "iso_b1",
		"adv-06/e — manager_b slot A ID unchanged ('iso_b1')"
	)
	_assert_eq(
		manager_b.get_slot(1).get_active_mutation_id(), "iso_b2",
		"adv-06/f — manager_b slot B ID unchanged ('iso_b2')"
	)


# ---------------------------------------------------------------------------
# ADV-07: ID uniqueness across cycles — cycle N IDs must not appear in
# cycle N+1 after consume.
#
# Why this exposes a bug: a history buffer or reference-counted slot object
# that is not properly zeroed could carry the prior cycle's ID into the next.
# ---------------------------------------------------------------------------

func test_adv_07_id_uniqueness_across_fusion_cycles() -> void:
	var manager: RefCounted = _new_manager()
	if not manager.has_method("consume_fusion_slots"):
		_fail("adv-07/a", "consume_fusion_slots method absent")
		return
	# Cycle 1
	_fill_both(manager, "x1", "x2")
	manager.call("consume_fusion_slots")
	# Cycle 2
	_fill_both(manager, "x3", "x4")
	manager.call("consume_fusion_slots")
	# After cycle 2 consume: neither x1, x2, x3, x4 should appear
	_assert_eq(manager.get_slot(0).get_active_mutation_id(), "",
		"adv-07/a — slot A empty after cycle 2 consume (no x1/x3 residue)")
	_assert_eq(manager.get_slot(1).get_active_mutation_id(), "",
		"adv-07/b — slot B empty after cycle 2 consume (no x2/x4 residue)")
	_assert_true(
		manager.get_slot(0).get_active_mutation_id() != "x1" and
		manager.get_slot(0).get_active_mutation_id() != "x3",
		"adv-07/c — slot A holds no ID from any prior cycle"
	)
	_assert_true(
		manager.get_slot(1).get_active_mutation_id() != "x2" and
		manager.get_slot(1).get_active_mutation_id() != "x4",
		"adv-07/d — slot B holds no ID from any prior cycle"
	)


# ---------------------------------------------------------------------------
# ADV-08: Fill count invariant — 3 full fill→consume cycles leave state clean.
#
# Why this exposes a bug: if internal state accumulates (e.g. a counter that
# prevents refill after N cycles, or a list that grows unbounded), the 3rd
# cycle would deviate from the 1st. Tests verify clean state after each cycle.
# ---------------------------------------------------------------------------

func test_adv_08_fill_count_invariant_three_cycles() -> void:
	var manager: RefCounted = _new_manager()
	if not manager.has_method("consume_fusion_slots"):
		_fail("adv-08/start", "consume_fusion_slots method absent")
		return
	var cycle_ids: Array[Array] = [
		["cycle1_a", "cycle1_b"],
		["cycle2_a", "cycle2_b"],
		["cycle3_a", "cycle3_b"],
	]
	for i: int in range(cycle_ids.size()):
		var ids: Array = cycle_ids[i]
		var label: String = "adv-08/cycle" + str(i + 1)
		# Fill both slots
		_fill_both(manager, ids[0], ids[1])
		_assert_true(manager.get_slot(0).is_filled(),
			label + "/pre-consume — slot A filled")
		_assert_true(manager.get_slot(1).is_filled(),
			label + "/pre-consume — slot B filled")
		# Consume
		manager.call("consume_fusion_slots")
		# Verify clean post-consume state
		_assert_false(manager.get_slot(0).is_filled(),
			label + "/post-consume — slot A empty")
		_assert_false(manager.get_slot(1).is_filled(),
			label + "/post-consume — slot B empty")
		_assert_eq(manager.get_slot(0).get_active_mutation_id(), "",
			label + "/post-consume — slot A id is empty string")
		_assert_eq(manager.get_slot(1).get_active_mutation_id(), "",
			label + "/post-consume — slot B id is empty string")
		_assert_false(manager.any_filled(),
			label + "/post-consume — any_filled() is false")


# ---------------------------------------------------------------------------
# ADV-09: Slot B-only fill (abnormal order via clear_slot(0) after fill A).
# After consuming a manager where only slot B is filled, both must be empty.
#
# Why this exposes a bug: a consume implementation that only iterates from
# index 0 and stops when it finds the first empty slot would skip slot B.
# ---------------------------------------------------------------------------

func test_adv_09_slot_b_only_filled_consume_clears_both() -> void:
	var manager: RefCounted = _new_manager()
	# Fill slot A then clear it manually, leaving only slot B filled
	manager.fill_next_available("only_b_mutation")
	manager.fill_next_available("slot_b_value")
	manager.clear_slot(0)  # Now only slot B is filled
	_assert_false(manager.get_slot(0).is_filled(), "adv-09/setup — slot A cleared")
	_assert_true(manager.get_slot(1).is_filled(), "adv-09/setup — slot B still filled")
	if not _consume(manager):
		_fail("adv-09/a", "consume_fusion_slots method absent")
		return
	_assert_false(
		manager.get_slot(0).is_filled(),
		"adv-09/a — slot A empty after consume (was already empty)"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"adv-09/b — slot B empty after consume (was the only filled slot)"
	)
	_assert_eq(manager.get_slot(1).get_active_mutation_id(), "",
		"adv-09/c — slot B get_active_mutation_id() == \"\" after consume")


# ---------------------------------------------------------------------------
# ADV-10: Object identity — slot instances are the same objects before and
# after consume (in-place clear, not slot replacement).
#
# Why this exposes a bug: if consume_fusion_slots() replaces slot instances
# (e.g., _slots[0] = MutationSlot.new()) instead of calling clear() on the
# existing instances, any external reference to the old slot objects becomes
# stale. Callers holding a get_slot() reference would see a zombie object.
# ---------------------------------------------------------------------------

func test_adv_10_slot_object_identity_preserved_after_consume() -> void:
	var manager: RefCounted = _new_manager()
	var slot0_before: RefCounted = manager.get_slot(0)
	var slot1_before: RefCounted = manager.get_slot(1)
	_fill_both(manager, "identity_a", "identity_b")
	if not _consume(manager):
		_fail("adv-10/a", "consume_fusion_slots method absent")
		return
	var slot0_after: RefCounted = manager.get_slot(0)
	var slot1_after: RefCounted = manager.get_slot(1)
	_assert_true(
		slot0_before == slot0_after,
		"adv-10/a — slot A object identity preserved after consume"
	)
	_assert_true(
		slot1_before == slot1_after,
		"adv-10/b — slot B object identity preserved after consume"
	)


# ---------------------------------------------------------------------------
# ADV-11: any_filled() is false after consume in all three pre-states:
# both filled, slot A only, slot B only.
#
# Why this exposes a bug: a buggy any_filled() that caches its result or a
# consume impl that clears slot data but not the any_filled backing state
# would fail this check for at least one pre-state.
# ---------------------------------------------------------------------------

func test_adv_11_any_filled_false_after_consume_all_prestates() -> void:
	if not _new_manager().has_method("consume_fusion_slots"):
		_fail("adv-11/a", "consume_fusion_slots method absent")
		return
	# Pre-state 1: both filled
	var m1: RefCounted = _new_manager()
	_fill_both(m1, "af_a", "af_b")
	m1.call("consume_fusion_slots")
	_assert_false(m1.any_filled(), "adv-11/a — any_filled() false after consume (both pre-filled)")

	# Pre-state 2: slot A only filled
	var m2: RefCounted = _new_manager()
	m2.fill_next_available("af_a_only")
	m2.call("consume_fusion_slots")
	_assert_false(m2.any_filled(), "adv-11/b — any_filled() false after consume (slot A pre-filled)")

	# Pre-state 3: slot B only filled (via manual clear of A)
	var m3: RefCounted = _new_manager()
	m3.fill_next_available("af_b1")
	m3.fill_next_available("af_b2")
	m3.clear_slot(0)
	m3.call("consume_fusion_slots")
	_assert_false(m3.any_filled(), "adv-11/c — any_filled() false after consume (slot B pre-filled)")

	# Pre-state 4: both already empty
	var m4: RefCounted = _new_manager()
	m4.call("consume_fusion_slots")
	_assert_false(m4.any_filled(), "adv-11/d — any_filled() false after consume (both pre-empty)")


# ---------------------------------------------------------------------------
# ADV-12: Partial-clear mutation detection — verify BOTH slots are cleared,
# not just one.
#
# Why this exposes a bug: if consume_fusion_slots() reimplements clearing
# as `_slots[0].clear()` (forgetting index 1), or vice versa, slot B or A
# would retain the old mutation ID. This is a direct mutation test.
# ---------------------------------------------------------------------------

func test_adv_12_both_slots_individually_empty_not_just_any_filled() -> void:
	var manager: RefCounted = _new_manager()
	_fill_both(manager, "partial_a", "partial_b")
	if not _consume(manager):
		_fail("adv-12/a", "consume_fusion_slots method absent")
		return
	# Check each slot independently — do NOT rely only on any_filled()
	_assert_false(
		manager.get_slot(0).is_filled(),
		"adv-12/a — slot A (index 0) individually confirmed empty after consume"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"adv-12/b — slot B (index 1) individually confirmed empty after consume"
	)
	_assert_eq(manager.get_slot(0).get_active_mutation_id(), "",
		"adv-12/c — slot A id == \"\" (not just is_filled())")
	_assert_eq(manager.get_slot(1).get_active_mutation_id(), "",
		"adv-12/d — slot B id == \"\" (not just is_filled())")


# ---------------------------------------------------------------------------
# ADV-13: Whitespace ID after consume — fill_next_available(" ") is a valid
# non-empty ID and must fill slot A normally.
#
# Why this exposes a bug: a consume implementation that leaves a post-fusion
# guard might reject all fills including valid whitespace-only IDs. Whitespace
# strings are not "" so the push_error guard must not fire.
# ---------------------------------------------------------------------------

func test_adv_13_whitespace_id_fills_slot_a_after_consume() -> void:
	var manager: RefCounted = _new_manager()
	if not _consume(manager):
		_fail("adv-13/a", "consume_fusion_slots method absent")
		return
	manager.fill_next_available(" ")
	_assert_true(
		manager.get_slot(0).is_filled(),
		"adv-13/a — slot A fills with whitespace ID after consume (whitespace is valid)"
	)
	_assert_eq(
		manager.get_slot(0).get_active_mutation_id(), " ",
		"adv-13/b — slot A holds exact whitespace ID ' '"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"adv-13/c — slot B remains empty (whitespace fill goes to slot A)"
	)


# ---------------------------------------------------------------------------
# ADV-14: Determinism — same fill→consume sequence produces identical state
# on two separate manager instances.
#
# Why this exposes a bug: if consume uses any random, time-based, or shared
# mutable state (even accidentally via a preload singleton), outputs diverge.
# ---------------------------------------------------------------------------

func test_adv_14_determinism_identical_state_on_two_instances() -> void:
	var m1: RefCounted = _new_manager()
	var m2: RefCounted = _new_manager()
	if not m1.has_method("consume_fusion_slots"):
		_fail("adv-14/a", "consume_fusion_slots method absent")
		return
	_fill_both(m1, "det_a", "det_b")
	_fill_both(m2, "det_a", "det_b")
	m1.call("consume_fusion_slots")
	m2.call("consume_fusion_slots")
	_assert_eq(
		m1.get_slot(0).is_filled(), m2.get_slot(0).is_filled(),
		"adv-14/a — slot A is_filled() identical on both instances"
	)
	_assert_eq(
		m1.get_slot(1).is_filled(), m2.get_slot(1).is_filled(),
		"adv-14/b — slot B is_filled() identical on both instances"
	)
	_assert_eq(
		m1.get_slot(0).get_active_mutation_id(),
		m2.get_slot(0).get_active_mutation_id(),
		"adv-14/c — slot A mutation id identical on both instances"
	)
	_assert_eq(
		m1.get_slot(1).get_active_mutation_id(),
		m2.get_slot(1).get_active_mutation_id(),
		"adv-14/d — slot B mutation id identical on both instances"
	)


# ---------------------------------------------------------------------------
# ADV-15: Empty-state consume — consume on a fresh manager (both already
# empty) must not crash, must not push_error, state stays empty.
#
# Why this exposes a bug: a guard that short-circuits when no slots are filled
# could work, but any guard that calls push_error or panics violates SCR-5-AC-6.
# ---------------------------------------------------------------------------

func test_adv_15_consume_on_fresh_empty_manager_no_crash() -> void:
	var manager: RefCounted = _new_manager()
	# Both slots are already empty from construction
	_assert_false(manager.any_filled(), "adv-15/setup — fresh manager any_filled()=false")
	if not _consume(manager):
		_fail("adv-15/a", "consume_fusion_slots method absent")
		return
	_assert_false(manager.get_slot(0).is_filled(),
		"adv-15/a — slot A remains empty after consume on fresh manager")
	_assert_false(manager.get_slot(1).is_filled(),
		"adv-15/b — slot B remains empty after consume on fresh manager")
	_assert_eq(manager.get_slot(0).get_active_mutation_id(), "",
		"adv-15/c — slot A id still \"\" after consume on fresh manager")
	_assert_eq(manager.get_slot(1).get_active_mutation_id(), "",
		"adv-15/d — slot B id still \"\" after consume on fresh manager")


# ---------------------------------------------------------------------------
# ADV-16: One-slot consume (slot A only) — both cleared, no push_error.
# SCR-5-AC-1, SCR-5-AC-2, SCR-5-AC-3.
#
# Why this exposes a bug: a consume implementation that pre-checks any_filled()
# or both_filled() and refuses to clear when the pre-condition isn't "both full"
# would leave slot A with "mutation_a" after the call, violating the spec.
# ---------------------------------------------------------------------------

func test_adv_16_one_slot_only_slot_a_filled_both_cleared() -> void:
	var manager: RefCounted = _new_manager()
	manager.fill_next_available("only_slot_a")
	_assert_true(manager.get_slot(0).is_filled(), "adv-16/setup — slot A filled")
	_assert_false(manager.get_slot(1).is_filled(), "adv-16/setup — slot B empty")
	if not _consume(manager):
		_fail("adv-16/a", "consume_fusion_slots method absent")
		return
	_assert_false(manager.get_slot(0).is_filled(),
		"adv-16/a — slot A empty after consume (was only filled slot)")
	_assert_false(manager.get_slot(1).is_filled(),
		"adv-16/b — slot B empty after consume (was already empty, must remain empty)")
	_assert_eq(manager.get_slot(0).get_active_mutation_id(), "",
		"adv-16/c — slot A get_active_mutation_id() == \"\"")
	_assert_eq(manager.get_slot(1).get_active_mutation_id(), "",
		"adv-16/d — slot B get_active_mutation_id() == \"\"")


# ---------------------------------------------------------------------------
# ADV-17: One-slot consume (slot B only via clear_slot(0)) — both cleared.
# SCR-5-AC-4, SCR-5-AC-5.
#
# Why this exposes a bug: a consume that iterates `for slot in _slots` and
# short-circuits on the first empty slot (index 0) would leave slot B uncleaned.
# This is the most dangerous partial-clear pattern for the B-only case.
# ---------------------------------------------------------------------------

func test_adv_17_one_slot_only_slot_b_filled_both_cleared() -> void:
	var manager: RefCounted = _new_manager()
	manager.fill_next_available("fill_for_a")
	manager.fill_next_available("only_slot_b")
	manager.clear_slot(0)  # Abnormal: leave only slot B filled
	_assert_false(manager.get_slot(0).is_filled(), "adv-17/setup — slot A cleared")
	_assert_true(manager.get_slot(1).is_filled(), "adv-17/setup — slot B filled with only_slot_b")
	if not _consume(manager):
		_fail("adv-17/a", "consume_fusion_slots method absent")
		return
	_assert_false(manager.get_slot(0).is_filled(),
		"adv-17/a — slot A still empty after consume (was already empty)")
	_assert_false(manager.get_slot(1).is_filled(),
		"adv-17/b — slot B empty after consume (was the only filled slot)")
	_assert_eq(manager.get_slot(1).get_active_mutation_id(), "",
		"adv-17/c — slot B get_active_mutation_id() == \"\" (stale 'only_slot_b' gone)")


# ---------------------------------------------------------------------------
# ADV-18: get_slot_count() always returns 2 before, during (simulated by
# checking before and after), and after consume.
#
# Why this exposes a bug: a consume implementation that removes or replaces
# slot instances in _slots (e.g. _slots.clear() then _slots.append(...)) could
# momentarily or permanently change the slot count if allocation fails.
# ---------------------------------------------------------------------------

func test_adv_18_slot_count_stable_before_and_after_consume() -> void:
	var manager: RefCounted = _new_manager()
	_assert_eq(manager.get_slot_count(), 2, "adv-18/a — slot count is 2 before any fills")
	_fill_both(manager, "count_a", "count_b")
	_assert_eq(manager.get_slot_count(), 2, "adv-18/b — slot count is 2 after filling both slots")
	if not _consume(manager):
		_fail("adv-18/c", "consume_fusion_slots method absent")
		return
	_assert_eq(manager.get_slot_count(), 2, "adv-18/c — slot count is 2 after consume")
	# Fill again and check once more
	_fill_both(manager, "count_c", "count_d")
	_assert_eq(manager.get_slot_count(), 2, "adv-18/d — slot count is 2 after refill post-consume")


# ---------------------------------------------------------------------------
# ADV-19: No hidden fields — manager must not expose _post_fusion, _locked,
# or equivalent field after consume.
# SCR-3-AC-5.
#
# Why this exposes a bug: if the implementer adds a lock-out or cooldown field
# to MutationSlotManager, fill_next_available would silently no-op post-fusion,
# breaking re-infection. We test that fill_next_available DOES work after consume
# (which indirectly detects any lock-out state).
# ---------------------------------------------------------------------------

func test_adv_19_no_hidden_lockout_state_fill_works_after_consume() -> void:
	var manager: RefCounted = _new_manager()
	_fill_both(manager, "pre_lock_a", "pre_lock_b")
	if not _consume(manager):
		_fail("adv-19/a", "consume_fusion_slots method absent")
		return
	# If any hidden lock state exists, this call would be blocked or no-op silently
	manager.fill_next_available("post_lock_test")
	_assert_true(
		manager.get_slot(0).is_filled(),
		"adv-19/a — fill_next_available works after consume (no lock-out state)"
	)
	_assert_eq(
		manager.get_slot(0).get_active_mutation_id(), "post_lock_test",
		"adv-19/b — slot A holds 'post_lock_test' after consume (no hidden flag blocking fill)"
	)
	# Verify no unexpected field exists by checking slot B was not affected
	_assert_false(
		manager.get_slot(1).is_filled(),
		"adv-19/c — slot B stays empty (fill went to A as expected with no state corruption)"
	)


# ---------------------------------------------------------------------------
# ADV-20: Large mutation ID (100 chars) — consume clears it cleanly.
#
# Why this exposes a bug: if a string-clearing implementation has a length
# check or truncation bug, a long ID might survive as a ghost value.
# ---------------------------------------------------------------------------

func test_adv_20_large_mutation_id_cleared_cleanly_by_consume() -> void:
	var large_id: String = "mutation_" + "x".repeat(91)  # 100 chars total
	var manager: RefCounted = _new_manager()
	_fill_both(manager, large_id, large_id + "_b")
	if not _consume(manager):
		_fail("adv-20/a", "consume_fusion_slots method absent")
		return
	_assert_eq(manager.get_slot(0).get_active_mutation_id(), "",
		"adv-20/a — slot A cleared of 100-char ID")
	_assert_eq(manager.get_slot(1).get_active_mutation_id(), "",
		"adv-20/b — slot B cleared of large variant ID")
	_assert_false(manager.get_slot(0).is_filled(),
		"adv-20/c — slot A is_filled() false after clearing large ID")
	_assert_false(manager.get_slot(1).is_filled(),
		"adv-20/d — slot B is_filled() false after clearing large ID")


# ---------------------------------------------------------------------------
# ADV-21: Identical IDs in both slots — consume clears both to "".
#
# Why this exposes a bug: a deduplication guard that might attempt to remove
# duplicate mutation IDs before clearing could skip one slot if both hold the
# same ID. Both must independently become "".
# ---------------------------------------------------------------------------

func test_adv_21_identical_ids_in_both_slots_both_cleared() -> void:
	var manager: RefCounted = _new_manager()
	# fill_next_available fills A first, then B is overwritten when both full.
	# Fill A, then overwrite B with same ID.
	manager.fill_next_available("dup_mutation")
	manager.fill_next_available("dup_filler")   # fills slot B
	# Now overwrite slot B to have the same ID as slot A
	manager.fill_next_available("dup_mutation") # both full: overwrites slot B
	_assert_eq(manager.get_slot(0).get_active_mutation_id(), "dup_mutation",
		"adv-21/setup — slot A holds 'dup_mutation'")
	_assert_eq(manager.get_slot(1).get_active_mutation_id(), "dup_mutation",
		"adv-21/setup — slot B also holds 'dup_mutation' (same ID)")
	if not _consume(manager):
		_fail("adv-21/a", "consume_fusion_slots method absent")
		return
	_assert_eq(manager.get_slot(0).get_active_mutation_id(), "",
		"adv-21/a — slot A cleared to \"\" even when both slots had same ID")
	_assert_eq(manager.get_slot(1).get_active_mutation_id(), "",
		"adv-21/b — slot B cleared to \"\" even when both slots had same ID")


# ---------------------------------------------------------------------------
# ADV-22: get_slot(0) and get_slot(1) return non-null objects after consume.
# Slot instances must remain accessible.
#
# Why this exposes a bug: if consume replaces slot instances with null or
# removes them from _slots, get_slot() would return null, crashing callers.
# ---------------------------------------------------------------------------

func test_adv_22_get_slot_returns_non_null_after_consume() -> void:
	var manager: RefCounted = _new_manager()
	_fill_both(manager, "nonnull_a", "nonnull_b")
	if not _consume(manager):
		_fail("adv-22/a", "consume_fusion_slots method absent")
		return
	var slot0: RefCounted = manager.get_slot(0)
	var slot1: RefCounted = manager.get_slot(1)
	_assert_true(slot0 != null, "adv-22/a — get_slot(0) non-null after consume")
	_assert_true(slot1 != null, "adv-22/b — get_slot(1) non-null after consume")
	# Verify the returned objects are still functional
	_assert_true(slot0.has_method("is_filled"), "adv-22/c — get_slot(0) still has is_filled()")
	_assert_true(slot1.has_method("is_filled"), "adv-22/d — get_slot(1) still has is_filled()")


# ---------------------------------------------------------------------------
# ADV-23: Out-of-range slot access after consume does not crash.
# get_slot(-1) and get_slot(2) must return null (regression check).
#
# Why this exposes a bug: if consume modifies _slots in a way that changes
# its bounds (e.g., appending or inserting), an out-of-range access that
# previously returned null might now return a value or crash.
# ---------------------------------------------------------------------------

func test_adv_23_out_of_range_slot_access_after_consume_returns_null() -> void:
	var manager: RefCounted = _new_manager()
	_fill_both(manager, "oob_a", "oob_b")
	if not _consume(manager):
		_fail("adv-23/a", "consume_fusion_slots method absent")
		return
	_assert_true(manager.get_slot(-1) == null,
		"adv-23/a — get_slot(-1) returns null after consume (no index regression)")
	_assert_true(manager.get_slot(2) == null,
		"adv-23/b — get_slot(2) returns null after consume (no index regression)")


# ---------------------------------------------------------------------------
# ADV-24: 10-cycle endurance — 10 full fill→consume cycles leave state clean.
# No state accumulation or performance degradation.
#
# Why this exposes a bug: if any internal array grows unbounded, or if slot
# references accumulate, the 10th cycle might behave differently from the 1st.
# ---------------------------------------------------------------------------

func test_adv_24_ten_cycle_endurance_no_state_accumulation() -> void:
	var manager: RefCounted = _new_manager()
	if not manager.has_method("consume_fusion_slots"):
		_fail("adv-24/start", "consume_fusion_slots method absent")
		return
	for i: int in range(10):
		var id_a: String = "endurance_a_" + str(i)
		var id_b: String = "endurance_b_" + str(i)
		_fill_both(manager, id_a, id_b)
		manager.call("consume_fusion_slots")
		# After each cycle: fully clean state
		_assert_false(manager.get_slot(0).is_filled(),
			"adv-24/cycle" + str(i + 1) + " — slot A empty after consume")
		_assert_false(manager.get_slot(1).is_filled(),
			"adv-24/cycle" + str(i + 1) + " — slot B empty after consume")
		_assert_false(manager.any_filled(),
			"adv-24/cycle" + str(i + 1) + " — any_filled() false after consume")
		_assert_eq(manager.get_slot_count(), 2,
			"adv-24/cycle" + str(i + 1) + " — slot count stable at 2")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_slot_consumption_rules_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_adv_method_exists()
	test_adv_01_empty_string_fill_after_consume_no_crash_slots_empty()
	test_adv_02_rapid_repeated_consume_calls_no_crash()
	test_adv_03_ghost_id_active_mutation_id_is_empty_string_not_null()
	test_adv_04_ghost_id_inversion_both_invariants_simultaneous()
	test_adv_05_fill_after_clear_no_id_contamination()
	test_adv_06_instance_isolation_consume_on_a_does_not_affect_b()
	test_adv_07_id_uniqueness_across_fusion_cycles()
	test_adv_08_fill_count_invariant_three_cycles()
	test_adv_09_slot_b_only_filled_consume_clears_both()
	test_adv_10_slot_object_identity_preserved_after_consume()
	test_adv_11_any_filled_false_after_consume_all_prestates()
	test_adv_12_both_slots_individually_empty_not_just_any_filled()
	test_adv_13_whitespace_id_fills_slot_a_after_consume()
	test_adv_14_determinism_identical_state_on_two_instances()
	test_adv_15_consume_on_fresh_empty_manager_no_crash()
	test_adv_16_one_slot_only_slot_a_filled_both_cleared()
	test_adv_17_one_slot_only_slot_b_filled_both_cleared()
	test_adv_18_slot_count_stable_before_and_after_consume()
	test_adv_19_no_hidden_lockout_state_fill_works_after_consume()
	test_adv_20_large_mutation_id_cleared_cleanly_by_consume()
	test_adv_21_identical_ids_in_both_slots_both_cleared()
	test_adv_22_get_slot_returns_non_null_after_consume()
	test_adv_23_out_of_range_slot_access_after_consume_returns_null()
	test_adv_24_ten_cycle_endurance_no_state_accumulation()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
