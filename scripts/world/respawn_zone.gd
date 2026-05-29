# DeadZone-style Area3D: when a body in group "player" enters, reset to spawn_point.

class_name RespawnZone
extends Area3D

@export var spawn_point: NodePath = NodePath()

func _on_body_entered(body: Node3D) -> void:
	if not (body.is_in_group("player") or body.is_in_group("Player")):
		return
	var target: Node3D = (get_node_or_null(spawn_point) as Node3D) if spawn_point != NodePath() else null
	if target != null:
		if body.has_method("reset_position"):
			body.call("reset_position", target.global_position)
		else:
			body.global_position = target.global_position
	if body.has_method("reset_hp"):
		body.call("reset_hp")
	if body.has_method("reset_chunks"):
		body.call("reset_chunks")
	if body.has_method("get_attack_executor"):
		var executor: Variant = body.call("get_attack_executor")
		if executor != null:
			executor.set("_is_active", false)
