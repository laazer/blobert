# claw_crawler_attack.gd
# Claw family: 2-hit melee combo with per-swipe telegraph + HADS hitbox re-arm.

class_name ClawCrawlerAttack
extends Node

@export var attack_range: float = 2.0
@export var cooldown_seconds: float = 1.2
@export var telegraph_fallback_seconds: float = 0.35
@export var combo_pause_seconds: float = 0.12
@export var swipe_hit_window_seconds: float = 0.18
@export var damage_per_hit: float = 7.0
@export var knockback_per_hit: float = 4.0

var _enemy: EnemyInfection3D
var _cooldown_left: float = 0.0
var _attack_cycle_active: bool = false
var _await_second_telegraph: bool = false
var _active_swipe: int = 0
var _swipe_window_left: float = 0.0
var _pause_left: float = 0.0
var _hitbox: Area3D


func _ready() -> void:
	var p: Node = get_parent()
	_enemy = p as EnemyInfection3D
	var hb_script: GDScript = load("res://scripts/enemies/enemy_attack_hitbox.gd") as GDScript
	_hitbox = hb_script.new() as Area3D
	_hitbox.name = "ClawSwipeHitbox"
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(1.0, 1.2, 0.7)
	shape.shape = box
	_hitbox.add_child(shape)
	add_child(_hitbox)
	if not _hitbox.body_entered.is_connected(_on_hitbox_body_claw):
		_hitbox.body_entered.connect(_on_hitbox_body_claw)


func _physics_process(delta: float) -> void:
	if _enemy == null or not is_instance_valid(_enemy):
		return
	if not is_inside_tree():
		return
	_cooldown_left = maxf(0.0, _cooldown_left - delta)
	if _active_swipe > 0:
		_swipe_window_left -= delta
		_sync_hitbox_position()
		if _swipe_window_left <= 0.0:
			_finish_swipe_window()
		return
	if _pause_left > 0.0:
		_pause_left -= delta
		if _pause_left <= 0.0:
			_begin_second_telegraph()
		return
	if _attack_cycle_active:
		return
	if _cooldown_left > 0.0:
		return
	var esm: EnemyStateMachine = _enemy.get_esm()
	if esm.get_state() == "dead":
		return
	var player: Node3D = get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return
	if _enemy.global_position.distance_to(player.global_position) > attack_range:
		return
	_begin_full_combo()


func _begin_full_combo() -> void:
	if _attack_cycle_active:
		return
	_attack_cycle_active = true
	_await_second_telegraph = false
	_begin_telegraph_for_current_swipe()


func _begin_second_telegraph() -> void:
	_await_second_telegraph = true
	_begin_telegraph_for_current_swipe()


func _begin_telegraph_for_current_swipe() -> void:
	var ctrl: EnemyAnimationController = _enemy.get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	if ctrl != null and ctrl.begin_ranged_attack_telegraph():
		if not ctrl.ranged_attack_telegraph_finished.is_connected(_on_telegraph_finished):
			ctrl.ranged_attack_telegraph_finished.connect(_on_telegraph_finished, CONNECT_ONE_SHOT)
		return
	var t: SceneTreeTimer = get_tree().create_timer(maxf(telegraph_fallback_seconds, 0.3))
	t.timeout.connect(_on_telegraph_finished, CONNECT_ONE_SHOT)


func _on_telegraph_finished() -> void:
	if _await_second_telegraph:
		_await_second_telegraph = false
		_open_swipe_window(2)
	else:
		_open_swipe_window(1)


func _open_swipe_window(swipe_idx: int) -> void:
	_active_swipe = swipe_idx
	_swipe_window_left = swipe_hit_window_seconds
	_hitbox.set("damage_amount", damage_per_hit)
	_hitbox.set("knockback_strength", knockback_per_hit)
	_sync_hitbox_position()
	_hitbox.set_hitbox_active(true)


func _sync_hitbox_position() -> void:
	var dir_x: float = 1.0
	var player: Node3D = get_tree().get_first_node_in_group("player") as Node3D
	if player != null:
		dir_x = signf(player.global_position.x - _enemy.global_position.x)
	if dir_x == 0.0:
		dir_x = 1.0
	_hitbox.global_position = _enemy.global_position + Vector3(dir_x * 0.55, 0.0, 0.0)


func _on_hitbox_body_claw(body: Node3D) -> void:
	if _active_swipe <= 0:
		return
	if body is PlayerController3D:
		_finish_swipe_window()


func _finish_swipe_window() -> void:
	if _active_swipe <= 0:
		return
	var which: int = _active_swipe
	_active_swipe = 0
	_swipe_window_left = 0.0
	_hitbox.set_hitbox_active(false)
	if which == 1:
		_pause_left = combo_pause_seconds
	elif which == 2:
		_attack_cycle_active = false
		_cooldown_left = cooldown_seconds
