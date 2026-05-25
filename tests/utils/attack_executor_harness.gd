extends RefCounted
class_name AttackExecutorHarness

const EXECUTOR_PATH := "res://scripts/attacks/attack_executor.gd"


static func load_executor_script() -> GDScript:
	return load(EXECUTOR_PATH) as GDScript


static func make_executor() -> Node:
	var script := load_executor_script()
	if script == null:
		return null
	return script.new()
