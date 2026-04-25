# EnemyAIController.gd
#
# Behavior orchestration for enemy AI: patrol, chase, and attack states.
# Attached to enemies as a child node; reads/writes EnemyBase state.
#
# State machine:
#   NORMAL → Patrol around area, random direction changes
#   WEAKENED → Slower movement, reduced aggression
#   INFECTED → Immobilized, preparing mutation drop
#
# Detection logic:
#   Player within detection_range + line_of_sight → switch to CHASE
#   No player detected for patrol_timer seconds → random direction change

class_name EnemyAIController
extends Node3D

@onready var enemy_base: CharacterBody3D = get_parent() as CharacterBody3D
@onready var attack_hitbox: Area3D = $AttackHitbox
@onready var animation_controller: Node = $EnemyAnimationController

# Detection parameters
@export var detection_range: float = 5.0
@export var patrol_range: Vector2 = Vector2(8.0, 0.0)  # X/Z bounds from spawn point
@export var chase_speed_multiplier: float = 1.3
@export var patrol_speed_multiplier: float = 0.7

# State timers
@onready var patrol_timer: Timer = $PatrolTimer
@onready var attack_cooldown_timer: Timer = $AttackCooldownTimer

var _patrol_direction: Vector2 = Vector2.RIGHT
var _last_known_player_position: Vector3 = Vector3.ZERO
var _is_chasing: bool = false

# Patrol state machine
enum PatrolState { IDLE, MOVING_LEFT, MOVING_RIGHT }
var _current_patrol_state: PatrolState = PatrolState.IDLE

func _ready() -> void:
	patrol_timer.timeout.connect(_on_patrol_timeout)
	attack_cooldown_timer.timeout.connect(_on_attack_cooldown_finished)
	_reset_patrol()

	# Initialize attack hitbox
	if attack_hitbox:
		attack_hitbox.monitoring = false
		attack_hitbox.set_hitbox_active(false)

func _physics_process(delta: float) -> void:
	var state := enemy_base.get_base_state()

	match state:
		EnemyBase.State.NORMAL:
			_handle_normal_state(delta)
		EnemyBase.State.WEAKENED:
			_handle_weakened_state(delta)
		EnemyBase.State.INFECTED:
			_handle_infected_state(delta)

func _handle_normal_state(delta: float) -> void:
	if _is_chasing:
		_chase_player(delta)
	else:
		_patrol(delta)

func _patrol(delta: float) -> void:
	match _current_patrol_state:
		PatrolState.IDLE:
			await get_tree().create_timer(1.0).timeout
			_current_patrol_state = PatrolState.MOVING_LEFT if randf() > 0.5 else PatrolState.MOVING_RIGHT

		PatrolState.MOVING_LEFT:
			_move_in_direction(-_patrol_direction, delta)
			if _has_reached_boundary():
				_current_patrol_state = PatrolState.IDLE
				await get_tree().create_timer(0.5).timeout
				_patrol_direction = -_patrol_direction

		PatrolState.MOVING_RIGHT:
			_move_in_direction(_patrol_direction, delta)
			if _has_reached_boundary():
				_current_patrol_state = PatrolState.IDLE

func _move_in_direction(direction: Vector2, delta: float) -> void:
	var speed := enemy_base.velocity.length() * patrol_speed_multiplier if enemy_base.velocity.length() > 0.1 else 2.0
	var move_vec := Vector3(direction.x, 0.0, direction.y) * speed * delta
	enemy_base.global_position += move_vec

func _has_reached_boundary() -> bool:
	var spawn_pos := _get_spawn_position()
	var current_x := enemy_base.global_position.x - spawn_pos.x

	return abs(current_x) > patrol_range.x

func _chase_player(delta: float) -> void:
	if not _is_player_in_range():
		_is_chasing = false
		_patrol_timer.start()
		return

	var player := _get_player_position()
	var direction := (player - enemy_base.global_position).normalized()

	# Move toward player
	var speed := 3.0 * chase_speed_multiplier
	enemy_base.velocity.x = direction.x * speed
	enemy_base.velocity.z = direction.z * speed
	enemy_base.move_and_slide()

	# Face player
	if abs(direction.x) > 0.1:
		rotation.y = -PI / 2 if direction.x < 0 else PI / 2

	# Try to attack when close enough
	var distance := enemy_base.global_position.distance_to(player)
	if distance < 2.0 and not _is_attack_cooldown_active():
		_trigger_attack()

func _get_player_position() -> Vector3:
	var scene_tree := get_tree()
	if scene_tree == null:
		return Vector3.ZERO

	for node in scene_tree.get_nodes_in_group("player"):
		if node is PlayerController3D:
			return node.global_position

	return _last_known_player_position

func _is_player_in_range() -> bool:
	var player_pos := _get_player_position()
	var distance := enemy_base.global_position.distance_to(player_pos)

	return distance <= detection_range and _has_line_of_sight(player_pos)

func _has_line_of_sight(target: Vector3) -> bool:
	var space_state := get_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(
		enemy_base.global_position,
		target
	)
	query.exclude = [enemy_base]

	var result := space_state.intersect_ray(query)
	return result.is_empty()

func _trigger_attack() -> void:
	if attack_hitbox:
		attack_hitbox.set_hitbox_active(true)
		attack_cooldown_timer.start(2.0)  # 2 second cooldown

		# Trigger animation
		if animation_controller and animation_controller.has_method("play_attack"):
			animation_controller.call("play_attack")

func _is_attack_cooldown_active() -> bool:
	return attack_cooldown_timer.is_stopped() == false

func _handle_weakened_state(_delta: float) -> void:
	# Weakened enemies move slower and have reduced detection range
	detection_range *= 0.5

	if not _is_chasing and _is_player_in_range():
		_is_chasing = true

	if _is_chasing:
		var player := _get_player_position()
		var direction := (player - enemy_base.global_position).normalized()

		var speed := 1.5 * chase_speed_multiplier
		enemy_base.velocity.x = direction.x * speed
		enemy_base.velocity.z = direction.z * speed
		enemy_base.move_and_slide()

func _handle_infected_state(_delta: float) -> void:
	# Infected enemies are immobilized and prepare mutation drop
	enemy_base.velocity = Vector3.ZERO

	if attack_hitbox:
		attack_hitbox.set_hitbox_active(false)

	# Trigger mutation drop after delay (handled by infection system)

func _reset_patrol() -> void:
	_patrol_direction = Vector2.RIGHT if randf() > 0.5 else Vector2.LEFT
	_current_patrol_state = PatrolState.IDLE
	patrol_timer.start(rand_range(2.0, 5.0))

func _on_patrol_timeout() -> void:
	_reset_patrol()

func _on_attack_cooldown_finished() -> void:
	if attack_hitbox:
		attack_hitbox.set_hitbox_active(false)

func _get_spawn_position() -> Vector3:
	return enemy_base.global_position

# Called when player deals damage to trigger weakened state
func on_player_damage_taken(_damage: float) -> void:
	var current_state := enemy_base.get_base_state()
	if current_state == EnemyBase.State.NORMAL:
		enemy_base.set_base_state(EnemyBase.State.WEAKENED)
		detection_range *= 0.5

# Called when chunk infects the enemy
func on_chunk_infect(chunk_index: int, mutation_name: String) -> void:
	var current_state := enemy_base.get_base_state()
	if current_state == EnemyBase.State.WEAKENED:
		enemy_base.set_base_state(EnemyBase.State.INFECTED)
		# Mutation drop will be handled by infection system
