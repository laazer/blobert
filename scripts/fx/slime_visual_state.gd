# slime_visual_state.gd
# Fusion active color feedback for the player's SlimeVisual node.
# Tints the mesh bright orange with emission while a fused mutation is active
# (PlayerController3D.is_fusion_active() == true), reverts to baseline otherwise.
#
# Attach to: SlimeVisual (Node3D), direct child of PlayerController3D.
# Mesh path: "MeshInstance3D" (direct child of SlimeVisual).

extends Node3D

const COLOR_BASELINE = Color(0.4, 0.9, 0.6, 1.0)
const COLOR_MUTATION_TINT = Color(1.0, 0.15, 0.0, 1.0)
const COLOR_MUTATION_EMISSION = Color(0.8, 0.1, 0.0, 1.0)

var _mesh: MeshInstance3D = null
var _mesh_ready: bool = false
var _material: StandardMaterial3D = null
var _player: Object = null  # PlayerController3D, resolved lazily
var _current_tinted: bool = false


func _ready() -> void:
	_mesh = get_node_or_null("MeshInstance3D") as MeshInstance3D
	if _mesh == null:
		push_error("SlimeVisualState: MeshInstance3D child not found — color feedback disabled")
		return
	if _mesh.material_override == null:
		push_error("SlimeVisualState: MeshInstance3D.material_override is null — color feedback disabled")
		return
	_material = _mesh.material_override.duplicate() as StandardMaterial3D
	_mesh.material_override = _material
	_mesh_ready = _material != null
	# Parent may not be fully ready yet — resolve lazily in _process
	_player = get_parent()


func _process(_delta: float) -> void:
	if not _mesh_ready or not is_instance_valid(_mesh):
		return
	if _player == null or not is_instance_valid(_player):
		_player = get_parent()
	if _player == null or not _player.has_method("is_fusion_active"):
		return
	var should_tint: bool = _player.is_fusion_active()
	if should_tint == _current_tinted:
		return
	_current_tinted = should_tint
	if _current_tinted:
		_material.albedo_color = COLOR_MUTATION_TINT
		_material.emission_enabled = true
		_material.emission = COLOR_MUTATION_EMISSION
		_material.emission_energy_multiplier = 1.5
	else:
		_material.albedo_color = COLOR_BASELINE
		_material.emission_enabled = false
