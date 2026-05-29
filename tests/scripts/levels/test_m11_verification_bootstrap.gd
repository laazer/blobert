#
# Runtime bootstrap for M11 verification sandbox: slot A seeded with acid so
# attack (J) works without manual absorb flow.

extends "res://tests/utils/test_utils.gd"

const _M11_CONTROLLER_PATH: String = "res://scripts/levels/m11_verification_controller_3d.gd"
const _HANDLER_PATH: String = "res://scripts/infection/infection_interaction_handler.gd"

var _pass_count: int = 0
var _fail_count: int = 0


func _build_m11_harness(test_label: String) -> Dictionary:
	var m11_script: GDScript = load(_M11_CONTROLLER_PATH) as GDScript
	var handler_script: GDScript = load(_HANDLER_PATH) as GDScript
	if m11_script == null or handler_script == null:
		_fail(test_label, "could not load m11 controller or handler script")
		return {}
	var root: Node3D = Node3D.new()
	root.name = "M11Harness"
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail(test_label, "no SceneTree")
		return {}
	tree.root.add_child(root)
	var handler: Node = handler_script.new() as Node
	handler.name = "InfectionInteractionHandler"
	root.add_child(handler)
	var m11: Node = m11_script.new() as Node
	m11.name = "M11VerificationController"
	root.add_child(m11)
	return {"root": root, "handler": handler, "m11": m11}


func _teardown(scene: Dictionary) -> void:
	var root: Variant = scene.get("root")
	if root != null and is_instance_valid(root):
		(root as Node).free()


func _slot_a_id(handler: Node) -> String:
	if not handler.has_method("get_mutation_slot_manager"):
		return ""
	var mgr: Variant = handler.call("get_mutation_slot_manager")
	if mgr == null or not mgr.has_method("get_slot"):
		return ""
	var slot_a: Variant = mgr.call("get_slot", 0)
	if slot_a == null or not slot_a.has_method("get_active_mutation_id"):
		return ""
	return slot_a.call("get_active_mutation_id") as String


func test_bootstrap_fills_slot_a_with_acid() -> void:
	var scene: Dictionary = _build_m11_harness("m11_bootstrap_acid")
	if scene.is_empty():
		return
	var handler: Node = scene["handler"]
	var m11: Node = scene["m11"]
	handler._ready()
	m11._ready()
	if m11.has_method("_bootstrap_verification"):
		m11.call("_bootstrap_verification")
	var mid: String = _slot_a_id(handler)
	_assert_eq_str(mid, "acid", "m11_bootstrap_slot_a_acid")
	_teardown(scene)


func test_ensure_slot_a_reseeds_after_clear() -> void:
	var scene: Dictionary = _build_m11_harness("m11_reseed_slot_a")
	if scene.is_empty():
		return
	var handler: Node = scene["handler"]
	var m11: Node = scene["m11"]
	handler._ready()
	m11._ready()
	if m11.has_method("_bootstrap_verification"):
		m11.call("_bootstrap_verification")
	if handler.has_method("get_mutation_slot_manager"):
		var mgr: Variant = handler.call("get_mutation_slot_manager")
		if mgr != null and mgr.has_method("get_slot"):
			var slot_a: Variant = mgr.call("get_slot", 0)
			if slot_a != null and slot_a.has_method("clear"):
				slot_a.call("clear")
	m11.set("_bootstrap_complete", true)
	if m11.has_method("_ensure_slot_a_seeded"):
		m11.call("_ensure_slot_a_seeded")
	var mid: String = _slot_a_id(handler)
	_assert_eq_str(mid, "acid", "m11_ensure_slot_a_reseed_acid")
	_teardown(scene)


func test_bootstrap_grants_all_mutation_inventory_ids() -> void:
	var scene: Dictionary = _build_m11_harness("m11_inventory_grant")
	if scene.is_empty():
		return
	var handler: Node = scene["handler"]
	var m11: Node = scene["m11"]
	handler._ready()
	m11._ready()
	if m11.has_method("_bootstrap_verification"):
		m11.call("_bootstrap_verification")
	if not handler.has_method("get_mutation_inventory"):
		_fail("m11_inventory_method", "handler missing get_mutation_inventory")
		_teardown(scene)
		return
	var inventory: Variant = handler.call("get_mutation_inventory")
	if inventory == null or not inventory.has_method("has"):
		_fail("m11_inventory_object", "inventory missing has()")
		_teardown(scene)
		return
	for mid in ["claw", "acid", "carapace", "adhesion"]:
		_assert_true(inventory.call("has", mid), "m11_inventory_has_" + mid)
	_teardown(scene)


func run_all() -> int:
	_pass_count = 0
	_fail_count = 0
	test_bootstrap_fills_slot_a_with_acid()
	test_ensure_slot_a_reseeds_after_clear()
	test_bootstrap_grants_all_mutation_inventory_ids()
	return _fail_count
