class_name PlayerProjectile3D
extends Area3D

const DEFAULT_POISON_DPS := 0.3
const DEFAULT_ACID_DPS := 0.2
const DEFAULT_SLOW_DURATION := 1.5
const DEGENERATE_DISTANCE_SQ := 1e-8

var damage: float = 0.0
var speed: float = 0.0
var lifetime: float = 2.0
var knockback_magnitude: float = 0.0
var knockback_direction: String = "away"
var modifiers: Dictionary = {}
var direction_x: float = 1.0
var color: Color = Color.WHITE

var _age: float = 0.0
var _consumed: bool = false


func _physics_process(delta: float) -> void:
	if _consumed:
		return
	_age += delta
	if _age >= lifetime:
		_consumed = true
		queue_free()
		return
	global_position.x += direction_x * speed * delta


func _on_body_entered(body: Node3D) -> void:
	if _consumed:
		return
	if body.has_method("take_damage"):
		_consumed = true
		var kb := _compute_knockback(body)
		body.take_damage(damage, kb)
		_apply_modifiers(body)
		queue_free()


func _compute_knockback(target: Node3D) -> Vector3:
	if knockback_magnitude == 0.0 or knockback_direction == "none":
		return Vector3.ZERO
	var delta := target.global_position - global_position
	delta.z = 0.0
	if delta.length_squared() < DEGENERATE_DISTANCE_SQ:
		delta = Vector3(1.0, 0.0, 0.0)
	else:
		delta = delta.normalized()
	match knockback_direction:
		"away":
			return delta * knockback_magnitude
		"toward":
			return -delta * knockback_magnitude
		_:
			return Vector3.ZERO


func _apply_modifiers(target: Node3D) -> void:
	if modifiers.get("poison", false):
		if target.has_method("apply_poison"):
			target.apply_poison(
				modifiers.get("poison_duration", 2.0),
				modifiers.get("poison_dps", DEFAULT_POISON_DPS)
			)
	if modifiers.get("acid_on_hit", false):
		if target.has_method("apply_acid"):
			var acid_dur: float = modifiers.get("acid_duration", 2.0)
			var acid_dps_val: float = modifiers.get("acid_dps", DEFAULT_ACID_DPS)
			if target.has_method("get_base_state") and target.get_base_state() == 1:
				acid_dur *= 2.0
			target.apply_acid(acid_dur, acid_dps_val)
	var slow_val = modifiers.get("slow", 0.0)
	if slow_val and slow_val > 0.0:
		if target.has_method("apply_slowness"):
			target.apply_slowness(slow_val, modifiers.get("slow_duration", DEFAULT_SLOW_DURATION))
