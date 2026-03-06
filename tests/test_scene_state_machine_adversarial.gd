#
# test_scene_state_machine_adversarial.gd
#
# Adversarial and edge-case tests for the Milestone 4 scene state machine
# logic module. These tests are designed to expose spec gaps and hidden
# vulnerabilities in API shape, configuration invariants, and long-sequence
# behavior beyond the primary behavioral suite.
#
# Ticket: scene_state_machine.md
#

class_name SceneStateMachineAdversarialTests
extends Object


const ALLOWED_STATES: Array[String] = [
	"BASELINE",
	"INFECTION_DEMO",
	"ENEMY_PLAYTEST",
]

const CONFIG_KEYS: Array[String] = [
	"enable_infection_loop",
	"enable_enemies",
	"enable_prototype_hud",
]


var _pass_count: int = 0
var _fail_count: int = 0


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


func _assert_eq_string(expected: String, actual: String, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected '" + expected + "', got '" + actual + "'")


func _load_scene_state_machine_script() -> GDScript:
	return load("res://scripts/scene_state_machine.gd") as GDScript


func _make_machine() -> Object:
	var script: GDScript = _load_scene_state_machine_script()
	if script == null:
		return null
	return script.new()


func _has_required_api(machine: Object) -> bool:
	return (
		machine.has_method("get_state_id")
		and machine.has_method("get_config")
		and machine.has_method("apply_event")
	)


func _state_of(machine: Object) -> String:
	return machine.get_state_id()


func _config_of(machine: Object) -> Dictionary:
	return machine.get_config()


func _assert_state_allowed(state: String, test_name: String) -> void:
	if ALLOWED_STATES.has(state):
		_pass(test_name)
	else:
		_fail(
			test_name,
			"state '" + state + "' is not in ALLOWED_STATES " + str(ALLOWED_STATES)
		)


func _assert_config_keys_exact(config: Dictionary, test_name: String) -> void:
	var keys: Array = config.keys()
	keys.sort()
	var expected: Array = CONFIG_KEYS.duplicate()
	expected.sort()
	if keys == expected:
		_pass(test_name)
	else:
		_fail(
			test_name,
			"config keys " + str(keys) + " do not exactly match expected " + str(expected)
		)


func _baseline_config() -> Dictionary:
	return {
		"enable_infection_loop": false,
		"enable_enemies": false,
		"enable_prototype_hud": true,
	}


func _infection_demo_config() -> Dictionary:
	return {
		"enable_infection_loop": true,
		"enable_enemies": false,
		"enable_prototype_hud": true,
	}


func _enemy_playtest_config() -> Dictionary:
	return {
		"enable_infection_loop": false,
		"enable_enemies": true,
		"enable_prototype_hud": true,
	}


func _configs_equal(a: Dictionary, b: Dictionary) -> bool:
	for key in CONFIG_KEYS:
		if not a.has(key) or not b.has(key):
			return false
		if bool(a[key]) != bool(b[key]):
			return false
	return true


func _apply_event(machine: Object, event_id) -> void:
	# Intentionally accept any type here; tests will exercise non-String values.
	machine.apply_event(event_id)


func _run_event_sequence(events: Array) -> Array:
	var machine: Object = _make_machine()
	if machine == null or not _has_required_api(machine):
		return []

	var trace: Array = []
	for event_id in events:
		_apply_event(machine, event_id)
		var state: String = _state_of(machine)
		var config: Dictionary = _config_of(machine)
		trace.append(
			{
				"state": state,
				"config": {
					"enable_infection_loop": bool(config.get("enable_infection_loop", false)),
					"enable_enemies": bool(config.get("enable_enemies", false)),
					"enable_prototype_hud": bool(config.get("enable_prototype_hud", false)),
				},
			}
		)
	return trace


# ---------------------------------------------------------------------------
# Adversarial configuration shape and type checks
# ---------------------------------------------------------------------------

func test_config_has_exact_expected_keys_and_bool_values() -> void:
	var machine: Object = _make_machine()
	if machine == null:
		_fail(
			"ssm_adv_config_keys_and_types",
			"SceneStateMachine script missing; cannot verify config shape"
		)
		return

	if not _has_required_api(machine):
		_fail(
			"ssm_adv_config_keys_and_types_api_missing",
			"SceneStateMachine must implement get_state_id(), get_config(), apply_event(event_id: String)"
		)
		return

	var config: Dictionary = _config_of(machine)
	_assert_config_keys_exact(
		config,
		"ssm_adv_config_keys_exact — config exposes only the canonical three flags"
	)

	var all_bools: bool = true
	for key in CONFIG_KEYS:
		if typeof(config[key]) != TYPE_BOOL:
			all_bools = false
			break

	_assert_true(
		all_bools,
		"ssm_adv_config_values_are_bools — all config values are strictly bool"
	)


# ---------------------------------------------------------------------------
# CHECKPOINT: config mutability vs internal state protection
# ---------------------------------------------------------------------------

func test_mutating_returned_config_does_not_change_internal_state() -> void:
	# CHECKPOINT
	var machine: Object = _make_machine()
	if machine == null:
		_fail(
			"ssm_adv_config_mutation_checkpoint",
			"SceneStateMachine script missing; cannot verify config mutation semantics"
		)
		return

	if not _has_required_api(machine):
		_fail(
			"ssm_adv_config_mutation_checkpoint_api_missing",
			"SceneStateMachine must implement get_state_id(), get_config(), apply_event(event_id: String)"
		)
		return

	var original: Dictionary = _config_of(machine)

	# Mutate the dictionary the caller received.
	original["enable_infection_loop"] = true
	original["enable_enemies"] = true
	original["enable_prototype_hud"] = false

	# Freshly read config must remain at canonical baseline flags.
	var fresh: Dictionary = _config_of(machine)
	if not _configs_equal(fresh, _baseline_config()):
		_fail(
			"ssm_adv_config_mutation_checkpoint_baseline_preserved",
			"mutating returned config must not change internal SceneStateMachine state; expected baseline "
			+ str(_baseline_config())
			+ ", got "
			+ str(fresh)
		)
	else:
		_pass("ssm_adv_config_mutation_checkpoint_baseline_preserved — internal config unaffected by external mutation")


# ---------------------------------------------------------------------------
# CHECKPOINT: non-String and case-mismatched events
# ---------------------------------------------------------------------------

func test_non_string_events_are_treated_as_strict_noops() -> void:
	# CHECKPOINT
	var machine: Object = _make_machine()
	if machine == null:
		_fail(
			"ssm_adv_non_string_events_noop",
			"SceneStateMachine script missing; cannot verify non-String event behavior"
		)
		return

	if not _has_required_api(machine):
		_fail(
			"ssm_adv_non_string_events_noop_api_missing",
			"SceneStateMachine must implement get_state_id(), get_config(), apply_event(event_id: String)"
		)
		return

	var state_before: String = _state_of(machine)
	var config_before: Dictionary = _config_of(machine)

	_apply_event(machine, null)
	_apply_event(machine, 123)
	_apply_event(machine, true)

	var state_after: String = _state_of(machine)
	var config_after: Dictionary = _config_of(machine)

	_assert_eq_string(
		state_before,
		state_after,
		"ssm_adv_non_string_events_state_noop — non-String events leave state unchanged"
	)

	if not _configs_equal(config_before, config_after):
		_fail(
			"ssm_adv_non_string_events_config_noop",
			"non-String events must not change configuration; before="
			+ str(config_before)
			+ ", after="
			+ str(config_after)
		)
	else:
		_pass("ssm_adv_non_string_events_config_noop — non-String events leave configuration unchanged")


func test_case_mismatched_event_ids_are_treated_as_unknown_noops() -> void:
	# CHECKPOINT
	var machine: Object = _make_machine()
	if machine == null:
		_fail(
			"ssm_adv_case_mismatch_events_noop",
			"SceneStateMachine script missing; cannot verify case-mismatched events"
		)
		return

	if not _has_required_api(machine):
		_fail(
			"ssm_adv_case_mismatch_events_noop_api_missing",
			"SceneStateMachine must implement get_state_id(), get_config(), apply_event(event_id: String)"
		)
		return

	var state_before: String = _state_of(machine)
	var config_before: Dictionary = _config_of(machine)

	_apply_event(machine, "Select_Baseline")
	_apply_event(machine, "SELECT_INFECTION_DEMO")
	_apply_event(machine, "Select_Enemy_Playtest")

	var state_after: String = _state_of(machine)
	var config_after: Dictionary = _config_of(machine)

	_assert_eq_string(
		state_before,
		state_after,
		"ssm_adv_case_mismatch_events_state_noop — case-mismatched events leave state unchanged"
	)

	if not _configs_equal(config_before, config_after):
		_fail(
			"ssm_adv_case_mismatch_events_config_noop",
			"case-mismatched events must not change configuration; before="
			+ str(config_before)
			+ ", after="
			+ str(config_after)
		)
	else:
		_pass("ssm_adv_case_mismatch_events_config_noop — case-mismatched events leave configuration unchanged")


# ---------------------------------------------------------------------------
# Long-sequence and stress behavior
# ---------------------------------------------------------------------------

func test_long_mixed_event_sequence_never_leaves_canonical_states_or_configs() -> void:
	var machine: Object = _make_machine()
	if machine == null:
		_fail(
			"ssm_adv_long_sequence_canonical_states",
			"SceneStateMachine script missing; cannot verify long-sequence behavior"
		)
		return

	if not _has_required_api(machine):
		_fail(
			"ssm_adv_long_sequence_canonical_states_api_missing",
			"SceneStateMachine must implement get_state_id(), get_config(), apply_event(event_id: String)"
		)
		return

	var events: Array = []
	for i in 100:
		events.append("unknown_event_" + str(i))
		events.append("select_infection_demo")
		events.append("select_enemy_playtest")
		events.append("select_baseline")

	for event_id in events:
		_apply_event(machine, event_id)
		var state: String = _state_of(machine)
		var config: Dictionary = _config_of(machine)
		_assert_state_allowed(
			state,
			"ssm_adv_long_sequence_state_allowed — state remains within canonical set during long sequence"
		)

		if state == "BASELINE":
			if not _configs_equal(config, _baseline_config()):
				_fail(
					"ssm_adv_long_sequence_baseline_config",
					"BASELINE config drifted during long sequence; expected "
					+ str(_baseline_config())
					+ ", got "
					+ str(config)
				)
		elif state == "INFECTION_DEMO":
			if not _configs_equal(config, _infection_demo_config()):
				_fail(
					"ssm_adv_long_sequence_infection_demo_config",
					"INFECTION_DEMO config drifted during long sequence; expected "
					+ str(_infection_demo_config())
					+ ", got "
					+ str(config)
				)
		elif state == "ENEMY_PLAYTEST":
			if not _configs_equal(config, _enemy_playtest_config()):
				_fail(
					"ssm_adv_long_sequence_enemy_playtest_config",
					"ENEMY_PLAYTEST config drifted during long sequence; expected "
					+ str(_enemy_playtest_config())
					+ ", got "
					+ str(config)
				)


func test_unknown_events_do_not_change_trace_compared_to_filtered_sequence() -> void:
	var noisy_events: Array = [
		"select_infection_demo",
		"unknown_1",
		"select_enemy_playtest",
		"unknown_2",
		"select_baseline",
		"unknown_3",
		"select_enemy_playtest",
	]

	var filtered_events: Array = [
		"select_infection_demo",
		"select_enemy_playtest",
		"select_baseline",
		"select_enemy_playtest",
	]

	var noisy_trace: Array = _run_event_sequence(noisy_events)
	var filtered_trace: Array = _run_event_sequence(filtered_events)

	if noisy_trace.size() == 0 or filtered_trace.size() == 0:
		_fail(
			"ssm_adv_unknown_events_trace_equivalence",
			"SceneStateMachine script or API missing; cannot verify trace equivalence"
		)
		return

	var equivalent: bool = noisy_trace.size() == filtered_trace.size()
	if equivalent:
		for i in noisy_trace.size():
			var a = noisy_trace[i]
			var b = filtered_trace[i]
			if a["state"] != b["state"]:
				equivalent = false
				break
			if not _configs_equal(a["config"], b["config"]):
				equivalent = false
				break

	_assert_true(
		equivalent,
		"ssm_adv_unknown_events_trace_equivalence — inserting unknown events does not change state/config trace"
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_scene_state_machine_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_config_has_exact_expected_keys_and_bool_values()
	test_mutating_returned_config_does_not_change_internal_state()
	test_non_string_events_are_treated_as_strict_noops()
	test_case_mismatched_event_ids_are_treated_as_unknown_noops()
	test_long_mixed_event_sequence_never_leaves_canonical_states_or_configs()
	test_unknown_events_do_not_change_trace_compared_to_filtered_sequence()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

