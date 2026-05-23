#
# test_player_state_machine.gd
#
# Primary behavioral unit tests for PlayerStateMachine (M11-01).
# Spec: project_board/specs/player_state_machine_spec.md (PSM-1..PSM-9)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/backlog/01_player_state_machine.md
#
# Instantiates via load("res://scripts/player/player_state_machine.gd") — no scene tree.
# Adversarial coverage: test_player_state_machine_adversarial.gd (Test Breaker).
#

class_name PlayerStateMachineTests
extends "res://tests/utils/test_utils.gd"


const FSM_PATH: String = "res://scripts/player/player_state_machine.gd"

# Frozen enum ints (PSM-2); tests compare get_state() without requiring global class_name.
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

const EXPECTED_STATE_COUNT: int = 10
const TIMER_EPS: float = 1e-4

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _load_fsm_script() -> GDScript:
	return load(FSM_PATH) as GDScript


func _load_ctx_script() -> GDScript:
	if not ResourceLoader.exists(FSM_PATH):
		return null
	var ctx_path: String = "res://scripts/player/player_state_derivation_context.gd"
	if ResourceLoader.exists(ctx_path):
		return load(ctx_path) as GDScript
	return load(FSM_PATH) as GDScript


func _make_machine() -> Object:
	var script: GDScript = _load_fsm_script()
	if script == null:
		return null
	return script.new()


func _make_ctx() -> Object:
	if ClassDB.class_exists("PlayerStateDerivationContext"):
		return ClassDB.instantiate("PlayerStateDerivationContext")
	var script: GDScript = _load_ctx_script()
	if script == null:
		return null
	if not script.can_instantiate():
		return null
	return script.new()


func _fail_missing_module(test_name: String) -> void:
	_fail(
		test_name,
		FSM_PATH + " not found or not loadable; implement PlayerStateMachine per PSM-1"
	)


func _has_fsm_api(machine: Object) -> bool:
	return (
		machine.has_method("get_state")
		and machine.has_method("get_state_timer")
		and machine.has_method("update")
		and machine.has_method("can_transition_to")
		and machine.has_method("transition")
		and machine.has_method("compute_derived_state")
		and machine.has_method("sync_from_context")
		and machine.has_method("notify_damage_taken")
		and machine.has_method("reset")
	)


func _state_of(machine: Object) -> int:
	return int(machine.get_state())


func _timer_of(machine: Object) -> float:
	return float(machine.get_state_timer())


func _set_jump_for_float_gate(machine: Object) -> void:
	machine.transition(STATE_JUMP)
	machine.update(0.04)


func _set_jump_timer(machine: Object, seconds: float) -> void:
	machine.transition(STATE_JUMP)
	if seconds > 0.0:
		machine.update(seconds)


func _ctx_floor_idle() -> Object:
	var ctx: Object = _make_ctx()
	if ctx == null:
		return null
	ctx.is_on_floor = true
	ctx.horizontal_speed = 0.0
	ctx.vertical_velocity = 0.0
	ctx.move_speed_threshold = 0.12
	ctx.is_wall_clinging = false
	ctx.is_any_chunk_stuck = false
	ctx.is_mutation_active = false
	ctx.current_hp = 100.0
	ctx.min_hp = 0.0
	ctx.hurt_pending = false
	return ctx


# ---------------------------------------------------------------------------
# PSM-1: Module identity
# ---------------------------------------------------------------------------

func test_psm1_script_loads_and_instantiates_headless() -> void:
	var script: GDScript = _load_fsm_script()
	if script == null:
		_fail_missing_module("psm1_script_exists")
		return
	var machine: Object = script.new()
	_assert_true(machine != null, "psm1_instantiation_non_null — PlayerStateMachine.new() succeeds headless")


func test_psm1_extends_refcounted_not_node() -> void:
	var machine: Object = _make_machine()
	if machine == null:
		_fail_missing_module("psm1_refcounted")
		return
	_assert_true(machine is RefCounted, "psm1_is_refcounted — extends RefCounted")
	_assert_false(machine is Node, "psm1_not_node — must not extend Node")


func test_psm1_class_name_registered() -> void:
	var script: GDScript = _load_fsm_script()
	if script == null:
		_fail_missing_module("psm1_class_name")
		return
	_assert_eq_string(
		"PlayerStateMachine",
		script.get_global_name(),
		"psm1_class_name — class_name PlayerStateMachine registered"
	)


# ---------------------------------------------------------------------------
# PSM-2: PlayerState enum
# ---------------------------------------------------------------------------

func test_psm2_initial_state_is_idle() -> void:
	var machine: Object = _make_machine()
	if machine == null:
		_fail_missing_module("psm2_initial_idle")
		return
	if not _has_fsm_api(machine):
		_fail("psm2_initial_idle_api", "PlayerStateMachine missing get_state() API")
		return
	_assert_eq_int(STATE_IDLE, _state_of(machine), "psm2_initial_idle — fresh machine is IDLE")


func test_psm2_enum_has_ten_members() -> void:
	var script: GDScript = _load_fsm_script()
	if script == null:
		_fail_missing_module("psm2_enum_count")
		return
	var enum_dict: Dictionary = script.get_script_constant_map()
	var member_names: PackedStringArray = PackedStringArray()
	for key in enum_dict.keys():
		var key_str: String = str(key)
		if key_str == "PlayerState" and enum_dict[key] is Dictionary:
			for member_key in (enum_dict[key] as Dictionary).keys():
				member_names.append(str(member_key))
			break
	if member_names.is_empty():
		for key in enum_dict.keys():
			var key_str: String = str(key)
			if key_str.begins_with("PlayerState."):
				member_names.append(key_str.get_slice(".", 1))
	if member_names.is_empty():
		_fail(
			"psm2_enum_count",
			"cannot enumerate PlayerState; implement nested enum with ten members (PSM-2)"
		)
		return
	_assert_eq_int(
		EXPECTED_STATE_COUNT,
		member_names.size(),
		"psm2_enum_count — PlayerState has exactly ten members"
	)


# ---------------------------------------------------------------------------
# PSM-3: state_timer contract
# ---------------------------------------------------------------------------

func test_psm3_initial_timer_zero() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm3_initial_timer")
		return
	_assert_approx(0.0, _timer_of(machine), "psm3_initial_timer_zero")


func test_psm3_update_accumulates_without_transition() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm3_update_accumulate")
		return
	machine.update(0.016)
	machine.update(0.016)
	_assert_approx(0.032, _timer_of(machine), "psm3_update_accumulate — two update(0.016) calls")


func test_psm3_transition_resets_timer() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm3_transition_reset_timer")
		return
	machine.update(0.1)
	var ok: bool = machine.transition(STATE_WALK)
	_assert_true(ok, "psm3_transition_walk_ok — transition(IDLE→WALK) succeeds")
	_assert_approx(0.0, _timer_of(machine), "psm3_transition_reset_timer — timer zero after state change")


func test_psm3_same_state_transition_does_not_reset_timer() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm3_same_state_no_reset")
		return
	machine.update(0.05)
	var ok: bool = machine.transition(STATE_IDLE)
	_assert_true(ok, "psm3_same_state_ok — transition(IDLE→IDLE) returns true")
	machine.update(0.01)
	_assert_approx(0.06, _timer_of(machine), "psm3_same_state_no_reset — timer keeps accumulating")


func test_psm3_update_zero_delta_is_noop() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm3_update_zero")
		return
	machine.update(0.05)
	machine.update(0.0)
	_assert_approx(0.05, _timer_of(machine), "psm3_update_zero — update(0.0) does not change timer")


# ---------------------------------------------------------------------------
# PSM-4: can_transition_to guards
# ---------------------------------------------------------------------------

func test_psm4_dead_cannot_leave_except_dead() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm4_dead_terminal_guard")
		return
	machine.transition(STATE_DEAD)
	_assert_false(
		machine.can_transition_to(STATE_IDLE),
		"psm4_dead_to_idle_denied — G-DEAD blocks IDLE from DEAD"
	)


func test_psm4_hurt_cannot_reenter_hurt() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm4_hurt_reentry")
		return
	machine.transition(STATE_HURT)
	_assert_false(
		machine.can_transition_to(STATE_HURT),
		"psm4_hurt_to_hurt_denied — G-HURT blocks HURT from HURT"
	)


func test_psm4_idle_cannot_float() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm4_idle_float")
		return
	_assert_false(
		machine.can_transition_to(STATE_FLOAT),
		"psm4_idle_float_denied — G-FLOAT blocks FLOAT from IDLE"
	)


func test_psm4_jump_can_float() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm4_jump_float")
		return
	machine.transition(STATE_JUMP)
	_assert_true(
		machine.can_transition_to(STATE_FLOAT),
		"psm4_jump_float_allowed — JUMP may transition to FLOAT (guard only)"
	)


func test_psm4_walk_can_dead() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm4_walk_dead")
		return
	machine.transition(STATE_WALK)
	_assert_true(
		machine.can_transition_to(STATE_DEAD),
		"psm4_walk_dead_allowed — death transition permitted from WALK"
	)


# ---------------------------------------------------------------------------
# PSM-5: transition application
# ---------------------------------------------------------------------------

func test_psm5_denied_transition_preserves_state_and_timer() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm5_denied_no_mutation")
		return
	machine.transition(STATE_WALK)
	machine.update(0.03)
	var before_state: int = _state_of(machine)
	var before_timer: float = _timer_of(machine)
	var ok: bool = machine.transition(STATE_FLOAT)
	_assert_false(ok, "psm5_float_from_walk_denied — transition(FLOAT) from WALK fails")
	_assert_eq_int(before_state, _state_of(machine), "psm5_denied_state_unchanged")
	_assert_approx(before_timer, _timer_of(machine), "psm5_denied_timer_unchanged")


func test_psm5_allowed_transition_updates_state_and_zeros_timer() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm5_allowed_transition")
		return
	machine.update(0.08)
	var ok: bool = machine.transition(STATE_WALK)
	_assert_true(ok, "psm5_walk_ok — transition to WALK succeeds")
	_assert_eq_int(STATE_WALK, _state_of(machine), "psm5_walk_state — get_state() is WALK")
	_assert_approx(0.0, _timer_of(machine), "psm5_walk_timer_reset — timer zero after transition")


# ---------------------------------------------------------------------------
# PSM-6: minimum action duration constants
# ---------------------------------------------------------------------------

func test_psm6_float_from_jump_blocked_before_min_duration() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm6_float_early")
		return
	_set_jump_for_float_gate(machine)
	var ok: bool = machine.transition(STATE_FLOAT)
	_assert_false(ok, "psm6_float_at_004 — transition(FLOAT) denied at timer 0.04 from JUMP")


func test_psm6_float_from_jump_allowed_at_min_duration() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm6_float_at_min")
		return
	_set_jump_timer(machine, 0.05)
	var ok: bool = machine.transition(STATE_FLOAT)
	_assert_true(ok, "psm6_float_at_005 — transition(FLOAT) allowed at timer 0.05 from JUMP")


func test_psm6_min_hurt_sec_is_zero() -> void:
	var script: GDScript = _load_fsm_script()
	if script == null:
		_fail_missing_module("psm6_min_hurt_const")
		return
	var constants: Dictionary = script.get_script_constant_map()
	if constants.has("MIN_HURT_SEC"):
		_assert_approx(
			0.0,
			float(constants["MIN_HURT_SEC"]),
			"psm6_min_hurt_sec — MIN_HURT_SEC == 0.0"
		)
		return
	_fail("psm6_min_hurt_const", "MIN_HURT_SEC constant not exposed on PlayerStateMachine")


# ---------------------------------------------------------------------------
# PSM-7: derivation
# ---------------------------------------------------------------------------

func test_psm7_derive_floor_idle() -> void:
	var machine: Object = _make_machine()
	var ctx: Object = _ctx_floor_idle()
	if machine == null or ctx == null or not _has_fsm_api(machine):
		_fail_missing_module("psm7_derive_idle")
		return
	var derived: int = int(machine.compute_derived_state(ctx))
	_assert_eq_int(STATE_IDLE, derived, "psm7_derive_idle — floor + low speed → IDLE")


func test_psm7_derive_floor_walk() -> void:
	var machine: Object = _make_machine()
	var ctx: Object = _ctx_floor_idle()
	if machine == null or ctx == null or not _has_fsm_api(machine):
		_fail_missing_module("psm7_derive_walk")
		return
	ctx.horizontal_speed = 0.2
	var derived: int = int(machine.compute_derived_state(ctx))
	_assert_eq_int(STATE_WALK, derived, "psm7_derive_walk — floor + speed 0.2 → WALK")


func test_psm7_derive_air_jump_and_fall() -> void:
	var machine: Object = _make_machine()
	var ctx: Object = _ctx_floor_idle()
	if machine == null or ctx == null or not _has_fsm_api(machine):
		_fail_missing_module("psm7_derive_air")
		return
	ctx.is_on_floor = false
	ctx.vertical_velocity = 0.5
	_assert_eq_int(
		STATE_JUMP,
		int(machine.compute_derived_state(ctx)),
		"psm7_derive_jump — air + vy>0.01 → JUMP"
	)
	ctx.vertical_velocity = -0.5
	_assert_eq_int(
		STATE_FALL,
		int(machine.compute_derived_state(ctx)),
		"psm7_derive_fall — air + vy<=0.01 → FALL"
	)


func test_psm7_derive_wall_cling() -> void:
	var machine: Object = _make_machine()
	var ctx: Object = _ctx_floor_idle()
	if machine == null or ctx == null or not _has_fsm_api(machine):
		_fail_missing_module("psm7_derive_wall_cling")
		return
	ctx.is_on_floor = false
	ctx.is_wall_clinging = true
	_assert_eq_int(
		STATE_WALL_CLING,
		int(machine.compute_derived_state(ctx)),
		"psm7_derive_wall_cling — cling flag → WALL_CLING"
	)


func test_psm7_derive_absorb_over_mutate() -> void:
	var machine: Object = _make_machine()
	var ctx: Object = _ctx_floor_idle()
	if machine == null or ctx == null or not _has_fsm_api(machine):
		_fail_missing_module("psm7_derive_absorb_priority")
		return
	ctx.is_any_chunk_stuck = true
	ctx.is_mutation_active = true
	_assert_eq_int(
		STATE_ABSORB,
		int(machine.compute_derived_state(ctx)),
		"psm7_derive_absorb_priority — chunk stuck wins over MUTATE"
	)


func test_psm7_derive_dead_on_zero_hp() -> void:
	var machine: Object = _make_machine()
	var ctx: Object = _ctx_floor_idle()
	if machine == null or ctx == null or not _has_fsm_api(machine):
		_fail_missing_module("psm7_derive_dead")
		return
	ctx.current_hp = 0.0
	ctx.min_hp = 0.0
	_assert_eq_int(
		STATE_DEAD,
		int(machine.compute_derived_state(ctx)),
		"psm7_derive_dead — hp<=min_hp → DEAD"
	)


func test_psm7_derive_never_float() -> void:
	var machine: Object = _make_machine()
	var ctx: Object = _ctx_floor_idle()
	if machine == null or ctx == null or not _has_fsm_api(machine):
		_fail_missing_module("psm7_derive_no_float")
		return
	ctx.is_on_floor = false
	ctx.vertical_velocity = 0.5
	var derived: int = int(machine.compute_derived_state(ctx))
	_assert_false(derived == STATE_FLOAT, "psm7_derive_no_float — derivation never returns FLOAT")


# ---------------------------------------------------------------------------
# PSM-8: damage notification / hurt latch
# ---------------------------------------------------------------------------

func test_psm8_notify_damage_yields_hurt_on_sync() -> void:
	var machine: Object = _make_machine()
	var ctx: Object = _ctx_floor_idle()
	if machine == null or ctx == null or not _has_fsm_api(machine):
		_fail_missing_module("psm8_hurt_on_sync")
		return
	machine.notify_damage_taken()
	machine.sync_from_context(ctx)
	_assert_eq_int(STATE_HURT, _state_of(machine), "psm8_hurt_on_sync — notify_damage then sync → HURT")


func test_psm8_double_notify_while_hurt_does_not_reenter() -> void:
	var machine: Object = _make_machine()
	var ctx: Object = _ctx_floor_idle()
	if machine == null or ctx == null or not _has_fsm_api(machine):
		_fail_missing_module("psm8_double_hurt")
		return
	machine.notify_damage_taken()
	machine.sync_from_context(ctx)
	machine.notify_damage_taken()
	var can_hurt: bool = machine.can_transition_to(STATE_HURT)
	_assert_false(can_hurt, "psm8_double_hurt_denied — second HURT blocked while already HURT")


# ---------------------------------------------------------------------------
# PSM-9: sync and reset
# ---------------------------------------------------------------------------

func test_psm9_reset_from_dead_to_idle() -> void:
	var machine: Object = _make_machine()
	if machine == null or not _has_fsm_api(machine):
		_fail_missing_module("psm9_reset_dead")
		return
	machine.transition(STATE_DEAD)
	machine.reset()
	_assert_eq_int(STATE_IDLE, _state_of(machine), "psm9_reset_dead_idle — reset() from DEAD → IDLE")
	_assert_approx(0.0, _timer_of(machine), "psm9_reset_timer_zero — reset() clears timer")


func test_psm9_sync_keeps_dead_without_reset() -> void:
	var machine: Object = _make_machine()
	var ctx: Object = _ctx_floor_idle()
	if machine == null or ctx == null or not _has_fsm_api(machine):
		_fail_missing_module("psm9_sync_dead_sticky")
		return
	machine.transition(STATE_DEAD)
	ctx.current_hp = 100.0
	machine.sync_from_context(ctx)
	_assert_eq_int(STATE_DEAD, _state_of(machine), "psm9_sync_dead_sticky — DEAD persists without reset()")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_player_state_machine.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_psm1_script_loads_and_instantiates_headless()
	test_psm1_extends_refcounted_not_node()
	test_psm1_class_name_registered()

	test_psm2_initial_state_is_idle()
	test_psm2_enum_has_ten_members()

	test_psm3_initial_timer_zero()
	test_psm3_update_accumulates_without_transition()
	test_psm3_transition_resets_timer()
	test_psm3_same_state_transition_does_not_reset_timer()
	test_psm3_update_zero_delta_is_noop()

	test_psm4_dead_cannot_leave_except_dead()
	test_psm4_hurt_cannot_reenter_hurt()
	test_psm4_idle_cannot_float()
	test_psm4_jump_can_float()
	test_psm4_walk_can_dead()

	test_psm5_denied_transition_preserves_state_and_timer()
	test_psm5_allowed_transition_updates_state_and_zeros_timer()

	test_psm6_float_from_jump_blocked_before_min_duration()
	test_psm6_float_from_jump_allowed_at_min_duration()
	test_psm6_min_hurt_sec_is_zero()

	test_psm7_derive_floor_idle()
	test_psm7_derive_floor_walk()
	test_psm7_derive_air_jump_and_fall()
	test_psm7_derive_wall_cling()
	test_psm7_derive_absorb_over_mutate()
	test_psm7_derive_dead_on_zero_hp()
	test_psm7_derive_never_float()

	test_psm8_notify_damage_yields_hurt_on_sync()
	test_psm8_double_notify_while_hurt_does_not_reenter()

	test_psm9_reset_from_dead_to_idle()
	test_psm9_sync_keeps_dead_without_reset()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
