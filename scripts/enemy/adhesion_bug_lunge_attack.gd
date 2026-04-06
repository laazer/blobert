# adhesion_bug_lunge_attack.gd
# Melee lunge + brief player root for adhesion family (mutation_drop == "adhesion").

class_name AdhesionBugLungeAttack
extends Node

@export var attack_range: float = 3.0
@export var cooldown_seconds: float = 2.0
@export var lunge_speed: float = 10.0
@export var lunge_duration_seconds: float = 0.28
@export var hit_radius_x: float = 0.95
@export var hit_radius_y: float = 1.4
@export var root_duration_seconds: float = 0.5
@export var telegraph_fallback_seconds: float = 0.3

var _enemy: EnemyInfection3D
var _cooldown_left: float = 0.0
var _attack_cycle_active: bool = false
var _lunging: bool = false
var _lunge_timer: float = 0.0
var _lunge_dir: float = 1.0
var _hit_registered: bool = false


func _ready() -> void:
	process_physics_priority = -100
	var p: Node = get_parent()
	_enemy = p as EnemyInfection3D


## Called from EnemyInfection3D._physics_process — child runs first (lower priority value).
func enemy_writes_velocity_x_this_frame() -> bool:
	return _lunging and _lunge_timer > 0.0


func _physics_process(delta: float) -> void:
	if _enemy == null or not is_instance_valid(_enemy):
		return
	if not is_inside_tree():
		return
	_cooldown_left = maxf(0.0, _cooldown_left - delta)
	if _lunging:
		_process_lunge(delta)
		return
	if _attack_cycle_active or _cooldown_left > 0.0:
		return
	var esm: EnemyStateMachine = _enemy.get_esm()
	if esm.get_state() == "dead":
		return
	var player: Node3D = get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return
	var dist: float = _enemy.global_position.distance_to(player.global_position)
	if dist > attack_range:
		return
	_begin_attack_cycle()


func _begin_attack_cycle() -> void:
	if _attack_cycle_active:
		return
	_attack_cycle_active = true
	var ctrl: EnemyAnimationController = _enemy.get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	if ctrl != null and ctrl.begin_ranged_attack_telegraph():
		if not ctrl.ranged_attack_telegraph_finished.is_connected(_on_telegraph_finished):
			ctrl.ranged_attack_telegraph_finished.connect(_on_telegraph_finished, CONNECT_ONE_SHOT)
		return
	var t: SceneTreeTimer = get_tree().create_timer(maxf(telegraph_fallback_seconds, 0.3))
	t.timeout.connect(_on_telegraph_finished, CONNECT_ONE_SHOT)


func _on_telegraph_finished() -> void:
	if not _attack_cycle_active:
		return
	_attack_cycle_active = false
	_start_lunge()


func _start_lunge() -> void:
	if _enemy == null or not is_instance_valid(_enemy):
		return
	var player: Node3D = get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return
	_lunge_dir = signf(player.global_position.x - _enemy.global_position.x)
	if _lunge_dir == 0.0:
		_lunge_dir = 1.0
	_lunge_timer = lunge_duration_seconds
	_lunging = true
	_hit_registered = false


func _process_lunge(delta: float) -> void:
	_lunge_timer -= delta
	_enemy.velocity.x = _lunge_dir * lunge_speed
	_try_register_hit()
	if _lunge_timer <= 0.0:
		_lunging = false
		_enemy.velocity.x = 0.0
		_cooldown_left = cooldown_seconds


func _try_register_hit() -> void:
	if _hit_registered:
		return
	var player: Node3D = get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return
	var dx: float = absf(_enemy.global_position.x - player.global_position.x)
	var dy: float = absf(_enemy.global_position.y - player.global_position.y)
	if dx > hit_radius_x or dy > hit_radius_y:
		return
	if player.has_method("apply_enemy_movement_root"):
		player.call("apply_enemy_movement_root", root_duration_seconds)
	_hit_registered = true
