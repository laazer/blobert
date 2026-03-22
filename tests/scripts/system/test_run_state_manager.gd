#
# test_run_state_manager.gd
#
# Primary behavioral tests for RunStateManager.
# All tests are headlessly verifiable: no Node, scene tree, or physics required.
# The implementation is loaded via load().new() and driven by apply_event().
# Signal emission is verified via Callable flag mechanics.
#
# Ticket: run_state_manager
# Spec:   agent_context/agents/2_spec/run_state_manager_spec.md
#
# Test IDs covered:
#   RSM-STRUCT-1 through RSM-STRUCT-4
#   RSM-TRANS-1  through RSM-TRANS-5
#   RSM-SIGNAL-1 through RSM-SIGNAL-6
#   RSM-RESET-1  through RSM-RESET-2
#   RSM-NOOP-1   through RSM-NOOP-4
#
# NOTE: get_state_id() returns uppercase strings ("START", "ACTIVE", "DEAD", "WIN").
# The task prompt mentions lowercase "start" for RSM-STRUCT-3 but the ticket and spec
# both specify uppercase. The ticket governs per spec section "Overview".
#

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


func _assert_eq_int(expected: int, actual: int, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected " + str(expected) + ", got " + str(actual))


func _assert_eq_string(expected: String, actual: String, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected '" + expected + "', got '" + actual + "'")


func _load_rsm_script() -> GDScript:
	return load("res://scripts/system/run_state_manager.gd") as GDScript


func _make_rsm() -> Object:
	var script: GDScript = _load_rsm_script()
	if script == null:
		return null
	return script.new()


# ---------------------------------------------------------------------------
# RSM-STRUCT: Script load, initial state, slot manager presence
# ---------------------------------------------------------------------------

func test_rsm_struct_1_script_loads_non_null() -> void:
	# RSM-STRUCT-1: Script exists at res://scripts/system/run_state_manager.gd and is loadable.
	var script: GDScript = _load_rsm_script()
	if script == null:
		_fail(
			"RSM-STRUCT-1",
			"load('res://scripts/system/run_state_manager.gd') returned null; file missing or parse error"
		)
		return
	var instance: Object = script.new()
	if instance == null:
		_fail("RSM-STRUCT-1", "script.new() returned null")
		return
	_pass("RSM-STRUCT-1 — script loads non-null and instantiates")
	instance.free()


func test_rsm_struct_2_initial_state_is_start_enum() -> void:
	# RSM-STRUCT-2: get_state() returns State.START (0) on a fresh instance.
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-STRUCT-2", "RunStateManager script missing or failed to instantiate")
		return
	var state_val: int = rsm.get_state()
	_assert_eq_int(
		0,
		state_val,
		"RSM-STRUCT-2 — get_state() returns State.START (0) on fresh instance"
	)
	rsm.free()


func test_rsm_struct_3_initial_state_id_is_start() -> void:
	# RSM-STRUCT-3: get_state_id() returns "START" on a fresh instance.
	# Spec and ticket require uppercase. Task prompt lowercase discrepancy is resolved
	# by the ticket governing per spec Overview note.
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-STRUCT-3", "RunStateManager script missing or failed to instantiate")
		return
	var state_id: String = rsm.get_state_id()
	_assert_eq_string(
		"START",
		state_id,
		"RSM-STRUCT-3 — get_state_id() returns 'START' on fresh instance"
	)
	rsm.free()


func test_rsm_struct_4_get_slot_manager_returns_non_null() -> void:
	# RSM-STRUCT-4: get_slot_manager() returns a non-null object on fresh instance.
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-STRUCT-4", "RunStateManager script missing or failed to instantiate")
		return
	var slot_mgr: Object = rsm.get_slot_manager()
	if slot_mgr == null:
		_fail("RSM-STRUCT-4", "get_slot_manager() returned null; expected MutationSlotManager instance")
	else:
		_pass("RSM-STRUCT-4 — get_slot_manager() returns non-null")
	rsm.free()


# ---------------------------------------------------------------------------
# RSM-TRANS: State transitions via apply_event
# ---------------------------------------------------------------------------

func test_rsm_trans_1_start_run_from_start_reaches_active() -> void:
	# RSM-TRANS-1: apply_event("start_run") from START → state becomes ACTIVE (1).
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-TRANS-1", "RunStateManager script missing")
		return
	rsm.apply_event("start_run")
	_assert_eq_int(1, rsm.get_state(), "RSM-TRANS-1 — start_run from START reaches ACTIVE (1)")
	rsm.free()


func test_rsm_trans_2_player_died_from_active_reaches_dead() -> void:
	# RSM-TRANS-2: apply_event("player_died") from ACTIVE → state becomes DEAD (2).
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-TRANS-2", "RunStateManager script missing")
		return
	rsm.apply_event("start_run")
	rsm.apply_event("player_died")
	_assert_eq_int(2, rsm.get_state(), "RSM-TRANS-2 — player_died from ACTIVE reaches DEAD (2)")
	rsm.free()


func test_rsm_trans_3_run_won_from_active_reaches_win() -> void:
	# RSM-TRANS-3: apply_event("run_won") from ACTIVE → state becomes WIN (3).
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-TRANS-3", "RunStateManager script missing")
		return
	rsm.apply_event("start_run")
	rsm.apply_event("run_won")
	_assert_eq_int(3, rsm.get_state(), "RSM-TRANS-3 — run_won from ACTIVE reaches WIN (3)")
	rsm.free()


func test_rsm_trans_4_restart_from_dead_reaches_start() -> void:
	# RSM-TRANS-4: apply_event("restart") from DEAD → state becomes START (0).
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-TRANS-4", "RunStateManager script missing")
		return
	rsm.apply_event("start_run")
	rsm.apply_event("player_died")
	rsm.apply_event("restart")
	_assert_eq_int(0, rsm.get_state(), "RSM-TRANS-4 — restart from DEAD reaches START (0)")
	rsm.free()


func test_rsm_trans_5_restart_from_win_reaches_start() -> void:
	# RSM-TRANS-5: apply_event("restart") from WIN → state becomes START (0).
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-TRANS-5", "RunStateManager script missing")
		return
	rsm.apply_event("start_run")
	rsm.apply_event("run_won")
	rsm.apply_event("restart")
	_assert_eq_int(0, rsm.get_state(), "RSM-TRANS-5 — restart from WIN reaches START (0)")
	rsm.free()


# ---------------------------------------------------------------------------
# RSM-SIGNAL: Signal emission on each valid transition
# ---------------------------------------------------------------------------

func test_rsm_signal_1_run_started_emits_on_start_to_active() -> void:
	# RSM-SIGNAL-1: run_started signal emits on START→ACTIVE.
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-SIGNAL-1", "RunStateManager script missing")
		return
	var fired: bool = false
	rsm.connect("run_started", func(): fired = true)
	rsm.apply_event("start_run")
	_assert_true(fired, "RSM-SIGNAL-1 — run_started signal emits on START→ACTIVE")
	rsm.free()


func test_rsm_signal_2_player_died_emits_on_active_to_dead() -> void:
	# RSM-SIGNAL-2: player_died signal emits on ACTIVE→DEAD.
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-SIGNAL-2", "RunStateManager script missing")
		return
	rsm.apply_event("start_run")
	var fired: bool = false
	rsm.connect("player_died", func(): fired = true)
	rsm.apply_event("player_died")
	_assert_true(fired, "RSM-SIGNAL-2 — player_died signal emits on ACTIVE→DEAD")
	rsm.free()


func test_rsm_signal_3_run_won_emits_on_active_to_win() -> void:
	# RSM-SIGNAL-3: run_won signal emits on ACTIVE→WIN.
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-SIGNAL-3", "RunStateManager script missing")
		return
	rsm.apply_event("start_run")
	var fired: bool = false
	rsm.connect("run_won", func(): fired = true)
	rsm.apply_event("run_won")
	_assert_true(fired, "RSM-SIGNAL-3 — run_won signal emits on ACTIVE→WIN")
	rsm.free()


func test_rsm_signal_4_run_restarted_emits_on_dead_to_start() -> void:
	# RSM-SIGNAL-4: run_restarted signal emits on DEAD→START.
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-SIGNAL-4", "RunStateManager script missing")
		return
	rsm.apply_event("start_run")
	rsm.apply_event("player_died")
	var fired: bool = false
	rsm.connect("run_restarted", func(): fired = true)
	rsm.apply_event("restart")
	_assert_true(fired, "RSM-SIGNAL-4 — run_restarted signal emits on DEAD→START")
	rsm.free()


func test_rsm_signal_5_run_restarted_emits_on_win_to_start() -> void:
	# RSM-SIGNAL-5: run_restarted signal emits on WIN→START.
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-SIGNAL-5", "RunStateManager script missing")
		return
	rsm.apply_event("start_run")
	rsm.apply_event("run_won")
	var fired: bool = false
	rsm.connect("run_restarted", func(): fired = true)
	rsm.apply_event("restart")
	_assert_true(fired, "RSM-SIGNAL-5 — run_restarted signal emits on WIN→START")
	rsm.free()


func test_rsm_signal_6_emit_before_state_change() -> void:
	# RSM-SIGNAL-6: Signal fires BEFORE _state is updated (emit-first contract).
	# Connect to run_started; inside the handler, capture get_state().
	# After apply_event("start_run"), the captured state must equal State.START (0),
	# proving the state had not yet advanced to ACTIVE at emission time.
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-SIGNAL-6", "RunStateManager script missing")
		return
	var captured_state: int = -1
	rsm.connect("run_started", func(): captured_state = rsm.get_state())
	rsm.apply_event("start_run")
	_assert_eq_int(
		0,
		captured_state,
		"RSM-SIGNAL-6 — get_state() inside run_started handler equals State.START (0); signal fired before state updated"
	)
	rsm.free()


# ---------------------------------------------------------------------------
# RSM-RESET: Slot manager is cleared on DEAD and WIN transitions
# ---------------------------------------------------------------------------

func test_rsm_reset_1_slots_cleared_after_active_to_dead() -> void:
	# RSM-RESET-1: After filling slots, ACTIVE→DEAD clears them (any_filled() == false).
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-RESET-1", "RunStateManager script missing")
		return
	rsm.apply_event("start_run")
	var slot_mgr: Object = rsm.get_slot_manager()
	if slot_mgr == null:
		_fail("RSM-RESET-1", "get_slot_manager() returned null; cannot fill slots")
		rsm.free()
		return
	slot_mgr.fill_next_available("test_mutation_a")
	slot_mgr.fill_next_available("test_mutation_b")
	var filled_before: bool = slot_mgr.any_filled()
	if not filled_before:
		_fail(
			"RSM-RESET-1",
			"precondition failed: slots not filled after fill_next_available(); test inconclusive"
		)
		rsm.free()
		return
	rsm.apply_event("player_died")
	_assert_false(
		slot_mgr.any_filled(),
		"RSM-RESET-1 — slot manager any_filled() == false after ACTIVE→DEAD"
	)
	rsm.free()


func test_rsm_reset_2_slots_cleared_after_active_to_win() -> void:
	# RSM-RESET-2: After filling slots, ACTIVE→WIN clears them (any_filled() == false).
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-RESET-2", "RunStateManager script missing")
		return
	rsm.apply_event("start_run")
	var slot_mgr: Object = rsm.get_slot_manager()
	if slot_mgr == null:
		_fail("RSM-RESET-2", "get_slot_manager() returned null; cannot fill slots")
		rsm.free()
		return
	slot_mgr.fill_next_available("test_mutation_a")
	slot_mgr.fill_next_available("test_mutation_b")
	var filled_before: bool = slot_mgr.any_filled()
	if not filled_before:
		_fail(
			"RSM-RESET-2",
			"precondition failed: slots not filled after fill_next_available(); test inconclusive"
		)
		rsm.free()
		return
	rsm.apply_event("run_won")
	_assert_false(
		slot_mgr.any_filled(),
		"RSM-RESET-2 — slot manager any_filled() == false after ACTIVE→WIN"
	)
	rsm.free()


# ---------------------------------------------------------------------------
# RSM-NOOP: Invalid or wrong events are strict no-ops
# ---------------------------------------------------------------------------

func test_rsm_noop_1_player_died_from_start_is_noop() -> void:
	# RSM-NOOP-1: apply_event("player_died") from START → state stays START, no signal.
	# Spec RSM-NOOP-2 in ticket; corresponds to "Wrong event (player_died) in START is no-op".
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-NOOP-1", "RunStateManager script missing")
		return
	var signal_fired: bool = false
	rsm.connect("player_died", func(): signal_fired = true)
	rsm.apply_event("player_died")
	_assert_eq_int(0, rsm.get_state(), "RSM-NOOP-1 — state stays START after player_died from START")
	_assert_false(signal_fired, "RSM-NOOP-1 — no signal fires on no-op player_died from START")
	rsm.free()


func test_rsm_noop_2_start_run_from_active_is_noop() -> void:
	# RSM-NOOP-2: apply_event("start_run") from ACTIVE → state stays ACTIVE, no signal.
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-NOOP-2", "RunStateManager script missing")
		return
	rsm.apply_event("start_run")
	var signal_fired: bool = false
	rsm.connect("run_started", func(): signal_fired = true)
	rsm.apply_event("start_run")
	_assert_eq_int(1, rsm.get_state(), "RSM-NOOP-2 — state stays ACTIVE after start_run from ACTIVE")
	_assert_false(signal_fired, "RSM-NOOP-2 — no signal fires on no-op start_run from ACTIVE")
	rsm.free()


func test_rsm_noop_3_unknown_event_from_any_state_is_noop() -> void:
	# RSM-NOOP-3: apply_event("unknown_event") from any state → no state change, no crash.
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-NOOP-3", "RunStateManager script missing")
		return
	# Test from START
	rsm.apply_event("unknown_event")
	_assert_eq_int(0, rsm.get_state(), "RSM-NOOP-3 — unknown_event from START leaves state unchanged")
	# Advance to ACTIVE and test
	rsm.apply_event("start_run")
	rsm.apply_event("unknown_event")
	_assert_eq_int(1, rsm.get_state(), "RSM-NOOP-3 — unknown_event from ACTIVE leaves state unchanged")
	# Advance to DEAD and test
	rsm.apply_event("player_died")
	rsm.apply_event("unknown_event")
	_assert_eq_int(2, rsm.get_state(), "RSM-NOOP-3 — unknown_event from DEAD leaves state unchanged")
	rsm.free()


func test_rsm_noop_4_restart_from_start_is_noop() -> void:
	# RSM-NOOP-4: apply_event("restart") from START → state stays START, no signal.
	var rsm: Object = _make_rsm()
	if rsm == null:
		_fail("RSM-NOOP-4", "RunStateManager script missing")
		return
	var signal_fired: bool = false
	rsm.connect("run_restarted", func(): signal_fired = true)
	rsm.apply_event("restart")
	_assert_eq_int(0, rsm.get_state(), "RSM-NOOP-4 — state stays START after restart from START")
	_assert_false(signal_fired, "RSM-NOOP-4 — no signal fires on no-op restart from START")
	rsm.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_run_state_manager.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Structure
	test_rsm_struct_1_script_loads_non_null()
	test_rsm_struct_2_initial_state_is_start_enum()
	test_rsm_struct_3_initial_state_id_is_start()
	test_rsm_struct_4_get_slot_manager_returns_non_null()

	# Transitions
	test_rsm_trans_1_start_run_from_start_reaches_active()
	test_rsm_trans_2_player_died_from_active_reaches_dead()
	test_rsm_trans_3_run_won_from_active_reaches_win()
	test_rsm_trans_4_restart_from_dead_reaches_start()
	test_rsm_trans_5_restart_from_win_reaches_start()

	# Signals
	test_rsm_signal_1_run_started_emits_on_start_to_active()
	test_rsm_signal_2_player_died_emits_on_active_to_dead()
	test_rsm_signal_3_run_won_emits_on_active_to_win()
	test_rsm_signal_4_run_restarted_emits_on_dead_to_start()
	test_rsm_signal_5_run_restarted_emits_on_win_to_start()
	test_rsm_signal_6_emit_before_state_change()

	# Slot reset
	test_rsm_reset_1_slots_cleared_after_active_to_dead()
	test_rsm_reset_2_slots_cleared_after_active_to_win()

	# No-ops
	test_rsm_noop_1_player_died_from_start_is_noop()
	test_rsm_noop_2_start_run_from_active_is_noop()
	test_rsm_noop_3_unknown_event_from_any_state_is_noop()
	test_rsm_noop_4_restart_from_start_is_noop()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
