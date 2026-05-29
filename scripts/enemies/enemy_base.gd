# enemy_base.gd
#
# Shared base script for procedurally generated enemies. Attached to
# CharacterBody3D roots created by scripts/asset_generation/load_assets.gd.
# Exposes identity exports, three-state enum, HP system, knockback impulse,
# and delegates DoT/slowness to EnemyEffectTracker child node.
#
# Spec: project_board/specs/enemy_health_damage_reception_spec.md
# Ticket: M11-14

class_name EnemyBase
extends CharacterBody3D

signal damaged(damage: float, current_hp: float)
signal died()
signal dot_tick(effect_name: String, tick_damage: float, current_hp: float)

@export var enemy_id: String = ""
@export var enemy_family: String = ""
@export var mutation_drop: String = ""
@export var max_hp: float = 10.0

enum State { NORMAL = 0, WEAKENED = 1, INFECTED = 2 }

const KNOCKBACK_DECAY_RATE: float = 0.8
const KNOCKBACK_EPSILON: float = 0.01
const WEAKENED_HP_THRESHOLD: float = 0.5

var current_state: State = State.NORMAL
var current_hp: float = 0.0:
	set(value):
		current_hp = clampf(value, 0.0, max_hp)
var _is_dead: bool = false
var _knockback_velocity: Vector3 = Vector3.ZERO
var _effect_tracker: EnemyEffectTracker = null


func _ready() -> void:
	current_hp = max_hp
	_effect_tracker = EnemyEffectTracker.new()
	_effect_tracker.name = "EnemyEffectTracker"
	_effect_tracker.dot_tick_requested.connect(_on_dot_tick_requested)
	add_child(_effect_tracker)


func _physics_process(_delta: float) -> void:
	if _is_dead:
		return
	velocity += _knockback_velocity
	_knockback_velocity *= KNOCKBACK_DECAY_RATE
	if _knockback_velocity.length() < KNOCKBACK_EPSILON:
		_knockback_velocity = Vector3.ZERO
	move_and_slide()


func set_base_state(state: State) -> void:
	current_state = state


func get_base_state() -> State:
	return current_state


func take_damage(damage: float, knockback: Vector3) -> void:
	if _is_dead:
		return
	damage = maxf(0.0, damage)
	current_hp = maxf(0.0, current_hp - damage)
	_check_weakened_threshold()
	if current_hp > 0.0 and knockback != Vector3.ZERO:
		_knockback_velocity = knockback
	damaged.emit(damage, current_hp)
	if current_hp <= 0.0:
		_enter_death_state()


func apply_poison(duration: float, dps: float) -> void:
	if _is_dead:
		return
	_effect_tracker.add_dot("poison", duration, dps)


func apply_acid(duration: float, dps: float) -> void:
	if _is_dead:
		return
	_effect_tracker.add_dot("acid", duration, dps)


func apply_acid_stack(duration: float, dps: float) -> void:
	if _is_dead:
		return
	_effect_tracker.add_acid_stack(duration, dps)


func get_acid_stack_count() -> int:
	if _effect_tracker == null:
		return 0
	return _effect_tracker.get_acid_stack_count()


func apply_slowness(multiplier: float, duration: float) -> void:
	if _is_dead:
		return
	_effect_tracker.set_slowness(multiplier, duration)


func get_speed_multiplier() -> float:
	if _effect_tracker == null:
		return 1.0
	return _effect_tracker.get_speed_multiplier()


func is_dead() -> bool:
	return _is_dead


func get_esm() -> Node:
	return get_node_or_null("EnemyAnimationController/GeneratedEnemyEsmStub")


func _on_dot_tick_requested(effect_name: String, tick_damage: float) -> void:
	_apply_dot_damage(effect_name, tick_damage)


func _apply_dot_damage(effect_name: String, amount: float) -> void:
	if _is_dead:
		return
	amount = maxf(0.0, amount)
	current_hp = maxf(0.0, current_hp - amount)
	_check_weakened_threshold()
	dot_tick.emit(effect_name, amount, current_hp)
	if current_hp <= 0.0:
		_enter_death_state()


func _check_weakened_threshold() -> void:
	if current_state != State.NORMAL:
		return
	if current_hp <= max_hp * WEAKENED_HP_THRESHOLD:
		current_state = State.WEAKENED


func _enter_death_state() -> void:
	_is_dead = true
	_effect_tracker.stop_all_effects()
	for child in get_children():
		if child is EnemyAIController:
			child.set_physics_process(false)
			break
	died.emit()
