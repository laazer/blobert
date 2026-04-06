# enemy_attack_hitbox.gd
#
# M8 melee-style attack overlap: Area3D that damages the player once per activation.
class_name EnemyAttackHitbox
extends Area3D

@export var damage_amount: float = 10.0
## Impulse scale along (player - self) in the X/Y plane (Z ignored).
@export var knockback_strength: float = 8.0

var _armed: bool = false


func _ready() -> void:
	monitoring = false
	collision_mask = 1
	if not body_entered.is_connected(_on_body_entered):
		body_entered.connect(_on_body_entered)


func set_hitbox_active(active: bool) -> void:
	if active:
		_armed = true
		monitoring = true
	else:
		_armed = false
		monitoring = false


func is_hitbox_active() -> bool:
	return monitoring and _armed


func _on_body_entered(body: Node3D) -> void:
	if body is PlayerController3D:
		_apply_hit(body as PlayerController3D)


func _apply_hit(player: PlayerController3D) -> void:
	if not _armed or not monitoring:
		return
	var kb := _compute_knockback(player)
	player.take_damage(damage_amount, kb)
	_armed = false
	monitoring = false


func _compute_knockback(player: PlayerController3D) -> Vector3:
	var delta_3 := player.global_position - global_position
	var delta := Vector3(delta_3.x, delta_3.y, 0.0)
	if delta.length_squared() < 1e-8:
		delta = Vector3(1.0, 0.0, 0.0)
	else:
		delta = delta.normalized()
	return delta * knockback_strength
