#
# test_enemy_animation_controller.gd
#
# Primary behavioral tests for EnemyAnimationController.
# Tests are fully headless — no real scene tree, no real AnimationPlayer.
# All stubs are defined inline as inner classes.
#
# EnemyAnimationController is loaded dynamically so this file parses even
# before the implementation file exists. When the implementation is absent,
# all tests fail with a clear diagnostic rather than a runner parse error.
#
# Spec:  project_board/7_milestone_7_enemy_animation_wiring/in_progress/
#        animation_controller_script.md
# Requirements: ACS-1 through ACS-9, ACS-NF1, ACS-NF2
#
# Test IDs: EAC-01 through EAC-22 (maps to T-ACS-01..T-ACS-22 from ACS-9)
# Plus EAC-NF1 covering ACS-NF1 AC-NF1.1.
#
# Checkpoint: project_board/checkpoints/M7-ACS/run-2026-04-01-testdesign.md
#

class_name EnemyAnimationControllerTests
extends "res://tests/utils/test_utils.gd"


const _CONTROLLER_PATH: String = "res://scripts/enemies/enemy_animation_controller.gd"


# ---------------------------------------------------------------------------
# Stub: AnimationPlayer (ACS-8 contract)
# ---------------------------------------------------------------------------

class StubAnimationPlayer:
	extends Object

	var current_animation: String = ""
	var speed_scale: float = 1.0
	var last_played_name: String = ""
	var last_played_blend: float = -999.0
	var play_call_count: int = 0
	var stop_call_count: int = 0
	var _is_playing: bool = false

	func play(anim_name: String, blend_time: float = -1.0) -> void:
		last_played_name = anim_name
		last_played_blend = blend_time
		current_animation = anim_name
		_is_playing = true
		play_call_count += 1

	func stop() -> void:
		_is_playing = false
		stop_call_count += 1

	func is_playing() -> bool:
		return _is_playing

	# Test helper: simulate natural one-shot clip completion.
	# Sets _is_playing = false without altering current_animation.
	func simulate_clip_end() -> void:
		_is_playing = false


# ---------------------------------------------------------------------------
# Stub: State machine (ACS-8 contract)
# ---------------------------------------------------------------------------

class StubStateMachine:
	extends Object

	var _state: String = "idle"

	func get_state() -> String:
		return _state


# ---------------------------------------------------------------------------
# Stub: Parent node (CharacterBody3D surrogate)
# Provides a `velocity` property so get_parent().velocity works.
# ---------------------------------------------------------------------------

class StubParent:
	extends Node

	var velocity: Vector3 = Vector3.ZERO


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

var _pass_count: int = 0
var _fail_count: int = 0

# Cached script reference — null if implementation file does not exist yet.
var _controller_script: GDScript = null
# Set to true after first load attempt so we do not retry on every test call.
var _load_attempted: bool = false


# ---------------------------------------------------------------------------
# Load controller script once.  Returns true if available.
# ---------------------------------------------------------------------------

func _load_script() -> bool:
	if _load_attempted:
		return _controller_script != null
	_load_attempted = true
	_controller_script = load(_CONTROLLER_PATH) as GDScript
	return _controller_script != null


# Create a new controller instance.  Returns null and records a failure if the
# implementation file does not exist.
func _new_controller(test_name: String) -> Object:
	if not _load_script():
		_fail(test_name, "implementation not found at " + _CONTROLLER_PATH)
		return null
	return _controller_script.new()


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

# Build a fully-wired controller for non-null tests.
# The controller is added as a child of stub_parent so get_parent() resolves.
# Returns [controller, anim_stub, sm_stub, parent] or null if script missing.
func _make_controller(test_name: String, state: String = "idle", vel: Vector3 = Vector3.ZERO) -> Array:
	var controller = _new_controller(test_name)
	if controller == null:
		return []

	var anim_stub := StubAnimationPlayer.new()
	var sm_stub := StubStateMachine.new()
	sm_stub._state = state

	var parent := StubParent.new()
	parent.velocity = vel

	parent.add_child(controller)
	controller.animation_player = anim_stub
	controller.state_machine = sm_stub
	controller._ready()

	return [controller, anim_stub, sm_stub, parent]


# Call _physics_process once with a standard delta.
func _tick(controller: Object) -> void:
	controller._physics_process(0.016)


# ---------------------------------------------------------------------------
# EAC-01: _ready() with null animation_player — warning, _ready_ok = false
# ACS-3 AC-3.1, AC-3.3
# ---------------------------------------------------------------------------

func test_eac_01_null_animation_player_sets_ready_ok_false() -> void:
	var controller = _new_controller("EAC-01")
	if controller == null:
		return

	var parent := StubParent.new()
	parent.add_child(controller)

	var sm_stub := StubStateMachine.new()
	controller.state_machine = sm_stub
	# animation_player intentionally left null

	controller._ready()

	_assert_false(
		controller._ready_ok,
		"EAC-01: _ready() with null animation_player sets _ready_ok = false"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-02: _ready() with null state_machine — warning, _ready_ok = false
# ACS-3 AC-3.2, AC-3.3
# ---------------------------------------------------------------------------

func test_eac_02_null_state_machine_sets_ready_ok_false() -> void:
	var controller = _new_controller("EAC-02")
	if controller == null:
		return

	var parent := StubParent.new()
	parent.add_child(controller)

	var anim_stub := StubAnimationPlayer.new()
	controller.animation_player = anim_stub
	# state_machine intentionally left null

	controller._ready()

	_assert_false(
		controller._ready_ok,
		"EAC-02: _ready() with null state_machine sets _ready_ok = false"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-03: _ready() with both valid — _ready_ok = true, no dormancy
# ACS-3 AC-3.4
# ---------------------------------------------------------------------------

func test_eac_03_both_valid_sets_ready_ok_true() -> void:
	var arr := _make_controller("EAC-03", "idle", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var parent: StubParent = arr[3]

	_assert_true(
		controller._ready_ok,
		"EAC-03: _ready() with both valid exports sets _ready_ok = true"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-04: State "idle", velocity zero → play("Idle", 0.15)
# ACS-4 AC-4.7
# ---------------------------------------------------------------------------

func test_eac_04_idle_state_zero_velocity_plays_idle() -> void:
	var arr := _make_controller("EAC-04", "idle", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)

	_assert_eq_string(
		"Idle",
		anim_stub.last_played_name,
		"EAC-04: state 'idle', zero velocity → play('Idle', ...)"
	)
	_assert_eq_float(
		0.15,
		anim_stub.last_played_blend,
		"EAC-04: state 'idle', zero velocity → blend_time 0.15"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-05: State "active", velocity zero → play("Idle", 0.15)
# ACS-4 AC-4.6
# ---------------------------------------------------------------------------

func test_eac_05_active_state_zero_velocity_plays_idle() -> void:
	var arr := _make_controller("EAC-05", "active", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)

	_assert_eq_string(
		"Idle",
		anim_stub.last_played_name,
		"EAC-05: state 'active', zero velocity → play('Idle', ...)"
	)
	_assert_eq_float(
		0.15,
		anim_stub.last_played_blend,
		"EAC-05: state 'active', zero velocity → blend_time 0.15"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-06: State "active", velocity >= 0.1 → play("Walk", 0.15)
# ACS-4 AC-4.4
# ---------------------------------------------------------------------------

func test_eac_06_active_state_moving_plays_walk() -> void:
	var arr := _make_controller("EAC-06", "active", Vector3(0.5, 0.0, 0.0))
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)

	_assert_eq_string(
		"Walk",
		anim_stub.last_played_name,
		"EAC-06: state 'active', velocity 0.5 → play('Walk', ...)"
	)
	_assert_eq_float(
		0.15,
		anim_stub.last_played_blend,
		"EAC-06: state 'active', moving → blend_time 0.15"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-07: State "idle", velocity >= 0.1 → play("Walk", 0.15)
# ACS-4 AC-4.5
# ---------------------------------------------------------------------------

func test_eac_07_idle_state_moving_plays_walk() -> void:
	var arr := _make_controller("EAC-07", "idle", Vector3(0.0, 0.0, 0.2))
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)

	_assert_eq_string(
		"Walk",
		anim_stub.last_played_name,
		"EAC-07: state 'idle', velocity 0.2 → play('Walk', ...)"
	)
	_assert_eq_float(
		0.15,
		anim_stub.last_played_blend,
		"EAC-07: state 'idle', moving → blend_time 0.15"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-08: State "weakened" → play("Idle", 0.15), speed_scale = 0.5
# ACS-4 AC-4.3
# ---------------------------------------------------------------------------

func test_eac_08_weakened_plays_idle_at_half_speed() -> void:
	var arr := _make_controller("EAC-08", "weakened", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)

	_assert_eq_string(
		"Idle",
		anim_stub.last_played_name,
		"EAC-08: state 'weakened' → play('Idle', ...)"
	)
	_assert_eq_float(
		0.15,
		anim_stub.last_played_blend,
		"EAC-08: state 'weakened' → blend_time 0.15"
	)
	_assert_eq_float(
		0.5,
		anim_stub.speed_scale,
		"EAC-08: state 'weakened' → speed_scale = 0.5"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-09: State "infected" → play("Idle", 0.15), speed_scale = 0.0
# ACS-4 AC-4.2
# ---------------------------------------------------------------------------

func test_eac_09_infected_plays_idle_at_zero_speed() -> void:
	var arr := _make_controller("EAC-09", "infected", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)

	_assert_eq_string(
		"Idle",
		anim_stub.last_played_name,
		"EAC-09: state 'infected' → play('Idle', ...)"
	)
	_assert_eq_float(
		0.15,
		anim_stub.last_played_blend,
		"EAC-09: state 'infected' → blend_time 0.15"
	)
	_assert_eq_float(
		0.0,
		anim_stub.speed_scale,
		"EAC-09: state 'infected' → speed_scale = 0.0"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-10: State "dead" → play("Death", 0.0), _death_latched = true
# ACS-7 AC-7.1, AC-7.2, AC-7.5
# ---------------------------------------------------------------------------

func test_eac_10_dead_plays_death_and_latches() -> void:
	var arr := _make_controller("EAC-10", "dead", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)

	_assert_eq_string(
		"Death",
		anim_stub.last_played_name,
		"EAC-10: state 'dead' → play('Death', ...)"
	)
	_assert_eq_float(
		0.0,
		anim_stub.last_played_blend,
		"EAC-10: state 'dead' → blend_time 0.0 (immediate)"
	)
	_assert_eq_float(
		1.0,
		anim_stub.speed_scale,
		"EAC-10: state 'dead' → speed_scale = 1.0"
	)
	_assert_true(
		controller._death_latched,
		"EAC-10: state 'dead' → _death_latched = true"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-11: State "dead" second tick → no additional play() (latch holds)
# ACS-7 AC-7.3
# ---------------------------------------------------------------------------

func test_eac_11_dead_second_tick_no_additional_play() -> void:
	var arr := _make_controller("EAC-11", "dead", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)
	var count_after_first: int = anim_stub.play_call_count

	_tick(controller)
	var count_after_second: int = anim_stub.play_call_count

	_assert_eq_int(
		count_after_first,
		count_after_second,
		"EAC-11: second tick while 'dead' does not call play() again (latch holds)"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-12: Same (clip, speed) consecutive ticks → play() not called on second tick
# ACS-5 AC-5.1
# ---------------------------------------------------------------------------

func test_eac_12_idempotent_no_play_on_second_tick() -> void:
	var arr := _make_controller("EAC-12", "idle", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)
	var count_after_first: int = anim_stub.play_call_count

	_tick(controller)
	var count_after_second: int = anim_stub.play_call_count

	_assert_eq_int(
		count_after_first,
		count_after_second,
		"EAC-12: same state/velocity on consecutive ticks → play() not called on second tick"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-13: trigger_hit_animation() → play("Hit", 0.0) called, _hit_active = true
# ACS-6 AC-6.1, AC-6.2, AC-6.3
# ---------------------------------------------------------------------------

func test_eac_13_trigger_hit_plays_hit_and_sets_flag() -> void:
	var arr := _make_controller("EAC-13", "active", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	# Prime the controller with one tick so internal state is established.
	_tick(controller)

	anim_stub.play_call_count = 0
	controller.trigger_hit_animation()

	_assert_eq_string(
		"Hit",
		anim_stub.last_played_name,
		"EAC-13: trigger_hit_animation() → play('Hit', ...)"
	)
	_assert_eq_float(
		0.0,
		anim_stub.last_played_blend,
		"EAC-13: trigger_hit_animation() → blend_time 0.0"
	)
	_assert_true(
		controller._hit_active,
		"EAC-13: trigger_hit_animation() → _hit_active = true"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-14: During _hit_active, state tick → no state play() call
# ACS-6 AC-6.4
# ---------------------------------------------------------------------------

func test_eac_14_during_hit_active_state_tick_suppressed() -> void:
	var arr := _make_controller("EAC-14", "active", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)
	controller.trigger_hit_animation()

	var count_at_hit_start: int = anim_stub.play_call_count

	# Tick while hit is still playing (is_playing stays true from trigger).
	_tick(controller)

	_assert_eq_int(
		count_at_hit_start,
		anim_stub.play_call_count,
		"EAC-14: while _hit_active, _physics_process tick does not call play() for state clip"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-15: simulate_clip_end() while _hit_active → play(resolved_clip, 0.15), _hit_active = false
# ACS-6 AC-6.5, AC-6.6
# ---------------------------------------------------------------------------

func test_eac_15_hit_completion_resumes_state_clip() -> void:
	var arr := _make_controller("EAC-15", "active", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)
	controller.trigger_hit_animation()

	# Simulate Hit clip finishing naturally.
	anim_stub.simulate_clip_end()
	anim_stub.play_call_count = 0

	# Tick to allow controller to detect completion and resume.
	_tick(controller)

	_assert_false(
		controller._hit_active,
		"EAC-15: after clip end tick, _hit_active = false"
	)
	_assert_eq_string(
		"Idle",
		anim_stub.last_played_name,
		"EAC-15: after Hit completion, controller resumes resolved clip (Idle for active+still)"
	)
	_assert_eq_float(
		0.15,
		anim_stub.last_played_blend,
		"EAC-15: after Hit completion, blend_time = 0.15"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-16: Hit ends while state is "dead" → play("Death", 0.0)
# ACS-6 AC-6.7
# ---------------------------------------------------------------------------

func test_eac_16_hit_completion_when_dead_plays_death() -> void:
	var arr := _make_controller("EAC-16", "active", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var sm_stub: StubStateMachine = arr[2]
	var parent: StubParent = arr[3]

	_tick(controller)
	controller.trigger_hit_animation()

	# Enemy dies while hit is playing.
	sm_stub._state = "dead"
	anim_stub.simulate_clip_end()
	anim_stub.play_call_count = 0

	_tick(controller)

	_assert_eq_string(
		"Death",
		anim_stub.last_played_name,
		"EAC-16: Hit completes while state is 'dead' → play('Death', ...)"
	)
	_assert_eq_float(
		0.0,
		anim_stub.last_played_blend,
		"EAC-16: Death triggered with blend_time 0.0"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-17: trigger_hit_animation() re-entrant → play("Hit", 0.0) again; _prior_clip unchanged
# ACS-6 AC-6.8
# ---------------------------------------------------------------------------

func test_eac_17_trigger_hit_reentrant_restarts_without_changing_prior_clip() -> void:
	var arr := _make_controller("EAC-17", "active", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)
	controller.trigger_hit_animation()

	var prior_clip_after_first: String = controller._prior_clip
	var prior_speed_after_first: float = controller._prior_speed

	anim_stub.play_call_count = 0
	# Call trigger_hit_animation a second time while still in hit.
	controller.trigger_hit_animation()

	_assert_eq_string(
		"Hit",
		anim_stub.last_played_name,
		"EAC-17: re-entrant trigger_hit_animation() plays 'Hit' again"
	)
	_assert_eq_float(
		0.0,
		anim_stub.last_played_blend,
		"EAC-17: re-entrant hit uses blend_time 0.0"
	)
	_assert_eq_int(
		1,
		anim_stub.play_call_count,
		"EAC-17: re-entrant trigger_hit_animation() calls play() exactly once"
	)
	_assert_eq_string(
		prior_clip_after_first,
		controller._prior_clip,
		"EAC-17: _prior_clip is unchanged on re-entrant trigger_hit_animation()"
	)
	_assert_eq_float(
		prior_speed_after_first,
		controller._prior_speed,
		"EAC-17: _prior_speed is unchanged on re-entrant trigger_hit_animation()"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-18: trigger_hit_animation() while _death_latched = true → no play() call
# ACS-7 AC-7.4
# ---------------------------------------------------------------------------

func test_eac_18_trigger_hit_while_death_latched_is_noop() -> void:
	var arr := _make_controller("EAC-18", "dead", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)
	# Death is now latched.
	_assert_true(
		controller._death_latched,
		"EAC-18: precondition — _death_latched = true after first dead tick"
	)

	anim_stub.play_call_count = 0
	controller.trigger_hit_animation()

	_assert_eq_int(
		0,
		anim_stub.play_call_count,
		"EAC-18: trigger_hit_animation() while _death_latched → no play() call"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-19: Custom move_threshold = 0.5, velocity 0.3 → play("Idle", ...)
# ACS-4 AC-4.9
# ---------------------------------------------------------------------------

func test_eac_19_custom_move_threshold_subthreshold_velocity_plays_idle() -> void:
	var controller = _new_controller("EAC-19")
	if controller == null:
		return

	var anim_stub := StubAnimationPlayer.new()
	var sm_stub := StubStateMachine.new()
	sm_stub._state = "active"

	var parent := StubParent.new()
	parent.velocity = Vector3(0.3, 0.0, 0.0)

	parent.add_child(controller)
	controller.animation_player = anim_stub
	controller.state_machine = sm_stub
	controller.move_threshold = 0.5
	controller._ready()

	_tick(controller)

	_assert_eq_string(
		"Idle",
		anim_stub.last_played_name,
		"EAC-19: move_threshold=0.5, velocity 0.3 → play('Idle', ...) (below threshold)"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-20: Custom blend_time = 0.0 → transition uses 0.0 blend
# ACS-5 AC-5.5
# ---------------------------------------------------------------------------

func test_eac_20_custom_blend_time_zero_passed_to_play() -> void:
	var controller = _new_controller("EAC-20")
	if controller == null:
		return

	var anim_stub := StubAnimationPlayer.new()
	var sm_stub := StubStateMachine.new()
	sm_stub._state = "idle"

	var parent := StubParent.new()
	parent.velocity = Vector3.ZERO

	parent.add_child(controller)
	controller.animation_player = anim_stub
	controller.state_machine = sm_stub
	controller.blend_time = 0.0
	controller._ready()

	_tick(controller)

	_assert_eq_float(
		0.0,
		anim_stub.last_played_blend,
		"EAC-20: blend_time=0.0 → play() called with 0.0 as second argument"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-21: Unknown state string "stunned" → play("Idle", 0.15), no crash
# ACS-4 AC-4.8
# ---------------------------------------------------------------------------

func test_eac_21_unknown_state_fallback_plays_idle() -> void:
	var arr := _make_controller("EAC-21", "stunned", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	_tick(controller)

	_assert_eq_string(
		"Idle",
		anim_stub.last_played_name,
		"EAC-21: unknown state 'stunned' → fallback to play('Idle', ...)"
	)
	_assert_eq_float(
		0.15,
		anim_stub.last_played_blend,
		"EAC-21: unknown state fallback uses blend_time 0.15"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-22: _ready_ok = false (null guard) → _physics_process calls no stub methods
# ACS-3 AC-3.3, ACS-NF2 AC-NF2.1
# ---------------------------------------------------------------------------

func test_eac_22_null_guard_physics_process_calls_nothing() -> void:
	var controller = _new_controller("EAC-22")
	if controller == null:
		return

	var parent := StubParent.new()
	parent.add_child(controller)

	var anim_stub := StubAnimationPlayer.new()
	# Do NOT assign state_machine so null guard fires.
	controller.animation_player = anim_stub
	controller._ready()

	_assert_false(
		controller._ready_ok,
		"EAC-22: precondition — _ready_ok = false with null state_machine"
	)

	var play_before: int = anim_stub.play_call_count
	var stop_before: int = anim_stub.stop_call_count
	_tick(controller)

	_assert_eq_int(
		play_before,
		anim_stub.play_call_count,
		"EAC-22: _physics_process with _ready_ok=false calls no play() on stub"
	)
	_assert_eq_int(
		stop_before,
		anim_stub.stop_call_count,
		"EAC-22: _physics_process with _ready_ok=false calls no stop() on stub"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-23: After death latch, live ESM flip to "active" — no further play() (DAP-2.1)
# ---------------------------------------------------------------------------

func test_eac_23_death_latch_blocks_play_after_state_flips_to_active() -> void:
	var arr := _make_controller("EAC-23", "dead", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var sm_stub: StubStateMachine = arr[2]
	var parent: StubParent = arr[3]

	_tick(controller)
	var plays_after_death: int = anim_stub.play_call_count

	sm_stub._state = "active"
	parent.velocity = Vector3(1.0, 0.0, 0.0)
	_tick(controller)

	_assert_eq_int(
		plays_after_death,
		anim_stub.play_call_count,
		"EAC-23 (DAP-2.1): after _death_latched, state flip to active does not call play()"
	)
	parent.free()


# ---------------------------------------------------------------------------
# EAC-NF1: 60-tick steady state — play() called exactly once (tick 1 only)
# ACS-NF1 AC-NF1.1
# ---------------------------------------------------------------------------

func test_eac_nf1_sixty_tick_steady_state_play_called_once() -> void:
	var arr := _make_controller("EAC-NF1", "idle", Vector3.ZERO)
	if arr.is_empty():
		return
	var controller = arr[0]
	var anim_stub: StubAnimationPlayer = arr[1]
	var parent: StubParent = arr[3]

	for _i in 60:
		_tick(controller)

	_assert_eq_int(
		1,
		anim_stub.play_call_count,
		"EAC-NF1: 60 ticks with no state/velocity change → play() called exactly once"
	)
	parent.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_animation_controller.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_eac_01_null_animation_player_sets_ready_ok_false()
	test_eac_02_null_state_machine_sets_ready_ok_false()
	test_eac_03_both_valid_sets_ready_ok_true()
	test_eac_04_idle_state_zero_velocity_plays_idle()
	test_eac_05_active_state_zero_velocity_plays_idle()
	test_eac_06_active_state_moving_plays_walk()
	test_eac_07_idle_state_moving_plays_walk()
	test_eac_08_weakened_plays_idle_at_half_speed()
	test_eac_09_infected_plays_idle_at_zero_speed()
	test_eac_10_dead_plays_death_and_latches()
	test_eac_11_dead_second_tick_no_additional_play()
	test_eac_12_idempotent_no_play_on_second_tick()
	test_eac_13_trigger_hit_plays_hit_and_sets_flag()
	test_eac_14_during_hit_active_state_tick_suppressed()
	test_eac_15_hit_completion_resumes_state_clip()
	test_eac_16_hit_completion_when_dead_plays_death()
	test_eac_17_trigger_hit_reentrant_restarts_without_changing_prior_clip()
	test_eac_18_trigger_hit_while_death_latched_is_noop()
	test_eac_19_custom_move_threshold_subthreshold_velocity_plays_idle()
	test_eac_20_custom_blend_time_zero_passed_to_play()
	test_eac_21_unknown_state_fallback_plays_idle()
	test_eac_22_null_guard_physics_process_calls_nothing()
	test_eac_23_death_latch_blocks_play_after_state_flips_to_active()
	test_eac_nf1_sixty_tick_steady_state_play_called_once()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
