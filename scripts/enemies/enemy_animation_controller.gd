# enemy_animation_controller.gd
#
# State-driven animation dispatcher for enemy nodes. Reads the current
# EnemyStateMachine state each physics frame and plays the matching clip
# on the enemy's AnimationPlayer with crossfade blending.
#
# Attaches as a direct child of the enemy CharacterBody3D root produced by
# generate_enemy_scenes.gd. The AnimationPlayer is resolved at _ready() via
# find_child() when not injected directly (e.g. in tests).
# EnemyStateMachine extends RefCounted so it cannot be an @export — wire it
# via setup() or assign state_machine directly before calling _ready().
#
# Ticket: animation_controller_script
# Spec:   project_board/7_milestone_7_enemy_animation_wiring/in_progress/
#         animation_controller_script.md
# Requirements: ACS-1 through ACS-9, ACS-NF1, ACS-NF2

class_name EnemyAnimationController
extends Node


# animation_player: resolved at _ready() via find_child() when null.
# Tests may inject directly: controller.animation_player = stub
var animation_player: Object = null

# state_machine: EnemyStateMachine extends RefCounted (not Node) so it
# cannot be an @export. Assign via setup() or directly before _ready().
var state_machine: Object = null

@export var move_threshold: float = 0.1
@export var blend_time: float = 0.15


# Set to true in _ready() when both dependencies are valid. All per-frame
# logic is gated on this flag. Never reset after _ready() runs.
var _ready_ok: bool = false

# Parent body reference — stored in _ready() for velocity access.
var _parent_body: Node = null

# Tracks the last-applied (clip, speed, blend) tuple to avoid redundant
# play() calls on unchanged state (ACS-5 idempotency). blend_time is
# included so runtime mutations to the export are reflected on the very
# next transition.
var _current_clip: String = ""
var _current_speed: float = 1.0
var _current_blend_time: float = -999.0  # Sentinel: forces first-tick play()

# Death latch — irreversible once set. Suppresses all further transitions
# and hit calls for the lifetime of this node.
var _death_latched: bool = false

# Hit one-shot state.
var _hit_active: bool = false
# _prior_clip / _prior_speed are set when trigger_hit_animation() is first
# called (not on re-entrant calls). Resume uses live state re-evaluation
# (AC-6.6), not these fields — they exist for test observability (EAC-17).
var _prior_clip: String = ""
var _prior_speed: float = 1.0


# Wire the state machine reference. Called by the generator after instantiation.
# In production, the real EnemyStateMachine will be passed here from M15
# navigation/AI wiring. For now the generator passes null (pre-M15).
func setup(esm: Object) -> void:
	state_machine = esm


func _ready() -> void:
	# Resolve AnimationPlayer: prefer injected value, fall back to find_child().
	if animation_player == null:
		animation_player = get_parent().find_child("AnimationPlayer", true, false)

	if animation_player == null:
		push_warning(
			"EnemyAnimationController (%s): animation_player export is null" % name
		)

	if state_machine == null:
		push_warning(
			"EnemyAnimationController (%s): state_machine export is null" % name
		)

	_parent_body = get_parent()
	if _parent_body == null:
		push_warning(
			"EnemyAnimationController (%s): get_parent() returned null" % name
		)

	if animation_player != null and state_machine != null and _parent_body != null:
		_ready_ok = true


func _physics_process(_delta: float) -> void:
	if not _ready_ok:
		return

	if _death_latched:
		return

	# Hit active window: while the hit clip is still playing, suppress all
	# other dispatches. Only exit hit mode when the clip ends
	# (is_playing() false OR current_animation changed away from "Hit").
	if _hit_active:
		var hit_finished: bool = (
			not animation_player.is_playing()
			or animation_player.current_animation != "Hit"
		)
		if not hit_finished:
			return
		# Hit clip finished — clear flag and invalidate cached clip so the
		# resume transition always fires even if the resolved clip matches
		# what was playing before the hit.
		_hit_active = false
		_current_clip = ""

	# Resolve target clip name and speed from current state and velocity.
	var state: String = state_machine.get_state()
	var vel_len: float = _parent_body.velocity.length()
	var clip: String = _resolve_clip_name(state, vel_len)
	# speed_scale uses == for float comparison intentionally: the controller
	# only ever writes exact float literals (0.0, 0.5, 1.0) to _current_speed,
	# matching the exact values returned by _resolve_speed(). This is safe for
	# the test suite which sets the same exact literals.
	var speed: float = _resolve_speed(state)

	# Death branch: one-shot, immediate, latches forever.
	if clip == "Death":
		animation_player.speed_scale = 1.0
		animation_player.play("Death", 0.0)
		_death_latched = true
		_current_clip = "Death"
		_current_speed = 1.0
		_current_blend_time = 0.0
		return

	# Idempotency: skip play() if clip, speed, and blend_time are all unchanged.
	if clip == _current_clip and speed == _current_speed and blend_time == _current_blend_time:
		return

	# speed_scale is the correct approach for persistent per-state playback
	# speed in Godot 4. AnimationPlayer.play()'s custom_speed parameter is not
	# reliable for persistent speed across frames — speed_scale persists.
	animation_player.speed_scale = speed
	animation_player.play(clip, blend_time)
	_current_clip = clip
	_current_speed = speed
	_current_blend_time = blend_time


# Returns the clip name for the current state and velocity.
# Evaluated in priority order per ACS-4 resolution table.
func _resolve_clip_name(state: String, vel_len: float) -> String:
	if state == "dead":
		return "Death"
	if state == "infected":
		return "Idle"
	if state == "weakened":
		return "Idle"
	if state == "idle" or state == "active":
		if vel_len >= move_threshold:
			return "Walk"
		return "Idle"
	# Fallback for unknown/future state strings.
	return "Idle"


# Returns the speed_scale value for the current state.
func _resolve_speed(state: String) -> float:
	if state == "dead":
		return 1.0
	if state == "infected":
		return 0.0
	if state == "weakened":
		return 0.5
	return 1.0


# Plays the "Hit" clip as a one-shot. Suppresses normal state dispatch
# until the clip finishes. Re-entrant calls restart from frame 0 without
# modifying the saved prior clip.
func trigger_hit_animation() -> void:
	if not _ready_ok:
		return

	if _death_latched:
		return

	if not _hit_active:
		# Save prior clip for bookkeeping (not used for resume — live
		# state re-evaluation is used instead per AC-6.6).
		_prior_clip = _current_clip
		_prior_speed = _current_speed
		_hit_active = true

	animation_player.play("Hit", 0.0)
