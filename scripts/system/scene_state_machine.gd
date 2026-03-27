## scene_state_machine.gd
##
## Pure-logic scene variant state machine for the 3D main scene.
## Canonical states for this ticket:
##   - BASELINE
##   - INFECTION_DEMO
##   - ENEMY_PLAYTEST
##
## Public API (see tests/test_scene_state_machine*.gd):
##   - get_state_id() -> String
##   - get_config() -> Dictionary
##   - apply_event(event_id) -> void
##
## Recognized events (case-sensitive):
##   - "select_baseline"
##   - "select_infection_demo"
##   - "select_enemy_playtest"
##
## Unknown events, non-String event_ids, and redundant selections are strict
## no-ops. get_config() always returns a defensive copy of the internal
## configuration so callers may mutate the returned Dictionary without affecting
## the internal state.

class_name SceneStateMachine
extends RefCounted


const STATE_BASELINE: String = "BASELINE"
const STATE_INFECTION_DEMO: String = "INFECTION_DEMO"
const STATE_ENEMY_PLAYTEST: String = "ENEMY_PLAYTEST"

const EVENT_SELECT_BASELINE: String = "select_baseline"
const EVENT_SELECT_INFECTION_DEMO: String = "select_infection_demo"
const EVENT_SELECT_ENEMY_PLAYTEST: String = "select_enemy_playtest"


var _state_id: String = STATE_BASELINE


func get_state_id() -> String:
	return _state_id


func get_config() -> Dictionary:
	# Derive configuration flags from the current state and return a fresh
	# Dictionary instance on every call to ensure external mutation cannot
	# affect internal state.
	match _state_id:
		STATE_BASELINE:
			return {
				"enable_infection_loop": false,
				"enable_enemies": false,
				"enable_prototype_hud": true,
			}
		STATE_INFECTION_DEMO:
			return {
				"enable_infection_loop": true,
				"enable_enemies": false,
				"enable_prototype_hud": true,
			}
		STATE_ENEMY_PLAYTEST:
			return {
				"enable_infection_loop": false,
				"enable_enemies": true,
				"enable_prototype_hud": true,
			}
		_:
			push_error("SceneStateMachine: unhandled state in get_config: " + _state_id)
			return {}


func apply_event(event_id: Variant) -> void:
	# Non-String event identifiers are treated as strict no-ops.
	if typeof(event_id) != TYPE_STRING:
		return

	var event_str: String = event_id
	var target_state: String = _state_id

	match event_str:
		EVENT_SELECT_BASELINE:
			target_state = STATE_BASELINE
		EVENT_SELECT_INFECTION_DEMO:
			target_state = STATE_INFECTION_DEMO
		EVENT_SELECT_ENEMY_PLAYTEST:
			target_state = STATE_ENEMY_PLAYTEST
		_:
			# Unknown event ID: strict no-op.
			return

	# Redundant selection is a strict no-op for both state and configuration.
	if target_state == _state_id:
		return

	_state_id = target_state

