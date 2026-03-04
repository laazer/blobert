# enemy_state_machine.gd
#
# Pure enemy lifecycle state machine for the infection loop. No Node or scene
# dependencies. Canonical states: idle, active, weakened, infected, dead.
# Consumes discrete events (weaken, infection, death) and exposes state for
# other systems.
#
# Ticket: enemy_state_machine.md
# Spec: Idle/Active -> weakened (weaken); weakened -> infected (infect);
#       any non-dead -> dead (death); reset() -> idle from any state.
#       All other event/state combinations are no-ops.

class_name EnemyStateMachine
extends RefCounted


const STATE_IDLE: String = "idle"
const STATE_ACTIVE: String = "active"
const STATE_WEAKENED: String = "weakened"
const STATE_INFECTED: String = "infected"
const STATE_DEAD: String = "dead"


var _state: String = STATE_IDLE


func get_state() -> String:
	return _state


func apply_weaken_event() -> void:
	if _state == STATE_DEAD or _state == STATE_WEAKENED or _state == STATE_INFECTED:
		return
	if _state == STATE_IDLE or _state == STATE_ACTIVE:
		_state = STATE_WEAKENED


func apply_infection_event() -> void:
	if _state != STATE_WEAKENED:
		return
	_state = STATE_INFECTED


func apply_death_event() -> void:
	if _state == STATE_DEAD:
		return
	_state = STATE_DEAD


func reset() -> void:
	_state = STATE_IDLE
