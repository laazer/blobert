# acid_projectile_3d.gd
# Enemy acid glob: moves on X toward the player, damages on first player touch,
# despawns on StaticBody3D contact or max age (M8 acid_enemy_attack).

class_name AcidProjectile3D
extends Area3D

@export var impact_damage: float = 8.0
@export var dot_tick_damage: float = 4.0
@export var dot_duration_seconds: float = 3.0
@export var dot_tick_interval: float = 0.5
@export var max_lifetime_seconds: float = 3.0

var _dir_x: float = 1.0
var _speed: float = 14.0
var _age: float = 0.0
var _consumed: bool = false


func setup(direction_sign_x: float, speed: float) -> void:
	_dir_x = direction_sign_x if direction_sign_x != 0.0 else 1.0
	_speed = speed


func _ready() -> void:
	set_physics_process(true)
	body_entered.connect(_on_body_entered)


func _physics_process(delta: float) -> void:
	if _consumed:
		return
	_age += delta
	if _age >= max_lifetime_seconds:
		_consumed = true
		queue_free()
		return
	global_position.x += _dir_x * _speed * delta


func _on_body_entered(body: Node3D) -> void:
	if _consumed:
		return
	if body.is_in_group("player") and body.has_method("apply_enemy_acid_damage"):
		_consumed = true
		body.call(
			"apply_enemy_acid_damage",
			impact_damage,
			dot_tick_damage,
			dot_duration_seconds,
			dot_tick_interval
		)
		queue_free()
		return
	if body is StaticBody3D:
		_consumed = true
		queue_free()
