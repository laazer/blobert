#
# test_enemy_state_machine.gd
#
# Primary behavioral tests for the Milestone 2 enemy state machine logic module.
# These tests treat `EnemyStateMachine` as a pure, deterministic module with no
# Node or scene dependencies, instantiated directly via `EnemyStateMachine.new()`.
# They verify the canonical state set, core weaken → infect → dead transitions,
# determinism, and per-instance isolation.
#
# Ticket: enemy_state_machine.md
# Planner/Spec checkpoints:
#   - Enemy state machine is a pure logic module (no Node dependencies).
#   - Canonical states for this ticket: Idle, Active, Weakened, Infected, Dead.
#   - Module consumes discrete events (weaken hit, infection while weakened,
#     absorb/kill resolution) and exposes lifecycle state for other systems.
#

class_name EnemyStateMachineTests
extends "res://tests/utils/test_utils.gd"


const ALLOWED_STATES: Array[String] = [
	"idle",
	"active",
	"weakened",
	"infected",
	"dead",
]


var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _assert_state(expected: String, actual: String, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(
			test_name,
			"expected state '" + expected + "', got '" + actual + "'"
		)


func _assert_state_allowed(actual: String, test_name: String) -> void:
	if ALLOWED_STATES.has(actual):
		_pass(test_name)
	else:
		_fail(
			test_name,
			"state '" + actual + "' is not in ALLOWED_STATES " + str(ALLOWED_STATES)
		)


func _make_machine() -> EnemyStateMachine:
	var machine: EnemyStateMachine = EnemyStateMachine.new()
	return machine


func _state_of(machine: EnemyStateMachine) -> String:
	return machine.get_state()


# ---------------------------------------------------------------------------
# Structure and headless instantiability
# ---------------------------------------------------------------------------

func test_instantiation_succeeds_headless() -> void:
	var machine: EnemyStateMachine = _make_machine()
	_assert_true(
		machine != null,
		"esm_structure_instantiation_non_null — EnemyStateMachine.new() returns non-null object in headless context"
	)


func test_initial_state_is_idle() -> void:
	var machine: EnemyStateMachine = _make_machine()
	var state: String = _state_of(machine)
	_assert_state(
		"idle",
		state,
		"esm_state_initial_idle — fresh EnemyStateMachine starts in 'idle' state"
	)
	_assert_state_allowed(
		state,
		"esm_state_initial_allowed — initial state is within canonical set"
	)


func test_reset_restores_idle_from_non_idle() -> void:
	var machine: EnemyStateMachine = _make_machine()
	# Drive into a non-idle state then reset.
	machine.apply_weaken_event()
	var weakened_state: String = _state_of(machine)
	_assert_state(
		"weakened",
		weakened_state,
		"esm_reset_precondition_weakened — apply_weaken_event() from idle reaches 'weakened'"
	)

	machine.reset()
	var reset_state: String = _state_of(machine)
	_assert_state(
		"idle",
		reset_state,
		"esm_reset_restores_idle — reset() returns machine to 'idle' from non-idle state"
	)


# ---------------------------------------------------------------------------
# Core transitions: weaken → infect → dead
# ---------------------------------------------------------------------------

func test_weaken_from_idle_transitions_to_weakened() -> void:
	var machine: EnemyStateMachine = _make_machine()
	machine.apply_weaken_event()
	var state: String = _state_of(machine)
	_assert_state(
		"weakened",
		state,
		"esm_transition_weaken_from_idle — weaken event from idle transitions to 'weakened'"
	)


func test_infect_from_weakened_transitions_to_infected() -> void:
	var machine: EnemyStateMachine = _make_machine()
	machine.apply_weaken_event()
	machine.apply_infection_event()
	var state: String = _state_of(machine)
	_assert_state(
		"infected",
		state,
		"esm_transition_infect_from_weakened — infection event from weakened transitions to 'infected'"
	)


func test_death_from_any_non_dead_transitions_to_dead() -> void:
	var machine: EnemyStateMachine = _make_machine()

	# Case 1: idle → dead.
	machine.apply_death_event()
	var state_idle_dead: String = _state_of(machine)
	_assert_state(
		"dead",
		state_idle_dead,
		"esm_transition_death_from_idle — death event from idle transitions to 'dead'"
	)

	# Case 2: weakened → dead.
	machine.reset()
	machine.apply_weaken_event()
	machine.apply_death_event()
	var state_weakened_dead: String = _state_of(machine)
	_assert_state(
		"dead",
		state_weakened_dead,
		"esm_transition_death_from_weakened — death event from weakened transitions to 'dead'"
	)

	# Case 3: infected → dead.
	machine.reset()
	machine.apply_weaken_event()
	machine.apply_infection_event()
	machine.apply_death_event()
	var state_infected_dead: String = _state_of(machine)
	_assert_state(
		"dead",
		state_infected_dead,
		"esm_transition_death_from_infected — death event from infected transitions to 'dead'"
	)


# ---------------------------------------------------------------------------
# No invalid or stuck states: disallowed event/state combinations are no-ops
# and state label is always within the canonical set.
# ---------------------------------------------------------------------------

func test_infect_while_not_weakened_is_noop() -> void:
	var machine: EnemyStateMachine = _make_machine()

	# Infect from idle: no-op.
	var before_idle: String = _state_of(machine)
	machine.apply_infection_event()
	var after_idle: String = _state_of(machine)
	_assert_state(
		before_idle,
		after_idle,
		"esm_noop_infect_from_idle — infection event from idle does not change state"
	)

	# Infect from infected: idempotent / no-op.
	machine.apply_weaken_event()
	machine.apply_infection_event()
	var infected_before: String = _state_of(machine)
	machine.apply_infection_event()
	var infected_after: String = _state_of(machine)
	_assert_state(
		infected_before,
		infected_after,
		"esm_noop_infect_from_infected — repeated infection leaves state at 'infected'"
	)


func test_weaken_on_already_weakened_is_noop() -> void:
	var machine: EnemyStateMachine = _make_machine()
	machine.apply_weaken_event()
	var weakened_before: String = _state_of(machine)
	machine.apply_weaken_event()
	var weakened_after: String = _state_of(machine)
	_assert_state(
		weakened_before,
		weakened_after,
		"esm_noop_weaken_from_weakened — weaken event while already weakened is a no-op"
	)


func test_events_after_dead_are_noops_and_state_remains_dead() -> void:
	var machine: EnemyStateMachine = _make_machine()
	machine.apply_weaken_event()
	machine.apply_infection_event()
	machine.apply_death_event()

	var dead_initial: String = _state_of(machine)
	_assert_state(
		"dead",
		dead_initial,
		"esm_dead_initial_state — precondition: machine is in 'dead' state"
	)

	machine.apply_weaken_event()
	machine.apply_infection_event()
	machine.apply_death_event()
	var dead_after: String = _state_of(machine)

	_assert_state(
		dead_initial,
		dead_after,
		"esm_noop_events_after_dead — weaken/infect/death after dead leave state at 'dead'"
	)


func test_state_label_always_within_allowed_set_for_mixed_sequence() -> void:
	var machine: EnemyStateMachine = _make_machine()

	var sequence: Array[String] = [
		"weaken",
		"infect",
		"death",
		"infect",
		"weaken",
		"death",
	]

	for idx in sequence.size():
		var step: String = sequence[idx]
		match step:
			"weaken":
				machine.apply_weaken_event()
			"infect":
				machine.apply_infection_event()
			"death":
				machine.apply_death_event()
			_:
				# No other steps used in this suite.
				pass

		var state: String = _state_of(machine)
		_assert_state_allowed(
			state,
			"esm_allowed_state_after_step_" + str(idx) + " — state label remains within canonical set after mixed sequence"
		)


# ---------------------------------------------------------------------------
# Determinism and per-instance isolation
# ---------------------------------------------------------------------------

func _run_event_sequence(events: Array[String]) -> Array[String]:
	var machine: EnemyStateMachine = _make_machine()
	var states: Array[String] = []

	for step in events:
		match step:
			"weaken":
				machine.apply_weaken_event()
			"infect":
				machine.apply_infection_event()
			"death":
				machine.apply_death_event()
			"reset":
				machine.reset()
			_:
				pass

		states.append(_state_of(machine))

	return states


func test_determinism_for_fixed_event_sequence() -> void:
	var events: Array[String] = [
		"weaken",
		"infect",
		"death",
		"reset",
		"weaken",
	]

	var first: Array[String] = _run_event_sequence(events)
	var second: Array[String] = _run_event_sequence(events)

	var deterministic: bool = first.size() == second.size()
	if deterministic:
		for i in first.size():
			if first[i] != second[i]:
				deterministic = false
				break

	_assert_true(
		deterministic,
		"esm_determinism_fixed_sequence — identical event sequences produce identical state traces"
	)


func test_two_instances_are_isolated() -> void:
	var a: EnemyStateMachine = _make_machine()
	var b: EnemyStateMachine = _make_machine()

	# Drive A through weaken → infect; B remains idle then only weakened.
	a.apply_weaken_event()
	a.apply_infection_event()

	var a_state: String = _state_of(a)
	var b_state_before: String = _state_of(b)

	_assert_state(
		"infected",
		a_state,
		"esm_isolation_a_infected — precondition: A reached 'infected' via weaken+infect"
	)
	_assert_state(
		"idle",
		b_state_before,
		"esm_isolation_b_initial_idle — B remains 'idle' while A transitions"
	)

	# Now apply weaken only to B.
	b.apply_weaken_event()
	var b_state_after: String = _state_of(b)
	_assert_state(
		"weakened",
		b_state_after,
		"esm_isolation_b_weakened — B transitions to 'weakened' independently of A"
	)

	# Confirm A remains infected and was not affected by B's transitions.
	var a_state_after: String = _state_of(a)
	_assert_state(
		a_state,
		a_state_after,
		"esm_isolation_a_unchanged — A's state unchanged when B transitions"
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_state_machine.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Structure and instantiation
	test_instantiation_succeeds_headless()
	test_initial_state_is_idle()
	test_reset_restores_idle_from_non_idle()

	# Core weaken → infect → dead transitions
	test_weaken_from_idle_transitions_to_weakened()
	test_infect_from_weakened_transitions_to_infected()
	test_death_from_any_non_dead_transitions_to_dead()

	# No invalid or stuck states
	test_infect_while_not_weakened_is_noop()
	test_weaken_on_already_weakened_is_noop()
	test_events_after_dead_are_noops_and_state_remains_dead()
	test_state_label_always_within_allowed_set_for_mixed_sequence()

	# Determinism and instance isolation
	test_determinism_for_fixed_event_sequence()
	test_two_instances_are_isolated()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

