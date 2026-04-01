# enemy_animation_controller.gd
#
# State-driven animation dispatcher for enemy nodes. Reads the current
# EnemyStateMachine state each physics frame and plays the matching clip
# on the enemy's AnimationPlayer with crossfade blending.
#
# Attaches as a direct child of the enemy CharacterBody3D root produced by
# generate_enemy_scenes.gd. Exports are wired in the generated .tscn.
#
# Ticket: animation_controller_script
# Spec:   project_board/7_milestone_7_enemy_animation_wiring/in_progress/
#         animation_controller_script.md
# Requirements: ACS-1 through ACS-9, ACS-NF1, ACS-NF2

class_name EnemyAnimationController
extends Node


@export var animation_player = null
@export var state_machine = null
@export var move_threshold: float = 0.1
@export var blend_time: float = 0.15


# Set to true in _ready() when both exports are valid. All per-frame
# logic is gated on this flag. Never reset after _ready() runs.
var _ready_ok: bool = false

# Tracks the last-applied (clip, speed, blend) tuple to avoid redundant
# play() calls on unchanged state (ACS-5 idempotency). blend_time is
# included so that runtime mutations to the export are reflected on the
# very next transition.
var _current_clip: String = ""
var _current_speed: float = 1.0
var _current_blend_time: float = -999.0  # Sentinel: forces first-tick play()

# Death latch — irreversible once set. Suppresses all further transitions
# and hit calls for the lifetime of this node.
var _death_latched: bool = false

# Hit one-shot state.
var _hit_active: bool = false
var _prior_clip: String = ""
var _prior_speed: float = 1.0


func _ready() -> void:
	if animation_player == null:
		push_warning(
			"EnemyAnimationController (%s): animation_player export is null" % name
		)
		_ready_ok = false

	if state_machine == null:
		push_warning(
			"EnemyAnimationController (%s): state_machine export is null" % name
		)
		_ready_ok = false

	if animation_player != null and state_machine != null:
		_ready_ok = true


func _physics_process(_delta: float) -> void:
	if not _ready_ok:
		return

	if _death_latched:
		return

	# Hit active window: while the hit clip is still playing, suppress all
	# other dispatches — including death. Only exit hit mode when the clip
	# ends (is_playing() false OR current_animation changed away from "Hit").
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

	# Resolve target (clip, speed) from current state and velocity.
	var resolved := _resolve_target()
	var clip: String = resolved[0]
	var speed: float = resolved[1]

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

	animation_player.speed_scale = speed
	animation_player.play(clip, blend_time)
	_current_clip = clip
	_current_speed = speed
	_current_blend_time = blend_time


# Returns [clip_name, speed] for the current state and velocity.
# Evaluated in priority order per ACS-4 resolution table.
func _resolve_target() -> Array:
	var state: String = state_machine.get_state()

	if state == "dead":
		return ["Death", 1.0]

	if state == "infected":
		return ["Idle", 0.0]

	if state == "weakened":
		return ["Idle", 0.5]

	if state == "idle" or state == "active":
		var vel_len: float = get_parent().velocity.length()
		if vel_len >= move_threshold:
			return ["Walk", 1.0]
		return ["Idle", 1.0]

	# Fallback for unknown/future state strings.
	return ["Idle", 1.0]


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
