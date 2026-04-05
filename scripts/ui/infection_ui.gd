class_name InfectionUI
extends CanvasLayer

# HUD scale (MAINT-HCSI / HCSI-1 … HCSI-5)
# Uniform scale factor for all packaged HUD controls in game_ui.tscn (direct Control
# children of this CanvasLayer, including the Hints subtree). Applied via Control.scale
# with pivot_offset (0,0) so top-left–anchored layout matches legacy positions at 1.0.
# Default 1.0 preserves scene offset_* and theme_override_font_sizes as authoring truth (HCSI-2).
# Set in the inspector on GameUI, via code, or scene instance overrides.
#
# Hints subtree: nested labels use Control.scale; the Hints container uses runtime
# offset_* (from design base below) so its layout size tracks hud_scale — required
# for global-rect / hit-test parity with sibling HUD controls under CanvasLayer.
@export var hud_scale: float = 1.0:
	get:
		return _hud_scale_value
	set(value):
		_hud_scale_value = _sanitize_hud_scale(value)
		_apply_hud_scale_to_direct_controls()

var _hud_scale_value: float = 1.0

# Must match game_ui.tscn Hints offset_right / offset_bottom at hud_scale == 1.0 (HCSI-2).
const _HINTS_PACK_BASE_W: float = 2000.0
const _HINTS_PACK_BASE_H: float = 102.0

# --- Named color constants (spec NF-1) ---

const COLOR_SLOT_EMPTY         = Color(0.2, 0.2, 0.2, 0.6)
const COLOR_SLOT_SINGLE_FILLED = Color(0.4, 0.85, 0.55, 1.0)
const COLOR_SLOT_DUAL_FILLED   = Color(0.3, 0.65, 1.0, 1.0)
const COLOR_SLOT_POST_FUSION   = Color(1.0, 1.0, 1.0, 1.0)

const COLOR_LABEL_EMPTY         = Color(0.7, 0.7, 0.7, 1.0)
const COLOR_LABEL_SINGLE_FILLED = Color(0.9, 1.0, 0.9, 1.0)
const COLOR_LABEL_DUAL_FILLED   = Color(0.6, 0.85, 1.0, 1.0)
const COLOR_LABEL_POST_FUSION   = Color(1.0, 0.9, 0.5, 1.0)

const POST_FUSION_FLASH_DURATION_MS: int = 600

var _absorb_available: bool = false
var _player: PlayerController3D
var _initial_max_hp: float = 0.0
var _handler: Node
var _slot_manager: Object = null  # MutationSlotManager (preferred) or fallback MutationSlot

var _prev_mutation_count: int = 0
var _absorb_feedback_until_ms: int = 0
var _post_fusion_flash_until_ms: int = 0
var _prev_both_filled: bool = false


func _sanitize_hud_scale(s: float) -> float:
	if is_nan(s) or is_inf(s):
		return 1.0
	if s <= 0.0:
		return 0.0
	return s


func _apply_hud_scale_to_direct_controls() -> void:
	var s: float = _hud_scale_value
	var sv: Vector2 = Vector2(s, s)
	for child in get_children():
		var c := child as Control
		if c == null:
			continue
		if c.name == "Hints":
			c.pivot_offset = Vector2.ZERO
			c.scale = Vector2.ONE
			c.offset_left = 0.0
			c.offset_top = 0.0
			c.offset_right = _HINTS_PACK_BASE_W * s
			c.offset_bottom = _HINTS_PACK_BASE_H * s
			for h in c.get_children():
				var hc := h as Control
				if hc == null:
					continue
				hc.pivot_offset = Vector2.ZERO
				hc.scale = sv
		else:
			c.pivot_offset = Vector2.ZERO
			c.scale = sv


func _ready() -> void:
	_apply_hud_scale_to_direct_controls()
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


func _get_fusion_active_label() -> Label:
	return get_node_or_null("FusionActiveLabel") as Label


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


func _update_fusion_display() -> void:
	if _player == null:
		return
	var label: Label = _get_fusion_active_label()
	if label != null:
		label.visible = _player.is_fusion_active()


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

	_update_fusion_display()

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

	# Compute both_filled for dual-slot color logic.
	var s0_disp: Object = _get_slot(0)
	var s1_disp: Object = _get_slot(1)
	var both_filled: bool = (
		s0_disp != null and s0_disp.has_method("is_filled") and s0_disp.is_filled()
		and s1_disp != null and s1_disp.has_method("is_filled") and s1_disp.is_filled()
	)

	# Detect post-fusion transition: both_filled true→false with fusion active.
	if _prev_both_filled and not both_filled and _player != null and _player.is_fusion_active():
		_post_fusion_flash_until_ms = now_ms + POST_FUSION_FLASH_DURATION_MS
	_prev_both_filled = both_filled

	var post_fusion_flash_active: bool = now_ms < _post_fusion_flash_until_ms

	# Drive dual-slot displays (DSM-4).
	_update_slot_display(1, _get_slot(0), both_filled, post_fusion_flash_active)
	_update_slot_display(2, _get_slot(1), both_filled, post_fusion_flash_active)

	# Legacy single-slot label (backward compat — shows slot A state or empty).
	var slot_label: Label = _get_mutation_slot_label()
	if slot_label != null:
		var s0: Object = _get_slot(0)
		var s0_filled: bool = s0 != null and s0.has_method("is_filled") and s0.is_filled()
		slot_label.visible = true
		if s0_filled:
			slot_label.text = "Mutation Slot: " + s0.get_active_mutation_id() + " active"
			slot_label.modulate = COLOR_LABEL_SINGLE_FILLED

		else:
			slot_label.text = "Mutation Slot: Empty"
			slot_label.modulate = COLOR_LABEL_EMPTY

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


func _update_slot_display(slot_number: int, slot: Object, both_filled: bool, post_fusion_flash_active: bool) -> void:
	var label: Label = get_node_or_null("MutationSlot" + str(slot_number) + "Label") as Label
	var icon: ColorRect = get_node_or_null("MutationIcon" + str(slot_number)) as ColorRect
	var filled: bool = slot != null and slot.has_method("is_filled") and slot.is_filled()
	var slot_id: String = ""
	if filled and slot.has_method("get_active_mutation_id"):
		slot_id = slot.get_active_mutation_id()

	# Color priority (highest wins): post_fusion_flash > dual_filled > single_filled > empty
	var icon_color: Color
	var label_color: Color
	if post_fusion_flash_active:
		icon_color = COLOR_SLOT_POST_FUSION
		label_color = COLOR_LABEL_POST_FUSION
	elif filled and both_filled:
		icon_color = COLOR_SLOT_DUAL_FILLED
		label_color = COLOR_LABEL_DUAL_FILLED
	elif filled and not both_filled:
		icon_color = COLOR_SLOT_SINGLE_FILLED
		label_color = COLOR_LABEL_SINGLE_FILLED
	else:
		icon_color = COLOR_SLOT_EMPTY
		label_color = COLOR_LABEL_EMPTY

	if label != null:
		label.visible = true
		if filled and slot_id != "":
			label.text = "Slot " + str(slot_number) + ": " + slot_id + " active"
		else:
			label.text = "Slot " + str(slot_number) + ": Empty"
		label.modulate = label_color

	if icon != null:
		icon.visible = true
		icon.color = icon_color
