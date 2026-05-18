# enemy_health_bar_3d.gd
#
# World-space 3D health bar for enemies. Floats above enemy head and shows HP ratio.
# Updates in real-time on damage, hides when at full health after timeout.
#
# Implemented as a Control node that projects enemy 3D world position to screen space
# for 2D rendering. Updates position each frame to track enemy movement and camera changes.
#
# Ticket: project_board/8_milestone_8_enemy_attacks/in_progress/01_enemy_floating_health_bar.md
# Requirements:
#   - Tracks enemy HP in real time
#   - Hidden by default; shown when damaged
#   - Billboard behavior (always faces camera)
#   - Positioned above enemy
#   - Cleans up on enemy death/despawn
#   - Feature toggle for performance testing
#

extends Control

class_name EnemyHealthBar3D

# Configuration
@export var enabled: bool = true
@export var height_offset: float = 2.5  # Y offset above enemy
@export var visibility_timeout: float = 3.0  # Seconds to hide bar after recovery
@export var scale_size: float = 1.0

# UI dimensions (tuning constants)
const PROGRESS_BAR_MAX_VALUE: float = 100.0
const PROGRESS_BAR_WIDTH: int = 100
const PROGRESS_BAR_HEIGHT: int = 20

# Visibility threshold (ratio of max_hp at which auto-hide triggers)
const FULL_HEALTH_RATIO_THRESHOLD: float = 0.99

# Internal state
var _enemy: Node = null
var _progress_bar: ProgressBar = null
var _visibility_timer: Timer = null
var _camera: Camera3D = null
var _original_position: Vector2 = Vector2.ZERO
var _last_hp_ratio: float = 1.0
var _is_damaged: bool = false


func _ready() -> void:
	# Check debug flag
	if ProjectSettings.has_setting("debug/enable_enemy_health_bars"):
		enabled = ProjectSettings.get_setting("debug/enable_enemy_health_bars")

	# Find or create ProgressBar
	_progress_bar = find_child("ProgressBar", true, false) as ProgressBar
	if _progress_bar == null:
		_progress_bar = ProgressBar.new()
		_progress_bar.name = "ProgressBar"
		add_child(_progress_bar)

	# Configure ProgressBar
	_progress_bar.min_value = 0.0
	_progress_bar.max_value = PROGRESS_BAR_MAX_VALUE
	_progress_bar.value = PROGRESS_BAR_MAX_VALUE
	_progress_bar.show_percentage = false
	_progress_bar.custom_minimum_size = Vector2(PROGRESS_BAR_WIDTH, PROGRESS_BAR_HEIGHT)

	# Setup visibility timer
	_visibility_timer = find_child("HideTimer", true, false) as Timer
	if _visibility_timer == null:
		_visibility_timer = Timer.new()
		_visibility_timer.name = "HideTimer"
		add_child(_visibility_timer)

	# Connect timeout signal if not already connected
	if not _visibility_timer.timeout.is_connected(Callable(self, "_on_visibility_timeout")):
		_visibility_timer.timeout.connect(Callable(self, "_on_visibility_timeout"))

	# Start hidden
	visible = false
	_is_damaged = false

	# Store original position for offset calculations
	_original_position = global_position


func _exit_tree() -> void:
	# Clean up when bar is removed from scene
	if _visibility_timer != null and _visibility_timer.timeout.is_connected(Callable(self, "_on_visibility_timeout")):
		_visibility_timer.timeout.disconnect(Callable(self, "_on_visibility_timeout"))


func _process(_delta: float) -> void:
	if not enabled or _enemy == null or not is_instance_valid(_enemy):
		return

	# Update position to follow enemy and face camera
	_update_position_and_rotation()


func _update_position_and_rotation() -> void:
	# Update position to be above enemy in 3D space
	_camera = get_viewport().get_camera_3d()
	if _camera == null or not (_enemy is Node3D):
		return

	var enemy_3d = _enemy as Node3D
	var enemy_world_pos = enemy_3d.global_position + Vector3(0, height_offset, 0)

	# Project 3D position to 2D screen space
	var screen_pos = _camera.unproject_position(enemy_world_pos)
	global_position = screen_pos - size / 2.0  # Center on projected position


func update_from_enemy(enemy: Node) -> void:
	# Set the enemy reference and initialize bar state
	if enemy == null:
		_enemy = null
		return

	_enemy = enemy

	# Update bar position to be above enemy
	if enemy is Node3D and is_inside_tree():
		_update_position_and_rotation()

	# Get current HP ratio
	var current_hp = _get_enemy_hp()
	var max_hp = _get_enemy_max_hp()
	_update_health_display(current_hp, max_hp)


func on_enemy_damaged(damage_amount: float = 1.0) -> void:
	# Called when enemy takes damage
	if _enemy == null or not is_instance_valid(_enemy) or not enabled:
		return

	# Show the bar if it was hidden
	if not _is_damaged:
		_is_damaged = true
		visible = true

	# Cancel any pending hide timeout
	if _visibility_timer != null and not _visibility_timer.is_stopped():
		_visibility_timer.stop()

	# Update display
	var current_hp = _get_enemy_hp()
	var max_hp = _get_enemy_max_hp()
	_update_health_display(current_hp, max_hp)


func on_enemy_healed(heal_amount: float = 1.0) -> void:
	# Called when enemy heals
	if _enemy == null or not is_instance_valid(_enemy) or not enabled:
		return

	var current_hp = _get_enemy_hp()
	var max_hp = _get_enemy_max_hp()
	_update_health_display(current_hp, max_hp)


func on_enemy_died() -> void:
	# Called when enemy dies; prepare for cleanup
	if _visibility_timer != null and not _visibility_timer.is_stopped():
		_visibility_timer.stop()

	# Hide the bar immediately
	visible = false
	_is_damaged = false

	# Disconnect from enemy
	_enemy = null


func _update_health_display(current_hp: float, max_hp: float) -> void:
	# Update progress bar value based on HP ratio
	if _progress_bar == null:
		return

	# Safety: prevent division by zero
	if max_hp <= 0:
		_progress_bar.value = 0.0
		_last_hp_ratio = 0.0
		return

	# Calculate HP ratio and clamp to [0, 1]
	var hp_ratio = clamp(current_hp / max_hp, 0.0, 1.0)
	_last_hp_ratio = hp_ratio

	# Set progress bar to reflect percentage (0-100)
	_progress_bar.value = hp_ratio * PROGRESS_BAR_MAX_VALUE

	# Auto-hide if back at full health
	if hp_ratio >= FULL_HEALTH_RATIO_THRESHOLD:  # Account for floating point precision
		if _is_damaged:
			_start_visibility_timeout()


func _start_visibility_timeout() -> void:
	# Start timer to hide bar after timeout
	if _visibility_timer == null or not is_instance_valid(_visibility_timer):
		return

	# Only start timer if it's in the scene tree
	if not _visibility_timer.is_inside_tree():
		return

	_visibility_timer.wait_time = visibility_timeout
	_visibility_timer.one_shot = true
	_visibility_timer.start()


func _on_visibility_timeout() -> void:
	# Hide the bar after timeout (if still at full health)
	var current_hp = _get_enemy_hp()
	var max_hp = _get_enemy_max_hp()

	if max_hp > 0 and current_hp / max_hp >= FULL_HEALTH_RATIO_THRESHOLD:
		visible = false
		_is_damaged = false


func _get_enemy_hp() -> float:
	# Get current HP from enemy
	if _enemy == null or not is_instance_valid(_enemy):
		return 0.0

	# Try meta first
	if _enemy.has_meta("current_hp"):
		return _enemy.get_meta("current_hp") as float

	# Try property
	if _enemy.has_method("get_current_hp"):
		return _enemy.call("get_current_hp") as float

	if "current_hp" in _enemy:
		return _enemy.current_hp as float

	return 0.0


func _get_enemy_max_hp() -> float:
	# Get max HP from enemy
	if _enemy == null or not is_instance_valid(_enemy):
		return 1.0

	# Try meta first
	if _enemy.has_meta("max_hp"):
		return _enemy.get_meta("max_hp") as float

	# Try property
	if _enemy.has_method("get_max_hp"):
		return _enemy.call("get_max_hp") as float

	if "max_hp" in _enemy:
		return _enemy.max_hp as float

	return 1.0


func connect_to_enemy(damage_signal: Signal) -> void:
	# Connect to enemy damage signal for real-time updates
	if damage_signal.is_null():
		return

	# Avoid duplicate connections
	if not damage_signal.is_connected(Callable(self, "on_enemy_damaged")):
		damage_signal.connect(Callable(self, "on_enemy_damaged"))
