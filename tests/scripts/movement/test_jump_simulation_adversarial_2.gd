# test_jump_simulation_adversarial_2.gd
#
# TB-J-014–TB-J-020 continuation of the jump adversarial suite (split from
# test_jump_simulation_adversarial.gd for MAX_FILE_LINES policy).

class_name JumpSimulationAdversarialTests2
extends "res://tests/utils/test_utils.gd"

const EPSILON: float = 1e-4

var _pass_count: int = 0
var _fail_count: int = 0


func _make_state_with(vx: float, vy: float, on_floor: bool) -> MovementSimulation.MovementState:
	var s: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	s.velocity = Vector2(vx, vy)
	s.is_on_floor = on_floor
	return s


# ---------------------------------------------------------------------------
# [M1-002] TB-J-014 — coyote_timer expires over multiple frames: jump blocked
# after window exhausted
#
# VULNERABILITY: This sequence test simulates a player walking off a ledge,
# then pressing jump after the coyote window expires. The multi-step scenario
# ensures the timer correctly drains across frames and the jump is blocked on
# the frame where the window has just closed.
# ---------------------------------------------------------------------------

func test_j014_coyote_window_expires_over_frames_jump_then_blocked() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	# sim.coyote_time = 0.1 (default). We'll use delta=0.016 per frame.
	# Frame 0: departure — prior.is_on_floor=true → result.coyote_timer=0.1
	var s0: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	s0.jump_consumed = false
	var s1: MovementSimulation.MovementState = sim.simulate(s0, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_approx(s1.coyote_timer, 0.1,
		"TB-J-014 — departure frame: coyote_timer reset to 0.1")

	# Frames 1–6: airborne, no jump. Each frame decrements by 0.016.
	# After 6 frames: 0.1 - 6*0.016 = 0.1 - 0.096 = 0.004 (still > 0, barely eligible)
	var current: MovementSimulation.MovementState = _make_state_with(0.0, s1.velocity.y, false)
	current.coyote_timer = s1.coyote_timer
	current.jump_consumed = s1.jump_consumed
	for i in range(6):
		var next: MovementSimulation.MovementState = sim.simulate(current, 0.0, false, false, false, 0.0, [false, false], 0.016)
		current = _make_state_with(0.0, next.velocity.y, false)
		current.coyote_timer = next.coyote_timer
		current.jump_consumed = next.jump_consumed

	# After 6 frames: coyote_timer ≈ 0.004 (still > 0, so jump should fire)
	_assert_true(current.coyote_timer > 0.0,
		"TB-J-014 — after 6 frames: coyote_timer > 0 (barely eligible)")
	var result_eligible: MovementSimulation.MovementState = sim.simulate(current, 0.0, true, true, false, 0.0, [false, false], 0.016)
	var expected_vy: float = -sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.016
	_assert_approx(result_eligible.velocity.y, expected_vy,
		"TB-J-014 — coyote jump fires when timer barely > 0 after 6 airborne frames")

	# Now simulate until coyote_timer reaches exactly 0
	# From 0.004 with delta=0.016: max(0, 0.004 - 0.016) = 0.0
	var s_expired: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	s_expired.coyote_timer = 0.004
	s_expired.jump_consumed = false
	var s_after_expiry: MovementSimulation.MovementState = sim.simulate(s_expired, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_approx(s_after_expiry.coyote_timer, 0.0,
		"TB-J-014 — timer expires (0.004 - 0.016 = 0.0 clamped)")

	# Jump attempt with expired timer: must be blocked
	var s_blocked: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	s_blocked.coyote_timer = 0.0
	s_blocked.jump_consumed = false
	var result_blocked: MovementSimulation.MovementState = sim.simulate(s_blocked, 0.0, true, true, false, 0.0, [false, false], 0.016)
	_assert_approx(result_blocked.velocity.y, 0.0 + 980.0 * 0.016,
		"TB-J-014 — jump blocked when coyote_timer=0.0 (expired window)")


# ---------------------------------------------------------------------------
# [M1-002] TB-J-015 — Config mutation between calls (coyote_time and jump_height)
#
# VULNERABILITY: Changing sim.coyote_time or sim.jump_height between calls must
# take effect immediately on the next call. An implementation that caches these
# values at initialization time (e.g., stored in a local variable in _init())
# would miss the mutation. This mirrors the existing M1-001 TB-008 pattern.
# ---------------------------------------------------------------------------

func test_j015a_coyote_time_mutation_takes_effect_immediately() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	# First call: default coyote_time=0.1 → on floor, timer resets to 0.1
	var prior1: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result1: MovementSimulation.MovementState = sim.simulate(prior1, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_approx(result1.coyote_timer, 0.1,
		"TB-J-015a — before mutation: on-floor reset gives coyote_timer=0.1")

	# Mutate coyote_time after first call
	sim.coyote_time = 0.25
	var prior2: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result2: MovementSimulation.MovementState = sim.simulate(prior2, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_approx(result2.coyote_timer, 0.25,
		"TB-J-015a — after mutation to 0.25: on-floor reset gives coyote_timer=0.25")


func test_j015b_jump_height_mutation_takes_effect_immediately() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	# First jump with default height
	var prior1: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior1.jump_consumed = false
	var result1: MovementSimulation.MovementState = sim.simulate(prior1, 0.0, true, true, false, 0.0, [false, false], 0.0)
	var impulse1: float = result1.velocity.y  # delta=0 isolates impulse

	# Mutate jump_height
	sim.jump_height = 30.0
	var prior2: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior2.jump_consumed = false
	var result2: MovementSimulation.MovementState = sim.simulate(prior2, 0.0, true, true, false, 0.0, [false, false], 0.0)
	var impulse2: float = result2.velocity.y
	var expected_impulse2: float = -sqrt(2.0 * 980.0 * 30.0)

	_assert_approx(impulse2, expected_impulse2,
		"TB-J-015b — jump_height mutated to 30.0: new impulse = -sqrt(2*980*30)")
	_assert_true(impulse1 != impulse2,
		"TB-J-015b — mutated jump_height produces different impulse than original")


# ---------------------------------------------------------------------------
# [M1-002] TB-J-016 — Coyote jump sets jump_consumed=true, preventing immediate
# re-jump even from coyote eligibility on the next frame
#
# VULNERABILITY: After a coyote jump fires, jump_consumed=true. On the next
# airborne frame, even if coyote_timer was not yet fully decremented (still
# residually > 0 in prior result), the consumed flag must block a second
# coyote jump. An implementation that forgets to check jump_consumed when
# is_on_floor=false would allow a double-coyote-jump.
# ---------------------------------------------------------------------------

func test_j016_coyote_jump_sets_consumed_blocks_second_coyote_attempt() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Frame 1: coyote jump fires
	var s0: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	s0.coyote_timer = 0.05
	s0.jump_consumed = false
	var s1: MovementSimulation.MovementState = sim.simulate(s0, 0.0, true, true, false, 0.0, [false, false], 0.016)
	# Jump fires: s1.jump_consumed=true, s1.coyote_timer = max(0, 0.05-0.016) = 0.034
	_assert_true(s1.jump_consumed == true,
		"TB-J-016 — coyote jump frame: jump_consumed=true")
	_assert_approx(s1.coyote_timer, 0.034,
		"TB-J-016 — coyote jump frame: coyote_timer decremented to 0.034")

	# Frame 2: still airborne, coyote_timer=0.034>0, but consumed=true → must block
	var s1_carry: MovementSimulation.MovementState = _make_state_with(0.0, s1.velocity.y, false)
	s1_carry.coyote_timer = s1.coyote_timer  # 0.034 > 0
	s1_carry.jump_consumed = s1.jump_consumed  # true
	var s2: MovementSimulation.MovementState = sim.simulate(s1_carry, 0.0, true, true, false, 0.0, [false, false], 0.016)
	# consumed=true blocks jump even with coyote_timer=0.034>0
	var expected_vy: float = s1.velocity.y + 980.0 * 0.016
	_assert_approx(s2.velocity.y, expected_vy,
		"TB-J-016 — frame after coyote jump: consumed=true blocks second coyote attempt")
	_assert_true(s2.jump_consumed == true,
		"TB-J-016 — consumed remains true in air after blocked second coyote attempt")


# ---------------------------------------------------------------------------
# [M1-002] TB-J-017 — Determinism: identical adversarial inputs produce
# identical outputs across multiple calls
#
# VULNERABILITY: Confirms the simulation has no hidden mutable internal state
# that would cause different results for identical inputs called sequentially.
# Especially relevant if any implementation accidentally stores frame-specific
# scratch variables as instance fields.
# ---------------------------------------------------------------------------

func test_j017_determinism_coyote_jump_scenario() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.coyote_timer = 0.05
	prior.jump_consumed = false

	var result_a: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, [false, false], 0.016)
	var result_b: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, [false, false], 0.016)

	_assert_approx(result_a.velocity.y, result_b.velocity.y,
		"TB-J-017 — determinism: coyote jump produces identical velocity.y on repeat calls")
	_assert_approx(result_a.coyote_timer, result_b.coyote_timer,
		"TB-J-017 — determinism: coyote jump produces identical coyote_timer on repeat calls")
	_assert_true(result_a.jump_consumed == result_b.jump_consumed,
		"TB-J-017 — determinism: jump_consumed identical across repeat calls")


func test_j017b_determinism_jump_cut_scenario() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, -450.0, false)
	prior.jump_consumed = true

	var result_a: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	var result_b: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)

	_assert_approx(result_a.velocity.y, result_b.velocity.y,
		"TB-J-017b — determinism: jump cut produces identical velocity.y on repeat calls")


# ---------------------------------------------------------------------------
# [M1-002] TB-J-018 — Negative coyote_time config: timer behavior
#
# VULNERABILITY: negative coyote_time is undefined behavior per spec. On the
# floor frame, result.coyote_timer = self.coyote_time = negative value, which
# is never > 0.0, so no coyote jumps are possible. The result must be finite
# and not NaN. Also: with a negative coyote_time reset, the airborne decrement
# max(0.0, negative - delta) = 0.0, so it clamps immediately.
# CHECKPOINT
# ---------------------------------------------------------------------------

func test_j018_negative_coyote_time_produces_finite_timer_no_coyote_window() -> void:
	# CHECKPOINT
	var sim: MovementSimulation = MovementSimulation.new()
	sim.coyote_time = -0.1  # negative: undefined behavior but must not crash
	var prior_floor: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior_floor.jump_consumed = false
	var result_floor: MovementSimulation.MovementState = sim.simulate(prior_floor, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_true(is_finite(result_floor.coyote_timer),
		"TB-J-018 — negative coyote_time: result.coyote_timer is finite on floor frame")
	# result.coyote_timer = coyote_time = -0.1 (negative). Not > 0.0 → no coyote window.
	_assert_false(result_floor.coyote_timer > 0.0,
		"TB-J-018 — negative coyote_time: timer not > 0.0 (no coyote window)")

	# Airborne frame with negative prior coyote_timer: max(0, -0.1 - delta) = 0.0
	var prior_air: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_air.coyote_timer = -0.1
	prior_air.jump_consumed = false
	var result_air: MovementSimulation.MovementState = sim.simulate(prior_air, 0.0, true, true, false, 0.0, [false, false], 0.016)
	_assert_approx(result_air.coyote_timer, 0.0,
		"TB-J-018 — negative timer, airborne: max(0, -0.1 - 0.016) = 0.0 (clamped)")
	# No coyote jump: prior.coyote_timer = -0.1, which is NOT > 0.0
	var expected_vy: float = 0.0 + 980.0 * 0.016
	_assert_approx(result_air.velocity.y, expected_vy,
		"TB-J-018 — negative coyote_timer in prior: no coyote jump (not > 0.0)")


# ---------------------------------------------------------------------------
# [M1-002] TB-J-019 — Jump with horizontal movement simultaneously
#
# VULNERABILITY: Confirms jump impulse is applied only to velocity.y and does
# not accidentally interact with the horizontal velocity calculation. An
# implementation that erroneously applies some impulse component to velocity.x
# (e.g., from a copy-paste bug) would fail this test.
# ---------------------------------------------------------------------------

func test_j019_horizontal_velocity_independent_of_jump_impulse() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var ms: float = sim.max_speed
	var prior: MovementSimulation.MovementState = _make_state_with(ms, 0.0, true)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, true, true, false, 0.0, [false, false], 0.016)
	_assert_approx(result.velocity.x, ms,
		"TB-J-019 — horizontal at max_speed unaffected by simultaneous jump impulse")
	# Vertical: jump impulse applied
	var expected_vy: float = -sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected_vy,
		"TB-J-019 — vertical jump impulse unaffected by horizontal movement")


# ---------------------------------------------------------------------------
# [M1-002] TB-J-020 — Jump cut does not apply to horizontal velocity
#
# VULNERABILITY: The jump cut condition clamps result.velocity.y only. An
# implementation with a copy-paste error might accidentally clamp velocity.x
# using the same condition. This test confirms velocity.x is unchanged by
# jump cut logic.
# ---------------------------------------------------------------------------

func test_j020_jump_cut_does_not_affect_velocity_x() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	# Ascending fast horizontally — jump cut should only touch velocity.y
	var prior: MovementSimulation.MovementState = _make_state_with(180.0, -450.0, false)
	prior.jump_consumed = true
	# jump_pressed=false → cut condition: -450+15.68=-434.32 < -200 → clamp vy to -200
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, false, 0.0, [false, false], 0.016)
	var step: float = sim.acceleration * 0.016
	_assert_approx(result.velocity.x, 180.0 + step,
		"TB-J-020 — jump cut does not affect velocity.x (horizontal += one accel step toward max_speed)")
	_assert_approx(result.velocity.y, -200.0,
		"TB-J-020 — jump cut clamps velocity.y to -200.0 as expected")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_jump_simulation_adversarial_2.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_j014_coyote_window_expires_over_frames_jump_then_blocked()
	test_j015a_coyote_time_mutation_takes_effect_immediately()
	test_j015b_jump_height_mutation_takes_effect_immediately()
	test_j016_coyote_jump_sets_consumed_blocks_second_coyote_attempt()
	test_j017_determinism_coyote_jump_scenario()
	test_j017b_determinism_jump_cut_scenario()
	test_j018_negative_coyote_time_produces_finite_timer_no_coyote_window()
	test_j019_horizontal_velocity_independent_of_jump_impulse()
	test_j020_jump_cut_does_not_affect_velocity_x()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

