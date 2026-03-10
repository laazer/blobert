# infection_absorb_fx_presenter.gd
#
# Presentation: visual feedback for absorb event. Subscribes to 
# InfectionInteractionHandler.absorb_resolved and plays particle/animation
# feedback at the target enemy position.
#
# Behavior: when absorb resolves, spawn a brief particle effect (white/cyan
# particles, 0.3-0.5s duration) at the enemy's position, then clean up.
#
# Ticket: visual_feedback_infection.md (Task 5 - Absorb Feedback)

extends Node

var _handler: InfectionInteractionHandler = null
var _active_effects: Array[Node] = []


func _ready() -> void:
	var parent: Node = get_parent()
	if parent != null:
		_handler = parent.get_node_or_null("InfectionInteractionHandler") as InfectionInteractionHandler
		if _handler != null:
			_handler.absorb_resolved.connect(_on_absorb_resolved)


func _on_absorb_resolved(esm: EnemyStateMachine) -> void:
	if esm == null:
		return
	
	var enemy_node: Node = esm.get_parent() if esm != null else null
	if enemy_node == null:
		return
	
	var enemy_pos: Vector2 = (enemy_node as Node2D).global_position if enemy_node is Node2D else Vector2.ZERO
	
	# Spawn particle effect at enemy position
	_spawn_absorb_particles(enemy_pos)


func _spawn_absorb_particles(pos: Vector2) -> void:
	# Create a simple CPUParticles2D for absorb feedback
	var particles := CPUParticles2D.new()
	particles.global_position = pos
	particles.emitting = false
	particles.lifetime = 0.4
	particles.amount = 12
	particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_CIRCLE
	particles.emission_sphere_radius = 10.0
	particles.direction = Vector2(0, -1)
	particles.spread_degrees = 180.0
	particles.initial_velocity_min = 100.0
	particles.initial_velocity_max = 150.0
	particles.angular_velocity_min = 0.0
	particles.angular_velocity_max = 360.0
	particles.gravity = Vector2(0, 50.0)
	
	# Color: white to cyan
	var gradient := Gradient.new()
	gradient.add_point(0.0, Color.WHITE)
	gradient.add_point(1.0, Color(0.5, 1.0, 1.0, 0.0))
	particles.color_initial_ramp = gradient
	
	# Size: small particles that fade
	var size_curve := Curve.new()
	size_curve.add_point(Vector2(0.0, 1.0))
	size_curve.add_point(Vector2(1.0, 0.0))
	particles.scale_amount_curve = size_curve
	
	# Add to scene and emit
	get_parent().add_child(particles)
	particles.emitting = true
	_active_effects.append(particles)
	
	# Clean up after effect finishes
	await get_tree().create_timer(particles.lifetime).timeout
	if particles != null and not particles.is_queued_for_deletion():
		particles.queue_free()
	_active_effects.erase(particles)
