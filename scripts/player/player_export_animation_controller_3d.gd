# player_export_animation_controller_3d.gd
#
# Drives player_slime GLB clips (idle / move / jump) from CharacterBody3D motion.
# Expects parent CharacterBody3D and an imported model under SlimeVisual. Uses the
# AnimationPlayer that ships inside the GLB (same node paths as authored) — do not
# retarget clips onto a sibling AnimationPlayer; that breaks skeleton resolution.

class_name PlayerExportAnimationController3D
extends Node

const _WIRE_MAX_ATTEMPTS: int = 8

@export var move_speed_threshold: float = 0.12
@export var blend_time: float = 0.15

var _body: CharacterBody3D = null
var _anim: AnimationPlayer = null
var _ready_ok: bool = false
var _clip_by_base: Dictionary = {}  # String -> StringName
var _current: StringName = StringName()
var _wire_attempts: int = 0


func _ready() -> void:
	set_physics_process(true)
	call_deferred("_try_wire")


func _try_wire() -> void:
	if _ready_ok:
		return
	_wire_attempts += 1
	_body = get_parent() as CharacterBody3D
	if _body == null:
		return
	var slime: Node3D = _body.get_node_or_null("SlimeVisual") as Node3D
	if slime == null:
		return
	var embedded_list: Array[Node] = slime.find_children("*", "AnimationPlayer", true, false)
	if embedded_list.is_empty():
		if _wire_attempts < _WIRE_MAX_ATTEMPTS:
			call_deferred("_try_wire")
		else:
			push_warning(
				"PlayerExportAnimationController3D: no AnimationPlayer under SlimeVisual after "
				+ str(_WIRE_MAX_ATTEMPTS)
				+ " attempts — player GLB animations disabled"
			)
		return
	_anim = embedded_list[0] as AnimationPlayer
	_index_clips()
	if not _clip_by_base.has("idle"):
		push_warning(
			"PlayerExportAnimationController3D: GLB has no 'idle' clip — animations disabled"
		)
		return
	_force_loop_linear_for_bases(["idle", "move", "jump"])
	_ready_ok = true
	_current = StringName()
	_play_base("idle", true)


static func clip_base_for_state(
	is_on_floor: bool, horizontal_speed: float, threshold: float
) -> String:
	if is_on_floor:
		return "move" if absf(horizontal_speed) > threshold else "idle"
	return "jump"


func _physics_process(_delta: float) -> void:
	if not _ready_ok or _body == null or _anim == null:
		return
	var base: String = clip_base_for_state(
		_body.is_on_floor(), _body.velocity.x, move_speed_threshold
	)
	if not _clip_by_base.has(base):
		if base == "jump" and _clip_by_base.has("move"):
			base = "move"
		else:
			base = "idle"
	_play_base(base, false)


func _play_base(base: String, force: bool) -> void:
	var clip: StringName = _clip_by_base[base] as StringName
	if clip == StringName():
		return
	if not force and clip == _current:
		if _anim.is_playing():
			return
	_anim.speed_scale = 1.0
	_anim.play(clip, blend_time)
	_current = clip


func _index_clips() -> void:
	_clip_by_base.clear()
	if _anim == null:
		return
	for full: StringName in _anim.get_animation_list():
		var s: String = str(full)
		var base: String = s.get_file().to_lower()
		if not base.is_empty():
			_clip_by_base[base] = full


func _force_loop_linear_for_bases(bases: Array[String]) -> void:
	if _anim == null:
		return
	for full: StringName in _anim.get_animation_list():
		var base: String = str(full).get_file().to_lower()
		if not bases.has(base):
			continue
		var anim: Animation = _anim.get_animation(full)
		if anim != null:
			anim.loop_mode = Animation.LOOP_LINEAR
