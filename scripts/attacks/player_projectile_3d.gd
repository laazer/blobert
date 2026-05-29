class_name PlayerProjectile3D
extends Area3D

const DEFAULT_POISON_DPS := 0.3
const DEFAULT_ACID_DPS := 0.2
const DEFAULT_SLOW_DURATION := 1.5
const DEGENERATE_DISTANCE_SQ := 1e-8
const PROJECTILE_RADIUS := 0.22
const PROJECTILE_LAYER := 4
const PROJECTILE_MASK := 3

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


func _ready() -> void:
	collision_layer = PROJECTILE_LAYER
	collision_mask = PROJECTILE_MASK
	monitoring = true
	monitorable = false
	if not body_entered.is_connected(_on_body_entered):
		body_entered.connect(_on_body_entered)
	_ensure_visual_and_collision()


func _ensure_visual_and_collision() -> void:
	var shape_node: CollisionShape3D = get_node_or_null("CollisionShape3D") as CollisionShape3D
	if shape_node == null:
		shape_node = CollisionShape3D.new()
		shape_node.name = "CollisionShape3D"
		add_child(shape_node)
	if shape_node.shape == null:
		var sphere := SphereShape3D.new()
		sphere.radius = PROJECTILE_RADIUS
		shape_node.shape = sphere

	var mesh_node: MeshInstance3D = get_node_or_null("MeshInstance3D") as MeshInstance3D
	if mesh_node == null:
		mesh_node = MeshInstance3D.new()
		mesh_node.name = "MeshInstance3D"
		add_child(mesh_node)
	if mesh_node.mesh == null:
		var mesh := SphereMesh.new()
		mesh.radius = PROJECTILE_RADIUS
		mesh.height = PROJECTILE_RADIUS * 2.0
		mesh_node.mesh = mesh
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.emission_enabled = true
	material.emission = color
	material.emission_energy_multiplier = 2.0
	material.albedo_color = color
	mesh_node.material_override = material


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
	if body.is_in_group("player") or body.is_in_group("chunk"):
		return
	if body.has_method("take_damage"):
		_consumed = true
		var kb := _compute_knockback(body)
		body.take_damage(damage, kb)
		_apply_modifiers(body)
		queue_free()
	else:
		_consumed = true
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
	var slow_val = modifiers.get("slow", null)
	if slow_val != null:
		if target.has_method("apply_slowness"):
			target.apply_slowness(slow_val, modifiers.get("slow_duration", DEFAULT_SLOW_DURATION))
