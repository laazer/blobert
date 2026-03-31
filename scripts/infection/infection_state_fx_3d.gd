## infection_state_fx_3d.gd
##
## Presentation: visual feedback for 3D enemy infection states. Reads
## EnemyStateMachine state from parent EnemyInfection3D node and drives a child
## EnemyVisual MeshInstance3D. No gameplay logic.
##
## Behavior:
## - When the enemy takes damage (transitions into weakened/infected), briefly
##   blinks the EnemyVisual for a fixed duration.
## - When the enemy reaches the dead state (including via absorb), hides the
##   entire enemy node so it disappears from the scene.

extends Node3D


const BLINK_DURATION_SECONDS: float = 0.35
const BLINK_FREQUENCY_HZ: float = 10.0


var _enemy: Node3D
var _visual: Node3D
var _esm: EnemyStateMachine

var _last_state: String = ""
var _blink_time_remaining: float = 0.0
var _blink_elapsed: float = 0.0


func _ready() -> void:
	_enemy = get_parent() as Node3D
	_visual = _get_visual_node()
	_esm = _get_esm_from_enemy()
	if _esm != null:
		_last_state = _esm.get_state()


func _get_visual_node() -> Node3D:
	if _enemy == null:
		return null
	return _enemy.get_node_or_null("EnemyVisual") as Node3D


func _get_esm_from_enemy() -> EnemyStateMachine:
	if _enemy == null:
		return null
	if _enemy.has_method("get_esm"):
		return _enemy.get_esm()
	return null


func _process(delta: float) -> void:
	if _enemy == null:
		_enemy = get_parent() as Node3D
	if _visual == null or not is_instance_valid(_visual):
		_visual = _get_visual_node()
	if _esm == null:
		_esm = _get_esm_from_enemy()
	if _esm == null:
		return

	var state: String = _esm.get_state()

	if state != _last_state:
		_on_state_changed(state)
		_last_state = state

	# Dead state: hide the enemy once and stop further FX updates.
	if state == "dead":
		if _enemy != null:
			_enemy.visible = false
		return

	_update_blink(delta)


func _on_state_changed(state: String) -> void:
	match state:
		"weakened", "infected":
			_start_blink()
		"dead":
			# Handled in _process; no-op here to avoid duplicate side effects.
			_blink_time_remaining = 0.0
			_blink_elapsed = 0.0
		_:
			pass


func _start_blink() -> void:
	_blink_time_remaining = BLINK_DURATION_SECONDS
	_blink_elapsed = 0.0
	if _visual != null:
		_visual.visible = true


func _update_blink(delta: float) -> void:
	if _visual == null:
		return
	if _blink_time_remaining <= 0.0:
		_visual.visible = true
		return

	_blink_time_remaining -= delta
	if _blink_time_remaining <= 0.0:
		_visual.visible = true
		return

	_blink_elapsed += delta
	var cycle: float = fmod(_blink_elapsed * BLINK_FREQUENCY_HZ, 1.0)
	_visual.visible = cycle < 0.5

