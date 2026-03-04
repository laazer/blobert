#
# detach_recall_fx_presenter.gd
#
# Presentation layer for detach/recall visual feedback. Subscribes to
# PlayerController signals and drives simple, readable placeholder VFX:
#   - brief player flash on detach and reabsorb
#   - optional tendril-style Line2D during recall window
# It also exposes a small test-state hook for headless tests.
#
# Spec: agent_context/projects/blobert/specs/detach_recall_fx_spec.md
#

extends Node

## Test hook: returns current cue state for headless assertions.
## Keys: detach_triggered, recall_started_triggered, reabsorbed_triggered, last_event (string).
func get_detach_recall_fx_test_state() -> Dictionary:
	return {
		"detach_triggered": _detach_triggered,
		"recall_started_triggered": _recall_started_triggered,
		"reabsorbed_triggered": _reabsorbed_triggered,
		"last_event": _last_event
	}

var _detach_triggered: bool = false
var _recall_started_triggered: bool = false
var _reabsorbed_triggered: bool = false
var _last_event: String = ""

var _player: PlayerController
var _player_visual: Node2D
var _tendril: Line2D


func _ready() -> void:
	_player = _get_player()
	if _player != null:
		_player.detach_fired.connect(_on_detach_fired)
		_player.recall_started.connect(_on_recall_started)
		_player.chunk_reabsorbed.connect(_on_chunk_reabsorbed)

		_player_visual = _player.get_node_or_null("PlayerVisual") as Node2D

		_tendril = Line2D.new()
		_tendril.width = 2.0
		_tendril.default_color = Color(0.8, 0.9, 1.0, 0.9)
		_tendril.visible = false
		add_child(_tendril)

	set_process(true)


func _process(_delta: float) -> void:
	# Keep tendril endpoints following player + chunk while recall is active.
	if _tendril != null and _tendril.visible and _player != null and _player._chunk_node != null and is_instance_valid(_player._chunk_node):
		var pts: PackedVector2Array = PackedVector2Array()
		pts.push_back(_player.global_position)
		pts.push_back(_player._chunk_node.global_position)
		_tendril.points = pts


func _get_player() -> PlayerController:
	var root: Node = get_parent()
	if root == null:
		return null
	return root.get_node_or_null("Player") as PlayerController


func _flash_player(color: Color, duration: float) -> void:
	if _player_visual == null:
		return
	var original: Color = _player_visual.modulate
	_player_visual.modulate = color
	var timer := get_tree().create_timer(duration)
	timer.timeout.connect(func() -> void:
		if is_instance_valid(_player_visual):
			_player_visual.modulate = original
	)


func _on_detach_fired(_player_position: Vector2, _chunk_position: Vector2) -> void:
	_detach_triggered = true
	_last_event = "detach"

	# Simple readable cue: brief bright flash on the slime body.
	_flash_player(Color(1.1, 1.1, 1.1, 1.0), 0.08)


func _on_recall_started(player_position: Vector2, chunk_position: Vector2) -> void:
	_recall_started_triggered = true
	_last_event = "recall_started"

	# Enable a simple tendril between player and chunk for the recall window.
	if _tendril != null:
		var pts: PackedVector2Array = PackedVector2Array()
		pts.push_back(player_position)
		pts.push_back(chunk_position)
		_tendril.points = pts
		_tendril.visible = true


func _on_chunk_reabsorbed(player_position: Vector2, _chunk_position: Vector2) -> void:
	_reabsorbed_triggered = true
	_last_event = "chunk_reabsorbed"

	# Clear tendril and show a distinct confirmation flash (slightly tinted).
	if _tendril != null:
		_tendril.visible = false

	_flash_player(Color(0.8, 1.0, 0.9, 1.0), 0.08)
