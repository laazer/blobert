# cling_state_fx.gd
#
# Presentation: visual feedback for wall cling state. Reads PlayerController
# cling state from parent and drives PlayerVisual sprite modulate tint.
# No gameplay logic; purely reactive to state changes.
#
# Spec: wall_cling_visual_readability_spec.md (Revision 1)
# Follows infection_state_fx.gd pattern for consistency.
#

extends Node

## Reference to parent PlayerController node
var _player: Node = null

## Reference to PlayerVisual (Polygon2D or CanvasItem) for modulate
var _visual: CanvasItem = null

## Optional particle emitter for wall cling slide trail
var _particle_emitter: Node = null

## Tint color constants (from spec)
const IDLE_TINT: Color = Color(0.4, 0.9, 0.6, 1.0)
const CLING_TINT: Color = Color(0.8, 1.0, 0.5, 1.0)


# ---------------------------------------------------------------------------
# _ready() — Initialize references to parent and child nodes
# ---------------------------------------------------------------------------

func _ready() -> void:
	# Cache parent node (should be PlayerController).
	_player = get_parent()

	# Locate PlayerVisual node (sibling or child).
	if _player != null:
		_visual = _player.get_node_or_null("PlayerVisual") as CanvasItem
		if _visual == null:
			# Try to find PlayerVisual as a child of _player.
			for child in _player.get_children():
				if child.name == "PlayerVisual" and child is CanvasItem:
					_visual = child
					break

	# Optionally locate particle emitter (child of this FX node).
	_particle_emitter = get_node_or_null("ClingTrail")


# ---------------------------------------------------------------------------
# _process() — Poll cling state and update visuals
# ---------------------------------------------------------------------------

func _process(_delta: float) -> void:
	# Ensure parent and visual are still valid.
	if _player == null:
		_player = get_parent()
		if _player == null:
			return

	if _visual == null:
		_visual = _player.get_node_or_null("PlayerVisual") as CanvasItem
		if _visual == null:
			return

	# Poll cling state from parent.
	var is_clinging: bool = false
	if _player.has_method("is_wall_clinging_state"):
		is_clinging = _player.is_wall_clinging_state()

	# Apply or remove tint based on state.
	if is_clinging:
		_apply_tint(CLING_TINT)
		_update_particle_emitter(true)
	else:
		_apply_tint(IDLE_TINT)
		_update_particle_emitter(false)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

## Apply color tint to visual (instantaneous, no fade).
func _apply_tint(color: Color) -> void:
	if _visual != null:
		_visual.modulate = color


## Manage particle emitter: enable while clinging, disable on detach.
func _update_particle_emitter(is_clinging: bool) -> void:
	if _particle_emitter == null:
		return

	# Only enable particles if is_clinging is true.
	# (Optional: could add velocity check here to only emit while sliding,
	# but for now, emit as long as cling state is true.)
	if _particle_emitter.has_property("emitting"):
		_particle_emitter.set("emitting", is_clinging)
