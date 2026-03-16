class_name InfectionUI
extends CanvasLayer

var _absorb_available: bool = false
var _player: PlayerController3D
var _initial_max_hp: float = 0.0
var _handler: Node
var _slot_manager: Object = null  # MutationSlotManager (preferred) or fallback MutationSlot

var _prev_mutation_count: int = 0
var _absorb_feedback_until_ms: int = 0


func _ready() -> void:
	_player = get_tree().get_first_node_in_group("player") as PlayerController3D
	var root: Node = get_parent()
	if root != null:
		_handler = root.get_node_or_null("InfectionInteractionHandler")
		if _handler != null:
			if _handler.has_method("get_mutation_slot_manager"):
				_slot_manager = _handler.get_mutation_slot_manager()
			elif _handler.has_method("get_mutation_slot"):
				_slot_manager = _handler.get_mutation_slot()



func set_absorb_available(available: bool) -> void:
	_absorb_available = available


func _get_absorb_prompt_label() -> Label:
	return get_node_or_null("AbsorbPromptLabel") as Label


func _get_fuse_prompt_label() -> Label:
	return get_node_or_null("FusePromptLabel") as Label


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


# Legacy single-slot label — kept for backward compat (DSM-4-AC-8).
func _get_mutation_slot_label() -> Label:
	return get_node_or_null("MutationSlotLabel") as Label


func _get_absorb_feedback_label() -> Label:
	return get_node_or_null("AbsorbFeedbackLabel") as Label


# Legacy single-slot icon — kept for backward compat (DSM-4-AC-8).
func _get_mutation_icon() -> ColorRect:
	return get_node_or_null("MutationIcon") as ColorRect


# --- Dual-slot node accessors (null-safe; no crash if absent from scene) ---

func _get_slot1_label() -> Label:
	return get_node_or_null("MutationSlot1Label") as Label


func _get_slot1_icon() -> ColorRect:
	return get_node_or_null("MutationIcon1") as ColorRect


func _get_slot2_label() -> Label:
	return get_node_or_null("MutationSlot2Label") as Label


func _get_slot2_icon() -> ColorRect:
	return get_node_or_null("MutationIcon2") as ColorRect


func _get_input_hints_config() -> Node:
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree == null or tree.root == null:
		return null
	return tree.root.get_node_or_null("InputHintsConfig")


func _collect_input_hint_labels() -> Array:
	var labels: Array = []

	var hints_root: Node = get_node_or_null("Hints")
	if hints_root != null:
		for child in hints_root.get_children():
			var label := child as Label
			if label != null:
				labels.append(label)

	var core_names: Array = ["MoveHint", "JumpHint", "DetachHint", "DetachRecallHint", "AbsorbHint"]
	for name in core_names:
		var label_node := get_node_or_null(name) as Label
		if label_node != null and not labels.has(label_node):
			labels.append(label_node)

	return labels


func _update_input_hints_visibility() -> void:
	var config: Node = _get_input_hints_config()
	var enabled: bool = true
	if config != null and ("input_hints_enabled" in config):
		enabled = config.input_hints_enabled

	var labels: Array = _collect_input_hint_labels()
	for label in labels:
		var typed_label := label as Label
		if typed_label != null:
			typed_label.visible = enabled


func _process(_delta: float) -> void:
	var absorb_label: Label = _get_absorb_prompt_label()
	if absorb_label != null:
		absorb_label.visible = _absorb_available

	var fuse_label: Label = _get_fuse_prompt_label()
	if fuse_label != null:
		var s0: Object = _get_slot(0)
		var s1: Object = _get_slot(1)
		var both_filled: bool = (
			s0 != null and s0.has_method("is_filled") and s0.is_filled()
			and s1 != null and s1.has_method("is_filled") and s1.is_filled()
		)
		fuse_label.visible = both_filled

	_update_input_hints_visibility()

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


# Drives mutation display for both slots each frame.
# When a MutationSlotManager is available the numbered slot labels/icons
# (MutationSlot1Label, MutationIcon1, MutationSlot2Label, MutationIcon2) are
# updated independently per slot. The legacy MutationSlotLabel / MutationIcon
# nodes reflect slot A state for backward compatibility.
func _update_mutation_display() -> void:
	var mutation_label: Label = _get_mutation_label()
	var absorb_feedback: Label = _get_absorb_feedback_label()
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
	var any_mutation: bool = count > 0

	# Drive dual-slot displays (DSM-4).
	_update_slot_display(1, _get_slot(0))
	_update_slot_display(2, _get_slot(1))

	# Legacy single-slot label (backward compat — shows slot A state or empty).
	var slot_label: Label = _get_mutation_slot_label()
	if slot_label != null:
		var s0: Object = _get_slot(0)
		var s0_filled: bool = s0 != null and s0.has_method("is_filled") and s0.is_filled()
		slot_label.visible = true
		if s0_filled:
			slot_label.text = "Mutation Slot: " + s0.get_active_mutation_id() + " active"
			slot_label.modulate = Color(0.9, 1.0, 0.9, 1.0)

		else:
			slot_label.text = "Mutation Slot: Empty"
			slot_label.modulate = Color(0.7, 0.7, 0.7, 1.0)

	if mutation_label != null:
		mutation_label.visible = any_mutation
		if any_mutation:
			mutation_label.text = "Mutations: " + str(count) + " absorbed"

		if showing_absorb_feedback:
			mutation_label.modulate = Color(0.6, 1.0, 0.7, 1.0)
		else:
			mutation_label.modulate = Color(1.0, 1.0, 1.0, 1.0)

	if absorb_feedback != null:
		absorb_feedback.visible = showing_absorb_feedback


func _get_slot(index: int) -> Object:
	if _slot_manager != null and _slot_manager.has_method("get_slot"):
		return _slot_manager.get_slot(index)
	# Fallback: treat _slot_manager as a single slot for index 0.
	if index == 0 and _slot_manager != null:
		return _slot_manager
	return null


func _update_slot_display(slot_number: int, slot: Object) -> void:
	var label: Label = get_node_or_null("MutationSlot" + str(slot_number) + "Label") as Label
	var icon: ColorRect = get_node_or_null("MutationIcon" + str(slot_number)) as ColorRect
	var filled: bool = slot != null and slot.has_method("is_filled") and slot.is_filled()
	var slot_id: String = ""
	if filled and slot.has_method("get_active_mutation_id"):
		slot_id = slot.get_active_mutation_id()

	if label != null:
		label.visible = true
		if filled and slot_id != "":
			label.text = "Slot " + str(slot_number) + ": " + slot_id + " active"

			label.modulate = Color(0.9, 1.0, 0.9, 1.0)
		else:
			label.text = "Slot " + str(slot_number) + ": Empty"
			label.modulate = Color(0.7, 0.7, 0.7, 1.0)

	if icon != null:
		icon.visible = true
		if filled:
			icon.color = Color(0.4, 0.85, 0.55, 1.0)
		else:
			icon.color = Color(0.2, 0.2, 0.2, 0.6)
