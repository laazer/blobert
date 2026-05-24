#
# test_player_input_action_policy_adversarial.gd
#
# Adversarial extension for PlayerInputActionPolicy (M11-03).
# Spec edge cases EC-IAM-1..EC-IAM-18 (combat ties, matrix holes, menu suppression).
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/03_input_action_mapping.md
# Spec: project_board/specs/input_action_mapping_spec.md
#
# Extends primary suite helpers; no scene tree.
#

class_name PlayerInputActionPolicyAdversarialTests
extends "res://tests/scripts/player/test_player_input_action_policy.gd"


const _COMBAT_ACTIONS: Array[String] = ["attack", "infect", "absorb", "fuse"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _require_policy(test_name: String) -> Object:
	var policy: Object = _make_policy()
	if policy == null:
		_fail_missing_module(test_name)
		return null
	if not _has_policy_api(policy):
		_fail(test_name + "_api", "PlayerInputActionPolicy missing required API")
		return null
	return policy


func _permutations_three() -> Array:
	return [
		["attack", "absorb", "infect"],
		["absorb", "attack", "infect"],
		["infect", "absorb", "attack"],
		["attack", "infect", "absorb"],
		["infect", "attack", "absorb"],
		["absorb", "infect", "attack"],
	]


# ---------------------------------------------------------------------------
# EC-IAM-2 — combat priority order-independent (attack wins)
# ---------------------------------------------------------------------------

func test_ec_iam2_combat_winner_independent_of_press_order() -> void:
	var policy: Object = _require_policy("ec_iam2_order")
	if policy == null:
		return
	for batch in _permutations_three():
		var consumed: Array = policy.resolve_consumed_actions(STATE_IDLE, _pressed(batch))
		_assert_consumed_eq(
			["attack"],
			consumed,
			"ec_iam2_attack_wins_order_" + "_".join(batch),
		)


func test_ec_iam2_alias_mutate_loses_to_attack_same_frame() -> void:
	var policy: Object = _require_policy("ec_iam2_mutate_attack")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_IDLE,
		_pressed(["mutate", "attack"]),
	)
	_assert_consumed_eq(["attack"], consumed, "ec_iam2_mutate_alias_attack_wins")


# ---------------------------------------------------------------------------
# EC-IAM-3 / EC-IAM-4 — lower combat priority without attack
# ---------------------------------------------------------------------------

func test_ec_iam3_infect_beats_absorb_without_attack() -> void:
	var policy: Object = _require_policy("ec_iam3_infect_absorb")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_WALK,
		_pressed(["absorb", "infect"]),
	)
	_assert_consumed_eq(["infect"], consumed, "ec_iam3_infect_over_absorb")


func test_ec_iam4_absorb_beats_fuse_without_higher_combat() -> void:
	var policy: Object = _require_policy("ec_iam4_absorb_fuse")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_IDLE,
		_pressed(["fuse", "absorb", "swap_mutation"]),
	)
	_assert_consumed_eq(["absorb"], consumed, "ec_iam4_absorb_over_fuse_and_alias")


# ---------------------------------------------------------------------------
# EC-IAM-14 — detach slots independent (both consumed)
# ---------------------------------------------------------------------------

func test_ec_iam14_detach_both_slots_same_frame() -> void:
	var policy: Object = _require_policy("ec_iam14_detach_dual")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_IDLE,
		_pressed(["detach_2", "detach"]),
	)
	_assert_consumed_eq(["detach", "detach_2"], consumed, "ec_iam14_both_detach_slots")


func test_ec_iam14_detach_with_movement_and_jump_idle() -> void:
	var policy: Object = _require_policy("ec_iam14_detach_move")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_WALK,
		_pressed(["jump", "detach", "move_right", "move_left", "detach_2"]),
	)
	_assert_consumed_eq(
		["move_left", "move_right", "jump", "detach", "detach_2"],
		consumed,
		"ec_iam14_independent_group_stable_order",
	)


# ---------------------------------------------------------------------------
# EC-IAM — FALL / WALL_CLING deny absorb (matrix + resolve)
# ---------------------------------------------------------------------------

func test_ec_iam_fall_denies_absorb_permit() -> void:
	var policy: Object = _require_policy("ec_iam_fall_absorb_permit")
	if policy == null:
		return
	_assert_permitted(policy, STATE_FALL, "absorb", false, "ec_iam_fall_absorb_not_permitted")


func test_ec_iam_wall_cling_denies_absorb_permit() -> void:
	var policy: Object = _require_policy("ec_iam_wall_absorb_permit")
	if policy == null:
		return
	_assert_permitted(
		policy,
		STATE_WALL_CLING,
		"absorb",
		false,
		"ec_iam_wall_cling_absorb_not_permitted",
	)


func test_ec_iam_fall_resolve_drops_denied_absorb_keeps_attack() -> void:
	var policy: Object = _require_policy("ec_iam_fall_resolve")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_FALL,
		_pressed(["absorb", "attack"]),
	)
	_assert_consumed_eq(["attack"], consumed, "ec_iam_fall_attack_without_absorb")


func test_ec_iam_wall_cling_resolve_drops_absorb_keeps_fuse() -> void:
	var policy: Object = _require_policy("ec_iam_wall_resolve")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_WALL_CLING,
		_pressed(["fuse", "absorb"]),
	)
	_assert_consumed_eq(["fuse"], consumed, "ec_iam_wall_fuse_without_absorb")


# ---------------------------------------------------------------------------
# EC-IAM-5 — menu suppresses movement and combat
# ---------------------------------------------------------------------------

func test_ec_iam5_menu_suppresses_movement_and_combat() -> void:
	var policy: Object = _require_policy("ec_iam5_menu_move")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_IDLE,
		_pressed(["menu", "move_left", "move_right", "jump", "attack"]),
	)
	_assert_consumed_eq(["menu"], consumed, "ec_iam5_menu_only_when_movement_also_pressed")


func test_ec_iam5_hurt_menu_suppresses_attack() -> void:
	var policy: Object = _require_policy("ec_iam5_hurt_menu")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_HURT,
		_pressed(["menu", "attack", "move_left"]),
	)
	_assert_consumed_eq(["menu"], consumed, "ec_iam5_hurt_menu_suppresses_gameplay")


# ---------------------------------------------------------------------------
# EC-IAM-1 / EC-IAM-8 — unknown and fail-closed in resolve batches
# ---------------------------------------------------------------------------

func test_ec_iam1_unknown_not_permitted_any_state() -> void:
	var policy: Object = _require_policy("ec_iam1_unknown_permit")
	if policy == null:
		return
	for state in [
		STATE_IDLE,
		STATE_JUMP,
		STATE_ABSORB,
		STATE_HURT,
		STATE_DEAD,
	]:
		_assert_permitted(
			policy,
			state,
			"not_a_real_input_action",
			false,
			"ec_iam1_unknown_denied_state_" + str(state),
		)


func test_ec_iam1_unknown_stripped_from_resolve_valid_remains() -> void:
	var policy: Object = _require_policy("ec_iam1_unknown_resolve")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_IDLE,
		_pressed(["bogus_action", "move_left", "attack", "also_fake"]),
	)
	_assert_consumed_eq(
		["move_left", "attack"],
		consumed,
		"ec_iam1_unknown_ignored_valid_consumed",
	)


func test_ec_iam8_absorb_state_detach_denied_in_resolve() -> void:
	var policy: Object = _require_policy("ec_iam8_absorb_detach")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_ABSORB,
		_pressed(["detach", "menu", "attack"]),
	)
	_assert_consumed_eq(["menu"], consumed, "ec_iam8_absorb_only_menu_survives")


# ---------------------------------------------------------------------------
# EC-IAM-6 / EC-IAM-7 — HURT and DEAD deny-all gameplay resolution
# ---------------------------------------------------------------------------

func test_ec_iam7_hurt_denies_all_gameplay_permits() -> void:
	var policy: Object = _require_policy("ec_iam7_hurt_permits")
	if policy == null:
		return
	for action in [
		"move_left",
		"move_right",
		"jump",
		"attack",
		"absorb",
		"infect",
		"fuse",
		"detach",
		"detach_2",
	]:
		_assert_permitted(
			policy,
			STATE_HURT,
			action,
			false,
			"ec_iam7_hurt_denies_" + action,
		)


func test_ec_iam7_hurt_resolve_empty_without_menu() -> void:
	var policy: Object = _require_policy("ec_iam7_hurt_resolve")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_HURT,
		_pressed(["attack", "move_left", "jump", "absorb", "detach"]),
	)
	_assert_consumed_eq([], consumed, "ec_iam7_hurt_no_gameplay_consumed")


func test_ec_iam6_dead_resolve_empty_for_gameplay_batch() -> void:
	var policy: Object = _require_policy("ec_iam6_dead_resolve")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_DEAD,
		_pressed(["menu", "attack", "move_left", "jump", "debug_kill"]),
	)
	_assert_consumed_eq([], consumed, "ec_iam6_dead_empty_consumed")


func test_ec_iam6_dead_denies_menu_permit() -> void:
	var policy: Object = _require_policy("ec_iam6_dead_menu")
	if policy == null:
		return
	_assert_permitted(policy, STATE_DEAD, "menu", false, "ec_iam6_dead_menu_denied")


# ---------------------------------------------------------------------------
# EC-IAM-12 — debug_kill coexists with combat winner when enabled
# ---------------------------------------------------------------------------

func test_ec_iam12_debug_kill_with_attack_when_enabled() -> void:
	var policy: Object = _require_policy("ec_iam12_debug_combat")
	if policy == null:
		return
	policy.set("debug_actions_enabled", true)
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_IDLE,
		_pressed(["debug_kill", "attack", "absorb"]),
	)
	_assert_consumed_eq(
		["attack", "debug_kill"],
		consumed,
		"ec_iam12_debug_after_combat_winner",
	)


# ---------------------------------------------------------------------------
# EC-IAM-16 — MUTATE state locks meta actions in resolve
# ---------------------------------------------------------------------------

func test_ec_iam16_mutate_state_resolve_menu_only() -> void:
	var policy: Object = _require_policy("ec_iam16_mutate_resolve")
	if policy == null:
		return
	var consumed: Array = policy.resolve_consumed_actions(
		STATE_MUTATE,
		_pressed(["fuse", "infect", "menu", "move_left"]),
	)
	_assert_consumed_eq(["menu"], consumed, "ec_iam16_mutate_menu_only")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_player_input_action_policy_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_ec_iam2_combat_winner_independent_of_press_order()
	test_ec_iam2_alias_mutate_loses_to_attack_same_frame()
	test_ec_iam3_infect_beats_absorb_without_attack()
	test_ec_iam4_absorb_beats_fuse_without_higher_combat()
	test_ec_iam14_detach_both_slots_same_frame()
	test_ec_iam14_detach_with_movement_and_jump_idle()
	test_ec_iam_fall_denies_absorb_permit()
	test_ec_iam_wall_cling_denies_absorb_permit()
	test_ec_iam_fall_resolve_drops_denied_absorb_keeps_attack()
	test_ec_iam_wall_cling_resolve_drops_absorb_keeps_fuse()
	test_ec_iam5_menu_suppresses_movement_and_combat()
	test_ec_iam5_hurt_menu_suppresses_attack()
	test_ec_iam1_unknown_not_permitted_any_state()
	test_ec_iam1_unknown_stripped_from_resolve_valid_remains()
	test_ec_iam8_absorb_state_detach_denied_in_resolve()
	test_ec_iam7_hurt_denies_all_gameplay_permits()
	test_ec_iam7_hurt_resolve_empty_without_menu()
	test_ec_iam6_dead_resolve_empty_for_gameplay_batch()
	test_ec_iam6_dead_denies_menu_permit()
	test_ec_iam12_debug_kill_with_attack_when_enabled()
	test_ec_iam16_mutate_state_resolve_menu_only()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
