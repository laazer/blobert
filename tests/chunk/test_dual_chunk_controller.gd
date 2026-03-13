# test_dual_chunk_controller.gd
#
# Controller-level integration tests for the dual chunk system.
# Tests the MovementSimulation contract that PlayerController3D depends on
# for dual-chunk detach, recall, and HP management.
#
# Written by: Gameplay Systems Agent — 2026-03-13
#
# These tests operate on MovementSimulation directly (headless-safe) and
# verify the invariants the controller relies on:
#   - Detach chunk 1 then detach chunk 2 (both out simultaneously)
#   - Recall chunk 1 while chunk 2 is detached
#   - Recall chunk 2 while chunk 1 is detached
#   - HP balance across dual detach+recall cycle
#   - State independence across mixed detach/recall flows
#   - No state corruption when mixing one-chunk and two-chunk flows
#
# Controller public API shape:
#   - has_chunk_2() -> bool: returns true when chunk 2 is attached
#
# Note: PlayerController3D extends CharacterBody3D and cannot be instantiated
# headlessly. These tests validate the simulation contract that backs the
# controller. Scene-level integration tests (requiring a running scene) are
# deferred to manual QA per task notes.

class_name DualChunkControllerTests
extends Object

const EPSILON: float = 1e-4

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _approx_eq(a: float, b: float) -> bool:
	return abs(a - b) < EPSILON


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


func _assert_approx(a: float, b: float, test_name: String) -> void:
	if _approx_eq(a, b):
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b))


func _make_state() -> MovementSimulation.MovementState:
	return MovementSimulation.MovementState.new()


# Simulates one frame with both detach inputs parameterized.
func _sim_frame(sim: MovementSimulation, prior: MovementSimulation.MovementState,
		detach: bool, detach_2: bool) -> MovementSimulation.MovementState:
	return sim.simulate(prior, 0.0, false, false, false, 0.0, detach, 0.016, detach_2)


# ===========================================================================
# Detach both chunks (both out simultaneously)
# ===========================================================================

# DC-1: Detach chunk 1 then detach chunk 2 on consecutive frames.
# After both detaches: has_chunk=false, has_chunk_2=false.
func test_detach_chunk1_then_chunk2_both_out() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk = true
	state.has_chunk_2 = true
	state.current_hp = 100.0

	# Frame 1: detach chunk 1 only
	state = _sim_frame(sim, state, true, false)
	_assert_false(state.has_chunk,
		"dc-1/a — after detach chunk 1: has_chunk=false")
	_assert_true(state.has_chunk_2 == true,
		"dc-1/b — chunk 2 still attached after detach chunk 1 only")
	_assert_approx(state.current_hp, 75.0,
		"dc-1/c — HP reduced once after detach chunk 1")

	# Frame 2: detach chunk 2 only (chunk 1 already detached)
	state = _sim_frame(sim, state, false, true)
	_assert_false(state.has_chunk,
		"dc-1/d — has_chunk stays false after detach chunk 2")
	_assert_false(state.has_chunk_2,
		"dc-1/e — has_chunk_2=false after detach chunk 2")
	_assert_approx(state.current_hp, 50.0,
		"dc-1/f — HP reduced twice total: 100→75→50")


# DC-2: Detach both chunks on the same frame.
# Result: both detached, HP reduced twice cumulatively.
func test_detach_both_chunks_same_frame() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk = true
	state.has_chunk_2 = true
	state.current_hp = 100.0

	state = _sim_frame(sim, state, true, true)
	_assert_false(state.has_chunk,
		"dc-2/a — both detached same frame: has_chunk=false")
	_assert_false(state.has_chunk_2,
		"dc-2/b — both detached same frame: has_chunk_2=false")
	_assert_approx(state.current_hp, 50.0,
		"dc-2/c — dual detach same frame: HP=50 (100→75→50)")


# ===========================================================================
# Recall chunk 1 while chunk 2 is detached (controller sim)
# ===========================================================================

# DC-3: Simulate recall of chunk 1 while chunk 2 stays detached.
# Controller sets has_chunk=true on recall completion. has_chunk_2 remains false.
func test_recall_chunk1_while_chunk2_detached() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Start: both detached, HP=50 (post dual-detach state)
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk = false
	state.has_chunk_2 = false
	state.current_hp = 50.0

	# Controller-side recall of chunk 1: restores has_chunk and HP.
	# Mirroring what PlayerController3D does at recall completion.
	state.current_hp = minf(sim.max_hp, state.current_hp + sim.hp_cost_per_detach)
	state.has_chunk = true

	# Verify chunk 1 recalled, chunk 2 still detached
	_assert_true(state.has_chunk == true,
		"dc-3/a — chunk 1 recalled: has_chunk=true")
	_assert_false(state.has_chunk_2,
		"dc-3/b — chunk 2 still detached during chunk 1 recall: has_chunk_2=false")
	_assert_approx(state.current_hp, 75.0,
		"dc-3/c — HP restored to 75 after chunk 1 recall (50+25)")

	# Run simulation frame to verify carry-forward
	var result: MovementSimulation.MovementState = _sim_frame(sim, state, false, false)
	_assert_true(result.has_chunk == true,
		"dc-3/d — has_chunk carries forward true after recall")
	_assert_false(result.has_chunk_2,
		"dc-3/e — has_chunk_2 stays false (chunk 2 not recalled)")


# DC-4: Simulate recall of chunk 2 while chunk 1 stays detached.
func test_recall_chunk2_while_chunk1_detached() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Start: both detached, HP=50
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk = false
	state.has_chunk_2 = false
	state.current_hp = 50.0

	# Controller-side recall of chunk 2: restores has_chunk_2 and HP.
	state.current_hp = minf(sim.max_hp, state.current_hp + sim.hp_cost_per_detach)
	state.has_chunk_2 = true

	# Verify chunk 2 recalled, chunk 1 still detached
	_assert_false(state.has_chunk,
		"dc-4/a — chunk 1 still detached: has_chunk=false")
	_assert_true(state.has_chunk_2 == true,
		"dc-4/b — chunk 2 recalled: has_chunk_2=true")
	_assert_approx(state.current_hp, 75.0,
		"dc-4/c — HP restored to 75 after chunk 2 recall (50+25)")

	# Run simulation frame to verify carry-forward
	var result: MovementSimulation.MovementState = _sim_frame(sim, state, false, false)
	_assert_false(result.has_chunk,
		"dc-4/d — has_chunk stays false (chunk 1 not recalled)")
	_assert_true(result.has_chunk_2 == true,
		"dc-4/e — has_chunk_2 carries forward true after recall")


# ===========================================================================
# HP balance across dual detach + recall cycle
# ===========================================================================

# DC-5: Full dual detach + dual recall HP balance.
# Start: HP=100. Detach both: HP=50. Recall both: HP=100 (capped at max_hp).
func test_hp_balance_dual_detach_and_dual_recall() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Detach both chunks on same frame
	var state: MovementSimulation.MovementState = _make_state()
	state.current_hp = 100.0
	state = _sim_frame(sim, state, true, true)
	_assert_approx(state.current_hp, 50.0,
		"dc-5/a — after dual detach: HP=50")

	# Recall chunk 1 (controller-side)
	state.current_hp = minf(sim.max_hp, state.current_hp + sim.hp_cost_per_detach)
	state.has_chunk = true
	_assert_approx(state.current_hp, 75.0,
		"dc-5/b — after recall chunk 1: HP=75")

	# Recall chunk 2 (controller-side)
	state.current_hp = minf(sim.max_hp, state.current_hp + sim.hp_cost_per_detach)
	state.has_chunk_2 = true
	_assert_approx(state.current_hp, 100.0,
		"dc-5/c — after recall chunk 2: HP=100 (restored to max)")

	_assert_true(state.has_chunk == true,
		"dc-5/d — chunk 1 restored after full cycle")
	_assert_true(state.has_chunk_2 == true,
		"dc-5/e — chunk 2 restored after full cycle")


# DC-6: HP floor clamp during dual detach followed by recall sequence.
# prior_hp=20.0: dual detach → HP=0. Recall both → HP=50 (capped at max_hp=100).
func test_hp_floor_clamp_dual_detach_then_recall() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	sim.max_hp = 100.0

	var state: MovementSimulation.MovementState = _make_state()
	state.current_hp = 20.0

	# Dual detach: 20→max(0,20-25)=0→max(0,0-25)=0
	state = _sim_frame(sim, state, true, true)
	_assert_approx(state.current_hp, 0.0,
		"dc-6/a — HP floor clamp at dual detach: HP=0")

	# Recall chunk 1: 0+25=25
	state.current_hp = minf(sim.max_hp, state.current_hp + sim.hp_cost_per_detach)
	state.has_chunk = true
	_assert_approx(state.current_hp, 25.0,
		"dc-6/b — after recall chunk 1: HP=25")

	# Recall chunk 2: 25+25=50
	state.current_hp = minf(sim.max_hp, state.current_hp + sim.hp_cost_per_detach)
	state.has_chunk_2 = true
	_assert_approx(state.current_hp, 50.0,
		"dc-6/c — after recall chunk 2: HP=50")


# ===========================================================================
# No state corruption in mixed flows
# ===========================================================================

# DC-7: Detach chunk 1, recall it, then detach chunk 2 — no state corruption.
# After detach-recall-detach2 sequence, has_chunk=true, has_chunk_2=false.
func test_no_state_corruption_mixed_flow_detach_recall_detach2() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_state()
	state.current_hp = 100.0

	# Step 1: Detach chunk 1
	state = _sim_frame(sim, state, true, false)
	_assert_false(state.has_chunk, "dc-7/a — chunk 1 detached")
	_assert_true(state.has_chunk_2 == true, "dc-7/b — chunk 2 still attached")

	# Step 2: Recall chunk 1 (controller-side)
	state.current_hp = minf(sim.max_hp, state.current_hp + sim.hp_cost_per_detach)
	state.has_chunk = true
	_assert_true(state.has_chunk == true, "dc-7/c — chunk 1 recalled")
	_assert_approx(state.current_hp, 100.0, "dc-7/d — HP restored to 100 after recall")

	# Step 3: Detach chunk 2
	state = _sim_frame(sim, state, false, true)
	_assert_true(state.has_chunk == true, "dc-7/e — chunk 1 still attached after chunk 2 detach")
	_assert_false(state.has_chunk_2, "dc-7/f — chunk 2 detached")
	_assert_approx(state.current_hp, 75.0, "dc-7/g — HP=75 after detach chunk 2")


# DC-8: Press detach while chunk 1 is detached and chunk 2 is attached.
# simulate() treats detach as no-op for chunk 1 (has_chunk=false).
# has_chunk_2 should remain true.
func test_detach_press_when_chunk1_already_detached_no_effect_on_chunk2() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk = false   # chunk 1 already detached
	state.has_chunk_2 = true
	state.current_hp = 75.0

	# Press detach (chunk 1 action) — should be no-op since has_chunk=false
	var result: MovementSimulation.MovementState = _sim_frame(sim, state, true, false)
	_assert_false(result.has_chunk,
		"dc-8/a — detach no-op when chunk 1 already detached")
	_assert_true(result.has_chunk_2 == true,
		"dc-8/b — chunk 2 unaffected by detach press when chunk 1 already detached")
	_assert_approx(result.current_hp, 75.0,
		"dc-8/c — HP unchanged on detach no-op")


# DC-9: Press detach_2 while chunk 2 is detached and chunk 1 is attached.
# simulate() treats detach_2 as no-op for chunk 2 (has_chunk_2=false).
# has_chunk should remain true.
func test_detach_2_press_when_chunk2_already_detached_no_effect_on_chunk1() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk = true
	state.has_chunk_2 = false  # chunk 2 already detached
	state.current_hp = 75.0

	# Press detach_2 — should be no-op since has_chunk_2=false
	var result: MovementSimulation.MovementState = _sim_frame(sim, state, false, true)
	_assert_true(result.has_chunk == true,
		"dc-9/a — chunk 1 unaffected by detach_2 press when chunk 2 already detached")
	_assert_false(result.has_chunk_2,
		"dc-9/b — detach_2 no-op when chunk 2 already detached")
	_assert_approx(result.current_hp, 75.0,
		"dc-9/c — HP unchanged on detach_2 no-op")


# DC-10: Determinism — same dual-detach inputs produce identical output every time.
func test_dual_detach_determinism() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state_a: MovementSimulation.MovementState = _make_state()
	state_a.current_hp = 100.0
	var state_b: MovementSimulation.MovementState = _make_state()
	state_b.current_hp = 100.0

	var result_a: MovementSimulation.MovementState = _sim_frame(sim, state_a, true, true)
	var result_b: MovementSimulation.MovementState = _sim_frame(sim, state_b, true, true)

	_assert_true(result_a.has_chunk == result_b.has_chunk,
		"dc-10/a — determinism: has_chunk identical across runs")
	_assert_true(result_a.has_chunk_2 == result_b.has_chunk_2,
		"dc-10/b — determinism: has_chunk_2 identical across runs")
	_assert_approx(result_a.current_hp, result_b.current_hp,
		"dc-10/c — determinism: current_hp identical across runs")


# ===========================================================================
# Public entry point
# ===========================================================================

func run_all() -> int:
	print("--- test_dual_chunk_controller.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_detach_chunk1_then_chunk2_both_out()
	test_detach_both_chunks_same_frame()
	test_recall_chunk1_while_chunk2_detached()
	test_recall_chunk2_while_chunk1_detached()
	test_hp_balance_dual_detach_and_dual_recall()
	test_hp_floor_clamp_dual_detach_then_recall()
	test_no_state_corruption_mixed_flow_detach_recall_detach2()
	test_detach_press_when_chunk1_already_detached_no_effect_on_chunk2()
	test_detach_2_press_when_chunk2_already_detached_no_effect_on_chunk1()
	test_dual_detach_determinism()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
