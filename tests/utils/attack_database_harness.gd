extends RefCounted
class_name AttackDatabaseHarness

const DB_SCRIPT_PATH := "res://scripts/attacks/attack_database.gd"


## Instantiate a fresh AttackDatabaseNode and add it to the scene tree so
## _ready() fires and _register_defaults() runs. Returns null and calls the
## provided fail_callback if the script is not loadable.
##
## Usage (in a test method):
##   var db = AttackDatabaseHarness.make_db("label", _fail_test)
##   if db == null: return
##   ...
##   AttackDatabaseHarness.free_db(db)
##
## NOTE: The fail_callback signature must accept (label: String, msg: String).
static func make_db(test_label: String, fail_callback: Callable) -> Node:
	var script = load(DB_SCRIPT_PATH) as GDScript
	if script == null:
		fail_callback.call(test_label, DB_SCRIPT_PATH + " not loadable (not yet implemented)")
		return null
	var inst = script.new()
	if inst == null:
		fail_callback.call(test_label, "instantiation returned null")
		return null
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		fail_callback.call(test_label, "SceneTree not available; cannot add_child")
		inst.free()
		return null
	tree.root.add_child(inst)
	return inst


static func free_db(db: Node) -> void:
	if db != null and is_instance_valid(db):
		db.free()


static func make_combo_resource(combo_hits: int = 3) -> AttackResource:
	var r = AttackResource.new()
	r.attack_id = 101
	r.attack_name = "Venomous Shred"
	r.effect_type = "MELEE_SWIPE_COMBO"
	r.damage = 1.8
	r.cooldown = 2.0
	r.attack_range = 1.2
	r.startup_frames = 0
	r.knockback_magnitude = 80.0
	r.knockback_direction = "away"
	r.modifiers = {
		"acid_on_hit": true,
		"acid_duration": 2.5,
		"acid_dps": 0.4,
		"combo_frame_interval": 6
	}
	r.set("combo_hits", combo_hits)
	return r
