#
# test_mutation_slot_system_dual_adversarial.gd
#
# Adversarial tests for the dual-slot MutationSlotManager.
# Spec: two_mutation_slots_spec.md
#
# Covers edge cases: null/empty IDs, out-of-range indices, simultaneous fills,
# clear-all then refill, fill-after-full, manager isolation, bogus resolver arg.
#

class_name MutationSlotSystemDualAdversarialTests
extends Object


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
# Empty-string guard (DSM-2 empty-string rule)
# ---------------------------------------------------------------------------

func test_fill_empty_string_leaves_slots_empty() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("fill_next_available"):
		_fail("adv_empty_str_no_fill", "manager missing; skipping")
		return
	manager.fill_next_available("")
	_assert_false(manager.any_filled(),
		"adv_empty_str_no_fill — fill_next_available('') must not fill any slot")


func test_fill_empty_string_on_partially_filled_manager_does_not_corrupt() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("fill_next_available"):
		_fail("adv_empty_str_partial", "manager missing; skipping")
		return
	manager.fill_next_available("mutation_a")
	var id_before: String = manager.get_slot(0).get_active_mutation_id()
	manager.fill_next_available("")
	var id_after: String = manager.get_slot(0).get_active_mutation_id()
	_assert_eq_string(id_before, id_after,
		"adv_empty_str_partial — fill('') does not overwrite existing slot A content")
	_assert_false(manager.get_slot(1).is_filled(),
		"adv_empty_str_partial_b_empty — slot B remains empty after fill('') when slot A is filled")


# ---------------------------------------------------------------------------
# Repeated fills of same slot
# ---------------------------------------------------------------------------

func test_repeated_fills_slot_a_only_stays_in_slot_a() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("fill_next_available"):
		_fail("adv_repeated_fill_a", "manager missing; skipping")
		return
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	# Both full — slot B overwritten, slot A preserved
	manager.fill_next_available("mutation_c")
	manager.fill_next_available("mutation_d")
	_assert_eq_string("mutation_a", manager.get_slot(0).get_active_mutation_id(),
		"adv_repeated_fill_slot_a_frozen — slot A never overwritten by fill_next_available once full")
	_assert_eq_string("mutation_d", manager.get_slot(1).get_active_mutation_id(),
		"adv_repeated_fill_slot_b_last_wins — slot B takes the last fill")


# ---------------------------------------------------------------------------
# Simultaneous fill (two managers, one per call)
# ---------------------------------------------------------------------------

func test_two_managers_do_not_share_state() -> void:
	var m1: Object = _make_manager()
	var m2: Object = _make_manager()
	if m1 == null or m2 == null:
		_fail("adv_isolation", "manager missing; skipping")
		return
	m1.fill_next_available("mutation_x")
	_assert_false(m2.any_filled(),
		"adv_isolation_m2_empty — filling m1 does not affect m2")
	_assert_eq_string("", m2.get_slot(0).get_active_mutation_id(),
		"adv_isolation_m2_slot_a_empty — m2 slot A unaffected by m1 fill")


func test_manager_isolates_from_cleared_sibling() -> void:
	var m1: Object = _make_manager()
	var m2: Object = _make_manager()
	if m1 == null or m2 == null:
		_fail("adv_isolation_clear", "manager missing; skipping")
		return
	m1.fill_next_available("mutation_x")
	m1.fill_next_available("mutation_y")
	m1.clear_all()
	m2.fill_next_available("mutation_z")
	_assert_false(m1.any_filled(), "adv_isolation_clear_m1_empty — m1 cleared independently")
	_assert_true(m2.any_filled(), "adv_isolation_clear_m2_filled — m2 unaffected by m1 clear")


# ---------------------------------------------------------------------------
# Clear-all then refill
# ---------------------------------------------------------------------------

func test_clear_all_then_refill_starts_fresh() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("fill_next_available") or not manager.has_method("clear_all"):
		_fail("adv_clear_refill", "manager API missing; skipping")
		return
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	manager.clear_all()
	manager.fill_next_available("mutation_new")
	_assert_eq_string("mutation_new", manager.get_slot(0).get_active_mutation_id(),
		"adv_clear_refill_slot_a — after clear_all, next fill goes to slot A")
	_assert_false(manager.get_slot(1).is_filled(),
		"adv_clear_refill_slot_b_empty — after clear_all, slot B remains empty on first refill")


func test_repeated_clear_all_is_idempotent() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("clear_all"):
		_fail("adv_clear_all_idempotent", "manager API missing; skipping")
		return
	manager.clear_all()
	manager.clear_all()
	manager.clear_all()
	_assert_false(manager.any_filled(),
		"adv_clear_all_idempotent — repeated clear_all() on empty manager does not crash and leaves empty")


# ---------------------------------------------------------------------------
# Fill-after-full edge cases
# ---------------------------------------------------------------------------

func test_fill_after_full_preserves_slot_a_and_overwrites_slot_b() -> void:
	var manager: Object = _make_manager()
	if manager == null or not manager.has_method("fill_next_available"):
		_fail("adv_fill_after_full", "manager API missing; skipping")
		return
	for i in range(5):
		manager.fill_next_available("round_" + str(i))
	# After 5 fills: slot A = round_0, slot B = round_4
	_assert_eq_string("round_0", manager.get_slot(0).get_active_mutation_id(),
		"adv_fill_after_full_slot_a — slot A always holds the very first fill")
	_assert_eq_string("round_4", manager.get_slot(1).get_active_mutation_id(),
		"adv_fill_after_full_slot_b — slot B holds the last fill when repeatedly overwriting")


# ---------------------------------------------------------------------------
# DSM-6 — Bogus object in resolver
# ---------------------------------------------------------------------------

func test_resolver_bogus_slot_arg_no_crash() -> void:
	var resolver: Object = _make_resolver()
	var inv: Object = _make_inventory()
	var esm: Object = _make_esm()
	if resolver == null or inv == null or esm == null:
		_fail("adv_bogus_slot", "dependencies missing; skipping")
		return
	esm.apply_weaken_event()
	esm.apply_infection_event()
	# Bogus object: has neither set_active_mutation_id nor fill_next_available
	var bogus := RefCounted.new()
	resolver.resolve_absorb(esm, inv, bogus)
	_assert_eq_string("dead", esm.get_state(),
		"adv_bogus_slot_esm_dies — ESM still reaches dead state with bogus slot arg")


# ---------------------------------------------------------------------------
# DSM-5 — Backward-compat: single-slot test suite must not break
# ---------------------------------------------------------------------------

func test_mutation_slot_gd_api_is_frozen() -> void:
	var slot_script: GDScript = load("res://scripts/mutation/mutation_slot.gd") as GDScript
	if slot_script == null:
		_fail("adv_frozen_api", "mutation_slot.gd not found")
		return
	var slot: Object = slot_script.new()
	_assert_true(
		slot.has_method("is_filled") and slot.has_method("get_active_mutation_id")
		and slot.has_method("set_active_mutation_id") and slot.has_method("clear"),
		"adv_frozen_api — MutationSlot API unchanged (is_filled, get_active_mutation_id, set_active_mutation_id, clear)"
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_mutation_slot_system_dual_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Empty-string guard
	test_fill_empty_string_leaves_slots_empty()
	test_fill_empty_string_on_partially_filled_manager_does_not_corrupt()

	# Repeated fills
	test_repeated_fills_slot_a_only_stays_in_slot_a()

	# Manager isolation
	test_two_managers_do_not_share_state()
	test_manager_isolates_from_cleared_sibling()

	# Clear-all then refill
	test_clear_all_then_refill_starts_fresh()
	test_repeated_clear_all_is_idempotent()

	# Fill-after-full
	test_fill_after_full_preserves_slot_a_and_overwrites_slot_b()

	# Bogus resolver arg
	test_resolver_bogus_slot_arg_no_crash()

	# Backward compat
	test_mutation_slot_gd_api_is_frozen()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
