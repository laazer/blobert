class_name AttackExecutor
extends Node

const FRAMES_PER_SECOND := 60.0
const HITBOX_RANGE_FACTOR := 0.5
const DEFAULT_POISON_DPS := 0.3
const DEFAULT_ACID_DPS := 0.2
const DEFAULT_SLOW_DURATION := 1.5
const DEGENERATE_DISTANCE_SQ := 1e-8

signal attack_started(resource: AttackResource)
signal attack_hit(target: Node3D, resource: AttackResource)
signal projectile_fired(projectile: Node3D, resource: AttackResource)
signal melee_vfx_requested(position: Vector3, color: Color, scale: float)

var _is_active: bool = false


func execute_attack(resource: AttackResource) -> void:
	if resource == null:
		return
	if _is_active:
		return
	_is_active = true
	attack_started.emit(resource)
	match resource.effect_type:
		"MELEE_SWIPE":
			_handle_melee_swipe(resource)
		"PROJECTILE_SPIT":
			_handle_projectile_spit(resource)
		_:
			_handle_unknown(resource)
	_is_active = false


func is_active() -> bool:
	return _is_active


func _handle_melee_swipe(resource: AttackResource) -> void:
	if resource.startup_frames > 0:
		var tree := get_tree()
		if tree:
			await tree.create_timer(resource.startup_frames / FRAMES_PER_SECOND).timeout

	var facing := _get_facing_sign()
	var owner_pos := _get_owner_position()
	var center := owner_pos + Vector3(facing * resource.attack_range * HITBOX_RANGE_FACTOR, 0.0, 0.0)
	var radius := resource.attack_range * HITBOX_RANGE_FACTOR
	var enemies := _query_enemies_in_range(center, radius)

	for enemy in enemies:
		var pre_state: int = -1
		if enemy.has_method("get_base_state"):
			pre_state = enemy.get_base_state()
		var kb := _calculate_knockback(
			enemy.global_position, owner_pos,
			resource.knockback_magnitude, resource.knockback_direction
		)
		_apply_damage(enemy, resource.damage, kb)
		_apply_modifiers(enemy, resource.modifiers, pre_state)
		attack_hit.emit(enemy, resource)

	melee_vfx_requested.emit(center, resource.color, resource.vfx_scale)


func _handle_projectile_spit(resource: AttackResource) -> void:
	if resource.startup_frames > 0:
		var tree := get_tree()
		if tree:
			await tree.create_timer(resource.startup_frames / FRAMES_PER_SECOND).timeout

	var projectile := PlayerProjectile3D.new()
	projectile.damage = resource.damage
	projectile.speed = resource.projectile_speed
	projectile.lifetime = resource.projectile_lifetime
	projectile.knockback_magnitude = resource.knockback_magnitude
	projectile.knockback_direction = resource.knockback_direction
	projectile.modifiers = resource.modifiers.duplicate(true)
	projectile.direction_x = _get_facing_sign()
	projectile.color = resource.color

	var grandparent: Node = null
	if get_parent():
		grandparent = get_parent().get_parent()
	if grandparent:
		grandparent.add_child(projectile)
		projectile.global_position = _get_owner_position()

	projectile_fired.emit(projectile, resource)


func _handle_unknown(resource: AttackResource) -> void:
	push_warning("AttackExecutor: unknown effect_type '%s'" % resource.effect_type)


func _apply_damage(target: Node3D, damage: float, knockback: Vector3) -> void:
	if target.has_method("take_damage"):
		target.take_damage(damage, knockback)


func _apply_modifiers(target: Node3D, modifiers: Dictionary, pre_damage_state: int = -1) -> void:
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

	if modifiers.get("infect_weakened", false):
		if target.has_method("get_base_state") and target.has_method("set_base_state"):
			if target.has_method("is_dead") and target.is_dead():
				return
			var check_state: int = pre_damage_state if pre_damage_state >= 0 else -1
			if check_state < 0 and target.has_method("get_base_state"):
				check_state = target.get_base_state()
			if check_state == 1:
				target.set_base_state(2)


func _calculate_knockback(
	target_pos: Vector3, owner_pos: Vector3,
	magnitude: float, direction: String
) -> Vector3:
	if magnitude == 0.0 or direction == "none":
		return Vector3.ZERO

	var delta := target_pos - owner_pos
	delta.z = 0.0

	if delta.length_squared() < DEGENERATE_DISTANCE_SQ:
		delta = Vector3(1.0, 0.0, 0.0)
	else:
		delta = delta.normalized()

	match direction:
		"away":
			return delta * magnitude
		"toward":
			return -delta * magnitude
		_:
			return Vector3.ZERO


func _query_enemies_in_range(center: Vector3, radius: float) -> Array:
	var tree := get_tree()
	if tree == null:
		return []

	var result: Array = []
	for node in tree.get_nodes_in_group("enemies"):
		if node is Node3D:
			if (node as Node3D).global_position.distance_to(center) <= radius:
				result.append(node)
	return result


func _get_facing_sign() -> float:
	var parent := get_parent()
	if parent and parent.has_method("get_facing_sign"):
		return parent.get_facing_sign()
	return 1.0


func _get_owner_position() -> Vector3:
	var parent := get_parent()
	if parent and parent is Node3D:
		return (parent as Node3D).global_position
	return Vector3.ZERO
