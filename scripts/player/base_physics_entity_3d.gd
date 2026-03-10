# base_physics_entity_3d.gd
#
# Base class for entities that need basic collision in 3D.
# Extends CharacterBody3D.

class_name BasePhysicsEntity3D
extends CharacterBody3D

func _physics_process(delta: float) -> void:
	var project_gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity", 9.8) as float
	velocity.y -= project_gravity * delta