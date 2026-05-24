# player_input_action_policy.gd
#
# Pure RefCounted input permit + consumption policy (M11-03).
# Spec: project_board/specs/input_action_mapping_spec.md (IAM-5, IAM-6)
# No Input.* or Node dependencies.

class_name PlayerInputActionPolicy
extends RefCounted

const PlayerStateMachine = preload("res://scripts/player/player_state_machine.gd")

const ACTION_MOVE_LEFT: StringName = &"move_left"
const ACTION_MOVE_RIGHT: StringName = &"move_right"
const ACTION_JUMP: StringName = &"jump"
const ACTION_DETACH: StringName = &"detach"
const ACTION_DETACH_2: StringName = &"detach_2"
const ACTION_ATTACK: StringName = &"attack"
const ACTION_ABSORB: StringName = &"absorb"
const ACTION_INFECT: StringName = &"infect"
const ACTION_FUSE: StringName = &"fuse"
const ACTION_MENU: StringName = &"menu"
const ACTION_DEBUG_KILL: StringName = &"debug_kill"

const _CATALOG: Array[StringName] = [
	ACTION_MOVE_LEFT,
	ACTION_MOVE_RIGHT,
	ACTION_JUMP,
	ACTION_DETACH,
	ACTION_DETACH_2,
	ACTION_ATTACK,
	ACTION_ABSORB,
	ACTION_INFECT,
	ACTION_FUSE,
	ACTION_MENU,
	ACTION_DEBUG_KILL,
]

const _INDEPENDENT_ORDER: Array[StringName] = [
	ACTION_MOVE_LEFT,
	ACTION_MOVE_RIGHT,
	ACTION_JUMP,
	ACTION_DETACH,
	ACTION_DETACH_2,
]

const _COMBAT_ORDER: Array[StringName] = [
	ACTION_ATTACK,
	ACTION_INFECT,
	ACTION_ABSORB,
	ACTION_FUSE,
]

## Set by controller from OS.is_debug_build(); tests toggle directly (IAM-9).
var debug_actions_enabled: bool = false

## IAM-5.2 matrix: state index -> action -> permitted (contextual ○ cells are true).
const _PERMIT_MATRIX: Dictionary = {
	PlayerStateMachine.PlayerState.IDLE: {
		ACTION_MOVE_LEFT: true,
		ACTION_MOVE_RIGHT: true,
		ACTION_JUMP: true,
		ACTION_DETACH: true,
		ACTION_DETACH_2: true,
		ACTION_ATTACK: true,
		ACTION_ABSORB: true,
		ACTION_INFECT: true,
		ACTION_FUSE: true,
		ACTION_MENU: true,
		ACTION_DEBUG_KILL: true,
	},
	PlayerStateMachine.PlayerState.WALK: {
		ACTION_MOVE_LEFT: true,
		ACTION_MOVE_RIGHT: true,
		ACTION_JUMP: true,
		ACTION_DETACH: true,
		ACTION_DETACH_2: true,
		ACTION_ATTACK: true,
		ACTION_ABSORB: true,
		ACTION_INFECT: true,
		ACTION_FUSE: true,
		ACTION_MENU: true,
		ACTION_DEBUG_KILL: true,
	},
	PlayerStateMachine.PlayerState.JUMP: {
		ACTION_MOVE_LEFT: true,
		ACTION_MOVE_RIGHT: true,
		ACTION_JUMP: false,
		ACTION_DETACH: true,
		ACTION_DETACH_2: true,
		ACTION_ATTACK: true,
		ACTION_ABSORB: false,
		ACTION_INFECT: false,
		ACTION_FUSE: true,
		ACTION_MENU: true,
		ACTION_DEBUG_KILL: true,
	},
	PlayerStateMachine.PlayerState.FALL: {
		ACTION_MOVE_LEFT: true,
		ACTION_MOVE_RIGHT: true,
		ACTION_JUMP: true,
		ACTION_DETACH: true,
		ACTION_DETACH_2: true,
		ACTION_ATTACK: true,
		ACTION_ABSORB: false,
		ACTION_INFECT: false,
		ACTION_FUSE: true,
		ACTION_MENU: true,
		ACTION_DEBUG_KILL: true,
	},
	PlayerStateMachine.PlayerState.FLOAT: {
		ACTION_MOVE_LEFT: true,
		ACTION_MOVE_RIGHT: true,
		ACTION_JUMP: true,
		ACTION_DETACH: false,
		ACTION_DETACH_2: false,
		ACTION_ATTACK: true,
		ACTION_ABSORB: false,
		ACTION_INFECT: false,
		ACTION_FUSE: true,
		ACTION_MENU: true,
		ACTION_DEBUG_KILL: true,
	},
	PlayerStateMachine.PlayerState.WALL_CLING: {
		ACTION_MOVE_LEFT: true,
		ACTION_MOVE_RIGHT: true,
		ACTION_JUMP: true,
		ACTION_DETACH: true,
		ACTION_DETACH_2: true,
		ACTION_ATTACK: true,
		ACTION_ABSORB: false,
		ACTION_INFECT: false,
		ACTION_FUSE: true,
		ACTION_MENU: true,
		ACTION_DEBUG_KILL: true,
	},
	PlayerStateMachine.PlayerState.ABSORB: {
		ACTION_MENU: true,
	},
	PlayerStateMachine.PlayerState.MUTATE: {
		ACTION_MENU: true,
	},
	PlayerStateMachine.PlayerState.HURT: {
		ACTION_MENU: true,
	},
	PlayerStateMachine.PlayerState.DEAD: {},
}


func normalize_action(action: StringName) -> StringName:
	match action:
		&"mutate":
			return ACTION_INFECT
		&"swap_mutation":
			return ACTION_FUSE
		_:
			return action


func is_action_permitted(
	state: PlayerStateMachine.PlayerState,
	action: StringName,
) -> bool:
	var canonical: StringName = normalize_action(action)
	if not _is_catalog_action(canonical):
		return false
	if canonical == ACTION_DEBUG_KILL:
		if not debug_actions_enabled:
			return false
		if state == PlayerStateMachine.PlayerState.DEAD:
			return false
		return _matrix_allows(state, canonical)
	return _matrix_allows(state, canonical)


func resolve_consumed_actions(
	state: PlayerStateMachine.PlayerState,
	actions_pressed: Array[StringName],
) -> Array[StringName]:
	var permitted: Array[StringName] = []
	for raw in actions_pressed:
		var canonical: StringName = normalize_action(raw)
		if is_action_permitted(state, canonical):
			if canonical not in permitted:
				permitted.append(canonical)
	if ACTION_MENU in permitted:
		return [ACTION_MENU]
	var result: Array[StringName] = []
	for action in _INDEPENDENT_ORDER:
		if action in permitted:
			result.append(action)
	for action in _COMBAT_ORDER:
		if action in permitted:
			result.append(action)
			break
	if ACTION_DEBUG_KILL in permitted:
		result.append(ACTION_DEBUG_KILL)
	return result


func _is_catalog_action(action: StringName) -> bool:
	return action in _CATALOG


func _matrix_allows(state: PlayerStateMachine.PlayerState, action: StringName) -> bool:
	var row: Variant = _PERMIT_MATRIX.get(state, null)
	if row == null:
		return false
	return bool(row.get(action, false))
