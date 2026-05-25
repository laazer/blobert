class_name AttackResource
extends Resource

@export var attack_id: int = 0
@export var attack_name: String = ""
@export var description: String = ""
@export var effect_type: String = ""
@export var damage: float = 1.0
@export var cooldown: float = 0.8
@export var attack_range: float = 1.5
@export var startup_frames: int = 0
@export var knockback_magnitude: float = 0.0
@export var knockback_direction: String = "away"
@export var projectile_speed: float = 0.0
@export var projectile_lifetime: float = 2.0
@export var color: Color = Color.WHITE
@export var vfx_scale: float = 1.0
@export var modifiers: Dictionary = {}:
	set(value):
		modifiers = value.duplicate(true) if value else {}
	get:
		return modifiers
