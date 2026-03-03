extends CanvasLayer

var _absorb_available: bool = false


func set_absorb_available(available: bool) -> void:
	_absorb_available = available


func _get_absorb_prompt_label() -> Label:
	return get_node_or_null("AbsorbPromptLabel") as Label


func _process(_delta: float) -> void:
	var label: Label = _get_absorb_prompt_label()
	if label == null:
		return
	label.visible = _absorb_available


