class_name CameraFollow
extends Camera2D

# Smoothing (SPEC-40)
@export var smoothing_enabled: bool = true
@export var smoothing_speed: float = 5.0

# Drag margins / dead zone (SPEC-41)
@export var drag_horizontal: bool = true
@export var drag_vertical: bool = false
@export var follow_drag_left_margin: float = 0.2
@export var follow_drag_right_margin: float = 0.2
@export var follow_drag_top_margin: float = 0.2
@export var follow_drag_bottom_margin: float = 0.2

# Level bounds (SPEC-42)
@export var follow_limit_left: int = -10000000
@export var follow_limit_right: int = 10000000
@export var follow_limit_top: int = -10000000
@export var follow_limit_bottom: int = 10000000


func _ready() -> void:
	position_smoothing_enabled = smoothing_enabled
	position_smoothing_speed = smoothing_speed
	drag_horizontal_enabled = drag_horizontal
	drag_vertical_enabled = drag_vertical
	drag_left_margin = follow_drag_left_margin
	drag_right_margin = follow_drag_right_margin
	drag_top_margin = follow_drag_top_margin
	drag_bottom_margin = follow_drag_bottom_margin
	limit_left = follow_limit_left
	limit_right = follow_limit_right
	limit_top = follow_limit_top
	limit_bottom = follow_limit_bottom
