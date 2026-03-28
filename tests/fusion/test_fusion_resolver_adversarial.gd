#
# test_fusion_resolver_adversarial.gd
#
# Adversarial test suite for FusionResolver.
# Ticket: fusion_rules_and_hybrid.md
# Spec:   fusion_rules_and_hybrid_spec.md (FRH-2, FRH-3, FRH-5)
#
# Purpose: Expose coverage gaps, blind spots, and edge-case failures that a
# naive FusionResolver implementation would miss — distinct from the 20 cases
# already covered by the primary suite (test_fusion_resolver.gd).
#
# TDD RED PHASE: FusionResolver does not exist yet.
# All references to FusionResolver use load() + has_method() guards so the
# suite parses and runs headlessly without crashing, recording precise FAIL
# messages for each unimplemented symbol.
#
# Adversarial coverage matrix:
#
# | ID     | Category              | Vulnerability probed                                                       |
# |--------|-----------------------|----------------------------------------------------------------------------|
# | ADV-01 | Double-fuse no-op     | Second resolve_fusion call on empty manager is a no-op; apply not called   |
# | ADV-02 | Guard bypass          | resolve_fusion called directly on empty manager — no effect applied        |
# | ADV-03 | Null slot double      | manager.get_slot returns null — can_fuse returns false, no crash           |
# | ADV-04 | Null slot double      | manager.get_slot returns null — resolve_fusion no-op, no crash             |
# | ADV-05 | Wrong player type     | player lacks apply_fusion_effect — slots still consumed, no crash          |
# | ADV-06 | Constants immutability| FUSION_DURATION and FUSION_MULTIPLIER unchanged after resolve_fusion call  |
# | ADV-07 | Constants positivity  | FUSION_DURATION > 0 and FUSION_MULTIPLIER > 0 (not zero, not negative)     |
# | ADV-08 | Re-trigger args       | Two-cycle fuse: second call passes same duration/multiplier (reset, not stack) |
# | ADV-09 | Partial slot A only   | resolve_fusion with only slot A filled: guard blocks, no side effects       |
# | ADV-10 | Partial slot B only   | resolve_fusion with only slot B filled: guard blocks, no side effects       |
# | ADV-11 | Both slots empty      | resolve_fusion with both empty: guard blocks, no side effects               |
# | ADV-12 | Determinism           | Identical inputs → identical outputs across two resolver instances          |
# | ADV-13 | Resolver isolation    | Two resolver instances do not share state                                   |
# | ADV-14 | No manager mutation   | can_fuse must not modify slot state (pure function)                         |
# | ADV-15 | Order-of-args swap    | resolve_fusion(player, manager) (wrong arg order) — no crash                |
# | ADV-16 | Manager with get_slot but returns null for index 1 only — can_fuse false |
# | ADV-17 | Endurance             | 5-cycle fill→fuse sequence: apply count == 5, slots empty at end            |
# | ADV-18 | No-op resolve null mgr| resolve_fusion(null, valid_player) — no crash, apply_fusion_effect not called |

class_name FusionResolverAdversarialTests
extends "res://tests/utils/test_utils.gd"


# ---------------------------------------------------------------------------
# Doubles
# ---------------------------------------------------------------------------

# Tracks calls to apply_fusion_effect. Extends Object for manual free().
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


# Simulates a manager whose get_slot() always returns null.
# This is a strictly more targeted vulnerability than "no get_slot at all":
# an implementation that does has_method("get_slot") and then blindly calls
# .is_filled() on the return value will crash here.
class NullSlotDouble extends Object:
	func get_slot(_index: int) -> Object:
		return null

	func has_method_get_slot() -> bool:
		return true

	func free_self() -> void:
		free()


# Simulates a manager where get_slot(0) returns null but get_slot(1) returns
# a filled slot. Tests that both slots are checked and that a null on slot 0
# alone causes can_fuse to return false (not just fall through to slot 1).
class PartialNullSlotDouble extends Object:
	var _slot_b: RefCounted = null

	func _init() -> void:
		var script: GDScript = load("res://scripts/mutation/mutation_slot.gd") as GDScript
		if script != null:
			_slot_b = script.new()
			_slot_b.set_active_mutation_id("mutation_b")

	func get_slot(index: int) -> Object:
		if index == 0:
			return null
		if index == 1:
			return _slot_b
		return null

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


# Guard: fails descriptively if resolver is absent (caller returns early).
func _require_resolver(resolver: Object, test_name: String) -> bool:
	if resolver == null:
		_fail(
			test_name,
			"FusionResolver not found at res://scripts/fusion/fusion_resolver.gd — implement per FRH-3"
		)
		return true
	return false


func _require_can_fuse(resolver: Object, test_name: String) -> bool:
	if not resolver.has_method("can_fuse"):
		_fail(test_name, "can_fuse() missing on FusionResolver — implement per FRH-3-AC-2")
		return true
	return false


func _require_resolve_fusion(resolver: Object, test_name: String) -> bool:
	if not resolver.has_method("resolve_fusion"):
		_fail(test_name, "resolve_fusion() missing on FusionResolver — implement per FRH-3-AC-3")
		return true
	return false


# ---------------------------------------------------------------------------
# ADV-01  Double-fuse no-op: second resolve_fusion is a no-op because slots
#          are empty after the first call.
#
# Vulnerability exposed: A naive implementation that skips the internal
# can_fuse guard inside resolve_fusion would call apply_fusion_effect a
# second time on the same now-empty manager, incorrectly triggering the
# effect without slots. The guard MUST be re-evaluated inside resolve_fusion
# on every call, not cached from a prior can_fuse check.
# ---------------------------------------------------------------------------

func test_adv_01_double_fuse_second_call_is_noop() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-01/double-fuse-noop"):
		return
	if _require_resolve_fusion(resolver, "adv-01/double-fuse-noop"):
		resolver.free()
		return

	var manager: Object = _make_filled_manager()
	if manager == null:
		_fail("adv-01/double-fuse-noop", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()

	# First resolve_fusion: should succeed (both slots filled).
	resolver.call("resolve_fusion", manager, player)

	# At this point slots are empty; calling resolve_fusion again must be a no-op.
	resolver.call("resolve_fusion", manager, player)

	_assert_eq_int(
		1,
		player.apply_fusion_effect_call_count,
		"adv-01/a — apply_fusion_effect must be called exactly once across two resolve_fusion calls on same manager (second call must be no-op, slots already empty per FRH-3-AC-9)"
	)
	_assert_false(
		manager.get_slot(0).is_filled(),
		"adv-01/b — slot A must remain empty after the second (no-op) resolve_fusion call"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"adv-01/c — slot B must remain empty after the second (no-op) resolve_fusion call"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-02  Guard bypass: resolve_fusion called directly on an empty manager
#          (bypassing any external can_fuse check) must produce no effect.
#
# Vulnerability exposed: A shallow implementation that only guards via an
# external can_fuse check but does not re-evaluate the guard inside
# resolve_fusion itself could be fooled by a caller that calls resolve_fusion
# directly without calling can_fuse first. The spec mandates that resolve_fusion
# calls can_fuse internally (FRH-3-AC-3 / FRH-3-AC-9). This test drives
# resolve_fusion without any preceding can_fuse call, on a manager where both
# slots are empty from the start.
# ---------------------------------------------------------------------------

func test_adv_02_guard_bypass_resolve_on_empty_manager_no_effect() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-02/guard-bypass"):
		return
	if _require_resolve_fusion(resolver, "adv-02/guard-bypass"):
		resolver.free()
		return

	var manager: Object = _make_manager()
	if manager == null:
		_fail("adv-02/guard-bypass", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()

	# Both slots empty — call resolve_fusion directly without can_fuse.
	resolver.call("resolve_fusion", manager, player)

	_assert_eq_int(
		0,
		player.apply_fusion_effect_call_count,
		"adv-02/a — apply_fusion_effect must NOT be called when resolve_fusion is invoked directly on an empty manager (internal guard must fire per FRH-3)"
	)
	_assert_false(
		manager.get_slot(0).is_filled(),
		"adv-02/b — slot A must remain empty (guard prevented any mutation)"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"adv-02/c — slot B must remain empty (guard prevented any mutation)"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-03  NullSlotDouble — can_fuse returns false when manager.get_slot()
#          returns null (distinct from the "no get_slot method" case in
#          primary suite test_frh2_ac6).
#
# Vulnerability exposed: An implementation that does:
#   if not slot_manager.has_method("get_slot"): return false
#   slot_manager.get_slot(0).is_filled()  # CRASH: null.is_filled()
# passes the primary suite (plain Object lacks get_slot) but fails here
# because this manager HAS get_slot — it just returns null from it.
# ---------------------------------------------------------------------------

func test_adv_03_can_fuse_returns_false_when_get_slot_returns_null() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-03/null-slot-double-can-fuse"):
		return
	if _require_can_fuse(resolver, "adv-03/null-slot-double-can-fuse"):
		resolver.free()
		return

	var null_mgr: NullSlotDouble = NullSlotDouble.new()

	var result: bool = resolver.call("can_fuse", null_mgr)
	_assert_false(
		result,
		"adv-03/a — can_fuse must return false (not crash) when manager.get_slot() returns null per FRH-2-AC-6 extended"
	)

	null_mgr.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-04  NullSlotDouble — resolve_fusion with a manager whose get_slot()
#          returns null must be a no-op (no crash, no apply, no consume attempt).
#
# Vulnerability exposed: resolve_fusion calls can_fuse internally. If can_fuse
# null-checks correctly and returns false, resolve_fusion must early-return
# without touching the manager further. A buggy implementation that calls
# manager.consume_fusion_slots() unconditionally would crash or corrupt state.
# ---------------------------------------------------------------------------

func test_adv_04_resolve_fusion_noop_when_get_slot_returns_null() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-04/null-slot-double-resolve"):
		return
	if _require_resolve_fusion(resolver, "adv-04/null-slot-double-resolve"):
		resolver.free()
		return

	var null_mgr: NullSlotDouble = NullSlotDouble.new()
	var player: PlayerDouble = PlayerDouble.new()

	# Must not crash.
	resolver.call("resolve_fusion", null_mgr, player)

	_assert_eq_int(
		0,
		player.apply_fusion_effect_call_count,
		"adv-04/a — apply_fusion_effect must NOT be called when get_slot() returns null (guard fires, early return per FRH-3-AC-9)"
	)

	player.free_self()
	null_mgr.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-05  Wrong player type — player is a valid Object but lacks
#          apply_fusion_effect. Slots must still be consumed, no crash.
#
# Vulnerability exposed: spec FRH-3 says: if player.has_method("apply_fusion_effect")
# is false, call push_error AND still call consume_fusion_slots. A naive
# implementation that checks the method, crashes if absent, or forgets to
# consume slots would fail this test. Slot consumption being the conservative
# fallback is the critical invariant here.
# ---------------------------------------------------------------------------

func test_adv_05_wrong_player_type_slots_consumed_no_crash() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-05/wrong-player-type"):
		return
	if _require_resolve_fusion(resolver, "adv-05/wrong-player-type"):
		resolver.free()
		return

	var manager: Object = _make_filled_manager()
	if manager == null:
		_fail("adv-05/wrong-player-type", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	# A plain Object — has no apply_fusion_effect method.
	var bad_player: Object = Object.new()

	# Must not crash.
	resolver.call("resolve_fusion", manager, bad_player)

	# Slots must have been consumed even though the player lacked the method.
	_assert_false(
		manager.get_slot(0).is_filled(),
		"adv-05/a — slot A must be empty after resolve_fusion with wrong-type player (slots consumed per FRH-3 risk note)"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"adv-05/b — slot B must be empty after resolve_fusion with wrong-type player (slots consumed per FRH-3 risk note)"
	)

	bad_player.free()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-06  Constants immutability — FUSION_DURATION and FUSION_MULTIPLIER must
#          be unchanged after a resolve_fusion call.
#
# Vulnerability exposed: the primary suite checks constant values BEFORE any
# call. This test checks them AFTER a successful resolve_fusion. A naive
# implementation that uses mutable instance vars named FUSION_DURATION /
# FUSION_MULTIPLIER (instead of const) and mutates them inside resolve_fusion
# (e.g., to track elapsed time or ratio) would fail here.
# ---------------------------------------------------------------------------

func test_adv_06_constants_unchanged_after_resolve_fusion() -> void:
	var script: GDScript = _load_resolver_script()
	if script == null:
		_fail(
			"adv-06/constants-immutable",
			"FusionResolver script not found — cannot check constants per FRH-3-AC-4"
		)
		return

	var resolver: Object = script.new()
	if resolver == null:
		_fail("adv-06/constants-immutable", "FusionResolver.new() returned null")
		return

	if _require_resolve_fusion(resolver, "adv-06/constants-immutable"):
		resolver.free()
		return

	var manager: Object = _make_filled_manager()
	if manager == null:
		_fail("adv-06/constants-immutable", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()
	resolver.call("resolve_fusion", manager, player)

	# Constants must be exactly their spec values after the call.
	var dur: Variant = resolver.get("FUSION_DURATION")
	var mul: Variant = resolver.get("FUSION_MULTIPLIER")

	if dur == null:
		_fail("adv-06/a", "FUSION_DURATION not accessible after resolve_fusion call — implement per FRH-3-AC-4")
	else:
		_assert_true(
			absf(float(dur) - 5.0) < 0.0001,
			"adv-06/a — FUSION_DURATION must equal 5.0 after resolve_fusion (must not be mutated per FRH-3-AC-4)"
		)

	if mul == null:
		_fail("adv-06/b", "FUSION_MULTIPLIER not accessible after resolve_fusion call — implement per FRH-3-AC-4")
	else:
		_assert_true(
			absf(float(mul) - 1.5) < 0.0001,
			"adv-06/b — FUSION_MULTIPLIER must equal 1.5 after resolve_fusion (must not be mutated per FRH-3-AC-4)"
		)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-07  Constants positivity — FUSION_DURATION > 0 and FUSION_MULTIPLIER > 0.
#
# Vulnerability exposed: A zero or negative constant produces a silent
# no-effect or reversed effect in the player controller. The spec fixes
# values (5.0, 1.5) but a regression that sets either to 0 or -1 would pass
# equality-only checks if only exact values are checked. This test adds an
# explicit > 0 lower bound to catch off-by-sign or off-by-unit errors.
# ---------------------------------------------------------------------------

func test_adv_07_constants_are_positive() -> void:
	var script: GDScript = _load_resolver_script()
	if script == null:
		_fail(
			"adv-07/constants-positive",
			"FusionResolver script not found — cannot check constants per FRH-3-AC-4"
		)
		return

	var resolver: Object = script.new()
	if resolver == null:
		_fail("adv-07/constants-positive", "FusionResolver.new() returned null")
		return

	var dur: Variant = resolver.get("FUSION_DURATION")
	var mul: Variant = resolver.get("FUSION_MULTIPLIER")

	if dur == null:
		_fail("adv-07/a", "FUSION_DURATION not found — cannot check positivity per FRH-3-AC-4")
	else:
		_assert_true(
			float(dur) > 0.0,
			"adv-07/a — FUSION_DURATION must be > 0 (a zero duration would make the effect invisible per FRH-4-AC-8)"
		)

	if mul == null:
		_fail("adv-07/b", "FUSION_MULTIPLIER not found — cannot check positivity per FRH-3-AC-4")
	else:
		_assert_true(
			float(mul) > 0.0,
			"adv-07/b — FUSION_MULTIPLIER must be > 0 (a zero or negative multiplier would nullify or reverse the speed boost)"
		)

	resolver.free()


# ---------------------------------------------------------------------------
# ADV-08  Re-trigger args — in a two-cycle fill→fuse→fill→fuse sequence, the
#          second resolve_fusion call passes the same duration and multiplier
#          as the first. Verifies reset-not-stack semantics via the args passed.
#
# Vulnerability exposed: An implementation that accumulates duration on
# repeated calls (e.g., timer += FUSION_DURATION on each call) would pass the
# first call's args check but the PlayerController3D would receive incorrect
# cumulative state. This test verifies that the second call's args match the
# spec constants exactly, not a doubled value.
# ---------------------------------------------------------------------------

func test_adv_08_two_cycle_fuse_second_call_args_same_as_first() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-08/re-trigger-args"):
		return
	if _require_resolve_fusion(resolver, "adv-08/re-trigger-args"):
		resolver.free()
		return

	var manager: Object = _make_manager()
	if manager == null:
		_fail("adv-08/re-trigger-args", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()

	# Cycle 1
	manager.fill_next_available("a1")
	manager.fill_next_available("b1")
	resolver.call("resolve_fusion", manager, player)

	# Cycle 2
	manager.fill_next_available("a2")
	manager.fill_next_available("b2")
	resolver.call("resolve_fusion", manager, player)

	_assert_eq_int(
		2,
		player.apply_fusion_effect_call_count,
		"adv-08/a — apply_fusion_effect must be called exactly twice across two complete cycles"
	)
	# last_duration and last_multiplier hold the SECOND call's arguments.
	_assert_true(
		absf(player.last_duration - 5.0) < 0.0001,
		"adv-08/b — second call to apply_fusion_effect must use FUSION_DURATION (5.0), not accumulated value"
	)
	_assert_true(
		absf(player.last_multiplier - 1.5) < 0.0001,
		"adv-08/c — second call to apply_fusion_effect must use FUSION_MULTIPLIER (1.5), not accumulated value"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-09  Partial slot A only — resolve_fusion with only slot A filled.
#          Guard must block: apply_fusion_effect NOT called, slot A unchanged.
#
# Vulnerability exposed: The primary suite covers this path via
# test_frh3_ac9, but only checks apply call count and slot A. This adversarial
# test additionally verifies that slot B is still empty (no state was leaked
# into slot B from the failed attempt) and that the specific slot-A mutation
# ID is preserved exactly.
# ---------------------------------------------------------------------------

func test_adv_09_partial_slot_a_only_guard_blocks_state_preserved() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-09/partial-a-only"):
		return
	if _require_resolve_fusion(resolver, "adv-09/partial-a-only"):
		resolver.free()
		return

	var manager: Object = _make_manager()
	if manager == null:
		_fail("adv-09/partial-a-only", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	manager.fill_next_available("partial_a_id")
	var player: PlayerDouble = PlayerDouble.new()
	resolver.call("resolve_fusion", manager, player)

	_assert_eq_int(
		0,
		player.apply_fusion_effect_call_count,
		"adv-09/a — apply_fusion_effect NOT called when only slot A is filled (guard fires per FRH-2-AC-2)"
	)
	_assert_true(
		manager.get_slot(0).is_filled(),
		"adv-09/b — slot A must still be filled after failed guard (no consume per FRH-5-AC-5)"
	)
	_assert_true(
		manager.get_slot(0).get_active_mutation_id() == "partial_a_id",
		"adv-09/c — slot A mutation ID ('partial_a_id') must be preserved exactly after failed guard"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"adv-09/d — slot B must remain empty (no state leaked from failed fusion attempt)"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-10  Partial slot B only — resolve_fusion with only slot B filled.
#          Guard must block: apply_fusion_effect NOT called, slot B unchanged.
#
# Vulnerability exposed: A can_fuse implementation that only checks slot 0
# would see slot 0 empty and return false — correct for ADV-09. But if it
# accidentally checks slot 1 first and returns true (guard checks in wrong
# order or OR instead of AND), slot B filled alone would trigger fusion.
# This test directly detects that specific mutation.
# ---------------------------------------------------------------------------

func test_adv_10_partial_slot_b_only_guard_blocks_state_preserved() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-10/partial-b-only"):
		return
	if _require_resolve_fusion(resolver, "adv-10/partial-b-only"):
		resolver.free()
		return

	var manager: Object = _make_manager()
	if manager == null:
		_fail("adv-10/partial-b-only", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	# Fill slot B directly (bypass fill_next_available to avoid filling A first).
	manager.get_slot(1).set_active_mutation_id("partial_b_id")

	var player: PlayerDouble = PlayerDouble.new()
	resolver.call("resolve_fusion", manager, player)

	_assert_eq_int(
		0,
		player.apply_fusion_effect_call_count,
		"adv-10/a — apply_fusion_effect NOT called when only slot B is filled (guard fires per FRH-2-AC-3)"
	)
	_assert_false(
		manager.get_slot(0).is_filled(),
		"adv-10/b — slot A must remain empty (no state leaked)"
	)
	_assert_true(
		manager.get_slot(1).is_filled(),
		"adv-10/c — slot B must still be filled (not consumed per FRH-5-AC-5)"
	)
	_assert_true(
		manager.get_slot(1).get_active_mutation_id() == "partial_b_id",
		"adv-10/d — slot B mutation ID ('partial_b_id') must be preserved exactly after failed guard"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-11  Both slots empty — resolve_fusion with both empty is a no-op.
#          No effect applied, no consume called.
#
# Vulnerability exposed: An implementation that calls consume_fusion_slots
# unconditionally before the guard (inverted order) would call consume on an
# already-empty manager — which itself is harmless — but would then proceed
# to call apply_fusion_effect because the guard now sees two empty slots
# as "matching" some degenerate state. Verifies strict pre-condition.
# ---------------------------------------------------------------------------

func test_adv_11_both_slots_empty_resolve_fusion_is_noop() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-11/both-empty-noop"):
		return
	if _require_resolve_fusion(resolver, "adv-11/both-empty-noop"):
		resolver.free()
		return

	var manager: Object = _make_manager()
	if manager == null:
		_fail("adv-11/both-empty-noop", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()

	# Fresh manager — both slots empty from construction.
	resolver.call("resolve_fusion", manager, player)

	_assert_eq_int(
		0,
		player.apply_fusion_effect_call_count,
		"adv-11/a — apply_fusion_effect must NOT be called on a fresh manager with both slots empty (guard fires per FRH-2-AC-1)"
	)
	_assert_false(
		manager.get_slot(0).is_filled(),
		"adv-11/b — slot A must remain empty"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"adv-11/c — slot B must remain empty"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-12  Determinism — identical inputs on two independent resolver instances
#          produce identical observable outputs.
#
# Vulnerability exposed: If FusionResolver holds any mutable class-level
# (static) state — e.g. a call counter, a "last player" reference, or a
# preloaded singleton — two instances would diverge on their second operation.
# Both resolvers must produce identical slot and player states from the same
# starting conditions.
# ---------------------------------------------------------------------------

func test_adv_12_determinism_two_resolver_instances_identical_outputs() -> void:
	var script: GDScript = _load_resolver_script()
	if script == null:
		_fail(
			"adv-12/determinism",
			"FusionResolver script not found — cannot check determinism per FRH-3"
		)
		return

	var r1: Object = script.new()
	var r2: Object = script.new()

	if r1 == null or r2 == null:
		_fail("adv-12/determinism", "FusionResolver.new() returned null for one of two instances")
		if r1 != null:
			r1.free()
		if r2 != null:
			r2.free()
		return

	if not r1.has_method("resolve_fusion") or not r2.has_method("resolve_fusion"):
		_fail("adv-12/determinism", "resolve_fusion() missing — implement per FRH-3-AC-3")
		r1.free()
		r2.free()
		return

	var m1: Object = _make_filled_manager()
	var m2: Object = _make_filled_manager()
	if m1 == null or m2 == null:
		_fail("adv-12/determinism", "MutationSlotManager could not be instantiated; skipping")
		r1.free()
		r2.free()
		return

	var p1: PlayerDouble = PlayerDouble.new()
	var p2: PlayerDouble = PlayerDouble.new()

	r1.call("resolve_fusion", m1, p1)
	r2.call("resolve_fusion", m2, p2)

	_assert_true(
		p1.apply_fusion_effect_call_count == p2.apply_fusion_effect_call_count,
		"adv-12/a — both resolver instances must call apply_fusion_effect the same number of times"
	)
	_assert_true(
		absf(p1.last_duration - p2.last_duration) < 0.0001,
		"adv-12/b — both resolver instances must pass the same duration to apply_fusion_effect"
	)
	_assert_true(
		absf(p1.last_multiplier - p2.last_multiplier) < 0.0001,
		"adv-12/c — both resolver instances must pass the same multiplier to apply_fusion_effect"
	)
	_assert_true(
		m1.get_slot(0).is_filled() == m2.get_slot(0).is_filled(),
		"adv-12/d — slot A state must be identical after both resolvers run"
	)
	_assert_true(
		m1.get_slot(1).is_filled() == m2.get_slot(1).is_filled(),
		"adv-12/e — slot B state must be identical after both resolvers run"
	)

	p1.free_self()
	p2.free_self()
	r1.free()
	r2.free()


# ---------------------------------------------------------------------------
# ADV-13  Resolver instance isolation — two resolvers operating on independent
#          managers must not share slot state.
#
# Vulnerability exposed: If resolve_fusion caches the manager reference in an
# instance field and a second resolver instance on a second manager reads the
# first resolver's cached manager, it would corrupt state. Confirms that
# using two resolvers simultaneously does not cause cross-contamination.
# ---------------------------------------------------------------------------

func test_adv_13_resolver_isolation_no_cross_manager_contamination() -> void:
	var script: GDScript = _load_resolver_script()
	if script == null:
		_fail(
			"adv-13/resolver-isolation",
			"FusionResolver script not found — implement per FRH-3"
		)
		return

	var r1: Object = script.new()
	var r2: Object = script.new()

	if r1 == null or r2 == null:
		_fail("adv-13/resolver-isolation", "FusionResolver.new() returned null")
		if r1 != null:
			r1.free()
		if r2 != null:
			r2.free()
		return

	if not r1.has_method("resolve_fusion") or not r2.has_method("resolve_fusion"):
		_fail("adv-13/resolver-isolation", "resolve_fusion() missing — implement per FRH-3-AC-3")
		r1.free()
		r2.free()
		return

	var m_full: Object = _make_filled_manager()
	var m_empty: Object = _make_manager()
	if m_full == null or m_empty == null:
		_fail("adv-13/resolver-isolation", "MutationSlotManager could not be instantiated; skipping")
		r1.free()
		r2.free()
		return

	var p1: PlayerDouble = PlayerDouble.new()
	var p2: PlayerDouble = PlayerDouble.new()

	# r1 resolves on m_full (should succeed).
	r1.call("resolve_fusion", m_full, p1)
	# r2 resolves on m_empty (should be a no-op).
	r2.call("resolve_fusion", m_empty, p2)

	# r1's operation must have applied the effect.
	_assert_eq_int(
		1,
		p1.apply_fusion_effect_call_count,
		"adv-13/a — r1 must have called apply_fusion_effect once (both slots were filled)"
	)
	# r2's operation must NOT have applied the effect (m_empty has no filled slots).
	_assert_eq_int(
		0,
		p2.apply_fusion_effect_call_count,
		"adv-13/b — r2 must NOT have called apply_fusion_effect (m_empty has no filled slots; no cross-contamination from r1)"
	)
	# m_empty's slots must be untouched.
	_assert_false(
		m_empty.get_slot(0).is_filled(),
		"adv-13/c — m_empty slot A must remain empty after r2 no-op"
	)
	_assert_false(
		m_empty.get_slot(1).is_filled(),
		"adv-13/d — m_empty slot B must remain empty after r2 no-op"
	)

	p1.free_self()
	p2.free_self()
	r1.free()
	r2.free()


# ---------------------------------------------------------------------------
# ADV-14  can_fuse is a pure function — it must not modify slot state.
#
# Vulnerability exposed: A buggy implementation that "optimistically consumes"
# slots inside can_fuse (treating it as a combined check-and-consume) would
# leave both slots empty after can_fuse even though fusion never completed.
# Callers calling can_fuse as a read-only guard would lose their slot data.
# The spec explicitly states can_fuse has no side effects (FRH-3).
# ---------------------------------------------------------------------------

func test_adv_14_can_fuse_does_not_modify_slot_state() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-14/can-fuse-pure"):
		return
	if _require_can_fuse(resolver, "adv-14/can-fuse-pure"):
		resolver.free()
		return

	var manager: Object = _make_filled_manager()
	if manager == null:
		_fail("adv-14/can-fuse-pure", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	# Call can_fuse multiple times and verify slots remain filled throughout.
	var r1: bool = resolver.call("can_fuse", manager)
	var r2: bool = resolver.call("can_fuse", manager)
	var r3: bool = resolver.call("can_fuse", manager)

	_assert_true(
		r1 and r2 and r3,
		"adv-14/a — can_fuse must return true on three successive calls when both slots remain filled"
	)
	_assert_true(
		manager.get_slot(0).is_filled(),
		"adv-14/b — slot A must still be filled after 3 calls to can_fuse (can_fuse must not consume slots per FRH-3)"
	)
	_assert_true(
		manager.get_slot(1).is_filled(),
		"adv-14/c — slot B must still be filled after 3 calls to can_fuse (can_fuse must not consume slots per FRH-3)"
	)

	resolver.free()


# ---------------------------------------------------------------------------
# ADV-15  Resolve with null manager and valid player — no crash.
#
# Vulnerability exposed: The primary suite covers resolve_fusion(null, null)
# via FRH-3-AC-7. This test covers the asymmetric case: null manager but a
# real player double. A naive implementation that null-checks manager and
# player in the wrong order could skip the player null-check but crash on
# the manager when it tries to call can_fuse or consume_fusion_slots on null.
# Also verifies that apply_fusion_effect is NOT called (guard blocks on null mgr).
# ---------------------------------------------------------------------------

func test_adv_15_resolve_fusion_null_manager_valid_player_no_crash_no_apply() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-15/null-manager-valid-player"):
		return
	if _require_resolve_fusion(resolver, "adv-15/null-manager-valid-player"):
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()

	# Must not crash.
	resolver.call("resolve_fusion", null, player)

	_assert_eq_int(
		0,
		player.apply_fusion_effect_call_count,
		"adv-15/a — apply_fusion_effect must NOT be called when manager is null (guard fires per FRH-2-AC-5 / FRH-3-AC-7)"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-16  PartialNullSlotDouble — get_slot(0) returns null, get_slot(1) returns
#          a filled slot. can_fuse must return false (not crash or return true
#          because slot 1 is filled).
#
# Vulnerability exposed: An implementation that checks slot 0 first, gets null,
# fails to null-check, and crashes — OR an implementation that skips the null
# slot 0 and only checks slot 1 (finding it filled) and erroneously returns true.
# Either failure mode is caught here. The AND requires BOTH slots non-null and filled.
# ---------------------------------------------------------------------------

func test_adv_16_partial_null_slot_double_can_fuse_false_no_crash() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-16/partial-null-slot"):
		return
	if _require_can_fuse(resolver, "adv-16/partial-null-slot"):
		resolver.free()
		return

	var partial_mgr: PartialNullSlotDouble = PartialNullSlotDouble.new()

	var result: bool = resolver.call("can_fuse", partial_mgr)
	_assert_false(
		result,
		"adv-16/a — can_fuse must return false when get_slot(0) returns null even if get_slot(1) is filled (AND requires both valid AND filled per FRH-2)"
	)

	partial_mgr.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-17  5-cycle endurance — fill→fuse repeated 5 times; apply_fusion_effect
#          call count must equal 5; slots empty at the end of each cycle.
#
# Vulnerability exposed: An implementation that introduces any per-cycle state
# accumulation (e.g., a call history list, a counter that gates further calls,
# a timer that is never reset) would deviate on cycles 2+ from the expected
# behaviour. Also detects off-by-one counting bugs in call count tracking.
# ---------------------------------------------------------------------------

func test_adv_17_five_cycle_endurance_apply_count_and_slots_clean_each_cycle() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-17/five-cycle-endurance"):
		return
	if _require_resolve_fusion(resolver, "adv-17/five-cycle-endurance"):
		resolver.free()
		return

	var manager: Object = _make_manager()
	if manager == null:
		_fail("adv-17/five-cycle-endurance", "MutationSlotManager could not be instantiated; skipping")
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()

	for i: int in range(5):
		var id_a: String = "cycle_a_" + str(i)
		var id_b: String = "cycle_b_" + str(i)
		manager.fill_next_available(id_a)
		manager.fill_next_available(id_b)
		resolver.call("resolve_fusion", manager, player)

		_assert_false(
			manager.get_slot(0).is_filled(),
			"adv-17/cycle" + str(i + 1) + "/slot-a — slot A must be empty after cycle " + str(i + 1)
		)
		_assert_false(
			manager.get_slot(1).is_filled(),
			"adv-17/cycle" + str(i + 1) + "/slot-b — slot B must be empty after cycle " + str(i + 1)
		)
		_assert_eq_int(
			i + 1,
			player.apply_fusion_effect_call_count,
			"adv-17/cycle" + str(i + 1) + "/count — apply_fusion_effect call count must be " + str(i + 1) + " after cycle " + str(i + 1)
		)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# ADV-18  resolve_fusion(null, valid_player) confirm asymmetric null guard.
#          Addressed via ADV-15; this test covers the ADDITIONAL invariant
#          that can_fuse is NOT internally called on the player argument —
#          i.e. only manager is passed to can_fuse, not player.
#
# Vulnerability exposed: A scrambled implementation that passes player as the
# slot_manager argument to can_fuse would try to call .get_slot() on the
# PlayerDouble and crash (or accidentally return false silently while
# consuming nothing). This test verifies that resolve_fusion(null, player)
# and resolve_fusion(player_as_mgr, null) behave differently (the latter
# is covered by ADV-05 for the "bad type" case).
#
# Here we verify that the null manager path produces zero apply calls
# (which only holds if can_fuse received manager=null, not player as manager).
# ---------------------------------------------------------------------------

func test_adv_18_resolve_fusion_manager_null_player_valid_apply_not_called() -> void:
	var resolver: Object = _make_resolver()
	if _require_resolver(resolver, "adv-18/asymmetric-null-guard"):
		return
	if _require_resolve_fusion(resolver, "adv-18/asymmetric-null-guard"):
		resolver.free()
		return

	var player: PlayerDouble = PlayerDouble.new()

	resolver.call("resolve_fusion", null, player)

	# can_fuse(null) must have returned false → resolve is a no-op.
	_assert_eq_int(
		0,
		player.apply_fusion_effect_call_count,
		"adv-18/a — apply_fusion_effect must NOT be called when manager=null regardless of player validity (can_fuse(null) must return false per FRH-2-AC-5)"
	)

	# The player double must still be in its initial state (no partial apply).
	_assert_true(
		absf(player.last_duration - (-1.0)) < 0.0001,
		"adv-18/b — player.last_duration must remain at sentinel -1.0 (apply_fusion_effect was never called)"
	)
	_assert_true(
		absf(player.last_multiplier - (-1.0)) < 0.0001,
		"adv-18/c — player.last_multiplier must remain at sentinel -1.0 (apply_fusion_effect was never called)"
	)

	player.free_self()
	resolver.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- tests/fusion/test_fusion_resolver_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_adv_01_double_fuse_second_call_is_noop()
	test_adv_02_guard_bypass_resolve_on_empty_manager_no_effect()
	test_adv_03_can_fuse_returns_false_when_get_slot_returns_null()
	test_adv_04_resolve_fusion_noop_when_get_slot_returns_null()
	test_adv_05_wrong_player_type_slots_consumed_no_crash()
	test_adv_06_constants_unchanged_after_resolve_fusion()
	test_adv_07_constants_are_positive()
	test_adv_08_two_cycle_fuse_second_call_args_same_as_first()
	test_adv_09_partial_slot_a_only_guard_blocks_state_preserved()
	test_adv_10_partial_slot_b_only_guard_blocks_state_preserved()
	test_adv_11_both_slots_empty_resolve_fusion_is_noop()
	test_adv_12_determinism_two_resolver_instances_identical_outputs()
	test_adv_13_resolver_isolation_no_cross_manager_contamination()
	test_adv_14_can_fuse_does_not_modify_slot_state()
	test_adv_15_resolve_fusion_null_manager_valid_player_no_crash_no_apply()
	test_adv_16_partial_null_slot_double_can_fuse_false_no_crash()
	test_adv_17_five_cycle_endurance_apply_count_and_slots_clean_each_cycle()
	test_adv_18_resolve_fusion_manager_null_player_valid_apply_not_called()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
