## Verification-only: oscillates parent EnemyInfection3D on X so adhesion root (slow 0)
## is visible when the blob stops moving. Uses position nudge because the enemy
## script clears velocity.x each physics frame.

class_name M11EnemyPatrolProbe
extends Node

const _PATROL_SPEED: float = 2.5
const _X_MIN: float = -1.0
const _X_MAX: float = 5.0
const _ROOTED_SPEED_THRESHOLD: float = 0.01

var _dir: float = 1.0


func _process(delta: float) -> void:
	var enemy: CharacterBody3D = get_parent() as CharacterBody3D
	if enemy == null or not is_instance_valid(enemy):
		return
	if enemy.has_method("is_dead") and enemy.call("is_dead"):
		return
	var speed_mult: float = 1.0
	if enemy.has_method("get_speed_multiplier"):
		speed_mult = enemy.call("get_speed_multiplier") as float
	else:
		var tracker: Node = enemy.get_node_or_null("EnemyEffectTracker")
		if tracker != null and tracker.has_method("get_speed_multiplier"):
			speed_mult = tracker.call("get_speed_multiplier") as float
	if speed_mult <= _ROOTED_SPEED_THRESHOLD:
		return
	var pos: Vector3 = enemy.global_position
	pos.x += _PATROL_SPEED * _dir * speed_mult * delta
	enemy.global_position = pos
	if pos.x >= _X_MAX:
		_dir = -1.0
	elif pos.x <= _X_MIN:
		_dir = 1.0
