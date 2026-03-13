# test_second_chunk_simulation.gd
#
# Headless unit tests for second-chunk detach mechanics in
# scripts/movement_simulation.gd (SPEC-SCL-1 through SPEC-SCL-6).
#
# This file is a plain Object subclass. It does not extend Node or SceneTree.
# The entry point is run_all(), which is called by tests/run_tests.gd.
#
# It may also be invoked via:
#   godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd
#
# Spec coverage:
#   SPEC-SCL-1 — MovementState.has_chunk_2: bool = true (field declaration, default)
#   SPEC-SCL-2 — simulate() never sets has_chunk_2 = true; carry-forward only
#   SPEC-SCL-3 — Detach step 2 (step 19): detach_2_eligible condition; no-ops
#   SPEC-SCL-4 — simulate() 9-arg signature; detach_2_just_pressed as 9th arg;
#                8-arg call still works via default false
#   SPEC-SCL-5 — HP reduction on detach_2 (step 20); cumulative dual-detach
#   SPEC-SCL-6 — Independence invariant: has_chunk and has_chunk_2 are orthogonal
#
# NOTE: These tests are intentionally written to FAIL against the current
# implementation (8-arg simulate(), no has_chunk_2 field). They drive the
# implementation in Task 5 (red-green-refactor). Once the implementation adds:
#   - MovementState.has_chunk_2: bool = true
#   - simulate() 9th arg: detach_2_just_pressed: bool = false
#   - Steps 19 and 20 inside simulate()
# all tests here must pass.
#
# Checkpoint log (see project_board/CHECKPOINTS.md):
#   [second_chunk_logic] Test Designer — 9th arg position (last, after delta)
#   [second_chunk_logic] Test Designer — HP step 20 reads result.current_hp not prior

class_name SecondChunkSimulationTests
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
		_fail(test_name, "got " + str(a) + " expected " + str(b) + " (delta " + str(abs(a - b)) + ")")


# ---------------------------------------------------------------------------
# Factory helper — constructs a default state. has_chunk_2 defaults to true
# per SPEC-SCL-1. Tests that need has_chunk_2=false set it explicitly.
# ---------------------------------------------------------------------------

func _make_state() -> MovementSimulation.MovementState:
	return MovementSimulation.MovementState.new()


func _make_state_with(vx: float, vy: float, on_floor: bool) -> MovementSimulation.MovementState:
	var s: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	s.velocity = Vector2(vx, vy)
	s.is_on_floor = on_floor
	return s


# ---------------------------------------------------------------------------
# Helper: call simulate() with 9 args (including detach_2_just_pressed as last).
# This is the canonical call form for tests in this file.
# ---------------------------------------------------------------------------

func _simulate_9(sim: MovementSimulation,
		prior: MovementSimulation.MovementState,
		detach_just_pressed: bool,
		detach_2_just_pressed: bool) -> MovementSimulation.MovementState:
	# Args: prior, input_axis, jump_pressed, jump_just_pressed,
	#        is_on_wall, wall_normal_x, detach_just_pressed, delta,
	#        detach_2_just_pressed
	return sim.simulate(prior, 0.0, false, false, false, 0.0,
		detach_just_pressed, 0.016, detach_2_just_pressed)


# Helper: call simulate() with 8 args (existing call sites).
func _simulate_8(sim: MovementSimulation,
		prior: MovementSimulation.MovementState) -> MovementSimulation.MovementState:
	return sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)


# ===========================================================================
# SPEC-SCL-1 — MovementState.has_chunk_2 field declaration and default
# ===========================================================================

# AC-SCL-1.1: MovementState.new() produces has_chunk_2 == true (default value).
func test_scl1_has_chunk_2_default_is_true() -> void:
	var state: MovementSimulation.MovementState = _make_state()
	_assert_true(state.has_chunk_2 == true,
		"spec-scl-1/AC-1.1 — MovementState.new().has_chunk_2 == true (default)")


# AC-SCL-1.2: has_chunk_2 field is writable — can be set to false.
func test_scl1_has_chunk_2_is_writable_false() -> void:
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk_2 = false
	_assert_false(state.has_chunk_2,
		"spec-scl-1/AC-1.2 — has_chunk_2 is writable (can be set to false)")


# AC-SCL-1.3: has_chunk_2 field is writable back to true.
func test_scl1_has_chunk_2_is_writable_true() -> void:
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk_2 = false
	state.has_chunk_2 = true
	_assert_true(state.has_chunk_2 == true,
		"spec-scl-1/AC-1.3 — has_chunk_2 is writable back to true")


# AC-SCL-1.4: has_chunk_2 is accessible on the result of simulate() (field exists).
func test_scl1_simulate_result_has_chunk_2_accessible() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	# 9-arg call: detach_2_just_pressed=false → has_chunk_2 carries forward
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, false)
	_assert_true(result.has_chunk_2 == true,
		"spec-scl-1/AC-1.4 — result.has_chunk_2 accessible; carries forward true on no-op frame")


# AC-SCL-1.5: has_chunk and has_chunk_2 are both present and independently default to true.
func test_scl1_both_chunk_fields_default_true() -> void:
	var state: MovementSimulation.MovementState = _make_state()
	_assert_true(state.has_chunk == true,
		"spec-scl-1/AC-1.5a — has_chunk defaults true")
	_assert_true(state.has_chunk_2 == true,
		"spec-scl-1/AC-1.5b — has_chunk_2 defaults true independently")


# ===========================================================================
# SPEC-SCL-2 — simulate() never sets has_chunk_2 = true (carry-forward only)
# ===========================================================================

# AC-SCL-2.1: simulate() does not mutate prior_state.has_chunk_2 when it is true.
func test_scl2_prior_state_has_chunk_2_not_mutated_when_true() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	var _result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_true(prior.has_chunk_2 == true,
		"spec-scl-2/AC-2.1 — prior_state.has_chunk_2=true not mutated by simulate()")


# AC-SCL-2.2: simulate() does not mutate prior_state.has_chunk_2 when it is false.
func test_scl2_prior_state_has_chunk_2_not_mutated_when_false() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = false
	var _result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_false(prior.has_chunk_2,
		"spec-scl-2/AC-2.2 — prior_state.has_chunk_2=false not mutated by simulate()")


# AC-SCL-2.3: After detach_2 fires (false transition), next frame with detach_2=false
# does NOT restore has_chunk_2 to true.
func test_scl2_simulate_never_sets_has_chunk_2_true_after_detach() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Frame 1: detach_2 fires → result.has_chunk_2 becomes false
	var prior_f1: MovementSimulation.MovementState = _make_state()
	prior_f1.has_chunk_2 = true
	var result_f1: MovementSimulation.MovementState = _simulate_9(sim, prior_f1, false, true)
	_assert_false(result_f1.has_chunk_2,
		"spec-scl-2/AC-2.3a — after detach_2 fires, result_f1.has_chunk_2=false")

	# Frame 2: detach_2_just_pressed=false, prior.has_chunk_2=false → must remain false
	var result_f2: MovementSimulation.MovementState = _simulate_9(sim, result_f1, false, false)
	_assert_false(result_f2.has_chunk_2,
		"spec-scl-2/AC-2.3b — simulate() does not restore has_chunk_2 to true on next frame")


# AC-SCL-2.4: With prior.has_chunk_2=false and detach_2=true, result is still false
# (not re-detached, not restored — deterministic no-op).
func test_scl2_simulate_never_sets_has_chunk_2_true_any_input() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = false

	# detach_2=false: carry-forward
	var result_a: MovementSimulation.MovementState = _simulate_9(sim, prior, false, false)
	_assert_false(result_a.has_chunk_2,
		"spec-scl-2/AC-2.4a — has_chunk_2=false + detach_2=false: stays false")

	# detach_2=true: no-op (chunk already detached — simulate() never sets true)
	var result_b: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_false(result_b.has_chunk_2,
		"spec-scl-2/AC-2.4b — has_chunk_2=false + detach_2=true: stays false (no recall in simulate)")


# ===========================================================================
# SPEC-SCL-3 — Detach step 2 (step 19): condition, result, and no-ops
# ===========================================================================

# AC-SCL-3.1: detach_2 fires when detach_2_just_pressed=true AND prior.has_chunk_2=true.
# Result: result.has_chunk_2 == false.
func test_scl3_detach_2_fires_when_pressed_and_has_chunk_2_true() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_false(result.has_chunk_2,
		"spec-scl-3/AC-3.1 — detach_2_just_pressed=true + has_chunk_2=true → result.has_chunk_2=false")


# AC-SCL-3.2: detach_2 is a no-op when prior.has_chunk_2=false (chunk already detached),
# even if detach_2_just_pressed=true. Result carries forward as false.
func test_scl3_detach_2_noop_when_has_chunk_2_false() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = false
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_false(result.has_chunk_2,
		"spec-scl-3/AC-3.2 — detach_2_just_pressed=true + has_chunk_2=false: no-op, carries false")


# AC-SCL-3.3: detach_2 is a no-op when detach_2_just_pressed=false,
# even if prior.has_chunk_2=true. Result carries forward as true.
func test_scl3_detach_2_noop_when_just_pressed_false() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, false)
	_assert_true(result.has_chunk_2 == true,
		"spec-scl-3/AC-3.3 — detach_2_just_pressed=false + has_chunk_2=true: carry-forward true")


# AC-SCL-3.4: detach_2 step does NOT affect any field other than has_chunk_2.
# Specifically: velocity, is_on_floor, has_chunk are unaffected.
func test_scl3_detach_2_does_not_affect_other_fields() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Reference: no detach_2 press
	var prior_ref: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_ref.has_chunk_2 = true
	var result_ref: MovementSimulation.MovementState = _simulate_9(sim, prior_ref, false, false)

	# detach_2 fires: same everything, only detach_2_just_pressed=true
	var prior_d2: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_d2.has_chunk_2 = true
	var result_d2: MovementSimulation.MovementState = _simulate_9(sim, prior_d2, false, true)

	# has_chunk_2 should differ (detach fired), but no other field should be affected
	_assert_false(result_d2.has_chunk_2,
		"spec-scl-3/AC-3.4a — detach_2 fired (has_chunk_2=false)")
	_assert_approx(result_d2.velocity.x, result_ref.velocity.x,
		"spec-scl-3/AC-3.4b — detach_2 does not affect velocity.x")
	_assert_approx(result_d2.velocity.y, result_ref.velocity.y,
		"spec-scl-3/AC-3.4c — detach_2 does not affect velocity.y")
	_assert_true(result_d2.is_on_floor == result_ref.is_on_floor,
		"spec-scl-3/AC-3.4d — detach_2 does not affect is_on_floor")


# AC-SCL-3.5: has_chunk_2 carry-forward across multiple no-detach frames (true).
func test_scl3_has_chunk_2_carry_forward_true_multiple_frames() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk_2 = true

	state = _simulate_9(sim, state, false, false)
	_assert_true(state.has_chunk_2 == true,
		"spec-scl-3/AC-3.5a — carry-forward frame 1: has_chunk_2 still true")
	state = _simulate_9(sim, state, false, false)
	_assert_true(state.has_chunk_2 == true,
		"spec-scl-3/AC-3.5b — carry-forward frame 2: has_chunk_2 still true")
	state = _simulate_9(sim, state, false, false)
	_assert_true(state.has_chunk_2 == true,
		"spec-scl-3/AC-3.5c — carry-forward frame 3: has_chunk_2 still true")


# AC-SCL-3.6: has_chunk_2 carry-forward across multiple no-detach frames (false).
func test_scl3_has_chunk_2_carry_forward_false_multiple_frames() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk_2 = false

	state = _simulate_9(sim, state, false, false)
	_assert_false(state.has_chunk_2,
		"spec-scl-3/AC-3.6a — false carry-forward frame 1")
	state = _simulate_9(sim, state, false, false)
	_assert_false(state.has_chunk_2,
		"spec-scl-3/AC-3.6b — false carry-forward frame 2")
	state = _simulate_9(sim, state, false, false)
	_assert_false(state.has_chunk_2,
		"spec-scl-3/AC-3.6c — false carry-forward frame 3")


# ===========================================================================
# SPEC-SCL-4 — simulate() 9-argument signature
# ===========================================================================

# AC-SCL-4.1: 9-arg simulate() call succeeds and returns a non-null result.
# This verifies the 9th arg is accepted without parse/runtime error.
func test_scl4_nine_arg_signature_callable() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	# Full 9-arg call: prior, input_axis, jump_pressed, jump_just_pressed,
	#                  is_on_wall, wall_normal_x, detach_just_pressed, delta,
	#                  detach_2_just_pressed
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016, false)
	_assert_true(result != null,
		"spec-scl-4/AC-4.1 — 9-arg simulate() call succeeds and returns non-null")


# AC-SCL-4.2: 8-arg simulate() call still works (detach_2_just_pressed defaults to false).
# All existing call sites remain valid without modification.
func test_scl4_eight_arg_call_still_works_with_default() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	# 8-arg call — omits detach_2_just_pressed, which defaults to false
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_true(result != null,
		"spec-scl-4/AC-4.2a — 8-arg simulate() still works (backward compat)")
	# With detach_2_just_pressed defaulting to false, has_chunk_2 must carry forward
	_assert_true(result.has_chunk_2 == true,
		"spec-scl-4/AC-4.2b — 8-arg call: has_chunk_2 carries forward true (default=false is no-op)")


# AC-SCL-4.3: detach_2_just_pressed as 9th arg (after delta) affects has_chunk_2.
# Verifies positional argument ordering: the 9th arg is detach_2, not 8th.
func test_scl4_detach_2_just_pressed_is_ninth_positional_arg() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	# 9-arg call with detach_2_just_pressed=true in position 9 (after delta=0.016)
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016, true)
	_assert_false(result.has_chunk_2,
		"spec-scl-4/AC-4.3 — detach_2_just_pressed=true as 9th arg causes detach_2 to fire")


# AC-SCL-4.4: 8-arg call with prior.has_chunk_2=false: no detach (default false is no-op),
# has_chunk_2 stays false. Confirms existing call sites do not trigger detach_2.
func test_scl4_eight_arg_call_no_detach_2_side_effect() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = false
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_false(result.has_chunk_2,
		"spec-scl-4/AC-4.4 — 8-arg call: has_chunk_2=false carries forward (no accidental detach)")


# AC-SCL-4.5: 9-arg call with detach_2_just_pressed=false is a no-op on has_chunk_2.
# Confirms the default behavior matches an explicit false pass.
func test_scl4_nine_arg_false_matches_eight_arg_default() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true

	var result_8: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	var result_9: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016, false)

	_assert_true(result_8.has_chunk_2 == result_9.has_chunk_2,
		"spec-scl-4/AC-4.5 — 8-arg and 9-arg(false) produce identical has_chunk_2")


# ===========================================================================
# SPEC-SCL-5 — HP reduction on detach_2 (step 20)
# ===========================================================================

# AC-SCL-5.1: Detaching chunk 2 reduces HP by hp_cost_per_detach.
# Default: prior_hp=100.0, cost=25.0 → result.current_hp=75.0
func test_scl5_hp_reduced_on_detach_2() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	prior.current_hp = 100.0
	# sim defaults: hp_cost_per_detach=25.0, min_hp=0.0
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_approx(result.current_hp, 75.0,
		"spec-scl-5/AC-5.1 — detach_2: HP reduced from 100 to 75 (cost=25)")


# AC-SCL-5.2: No HP reduction when detach_2_just_pressed=false (no-op frame).
# HP must carry forward unchanged.
func test_scl5_hp_not_reduced_when_no_detach_2() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	prior.current_hp = 100.0
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, false)
	_assert_approx(result.current_hp, 100.0,
		"spec-scl-5/AC-5.2 — no detach_2: HP carries forward at 100")


# AC-SCL-5.3: No HP reduction when has_chunk_2=false (chunk already detached),
# even with detach_2_just_pressed=true. This is the no-op path for an already-detached chunk.
func test_scl5_hp_not_reduced_when_has_chunk_2_already_false() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = false
	prior.current_hp = 60.0
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_approx(result.current_hp, 60.0,
		"spec-scl-5/AC-5.3 — detach_2 no-op (has_chunk_2=false): HP not reduced")


# AC-SCL-5.4: HP floor clamp on detach_2. When remaining HP would go below min_hp,
# result.current_hp is clamped to min_hp.
# Example: prior_hp=10.0, cost=25.0, min_hp=0.0 → max(0.0, -15.0) = 0.0
func test_scl5_hp_floor_clamp_on_detach_2() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	prior.current_hp = 10.0
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_approx(result.current_hp, 0.0,
		"spec-scl-5/AC-5.4 — HP floor clamp: 10.0 - 25.0 clamped to min_hp=0.0")


# AC-SCL-5.5: HP step 20 reads result.current_hp (output of step 18), not prior_state.current_hp.
# Dual detach on same frame: detach chunk 1 AND chunk 2 simultaneously.
# Both HP reductions are cumulative: 100 - 25 (chunk 1) = 75, then 75 - 25 (chunk 2) = 50.
func test_scl5_dual_detach_same_frame_hp_cumulative() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	prior.current_hp = 100.0
	# Both detach_just_pressed=true AND detach_2_just_pressed=true on same frame
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016, true)
	_assert_false(result.has_chunk,
		"spec-scl-5/AC-5.5a — dual detach: has_chunk=false")
	_assert_false(result.has_chunk_2,
		"spec-scl-5/AC-5.5b — dual detach: has_chunk_2=false")
	_assert_approx(result.current_hp, 50.0,
		"spec-scl-5/AC-5.5c — dual detach: HP reduced twice cumulatively (100→75→50)")


# AC-SCL-5.6: Dual detach same frame, HP floor clamp on second reduction.
# prior_hp=20.0, cost=25.0: after step 18 → max(0, -5)=0.0; after step 20 → max(0, -25)=0.0.
func test_scl5_dual_detach_hp_floor_clamp_on_second_reduction() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	prior.current_hp = 20.0
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016, true)
	_assert_approx(result.current_hp, 0.0,
		"spec-scl-5/AC-5.6 — dual detach floor clamp: 20→(20-25→0)→(0-25→0) = 0.0")


# AC-SCL-5.7: Detach only chunk 1 on a frame with prior.current_hp=100.
# Step 18 fires (chunk 1 detached) → HP=75; step 20 is no-op (detach_2 not pressed).
func test_scl5_detach_chunk_1_only_hp_reduced_once() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	prior.current_hp = 100.0
	# Only chunk 1 detach (detach_2_just_pressed=false, so step 20 is no-op)
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016, false)
	_assert_false(result.has_chunk,
		"spec-scl-5/AC-5.7a — chunk 1 detached")
	_assert_true(result.has_chunk_2 == true,
		"spec-scl-5/AC-5.7b — chunk 2 still attached")
	_assert_approx(result.current_hp, 75.0,
		"spec-scl-5/AC-5.7c — HP reduced once for chunk 1 only (100→75)")


# AC-SCL-5.8: Detach only chunk 2 on a frame with prior.current_hp=100.
# Step 18 is no-op (chunk 1 not detached); step 20 fires → HP=75.
func test_scl5_detach_chunk_2_only_hp_reduced_once() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	prior.current_hp = 100.0
	# Only chunk 2 detach
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016, true)
	_assert_true(result.has_chunk == true,
		"spec-scl-5/AC-5.8a — chunk 1 still attached")
	_assert_false(result.has_chunk_2,
		"spec-scl-5/AC-5.8b — chunk 2 detached")
	_assert_approx(result.current_hp, 75.0,
		"spec-scl-5/AC-5.8c — HP reduced once for chunk 2 only (100→75)")


# ===========================================================================
# SPEC-SCL-6 — Independence invariant: has_chunk and has_chunk_2 are orthogonal
# ===========================================================================

# AC-SCL-6.1: has_chunk=true, has_chunk_2=true (start state) — both carry forward.
func test_scl6_independence_both_true_carry_forward() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, false)
	_assert_true(result.has_chunk == true,
		"spec-scl-6/AC-6.1a — both=true: has_chunk carries forward true")
	_assert_true(result.has_chunk_2 == true,
		"spec-scl-6/AC-6.1b — both=true: has_chunk_2 carries forward true")


# AC-SCL-6.2: has_chunk=false, has_chunk_2=true — independent carry-forward.
func test_scl6_independence_chunk1_false_chunk2_true() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = false
	prior.has_chunk_2 = true
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, false)
	_assert_false(result.has_chunk,
		"spec-scl-6/AC-6.2a — chunk1=false, chunk2=true: has_chunk stays false")
	_assert_true(result.has_chunk_2 == true,
		"spec-scl-6/AC-6.2b — chunk1=false, chunk2=true: has_chunk_2 stays true")


# AC-SCL-6.3: has_chunk=true, has_chunk_2=false — independent carry-forward.
func test_scl6_independence_chunk1_true_chunk2_false() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = false
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, false)
	_assert_true(result.has_chunk == true,
		"spec-scl-6/AC-6.3a — chunk1=true, chunk2=false: has_chunk stays true")
	_assert_false(result.has_chunk_2,
		"spec-scl-6/AC-6.3b — chunk1=true, chunk2=false: has_chunk_2 stays false")


# AC-SCL-6.4: has_chunk=false, has_chunk_2=false — both carry forward false.
func test_scl6_independence_both_false_carry_forward() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = false
	prior.has_chunk_2 = false
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, false)
	_assert_false(result.has_chunk,
		"spec-scl-6/AC-6.4a — both=false: has_chunk stays false")
	_assert_false(result.has_chunk_2,
		"spec-scl-6/AC-6.4b — both=false: has_chunk_2 stays false")


# AC-SCL-6.5: Detaching chunk 1 does NOT affect has_chunk_2.
func test_scl6_detach_chunk_1_does_not_affect_has_chunk_2() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	# Only detach_just_pressed=true (chunk 1 only)
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, true, false)
	_assert_false(result.has_chunk,
		"spec-scl-6/AC-6.5a — detach chunk 1: has_chunk=false")
	_assert_true(result.has_chunk_2 == true,
		"spec-scl-6/AC-6.5b — detach chunk 1 does NOT affect has_chunk_2 (stays true)")


# AC-SCL-6.6: Detaching chunk 2 does NOT affect has_chunk.
func test_scl6_detach_chunk_2_does_not_affect_has_chunk() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	# Only detach_2_just_pressed=true (chunk 2 only)
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_true(result.has_chunk == true,
		"spec-scl-6/AC-6.6a — detach chunk 2 does NOT affect has_chunk (stays true)")
	_assert_false(result.has_chunk_2,
		"spec-scl-6/AC-6.6b — detach chunk 2: has_chunk_2=false")


# AC-SCL-6.7: With chunk1=false, detaching chunk 2 only fires detach_2 — has_chunk unchanged.
func test_scl6_detach_chunk_2_when_chunk_1_already_detached() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = false   # chunk 1 already detached
	prior.has_chunk_2 = true
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_false(result.has_chunk,
		"spec-scl-6/AC-6.7a — has_chunk stays false when detaching chunk 2")
	_assert_false(result.has_chunk_2,
		"spec-scl-6/AC-6.7b — has_chunk_2 becomes false on detach_2")


# AC-SCL-6.8: With chunk2=false, detaching chunk 1 only fires detach_1 — has_chunk_2 unchanged.
func test_scl6_detach_chunk_1_when_chunk_2_already_detached() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = false   # chunk 2 already detached
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, true, false)
	_assert_false(result.has_chunk,
		"spec-scl-6/AC-6.8a — has_chunk becomes false on detach_1")
	_assert_false(result.has_chunk_2,
		"spec-scl-6/AC-6.8b — has_chunk_2 stays false when detaching chunk 1")


# ===========================================================================
# has_chunk_2 carry-forward across multiple frames (cross-spec)
# ===========================================================================

# Multi-frame carry-forward: has_chunk_2 persists false across several frames
# when no detach is pressed, showing stable state tracking across ticks.
func test_carry_forward_has_chunk_2_false_across_frames_after_detach() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Frame 1: detach fires
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk_2 = true
	state = _simulate_9(sim, state, false, true)
	_assert_false(state.has_chunk_2,
		"carry-fwd — frame 1 (detach fired): has_chunk_2=false")

	# Frames 2-4: no detach press; has_chunk_2 must stay false each frame
	state = _simulate_9(sim, state, false, false)
	_assert_false(state.has_chunk_2,
		"carry-fwd — frame 2 (no detach): has_chunk_2 stays false")
	state = _simulate_9(sim, state, false, false)
	_assert_false(state.has_chunk_2,
		"carry-fwd — frame 3 (no detach): has_chunk_2 stays false")
	state = _simulate_9(sim, state, false, false)
	_assert_false(state.has_chunk_2,
		"carry-fwd — frame 4 (no detach): has_chunk_2 stays false")


# Multi-frame carry-forward: has_chunk_2 persists true across several frames
# when no detach is pressed (normal gameplay — chunk attached throughout).
func test_carry_forward_has_chunk_2_true_across_frames_no_detach() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk_2 = true

	for _i: int in range(5):
		state = _simulate_9(sim, state, false, false)
	_assert_true(state.has_chunk_2 == true,
		"carry-fwd — 5 frames with no detach: has_chunk_2 remains true throughout")


# ===========================================================================
# Non-functional: engine agnosticism (SPEC-SCL-9)
# ===========================================================================

# simulate() with 9 args completes headlessly without engine API access.
# Exercises both the detach_2=true and detach_2=false code paths.
func test_nf_simulate_9_arg_is_engine_agnostic() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()

	var result_with_detach_2: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016, true)
	var result_without_detach_2: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016, false)

	_assert_true(result_with_detach_2 != null,
		"nf — 9-arg simulate(detach_2=true) completes headlessly")
	_assert_true(result_without_detach_2 != null,
		"nf — 9-arg simulate(detach_2=false) completes headlessly")


# ===========================================================================
# Determinism
# ===========================================================================

# Identical 9-arg inputs must produce identical has_chunk_2 output.
func test_determinism_has_chunk_2_identical_inputs() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(50.0, -100.0, false)
	prior.has_chunk_2 = true

	var result_a: MovementSimulation.MovementState = sim.simulate(
		prior, 0.5, true, false, false, 0.0, false, 0.02, true)
	var result_b: MovementSimulation.MovementState = sim.simulate(
		prior, 0.5, true, false, false, 0.0, false, 0.02, true)
	_assert_true(result_a.has_chunk_2 == result_b.has_chunk_2,
		"determinism — identical 9-arg inputs produce identical has_chunk_2 output")


# Dual detach is deterministic: same prior + same inputs → same result.
func test_determinism_dual_detach_same_frame() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	prior.current_hp = 100.0

	var result_a: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016, true)
	var result_b: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016, true)

	_assert_true(result_a.has_chunk == result_b.has_chunk,
		"determinism — dual detach: has_chunk identical across runs")
	_assert_true(result_a.has_chunk_2 == result_b.has_chunk_2,
		"determinism — dual detach: has_chunk_2 identical across runs")
	_assert_approx(result_a.current_hp, result_b.current_hp,
		"determinism — dual detach: current_hp identical across runs")


# ===========================================================================
# Public entry point
# ===========================================================================

func run_all() -> int:
	print("--- test_second_chunk_simulation.gd ---")
	_pass_count = 0
	_fail_count = 0

	# SPEC-SCL-1: has_chunk_2 field declaration and default
	test_scl1_has_chunk_2_default_is_true()
	test_scl1_has_chunk_2_is_writable_false()
	test_scl1_has_chunk_2_is_writable_true()
	test_scl1_simulate_result_has_chunk_2_accessible()
	test_scl1_both_chunk_fields_default_true()

	# SPEC-SCL-2: simulate() never sets has_chunk_2 = true
	test_scl2_prior_state_has_chunk_2_not_mutated_when_true()
	test_scl2_prior_state_has_chunk_2_not_mutated_when_false()
	test_scl2_simulate_never_sets_has_chunk_2_true_after_detach()
	test_scl2_simulate_never_sets_has_chunk_2_true_any_input()

	# SPEC-SCL-3: Detach step 2 (step 19)
	test_scl3_detach_2_fires_when_pressed_and_has_chunk_2_true()
	test_scl3_detach_2_noop_when_has_chunk_2_false()
	test_scl3_detach_2_noop_when_just_pressed_false()
	test_scl3_detach_2_does_not_affect_other_fields()
	test_scl3_has_chunk_2_carry_forward_true_multiple_frames()
	test_scl3_has_chunk_2_carry_forward_false_multiple_frames()

	# SPEC-SCL-4: 9-arg signature
	test_scl4_nine_arg_signature_callable()
	test_scl4_eight_arg_call_still_works_with_default()
	test_scl4_detach_2_just_pressed_is_ninth_positional_arg()
	test_scl4_eight_arg_call_no_detach_2_side_effect()
	test_scl4_nine_arg_false_matches_eight_arg_default()

	# SPEC-SCL-5: HP reduction on detach_2
	test_scl5_hp_reduced_on_detach_2()
	test_scl5_hp_not_reduced_when_no_detach_2()
	test_scl5_hp_not_reduced_when_has_chunk_2_already_false()
	test_scl5_hp_floor_clamp_on_detach_2()
	test_scl5_dual_detach_same_frame_hp_cumulative()
	test_scl5_dual_detach_hp_floor_clamp_on_second_reduction()
	test_scl5_detach_chunk_1_only_hp_reduced_once()
	test_scl5_detach_chunk_2_only_hp_reduced_once()

	# SPEC-SCL-6: Independence invariant
	test_scl6_independence_both_true_carry_forward()
	test_scl6_independence_chunk1_false_chunk2_true()
	test_scl6_independence_chunk1_true_chunk2_false()
	test_scl6_independence_both_false_carry_forward()
	test_scl6_detach_chunk_1_does_not_affect_has_chunk_2()
	test_scl6_detach_chunk_2_does_not_affect_has_chunk()
	test_scl6_detach_chunk_2_when_chunk_1_already_detached()
	test_scl6_detach_chunk_1_when_chunk_2_already_detached()

	# Carry-forward (cross-spec)
	test_carry_forward_has_chunk_2_false_across_frames_after_detach()
	test_carry_forward_has_chunk_2_true_across_frames_no_detach()

	# Non-functional
	test_nf_simulate_9_arg_is_engine_agnostic()

	# Determinism
	test_determinism_has_chunk_2_identical_inputs()
	test_determinism_dual_detach_same_frame()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
