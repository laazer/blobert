extends Label


func _init() -> void:
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree == null or tree.root == null:
		return

	var config: Node = tree.root.get_node_or_null("InputHintsConfig")
	if config == null:
		return

	if "input_hints_enabled" in config:
		visible = config.input_hints_enabled

