extends CanvasLayer

var _absorb_available: bool = false
var _player: PlayerController
var _initial_max_hp: float = 0.0
var _handler: Node
var _prev_mutation_count: int = 0
var _absorb_feedback_until_ms: int = 0


func _ready() -> void:
	_player = get_tree().get_first_node_in_group("player") as PlayerController
	var root: Node = get_parent()
	if root != null:
		_handler = root.get_node_or_null("InfectionInteractionHandler")


func set_absorb_available(available: bool) -> void:
	_absorb_available = available


func _get_absorb_prompt_label() -> Label:
	return get_node_or_null("AbsorbPromptLabel") as Label


func _get_hp_label() -> Label:
	return get_node_or_null("HPLabel") as Label


func _get_hp_bar() -> Range:
	return get_node_or_null("HPBar") as Range


func _get_chunk_label() -> Label:
	return get_node_or_null("ChunkStatusLabel") as Label


func _get_cling_label() -> Label:
	return get_node_or_null("ClingStatusLabel") as Label


func _get_mutation_label() -> Label:
	return get_node_or_null("MutationLabel") as Label


func _get_absorb_feedback_label() -> Label:
	return get_node_or_null("AbsorbFeedbackLabel") as Label


func _get_mutation_icon() -> Control:
	return get_node_or_null("MutationIcon") as Control


func _process(_delta: float) -> void:
	var absorb_label: Label = _get_absorb_prompt_label()
	if absorb_label != null:
		absorb_label.visible = _absorb_available

	_update_mutation_display()

	if _player == null:
		return

	var hp_label: Label = _get_hp_label()
	var hp_bar: Range = _get_hp_bar()
	if hp_label != null or hp_bar != null:
		var hp_value: float = _player.get_current_hp()
		if _initial_max_hp <= 0.0:
			_initial_max_hp = max(hp_value, 1.0)
		var effective_max: float = _initial_max_hp

		if hp_label != null:
			hp_label.text = "HP: " + str(int(round(hp_value))) + " / " + str(int(round(effective_max)))

		if hp_bar != null:
			hp_bar.min_value = 0.0
			hp_bar.max_value = effective_max
			var clamped_hp: float = clamp(hp_value, hp_bar.min_value, hp_bar.max_value)
			hp_bar.value = clamped_hp

	var chunk_label: Label = _get_chunk_label()
	if chunk_label != null:
		chunk_label.text = "Chunk: " + ("Attached" if _player.has_chunk() else "Detached")

	var cling_label: Label = _get_cling_label()
	if cling_label != null:
		cling_label.text = "Wall Cling: " + ("ON" if _player.is_wall_clinging_state() else "OFF")


func _update_mutation_display() -> void:
	var mutation_label: Label = _get_mutation_label()
	var absorb_feedback: Label = _get_absorb_feedback_label()
	var mutation_icon: Control = _get_mutation_icon()
	var inv: Object = null
	if _handler != null and _handler.has_method("get_mutation_inventory"):
		inv = _handler.get_mutation_inventory()
	var count: int = 0
	if inv != null and inv.has_method("get_granted_count"):
		count = inv.get_granted_count()

	if count > _prev_mutation_count:
		_absorb_feedback_until_ms = Time.get_ticks_msec() + 800
	_prev_mutation_count = count

	var now_ms: int = Time.get_ticks_msec()
	var showing_absorb_feedback: bool = now_ms < _absorb_feedback_until_ms

	if mutation_label != null:
		mutation_label.visible = count > 0
		mutation_label.text = "Mutation: " + str(count) + " active"
		if showing_absorb_feedback:
			mutation_label.modulate = Color(0.6, 1.0, 0.7, 1.0)
		else:
			mutation_label.modulate = Color(1.0, 1.0, 1.0, 1.0)

	if absorb_feedback != null:
		absorb_feedback.visible = showing_absorb_feedback

	if mutation_icon != null:
		mutation_icon.visible = count > 0

