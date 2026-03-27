## scene_variant_controller_3d.gd
##
## Lightweight controller that owns a SceneStateMachine instance for the 3D
## main scene and exposes a simple API for selecting variants and querying
## feature-gate flags. Feature systems in the scene (or in tests) call
## is_infection_enabled(), is_enemies_enabled(), and is_prototype_hud_enabled()
## to determine whether they should be active for the current state.

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


## Feature-gate query helpers.
## These are the canonical read surface for any feature system that needs to
## change behaviour based on scene state. All three delegate to get_config()
## on the owned SceneStateMachine so the truth always lives in one place.

func is_infection_enabled() -> bool:
	if _state_machine == null:
		return false
	return _state_machine.get_config().get("enable_infection_loop", false)


func is_enemies_enabled() -> bool:
	if _state_machine == null:
		return false
	return _state_machine.get_config().get("enable_enemies", false)


func is_prototype_hud_enabled() -> bool:
	if _state_machine == null:
		return false
	return _state_machine.get_config().get("enable_prototype_hud", false)

