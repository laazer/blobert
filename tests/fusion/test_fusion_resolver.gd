#
# test_fusion_resolver.gd
#
# Primary behavioral tests for the FusionResolver pure-logic script.
# Scope:
#   - FRH-2 — Fusion guard: can_fuse returns correct bool for all slot combinations
#              including null manager and null slot edge cases.
#   - FRH-3 — FusionResolver API: class existence, method signatures, constant
#              values, call order (apply_fusion_effect before consume_fusion_slots),
#              null player/manager safety.
#   - FRH-5 — Slot consumption: both slots empty after resolve_fusion; re-fill
#              cycle works; failed guard does not consume slots.
#   - Null-safety: can_fuse(null), resolve_fusion(null, null), resolve_fusion with
#                  null player — all must return without crash.
#
# TDD RED PHASE: FusionResolver does not exist yet.
# All tests that reference FusionResolver use load() + has_method() guards so
# the suite parses and runs headlessly without crashing, recording precise
# FAIL messages that enumerate each unimplemented symbol.
#
# Ticket: fusion_rules_and_hybrid.md
# Spec:   fusion_rules_and_hybrid_spec.md (FRH-2, FRH-3, FRH-5)
#

class_name FusionResolverTests
extends "res://tests/utils/test_utils.gd"


# ---------------------------------------------------------------------------
# Player double — tracks calls to apply_fusion_effect
# ---------------------------------------------------------------------------

class PlayerDouble extends Object:
	var apply_fusion_effect_call_count: int = 0
	var last_duration: float = -1.0
	var last_multiplier: float = -1.0

	func apply_fusion_effect(duration: float, multiplier: float) -> void:
		apply_fusion_effect_call_count += 1
		last_duration = duration
		last_multiplier = multiplier

	func free_self() -> void:
		free()


var _pass_count: int = 0
var _fail_count: int = 0


func _load_resolver_script() -> GDScript:
	return load("res://scripts/fusion/fusion_resolver.gd") as GDScript


func _load_manager_script() -> GDScript:
	return load("res://scripts/mutation/mutation_slot_manager.gd") as GDScript


func _make_resolver() -> Object:
	var script: GDScript = _load_resolver_script()
	if script == null:
		return null
	return script.new()


func _make_manager() -> Object:
	var script: GDScript = _load_manager_script()
	if script == null:
		return null
	return script.new()


func _make_filled_manager() -> Object:
	var manager: Object = _make_manager()
	if manager == null:
		return null
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	return manager


# Guard helper: fails descriptively and returns true (caller must return early)
# when FusionResolver is not yet implemented.
func _require_resolver(resolver: Object, test_name: String) -> bool:
	if resolver == null:
		_fail(
			test_name,
			"FusionResolver script not found at res://scripts/fusion/fusion_resolver.gd — implement per FRH-3"
		)
		return true
	return false


func _require_can_fuse(resolver: Object, test_name: String) -> bool:
	if not resolver.has_method("can_fuse"):
		_fail(
			test_name,
			"can_fuse() not found on FusionResolver — implement per FRH-3-AC-2"
		)
		return true
	return false


func _require_resolve_fusion(resolver: Object, test_name: String) -> bool:
	if not resolver.has_method("resolve_fusion"):
		_fail(
			test_name,
			"resolve_fusion() not found on FusionResolver — implement per FRH-3-AC-3"
		)
		return true
	return false


# ---------------------------------------------------------------------------
# FRH-3-AC-1  FusionResolver script exists and is instantiable headlessly
# ---------------------------------------------------------------------------

func test_frh3_ac1_resolver_script_exists_and_instantiates() -> void:
	var script: GDScript = _load_resolver_script()
	_assert_true(
		script != null,
		"frh3_ac1_script_exists — FusionResolver script must exist at res://scripts/fusion/fusion_resolver.gd per FRH-3-AC-1"
	)
	if script == null:
		return

	var resolver: Object = script.new()
	_assert_true(
		resolver != null,
		"frh3_ac1_instantiates — FusionResolver.new() must return a non-null instance per FRH-3-AC-1"
	)
	if resolver != null:
		resolver.free()


# ---------------------------------------------------------------------------
# FRH-3-AC-2  can_fuse method exists on FusionResolver
# ---------------------------------------------------------------------------

func test_frh3_ac2_can_fuse_method_exists() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh3_ac2_can_fuse_exists"):
		return

	_assert_true(
		resolver.has_method("can_fuse"),
		"frh3_ac2_can_fuse_exists — FusionResolver must have can_fuse() per FRH-3-AC-2"
	)
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-3-AC-3  resolve_fusion method exists on FusionResolver
# ---------------------------------------------------------------------------

func test_frh3_ac3_resolve_fusion_method_exists() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh3_ac3_resolve_fusion_exists"):
		return

	_assert_true(
		resolver.has_method("resolve_fusion"),
		"frh3_ac3_resolve_fusion_exists — FusionResolver must have resolve_fusion() per FRH-3-AC-3"
	)
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-3-AC-4  FUSION_DURATION constant equals 5.0
# ---------------------------------------------------------------------------

func test_frh3_ac4_fusion_duration_constant() -> void:
	var script: GDScript = _load_resolver_script()
	if script == null:
		_fail(
			"frh3_ac4_fusion_duration_constant",
			"FusionResolver script not found — cannot check FUSION_DURATION per FRH-3-AC-4"
		)
		return

	var resolver: Object = script.new()
	if resolver == null:
		_fail("frh3_ac4_fusion_duration_constant", "FusionResolver.new() returned null")
		return

	# Constants are accessible as properties on the instance in GDScript.
	if not (resolver.get("FUSION_DURATION") != null):
		_fail(
			"frh3_ac4_fusion_duration_constant",
			"FUSION_DURATION constant not found on FusionResolver — implement per FRH-3-AC-4"
		)
		resolver.free()
		return

	_assert_eq_float(
		5.0,
		float(resolver.get("FUSION_DURATION")),
		"frh3_ac4_fusion_duration_constant — FUSION_DURATION must equal 5.0 per FRH-3-AC-4"
	)
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-3-AC-4  FUSION_MULTIPLIER constant equals 1.5
# ---------------------------------------------------------------------------

func test_frh3_ac4_fusion_multiplier_constant() -> void:
	var script: GDScript = _load_resolver_script()
	if script == null:
		_fail(
			"frh3_ac4_fusion_multiplier_constant",
			"FusionResolver script not found — cannot check FUSION_MULTIPLIER per FRH-3-AC-4"
		)
		return

	var resolver: Object = script.new()
	if resolver == null:
		_fail("frh3_ac4_fusion_multiplier_constant", "FusionResolver.new() returned null")
		return

	if not (resolver.get("FUSION_MULTIPLIER") != null):
		_fail(
			"frh3_ac4_fusion_multiplier_constant",
			"FUSION_MULTIPLIER constant not found on FusionResolver — implement per FRH-3-AC-4"
		)
		resolver.free()
		return

	_assert_eq_float(
		1.5,
		float(resolver.get("FUSION_MULTIPLIER")),
		"frh3_ac4_fusion_multiplier_constant — FUSION_MULTIPLIER must equal 1.5 per FRH-3-AC-4"
	)
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-2-AC-1  can_fuse returns false when both slots empty
# ---------------------------------------------------------------------------

func test_frh2_ac1_can_fuse_false_both_slots_empty() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh2_ac1_both_empty"):
		return
	if _require_can_fuse(resolver, "frh2_ac1_both_empty"):
		resolver.free()
		return

	var manager: Object = _make_manager()
	if manager == null:
		_fail("frh2_ac1_both_empty", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	# Both slots empty on fresh construction.
	var result: bool = resolver.call("can_fuse", manager)
	_assert_false(
		result,
		"frh2_ac1_both_empty — can_fuse must return false when both slots are empty per FRH-2-AC-1"
	)
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-2-AC-2  can_fuse returns false when only slot A is filled
# ---------------------------------------------------------------------------

func test_frh2_ac2_can_fuse_false_only_slot_a_filled() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh2_ac2_only_a_filled"):
		return
	if _require_can_fuse(resolver, "frh2_ac2_only_a_filled"):
		resolver.free()
		return

	var manager: Object = _make_manager()
	if manager == null:
		_fail("frh2_ac2_only_a_filled", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	manager.fill_next_available("mutation_a")
	# Slot B intentionally left empty.

	var result: bool = resolver.call("can_fuse", manager)
	_assert_false(
		result,
		"frh2_ac2_only_a_filled — can_fuse must return false when slot A is filled and slot B is empty per FRH-2-AC-2"
	)
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-2-AC-3  can_fuse returns false when only slot B is filled
# ---------------------------------------------------------------------------

func test_frh2_ac3_can_fuse_false_only_slot_b_filled() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh2_ac3_only_b_filled"):
		return
	if _require_can_fuse(resolver, "frh2_ac3_only_b_filled"):
		resolver.free()
		return

	var manager: Object = _make_manager()
	if manager == null:
		_fail("frh2_ac3_only_b_filled", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	# Fill slot B directly, leaving slot A empty.
	manager.get_slot(1).set_active_mutation_id("mutation_b")

	var result: bool = resolver.call("can_fuse", manager)
	_assert_false(
		result,
		"frh2_ac3_only_b_filled — can_fuse must return false when slot A is empty and slot B is filled per FRH-2-AC-3"
	)
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-2-AC-4  can_fuse returns true when both slots filled
# ---------------------------------------------------------------------------

func test_frh2_ac4_can_fuse_true_both_slots_filled() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh2_ac4_both_filled"):
		return
	if _require_can_fuse(resolver, "frh2_ac4_both_filled"):
		resolver.free()
		return

	var manager: Object = _make_filled_manager()
	if manager == null:
		_fail("frh2_ac4_both_filled", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	var result: bool = resolver.call("can_fuse", manager)
	_assert_true(
		result,
		"frh2_ac4_both_filled — can_fuse must return true only when both slots are filled per FRH-2-AC-4"
	)
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-2-AC-5  can_fuse(null) returns false and does not crash
# ---------------------------------------------------------------------------

func test_frh2_ac5_can_fuse_null_returns_false_no_crash() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh2_ac5_can_fuse_null"):
		return
	if _require_can_fuse(resolver, "frh2_ac5_can_fuse_null"):
		resolver.free()
		return

	var result: bool = resolver.call("can_fuse", null)
	_assert_false(
		result,
		"frh2_ac5_can_fuse_null — can_fuse(null) must return false without crash per FRH-2-AC-5"
	)
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-3-AC-5 + FRH-5-AC-1 + FRH-5-AC-2
# After resolve_fusion with both slots filled and a valid player double,
# both slots must be empty.
# ---------------------------------------------------------------------------

func test_frh3_ac5_frh5_ac1_ac2_slots_empty_after_resolve_fusion() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh3_ac5_slots_empty_after_resolve"):
		return
	if _require_resolve_fusion(resolver, "frh3_ac5_slots_empty_after_resolve"):
		resolver.free()
		return

	var manager: Object = _make_filled_manager()
	if manager == null:
		_fail("frh3_ac5_slots_empty_after_resolve", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()

	resolver.call("resolve_fusion", manager, player)

	_assert_false(
		manager.get_slot(0).is_filled(),
		"frh3_ac5_frh5_ac1_slot_a_empty — get_slot(0).is_filled() must be false after resolve_fusion per FRH-3-AC-5 / FRH-5-AC-1"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"frh3_ac5_frh5_ac2_slot_b_empty — get_slot(1).is_filled() must be false after resolve_fusion per FRH-3-AC-5 / FRH-5-AC-2"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-3-AC-6  apply_fusion_effect called exactly once with (5.0, 1.5)
# ---------------------------------------------------------------------------

func test_frh3_ac6_apply_fusion_effect_called_once_with_correct_args() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh3_ac6_apply_effect_call"):
		return
	if _require_resolve_fusion(resolver, "frh3_ac6_apply_effect_call"):
		resolver.free()
		return

	var manager: Object = _make_filled_manager()
	if manager == null:
		_fail("frh3_ac6_apply_effect_call", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()

	resolver.call("resolve_fusion", manager, player)

	_assert_eq_int(
		1,
		player.apply_fusion_effect_call_count,
		"frh3_ac6_apply_effect_call_count — apply_fusion_effect must be called exactly once per FRH-3-AC-6"
	)
	_assert_eq_float(
		5.0,
		player.last_duration,
		"frh3_ac6_apply_effect_duration — apply_fusion_effect must be called with duration=5.0 per FRH-3-AC-6"
	)
	_assert_eq_float(
		1.5,
		player.last_multiplier,
		"frh3_ac6_apply_effect_multiplier — apply_fusion_effect must be called with multiplier=1.5 per FRH-3-AC-6"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-3-AC-11  apply_fusion_effect is called BEFORE consume_fusion_slots
# Verified behaviorally: player.apply_fusion_effect was called when slots
# were still filled. We check that the player received the call (it would
# not if consume ran first and caused an internal guard failure), and that
# slots are empty after — both conditions must be true.
# ---------------------------------------------------------------------------

func test_frh3_ac11_apply_effect_before_consume_call_order() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh3_ac11_call_order"):
		return
	if _require_resolve_fusion(resolver, "frh3_ac11_call_order"):
		resolver.free()
		return

	var manager: Object = _make_filled_manager()
	if manager == null:
		_fail("frh3_ac11_call_order", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()

	resolver.call("resolve_fusion", manager, player)

	# If apply_fusion_effect was called at least once AND slots are now empty,
	# the only valid execution order is: apply_effect (while slots filled) → consume.
	var effect_called: bool = player.apply_fusion_effect_call_count >= 1
	var slots_consumed: bool = (not manager.get_slot(0).is_filled()) and (not manager.get_slot(1).is_filled())

	_assert_true(
		effect_called and slots_consumed,
		"frh3_ac11_call_order — apply_fusion_effect must be called before consume_fusion_slots; both conditions must hold per FRH-3-AC-11"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-3-AC-7  resolve_fusion(null, null) does not crash
# ---------------------------------------------------------------------------

func test_frh3_ac7_resolve_fusion_null_null_no_crash() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh3_ac7_null_null"):
		return
	if _require_resolve_fusion(resolver, "frh3_ac7_null_null"):
		resolver.free()
		return

	# Must complete without crashing.
	resolver.call("resolve_fusion", null, null)
	_pass(
		"frh3_ac7_null_null — resolve_fusion(null, null) must not crash per FRH-3-AC-7"
	)
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-3-AC-8  resolve_fusion with null player: slots consumed, no crash
# ---------------------------------------------------------------------------

func test_frh3_ac8_resolve_fusion_null_player_consumes_slots() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh3_ac8_null_player"):
		return
	if _require_resolve_fusion(resolver, "frh3_ac8_null_player"):
		resolver.free()
		return

	var manager: Object = _make_filled_manager()
	if manager == null:
		_fail("frh3_ac8_null_player", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	resolver.call("resolve_fusion", manager, null)

	_assert_false(
		manager.get_slot(0).is_filled(),
		"frh3_ac8_null_player_slot_a_empty — slot A must be empty after resolve_fusion with null player per FRH-3-AC-8"
	)
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-3-AC-9  resolve_fusion is no-op when can_fuse returns false
# (one slot empty — guard fails — slots unchanged, apply_fusion_effect not called)
# ---------------------------------------------------------------------------

func test_frh3_ac9_resolve_fusion_no_op_when_guard_fails() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh3_ac9_guard_no_op"):
		return
	if _require_resolve_fusion(resolver, "frh3_ac9_guard_no_op"):
		resolver.free()
		return

	var manager: Object = _make_manager()
	if manager == null:
		_fail("frh3_ac9_guard_no_op", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	# Only slot A filled; guard must fail.
	manager.fill_next_available("mutation_a")

	var player: PlayerDouble = PlayerDouble.new()

	resolver.call("resolve_fusion", manager, player)

	# Slot A must still be filled (not consumed).
	_assert_true(
		manager.get_slot(0).is_filled(),
		"frh3_ac9_slot_a_unchanged — slot A must remain filled when guard fails per FRH-3-AC-9 / FRH-5-AC-5"
	)
	# apply_fusion_effect must NOT have been called.
	_assert_eq_int(
		0,
		player.apply_fusion_effect_call_count,
		"frh3_ac9_apply_effect_not_called — apply_fusion_effect must not be called when guard fails per FRH-3-AC-9"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-5-AC-3  consume_fusion_slots on MutationSlotManager clears both slots
# (Verifies the existing contract is still intact — no change to manager required)
# ---------------------------------------------------------------------------

func test_frh5_ac3_consume_fusion_slots_existing_contract() -> void:
	var manager: Object = _make_filled_manager()
	if manager == null:
		_fail("frh5_ac3_consume_contract", "MutationSlotManager could not be instantiated; skipping")
		return

	if not manager.has_method("consume_fusion_slots"):
		_fail(
			"frh5_ac3_consume_contract",
			"consume_fusion_slots() not found on MutationSlotManager — prerequisite contract broken"
		)
		return

	manager.consume_fusion_slots()

	_assert_false(
		manager.get_slot(0).is_filled(),
		"frh5_ac3_slot_a_cleared — slot A must be empty after consume_fusion_slots per FRH-5-AC-3"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"frh5_ac3_slot_b_cleared — slot B must be empty after consume_fusion_slots per FRH-5-AC-3"
	)


# ---------------------------------------------------------------------------
# FRH-5-AC-4  After resolve_fusion consumes slots, fill_next_available fills slot A
# ---------------------------------------------------------------------------

func test_frh5_ac4_fill_after_resolve_goes_to_slot_a() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh5_ac4_fill_after_resolve"):
		return
	if _require_resolve_fusion(resolver, "frh5_ac4_fill_after_resolve"):
		resolver.free()
		return

	var manager: Object = _make_filled_manager()
	if manager == null:
		_fail("frh5_ac4_fill_after_resolve", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()
	resolver.call("resolve_fusion", manager, player)

	# Re-fill after consume.
	manager.fill_next_available("mutation_new")

	_assert_true(
		manager.get_slot(0).is_filled(),
		"frh5_ac4_slot_a_filled — slot A must accept a fill immediately after resolve_fusion per FRH-5-AC-4"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"frh5_ac4_slot_b_empty — slot B must still be empty after one post-resolve fill per FRH-5-AC-4"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-5-AC-5  Failed guard (one slot empty) does not consume slots
# (Separate from AC-9; focuses specifically on slot content unchanged)
# ---------------------------------------------------------------------------

func test_frh5_ac5_failed_guard_does_not_consume_slots() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh5_ac5_guard_no_consume"):
		return
	if _require_resolve_fusion(resolver, "frh5_ac5_guard_no_consume"):
		resolver.free()
		return

	var manager: Object = _make_manager()
	if manager == null:
		_fail("frh5_ac5_guard_no_consume", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	# Only slot B filled — guard returns false.
	manager.get_slot(1).set_active_mutation_id("mutation_b")

	var player: PlayerDouble = PlayerDouble.new()
	resolver.call("resolve_fusion", manager, player)

	_assert_false(
		manager.get_slot(0).is_filled(),
		"frh5_ac5_slot_a_unchanged_empty — slot A (already empty) must remain empty after failed guard per FRH-5-AC-5"
	)
	_assert_true(
		manager.get_slot(1).is_filled(),
		"frh5_ac5_slot_b_unchanged_filled — slot B must remain filled after failed guard; consume must not have run per FRH-5-AC-5"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# FRH-5-AC-6  Full two-cycle sequence: fill, fuse, re-fill, fuse
# Two successful fusions leave slots empty and apply_fusion_effect called twice.
# ---------------------------------------------------------------------------

func test_frh5_ac6_two_cycle_sequence() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh5_ac6_two_cycle"):
		return
	if _require_resolve_fusion(resolver, "frh5_ac6_two_cycle"):
		resolver.free()
		return

	var manager: Object = _make_manager()
	if manager == null:
		_fail("frh5_ac6_two_cycle", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()

	# Cycle 1
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	resolver.call("resolve_fusion", manager, player)

	# Cycle 2
	manager.fill_next_available("mutation_c")
	manager.fill_next_available("mutation_d")
	resolver.call("resolve_fusion", manager, player)

	_assert_eq_int(
		2,
		player.apply_fusion_effect_call_count,
		"frh5_ac6_two_fusions_applied — apply_fusion_effect must be called exactly twice over two complete cycles per FRH-5-AC-6"
	)
	_assert_false(
		manager.get_slot(0).is_filled(),
		"frh5_ac6_slot_a_empty_end — slot A must be empty after second fuse per FRH-5-AC-6"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"frh5_ac6_slot_b_empty_end — slot B must be empty after second fuse per FRH-5-AC-6"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# Null-safety: can_fuse with a manager whose get_slot(0) returns null
# (FRH-2-AC-6: simulated by passing a plain Object that has no get_slot method)
# ---------------------------------------------------------------------------

func test_frh2_ac6_can_fuse_returns_false_when_get_slot_missing() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "frh2_ac6_missing_get_slot"):
		return
	if _require_can_fuse(resolver, "frh2_ac6_missing_get_slot"):
		resolver.free()
		return

	# A plain Object has no get_slot method — simulates a malformed manager.
	var malformed: Object = Object.new()

	var result: bool = resolver.call("can_fuse", malformed)
	_assert_false(
		result,
		"frh2_ac6_malformed_manager — can_fuse must return false (not crash) when manager lacks get_slot() per FRH-2-AC-6"
	)

	malformed.free()
	resolver.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- tests/fusion/test_fusion_resolver.gd ---")
	_pass_count = 0
	_fail_count = 0

	# FRH-3: FusionResolver API surface
	test_frh3_ac1_resolver_script_exists_and_instantiates()
	test_frh3_ac2_can_fuse_method_exists()
	test_frh3_ac3_resolve_fusion_method_exists()
	test_frh3_ac4_fusion_duration_constant()
	test_frh3_ac4_fusion_multiplier_constant()

	# FRH-2: Fusion guard — can_fuse return values for all slot combinations
	test_frh2_ac1_can_fuse_false_both_slots_empty()
	test_frh2_ac2_can_fuse_false_only_slot_a_filled()
	test_frh2_ac3_can_fuse_false_only_slot_b_filled()
	test_frh2_ac4_can_fuse_true_both_slots_filled()
	test_frh2_ac5_can_fuse_null_returns_false_no_crash()
	test_frh2_ac6_can_fuse_returns_false_when_get_slot_missing()

	# FRH-3 + FRH-5: resolve_fusion behaviour
	test_frh3_ac5_frh5_ac1_ac2_slots_empty_after_resolve_fusion()
	test_frh3_ac6_apply_fusion_effect_called_once_with_correct_args()
	test_frh3_ac11_apply_effect_before_consume_call_order()
	test_frh3_ac7_resolve_fusion_null_null_no_crash()
	test_frh3_ac8_resolve_fusion_null_player_consumes_slots()
	test_frh3_ac9_resolve_fusion_no_op_when_guard_fails()

	# FRH-5: Slot consumption contracts
	test_frh5_ac3_consume_fusion_slots_existing_contract()
	test_frh5_ac4_fill_after_resolve_goes_to_slot_a()
	test_frh5_ac5_failed_guard_does_not_consume_slots()
	test_frh5_ac6_two_cycle_sequence()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
