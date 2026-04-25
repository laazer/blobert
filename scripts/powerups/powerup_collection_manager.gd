# PowerUpCollectionManager.gd
#
# Manages power-up spawning, collection, and effects in the game world.
# Attached to scene root; handles collision detection and effect application.
#
# Features:
#   - Spawns power-ups at designated locations
#   - Detects player proximity for collection
#   - Applies temporary/permanent effects
#   - Manages active power-up timers

class_name PowerUpCollectionManager
extends Node3D

@onready var player_controller: PlayerController3D = get_node_or_null("../PlayerController") as PlayerController3D

# Spawn configuration
@export var spawn_points: Array[Node3D] = []  # Nodes marked with "PowerUpSpawnPoint" tag
@export var spawn_interval: float = 10.0      # Seconds between spawns
@export var max_active_powerups: int = 3       # Maximum simultaneous power-ups

# Power-up type weights (for random spawning)
@export var health_boost_weight: float = 0.4
@export var speed_boost_weight: float = 0.3
@export var shield_weight: float = 0.2
@export var extra_slot_weight: float = 0.1

var _active_powerups: Array[PowerUp] = []
var _spawn_timer: Timer = null
var _collection_radius: float = 2.5

func _ready() -> void:
	_spawn_timer = Timer.new()
	_spawn_timer.wait_time = spawn_interval
	_spawn_timer.one_shot = false
	_spawn_timer.autostart = false
	add_child(_spawn_timer)

	_spawn_timer.timeout.connect(_on_spawn_timer_timeout)
	_spawn_timer.start()

func _physics_process(_delta: float) -> void:
	# Check for player proximity to active power-ups
	for powerup in _active_powerups.duplicate():  # Duplicate to avoid modification during iteration
		if not powerup.is_active:
			continue

		var distance := global_position.distance_to(powerup.spawn_position)

		if distance < _collection_radius and player_controller != null:
			_collect_power_up(powerup)

func spawn_random_power_up() -> void:
	if _active_powerups.size() >= max_active_powerups:
		return

	var power_up_type := _select_random_type()
	var duration := _get_duration_for_type(power_up_type)
	var value := _get_value_for_type(power_up_type)

	var spawn_point := _get_random_spawn_point()
	if spawn_point == null:
		push_warning("No spawn points available for power-up")
		return

	var powerup := PowerUp.new(power_up_type, duration, value)
	powerup.spawn_position = spawn_point.global_position
	powerup.is_active = true

	_active_powerups.append(powerup)

func _select_random_type() -> Type:
	var rand := randf()
	if rand < health_boost_weight:
		return PowerUp.Type.HEALTH_BOOST
	elif rand < health_boost_weight + speed_boost_weight:
		return PowerUp.Type.SPEED_BOOST
	elif rand < health_boost_weight + speed_boost_weight + shield_weight:
		return PowerUp.Type.SHIELD
	else:
		return PowerUp.Type.EXTRA_SLOT

func _get_duration_for_type(power_up_type: Type) -> float:
	match power_up_type:
		Type.SPEED_BOOST: return 15.0
		Type.SHIELD: return 10.0
		_: return 0.0

func _get_value_for_type(power_up_type: Type) -> float:
	match power_up_type:
		Type.HEALTH_BOOST: return 25.0
		Type.SPEED_BOOST: return 1.5  # 50% speed increase
		Type.SHIELD: return 1.0       # Full damage reduction
		Type.EXTRA_SLOT: return 1.0   # One additional slot

func _get_random_spawn_point() -> Node3D:
	if spawn_points.is_empty():
		return null

	var index := randi() % spawn_points.size()
	return spawn_points[index] as Node3D

func _collect_power_up(powerup: PowerUp) -> void:
	powerup.is_active = false
	_active_powerups.erase(powerup)

	if player_controller != null and powerup.power_up_type in [Type.SPEED_BOOST, Type.SHIELD]:
		# Apply effect immediately
		powerup.apply_effect(player_controller)

func _on_spawn_timer_timeout() -> void:
	spawn_random_power_up()
