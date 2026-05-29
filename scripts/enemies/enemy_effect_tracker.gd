# enemy_effect_tracker.gd
#
# Helper node for managing DoT effects (poison, acid) and speed modifiers
# (slowness) on enemies. Created by EnemyBase._ready() as a child node.
# Owns _process(delta) for tick timing.
#
# Spec: project_board/specs/enemy_health_damage_reception_spec.md
# Requirements: EHD-4, EHD-7, EHD-8

class_name EnemyEffectTracker
extends Node

signal dot_tick_requested(effect_name: String, tick_damage: float)

const DOT_TICK_INTERVAL: float = 0.5

var _active_dots: Dictionary = {}
var _slowness_multiplier: float = 1.0
var _slowness_remaining: float = 0.0
var _acid_stack_counter: int = 0


func add_dot(effect_name: String, duration: float, dps: float) -> void:
	if duration <= 0.0:
		return
	_active_dots[effect_name] = {
		"remaining_duration": duration,
		"dps": dps,
		"elapsed_since_tick": 0.0,
	}


func add_acid_stack(duration: float, dps: float) -> void:
	if duration <= 0.0:
		return
	var key: String = "acid_stack_%d" % _acid_stack_counter
	_acid_stack_counter += 1
	add_dot(key, duration, dps)


func get_acid_stack_count() -> int:
	var count: int = 0
	for key in _active_dots.keys():
		if (key as String).begins_with("acid_stack_"):
			count += 1
	return count


func set_slowness(multiplier: float, duration: float) -> void:
	if duration <= 0.0:
		return
	_slowness_multiplier = maxf(0.0, multiplier)
	_slowness_remaining = duration


func get_speed_multiplier() -> float:
	if _slowness_remaining > 0.0:
		return _slowness_multiplier
	return 1.0


func has_active_dot(effect_name: String) -> bool:
	return _active_dots.has(effect_name)


func stop_all_effects() -> void:
	_active_dots.clear()
	_slowness_multiplier = 1.0
	_slowness_remaining = 0.0


func _process(delta: float) -> void:
	_tick_dots(delta)
	_tick_slowness(delta)


func _tick_dots(delta: float) -> void:
	var to_remove: Array = []
	for effect_name in _active_dots.keys():
		if not _active_dots.has(effect_name):
			continue
		var effect: Dictionary = _active_dots[effect_name]
		effect.elapsed_since_tick += delta
		effect.remaining_duration -= delta
		while effect.elapsed_since_tick >= DOT_TICK_INTERVAL:
			effect.elapsed_since_tick -= DOT_TICK_INTERVAL
			var tick_damage: float = effect.dps * DOT_TICK_INTERVAL
			dot_tick_requested.emit(effect_name, tick_damage)
			if not _active_dots.has(effect_name):
				break
		if _active_dots.has(effect_name) and effect.remaining_duration <= 0.0:
			to_remove.append(effect_name)
	for n in to_remove:
		_active_dots.erase(n)


func _tick_slowness(delta: float) -> void:
	if _slowness_remaining > 0.0:
		_slowness_remaining -= delta
		if _slowness_remaining <= 0.0:
			_slowness_remaining = 0.0
			_slowness_multiplier = 1.0
