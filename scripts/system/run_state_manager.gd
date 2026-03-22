# run_state_manager.gd
#
# Pure state machine for a single roguelike run lifecycle.
# No SceneTree API. Scene loading delegated to consumers via signals.
#
# Invariants:
#   - _state is always one of the four State enum values.
#   - Every valid transition emits its signal BEFORE updating _state.
#   - Invalid transitions (wrong event for current state, or unknown event) are strict no-ops.
#   - _slot_manager is created once in _init() and never replaced.
#
# Ticket: run_state_manager
# Spec:   agent_context/agents/2_spec/run_state_manager_spec.md

class_name RunStateManager
extends RefCounted

enum State { START = 0, ACTIVE = 1, DEAD = 2, WIN = 3 }

signal run_started
signal player_died
signal run_won
signal run_restarted

var _state: State = State.START
var _slot_manager: RefCounted


func _init() -> void:
	_slot_manager = preload("res://scripts/mutation/mutation_slot_manager.gd").new()


func get_state() -> State:
	return _state


func get_state_id() -> String:
	return State.keys()[_state]


func get_slot_manager() -> RefCounted:
	return _slot_manager


func apply_event(event: String) -> void:
	match [_state, event]:
		[State.START, "start_run"]:
			run_started.emit()
			_state = State.ACTIVE
		[State.ACTIVE, "player_died"]:
			player_died.emit()
			_state = State.DEAD
			_slot_manager.clear_all()
		[State.ACTIVE, "run_won"]:
			run_won.emit()
			_state = State.WIN
			_slot_manager.clear_all()
		[State.DEAD, "restart"]:
			run_restarted.emit()
			_state = State.START
		[State.WIN, "restart"]:
			run_restarted.emit()
			_state = State.START
		_:
			pass  # strict no-op: unknown event or wrong event for current state
