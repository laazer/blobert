# enemy_status_effect_indicators.gd
#
# World-space status effect indicator badges for enemies. Displays active effects above health bar.
# Shows compact icons representing poisoned, slowed, stunned, weakened, infected states.
#
# Implemented as a Control node that reads status effects from enemy node and renders
# sorted, bounded icon list with overflow badge.
#
# Ticket: project_board/8_milestone_8_enemy_attacks/in_progress/02_enemy_status_effect_indicators.md
# Requirements:
#   - Renders status effect icons above health bar
#   - Deterministic sort order: stun > weaken > poison > slow > infection
#   - Max visible count with overflow badge
#   - Real-time updates on effect add/remove/refresh
#   - Fallback icon for unknown effects (no missing-resource errors)
#

extends Control

class_name EnemyStatusEffectIndicators

# Configuration (all @export, live-tunable)
@export var enabled: bool = true
@export var max_visible_count: int = 5
@export var icon_size: Vector2 = Vector2(32, 32)
@export var spacing: int = 4
@export var fallback_icon_path: String = "res://assets/ui/status_effects/unknown_effect.png"

# Constants for effect priorities
const EFFECT_PRIORITY_STUN: int = 0
const EFFECT_PRIORITY_WEAKEN: int = 1
const EFFECT_PRIORITY_POISON: int = 2
const EFFECT_PRIORITY_SLOW: int = 3
const EFFECT_PRIORITY_INFECTION: int = 4
const EFFECT_PRIORITY_UNKNOWN: int = 999  # Unknown effects get lowest priority

# Constants for EnemyBase.State enum values (from enemy_base.gd)
const ENEMY_STATE_WEAKENED: int = 1
const ENEMY_STATE_INFECTED: int = 2

# Internal state
var _enemy: Node = null
var _last_seen_effects: Array = []
var _icon_container: HBoxContainer = null
var _overflow_badge: Label = null
var _initialized_max_visible: int = -1

# Effect ID to priority mapping (lower = higher priority)
var _effect_priority: Dictionary = {
	"stun": EFFECT_PRIORITY_STUN,
	"weaken": EFFECT_PRIORITY_WEAKEN,
	"poison": EFFECT_PRIORITY_POISON,
	"slow": EFFECT_PRIORITY_SLOW,
	"infection": EFFECT_PRIORITY_INFECTION
}


func _ensure_initialized() -> void:
	"""Build icon slots synchronously (headless tests may call update before deferred _ready)."""
	if (
		_overflow_badge != null
		and is_instance_valid(_overflow_badge)
		and _initialized_max_visible == max_visible_count
	):
		return

	_initialized_max_visible = max_visible_count
	_overflow_badge = null
	_icon_container = null
	_last_seen_effects = []

	_icon_container = find_child("IconContainer", false, false) as HBoxContainer
	if _icon_container == null:
		_icon_container = HBoxContainer.new()
		_icon_container.name = "IconContainer"
		add_child(_icon_container)

	while _icon_container.get_child_count() > 0:
		var child := _icon_container.get_child(0)
		_icon_container.remove_child(child)
		child.free()

	for i in range(max_visible_count):
		var tex_rect := TextureRect.new()
		tex_rect.name = "Icon_%d" % i
		tex_rect.custom_minimum_size = icon_size
		tex_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tex_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
		tex_rect.visible = false
		_icon_container.add_child(tex_rect)

	_overflow_badge = Label.new()
	_overflow_badge.name = "OverflowBadge"
	_overflow_badge.visible = false
	_icon_container.add_child(_overflow_badge)

	visible = false


func _ready() -> void:
	_ensure_initialized()
	if _enemy != null:
		_process_update()


func _process(_delta: float) -> void:
	if not enabled or _enemy == null or not is_instance_valid(_enemy):
		return

	_process_update()


func update_from_enemy(enemy: Node) -> void:
	"""Set the enemy reference and initialize indicator state."""
	if enemy == null:
		_enemy = null
		visible = false
		return

	_enemy = enemy
	_ensure_initialized()
	_process_update()


func set_active_effects(effects: Array) -> void:
	"""Directly set active effects array for testing."""
	_ensure_initialized()
	_update_from_effects(effects)


# ---------------------------------------------------------------------------
# Private methods: status effect reading and caching
# ---------------------------------------------------------------------------

func _process_update() -> void:
	"""Each frame, read enemy effects and update if changed."""
	if _enemy == null:
		return

	var effects = _get_active_effects_from_enemy()
	_update_from_effects(effects)


func _get_active_effects_from_enemy() -> Array:
	"""Read active effects from enemy using multiple interface methods (priority order)."""
	if _enemy == null:
		return []

	# Priority 1: Getter method when it returns a non-empty array
	if _enemy.has_method("get_active_status_effects"):
		var method_result = _enemy.call("get_active_status_effects")
		if method_result is Array and method_result.size() > 0:
			return method_result

	# Priority 2: Node property (wins over meta when both are set)
	if "active_status_effects" in _enemy:
		var prop_result = _enemy.active_status_effects
		if prop_result is Array and prop_result.size() > 0:
			return prop_result

	# Priority 3: Meta
	if _enemy.has_meta("active_status_effects"):
		var meta_result = _enemy.get_meta("active_status_effects")
		if meta_result is Array and meta_result.size() > 0:
			return meta_result

	# Priority 4: Getter method (allow empty)
	if _enemy.has_method("get_active_status_effects"):
		var empty_method_result = _enemy.call("get_active_status_effects")
		if empty_method_result is Array:
			return empty_method_result

	# Priority 4: Fallback to EnemyBase state enum
	if _enemy.has_method("get_base_state"):
		var state = _enemy.call("get_base_state")
		var fallback_effects = []
		if state == ENEMY_STATE_WEAKENED:
			fallback_effects.append("weaken")
		if state == ENEMY_STATE_INFECTED:
			fallback_effects.append("infection")
		return fallback_effects

	return []


func _update_from_effects(effects: Array) -> void:
	"""Check if effects changed; if so, render indicators."""
	# Cache check: only re-render if array changed
	if effects == _last_seen_effects:
		return

	_last_seen_effects = effects.duplicate()
	_render_indicators()


# ---------------------------------------------------------------------------
# Private methods: rendering and UI updates
# ---------------------------------------------------------------------------

func _render_indicators() -> void:
	"""Rebuild UI based on current effects: sort, clamp, render icons, update badge."""
	if _icon_container == null:
		return

	# Ensure we have the right number of TextureRects for current max_visible_count
	_ensure_icon_rects()

	# Sort effects by priority (stun first)
	var sorted_effects = _sort_effects(_last_seen_effects)

	# Take only the first max_visible_count effects
	var visible_effects = sorted_effects.slice(0, mini(max_visible_count, sorted_effects.size()))

	# Update icon TextureRects
	var icon_children = _get_icon_rects()
	for i in range(icon_children.size()):
		if i < visible_effects.size():
			var tex_rect = icon_children[i]
			var effect_id = visible_effects[i]
			var icon = _load_icon(effect_id)
			tex_rect.texture = icon
			tex_rect.visible = true
		else:
			icon_children[i].visible = false

	# Update overflow badge
	_update_overflow_badge(sorted_effects.size())

	# Show container only if any effects active
	visible = sorted_effects.size() > 0


func _ensure_icon_rects() -> void:
	"""Ensure we have exactly max_visible_count TextureRects for rendering."""
	if _icon_container == null:
		return

	var current_rects = _get_icon_rects()

	# If we have too many, remove extras
	if current_rects.size() > max_visible_count:
		for i in range(max_visible_count, current_rects.size()):
			current_rects[i].queue_free()

	# If we have too few, create more
	elif current_rects.size() < max_visible_count:
		for i in range(current_rects.size(), max_visible_count):
			var tex_rect = TextureRect.new()
			tex_rect.name = "Icon_%d" % i
			tex_rect.custom_minimum_size = icon_size
			tex_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tex_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
			tex_rect.visible = false
			_icon_container.add_child(tex_rect)


func _get_icon_rects() -> Array:
	"""Get all TextureRect children of icon container (for rendering)."""
	var rects = []
	if _icon_container == null:
		return rects

	for child in _icon_container.get_children():
		if child is TextureRect:
			rects.append(child)
	return rects


func _sort_effects(effects: Array) -> Array:
	"""Sort effects by priority (stun > weaken > poison > slow > infection); stable for ties."""
	var indexed: Array = []
	for i in range(effects.size()):
		indexed.append({"id": effects[i], "idx": i})
	indexed.sort_custom(func(a, b):
		var priority_a := _get_effect_priority(a.id)
		var priority_b := _get_effect_priority(b.id)
		if priority_a != priority_b:
			return priority_a < priority_b
		return a.idx < b.idx
	)
	var result: Array = []
	for entry in indexed:
		result.append(entry.id)
	return result


func _get_effect_priority(effect_id: Variant) -> int:
	"""Get numeric priority for effect ID (lower = higher priority, renders first)."""
	var id_str = str(effect_id)
	if _effect_priority.has(id_str):
		return _effect_priority[id_str]
	return EFFECT_PRIORITY_UNKNOWN  # Unknown effects get lowest priority (render last)


func _load_icon(effect_id: Variant) -> Texture2D:
	"""Load icon texture for effect ID with fallback to unknown_effect.png."""
	var id_str = str(effect_id).to_lower().strip_edges()

	# Validate effect_id format (alphanumeric + underscore only)
	if not id_str.is_valid_identifier():
		return _get_fallback_icon()

	var canonical_path = "res://assets/ui/status_effects/%s.png" % id_str

	# Try canonical path first
	if ResourceLoader.exists(canonical_path):
		return load(canonical_path) as Texture2D

	# Fallback to unknown_effect.png
	return _get_fallback_icon()


func _get_fallback_icon() -> Texture2D:
	"""Get fallback icon texture, with PlaceholderTexture2D as last resort."""
	if ResourceLoader.exists(fallback_icon_path):
		return load(fallback_icon_path) as Texture2D

	# Last resort: return placeholder texture (never return null)
	return PlaceholderTexture2D.new()


func _update_overflow_badge(total_effects: int) -> void:
	"""Show/hide overflow badge. If hidden effects, show "+N"."""
	if _overflow_badge == null:
		return

	if total_effects > max_visible_count:
		var hidden_count = total_effects - max_visible_count
		_overflow_badge.text = "+%d" % hidden_count
		_overflow_badge.visible = true
	else:
		_overflow_badge.visible = false
