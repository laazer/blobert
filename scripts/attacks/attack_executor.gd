class_name AttackExecutor
extends Node

const FRAMES_PER_SECOND := 60.0
const HITBOX_RANGE_FACTOR := 0.5
const DEFAULT_POISON_DPS := 0.3
const DEFAULT_ACID_DPS := 0.2
const DEFAULT_SLOW_DURATION := 1.5
const DEGENERATE_DISTANCE_SQ := 1e-8
const SLAM_LANDING_POLL_INTERVAL := 0.05
const SLAM_LANDING_TIMEOUT := 3.0
const PROJECTILE_SPAWN_OFFSET_X := 0.65
const PROJECTILE_SPAWN_OFFSET_Y := 0.45

signal attack_started(resource: AttackResource)
signal attack_hit(target: Node3D, resource: AttackResource)
signal projectile_fired(projectile: Node3D, resource: AttackResource)
signal melee_vfx_requested(position: Vector3, color: Color, scale: float)
signal slam_vfx_requested(position: Vector3, radius: float, color: Color, scale: float)

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
		"SLAM_AOE":
			_run_slam_attack_async(resource)
			return
		"MELEE_SWIPE_COMBO":
			_run_melee_swipe_combo_async(resource)
			return
		_:
			_handle_unknown(resource)
	_is_active = false


func _run_slam_attack_async(resource: AttackResource) -> void:
	await _handle_slam_aoe(resource)
	_is_active = false


func _run_melee_swipe_combo_async(resource: AttackResource) -> void:
	await _handle_melee_swipe_combo(resource)
	_is_active = false


func _handle_melee_swipe_combo(resource: AttackResource) -> void:
	if resource.combo_hits <= 0:
		return

	if resource.startup_frames > 0:
		var startup_tree := get_tree()
		if startup_tree:
			await startup_tree.create_timer(resource.startup_frames / FRAMES_PER_SECOND).timeout

	for _i in range(resource.combo_hits):
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
			_apply_combo_modifiers(enemy, resource.modifiers, pre_state)
			attack_hit.emit(enemy, resource)

		melee_vfx_requested.emit(center, resource.color, resource.vfx_scale)


func _apply_combo_modifiers(
	target: Node3D,
	modifiers: Dictionary,
	pre_damage_state: int = -1
) -> void:
	# Combo-specific acid path: apply_acid_stack instead of apply_acid so each
	# hit creates an independently-decaying DoT stack.
	if modifiers.get("acid_on_hit", false):
		if target.has_method("apply_acid_stack"):
			var acid_dur: float = modifiers.get("acid_duration", 2.0)
			var acid_dps_val: float = modifiers.get("acid_dps", DEFAULT_ACID_DPS)
			if target.has_method("get_base_state") and target.get_base_state() == 1:
				acid_dur *= 2.0
			target.apply_acid_stack(acid_dur, acid_dps_val)

	# Delegate all non-acid modifiers (poison, slow, infect_weakened) to the
	# shared base path, excluding acid_on_hit so apply_acid is not also called.
	var mods_sans_acid := modifiers.duplicate()
	mods_sans_acid.erase("acid_on_hit")
	_apply_modifiers(target, mods_sans_acid, pre_damage_state)


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

	var spawn_parent: Node = null
	if get_parent():
		spawn_parent = get_parent().get_parent()
	if spawn_parent:
		spawn_parent.add_child(projectile)
		var facing := _get_facing_sign()
		var owner_pos := _get_owner_position()
		projectile.global_position = owner_pos + Vector3(
			facing * PROJECTILE_SPAWN_OFFSET_X,
			PROJECTILE_SPAWN_OFFSET_Y,
			0.0
		)

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

	var slow_val = modifiers.get("slow", null)
	if slow_val != null:
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


func _is_owner_on_floor() -> bool:
	var parent := get_parent()
	if parent and parent.has_method("is_on_floor"):
		return parent.is_on_floor()
	return true


func _handle_slam_aoe(resource: AttackResource) -> void:
	if resource.startup_frames > 0:
		var startup_tree := get_tree()
		if startup_tree:
			await startup_tree.create_timer(resource.startup_frames / FRAMES_PER_SECOND).timeout

	if not _is_owner_on_floor():
		var elapsed := 0.0
		while elapsed < SLAM_LANDING_TIMEOUT:
			var poll_tree := get_tree()
			if poll_tree == null:
				break
			await poll_tree.create_timer(SLAM_LANDING_POLL_INTERVAL).timeout
			elapsed += SLAM_LANDING_POLL_INTERVAL
			if _is_owner_on_floor():
				break
		if not _is_owner_on_floor():
			return

	var owner_pos := _get_owner_position()
	var enemies := _query_enemies_in_range(owner_pos, resource.attack_range)

	for enemy in enemies:
		var kb := _calculate_knockback(
			enemy.global_position, owner_pos,
			resource.knockback_magnitude, resource.knockback_direction
		)
		_apply_damage(enemy, resource.damage, kb)
		_apply_modifiers(enemy, resource.modifiers)
		attack_hit.emit(enemy, resource)

	slam_vfx_requested.emit(owner_pos, resource.attack_range, resource.color, resource.vfx_scale)
