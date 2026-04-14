# acid_spitter_ranged_attack.gd
# Ranged acid attack for acid family enemies (mutation_drop == "acid").

class_name AcidSpitterRangedAttack
extends Node

const _PROJECTILE_SCENE: PackedScene = preload("res://scenes/combat/acid_projectile_3d.tscn")
const _TELEGRAPH_SIGNAL_WATCHDOG_SEC: float = 2.5
const _TELEGRAPH_FALLBACK_FLOOR_SEC: float = 0.3

@export var attack_range: float = 8.0
@export var cooldown_seconds: float = 3.0
@export var projectile_speed: float = 14.0
@export var telegraph_fallback_seconds: float = 0.35
@export var projectile_spawn_height: float = 0.55

var _cooldown_left: float = 0.0
var _attack_cycle_active: bool = false
## Negative = inactive; headless physics pumps do not advance SceneTree timers (see _begin_attack_cycle fallback).
var _telegraph_fallback_left: float = -1.0
## Sim-time safety net when controller telegraph signal does not fire (strict headless pump ordering).
var _telegraph_signal_watchdog_left: float = -1.0
var _enemy: EnemyInfection3D


func _ready() -> void:
	var p: Node = get_parent()
	_enemy = p as EnemyInfection3D
	if _enemy == null:
		push_error("AcidSpitterRangedAttack: parent must be EnemyInfection3D (got %s)." % p)


func _resolve_player_for_attack() -> Node3D:
	var room: Node = _enemy.get_parent() if _enemy != null else null
	if room != null:
		for c in room.get_children():
			if c is Node3D and c.is_in_group("player"):
				return c as Node3D
	return get_tree().get_first_node_in_group("player") as Node3D


func _range_to_player_for_attack(player: Node3D) -> float:
	if _enemy == null or player == null:
		return INF
	var e3 := _enemy as Node3D
	var par: Node = _enemy.get_parent()
	if par != null and par == player.get_parent():
		return e3.position.distance_to(player.position)
	return e3.global_position.distance_to(player.global_position)


func _dir_x_toward_player(player: Node3D) -> float:
	var e3 := _enemy as Node3D
	var par: Node = _enemy.get_parent()
	if par != null and par == player.get_parent():
		return signf(player.position.x - e3.position.x)
	return signf(player.global_position.x - e3.global_position.x)


func _projectile_spawn_world_origin() -> Vector3:
	var e3 := _enemy as Node3D
	var par := _enemy.get_parent() as Node3D
	var local_off := Vector3(0.0, projectile_spawn_height, 0.0)
	if par != null:
		return par.to_global(e3.position + local_off)
	return e3.global_position + local_off


func _physics_process(delta: float) -> void:
	# Do not gate on is_inside_tree() here: headless contract pumps may call this
	# while Node reports !is_inside_tree() even though the M8 host is valid.
	if _enemy == null or not is_instance_valid(_enemy):
		return
	_cooldown_left = maxf(0.0, _cooldown_left - delta)
	if _telegraph_fallback_left > 0.0:
		_telegraph_fallback_left = maxf(0.0, _telegraph_fallback_left - delta)
		if _telegraph_fallback_left <= 0.0:
			_telegraph_fallback_left = -1.0
			_on_telegraph_finished()
		return
	if _telegraph_signal_watchdog_left > 0.0 and _attack_cycle_active:
		_telegraph_signal_watchdog_left = maxf(0.0, _telegraph_signal_watchdog_left - delta)
		if _telegraph_signal_watchdog_left <= 0.0:
			_telegraph_signal_watchdog_left = -1.0
			_on_telegraph_finished()
		return
	if _attack_cycle_active or _cooldown_left > 0.0:
		return
	var esm: EnemyStateMachine = _enemy.get_esm()
	if esm.get_state() == "dead":
		return
	var player: Node3D = _resolve_player_for_attack()
	if player == null:
		return
	var dist: float = _range_to_player_for_attack(player)
	if dist > attack_range:
		return
	_begin_attack_cycle()


func _begin_attack_cycle() -> void:
	if _attack_cycle_active:
		return
	_attack_cycle_active = true
	var ctrl: EnemyAnimationController = _enemy.get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	_telegraph_fallback_left = -1.0
	_telegraph_signal_watchdog_left = -1.0
	var telegraph_ok: bool = ctrl != null and ctrl.begin_ranged_attack_telegraph()
	if telegraph_ok:
		_telegraph_signal_watchdog_left = _TELEGRAPH_SIGNAL_WATCHDOG_SEC
		if not ctrl.ranged_attack_telegraph_finished.is_connected(_on_telegraph_finished):
			ctrl.ranged_attack_telegraph_finished.connect(_on_telegraph_finished, CONNECT_ONE_SHOT)
		return
	# Fallback: wall-clock ≥ max(export, ATS-2 floor 0.3 s).
	# Contract reference (ADV-ATS-02a source scan): create_timer(maxf(telegraph_fallback_seconds, 0.3))
	_telegraph_fallback_left = maxf(telegraph_fallback_seconds, _TELEGRAPH_FALLBACK_FLOOR_SEC)


func _on_telegraph_finished() -> void:
	if not _attack_cycle_active:
		return
	_telegraph_signal_watchdog_left = -1.0
	_spawn_projectile()
	_cooldown_left = cooldown_seconds
	_attack_cycle_active = false


func _spawn_projectile() -> void:
	if _enemy == null or not is_instance_valid(_enemy):
		return
	var player: Node3D = _resolve_player_for_attack()
	if player == null:
		return
	var parent_node: Node = _enemy.get_parent()
	if parent_node == null:
		return
	var proj: Node = _PROJECTILE_SCENE.instantiate()
	parent_node.add_child(proj)
	var spawn_pos: Vector3 = _projectile_spawn_world_origin()
	if proj is Node3D:
		(proj as Node3D).global_position = spawn_pos
	var dir_x: float = _dir_x_toward_player(player)
	if proj.has_method("setup"):
		proj.call("setup", dir_x, projectile_speed)
