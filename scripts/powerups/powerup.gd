# PowerUp.gd
#
# Represents a collectible power-up item in the world.
# Pure logic class with no Node dependencies for testability.
#
# Power-up types:
#   HEALTH_BOOST - Restores HP when collected
#   SPEED_BOOST  - Temporarily increases movement speed
#   SHIELD       - Grants temporary damage immunity
#   EXTRA_SLOT   - Adds a mutation slot (permanent)

class_name PowerUp
extends RefCounted

enum Type {
	HEALTH_BOOST,
	SPEED_BOOST,
	SHIELD,
	EXTRA_SLOT
}

var power_up_type: Type = Type.HEALTH_BOOST
var duration: float = 0.0  # For temporary effects (seconds)
var value: float = 0.0     # For numeric effects (HP amount, speed multiplier)

# Spawn metadata
var spawn_position: Vector3 = Vector3.ZERO
var is_active: bool = true

func _init(type: Type, duration_secs: float = 0.0, hp_value: float = 0.0) -> void:
	power_up_type = type
	duration = duration_secs
	value = hp_value

func apply_effect(player_controller: Node) -> void:
	match power_up_type:
		Type.HEALTH_BOOST:
			if player_controller.has_method("restore_hp"):
				player_controller.restore_hp(value)

		Type.SPEED_BOOST:
			if player_controller.has_method("apply_speed_boost"):
				player_controller.apply_speed_boost(duration, value)

		Type.SHIELD:
			if player_controller.has_method("activate_shield"):
				player_controller.activate_shield(duration)

		Type.EXTRA_SLOT:
			if player_controller.has_method("unlock_mutation_slot"):
				player_controller.unlock_mutation_slot()

func is_temporary() -> bool:
	return duration > 0.0 and power_up_type in [Type.SPEED_BOOST, Type.SHIELD]
