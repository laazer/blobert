# carapace_husk_attack.gd
# Carapace family: long wind-up telegraph, X-axis charge, HADS hitbox, knockback, deceleration.

class_name CarapaceHuskAttack
extends Node

const _MIN_TELEGRAPH_WALL_SEC := 0.6

@export var attack_range: float = 6.0
@export var cooldown_seconds: float = 4.0
@export var telegraph_fallback_seconds: float = 0.35
@export var charge_speed: float = 16.0
@export var max_charge_range: float = 6.0
@export var damage_amount: float = 35.0
@export var knockback_strength: float = 22.0
@export var decel_factor: float = 0.82
@export var decel_velocity_epsilon: float = 0.15

var _enemy: EnemyInfection3D
var _cooldown_left: float = 0.0
var _attack_cycle_active: bool = false
var _charging: bool = false
var _decelerating: bool = false
var _charge_start_x: float = 0.0
var _charge_dir: float = 1.0
var _hitbox: Area3D


func _ready() -> void:
	process_physics_priority = -100
	var p: Node = get_parent()
	_enemy = p as EnemyInfection3D
	var hb_script: GDScript = load("res://scripts/enemies/enemy_attack_hitbox.gd") as GDScript
	_hitbox = hb_script.new() as Area3D
	_hitbox.name = "CarapaceChargeHitbox"
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(1.2, 1.4, 0.8)
	shape.shape = box
	_hitbox.add_child(shape)
	add_child(_hitbox)
	if not _hitbox.body_entered.is_connected(_on_hitbox_body_entered_carapace):
		_hitbox.body_entered.connect(_on_hitbox_body_entered_carapace)


func enemy_writes_velocity_x_this_frame() -> bool:
	return _charging or _decelerating


func _physics_process(delta: float) -> void:
	if _enemy == null or not is_instance_valid(_enemy):
		return
	if not is_inside_tree():
		return
	_cooldown_left = maxf(0.0, _cooldown_left - delta)
	if _decelerating:
		_process_decel(delta)
		return
	if _charging:
		_process_charge()
		return
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
	if ctrl != null and ctrl.begin_ranged_attack_telegraph(_MIN_TELEGRAPH_WALL_SEC):
		if not ctrl.ranged_attack_telegraph_finished.is_connected(_on_telegraph_finished):
			ctrl.ranged_attack_telegraph_finished.connect(_on_telegraph_finished, CONNECT_ONE_SHOT)
		return
	var t: SceneTreeTimer = get_tree().create_timer(maxf(telegraph_fallback_seconds, _MIN_TELEGRAPH_WALL_SEC))
	t.timeout.connect(_on_telegraph_finished, CONNECT_ONE_SHOT)


func _on_telegraph_finished() -> void:
	if not _attack_cycle_active:
		return
	_attack_cycle_active = false
	var player: Node3D = get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		_cooldown_left = cooldown_seconds
		return
	_charge_start_x = _enemy.global_position.x
	_charge_dir = signf(player.global_position.x - _enemy.global_position.x)
	if _charge_dir == 0.0:
		_charge_dir = 1.0
	_charging = true
	_hitbox.set("damage_amount", damage_amount)
	_hitbox.set("knockback_strength", knockback_strength)
	_sync_hitbox_position()
	_hitbox.set_hitbox_active(true)


func _sync_hitbox_position() -> void:
	var off := Vector3(_charge_dir * 0.65, 0.0, 0.0)
	_hitbox.global_position = _enemy.global_position + off


func _process_charge() -> void:
	var sc: int = _enemy.get_slide_collision_count()
	if sc > 0:
		for i in range(sc):
			var col: KinematicCollision3D = _enemy.get_slide_collision(i)
			if col == null:
				continue
			var n: Vector3 = col.get_normal()
			if absf(n.x) > 0.4:
				_end_charge_start_decel()
				return
	if absf(_enemy.global_position.x - _charge_start_x) >= max_charge_range:
		_end_charge_start_decel()
		return
	_enemy.velocity.x = _charge_dir * charge_speed
	_sync_hitbox_position()


func _on_hitbox_body_entered_carapace(body: Node3D) -> void:
	if not _charging:
		return
	if body is PlayerController3D:
		_end_charge_start_decel()


func _end_charge_start_decel() -> void:
	if not _charging:
		return
	_charging = false
	_hitbox.set_hitbox_active(false)
	_decelerating = true


func _process_decel(_delta: float) -> void:
	_enemy.velocity.x *= decel_factor
	if absf(_enemy.velocity.x) < decel_velocity_epsilon:
		_enemy.velocity.x = 0.0
		_decelerating = false
		_cooldown_left = cooldown_seconds
