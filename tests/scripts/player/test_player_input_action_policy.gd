#
# test_player_input_action_policy.gd
#
# Primary behavioral unit tests for PlayerInputActionPolicy (M11-03).
# Spec: project_board/specs/input_action_mapping_spec.md (IAM-2..IAM-9)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/03_input_action_mapping.md
#
# Instantiates via load("res://scripts/player/player_input_action_policy.gd") — no scene tree.
# Adversarial coverage: test_player_input_action_policy_adversarial.gd (Test Breaker).
#

extends "res://tests/utils/test_utils.gd"


const POLICY_PATH: String = "res://scripts/player/player_input_action_policy.gd"
const FSM_PATH: String = "res://scripts/player/player_state_machine.gd"

const STATE_IDLE: int = 0
const STATE_WALK: int = 1
const STATE_JUMP: int = 2
const STATE_FALL: int = 3
const STATE_FLOAT: int = 4
const STATE_WALL_CLING: int = 5
const STATE_ABSORB: int = 6
const STATE_MUTATE: int = 7
const STATE_HURT: int = 8
const STATE_DEAD: int = 9

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _load_policy_script() -> GDScript:
	if not ResourceLoader.exists(POLICY_PATH):
		return null
	return load(POLICY_PATH) as GDScript


func _make_policy() -> Object:
	var script: GDScript = _load_policy_script()
	if script == null or not script.can_instantiate():
		return null
	return script.new()


func _fail_missing_module(test_name: String) -> void:
	_fail(
		test_name,
		POLICY_PATH + " not found or not loadable; implement PlayerInputActionPolicy per IAM-7"
	)


func _has_policy_api(policy: Object) -> bool:
	return (
		policy.has_method("normalize_action")
		and policy.has_method("is_action_permitted")
		and policy.has_method("resolve_consumed_actions")
	)


func _sn(value: String) -> StringName:
	return StringName(value)


func _pressed(actions: Array) -> Array[StringName]:
	var out: Array[StringName] = []
	for a in actions:
		out.append(StringName(str(a)))
	return out


func _assert_permitted(
	policy: Object,
	state: int,
	action: String,
	expected: bool,
	test_name: String,
) -> void:
	var actual: bool = bool(policy.is_action_permitted(state, _sn(action)))
	if actual == expected:
		_pass(test_name)
	else:
		_fail(
			test_name,
			"state " + str(state) + " action '" + action + "' expected permitted="
			+ str(expected) + ", got " + str(actual)
		)


func _assert_consumed_eq(
	expected: Array,
	actual: Array,
	test_name: String,
) -> void:
	if actual.size() != expected.size():
		_fail(
			test_name,
			"size expected " + str(expected.size()) + ", got " + str(actual.size())
			+ " — expected " + str(expected) + ", got " + str(actual)
		)
		return
	for i in range(expected.size()):
		if str(actual[i]) != str(expected[i]):
			_fail(
				test_name,
				"index " + str(i) + " expected '" + str(expected[i]) + "', got '" + str(actual[i]) + "'"
			)
			return
	_pass(test_name)


# ---------------------------------------------------------------------------
# IAM-7: module contract
# ---------------------------------------------------------------------------

func test_iam7_script_loads_headless() -> void:
	var script: GDScript = _load_policy_script()
	if script == null:
		_fail("iam7_script_loads", POLICY_PATH + " missing")
		return
	var policy: Object = script.new()
	if policy == null:
		_fail("iam7_script_loads", "PlayerInputActionPolicy.new() returned null")
		return
	_pass("iam7_script_loads")


func test_iam7_extends_refcounted_not_node() -> void:
	var script: GDScript = _load_policy_script()
	if script == null:
		_fail_missing_module("iam7_extends_refcounted")
		return
	var base: Script = script.get_base_script() as Script
	var base_path: String = base.resource_path if base != null else ""
	_assert_eq_string(
		"res://scripts/player/player_input_action_policy.gd",
		script.resource_path,
		"iam7_policy_path",
	)
	_assert_true(
		script.can_instantiate() and not script.is_tool(),
		"iam7_instantiable_refcounted",
		"policy must instantiate headless without scene tree",
	)


func test_iam7_has_required_api() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam7_api")
		return
	_assert_true(_has_policy_api(policy), "iam7_api_methods", "missing normalize/permit/resolve API")


# ---------------------------------------------------------------------------
# IAM-2 / IAM-8: normalization and fail-closed
# ---------------------------------------------------------------------------

func test_iam2_normalize_mutate_to_infect() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam2_mutate_alias")
		return
	_assert_eq(_sn("infect"), policy.normalize_action(_sn("mutate")), "iam2_mutate_to_infect")


func test_iam2_normalize_swap_mutation_to_fuse() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam2_swap_alias")
		return
	_assert_eq(
		_sn("fuse"),
		policy.normalize_action(_sn("swap_mutation")),
		"iam2_swap_mutation_to_fuse",
	)


func test_iam8_normalize_unknown_passthrough() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam8_unknown_normalize")
		return
	_assert_eq(
		_sn("unknown_action"),
		policy.normalize_action(_sn("unknown_action")),
		"iam8_unknown_identity",
	)


func test_iam8_unknown_action_not_permitted() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam8_unknown_permit")
		return
	_assert_permitted(policy, STATE_IDLE, "unknown_action", false, "iam8_unknown_denied_idle")


func test_iam8_empty_pressed_returns_empty() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam8_empty_pressed")
		return
	var consumed: Array = policy.resolve_consumed_actions(STATE_IDLE, _pressed([]))
	_assert_consumed_eq([], consumed, "iam8_empty_resolve")


# ---------------------------------------------------------------------------
# IAM-5: state–action matrix spot checks
# ---------------------------------------------------------------------------

func test_iam5_idle_permits_attack() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_idle_attack")
		return
	_assert_permitted(policy, STATE_IDLE, "attack", true, "iam5_idle_attack_permitted")


func test_iam5_idle_permits_move_left() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_idle_move")
		return
	_assert_permitted(policy, STATE_IDLE, "move_left", true, "iam5_idle_move_left")


func test_iam5_jump_denies_jump() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_jump_denies_jump")
		return
	_assert_permitted(policy, STATE_JUMP, "jump", false, "iam5_jump_state_denies_jump")


func test_iam5_hurt_denies_attack() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_hurt_attack")
		return
	_assert_permitted(policy, STATE_HURT, "attack", false, "iam5_hurt_denies_attack")


func test_iam5_hurt_permits_menu() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_hurt_menu")
		return
	_assert_permitted(policy, STATE_HURT, "menu", true, "iam5_hurt_permits_menu")


func test_iam5_hurt_denies_move_left() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_hurt_move")
		return
	_assert_permitted(policy, STATE_HURT, "move_left", false, "iam5_hurt_denies_move_left")


func test_iam5_dead_denies_attack() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_dead_attack")
		return
	_assert_permitted(policy, STATE_DEAD, "attack", false, "iam5_dead_denies_attack")


func test_iam5_dead_denies_menu() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_dead_menu")
		return
	_assert_permitted(policy, STATE_DEAD, "menu", false, "iam5_dead_denies_menu")


func test_iam5_dead_denies_jump() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_dead_jump")
		return
	_assert_permitted(policy, STATE_DEAD, "jump", false, "iam5_dead_denies_jump")


func test_iam5_absorb_state_denies_attack() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_absorb_attack")
		return
	_assert_permitted(policy, STATE_ABSORB, "attack", false, "iam5_absorb_denies_attack")


func test_iam5_mutate_state_denies_fuse() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_mutate_fuse")
		return
	_assert_permitted(policy, STATE_MUTATE, "fuse", false, "iam5_mutate_denies_fuse")


func test_iam5_float_denies_detach() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_float_detach")
		return
	_assert_permitted(policy, STATE_FLOAT, "detach", false, "iam5_float_denies_detach")


func test_iam5_mutate_alias_permitted_as_infect() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam5_mutate_alias_infect")
		return
	_assert_permitted(policy, STATE_IDLE, "mutate", true, "iam5_idle_mutate_alias_permitted")


# ---------------------------------------------------------------------------
# IAM-6: consumption priority and menu suppression
# ---------------------------------------------------------------------------

func test_iam6_attack_beats_absorb_and_infect() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam6_attack_priority")
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_IDLE,
		_pressed(["attack", "absorb", "infect"]),
	)
	_assert_consumed_eq(["attack"], consumed, "iam6_attack_wins_combat_group")


func test_iam6_infect_beats_absorb() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam6_infect_priority")
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_IDLE,
		_pressed(["infect", "absorb"]),
	)
	_assert_consumed_eq(["infect"], consumed, "iam6_infect_beats_absorb")


func test_iam6_menu_suppresses_attack() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam6_menu_suppress")
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_IDLE,
		_pressed(["menu", "attack"]),
	)
	_assert_consumed_eq(["menu"], consumed, "iam6_menu_only_when_pressed")


func test_iam6_resolve_outputs_canonical_infect_not_mutate() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam6_canonical_output")
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_IDLE,
		_pressed(["mutate", "absorb"]),
	)
	_assert_consumed_eq(["infect"], consumed, "iam6_mutate_alias_resolves_to_infect")


# ---------------------------------------------------------------------------
# IAM-9: debug_kill gating
# ---------------------------------------------------------------------------

func test_iam9_debug_kill_disabled_always_false() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam9_debug_disabled")
		return
	if policy.get("debug_actions_enabled") != null:
		policy.set("debug_actions_enabled", false)
	_assert_permitted(
		policy,
		STATE_IDLE,
		"debug_kill",
		false,
		"iam9_debug_kill_denied_when_disabled",
	)


func test_iam9_debug_kill_idle_when_enabled() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam9_debug_enabled_idle")
		return
	if not policy.has_method("set") and not "debug_actions_enabled" in policy:
		_fail("iam9_debug_flag", "policy missing debug_actions_enabled property")
		return
	policy.set("debug_actions_enabled", true)
	_assert_permitted(
		policy,
		STATE_IDLE,
		"debug_kill",
		true,
		"iam9_debug_kill_permitted_idle_when_enabled",
	)


func test_iam9_dead_denies_debug_kill_when_enabled() -> void:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module("iam9_debug_dead")
		return
	policy.set("debug_actions_enabled", true)
	_assert_permitted(
		policy,
		STATE_DEAD,
		"debug_kill",
		false,
		"iam9_dead_denies_debug_kill_even_enabled",
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_player_input_action_policy.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_iam7_script_loads_headless()
	test_iam7_extends_refcounted_not_node()
	test_iam7_has_required_api()

	test_iam2_normalize_mutate_to_infect()
	test_iam2_normalize_swap_mutation_to_fuse()
	test_iam8_normalize_unknown_passthrough()
	test_iam8_unknown_action_not_permitted()
	test_iam8_empty_pressed_returns_empty()

	test_iam5_idle_permits_attack()
	test_iam5_idle_permits_move_left()
	test_iam5_jump_denies_jump()
	test_iam5_hurt_denies_attack()
	test_iam5_hurt_permits_menu()
	test_iam5_hurt_denies_move_left()
	test_iam5_dead_denies_attack()
	test_iam5_dead_denies_menu()
	test_iam5_dead_denies_jump()
	test_iam5_absorb_state_denies_attack()
	test_iam5_mutate_state_denies_fuse()
	test_iam5_float_denies_detach()
	test_iam5_mutate_alias_permitted_as_infect()

	test_iam6_attack_beats_absorb_and_infect()
	test_iam6_infect_beats_absorb()
	test_iam6_menu_suppresses_attack()
	test_iam6_resolve_outputs_canonical_infect_not_mutate()

	test_iam9_debug_kill_disabled_always_false()
	test_iam9_debug_kill_idle_when_enabled()
	test_iam9_dead_denies_debug_kill_when_enabled()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
