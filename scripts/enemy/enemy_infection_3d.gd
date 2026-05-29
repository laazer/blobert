# enemy_infection_3d.gd
#
# 3D engine-integration node for the infection loop: holds an EnemyStateMachine,
# exposes it to InfectionInteractionHandler for target/absorb, and detects
# player (for set_target_esm/clear_target) and chunk (contact → chunk_attached; DoT in PlayerController3D).
# Uses BasePhysicsEntity3D so the enemy is affected by gravity and collides with objects.
# Same contract as enemy_infection.gd but with Area3D and Node3D.

class_name EnemyInfection3D
extends BasePhysicsEntity3D

signal chunk_attached(chunk: RigidBody3D)

const KNOCKBACK_DECAY_RATE: float = 0.8
const KNOCKBACK_EPSILON: float = 0.01
const WEAKENED_HP_THRESHOLD: float = 0.5

@export var mutation_drop: String = "infection_mutation_01"
@export var model_scene: PackedScene = null
@export var max_hp: float = 10.0

var _esm: EnemyStateMachine = EnemyStateMachine.new()
var _handler: InfectionInteractionHandler
var _area: Area3D
var _attached_chunks: Array[RigidBody3D] = []
var _current_hp: float = 0.0
var _knockback_velocity: Vector3 = Vector3.ZERO
var _effect_tracker: EnemyEffectTracker = null


func _ready() -> void:
	add_to_group("enemies")
	_current_hp = max_hp
	_effect_tracker = EnemyEffectTracker.new()
	_effect_tracker.name = "EnemyEffectTracker"
	_effect_tracker.dot_tick_requested.connect(_on_dot_tick_requested)
	add_child(_effect_tracker)
	var anim_ctrl: EnemyAnimationController = get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	if anim_ctrl != null:
		anim_ctrl.setup(_esm)

	var p: Node = get_parent()
	while p != null:
		var candidate := p.get_node_or_null("InfectionInteractionHandler") as InfectionInteractionHandler
		if candidate != null:
			_handler = candidate
			break
		p = p.get_parent()
	_area = get_node_or_null("InteractionArea") as Area3D
	if _area != null:
		_area.body_entered.connect(_on_body_entered)
		_area.body_exited.connect(_on_body_exited)
	if model_scene != null:
		call_deferred("_swap_model_scene")
	else:
		call_deferred("_wire_and_notify_animation")


func _swap_model_scene() -> void:
	var old_visual: Node = get_node_or_null("EnemyVisual")
	if old_visual != null:
		old_visual.free()
	var new_visual: Node3D = model_scene.instantiate() as Node3D
	if new_visual != null:
		new_visual.name = "EnemyVisual"
		add_child(new_visual)
	call_deferred("_wire_and_notify_animation")


func _wire_and_notify_animation() -> void:
	_wire_glb_libraries_to_root_animation_player()
	var anim_ctrl: EnemyAnimationController = get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	if anim_ctrl != null:
		anim_ctrl.notify_root_animation_wired()
	_ensure_acid_spitter_ranged_attack_if_needed()
	_ensure_adhesion_bug_lunge_attack_if_needed()
	_ensure_carapace_husk_attack_if_needed()
	_ensure_claw_crawler_attack_if_needed()


func _ensure_acid_spitter_ranged_attack_if_needed() -> void:
	if mutation_drop != "acid":
		return
	if get_node_or_null("AcidSpitterRangedAttack") != null:
		return
	var atk_script: GDScript = load("res://scripts/enemy/acid_spitter_ranged_attack.gd") as GDScript
	if atk_script == null:
		return
	var atk: Node = atk_script.new() as Node
	atk.name = "AcidSpitterRangedAttack"
	add_child(atk)


func _ensure_adhesion_bug_lunge_attack_if_needed() -> void:
	if mutation_drop != "adhesion":
		return
	if get_node_or_null("AdhesionBugLungeAttack") != null:
		return
	var atk_script: GDScript = load("res://scripts/enemy/adhesion_bug_lunge_attack.gd") as GDScript
	if atk_script == null:
		return
	var atk: Node = atk_script.new() as Node
	atk.name = "AdhesionBugLungeAttack"
	add_child(atk)


func _ensure_carapace_husk_attack_if_needed() -> void:
	if mutation_drop != "carapace":
		return
	if get_node_or_null("CarapaceHuskAttack") != null:
		return
	var atk_script: GDScript = load("res://scripts/enemy/carapace_husk_attack.gd") as GDScript
	if atk_script == null:
		return
	var atk: Node = atk_script.new() as Node
	atk.name = "CarapaceHuskAttack"
	add_child(atk)


func _ensure_claw_crawler_attack_if_needed() -> void:
	if mutation_drop != "claw":
		return
	if get_node_or_null("ClawCrawlerAttack") != null:
		return
	var atk_script: GDScript = load("res://scripts/enemy/claw_crawler_attack.gd") as GDScript
	if atk_script == null:
		return
	var atk: Node = atk_script.new() as Node
	atk.name = "ClawCrawlerAttack"
	add_child(atk)


func _wire_glb_libraries_to_root_animation_player() -> void:
	var visual: Node = get_node_or_null("EnemyVisual")
	var target: AnimationPlayer = get_node_or_null("AnimationPlayer") as AnimationPlayer
	if visual == null or target == null:
		return
	var lib_names: Array[StringName] = []
	for ln in target.get_animation_library_list():
		lib_names.append(ln)
	for lib_name in lib_names:
		target.remove_animation_library(lib_name)
	var found: Array[Node] = visual.find_children("*", "AnimationPlayer", true, false)
	if found.is_empty():
		return
	var src: AnimationPlayer = found[0] as AnimationPlayer
	for lib_name in src.get_animation_library_list():
		var lib: AnimationLibrary = src.get_animation_library(lib_name)
		if lib == null:
			continue
		var dup: AnimationLibrary = lib.duplicate(true) as AnimationLibrary
		if dup == null:
			continue
		var err: Error = target.add_animation_library(lib_name, dup)
		if err != OK:
			push_warning(
				"EnemyInfection3D: add_animation_library(%s) failed: %s"
				% [str(lib_name), error_string(err)]
			)
	target.root_node = NodePath("../EnemyVisual")


func get_esm() -> EnemyStateMachine:
	return _esm


func get_base_state() -> int:
	match _esm.get_state():
		EnemyStateMachine.STATE_WEAKENED:
			return 1
		EnemyStateMachine.STATE_INFECTED:
			return 2
		_:
			return 0


func set_base_state(state: int) -> void:
	if _esm.get_state() == EnemyStateMachine.STATE_DEAD:
		return
	if state == 1:
		_esm.apply_weaken_event()
	elif state == 2:
		if _esm.get_state() == EnemyStateMachine.STATE_WEAKENED:
			_esm.apply_infection_event()
		elif _esm.get_state() in [EnemyStateMachine.STATE_IDLE, EnemyStateMachine.STATE_ACTIVE]:
			_esm.apply_weaken_event()
			_esm.apply_infection_event()


func take_damage(damage: float, knockback: Vector3) -> void:
	if is_dead():
		return
	damage = maxf(0.0, damage)
	_current_hp = maxf(0.0, _current_hp - damage)
	_sync_esm_from_hp()
	play_damage_hit_animation()
	if _current_hp > 0.0 and knockback != Vector3.ZERO:
		_knockback_velocity = knockback
	if _current_hp <= 0.0:
		_esm.apply_death_event()


func apply_acid(duration: float, dps: float) -> void:
	if is_dead() or _effect_tracker == null:
		return
	_effect_tracker.add_dot("acid", duration, dps)


func apply_slowness(multiplier: float, duration: float) -> void:
	if is_dead() or _effect_tracker == null:
		return
	_effect_tracker.set_slowness(multiplier, duration)


func get_speed_multiplier() -> float:
	if _effect_tracker == null:
		return 1.0
	return _effect_tracker.get_speed_multiplier()


func is_dead() -> bool:
	return _esm.get_state() == EnemyStateMachine.STATE_DEAD


func _sync_esm_from_hp() -> void:
	if _esm.get_state() in [
		EnemyStateMachine.STATE_WEAKENED,
		EnemyStateMachine.STATE_INFECTED,
		EnemyStateMachine.STATE_DEAD,
	]:
		return
	if _current_hp <= max_hp * WEAKENED_HP_THRESHOLD:
		_esm.apply_weaken_event()


func _on_dot_tick_requested(effect_name: String, tick_damage: float) -> void:
	if is_dead():
		return
	tick_damage = maxf(0.0, tick_damage)
	_current_hp = maxf(0.0, _current_hp - tick_damage)
	_sync_esm_from_hp()
	play_damage_hit_animation()
	if _current_hp <= 0.0:
		_esm.apply_death_event()


## Plays the one-shot Hit (damage) clip on the root AnimationPlayer, if wired.
## No-op when dead or controller / Hit clip unavailable.
func play_damage_hit_animation() -> void:
	if _esm.get_state() == "dead":
		return
	var anim_ctrl: EnemyAnimationController = get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	if anim_ctrl == null:
		return
	anim_ctrl.trigger_hit_animation()


## Containment Hall mini-boss uses the same scene with a larger instance scale.
func is_mini_boss_unit() -> bool:
	return name == "EnemyMiniBoss"


func unregister_attached_chunk(chunk: RigidBody3D) -> void:
	var idx: int = _attached_chunks.find(chunk)
	if idx >= 0:
		_attached_chunks.remove_at(idx)


func _on_body_entered(body: Node3D) -> void:
	if body.is_in_group("player"):
		if _handler != null:
			_handler.set_target_esm(_esm, self)
	if body.is_in_group("chunk"):
		var chunk: RigidBody3D = body as RigidBody3D
		if chunk in _attached_chunks:
			return
		if _esm.get_state() == "dead":
			return
		# Weaken / infect / absorb are driven by PlayerController3D chunk DoT ticks
		# (3 physics ticks) so blob damage can apply once per tick, then auto-return.
		chunk_attached.emit(chunk)
		_attached_chunks.append(chunk)


func _on_body_exited(body: Node3D) -> void:
	if body.is_in_group("player"):
		if _handler != null:
			_handler.clear_target()


func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	velocity += _knockback_velocity
	_knockback_velocity *= KNOCKBACK_DECAY_RATE
	if _knockback_velocity.length() < KNOCKBACK_EPSILON:
		_knockback_velocity = Vector3.ZERO
	var lunge_atk: Node = get_node_or_null("AdhesionBugLungeAttack")
	var lunge_controls_x: bool = false
	if lunge_atk != null and lunge_atk.has_method("enemy_writes_velocity_x_this_frame"):
		lunge_controls_x = lunge_atk.call("enemy_writes_velocity_x_this_frame") as bool
	var carapace_atk: Node = get_node_or_null("CarapaceHuskAttack")
	var carapace_controls_x: bool = false
	if carapace_atk != null and carapace_atk.has_method("enemy_writes_velocity_x_this_frame"):
		carapace_controls_x = carapace_atk.call("enemy_writes_velocity_x_this_frame") as bool
	if not lunge_controls_x and not carapace_controls_x and _knockback_velocity.length() < KNOCKBACK_EPSILON:
		velocity.x = 0.0
	velocity.z = 0.0
	# move and apply collisions; after sliding, clear vertical speed if we're on the floor
	move_and_slide()
	if is_on_floor():
		velocity.y = 0.0
