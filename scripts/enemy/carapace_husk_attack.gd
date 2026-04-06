# carapace_husk_attack.gd
# Minimal telegraph + stub active phase for carapace family (mutation_drop == "carapace").
# Future hitbox wiring: hitbox_and_damage_system ticket.

class_name CarapaceHuskAttack
extends Node

@export var attack_range: float = 6.0
@export var cooldown_seconds: float = 2.5
@export var telegraph_fallback_seconds: float = 0.35

var _enemy: EnemyInfection3D
var _cooldown_left: float = 0.0
var _attack_cycle_active: bool = false


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
	if _enemy.global_position.distance_to(player.global_position) > attack_range:
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
	_cooldown_left = cooldown_seconds
