# player_controller_3d.gd
#
# 3D engine-integration layer for blobert (2.5D).
# Uses the same MovementSimulation; maps Vector2 velocity to Vector3
# (X = horizontal, Y = vertical; 2D y+ down -> 3D y- so velocity.y = -sim.velocity.y).
# Movement constrained to plane Z=0; camera fixed for side view.

class_name PlayerController3D
extends BasePhysicsEntity3D

const MovementSimulation = preload("res://scripts/movement/movement_simulation.gd")
## 2D sim uses pixel-like units; 3D uses meters. 1 m = SCALE_2D_TO_3D "pixels".
const SCALE_2D_TO_3D: float = 100.0

var _simulation: MovementSimulation
var _current_state: MovementSimulation.MovementState

var _chunk_node: RigidBody3D = null
var _recall_in_progress: bool = false
var _recall_timer: float = 0.0
const _RECALL_TRAVEL_TIME: float = 0.25
const _CHUNK_SCENE: PackedScene = preload("res://scenes/chunk/chunk_3d.tscn")

var _mutation_slot: Object = null
var _base_max_speed: float = 0.0
const _MUTATION_SPEED_MULTIPLIER: float = 1.25

signal detach_fired(player_position: Vector3, chunk_position: Vector3)
signal recall_started(player_position: Vector3, chunk_position: Vector3)
signal chunk_reabsorbed(player_position: Vector3, chunk_position: Vector3)

@export var jump_height: float = 120.0
@export var coyote_time: float = 0.1
@export var jump_cut_velocity: float = -200.0
@export var cling_gravity_scale: float = 0.1
@export var max_cling_time: float = 1.5
@export var wall_jump_height: float = 100.0
@export var wall_jump_horizontal_speed: float = 180.0

## Detach lob: initial velocity (m/s) for the chunk when thrown. X = horizontal, Y = upward.
@export var detach_lob_horizontal: float = 5.0
@export var detach_lob_upward: float = 8.0
## Spawn offset (m) in lob direction so chunk clears the player.
const _DETACH_SPAWN_OFFSET: float = 0.4

## Game juice: jump stretch (kit jumpStretchSize). Scale applied to SlimeVisual.
@export var jump_stretch_scale: Vector3 = Vector3(0.85, 1.15, 0.85)
@export var juice_tween_duration: float = 0.1

func _ready() -> void:
	# CharacterBody3D does not apply gravity automatically; simulation drives velocity.

	_simulation = MovementSimulation.new()
	var project_gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity", 9.8) as float
	# Sim uses pixel-like units (gravity 980). Scale 3D 9.8 -> 980 for sim.
	_simulation.gravity = project_gravity * SCALE_2D_TO_3D

	_simulation.jump_height = jump_height
	_simulation.coyote_time = coyote_time
	_simulation.jump_cut_velocity = jump_cut_velocity
	_simulation.cling_gravity_scale = cling_gravity_scale
	_simulation.max_cling_time = max_cling_time
	_simulation.wall_jump_height = wall_jump_height
	_simulation.wall_jump_horizontal_speed = wall_jump_horizontal_speed

	_current_state = MovementSimulation.MovementState.new()
	_current_state.has_chunk = true
	_base_max_speed = _simulation.max_speed

	var root: Node = get_parent()
	if root != null:
		var handler: Node = root.get_node_or_null("InfectionInteractionHandler")
		if handler != null and handler.has_method("get_mutation_slot"):
			_mutation_slot = handler.call("get_mutation_slot")

func _process(_delta: float) -> void:
	var cam: Camera3D = get_node_or_null("Gimbal/Camera3D") as Camera3D
	if cam != null:
		cam.look_at(global_position)

	var trail: CPUParticles3D = get_node_or_null("ParticleTrail") as CPUParticles3D
	if trail != null:
		var moving: bool = abs(velocity.x) > 0.5 or abs(velocity.y) > 0.5
		trail.emitting = is_on_floor() and moving

func _physics_process(delta: float) -> void:
	var input_axis: float = Input.get_axis("move_left", "move_right")
	var jump_pressed: bool = Input.is_action_pressed("jump")
	var jump_just_pressed: bool = Input.is_action_just_pressed("jump")
	var detach_just_pressed: bool = Input.is_action_just_pressed("detach")

	_current_state.is_on_floor = is_on_floor()

	var is_on_wall_now: bool = is_on_wall()
	var wall_normal_x: float = 0.0
	if is_on_wall_now:
		wall_normal_x = get_wall_normal().x

	if _base_max_speed <= 0.0:
		_base_max_speed = _simulation.max_speed
	var speed_multiplier: float = 1.0
	if _mutation_slot != null and _mutation_slot.has_method("is_filled") and _mutation_slot.is_filled():
		speed_multiplier = _MUTATION_SPEED_MULTIPLIER
	_simulation.max_speed = _base_max_speed * speed_multiplier

	var next_state: MovementSimulation.MovementState = _simulation.simulate(
		_current_state, input_axis, jump_pressed, jump_just_pressed, is_on_wall_now, wall_normal_x, detach_just_pressed, delta
	)

	# Jump SFX + squash/stretch (kit pattern)
	if next_state.jump_consumed and not _current_state.jump_consumed:
		var am = _get_audio_manager()
		if am != null and am.jump_sfx != null:
			am.jump_sfx.pitch_scale = randf_range(1.0, 1.15)
			am.jump_sfx.play()
		_juice_jump_stretch()

	# Map 2D sim velocity to 3D (pixels/s -> m/s): X horizontal, 2D y+ down -> 3D y-.
	velocity = Vector3(
		next_state.velocity.x / SCALE_2D_TO_3D,
		-next_state.velocity.y / SCALE_2D_TO_3D,
		0.0
	)

	# Lock Z to plane.
	var pos: Vector3 = global_position
	pos.z = 0.0
	global_position = pos

	move_and_slide()

	# Land squash: just landed this frame
	if is_on_floor() and not _current_state.is_on_floor:
		_juice_land_squash()

	# Feed back engine-corrected velocity into sim state (m/s -> pixels/s, 2D y+ down).
	_current_state.velocity = Vector2(velocity.x * SCALE_2D_TO_3D, -velocity.y * SCALE_2D_TO_3D)
	_current_state.coyote_timer = next_state.coyote_timer
	_current_state.jump_consumed = next_state.jump_consumed
	_current_state.is_wall_clinging = next_state.is_wall_clinging
	_current_state.cling_timer = next_state.cling_timer
	_current_state.current_hp = next_state.current_hp

	var prev_has_chunk: bool = _current_state.has_chunk

	var recall_pressed: bool = (
		detach_just_pressed
		and (not prev_has_chunk)
		and _chunk_node != null
		and is_instance_valid(_chunk_node)
	)
	if recall_pressed and not _recall_in_progress:
		_recall_in_progress = true
		_recall_timer = 0.0
		if _chunk_node != null and is_instance_valid(_chunk_node):
			recall_started.emit(global_position, _chunk_node.global_position)

	_current_state.has_chunk = next_state.has_chunk

	if prev_has_chunk and not _current_state.has_chunk:
		var chunk: RigidBody3D = _CHUNK_SCENE.instantiate() as RigidBody3D
		assert(chunk != null, "chunk_3d.tscn root must be RigidBody3D")
		# Lob direction: same as movement, or right if standing still.
		var lob_dir: float = 1.0
		if abs(velocity.x) > 0.1:
			lob_dir = 1.0 if velocity.x > 0.0 else -1.0
		var spawn_offset: Vector3 = Vector3(lob_dir * _DETACH_SPAWN_OFFSET, 0.0, 0.0)
		chunk.global_position = global_position + spawn_offset
		var parent: Node = get_parent()
		if parent == null:
			push_error("PlayerController3D: cannot detach chunk — node has no parent")
		else:
			parent.add_child(chunk)
			_chunk_node = chunk
			chunk.freeze = false
			chunk.linear_velocity = Vector3(lob_dir * detach_lob_horizontal, detach_lob_upward, 0.0)
			var am := _get_audio_manager()
			if am != null and am.detach_sfx != null:
				am.detach_sfx.play()
			_juice_detach_pop()
			detach_fired.emit(global_position, chunk.global_position)

	if _recall_in_progress:
		_recall_timer += delta
		if _chunk_node == null or not is_instance_valid(_chunk_node):
			_recall_in_progress = false
		elif _recall_timer >= _RECALL_TRAVEL_TIME:
			_recall_in_progress = false
			var prior_hp: float = _current_state.current_hp
			_current_state.current_hp = minf(_simulation.max_hp, prior_hp + _simulation.hp_cost_per_detach)
			_current_state.has_chunk = true
			if _chunk_node != null and is_instance_valid(_chunk_node):
				var am := _get_audio_manager()
				if am != null and am.recall_sfx != null:
					am.recall_sfx.play()
				_juice_recall_pop()
				chunk_reabsorbed.emit(global_position, _chunk_node.global_position)
				_chunk_node.queue_free()
			_chunk_node = null

func _get_visual_node() -> Node3D:
	return get_node_or_null("SlimeVisual") as Node3D

func _juice_jump_stretch() -> void:
	var vis: Node3D = _get_visual_node()
	if vis == null:
		return
	var tween := create_tween()
	tween.tween_property(vis, "scale", jump_stretch_scale, juice_tween_duration)
	tween.tween_property(vis, "scale", Vector3.ONE, juice_tween_duration)

func _juice_land_squash() -> void:
	var vis: Node3D = _get_visual_node()
	if vis == null:
		return
	var squash := Vector3(1.15, 0.85, 1.15)
	var tween := create_tween()
	tween.tween_property(vis, "scale", squash, juice_tween_duration)
	tween.tween_property(vis, "scale", Vector3.ONE, juice_tween_duration * 1.2)

func _juice_detach_pop() -> void:
	var vis: Node3D = _get_visual_node()
	if vis == null:
		return
	var pop := Vector3(1.08, 1.08, 1.08)
	var tween := create_tween()
	tween.tween_property(vis, "scale", pop, juice_tween_duration * 0.5)
	tween.tween_property(vis, "scale", Vector3.ONE, juice_tween_duration)

func _juice_recall_pop() -> void:
	var vis: Node3D = _get_visual_node()
	if vis == null:
		return
	var pop := Vector3(1.05, 1.05, 1.05)
	var tween := create_tween()
	tween.tween_property(vis, "scale", pop, juice_tween_duration * 0.5)
	tween.tween_property(vis, "scale", Vector3.ONE, juice_tween_duration)

func _get_audio_manager() -> Node:
	if not is_inside_tree():
		return null
	var root: Node = get_tree().root
	return root.get_node_or_null("AudioManager")

func get_current_hp() -> float:
	return _current_state.current_hp

func has_chunk() -> bool:
	return _current_state.has_chunk

func is_wall_clinging_state() -> bool:
	return _current_state.is_wall_clinging
