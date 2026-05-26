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


static func build_scene(parent_node: Node3D, enemies: Array = [], pos: Vector3 = Vector3.ZERO) -> Dictionary:
	var executor := make_executor()
	if executor == null:
		return {}
	var scene_root := Node3D.new()
	scene_root.add_child(parent_node)
	parent_node.add_child(executor)
	parent_node.global_position = pos
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)
	for e in enemies:
		scene_root.add_child(e)
		if e.is_inside_tree():
			e.add_to_group("enemies")
	return {"root": scene_root, "parent": parent_node, "executor": executor}


static func teardown_scene(scene: Dictionary) -> void:
	var root = scene.get("root")
	if root != null and is_instance_valid(root):
		(root as Node).free()
