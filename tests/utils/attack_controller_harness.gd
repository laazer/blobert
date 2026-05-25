extends RefCounted
class_name AttackControllerHarness

const CONTROLLER_PATH := "res://scripts/player/player_controller_3d.gd"


static func load_controller_script() -> GDScript:
	return load(CONTROLLER_PATH) as GDScript


static func build_controller_scene() -> Dictionary:
	var ctrl_script = load_controller_script()
	if ctrl_script == null:
		return {}
	var controller = ctrl_script.new()
	if controller == null:
		return {}
	var scene_root = Node3D.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)
	scene_root.add_child(controller)
	return {"root": scene_root, "controller": controller}


static func teardown(scene: Dictionary) -> void:
	var root = scene.get("root")
	if root != null and is_instance_valid(root):
		(root as Node).free()


static func get_autoload_db() -> Node:
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		return null
	return tree.root.get_node_or_null("AttackDatabase")
