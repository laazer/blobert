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

@export var mutation_drop: String = "infection_mutation_01"
@export var model_scene: PackedScene = null

var _esm: EnemyStateMachine = EnemyStateMachine.new()
var _handler: InfectionInteractionHandler
var _area: Area3D
var _attached_chunks: Array[RigidBody3D] = []


func _ready() -> void:
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
	velocity.x = 0.0
	velocity.z = 0.0
	# move and apply collisions; after sliding, clear vertical speed if we're on the floor
	move_and_slide()
	if is_on_floor():
		if velocity.y != 0.0:
			Logging.trace("enemy landed, clearing velocity from " + str(velocity.y))
		velocity.y = 0.0
