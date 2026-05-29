## Chunk detach, recall, stuck-on-enemy DoT, and infection sync for PlayerController3D.

class_name PlayerChunkSlotProcessor
extends RefCounted

const _CHUNK_SCENE: PackedScene = preload("res://scenes/chunk/chunk_3d.tscn")
const _RECALL_TRAVEL_TIME: float = 0.25
const _DETACH_SPAWN_OFFSET: float = 0.4
const _DETACH_SPAWN_HEIGHT: float = 0.75
const _CHUNK_SLOT_COUNT: int = 2
const _CHUNK_KILL_PLANE_Y: float = -4.0
const _CHUNK_DOT_PHASE_WEAKEN: int = 3
const _CHUNK_DOT_PHASE_INFECT: int = 2
const _CHUNK_DOT_PHASE_RELEASE: int = 1
const _PLAY_PLANE_Z: float = 0.0
const _DETACH_LOB_DIRECTION_VELOCITY_EPSILON: float = 0.1
const _DETACH_POP_SCALE: Vector3 = Vector3(1.08, 1.08, 1.08)
const _RECALL_POP_SCALE: Vector3 = Vector3(1.05, 1.05, 1.05)
const _JUICE_POP_IN_DURATION_FACTOR: float = 0.5

var _owner: PlayerController3D


func _init(owner: PlayerController3D) -> void:
	_owner = owner


func process_slot(
	i: int,
	detach_just: bool,
	next_state: MovementSimulation.MovementState,
	delta: float,
) -> void:
	var prev_has: bool = _get_has_chunk(i)
	var chunk: RigidBody3D = _owner._chunks[i] as RigidBody3D

	if _owner._chunk_stuck[i]:
		var stuck_enemy: EnemyInfection3D = _owner._chunk_stuck_enemy[i] as EnemyInfection3D
		if stuck_enemy == null or not is_instance_valid(stuck_enemy) or stuck_enemy.is_dead():
			_abort_stuck_chunk_slot(i)
		elif _owner._chunk_dot_ticks_remaining[i] > 0:
			_owner._chunk_dot_time_accum[i] += delta
			if _owner._chunk_dot_time_accum[i] >= _owner.chunk_dot_step_interval:
				_owner._chunk_dot_time_accum[i] -= _owner.chunk_dot_step_interval
				_apply_chunk_dot_step(i)

	if not prev_has and not _owner._recall_in_progress[i] and not _owner._chunk_stuck[i] \
			and chunk != null and is_instance_valid(chunk) \
			and chunk.global_position.y < _CHUNK_KILL_PLANE_Y:
		chunk.queue_free()
		_owner._chunks[i] = null
		_set_has_chunk(i, true)
		return

	if not prev_has and not _owner._recall_in_progress[i] and not _owner._chunk_stuck[i] \
			and (chunk == null or not is_instance_valid(chunk)):
		_owner._chunk_stuck[i] = false
		_owner._chunk_stuck_enemy[i] = null
		_owner._chunks[i] = null
		_set_has_chunk(i, true)
		return

	var spawn_blocks_recall: bool = _owner._detach_spawn_blocks_recall[i] > 0

	var recall_pressed: bool = (
		detach_just
		and (not prev_has)
		and chunk != null
		and is_instance_valid(chunk)
		and (not _owner._chunk_stuck[i])
		and not spawn_blocks_recall
	)
	if recall_pressed and not _owner._recall_in_progress[i]:
		_owner._recall_in_progress[i] = true
		_owner._recall_timer[i] = 0.0
		_emit_recall_started(i)

	_set_has_chunk(i, _next_has_chunk(i, next_state))

	if prev_has and not _get_has_chunk(i):
		_spawn_chunk(i)

	if _owner._detach_spawn_blocks_recall[i] > 0:
		_owner._detach_spawn_blocks_recall[i] -= 1

	_tick_recall(i, delta)


func on_enemy_chunk_attached(chunk: RigidBody3D, enemy: EnemyInfection3D) -> void:
	if not is_instance_valid(chunk):
		return
	for i in _CHUNK_SLOT_COUNT:
		if chunk == _owner._chunks[i]:
			chunk.linear_velocity = Vector3.ZERO
			chunk.freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
			chunk.freeze = true
			chunk.reparent(enemy, true)
			_owner._chunk_stuck[i] = true
			_owner._chunk_stuck_enemy[i] = enemy
			_owner._chunk_dot_ticks_remaining[i] = _CHUNK_DOT_PHASE_WEAKEN
			_owner._chunk_dot_time_accum[i] = 0.0
			enemy.play_damage_hit_animation()
			return


func on_absorb_resolved(esm: EnemyStateMachine) -> void:
	for i in _CHUNK_SLOT_COUNT:
		var stuck_enemy: EnemyInfection3D = _owner._chunk_stuck_enemy[i] as EnemyInfection3D
		if _owner._chunk_stuck[i] and stuck_enemy != null and is_instance_valid(stuck_enemy):
			if stuck_enemy.get_esm() == esm:
				_owner._chunk_dot_ticks_remaining[i] = 0
				_owner._chunk_dot_time_accum[i] = 0.0
				var chunk: RigidBody3D = _owner._chunks[i] as RigidBody3D
				if chunk != null and is_instance_valid(chunk):
					stuck_enemy.unregister_attached_chunk(chunk)
					chunk.queue_free()
				_owner._chunks[i] = null
				_set_has_chunk(i, true)
				_owner._chunk_stuck[i] = false
				_owner._chunk_stuck_enemy[i] = null
	_owner._current_state.current_hp = minf(
		_owner._simulation.max_hp,
		_owner._current_state.current_hp + _owner._simulation.hp_cost_per_detach
	)


func _spawn_chunk(i: int) -> void:
	var chunk: RigidBody3D = _CHUNK_SCENE.instantiate() as RigidBody3D
	assert(chunk != null, "chunk_3d.tscn root must be RigidBody3D")
	var lob_dir: float = 1.0
	if absf(_owner.velocity.x) > _DETACH_LOB_DIRECTION_VELOCITY_EPSILON:
		lob_dir = 1.0 if _owner.velocity.x > 0.0 else -1.0
	var parent: Node = _owner.get_parent()
	if parent == null:
		push_error("PlayerController3D: cannot detach chunk — node has no parent")
		return
	parent.add_child(chunk)
	chunk.global_position = _owner.global_position + Vector3(
		lob_dir * _DETACH_SPAWN_OFFSET, _DETACH_SPAWN_HEIGHT, _PLAY_PLANE_Z
	)
	_owner._chunks[i] = chunk
	_owner._detach_spawn_blocks_recall[i] = 1
	chunk.add_collision_exception_with(_owner)
	chunk.freeze = false
	chunk.linear_velocity = Vector3(
		lob_dir * _owner.detach_lob_horizontal, _owner.detach_lob_upward, _PLAY_PLANE_Z
	)
	_owner._juice_detach_pop()
	if i == 0:
		var am := _owner._get_audio_manager()
		if am != null and am.detach_sfx != null:
			am.detach_sfx.play()
		_owner.detach_fired.emit(_owner.global_position, chunk.global_position)
	else:
		_owner.detach_2_fired.emit(_owner.global_position, chunk.global_position)


func _tick_recall(i: int, delta: float) -> void:
	if not _owner._recall_in_progress[i]:
		return
	_owner._recall_timer[i] += delta
	var chunk: RigidBody3D = _owner._chunks[i] as RigidBody3D
	if chunk == null or not is_instance_valid(chunk):
		_owner._recall_in_progress[i] = false
		_owner._chunk_stuck[i] = false
		_owner._chunk_stuck_enemy[i] = null
		_owner._chunks[i] = null
		_set_has_chunk(i, true)
		return
	var recall_target: Vector3 = _owner.global_position + Vector3(0.0, _DETACH_SPAWN_HEIGHT, _PLAY_PLANE_Z)
	chunk.freeze = true
	chunk.freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
	chunk.linear_velocity = Vector3.ZERO
	var recall_t: float = clampf(_owner._recall_timer[i] / _RECALL_TRAVEL_TIME, 0.0, 1.0)
	chunk.global_position = chunk.global_position.lerp(recall_target, recall_t)

	if _owner._recall_timer[i] >= _RECALL_TRAVEL_TIME:
		chunk.global_position = recall_target
		_owner._recall_in_progress[i] = false
		_owner._current_state.current_hp = minf(
			_owner._simulation.max_hp,
			_owner._current_state.current_hp + _owner._simulation.hp_cost_per_detach
		)
		_set_has_chunk(i, true)
		var am := _owner._get_audio_manager()
		if am != null and am.recall_sfx != null:
			am.recall_sfx.play()
		_owner._juice_recall_pop()
		_emit_chunk_reabsorbed(i, chunk.global_position)
		chunk.queue_free()
		_owner._chunk_stuck[i] = false
		_owner._chunk_stuck_enemy[i] = null
		_owner._chunks[i] = null


func _release_chunk_after_dot(i: int) -> void:
	var enemy: EnemyInfection3D = _owner._chunk_stuck_enemy[i] as EnemyInfection3D
	var chunk: RigidBody3D = _owner._chunks[i] as RigidBody3D
	if chunk == null or not is_instance_valid(chunk) or enemy == null or not is_instance_valid(enemy):
		_owner._chunk_dot_ticks_remaining[i] = 0
		_owner._chunk_dot_time_accum[i] = 0.0
		return
	var level_root: Node = enemy.get_parent()
	if level_root == null:
		_abort_stuck_chunk_slot(i)
		return
	enemy.unregister_attached_chunk(chunk)
	_owner._chunk_dot_ticks_remaining[i] = 0
	_owner._chunk_dot_time_accum[i] = 0.0
	chunk.reparent(level_root, true)
	chunk.freeze = false
	chunk.freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
	chunk.linear_velocity = Vector3.ZERO
	_owner._chunk_stuck[i] = false
	_owner._chunk_stuck_enemy[i] = null
	_owner._recall_in_progress[i] = true
	_owner._recall_timer[i] = 0.0
	_emit_recall_started(i)


func _abort_stuck_chunk_slot(i: int) -> void:
	var enemy: EnemyInfection3D = _owner._chunk_stuck_enemy[i] as EnemyInfection3D
	var chunk: RigidBody3D = _owner._chunks[i] as RigidBody3D
	if enemy != null and is_instance_valid(enemy) and chunk != null and is_instance_valid(chunk):
		enemy.unregister_attached_chunk(chunk)
	_owner._chunk_dot_ticks_remaining[i] = 0
	_owner._chunk_dot_time_accum[i] = 0.0
	_owner._chunk_stuck[i] = false
	_owner._chunk_stuck_enemy[i] = null
	if chunk != null and is_instance_valid(chunk):
		var level_root: Node = _owner.get_parent()
		if level_root != null:
			chunk.reparent(level_root, true)
		chunk.freeze = false
		chunk.freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
		chunk.linear_velocity = Vector3.ZERO
		_owner._recall_in_progress[i] = true
		_owner._recall_timer[i] = 0.0
		_emit_recall_started(i)
	else:
		_owner._chunks[i] = null
		_owner._recall_in_progress[i] = false
		_owner._recall_timer[i] = 0.0
		_set_has_chunk(i, true)


func _apply_chunk_dot_step(i: int) -> void:
	var enemy: EnemyInfection3D = _owner._chunk_stuck_enemy[i] as EnemyInfection3D
	if enemy == null or not is_instance_valid(enemy):
		_abort_stuck_chunk_slot(i)
		return
	var esm: EnemyStateMachine = enemy.get_esm()
	if esm == null:
		_abort_stuck_chunk_slot(i)
		return
	if enemy.is_dead():
		_abort_stuck_chunk_slot(i)
		return
	var remaining: int = _owner._chunk_dot_ticks_remaining[i]
	if remaining == _CHUNK_DOT_PHASE_WEAKEN:
		esm.apply_weaken_event()
		enemy.play_damage_hit_animation()
		_owner._chunk_dot_ticks_remaining[i] = _CHUNK_DOT_PHASE_INFECT
		return
	if remaining == _CHUNK_DOT_PHASE_INFECT:
		esm.apply_infection_event()
		enemy.play_damage_hit_animation()
		_owner._chunk_dot_ticks_remaining[i] = _CHUNK_DOT_PHASE_RELEASE
		return
	if remaining != _CHUNK_DOT_PHASE_RELEASE:
		return
	_release_chunk_after_dot(i)


func _get_has_chunk(i: int) -> bool:
	return _owner._current_state.has_chunks[i]


func _set_has_chunk(i: int, val: bool) -> void:
	_owner._current_state.has_chunks[i] = val


func _next_has_chunk(i: int, next: MovementSimulation.MovementState) -> bool:
	return next.has_chunks[i]


func _emit_recall_started(i: int) -> void:
	var chunk: RigidBody3D = _owner._chunks[i] as RigidBody3D
	if chunk == null or not is_instance_valid(chunk):
		return
	if i == 0:
		_owner.recall_started.emit(_owner.global_position, chunk.global_position)
	else:
		_owner.recall_2_started.emit(_owner.global_position, chunk.global_position)


func _emit_chunk_reabsorbed(i: int, chunk_pos: Vector3) -> void:
	if i == 0:
		_owner.chunk_reabsorbed.emit(_owner.global_position, chunk_pos)
	else:
		_owner.chunk_2_reabsorbed.emit(_owner.global_position, chunk_pos)
