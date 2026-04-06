# acid_spitter_ranged_attack.gd
# Ranged acid attack for acid family enemies (mutation_drop == "acid").

class_name AcidSpitterRangedAttack
extends Node

const _PROJECTILE_SCENE: PackedScene = preload("res://scenes/combat/acid_projectile_3d.tscn")

@export var attack_range: float = 8.0
@export var cooldown_seconds: float = 3.0
@export var projectile_speed: float = 14.0
@export var telegraph_fallback_seconds: float = 0.35
@export var projectile_spawn_height: float = 0.55

var _cooldown_left: float = 0.0
var _attack_cycle_active: bool = false
var _enemy: EnemyInfection3D


func _ready() -> void:
	var p: Node = get_parent()
	_enemy = p as EnemyInfection3D


func _physics_process(delta: float) -> void:
	if _enemy == null or not is_instance_valid(_enemy):
		return
	if not is_inside_tree():
		return
	_cooldown_left = maxf(0.0, _cooldown_left - delta)
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
	_attack_cycle_active = true
	var ctrl: EnemyAnimationController = _enemy.get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	if ctrl != null and ctrl.begin_ranged_attack_telegraph():
		if not ctrl.ranged_attack_telegraph_finished.is_connected(_on_telegraph_finished):
			ctrl.ranged_attack_telegraph_finished.connect(_on_telegraph_finished, CONNECT_ONE_SHOT)
		return
	var t: SceneTreeTimer = get_tree().create_timer(telegraph_fallback_seconds)
	t.timeout.connect(_on_telegraph_finished, CONNECT_ONE_SHOT)


func _on_telegraph_finished() -> void:
	_spawn_projectile()
	_cooldown_left = cooldown_seconds
	_attack_cycle_active = false


func _spawn_projectile() -> void:
	if _enemy == null or not is_instance_valid(_enemy):
		return
	var player: Node3D = get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return
	var parent_node: Node = _enemy.get_parent()
	if parent_node == null:
		return
	var proj: Node = _PROJECTILE_SCENE.instantiate()
	parent_node.add_child(proj)
	var spawn_pos: Vector3 = _enemy.global_position + Vector3(0.0, projectile_spawn_height, 0.0)
	if proj is Node3D:
		(proj as Node3D).global_position = spawn_pos
	var dir_x: float = signf(player.global_position.x - _enemy.global_position.x)
	if proj.has_method("setup"):
		proj.call("setup", dir_x, projectile_speed)
