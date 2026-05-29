## Sandbox bootstrap for M11 manual verification: infection demo flags, optional slot-A
## seed, 1–4 hotkeys, and attack debug HUD. Works with flat scenes or base+section layout.

class_name M11VerificationController3D
extends Node

const _MUTATION_IDS: Array[String] = ["claw", "acid", "carapace", "adhesion"]
const _ACTION_ATTACK: StringName = &"attack"
const _EXECUTOR_STUCK_RECOVER_SEC: float = 0.4
const _DEBUG_LABEL_FONT_SIZE: int = 14
const _DEBUG_LABEL_OUTLINE_SIZE: int = 2
const _DEBUG_LABEL_PIXEL_SIZE: float = 0.0025
const _DEBUG_LABEL_MODULATE: Color = Color(0.95, 1.0, 0.65, 1.0)
const _DEBUG_LABEL_BASIS_Y: Vector3 = Vector3(0.0, 0.965926, -0.258819)
const _DEBUG_LABEL_BASIS_Z: Vector3 = Vector3(0.0, 0.258819, 0.965926)
const _ATTACK_PING_COLOR_DEFAULT: Color = Color(0.9, 0.8, 0.2, 1.0)
const _PROJECTILE_PING_COLOR: Color = Color(0.2, 0.9, 1.0, 1.0)
const _PING_MESH_RADIUS: float = 0.18
const _PING_MESH_HEIGHT: float = 0.36
const _PING_EMISSION_ENERGY: float = 2.2
const _PING_Y_OFFSET: float = 1.0
const _PING_LIFETIME_SEC: float = 0.3
const _ROOTED_SPEED_THRESHOLD: float = 0.01
const _HOTKEY_SLOT_COUNT: int = 4
const _HOTKEY_INDEX_CLAW: int = 0
const _HOTKEY_INDEX_ACID: int = 1
const _HOTKEY_INDEX_CARAPACE: int = 2
const _HOTKEY_INDEX_ADHESION: int = 3

## Pre-filled slot A mutation when auto_seed_slot_a is true (also used after clear).
@export var default_slot_a_mutation: String = "acid"
@export var auto_seed_slot_a: bool = true
@export var grant_all_inventory: bool = true
@export var enable_attack_hotkeys: bool = true
@export var debug_label_offset: Vector3 = Vector3(0.0, 0.6, 0.0)

var _bootstrap_complete: bool = false
var _executor_busy_since_sec: float = -1.0
var _j_press_seen_count: int = 0
var _attack_started_count: int = 0
var _projectile_fired_count: int = 0
var _debug_label: Label3D = null
var _executor_connected: bool = false


func _ready() -> void:
	var variant: Node = _resolve_node("SceneVariantController")
	if variant != null and variant.has_method("select_infection_demo"):
		variant.call("select_infection_demo")
	set_process(true)
	call_deferred("_bootstrap_verification")


func _scene_root() -> Node:
	return get_parent()


func _resolve_node(node_name: StringName) -> Node:
	var root: Node = _scene_root()
	if root == null:
		return null
	return root.find_child(String(node_name), true, false)


func _bootstrap_verification() -> void:
	if _bootstrap_complete:
		return
	var handler: Node = _resolve_node("InfectionInteractionHandler")
	if handler == null:
		return
	if handler.has_method("get_mutation_slot_manager"):
		var mgr: Variant = handler.call("get_mutation_slot_manager")
		if mgr != null:
			if mgr.has_method("clear_all"):
				mgr.call("clear_all")
			if auto_seed_slot_a and mgr.has_method("fill_next_available"):
				mgr.call("fill_next_available", default_slot_a_mutation)
			_bind_player_mutation_slot(mgr)
			_bootstrap_complete = true
	if grant_all_inventory and handler.has_method("get_mutation_inventory"):
		var inventory: Variant = handler.call("get_mutation_inventory")
		if inventory != null and inventory.has_method("grant"):
			for mid in _MUTATION_IDS:
				inventory.call("grant", mid)


func _process(delta: float) -> void:
	_ensure_debug_label()
	_ensure_executor_debug_connections()
	if _bootstrap_complete:
		_bind_player_mutation_slot_if_needed()
		_ensure_slot_a_seeded()
		_update_executor_stuck_recovery(delta)
		_track_attack_input_debug()
		_update_debug_label()
		return
	_bootstrap_verification()
	_update_debug_label()


func _bind_player_mutation_slot_if_needed() -> void:
	var handler: Node = _resolve_node("InfectionInteractionHandler")
	if handler == null or not handler.has_method("get_mutation_slot_manager"):
		return
	var mgr: Variant = handler.call("get_mutation_slot_manager")
	if mgr == null:
		return
	var player: Node = _resolve_node("Player3D")
	if player == null:
		return
	if player.get("_mutation_slot") != mgr:
		_bind_player_mutation_slot(mgr)


func _bind_player_mutation_slot(mgr: Variant) -> void:
	var player: Node = _resolve_node("Player3D")
	if player == null:
		return
	player.set("_mutation_slot", mgr)
	if player.has_method("_ensure_mutation_slot_binding"):
		player.call("_ensure_mutation_slot_binding")


func _ensure_slot_a_seeded() -> void:
	if not auto_seed_slot_a:
		return
	var handler: Node = _resolve_node("InfectionInteractionHandler")
	if handler == null or not handler.has_method("get_mutation_slot_manager"):
		return
	var mgr: Variant = handler.call("get_mutation_slot_manager")
	if mgr == null or not mgr.has_method("get_slot"):
		return
	var slot_a: Variant = mgr.call("get_slot", 0)
	if slot_a == null:
		return
	if slot_a.has_method("is_filled") and not slot_a.call("is_filled"):
		if slot_a.has_method("set_active_mutation_id"):
			slot_a.call("set_active_mutation_id", default_slot_a_mutation)


func _update_executor_stuck_recovery(delta: float) -> void:
	var player: Node = _resolve_node("Player3D")
	if player == null or not player.has_method("get_attack_executor"):
		return
	var executor: AttackExecutor = player.call("get_attack_executor") as AttackExecutor
	if executor == null:
		_executor_busy_since_sec = -1.0
		return
	if not executor.is_active():
		_executor_busy_since_sec = -1.0
		return
	if _executor_busy_since_sec < 0.0:
		_executor_busy_since_sec = 0.0
	else:
		_executor_busy_since_sec += delta
	if _executor_busy_since_sec >= _EXECUTOR_STUCK_RECOVER_SEC:
		executor.set("_is_active", false)
		_executor_busy_since_sec = -1.0


func _track_attack_input_debug() -> void:
	if Input.is_action_just_pressed("attack"):
		_j_press_seen_count += 1
		_try_recover_stuck_executor_on_attack_press()


func _try_recover_stuck_executor_on_attack_press() -> void:
	var player: Node = _resolve_node("Player3D")
	if player == null or not player.has_method("get_attack_executor"):
		return
	var executor: AttackExecutor = player.call("get_attack_executor") as AttackExecutor
	if executor != null and executor.is_active():
		executor.set("_is_active", false)
		_executor_busy_since_sec = -1.0


func _spawn_debug_label_position() -> Vector3:
	var spawn: Node3D = _resolve_node("SpawnPosition") as Node3D
	if spawn != null:
		return spawn.global_position + debug_label_offset
	return debug_label_offset


func _ensure_debug_label() -> void:
	if _debug_label != null and is_instance_valid(_debug_label):
		return
	var root: Node = _scene_root()
	if root == null:
		return
	var existing: Label3D = root.find_child("M11AttackDebug", true, false) as Label3D
	if existing != null:
		_debug_label = existing
		return
	var label := Label3D.new()
	label.name = "M11AttackDebug"
	label.font_size = _DEBUG_LABEL_FONT_SIZE
	label.outline_size = _DEBUG_LABEL_OUTLINE_SIZE
	label.pixel_size = _DEBUG_LABEL_PIXEL_SIZE
	label.fixed_size = true
	label.modulate = _DEBUG_LABEL_MODULATE
	root.add_child(label)
	_debug_label = label
	_sync_debug_label_transform()


func _sync_debug_label_transform() -> void:
	if _debug_label == null:
		return
	var pos: Vector3 = _spawn_debug_label_position()
	_debug_label.global_position = pos
	var basis := Basis(
		Vector3(1.0, 0.0, 0.0),
		_DEBUG_LABEL_BASIS_Y,
		_DEBUG_LABEL_BASIS_Z
	)
	_debug_label.global_transform = Transform3D(basis, pos)


func _ensure_executor_debug_connections() -> void:
	if _executor_connected:
		return
	var player: Node = _resolve_node("Player3D")
	if player == null or not player.has_method("get_attack_executor"):
		return
	var executor: AttackExecutor = player.call("get_attack_executor") as AttackExecutor
	if executor == null:
		return
	if not executor.attack_started.is_connected(_on_attack_started_debug):
		executor.attack_started.connect(_on_attack_started_debug)
	if not executor.projectile_fired.is_connected(_on_projectile_fired_debug):
		executor.projectile_fired.connect(_on_projectile_fired_debug)
	_executor_connected = true


func _on_attack_started_debug(resource: AttackResource) -> void:
	_attack_started_count += 1
	var color := _ATTACK_PING_COLOR_DEFAULT
	if resource != null:
		color = resource.color
	var player: Node3D = _resolve_node("Player3D") as Node3D
	if player != null:
		_spawn_attack_ping(player.global_position, color)


func _on_projectile_fired_debug(projectile: Node3D, _resource: AttackResource) -> void:
	_projectile_fired_count += 1
	if projectile != null and is_instance_valid(projectile):
		_spawn_attack_ping(projectile.global_position, _PROJECTILE_PING_COLOR)


func _spawn_attack_ping(world_pos: Vector3, color: Color) -> void:
	var root: Node = _scene_root()
	if root == null:
		return
	var ping := MeshInstance3D.new()
	ping.name = "M11AttackPing"
	var mesh := SphereMesh.new()
	mesh.radius = _PING_MESH_RADIUS
	mesh.height = _PING_MESH_HEIGHT
	ping.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = _PING_EMISSION_ENERGY
	mat.albedo_color = color
	ping.material_override = mat
	ping.global_position = world_pos + Vector3(0.0, _PING_Y_OFFSET, 0.0)
	root.add_child(ping)
	var tree: SceneTree = get_tree() if is_inside_tree() else null
	if tree != null:
		var timer := tree.create_timer(_PING_LIFETIME_SEC)
		timer.timeout.connect(func() -> void:
			if ping != null and is_instance_valid(ping):
				ping.queue_free()
		)


func _update_debug_label() -> void:
	if _debug_label == null or not is_instance_valid(_debug_label):
		return
	_sync_debug_label_transform()
	var slot_a_id: String = "none"
	var handler: Node = _resolve_node("InfectionInteractionHandler")
	if handler != null and handler.has_method("get_mutation_slot_manager"):
		var mgr: Variant = handler.call("get_mutation_slot_manager")
		if mgr != null and mgr.has_method("get_slot"):
			var slot_a: Variant = mgr.call("get_slot", 0)
			if slot_a != null and slot_a.has_method("get_active_mutation_id"):
				var mid: String = slot_a.call("get_active_mutation_id") as String
				if mid != "":
					slot_a_id = mid
	var psm_name: String = "?"
	var player: Node = _resolve_node("Player3D")
	if player != null:
		var psm: Variant = player.get("_player_state_machine")
		if psm != null and psm.has_method("get_state"):
			psm_name = str(psm.call("get_state"))
	var fusion_on: bool = false
	if player != null:
		if player.has_method("is_fusion_active"):
			fusion_on = player.call("is_fusion_active")
		else:
			fusion_on = bool(player.get("_fusion_active"))
	var block_reason: String = _probe_attack_block_reason()
	var adhesion_hint: String = ""
	if slot_a_id == "adhesion":
		adhesion_hint = _probe_adhesion_root_hint()
	_debug_label.text = "DBG J=%d atk=%d proj=%d slotA=%s psm=%s fuse=%s gate=%s%s" % [
		_j_press_seen_count,
		_attack_started_count,
		_projectile_fired_count,
		slot_a_id,
		psm_name,
		"Y" if fusion_on else "N",
		block_reason,
		adhesion_hint,
	]


func _probe_adhesion_root_hint() -> String:
	var nearest: EnemyInfection3D = _find_nearest_enemy_infection()
	if nearest == null:
		return " root=—"
	var mult: float = 1.0
	if nearest.has_method("get_speed_multiplier"):
		mult = nearest.call("get_speed_multiplier") as float
	elif nearest.get_node_or_null("EnemyEffectTracker") != null:
		var tracker: Node = nearest.get_node_or_null("EnemyEffectTracker")
		if tracker.has_method("get_speed_multiplier"):
			mult = tracker.call("get_speed_multiplier") as float
	if mult <= _ROOTED_SPEED_THRESHOLD:
		return " root=STOP(%.1fs)" % mult
	return " root=off"


func _find_nearest_enemy_infection() -> EnemyInfection3D:
	var root: Node = _scene_root()
	if root == null:
		return null
	var player: Node3D = _resolve_node("Player3D") as Node3D
	if player == null:
		return null
	var best: EnemyInfection3D = null
	var best_dist_sq: float = INF
	for node: Node in root.find_children("*", "EnemyInfection3D", true, false):
		var enemy: EnemyInfection3D = node as EnemyInfection3D
		if enemy == null or not is_instance_valid(enemy):
			continue
		if enemy.has_method("is_dead") and enemy.call("is_dead"):
			continue
		var d_sq: float = player.global_position.distance_squared_to(enemy.global_position)
		if d_sq < best_dist_sq:
			best_dist_sq = d_sq
			best = enemy
	return best


func _probe_attack_block_reason() -> String:
	var player: Node = _resolve_node("Player3D")
	if player == null:
		return "no_player"
	var executor: AttackExecutor = null
	if player.has_method("get_attack_executor"):
		executor = player.call("get_attack_executor") as AttackExecutor
	if executor != null and executor.is_active():
		return "executor_busy"
	var policy: Variant = player.get("_input_policy")
	var psm: Variant = player.get("_player_state_machine")
	if policy != null and psm != null and policy.has_method("is_action_permitted"):
		var st: int = psm.call("get_state") as int
		if not policy.call("is_action_permitted", st, _ACTION_ATTACK):
			return "policy_%d" % st
	var slot_mgr: Variant = player.get("_mutation_slot")
	if slot_mgr == null:
		return "no_slot"
	var a_filled: bool = false
	var b_filled: bool = false
	if slot_mgr.has_method("get_slot"):
		var slot_a: Variant = slot_mgr.call("get_slot", 0)
		var slot_b: Variant = slot_mgr.call("get_slot", 1)
		if slot_a != null and slot_a.has_method("is_filled"):
			a_filled = slot_a.call("is_filled")
		if slot_b != null and slot_b.has_method("is_filled"):
			b_filled = slot_b.call("is_filled")
	if not a_filled and not b_filled:
		return "slots_empty"
	var tree: SceneTree = get_tree() if is_inside_tree() else null
	if tree == null or tree.root.get_node_or_null("AttackDatabase") == null:
		return "no_attack_db"
	return "ok"


func _unhandled_input(event: InputEvent) -> void:
	if not enable_attack_hotkeys:
		return
	if not (event is InputEventKey):
		return
	var key_event: InputEventKey = event as InputEventKey
	if not key_event.pressed or key_event.echo:
		return
	var idx: int = -1
	match key_event.keycode:
		KEY_1:
			idx = _HOTKEY_INDEX_CLAW
		KEY_2:
			idx = _HOTKEY_INDEX_ACID
		KEY_3:
			idx = _HOTKEY_INDEX_CARAPACE
		KEY_4:
			idx = _HOTKEY_INDEX_ADHESION
	if idx < 0 or idx >= _HOTKEY_SLOT_COUNT:
		return
	var handler: Node = _resolve_node("InfectionInteractionHandler")
	if handler == null or not handler.has_method("get_mutation_slot_manager"):
		return
	var mgr: Variant = handler.call("get_mutation_slot_manager")
	if mgr == null:
		return
	_force_slot_a_attack(mgr, _MUTATION_IDS[idx])


func _force_slot_a_attack(mgr: Variant, mutation_id: String) -> void:
	if not mgr.has_method("get_slot"):
		return
	var slot_a: Variant = mgr.call("get_slot", 0)
	var slot_b: Variant = mgr.call("get_slot", 1)
	if slot_a != null and slot_a.has_method("set_active_mutation_id"):
		slot_a.call("set_active_mutation_id", mutation_id)
	if slot_b != null and slot_b.has_method("clear"):
		slot_b.call("clear")
	_clear_player_attack_cooldowns()
	_try_recover_stuck_executor_on_attack_press()


func _clear_player_attack_cooldowns() -> void:
	var player: Node = _resolve_node("Player3D")
	if player == null:
		return
	player.set("_mutation_cooldowns", {})
