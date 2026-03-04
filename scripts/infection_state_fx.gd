# infection_state_fx.gd
#
# Presentation: visual feedback for enemy infection states. Reads ESM state from
# parent EnemyInfection and drives a child EnemyVisual modulate. No gameplay logic.
#
# State-to-visual: idle = default, weakened = amber, infected = purple tint,
# dead = dark/hidden. Purely reactive to state.
#
# Ticket: infection_interaction.md (Task 9)

extends Node

var _enemy: Node2D
var _visual: CanvasItem
var _esm: EnemyStateMachine
var _state_label: Label


func _ready() -> void:
	var parent: Node = get_parent()
	if parent is EnemyInfection:
		_enemy = parent as EnemyInfection
		_esm = _enemy.get_esm()
	_visual = _get_visual_node()
	_state_label = get_node_or_null("StateLabel") as Label


func _get_visual_node() -> CanvasItem:
	if _enemy == null:
		return null
	return _enemy.get_node_or_null("EnemyVisual") as CanvasItem


func _process(_delta: float) -> void:
	if _visual == null:
		_visual = _get_visual_node()
	if _esm == null:
		return
	var state: String = _esm.get_state()
	if _visual != null:
		_visual.modulate = _modulate_for_state(state)
	if _state_label != null:
		_update_state_label(state)


func _modulate_for_state(state: String) -> Color:
	match state:
		"weakened":
			return Color(1.0, 0.85, 0.5, 1.0)
		"infected":
			return Color(0.75, 0.5, 1.0, 1.0)
		"dead":
			return Color(0.25, 0.25, 0.25, 0.5)
		_:
			return Color(1.0, 1.0, 1.0, 1.0)


func _update_state_label(state: String) -> void:
	match state:
		"weakened":
			_state_label.visible = true
			_state_label.text = "Weakened"
			_state_label.modulate = Color(1.0, 0.9, 0.6, 1.0)
		"infected":
			_state_label.visible = true
			_state_label.text = "Infected"
			_state_label.modulate = Color(0.85, 0.65, 1.0, 1.0)
		"dead":
			_state_label.visible = true
			_state_label.text = "Dead"
			_state_label.modulate = Color(0.5, 0.5, 0.5, 0.8)
		_:
			_state_label.visible = false
