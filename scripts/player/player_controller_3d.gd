# Normative physics frame pipeline: project_board/specs/player_physics_frame_order_spec.md
# Maps MovementSimulation Vector2 → Vector3 (X=horiz, Y=vert, Z=0 plane lock).

class_name PlayerController3D
extends BasePhysicsEntity3D

const MovementSimulation = preload("res://scripts/movement/movement_simulation.gd")
const PlayerStateMachine = preload("res://scripts/player/player_state_machine.gd")
const PlayerStateDerivationContext = preload("res://scripts/player/player_state_derivation_context.gd")
const _MOVE_SPEED_THRESHOLD: float = 0.12
const SCALE_2D_TO_3D: float = 100.0

var _simulation: MovementSimulation
var _current_state: MovementSimulation.MovementState
var _player_state_machine: PlayerStateMachine
var _player_state_ctx: PlayerStateDerivationContext

var _chunks: Array = [null, null]
var _recall_in_progress: Array = [false, false]
var _recall_timer: Array = [0.0, 0.0]
var _chunk_stuck: Array = [false, false]
var _chunk_stuck_enemy: Array = [null, null]
var _chunk_dot_ticks_remaining: Array[int] = [0, 0]
var _chunk_dot_time_accum: Array[float] = [0.0, 0.0]
var _infection_handler: Node = null

@export var chunk_dot_step_interval: float = 0.45
var _detach_spawned: Array = [false, false]

const _RECALL_TRAVEL_TIME: float = 0.25
const _CHUNK_SCENE: PackedScene = preload("res://scenes/chunk/chunk_3d.tscn")

var _mutation_slot: Object = null
var _base_max_speed: float = 5.0
const _MUTATION_SPEED_MULTIPLIER: float = 1.25

var _attack_executor: AttackExecutor
var _mutation_cooldowns: Dictionary = {}
var _input_policy: PlayerInputActionPolicy

var _fusion_timer: float = 0.0
var _fusion_active: bool = false
var _fusion_multiplier: float = 1.0

var _enemy_acid_dots: Array = []
var _enemy_movement_root_remaining: float = 0.0
var _jump_buffer_timer: float = 0.0
var _jump_buffer_pending_at_frame_start: bool = false
var _jump_pressed_last_frame: bool = false
var _detach_pressed_last_frame: bool = false
var _detach_2_pressed_last_frame: bool = false

const _GROUND_COLLISION_MASK: int = 1
const _ONE_WAY_COLLISION_MASK: int = 2
const _FULL_GROUND_MASK: int = 3

signal detach_fired(player_position: Vector3, chunk_position: Vector3)
signal recall_started(player_position: Vector3, chunk_position: Vector3)
signal chunk_reabsorbed(player_position: Vector3, chunk_position: Vector3)
signal detach_2_fired(player_position: Vector3, chunk_position: Vector3)
signal recall_2_started(player_position: Vector3, chunk_position: Vector3)
signal chunk_2_reabsorbed(player_position: Vector3, chunk_position: Vector3)

const _DEFAULT_MOVEMENT_MAX_SPEED_2D: float = 300.0
@export var movement_max_speed_2d: float = _DEFAULT_MOVEMENT_MAX_SPEED_2D
@export var jump_height: float = 120.0
@export var coyote_time: float = 0.1
@export var jump_buffer_time: float = 0.1
@export var jump_cut_velocity: float = -200.0
@export var cling_gravity_scale: float = 0.1
@export var max_cling_time: float = 1.5
@export var wall_jump_height: float = 100.0
@export var wall_jump_horizontal_speed: float = 180.0

@export var detach_lob_horizontal: float = 5.0
@export var detach_lob_upward: float = 8.0
const _DETACH_SPAWN_OFFSET: float = 0.4
const _DETACH_SPAWN_HEIGHT: float = 0.75

const _CHUNK_SLOT_COUNT: int = 2
const _CHUNK_KILL_PLANE_Y: float = -4.0
const _CHUNK_DOT_PHASE_WEAKEN: int = 3
const _CHUNK_DOT_PHASE_INFECT: int = 2
const _CHUNK_DOT_PHASE_RELEASE: int = 1

const _DEFAULT_PROJECT_GRAVITY: float = 9.8
const _TRAIL_VELOCITY_THRESHOLD: float = 0.5
const _JUMP_SFX_PITCH_MIN: float = 1.0
const _JUMP_SFX_PITCH_MAX: float = 1.15
const _PLAY_PLANE_Z: float = 0.0
const _DETACH_LOB_DIRECTION_VELOCITY_EPSILON: float = 0.1

const _LAND_SQUASH_SCALE: Vector3 = Vector3(1.15, 0.85, 1.15)
const _LAND_SQUASH_OUT_DURATION_FACTOR: float = 1.2
const _DETACH_POP_SCALE: Vector3 = Vector3(1.08, 1.08, 1.08)
const _RECALL_POP_SCALE: Vector3 = Vector3(1.05, 1.05, 1.05)
const _JUICE_POP_IN_DURATION_FACTOR: float = 0.5

const _ENEMY_ACID_DEFAULT_DOT_DURATION: float = 3.0
const _ENEMY_ACID_DEFAULT_TICK_INTERVAL: float = 0.5
const _ENEMY_ACID_MIN_TICK_INTERVAL: float = 0.01

@export var jump_stretch_scale: Vector3 = Vector3(0.85, 1.15, 0.85)
@export var juice_tween_duration: float = 0.1


func _ready() -> void:
	_simulation = MovementSimulation.new()
	_simulation.max_speed = movement_max_speed_2d
	var project_gravity: float = ProjectSettings.get_setting(
		"physics/3d/default_gravity", _DEFAULT_PROJECT_GRAVITY
	) as float
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
	_player_state_machine = PlayerStateMachine.new()
	_player_state_ctx = PlayerStateDerivationContext.new()
	_base_max_speed = _simulation.max_speed
	collision_mask = _FULL_GROUND_MASK
	_attack_executor = AttackExecutor.new()
	add_child(_attack_executor)
	_input_policy = PlayerInputActionPolicy.new()

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
	get_tree().node_added.connect(_on_node_added_to_tree)


func _exit_tree() -> void:
	if not is_inside_tree():
		return
	if get_tree().node_added.is_connected(_on_node_added_to_tree):
		get_tree().node_added.disconnect(_on_node_added_to_tree)
	var root: Node = get_parent()
	if root == null:
		return
	var enemies: Array = root.find_children("*", "EnemyInfection3D", true, false)
	for enemy in enemies:
		if is_instance_valid(enemy) and enemy.chunk_attached.is_connected(_on_enemy_chunk_attached):
			enemy.chunk_attached.disconnect(_on_enemy_chunk_attached)


func _on_node_added_to_tree(node: Node) -> void:
	if node is EnemyInfection3D:
		if not node.chunk_attached.is_connected(_on_enemy_chunk_attached):
			node.chunk_attached.connect(_on_enemy_chunk_attached.bind(node))


func _process(_delta: float) -> void:
	var cam: Camera3D = get_node_or_null("Gimbal/Camera3D") as Camera3D
	if cam != null:
		cam.look_at(global_position)
	var trail: CPUParticles3D = get_node_or_null("ParticleTrail") as CPUParticles3D
	if trail != null:
		var moving: bool = (
			absf(velocity.x) > _TRAIL_VELOCITY_THRESHOLD
			or absf(velocity.y) > _TRAIL_VELOCITY_THRESHOLD
		)
		trail.emitting = is_on_floor() and moving


func _physics_process(delta: float) -> void:
	var input: Dictionary = _read_player_input()                            # Step 0
	_jump_buffer_pending_at_frame_start = _jump_buffer_timer > 0.0
	_player_state_machine.update(delta)                                     # Step 1
	_tick_controller_timers(delta, input["jump_just_pressed"])              # Step 2
	var frame: Dictionary = _prepare_frame_collision_state(delta)           # Step 3
	var next_state: MovementSimulation.MovementState = _dispatch_movement(input, frame, delta) # Step 4
	_update_one_way_collision_mask()                                        # Step 5
	_sync_renderer_from_state(next_state)                                   # Step 6
	_apply_collision_slide()                                                # Step 7
	_post_slide_housekeeping(next_state, input, frame, delta)               # Step 8
	_sync_player_state_machine()                                            # Step 9


func _read_player_input() -> Dictionary:
	var input_axis: float = Input.get_axis("move_left", "move_right")
	var jump_pressed: bool = Input.is_action_pressed("jump")
	var jump_just_pressed: bool = Input.is_action_just_pressed("jump")
	if not jump_just_pressed and jump_pressed and not _jump_pressed_last_frame:
		jump_just_pressed = true
	_jump_pressed_last_frame = jump_pressed
	var detach_pressed: bool = Input.is_action_pressed("detach")
	var detach_just_pressed: bool = Input.is_action_just_pressed("detach")
	if not detach_just_pressed and detach_pressed and not _detach_pressed_last_frame:
		detach_just_pressed = true
	_detach_pressed_last_frame = detach_pressed
	var detach_2_pressed: bool = Input.is_action_pressed("detach_2")
	var detach_2_just_pressed: bool = Input.is_action_just_pressed("detach_2")
	if not detach_2_just_pressed and detach_2_pressed and not _detach_2_pressed_last_frame:
		detach_2_just_pressed = true
	_detach_2_pressed_last_frame = detach_2_pressed
	if _enemy_movement_root_remaining > 0.0:
		input_axis = 0.0
		jump_pressed = false
		jump_just_pressed = false
	var attack_just_pressed: bool = Input.is_action_just_pressed("attack")
	if OS.is_debug_build() and Input.is_action_just_pressed("debug_kill"):
		_current_state.current_hp = _simulation.min_hp
	return {
		"input_axis": input_axis,
		"jump_pressed": jump_pressed,
		"jump_just_pressed": jump_just_pressed,
		"detach_just_pressed": detach_just_pressed,
		"detach_2_just_pressed": detach_2_just_pressed,
		"attack_just_pressed": attack_just_pressed,
	}


func _tick_controller_timers(delta: float, jump_just_pressed: bool) -> void:
	var buffer_duration: float = maxf(0.0, jump_buffer_time)
	if jump_just_pressed and buffer_duration > 0.0:
		_jump_buffer_timer = buffer_duration
	_jump_buffer_timer = maxf(0.0, _jump_buffer_timer - delta)
	for cd_key in _mutation_cooldowns:
		_mutation_cooldowns[cd_key] = maxf(0.0, _mutation_cooldowns[cd_key] - maxf(0.0, delta))


func _prepare_frame_collision_state(delta: float) -> Dictionary:
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
	return {"is_on_wall_now": is_on_wall_now, "wall_normal_x": wall_normal_x}


func _dispatch_movement(
	input: Dictionary,
	frame: Dictionary,
	delta: float
) -> MovementSimulation.MovementState:
	var effective_jump_just_pressed: bool = input["jump_just_pressed"]
	if _jump_buffer_timer > 0.0 and is_on_floor():
		effective_jump_just_pressed = true
		_jump_buffer_timer = 0.0
	var next_state: MovementSimulation.MovementState = _simulation.simulate(
		_current_state,
		input["input_axis"],
		input["jump_pressed"],
		effective_jump_just_pressed,
		frame["is_on_wall_now"],
		frame["wall_normal_x"],
		[input["detach_just_pressed"], input["detach_2_just_pressed"]],
		delta
	)
	velocity = Vector3(
		next_state.velocity.x / SCALE_2D_TO_3D,
		-next_state.velocity.y / SCALE_2D_TO_3D,
		_PLAY_PLANE_Z
	)
	if _enemy_movement_root_remaining > 0.0:
		velocity.x = 0.0
	var pos: Vector3 = global_position
	pos.z = _PLAY_PLANE_Z
	global_position = pos
	return next_state


func _update_one_way_collision_mask() -> void:
	# PFO-7: ascending (vy>0) or airborne apex (vy==0) excludes one-way; grounded vy<=0 includes one-way.
	var exclude_one_way: bool = velocity.y > 0.0 or (not is_on_floor() and velocity.y == 0.0)
	collision_mask = _GROUND_COLLISION_MASK if exclude_one_way else _FULL_GROUND_MASK


func _sync_renderer_from_state(next_state: MovementSimulation.MovementState) -> void:
	if next_state.jump_consumed and not _current_state.jump_consumed:
		var am := _get_audio_manager()
		if am != null and am.jump_sfx != null:
			am.jump_sfx.pitch_scale = randf_range(_JUMP_SFX_PITCH_MIN, _JUMP_SFX_PITCH_MAX)
			am.jump_sfx.play()
		_juice_jump_stretch()


func _apply_collision_slide() -> void:
	move_and_slide()
	if _enemy_movement_root_remaining > 0.0:
		velocity.x = 0.0


func _post_slide_housekeeping(
	next_state: MovementSimulation.MovementState,
	input: Dictionary,
	frame: Dictionary,
	delta: float
) -> void:
	var landed_this_frame: bool = is_on_floor() and not _current_state.is_on_floor
	# EC-1: buffer consumes on first grounded frame; floor contact is unknown until after Step 7.
	if landed_this_frame and _jump_buffer_pending_at_frame_start:
		_jump_buffer_timer = 0.0
		_current_state.velocity = Vector2(velocity.x * SCALE_2D_TO_3D, -velocity.y * SCALE_2D_TO_3D)
		_current_state.coyote_timer = next_state.coyote_timer
		_current_state.is_wall_clinging = next_state.is_wall_clinging
		_current_state.cling_timer = next_state.cling_timer
		_current_state.is_on_floor = true
		_current_state.jump_consumed = false
		next_state = _simulation.simulate(
			_current_state,
			input["input_axis"],
			false,
			true,
			frame["is_on_wall_now"],
			frame["wall_normal_x"],
			[false, false],
			delta
		)
		velocity = Vector3(
			next_state.velocity.x / SCALE_2D_TO_3D,
			-next_state.velocity.y / SCALE_2D_TO_3D,
			_PLAY_PLANE_Z
		)
		if _enemy_movement_root_remaining > 0.0:
			velocity.x = 0.0
		_sync_renderer_from_state(next_state)
	if landed_this_frame:
		_juice_land_squash()
	_current_state.velocity = Vector2(velocity.x * SCALE_2D_TO_3D, -velocity.y * SCALE_2D_TO_3D)
	_current_state.coyote_timer = next_state.coyote_timer
	_current_state.jump_consumed = next_state.jump_consumed
	_current_state.is_wall_clinging = next_state.is_wall_clinging
	_current_state.cling_timer = next_state.cling_timer
	_current_state.current_hp = next_state.current_hp
	var can_afford_throw: bool = _current_state.current_hp >= _simulation.hp_cost_per_detach
	var detach_inputs: Array = [
		input["detach_just_pressed"] and can_afford_throw,
		input["detach_2_just_pressed"] and can_afford_throw,
	]
	for i in _CHUNK_SLOT_COUNT:
		_process_chunk_slot(i, detach_inputs[i], next_state, delta)
	_tick_enemy_acid_dots(delta)
	if _enemy_movement_root_remaining > 0.0:
		_enemy_movement_root_remaining = maxf(0.0, _enemy_movement_root_remaining - delta)
	if input["attack_just_pressed"]:
		_try_attack()


func get_one_way_collision_mask() -> int:
	return collision_mask


func sync_movement_simulation_exports() -> void:
	if _simulation == null:
		return
	_simulation.jump_height = jump_height
	_simulation.coyote_time = coyote_time
	_simulation.jump_cut_velocity = jump_cut_velocity
	_simulation.cling_gravity_scale = cling_gravity_scale
	_simulation.max_cling_time = max_cling_time
	_simulation.wall_jump_height = wall_jump_height
	_simulation.wall_jump_horizontal_speed = wall_jump_horizontal_speed


func _process_chunk_slot(i: int, detach_just: bool, next_state: MovementSimulation.MovementState, delta: float) -> void:
	var prev_has: bool = _get_has_chunk(i)
	var chunk: RigidBody3D = _chunks[i] as RigidBody3D

	if _chunk_stuck[i] and _chunk_dot_ticks_remaining[i] > 0:
		_chunk_dot_time_accum[i] += delta
		if _chunk_dot_time_accum[i] >= chunk_dot_step_interval:
			_chunk_dot_time_accum[i] -= chunk_dot_step_interval
			_apply_chunk_dot_step(i)

	# Kill-plane: recover a live chunk that has fallen below the platform.
	if not prev_has and not _recall_in_progress[i] and not _chunk_stuck[i] \
			and chunk != null and is_instance_valid(chunk) \
			and chunk.global_position.y < _CHUNK_KILL_PLANE_Y:
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
	if absf(velocity.x) > _DETACH_LOB_DIRECTION_VELOCITY_EPSILON:
		lob_dir = 1.0 if velocity.x > 0.0 else -1.0
	var parent: Node = get_parent()
	if parent == null:
		push_error("PlayerController3D: cannot detach chunk — node has no parent")
		return
	parent.add_child(chunk)
	# Set global_position AFTER add_child so the physics body initialises
	# at the correct world position rather than the pre-tree local origin.
	chunk.global_position = global_position + Vector3(
		lob_dir * _DETACH_SPAWN_OFFSET, _DETACH_SPAWN_HEIGHT, _PLAY_PLANE_Z
	)
	_chunks[i] = chunk
	_detach_spawned[i] = true
	chunk.add_collision_exception_with(self)
	chunk.freeze = false
	chunk.linear_velocity = Vector3(
		lob_dir * detach_lob_horizontal, detach_lob_upward, _PLAY_PLANE_Z
	)
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
	for i in _CHUNK_SLOT_COUNT:
		if chunk == _chunks[i]:
			chunk.linear_velocity = Vector3.ZERO
			chunk.freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
			chunk.freeze = true
			chunk.reparent(enemy, true)
			_chunk_stuck[i] = true
			_chunk_stuck_enemy[i] = enemy
			_chunk_dot_ticks_remaining[i] = _CHUNK_DOT_PHASE_WEAKEN
			_chunk_dot_time_accum[i] = 0.0
			# Immediate damage feedback when the chunk sticks (before DoT ticks).
			enemy.play_damage_hit_animation()
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
	if remaining == _CHUNK_DOT_PHASE_WEAKEN:
		esm.apply_weaken_event()
		enemy.play_damage_hit_animation()
		_chunk_dot_ticks_remaining[i] = _CHUNK_DOT_PHASE_INFECT
		return
	if remaining == _CHUNK_DOT_PHASE_INFECT:
		esm.apply_infection_event()
		enemy.play_damage_hit_animation()
		_chunk_dot_ticks_remaining[i] = _CHUNK_DOT_PHASE_RELEASE
		return
	if remaining != _CHUNK_DOT_PHASE_RELEASE:
		return
	# Mini-boss and regular enemies: third step only releases the blob (recall).
	# Absorb the enemy with R after chunk returns; infected boss stays in place until then.
	_release_chunk_after_dot(i)


func _on_absorb_resolved(esm: EnemyStateMachine) -> void:
	for i in _CHUNK_SLOT_COUNT:
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


func _juice_pop(target_scale: Vector3, in_dur: float, out_dur: float) -> void:
	var vis: Node3D = _get_visual_node()
	if vis == null:
		return
	var tween := create_tween()
	tween.tween_property(vis, "scale", target_scale, in_dur)
	tween.tween_property(vis, "scale", Vector3.ONE, out_dur)


func _juice_jump_stretch() -> void:
	_juice_pop(jump_stretch_scale, juice_tween_duration, juice_tween_duration)


func _juice_land_squash() -> void:
	_juice_pop(_LAND_SQUASH_SCALE, juice_tween_duration,
		juice_tween_duration * _LAND_SQUASH_OUT_DURATION_FACTOR)


func _juice_detach_pop() -> void:
	_juice_pop(_DETACH_POP_SCALE, juice_tween_duration * _JUICE_POP_IN_DURATION_FACTOR,
		juice_tween_duration)


func _juice_recall_pop() -> void:
	_juice_pop(_RECALL_POP_SCALE, juice_tween_duration * _JUICE_POP_IN_DURATION_FACTOR,
		juice_tween_duration)


func _get_audio_manager() -> Node:
	var tree: SceneTree = get_tree() if is_inside_tree() else null
	return tree.root.get_node_or_null("AudioManager") if tree else null


func get_facing_sign() -> float:
	if velocity.x < 0.0:
		return -1.0
	return 1.0


func get_attack_executor() -> AttackExecutor:
	return _attack_executor


func _try_attack() -> void:
	if _input_policy == null or _mutation_slot == null:
		return
	if not _input_policy.is_action_permitted(
		_player_state_machine.get_state(), PlayerInputActionPolicy.ACTION_ATTACK
	):
		return
	var slot_a = _mutation_slot.get_slot(0) if _mutation_slot.has_method("get_slot") else null
	var slot_b = _mutation_slot.get_slot(1) if _mutation_slot.has_method("get_slot") else null
	var a_filled: bool = slot_a != null and slot_a.is_filled()
	var b_filled: bool = slot_b != null and slot_b.is_filled()
	if not a_filled and not b_filled:
		return
	var db: Node = _get_attack_database()
	if db == null:
		return
	var attack_resource: AttackResource = null
	var cooldown_key: String = ""
	if a_filled and b_filled:
		var a_id: String = slot_a.get_active_mutation_id()
		var b_id: String = slot_b.get_active_mutation_id()
		attack_resource = db.get_fused_attack(a_id, b_id)
		if attack_resource != null:
			var pair: Array = [a_id, b_id]
			pair.sort()
			cooldown_key = "%s_%s" % [pair[0], pair[1]]
		else:
			attack_resource = db.get_base_attack(a_id)
			cooldown_key = a_id
	else:
		var mid: String = slot_a.get_active_mutation_id() if a_filled else slot_b.get_active_mutation_id()
		attack_resource = db.get_base_attack(mid)
		cooldown_key = mid
	if attack_resource == null or _mutation_cooldowns.get(cooldown_key, 0.0) > 0.0:
		return
	_attack_executor.execute_attack(attack_resource)
	_mutation_cooldowns[cooldown_key] = attack_resource.cooldown


func _get_attack_database() -> Node:
	var tree: SceneTree = get_tree() if is_inside_tree() else null
	return tree.root.get_node_or_null("AttackDatabase") if tree else null


func _is_mutation_active() -> bool:
	if _fusion_active:
		return true
	if _mutation_slot == null:
		return false
	if _mutation_slot.has_method("any_filled"):
		return _mutation_slot.any_filled()
	if _mutation_slot.has_method("is_filled"):
		return _mutation_slot.is_filled()
	return false


func _is_any_chunk_stuck() -> bool:
	for i in _CHUNK_SLOT_COUNT:
		if _chunk_stuck[i]:
			return true
	return false


func _sync_player_state_machine() -> void:
	_player_state_ctx.is_on_floor = is_on_floor()
	_player_state_ctx.horizontal_speed = absf(velocity.x)
	_player_state_ctx.vertical_velocity = velocity.y
	_player_state_ctx.move_speed_threshold = _MOVE_SPEED_THRESHOLD
	_player_state_ctx.is_wall_clinging = _current_state.is_wall_clinging
	_player_state_ctx.is_any_chunk_stuck = _is_any_chunk_stuck()
	_player_state_ctx.is_mutation_active = _is_mutation_active()
	_player_state_ctx.current_hp = _current_state.current_hp
	_player_state_ctx.min_hp = _simulation.min_hp
	_player_state_ctx.hurt_pending = false
	_player_state_machine.sync_from_context(_player_state_ctx)


func get_current_hp() -> float:
	return _current_state.current_hp


func take_damage(amount: float, knockback: Vector3) -> void:
	_current_state.current_hp = maxf(_simulation.min_hp, _current_state.current_hp - amount)
	_player_state_machine.notify_damage_taken()
	var k := knockback
	k.z = _PLAY_PLANE_Z
	velocity.x += k.x
	velocity.y += k.y


func reset_hp() -> void:
	_current_state.current_hp = _simulation.max_hp
	_player_state_machine.reset()
	_mutation_cooldowns.clear()
	_enemy_acid_dots.clear()
	_enemy_movement_root_remaining = 0.0
	_jump_buffer_timer = 0.0
	_jump_pressed_last_frame = false
	_detach_pressed_last_frame = false
	_detach_2_pressed_last_frame = false
	velocity = Vector3.ZERO
	_current_state.velocity = Vector2.ZERO
	_current_state.jump_consumed = false
	if InputMap.has_action("jump"):
		Input.action_release("jump")


func reset_chunks() -> void:
	for i in _CHUNK_SLOT_COUNT:
		if _chunks[i] != null and is_instance_valid(_chunks[i]):
			_chunks[i].queue_free()
		_chunks[i] = null
		_chunk_stuck[i] = false
		_chunk_stuck_enemy[i] = null
		_recall_in_progress[i] = false
		_recall_timer[i] = 0.0
		_chunk_dot_ticks_remaining[i] = 0
		_chunk_dot_time_accum[i] = 0.0
	_current_state.has_chunks[0] = true
	_current_state.has_chunks[1] = true


func reset_position(target: Vector3) -> void:
	# global_position is preferred for world-space teleport. position is set as
	# a fallback because global_position setter is unreliable in Godot 4.6.1
	# headless mode. In production, ContainmentHall01 root has identity transform
	# so position == global_position; no world-space error results.
	global_position = target
	position = target
	velocity = Vector3.ZERO
	_jump_buffer_timer = 0.0
	_jump_pressed_last_frame = false
	_detach_pressed_last_frame = false
	_detach_2_pressed_last_frame = false


func has_chunk() -> bool:
	return _current_state.has_chunks[0]


func has_chunk_2() -> bool:
	return _current_state.has_chunks[1]


func is_wall_clinging_state() -> bool:
	return _player_state_machine.get_state() == PlayerStateMachine.PlayerState.WALL_CLING


func get_player_state() -> PlayerStateMachine.PlayerState:
	return _player_state_machine.get_state()


func get_player_state_machine() -> PlayerStateMachine:
	return _player_state_machine


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


func apply_enemy_movement_root(duration_seconds: float) -> void:
	_enemy_movement_root_remaining = maxf(_enemy_movement_root_remaining, duration_seconds)


func get_enemy_movement_root_remaining() -> float:
	return _enemy_movement_root_remaining


func apply_enemy_acid_damage(
	impact_damage: float,
	dot_tick_damage: float,
	dot_duration_seconds: float = _ENEMY_ACID_DEFAULT_DOT_DURATION,
	dot_tick_interval: float = _ENEMY_ACID_DEFAULT_TICK_INTERVAL
) -> void:
	_current_state.current_hp = maxf(_simulation.min_hp, _current_state.current_hp - impact_damage)
	if impact_damage > 0.0:
		_player_state_machine.notify_damage_taken()
	var iv: float = maxf(_ENEMY_ACID_MIN_TICK_INTERVAL, dot_tick_interval)
	var n_ticks: int = int(round(dot_duration_seconds / iv))
	if n_ticks < 1:
		n_ticks = 1
	_enemy_acid_dots.append(
		{
			"accum": 0.0,
			"tick": dot_tick_damage,
			"interval": iv,
			"ticks_remaining": n_ticks,
		}
	)


func get_enemy_acid_dot_instance_count() -> int:
	return _enemy_acid_dots.size()


func _tick_enemy_acid_dots(delta: float) -> void:
	var idx: int = _enemy_acid_dots.size() - 1
	while idx >= 0:
		var d: Dictionary = _enemy_acid_dots[idx]
		d["accum"] = float(d["accum"]) + delta
		var interval: float = float(d["interval"])
		if float(d["accum"]) >= interval:
			var ticks_from_time: int = int(floor(float(d["accum"]) / interval))
			var rem: int = int(d["ticks_remaining"])
			var use: int = mini(ticks_from_time, rem)
			if use > 0:
				var dmg: float = float(d["tick"]) * float(use)
				_current_state.current_hp = maxf(_simulation.min_hp, _current_state.current_hp - dmg)
				if dmg > 0.0:
					_player_state_machine.notify_damage_taken()
				d["accum"] = float(d["accum"]) - float(use) * interval
				d["ticks_remaining"] = rem - use
		if int(d["ticks_remaining"]) <= 0:
			_enemy_acid_dots.remove_at(idx)
		idx -= 1
