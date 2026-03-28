#
# test_scene_state_machine.gd
#
# Primary behavioral tests for the Milestone 4 scene state machine logic module.
# These tests treat `SceneStateMachine` as a pure, deterministic module with no
# Node or scene dependencies. It is instantiated directly via
# `SceneStateMachine.new()` (or via its script) and driven by symbolic selection
# events.
#
# Ticket: scene_state_machine.md
# Spec/checkpoints:
#   - Canonical states (this ticket): BASELINE, INFECTION_DEMO, ENEMY_PLAYTEST.
#   - Configuration surface: enable_infection_loop, enable_enemies,
#     enable_prototype_hud.
#   - Public event model: explicit selection events only
#     ("select_baseline", "select_infection_demo", "select_enemy_playtest").
#   - Initial state: BASELINE with infection/enemies disabled, HUD enabled.
#   - Unknown events and redundant selections are strict no-ops; behavior must
#     be deterministic with per-instance isolation.
#

class_name SceneStateMachineTests
extends "res://tests/utils/test_utils.gd"


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _load_scene_state_machine_script() -> GDScript:
	return load("res://scripts/system/scene_state_machine.gd") as GDScript


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


func _assert_config_keys_present(config: Dictionary, test_name: String) -> void:
	for key in CONFIG_KEYS:
		if not config.has(key):
			_fail(
				test_name,
				"config missing required key '" + key + "'; got keys " + str(config.keys())
			)
			return
	_pass(test_name)


func _apply_event(machine: Object, event_id: String) -> void:
	machine.apply_event(event_id)


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


# ---------------------------------------------------------------------------
# Structure and headless instantiability
# ---------------------------------------------------------------------------

func test_scene_state_machine_script_exists_and_is_pure_logic() -> void:
	var script: GDScript = _load_scene_state_machine_script()
	if script == null:
		_fail(
			"ssm_script_exists",
			"res://scripts/system/scene_state_machine.gd not found; implement SceneStateMachine per ticket"
		)
		return

	var instance: Object = script.new()
	if instance == null:
		_fail(
			"ssm_instantiates",
			"SceneStateMachine script did not instantiate; expected pure-logic Object/RefCounted"
		)
		return

	# Spec requires a pure-logic object, not a Node/scene.
	_assert_false(
		instance is Node,
		"ssm_not_node — SceneStateMachine must not extend Node"
	)


func test_initial_state_is_baseline_with_expected_config() -> void:
	var machine: Object = _make_machine()
	if machine == null:
		_fail(
			"ssm_initial_state_baseline",
			"SceneStateMachine script missing; cannot verify initial state"
		)
		return

	if not _has_required_api(machine):
		_fail(
			"ssm_initial_state_api_missing",
			"SceneStateMachine must implement get_state_id(), get_config(), apply_event(event_id: String)"
		)
		return

	var state: String = _state_of(machine)
	var config: Dictionary = _config_of(machine)

	_assert_state_allowed(
		state,
		"ssm_initial_state_allowed — initial state is within canonical set"
	)
	_assert_eq_string(
		"BASELINE",
		state,
		"ssm_initial_state_baseline_id — fresh SceneStateMachine starts in BASELINE state"
	)
	_assert_config_keys_present(
		config,
		"ssm_initial_config_keys_present — initial config dictionary exposes all required keys"
	)
	if not _configs_equal(config, _baseline_config()):
		_fail(
			"ssm_initial_config_matches_baseline",
			"initial config does not match expected BASELINE flags " + str(_baseline_config()) + ", got " + str(config)
		)
	else:
		_pass("ssm_initial_config_matches_baseline — initial config matches expected BASELINE flags")


# ---------------------------------------------------------------------------
# Core transitions: explicit selection events
# ---------------------------------------------------------------------------

func test_select_infection_demo_transitions_to_infection_demo_with_expected_flags() -> void:
	var machine: Object = _make_machine()
	if machine == null:
		_fail(
			"ssm_select_infection_demo",
			"SceneStateMachine script missing; cannot verify select_infection_demo"
		)
		return

	if not _has_required_api(machine):
		_fail(
			"ssm_select_infection_demo_api_missing",
			"SceneStateMachine must implement get_state_id(), get_config(), apply_event(event_id: String)"
		)
		return

	_apply_event(machine, "select_infection_demo")
	var state: String = _state_of(machine)
	var config: Dictionary = _config_of(machine)

	_assert_eq_string(
		"INFECTION_DEMO",
		state,
		"ssm_transition_infection_demo_state — select_infection_demo transitions to INFECTION_DEMO"
	)
	_assert_config_keys_present(
		config,
		"ssm_transition_infection_demo_config_keys — INFECTION_DEMO config exposes all required keys"
	)
	if not _configs_equal(config, _infection_demo_config()):
		_fail(
			"ssm_transition_infection_demo_flags",
			"INFECTION_DEMO config does not match expected flags " + str(_infection_demo_config()) + ", got " + str(config)
		)
	else:
		_pass("ssm_transition_infection_demo_flags — INFECTION_DEMO flags match expected configuration")


func test_select_enemy_playtest_transitions_to_enemy_playtest_with_expected_flags() -> void:
	var machine: Object = _make_machine()
	if machine == null:
		_fail(
			"ssm_select_enemy_playtest",
			"SceneStateMachine script missing; cannot verify select_enemy_playtest"
		)
		return

	if not _has_required_api(machine):
		_fail(
			"ssm_select_enemy_playtest_api_missing",
			"SceneStateMachine must implement get_state_id(), get_config(), apply_event(event_id: String)"
		)
		return

	_apply_event(machine, "select_enemy_playtest")
	var state: String = _state_of(machine)
	var config: Dictionary = _config_of(machine)

	_assert_eq_string(
		"ENEMY_PLAYTEST",
		state,
		"ssm_transition_enemy_playtest_state — select_enemy_playtest transitions to ENEMY_PLAYTEST"
	)
	_assert_config_keys_present(
		config,
		"ssm_transition_enemy_playtest_config_keys — ENEMY_PLAYTEST config exposes all required keys"
	)
	if not _configs_equal(config, _enemy_playtest_config()):
		_fail(
			"ssm_transition_enemy_playtest_flags",
			"ENEMY_PLAYTEST config does not match expected flags " + str(_enemy_playtest_config()) + ", got " + str(config)
		)
	else:
		_pass("ssm_transition_enemy_playtest_flags — ENEMY_PLAYTEST flags match expected configuration")


func test_select_baseline_from_non_baseline_returns_to_baseline_with_expected_flags() -> void:
	var machine: Object = _make_machine()
	if machine == null:
		_fail(
			"ssm_select_baseline_from_non_baseline",
			"SceneStateMachine script missing; cannot verify select_baseline"
		)
		return

	if not _has_required_api(machine):
		_fail(
			"ssm_select_baseline_from_non_baseline_api_missing",
			"SceneStateMachine must implement get_state_id(), get_config(), apply_event(event_id: String)"
		)
		return

	_apply_event(machine, "select_infection_demo")
	_apply_event(machine, "select_baseline")

	var state: String = _state_of(machine)
	var config: Dictionary = _config_of(machine)

	_assert_eq_string(
		"BASELINE",
		state,
		"ssm_transition_baseline_state — select_baseline transitions back to BASELINE"
	)
	if not _configs_equal(config, _baseline_config()):
		_fail(
			"ssm_transition_baseline_flags",
			"BASELINE config after transition does not match expected flags " + str(_baseline_config()) + ", got " + str(config)
		)
	else:
		_pass("ssm_transition_baseline_flags — BASELINE flags match expected configuration after transition")


# ---------------------------------------------------------------------------
# No invalid or stuck states: unknown and redundant events are no-ops
# ---------------------------------------------------------------------------

func test_unknown_event_is_strict_noop_for_state_and_config() -> void:
	var machine: Object = _make_machine()
	if machine == null:
		_fail(
			"ssm_unknown_event_noop",
			"SceneStateMachine script missing; cannot verify unknown event behavior"
		)
		return

	if not _has_required_api(machine):
		_fail(
			"ssm_unknown_event_noop_api_missing",
			"SceneStateMachine must implement get_state_id(), get_config(), apply_event(event_id: String)"
		)
		return

	var state_before: String = _state_of(machine)
	var config_before: Dictionary = _config_of(machine)

	_apply_event(machine, "unknown_event_id")

	var state_after: String = _state_of(machine)
	var config_after: Dictionary = _config_of(machine)

	_assert_eq_string(
		state_before,
		state_after,
		"ssm_unknown_event_state_noop — unknown event leaves state unchanged"
	)
	if not _configs_equal(config_before, config_after):
		_fail(
			"ssm_unknown_event_config_noop",
			"unknown event must not change configuration; before=" + str(config_before) + ", after=" + str(config_after)
		)
	else:
		_pass("ssm_unknown_event_config_noop — unknown event leaves configuration unchanged")


func test_redundant_selection_events_are_noops_for_state_and_config() -> void:
	var machine: Object = _make_machine()
	if machine == null:
		_fail(
			"ssm_redundant_selection_noop",
			"SceneStateMachine script missing; cannot verify redundant selection behavior"
		)
		return

	if not _has_required_api(machine):
		_fail(
			"ssm_redundant_selection_noop_api_missing",
			"SceneStateMachine must implement get_state_id(), get_config(), apply_event(event_id: String)"
		)
		return

	# Baseline redundant selection.
	var baseline_state_before: String = _state_of(machine)
	var baseline_config_before: Dictionary = _config_of(machine)
	_apply_event(machine, "select_baseline")
	var baseline_state_after: String = _state_of(machine)
	var baseline_config_after: Dictionary = _config_of(machine)

	_assert_eq_string(
		baseline_state_before,
		baseline_state_after,
		"ssm_redundant_baseline_state_noop — select_baseline when already BASELINE leaves state unchanged"
	)
	if not _configs_equal(baseline_config_before, baseline_config_after):
		_fail(
			"ssm_redundant_baseline_config_noop",
			"select_baseline when already BASELINE must not change configuration"
		)
	else:
		_pass("ssm_redundant_baseline_config_noop — select_baseline when BASELINE leaves configuration unchanged")

	# Infection demo redundant selection.
	_apply_event(machine, "select_infection_demo")
	var inf_state_before: String = _state_of(machine)
	var inf_config_before: Dictionary = _config_of(machine)
	_apply_event(machine, "select_infection_demo")
	var inf_state_after: String = _state_of(machine)
	var inf_config_after: Dictionary = _config_of(machine)

	_assert_eq_string(
		inf_state_before,
		inf_state_after,
		"ssm_redundant_infection_demo_state_noop — select_infection_demo when already INFECTION_DEMO leaves state unchanged"
	)
	if not _configs_equal(inf_config_before, inf_config_after):
		_fail(
			"ssm_redundant_infection_demo_config_noop",
			"select_infection_demo when already INFECTION_DEMO must not change configuration"
		)
	else:
		_pass("ssm_redundant_infection_demo_config_noop — redundant select_infection_demo leaves configuration unchanged")


# ---------------------------------------------------------------------------
# Determinism and per-instance isolation
# ---------------------------------------------------------------------------

func _run_event_sequence(events: Array[String]) -> Array:
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


func test_determinism_for_fixed_selection_sequence() -> void:
	var events: Array[String] = [
		"select_infection_demo",
		"select_enemy_playtest",
		"select_baseline",
		"select_enemy_playtest",
		"select_infection_demo",
	]

	var first: Array = _run_event_sequence(events)
	var second: Array = _run_event_sequence(events)

	if first.size() == 0 or second.size() == 0:
		_fail(
			"ssm_determinism_fixed_sequence",
			"SceneStateMachine script or API missing; cannot verify determinism"
		)
		return

	var deterministic: bool = first.size() == second.size()
	if deterministic:
		for i in first.size():
			var a = first[i]
			var b = second[i]
			if a["state"] != b["state"]:
				deterministic = false
				break
			if not _configs_equal(a["config"], b["config"]):
				deterministic = false
				break

	_assert_true(
		deterministic,
		"ssm_determinism_fixed_sequence — identical event sequences produce identical state/config traces"
	)


func test_two_instances_are_isolated_for_state_and_config() -> void:
	var a: Object = _make_machine()
	var b: Object = _make_machine()
	if a == null or b == null:
		_fail(
			"ssm_instance_isolation",
			"SceneStateMachine script missing; cannot verify instance isolation"
		)
		return

	if not _has_required_api(a) or not _has_required_api(b):
		_fail(
			"ssm_instance_isolation_api_missing",
			"SceneStateMachine must implement get_state_id(), get_config(), apply_event(event_id: String)"
		)
		return

	# Drive A through several transitions while B remains at defaults.
	var b_state_initial: String = _state_of(b)
	var b_config_initial: Dictionary = _config_of(b)

	_apply_event(a, "select_infection_demo")
	_apply_event(a, "select_enemy_playtest")

	var a_state: String = _state_of(a)
	var a_config: Dictionary = _config_of(a)
	var b_state_after: String = _state_of(b)
	var b_config_after: Dictionary = _config_of(b)

	_assert_eq_string(
		"ENEMY_PLAYTEST",
		a_state,
		"ssm_instance_isolation_a_state — A reaches ENEMY_PLAYTEST after events"
	)
	if not _configs_equal(a_config, _enemy_playtest_config()):
		_fail(
			"ssm_instance_isolation_a_config",
			"A config does not match expected ENEMY_PLAYTEST flags " + str(_enemy_playtest_config()) + ", got " + str(a_config)
		)
	else:
		_pass("ssm_instance_isolation_a_config — A config matches ENEMY_PLAYTEST flags")

	_assert_eq_string(
		b_state_initial,
		b_state_after,
		"ssm_instance_isolation_b_state_unchanged — B state unchanged while A transitions"
	)
	if not _configs_equal(b_config_initial, b_config_after):
		_fail(
			"ssm_instance_isolation_b_config_unchanged",
			"B configuration changed despite no events being applied"
		)
	else:
		_pass("ssm_instance_isolation_b_config_unchanged — B configuration unchanged when only A receives events")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_scene_state_machine.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Structure and instantiation
	test_scene_state_machine_script_exists_and_is_pure_logic()
	test_initial_state_is_baseline_with_expected_config()

	# Core selection transitions
	test_select_infection_demo_transitions_to_infection_demo_with_expected_flags()
	test_select_enemy_playtest_transitions_to_enemy_playtest_with_expected_flags()
	test_select_baseline_from_non_baseline_returns_to_baseline_with_expected_flags()

	# No invalid or stuck states
	test_unknown_event_is_strict_noop_for_state_and_config()
	test_redundant_selection_events_are_noops_for_state_and_config()

	# Determinism and per-instance isolation
	test_determinism_for_fixed_selection_sequence()
	test_two_instances_are_isolated_for_state_and_config()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

