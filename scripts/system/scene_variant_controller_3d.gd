## scene_variant_controller_3d.gd
##
## Lightweight controller that owns a SceneStateMachine instance for the 3D
## main scene and exposes a simple API for selecting variants in tests or
## debug flows. For this ticket, it is intentionally minimal and does not yet
## wire feature systems; it ensures that the state machine can be constructed
## and driven in a scene context without Node dependencies inside the
## SceneStateMachine itself.

extends Node


const _SCENE_STATE_MACHINE_SCRIPT: GDScript = preload("res://scripts/system/scene_state_machine.gd")


var _state_machine: SceneStateMachine


func _init() -> void:
	_state_machine = _SCENE_STATE_MACHINE_SCRIPT.new()


func get_state_machine() -> SceneStateMachine:
	return _state_machine


func select_baseline() -> void:
	if _state_machine == null:
		push_error("SceneVariantController3D: _state_machine is null in select_baseline")
		return
	_state_machine.apply_event(SceneStateMachine.EVENT_SELECT_BASELINE)


func select_infection_demo() -> void:
	if _state_machine == null:
		push_error("SceneVariantController3D: _state_machine is null in select_infection_demo")
		return
	_state_machine.apply_event(SceneStateMachine.EVENT_SELECT_INFECTION_DEMO)


func select_enemy_playtest() -> void:
	if _state_machine == null:
		push_error("SceneVariantController3D: _state_machine is null in select_enemy_playtest")
		return
	_state_machine.apply_event(SceneStateMachine.EVENT_SELECT_ENEMY_PLAYTEST)

