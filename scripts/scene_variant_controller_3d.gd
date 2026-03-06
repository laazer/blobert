## scene_variant_controller_3d.gd
##
## Lightweight controller that owns a SceneStateMachine instance for the 3D
## main scene and exposes a simple API for selecting variants in tests or
## debug flows. For this ticket, it is intentionally minimal and does not yet
## wire feature systems; it ensures that the state machine can be constructed
## and driven in a scene context without Node dependencies inside the
## SceneStateMachine itself.

extends Node


const _SCENE_STATE_MACHINE_SCRIPT: GDScript = preload("res://scripts/scene_state_machine.gd")


var _state_machine


func _ready() -> void:
	_state_machine = _SCENE_STATE_MACHINE_SCRIPT.new()


func get_state_machine():
	if _state_machine == null:
		_state_machine = _SCENE_STATE_MACHINE_SCRIPT.new()
	return _state_machine


func select_baseline() -> void:
	if _state_machine == null:
		return
	_state_machine.apply_event("select_baseline")


func select_infection_demo() -> void:
	if _state_machine == null:
		return
	_state_machine.apply_event("select_infection_demo")


func select_enemy_playtest() -> void:
	if _state_machine == null:
		return
	_state_machine.apply_event("select_enemy_playtest")

