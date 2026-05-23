# player_state_machine.gd
#
# RefCounted gameplay FSM for PlayerController3D (M11-01).
# Distinct from MovementSimulation.MovementState (kinematic snapshot).
# Spec: project_board/specs/player_state_machine_spec.md

class_name PlayerStateMachine
extends RefCounted

const PlayerStateDerivationContext = preload("res://scripts/player/player_state_derivation_context.gd")


enum PlayerState {
	IDLE,
	WALK,
	JUMP,
	FALL,
	FLOAT,
	WALL_CLING,
	ABSORB,
	MUTATE,
	HURT,
	DEAD,
}

const MIN_FLOAT_FROM_JUMP_SEC: float = 0.05
const MIN_HURT_SEC: float = 0.0
const VERTICAL_JUMP_EPSILON: float = 0.01

const _FLOAT_ALLOWED_SOURCES: Array[int] = [
	PlayerState.JUMP,
	PlayerState.FALL,
	PlayerState.FLOAT,
]

var _state: PlayerState = PlayerState.IDLE
var _state_timer: float = 0.0
var _hurt_pending: bool = false
## Set when notify_damage_taken() is called while already HURT (EC-2); blocks same-state HURT no-op.
var _hurt_reentry_blocked: bool = false


func get_state() -> PlayerState:
	return _state


func get_state_timer() -> float:
	return _state_timer


func update(delta: float) -> void:
	_state_timer += maxf(0.0, delta)


func can_transition_to(new_state: PlayerState) -> bool:
	if _state == PlayerState.DEAD and new_state != PlayerState.DEAD:
		return false
	if new_state == PlayerState.HURT and (_state == PlayerState.HURT or _state == PlayerState.DEAD):
		return false
	if new_state == PlayerState.FLOAT and _state not in _FLOAT_ALLOWED_SOURCES:
		return false
	if new_state == _state:
		return true
	return true


func transition(new_state: PlayerState) -> bool:
	if new_state == _state:
		if new_state == PlayerState.HURT and _hurt_reentry_blocked:
			return false
		return true
	if not can_transition_to(new_state):
		return false
	if (
		new_state == PlayerState.FLOAT
		and _state == PlayerState.JUMP
		and _state_timer < MIN_FLOAT_FROM_JUMP_SEC
	):
		return false
	_state = new_state
	_state_timer = 0.0
	_hurt_reentry_blocked = false
	if new_state == PlayerState.HURT:
		_hurt_pending = true
	return true


func compute_derived_state(ctx: PlayerStateDerivationContext) -> PlayerState:
	if ctx.current_hp <= ctx.min_hp:
		return PlayerState.DEAD
	var hurt_active: bool = _hurt_pending or ctx.hurt_pending
	if hurt_active:
		return PlayerState.HURT
	if ctx.is_any_chunk_stuck:
		return PlayerState.ABSORB
	if ctx.is_mutation_active:
		return PlayerState.MUTATE
	if ctx.is_wall_clinging:
		return PlayerState.WALL_CLING
	if not ctx.is_on_floor:
		if ctx.vertical_velocity >= VERTICAL_JUMP_EPSILON:
			return PlayerState.JUMP
		return PlayerState.FALL
	if ctx.horizontal_speed > ctx.move_speed_threshold:
		return PlayerState.WALK
	return PlayerState.IDLE


func notify_damage_taken() -> void:
	if _state == PlayerState.HURT:
		_hurt_reentry_blocked = true
		return
	_hurt_pending = true


func sync_from_context(ctx: PlayerStateDerivationContext) -> void:
	var target: PlayerState = compute_derived_state(ctx)
	var prev: PlayerState = _state
	if transition(target):
		if target == PlayerState.HURT:
			_hurt_pending = false
		elif target == PlayerState.DEAD:
			_hurt_pending = false
	elif prev == PlayerState.HURT and target != PlayerState.HURT:
		_hurt_pending = false


func reset() -> void:
	_state = PlayerState.IDLE
	_state_timer = 0.0
	_hurt_pending = false
	_hurt_reentry_blocked = false
