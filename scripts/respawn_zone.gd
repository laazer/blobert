# respawn_zone.gd
# DeadZone-style Area3D: when a body in group "player" enters, reset to spawn_point.

extends Area3D

@export var spawn_point: NodePath = NodePath()

func _on_body_entered(body: Node3D) -> void:
	if not (body.is_in_group("player") or body.is_in_group("Player")):
		return
	var target: Node3D = (get_node_or_null(spawn_point) as Node3D) if spawn_point != NodePath() else null
	if target != null:
		body.global_position = target.global_position
