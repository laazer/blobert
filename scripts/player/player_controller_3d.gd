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

# Per-slot chunk state — index 0 = slot 1 (detach), index 1 = slot 2 (detach_2).
var _chunks: Array = [null, null]             # RigidBody3D per slot
var _recall_in_progress: Array = [false, false]
var _recall_timer: Array = [0.0, 0.0]
var _chunk_stuck: Array = [false, false]      # true while frozen on an enemy
var _chunk_stuck_enemy: Array = [null, null]  # EnemyInfection3D per slot
## Chunk DoT: 3 steps (weaken → infect → release or mini-boss absorb), spaced by interval.
var _chunk_dot_ticks_remaining: Array[int] = [0, 0]
var _chunk_dot_time_accum: Array[float] = [0.0, 0.0]
var _infection_handler: Node = null

## Seconds between chunk damage steps while stuck on an enemy.
@export var chunk_dot_step_interval: float = 0.45
# True after a spawn until detach_just goes false — prevents the same
# just_pressed event from immediately triggering a recall on the next
# physics tick within the same display frame.
var _detach_spawned: Array = [false, false]

const _RECALL_TRAVEL_TIME: float = 0.25
const _CHUNK_SCENE: PackedScene = preload("res://scenes/chunk/chunk_3d.tscn")

var _mutation_slot: Object = null
var _base_max_speed: float = 0.0
const _MUTATION_SPEED_MULTIPLIER: float = 1.25

var _fusion_timer: float = 0.0
var _fusion_active: bool = false
var _fusion_multiplier: float = 1.0

signal detach_fired(player_position: Vector3, chunk_position: Vector3)
signal recall_started(player_position: Vector3, chunk_position: Vector3)
signal chunk_reabsorbed(player_position: Vector3, chunk_position: Vector3)
signal detach_2_fired(player_position: Vector3, chunk_position: Vector3)
signal recall_2_started(player_position: Vector3, chunk_position: Vector3)
signal chunk_2_reabsorbed(player_position: Vector3, chunk_position: Vector3)

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
## Spawn height (m) above player origin so chunk clears the floor.
## Player origin Y≈0 on floor; chunk radius=0.5 → 0.75 gives 0.25m clearance.
const _DETACH_SPAWN_HEIGHT: float = 0.75

## Game juice: jump stretch (kit jumpStretchSize). Scale applied to SlimeVisual.
@export var jump_stretch_scale: Vector3 = Vector3(0.85, 1.15, 0.85)
@export var juice_tween_duration: float = 0.1


func _ready() -> void:
	_simulation = MovementSimulation.new()
	var project_gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity", 9.8) as float
	_simulation.gravity = project_gravity * SCALE_2D_TO_3D
	_simulation.jump_height = jump_height
	_simulation.coyote_time = coyote_time
	_simulation.jump_cut_velocity = jump_cut_velocity
	_simulation.cling_gravity_scale = cling_gravity_scale
	_simulation.max_cling_time = max_cling_time
	_simulation.wall_jump_height = wall_jump_height
	_simulation.wall_jump_horizontal_speed = wall_jump_horizontal_speed
	_current_state = MovementSimulation.MovementState.new()
	_current_state.has_chunks[0] = true
	_current_state.has_chunks[1] = true
	_base_max_speed = _simulation.max_speed

	var root: Node = get_parent()
	if root != null:
		var handler: Node = root.get_node_or_null("InfectionInteractionHandler")
		_infection_handler = handler
		if handler != null:
			if handler.has_method("get_mutation_slot_manager"):
				_mutation_slot = handler.call("get_mutation_slot_manager")
			elif handler.has_method("get_mutation_slot"):
				_mutation_slot = handler.call("get_mutation_slot")
			handler.absorb_resolved.connect(_on_absorb_resolved)
		var enemies: Array = root.find_children("*", "EnemyInfection3D", true, false)
		for enemy in enemies:
			enemy.chunk_attached.connect(_on_enemy_chunk_attached.bind(enemy))


func _exit_tree() -> void:
	if not is_inside_tree():
		return
	var root: Node = get_parent()
	if root == null:
		return
	var enemies: Array = root.find_children("*", "EnemyInfection3D", true, false)
	for enemy in enemies:
		if is_instance_valid(enemy) and enemy.chunk_attached.is_connected(_on_enemy_chunk_attached):
			enemy.chunk_attached.disconnect(_on_enemy_chunk_attached)


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
	var detach_2_just_pressed: bool = Input.is_action_just_pressed("detach_2")

	_current_state.is_on_floor = is_on_floor()

	var is_on_wall_now: bool = is_on_wall()
	var wall_normal_x: float = 0.0
	if is_on_wall_now:
		wall_normal_x = get_wall_normal().x

	if _base_max_speed <= 0.0:
		_base_max_speed = _simulation.max_speed

	if _fusion_active:
		_fusion_timer -= delta
		if _fusion_timer > 0.0:
			_simulation.max_speed = _base_max_speed * _fusion_multiplier
		else:
			_fusion_active = false
			_fusion_timer = 0.0
			_fusion_multiplier = 1.0
	else:
		var speed_multiplier: float = 1.0
		if _mutation_slot != null:
			var mutation_active: bool = false
			if _mutation_slot.has_method("any_filled"):
				mutation_active = _mutation_slot.any_filled()
			elif _mutation_slot.has_method("is_filled"):
				mutation_active = _mutation_slot.is_filled()
			if mutation_active:
				speed_multiplier = _MUTATION_SPEED_MULTIPLIER
		_simulation.max_speed = _base_max_speed * speed_multiplier

	var next_state: MovementSimulation.MovementState = _simulation.simulate(
		_current_state, input_axis, jump_pressed, jump_just_pressed,
		is_on_wall_now, wall_normal_x, detach_just_pressed, delta, detach_2_just_pressed
	)

	if next_state.jump_consumed and not _current_state.jump_consumed:
		var am := _get_audio_manager()
		if am != null and am.jump_sfx != null:
			am.jump_sfx.pitch_scale = randf_range(1.0, 1.15)
			am.jump_sfx.play()
		_juice_jump_stretch()

	velocity = Vector3(
		next_state.velocity.x / SCALE_2D_TO_3D,
		-next_state.velocity.y / SCALE_2D_TO_3D,
		0.0
	)

	var pos: Vector3 = global_position
	pos.z = 0.0
	global_position = pos

	move_and_slide()

	if is_on_floor() and not _current_state.is_on_floor:
		_juice_land_squash()

	_current_state.velocity = Vector2(velocity.x * SCALE_2D_TO_3D, -velocity.y * SCALE_2D_TO_3D)
	_current_state.coyote_timer = next_state.coyote_timer
	_current_state.jump_consumed = next_state.jump_consumed
	_current_state.is_wall_clinging = next_state.is_wall_clinging
	_current_state.cling_timer = next_state.cling_timer
	_current_state.current_hp = next_state.current_hp

	var detach_inputs: Array = [detach_just_pressed, detach_2_just_pressed]
	for i in 2:
		_process_chunk_slot(i, detach_inputs[i], next_state, delta)


func _process_chunk_slot(i: int, detach_just: bool, next_state: MovementSimulation.MovementState, delta: float) -> void:
	var prev_has: bool = _get_has_chunk(i)
	var chunk: RigidBody3D = _chunks[i] as RigidBody3D

	if _chunk_stuck[i] and _chunk_dot_ticks_remaining[i] > 0:
		_chunk_dot_time_accum[i] += delta
		if _chunk_dot_time_accum[i] >= chunk_dot_step_interval:
			_chunk_dot_time_accum[i] -= chunk_dot_step_interval
			_apply_chunk_dot_step(i)

	# Kill-plane: recover a live chunk that has fallen below the platform.
	# Threshold matches the respawn zone bottom (-9 m) with some margin.
	const CHUNK_KILL_Y: float = -4.0
	if not prev_has and not _recall_in_progress[i] and not _chunk_stuck[i] \
			and chunk != null and is_instance_valid(chunk) \
			and chunk.global_position.y < CHUNK_KILL_Y:
		chunk.queue_free()
		_chunks[i] = null
		_set_has_chunk(i, true)
		return

	# Recover slot if chunk reference became invalid externally. Never fire
	# while stuck on an enemy — _on_absorb_resolved handles that path.
	if not prev_has and not _recall_in_progress[i] and not _chunk_stuck[i] and (chunk == null or not is_instance_valid(chunk)):
		_chunk_stuck[i] = false
		_chunk_stuck_enemy[i] = null
		_chunks[i] = null
		_set_has_chunk(i, true)
		return

	# Clear the spawn-guard once the key is released so the next press works.
	if not detach_just:
		_detach_spawned[i] = false

	var recall_pressed: bool = (
		detach_just
		and (not prev_has)
		and chunk != null
		and is_instance_valid(chunk)
		and (not _chunk_stuck[i])
		and (not _detach_spawned[i])
	)
	if recall_pressed and not _recall_in_progress[i]:
		_recall_in_progress[i] = true
		_recall_timer[i] = 0.0
		_emit_recall_started(i)

	_set_has_chunk(i, _next_has_chunk(i, next_state))

	if prev_has and not _get_has_chunk(i):
		_spawn_chunk(i)

	_tick_recall(i, delta)


func _spawn_chunk(i: int) -> void:
	var chunk: RigidBody3D = _CHUNK_SCENE.instantiate() as RigidBody3D
	assert(chunk != null, "chunk_3d.tscn root must be RigidBody3D")
	var lob_dir: float = 1.0
	if abs(velocity.x) > 0.1:
		lob_dir = 1.0 if velocity.x > 0.0 else -1.0
	var parent: Node = get_parent()
	if parent == null:
		push_error("PlayerController3D: cannot detach chunk — node has no parent")
		return
	parent.add_child(chunk)
	# Set global_position AFTER add_child so the physics body initialises
	# at the correct world position rather than the pre-tree local origin.
	chunk.global_position = global_position + Vector3(lob_dir * _DETACH_SPAWN_OFFSET, _DETACH_SPAWN_HEIGHT, 0.0)
	_chunks[i] = chunk
	_detach_spawned[i] = true
	chunk.add_collision_exception_with(self)
	chunk.freeze = false
	chunk.linear_velocity = Vector3(lob_dir * detach_lob_horizontal, detach_lob_upward, 0.0)
	_juice_detach_pop()
	if i == 0:
		var am := _get_audio_manager()
		if am != null and am.detach_sfx != null:
			am.detach_sfx.play()
		detach_fired.emit(global_position, chunk.global_position)
	else:
		detach_2_fired.emit(global_position, chunk.global_position)


func _tick_recall(i: int, delta: float) -> void:
	if not _recall_in_progress[i]:
		return
	_recall_timer[i] += delta
	var chunk: RigidBody3D = _chunks[i] as RigidBody3D
	if chunk == null or not is_instance_valid(chunk):
		_recall_in_progress[i] = false
		_chunk_stuck[i] = false
		_chunk_stuck_enemy[i] = null
		_chunks[i] = null
		_set_has_chunk(i, true)
		return
	if _recall_timer[i] >= _RECALL_TRAVEL_TIME:
		_recall_in_progress[i] = false
		_current_state.current_hp = minf(_simulation.max_hp, _current_state.current_hp + _simulation.hp_cost_per_detach)
		_set_has_chunk(i, true)
		var am := _get_audio_manager()
		if am != null and am.recall_sfx != null:
			am.recall_sfx.play()
		_juice_recall_pop()
		_emit_chunk_reabsorbed(i, chunk.global_position)
		chunk.queue_free()
		_chunk_stuck[i] = false
		_chunk_stuck_enemy[i] = null
		_chunks[i] = null


func _on_enemy_chunk_attached(chunk: RigidBody3D, enemy: EnemyInfection3D) -> void:
	if not is_instance_valid(chunk):
		return
	for i in 2:
		if chunk == _chunks[i]:
			chunk.linear_velocity = Vector3.ZERO
			chunk.freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
			chunk.freeze = true
			chunk.reparent(enemy, true)
			_chunk_stuck[i] = true
			_chunk_stuck_enemy[i] = enemy
			_chunk_dot_ticks_remaining[i] = 3
			_chunk_dot_time_accum[i] = 0.0
			return


func _release_chunk_after_dot(i: int) -> void:
	var enemy: EnemyInfection3D = _chunk_stuck_enemy[i] as EnemyInfection3D
	var chunk: RigidBody3D = _chunks[i] as RigidBody3D
	if chunk == null or not is_instance_valid(chunk) or enemy == null or not is_instance_valid(enemy):
		_chunk_dot_ticks_remaining[i] = 0
		_chunk_dot_time_accum[i] = 0.0
		return
	var level_root: Node = enemy.get_parent()
	if level_root == null:
		return
	enemy.unregister_attached_chunk(chunk)
	_chunk_dot_ticks_remaining[i] = 0
	_chunk_dot_time_accum[i] = 0.0
	# Keep world pose so the blob does not snap (e.g. under a scaled boss).
	chunk.reparent(level_root, true)
	chunk.freeze = false
	chunk.freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
	chunk.linear_velocity = Vector3.ZERO
	_chunk_stuck[i] = false
	_chunk_stuck_enemy[i] = null
	_recall_in_progress[i] = true
	_recall_timer[i] = 0.0
	_emit_recall_started(i)


func _apply_chunk_dot_step(i: int) -> void:
	var enemy: EnemyInfection3D = _chunk_stuck_enemy[i] as EnemyInfection3D
	if enemy == null or not is_instance_valid(enemy):
		_chunk_dot_ticks_remaining[i] = 0
		_chunk_dot_time_accum[i] = 0.0
		return
	var esm: EnemyStateMachine = enemy.get_esm()
	if esm == null:
		_chunk_dot_ticks_remaining[i] = 0
		_chunk_dot_time_accum[i] = 0.0
		return
	var remaining: int = _chunk_dot_ticks_remaining[i]
	if remaining == 3:
		esm.apply_weaken_event()
		_chunk_dot_ticks_remaining[i] = 2
		return
	if remaining == 2:
		esm.apply_infection_event()
		_chunk_dot_ticks_remaining[i] = 1
		return
	if remaining != 1:
		return
	# Mini-boss and regular enemies: third step only releases the blob (recall).
	# Absorb the enemy with R after chunk returns; infected boss stays in place until then.
	_release_chunk_after_dot(i)


func _on_absorb_resolved(esm: EnemyStateMachine) -> void:
	for i in 2:
		var stuck_enemy: EnemyInfection3D = _chunk_stuck_enemy[i] as EnemyInfection3D
		if _chunk_stuck[i] and stuck_enemy != null and is_instance_valid(stuck_enemy):
			if stuck_enemy.get_esm() == esm:
				_chunk_dot_ticks_remaining[i] = 0
				_chunk_dot_time_accum[i] = 0.0
				var chunk: RigidBody3D = _chunks[i] as RigidBody3D
				if chunk != null and is_instance_valid(chunk):
					stuck_enemy.unregister_attached_chunk(chunk)
					chunk.queue_free()
				_chunks[i] = null
				_set_has_chunk(i, true)
				_chunk_stuck[i] = false
				_chunk_stuck_enemy[i] = null
	_current_state.current_hp = minf(
		_simulation.max_hp,
		_current_state.current_hp + _simulation.hp_cost_per_detach
	)


func _get_has_chunk(i: int) -> bool:
	return _current_state.has_chunks[i]


func _set_has_chunk(i: int, val: bool) -> void:
	_current_state.has_chunks[i] = val


func _next_has_chunk(i: int, next: MovementSimulation.MovementState) -> bool:
	return next.has_chunks[i]


func _emit_recall_started(i: int) -> void:
	var chunk: RigidBody3D = _chunks[i] as RigidBody3D
	if chunk == null or not is_instance_valid(chunk):
		return
	if i == 0:
		recall_started.emit(global_position, chunk.global_position)
	else:
		recall_2_started.emit(global_position, chunk.global_position)


func _emit_chunk_reabsorbed(i: int, chunk_pos: Vector3) -> void:
	if i == 0:
		chunk_reabsorbed.emit(global_position, chunk_pos)
	else:
		chunk_2_reabsorbed.emit(global_position, chunk_pos)


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
	return _current_state.has_chunks[0]


func has_chunk_2() -> bool:
	return _current_state.has_chunks[1]


func is_wall_clinging_state() -> bool:
	return _current_state.is_wall_clinging


func is_fusion_active() -> bool:
	return _fusion_active


func apply_fusion_effect(duration: float, multiplier: float) -> void:
	if _fusion_active:
		_fusion_timer = maxf(_fusion_timer, duration)
		_fusion_multiplier = multiplier
		return
	_fusion_active = true
	_fusion_timer = duration
	_fusion_multiplier = multiplier
